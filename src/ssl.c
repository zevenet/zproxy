/*
 * Copyright (C) 2023  Zevenet S.L. <support@zevenet.com>
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as
 * published by the Free Software Foundation, either version 3 of the
 * License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#include <syslog.h>
#include <assert.h>
#include <arpa/inet.h>
#include <openssl/ssl.h>
#include <openssl/x509v3.h>
#include <errno.h>
#include <unistd.h>
#include <mutex>
#include "proxy.h"
#include "config.h"
#include "ssl.h"

#ifndef SSL3_ST_SR_CLNT_HELLO_A
#define SSL3_ST_SR_CLNT_HELLO_A (0x110 | SSL_ST_ACCEPT)
#endif
#ifndef SSL23_ST_SR_CLNT_HELLO_A
#define SSL23_ST_SR_CLNT_HELLO_A (0x210 | SSL_ST_ACCEPT)
#endif

static DH *DH512_params, *DH2048_params;

static DH *DH_tmp_callback(/* not used */ SSL *s,
			   /* not used */ int is_export, int keylength)
{
	return keylength == 512 ? DH512_params : DH2048_params;
}

#if OPENSSL_VERSION_NUMBER >= 0x10100000L
#define general_name_string(n) \
	reinterpret_cast<unsigned char *>( \
		strndup(reinterpret_cast<const char *>( \
				ASN1_STRING_get0_data(n->d.dNSName)), \
			ASN1_STRING_length(n->d.dNSName) + 1))
#else
#define general_name_string(n) \
	(unsigned char *)strndup((char *)ASN1_STRING_data(n->d.dNSName), \
				 ASN1_STRING_length(n->d.dNSName) + 1)
#endif

static int zproxy_sni_servername_cb(SSL *ssl, int dummy, struct list_head *certs)
{
	const char *server_name;
	sni_cert_ctx *c;
	regmatch_t matches;

	if ((server_name = SSL_get_servername(
		     ssl, TLSEXT_NAMETYPE_host_name)) == nullptr)
		return SSL_TLSEXT_ERR_NOACK;

	SSL_set_SSL_CTX(ssl, nullptr);

	list_for_each_entry(c, certs, list) {
		if (!regexec(&c->server_name, server_name, 0, &matches, 0)) {
			syslog(LOG_DEBUG, "Found cert for %s", server_name);
			SSL_set_SSL_CTX(ssl, c->ctx);
			return SSL_TLSEXT_ERR_OK;
		} else if (c->subjectAltNameCount > 0 &&
			c->subjectAltNames != nullptr) {
			size_t i;
			for (i = 0; i < c->subjectAltNameCount; i++) {
				if (!regexec(c->subjectAltNames[i],
					server_name, 0, &matches, 0)) {
					SSL_set_SSL_CTX(ssl, c->ctx);
					return SSL_TLSEXT_ERR_OK;
				}
			}
		}
	}

	syslog(LOG_DEBUG, "No match for %s, default used", server_name);
	c = list_first_entry(certs, struct sni_cert_ctx, list);
	SSL_set_SSL_CTX(ssl, c->ctx);
	return SSL_TLSEXT_ERR_OK;
}

void zproxy_conn_backend_ssl_free(struct zproxy_conn *conn)
{
	SSL_free(conn->backend.ssl);
}

void zproxy_conn_client_ssl_free(struct zproxy_conn *conn)
{
	SSL_free(conn->client.ssl);
}

static bool parseCertCN(regex_t *pattern, char *server_name)
{
	char server_[ZCU_DEF_BUFFER_SIZE];
	int len = 0, nlen = 0;

	server_[len++] = '^';
	do {
		// add: "[-a-z0-1]*"
		if (server_name[nlen] == '*') {
			server_[len++] = '[';
			server_[len++] = '-';
			server_[len++] = 'a';
			server_[len++] = '-';
			server_[len++] = 'z';
			server_[len++] = '0';
			server_[len++] = '-';
			server_[len++] = '9';
			server_[len++] = ']';
			server_[len++] = '*';
		} else if (server_name[nlen] == '.') {
			server_[len++] = '\\';
			server_[len++] = '.';
		} else
			server_[len++] = server_name[nlen];
		nlen++;

	} while (server_name[nlen] != '\0' && len < ZCU_DEF_BUFFER_SIZE);

	if (len >= ZCU_DEF_BUFFER_SIZE) {
		zcu_log_print(
			LOG_ERR,
			"Error parsing certificate server name, buffer full %s",
			server_name);
		return true;
	}

	server_[len++] = '$';
	server_[len++] = '\0';

	if (regcomp(pattern, server_, REG_NEWLINE))
		return true;

	return false;
}

static regex_t **get_subjectaltnames(X509 *x509, unsigned int *count_)
{
	size_t local_count;
	regex_t **result;
	STACK_OF(GENERAL_NAME) *san_stack =
		static_cast<STACK_OF(GENERAL_NAME) *>(X509_get_ext_d2i(
			x509, NID_subject_alt_name, nullptr, nullptr));
	unsigned char *temp[sk_GENERAL_NAME_num(san_stack)];
	GENERAL_NAME *name__;
	size_t i;

	local_count = 0;
	result = nullptr;
	name__ = nullptr;
	*count_ = 0;

	if (san_stack == nullptr)
		return nullptr;

	while (sk_GENERAL_NAME_num(san_stack) > 0) {
		name__ = sk_GENERAL_NAME_pop(san_stack);
		switch (name__->type) {
		case GEN_DNS:
			temp[local_count] = general_name_string(name__);
			if (temp[local_count] == nullptr) {
				fprintf(stderr, "out of memory");
				return NULL;
			}
			local_count++;
			break;
		default:
			zcu_log_print(
				LOG_ERR,
				"unsupported subjectAltName type encountered: %i",
				name__->type);
		}
		GENERAL_NAME_free(name__);
	}

	if (local_count > 0) {
		result = (regex_t **)calloc(1, sizeof(regex_t *) * local_count);
		if (result == nullptr) {
			fprintf(stderr, "out of memory");
			return NULL;
		}

		for (i = 0; i < local_count; i++) {
			result[i] = (regex_t *)calloc(1, sizeof(regex_t));
			if (result[i] == nullptr) {
				fprintf(stderr, "out of memory");
				return NULL;
			}
			if (parseCertCN(result[i],(char *)temp[i])) {
				fprintf(stderr, "out of memory");
				return NULL;
			}
			free(temp[i]);
		}
	}
	*count_ = (unsigned int)local_count;

	sk_GENERAL_NAME_pop_free(san_stack, GENERAL_NAME_free);

	return result;
}

int zproxy_ssl_ctx_alloc(struct zproxy_proxy_cfg *cfg, const char *cert_path, int *err)
{
	SSL_CTX *ctx;
	struct sni_cert_ctx *c;
	FILE * file;
	char server_name[ZCU_DEF_BUFFER_SIZE] = { "" };
	regmatch_t matches[5];
	regex_t regex;

	file = fopen(cert_path, "r");
	if (!file) {
		*err = SSL_CERTFILE_ERR;
		return -1;
	}

	fclose(file);

	c = (struct sni_cert_ctx *)calloc(1, sizeof(struct sni_cert_ctx));
	if (!c) {
		*err = SSL_INIT_ERR;
		return -1;
	}

	ctx = SSL_CTX_new(SSLv23_server_method());
	if (!ctx) {
		syslog(LOG_ERR, "cannot initialize ssl");
		*err = SSL_INIT_ERR;
		return -1;
	}

	SSL_CTX_use_certificate_chain_file(ctx, cert_path);
	SSL_CTX_use_PrivateKey_file(ctx, cert_path, SSL_FILETYPE_PEM);
	SSL_CTX_check_private_key(ctx);

	c->ctx = ctx;

	std::unique_ptr<BIO, decltype(&::BIO_free)> bio_cert(
		BIO_new_file(cert_path, "r"), ::BIO_free);
	std::unique_ptr<X509, decltype(&::X509_free)> x509(
		::PEM_read_bio_X509(bio_cert.get(), nullptr, nullptr, nullptr),
		::X509_free);
	X509_NAME_oneline(X509_get_subject_name(x509.get()), server_name,
			  ZCU_DEF_BUFFER_SIZE - 1);
	c->subjectAltNameCount = 0;
	c->subjectAltNames =
		get_subjectaltnames(x509.get(), &(c->subjectAltNameCount));

	regcomp(&regex, CONFIG_REGEX_CNName, REG_ICASE | REG_EXTENDED);
	if (!regexec(&regex, server_name, 4, matches, 0)) {
		server_name[matches[1].rm_eo] = '\0';
		if (parseCertCN(&c->server_name, server_name + matches[1].rm_so)) {
			regfree(&regex);
			*err = SSL_SERVERNAME_ERR;
			return -1;
		}
	} else {
		regfree(&regex);
		*err = SSL_SERVERNAME_ERR;
		return -1;
	}
	regfree(&regex);

	/* configure sni callback */
	if (!SSL_CTX_set_tlsext_servername_callback(ctx, zproxy_sni_servername_cb) ||
	    !SSL_CTX_set_tlsext_servername_arg(ctx, &cfg->runtime.ssl_certs)) {
		*err = SSL_LOADCB_ERR;
		return -1;
	}

	list_add_tail(&c->list, &cfg->runtime.ssl_certs);

	return 0;
}

DH *load_dh_params(const char *file)
{
	BIO *bio;
	DH *dh;

	bio = BIO_new_file(file, "r");
	if (!bio) {
	        zcu_log_print(LOG_ERR, "unable to open DH file - %s", file);
	        return NULL;
	}

	dh = PEM_read_bio_DHparams(bio, NULL, NULL, NULL);
	BIO_free(bio);

	return dh;
}

int zproxy_ssl_ctx_configure(const struct zproxy_proxy_cfg *cfg)
{
	uint64_t options = SSL_OP_ALL |
			   SSL_OP_NO_SSLv2 |
			   SSL_OP_NO_RENEGOTIATION |
			   SSL_OP_NO_SESSION_RESUMPTION_ON_RENEGOTIATION |
			   SSL_OP_NO_COMPRESSION |
			   SSL_OP_SINGLE_DH_USE |
			   SSL_OP_SINGLE_ECDH_USE |
			   cfg->ssl.ssl_op_enable;
	uint64_t disable_options = cfg->ssl.ssl_op_disable;
	X509_LOOKUP *lookup;
	X509_STORE *store;
	sni_cert_ctx *c;

	/* You cannot disable mandatory ssl options, sorry. */
	disable_options &= ~options;

	list_for_each_entry(c, &cfg->runtime.ssl_certs, list) {
		SSL_CTX_set_app_data(c->ctx, c);
		SSL_CTX_set_mode(c->ctx, SSL_MODE_RELEASE_BUFFERS);
		SSL_CTX_set_options(c->ctx, options);
		SSL_CTX_clear_options(c->ctx, disable_options);
		if (cfg->cfg->runtime.ssl_dh_params)
			SSL_CTX_set_tmp_dh(c->ctx, cfg->cfg->runtime.ssl_dh_params);
		else
			SSL_CTX_set_tmp_dh_callback(c->ctx, DH_tmp_callback);

		SSL_CTX_set_cipher_list(c->ctx, cfg->ssl.ciphers);

		store = SSL_CTX_get_cert_store(c->ctx);
		if ((lookup = X509_STORE_add_lookup(store, X509_LOOKUP_file())) == nullptr)
			syslog(LOG_ERR, "X509_STORE_add_lookup failed");
		X509_STORE_set_flags(store, X509_V_FLAG_CRL_CHECK | X509_V_FLAG_CRL_CHECK_ALL);

		/* This generates a EC_KEY structure with no key, but a group defined */
		if (cfg->cfg->runtime.ssl_ecdh_curve_nid != 0) {
			EC_KEY *ecdh;
			if ((ecdh = EC_KEY_new_by_curve_name(cfg->cfg->runtime.ssl_ecdh_curve_nid)) == nullptr)
				syslog(LOG_ERR, "Unable to generate Listener temp ECDH key");
			SSL_CTX_set_tmp_ecdh(c->ctx, ecdh);
			SSL_CTX_set_options(c->ctx, SSL_OP_SINGLE_ECDH_USE);
			EC_KEY_free(ecdh);
		}
		else {
			SSL_CTX_set_ecdh_auto(cfg->runtime.ssl_ctx, 1);
		}
	}

	return 0;
}

void zproxy_ssl_ctx_free(SSL_CTX *ctx)
{
	SSL_CTX_free(ctx);
}

SSL *zproxy_ssl_client_init(zproxy_proxy_cfg *cfg, int sd)
{
	SSL *ssl;
	struct sni_cert_ctx *c;

	// By default, use the first CTX
	c = list_first_entry(&cfg->runtime.ssl_certs, struct sni_cert_ctx, list);
	ssl = SSL_new(c->ctx);
	if (!ssl)
		return NULL;

	SSL_set_mode(ssl, SSL_MODE_ENABLE_PARTIAL_WRITE);
	SSL_set_accept_state(ssl);
	SSL_set_fd(ssl, sd);

	return ssl;
}

static int zproxy_conn_client_ssl_handshake(struct ev_loop *loop, struct zproxy_conn *conn)
{
	int ret, err, events;

	ret = SSL_do_handshake(conn->client.ssl);
	if (ret == 1) {
		switch (conn->state) {
		case ZPROXY_CONN_RECV_HTTP_REQ:
			events = EV_READ;
			break;
		case ZPROXY_CONN_RECV_HTTP_RESP:
			events = EV_WRITE;
			break;
		default:
			syslog(LOG_ERR, "unexpected state in %s: %u", __func__, conn->state);
			return -1;
		}

		conn->client.ssl_handshake = true;
		zproxy_io_update(loop, &conn->client.io, zproxy_client_cb, events);

		return 0;
	}

	err = SSL_get_error(conn->client.ssl, ret);
	switch (err) {
	case SSL_ERROR_WANT_READ:
		ev_io_stop(loop, &conn->client.io);
		ev_io_set(&conn->client.io, conn->client.io.fd, EV_READ);
		ev_io_start(loop, &conn->client.io);
		break;
	case SSL_ERROR_WANT_WRITE:
		ev_io_stop(loop, &conn->client.io);
		ev_io_set(&conn->client.io, conn->client.io.fd, EV_WRITE);
		ev_io_start(loop, &conn->client.io);
		break;
	default:
		return -1;
	}

	return 0;
}

void zproxy_client_ssl_cb(struct ev_loop *loop, struct ev_io *io, int events)
{
	struct zproxy_conn *conn;
	int ret;

	if (events & EV_ERROR)
		return;

	conn = container_of(io, struct zproxy_conn, client.io);

	if (conn->client.ssl_handshake) {
		ret = -1;
		goto err_close;
	}

	ret = zproxy_conn_client_ssl_handshake(loop, conn);
	if (ret < 0)
		goto err_close;

	return;
err_close:
	zproxy_conn_release(loop, conn, ret);
}

int __zproxy_conn_ssl_client_recv(struct ev_loop *loop,
				  struct zproxy_conn *conn,
				  uint32_t *numbytes)
{
	int ret, err;
	ret = SSL_read(conn->client.ssl, conn->client.buf + conn->client.buf_len,
		       conn->client.buf_siz - conn->client.buf_len);
	if (ret < 0) {
		err = SSL_get_error(conn->client.ssl, ret);
		switch (err) {
		case SSL_ERROR_WANT_WRITE:
			zproxy_io_update(loop, &conn->client.io,
					 zproxy_client_ssl_cb, EV_WRITE);
			return 0;
		case SSL_ERROR_WANT_READ:
			return 0;
		case SSL_ERROR_SYSCALL:
			if (errno == 0)
				return 1;
			else
				return -1;
		}

		syslog(LOG_ERR, "error reading from SSL client %s:%hu (%d)\n",
		       inet_ntoa(conn->client.addr.sin_addr),
		       ntohs(conn->client.addr.sin_port), err);
		return -1;
	}
	*numbytes = ret;

	return 1;
}

int zproxy_conn_ssl_client_send(struct ev_loop *loop,
				const char *buf, uint32_t buflen,
				uint32_t *numbytes, struct zproxy_conn *conn)
{
	int ret, err;

	ret = SSL_write(conn->client.ssl, buf, buflen);
	if (ret < 0) {
		err = SSL_get_error(conn->client.ssl, ret);
		switch (err) {
		case SSL_ERROR_WANT_READ:
			zproxy_io_update(loop, &conn->client.io,
					 zproxy_client_ssl_cb, EV_READ);
			return 0;
		case SSL_ERROR_WANT_WRITE:
			return 0;
		}

		syslog(LOG_ERR, "error sending to SSL client %s:%hu (%d)\n",
		       inet_ntoa(conn->client.addr.sin_addr),
		       ntohs(conn->client.addr.sin_port), err);
		return -1;
	}
	*numbytes = ret;

	return 1;
}

int zproxy_ssl_backend_ctx_alloc(struct zproxy_backend_cfg *cfg)
{
	SSL_CTX *ctx;

	ctx = SSL_CTX_new(SSLv23_client_method());
	if (!ctx) {
		syslog(LOG_ERR, "cannot initialize backend ssl");
		return -1;
	}

	cfg->runtime.ssl_ctx = ctx;

	return 0;
}

int zproxy_ssl_backend_init(struct zproxy_conn *conn)
{
	SSL_CTX *ctx;
	SSL *ssl;

	ctx = conn->backend.cfg->runtime.ssl_ctx;

	ssl = SSL_new(ctx);
	if (!ssl) {
		SSL_free(ssl);
		return -1;
	}

	SSL_set_mode(ssl, SSL_MODE_ENABLE_PARTIAL_WRITE);
	SSL_set_connect_state(ssl);
	SSL_set_fd(ssl, conn->backend.io.fd);

	conn->backend.ssl_ctx = ctx;
	conn->backend.ssl = ssl;

	return 0;
}

static int zproxy_conn_backend_ssl_handshake(struct ev_loop *loop, struct zproxy_conn *conn)
{
	int ret, err, events;

	ret = SSL_do_handshake(conn->backend.ssl);
	if (ret == 1) {
		switch (conn->state) {
		case ZPROXY_CONN_RECV_HTTP_REQ:
			events = EV_WRITE;
			break;
		case ZPROXY_CONN_RECV_HTTP_RESP:
			events = EV_READ;
			break;
		default:
			syslog(LOG_ERR, "unexpected state in %s: %u", __func__, conn->state);
			return -1;
		}

		zproxy_io_update(loop, &conn->backend.io, zproxy_backend_cb, events);
		return 0;
	}

	err = SSL_get_error(conn->backend.ssl, ret);
	switch (err) {
	case SSL_ERROR_WANT_READ:
		ev_io_stop(loop, &conn->backend.io);
		ev_io_set(&conn->backend.io, conn->backend.io.fd, EV_READ);
		ev_io_start(loop, &conn->backend.io);
		break;
	case SSL_ERROR_WANT_WRITE:
		ev_io_stop(loop, &conn->backend.io);
		ev_io_set(&conn->backend.io, conn->backend.io.fd, EV_WRITE);
		ev_io_start(loop, &conn->backend.io);
		break;
	default:
		return -1;
	}

	return 0;
}

void zproxy_backend_ssl_cb(struct ev_loop *loop, struct ev_io *io, int events)
{
	struct zproxy_conn *conn;
	int ret;

	if (events & EV_ERROR)
		return;

	conn = container_of(io, struct zproxy_conn, backend.io);

	ret = zproxy_conn_backend_ssl_handshake(loop, conn);
	if (ret < 0)
		goto err_close;

	return;
err_close:
	zproxy_conn_release(loop, conn, ret);
}

int __zproxy_conn_ssl_backend_recv(struct ev_loop *loop, struct zproxy_conn *conn,
				   uint32_t *numbytes)
{
	int ret, err;

	ret = SSL_read(conn->backend.ssl, conn->backend.buf + conn->backend.buf_len,
		       conn->backend.buf_siz - conn->backend.buf_len);
	if (ret < 0) {
		err = SSL_get_error(conn->backend.ssl, ret);
		switch (err) {
		case SSL_ERROR_WANT_WRITE:
			zproxy_io_update(loop, &conn->backend.io,
					 zproxy_backend_ssl_cb, EV_WRITE);
			return 0;
		case SSL_ERROR_WANT_READ:
			return 0;
		case SSL_ERROR_SYSCALL:
			if (errno == 0)
				return 1;
			else
				return -1;
		}

		syslog(LOG_ERR, "error reading from SSL backend %s:%hu (%d)\n",
		       inet_ntoa(conn->backend.addr.sin_addr),
		       ntohs(conn->backend.addr.sin_port), err);
		return -1;
	}
	*numbytes = ret;

	return 1;
}

int __zproxy_conn_ssl_backend_send(struct ev_loop *loop, struct zproxy_conn *conn,
				   uint32_t *numbytes)
{
	int ret, err;

	ret = SSL_write(conn->backend.ssl, &conn->client.buf[conn->backend.buf_sent],
			conn->client.buf_len - conn->backend.buf_sent);
	if (ret < 0) {
		err = SSL_get_error(conn->backend.ssl, ret);
		switch (err) {
		case SSL_ERROR_WANT_READ:
			zproxy_io_update(loop, &conn->backend.io,
					 zproxy_backend_ssl_cb, EV_READ);
			return 0;
		case SSL_ERROR_WANT_WRITE:
			return 0;
		}

		syslog(LOG_ERR, "error sending to SSL backend %s:%hu (%d)\n",
		       inet_ntoa(conn->backend.addr.sin_addr),
		       ntohs(conn->backend.addr.sin_port), err);
		return -1;
	}
	*numbytes = ret;

	return 1;
}
