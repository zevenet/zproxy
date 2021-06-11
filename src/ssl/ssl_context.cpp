/*
 *    Zevenet zproxy Load Balancer Software License
 *    This file is part of the Zevenet zproxy Load Balancer software package.
 *
 *    Copyright (C) 2019-today ZEVENET SL, Sevilla (Spain)
 *
 *    This program is free software: you can redistribute it and/or modify
 *    it under the terms of the GNU Affero General Public License as
 *    published by the Free Software Foundation, either version 3 of the
 *    License, or any later version.
 *
 *    This program is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *    GNU Affero General Public License for more details.
 *
 *    You should have received a copy of the GNU Affero General Public License
 *    along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 */

#include "ssl_context.h"
#include "ssl_session.h"

using namespace ssl;

bool SSLContext::init(const std::string &cert_file, const std::string &key_file)
{
	initOpenssl();
	ssl_ctx = std::shared_ptr<SSL_CTX>(SSL_CTX_new(SSLv23_method()),
					   &::SSL_CTX_free);
	if (ssl_ctx == nullptr) {
		zcu_log_print(LOG_ERR, "SSL_CTX_new failed");
		return false;
	}
	int r = SSL_CTX_use_certificate_file(ssl_ctx.get(), cert_file.c_str(),
					     SSL_FILETYPE_PEM);
	if (r <= 0) {
		zcu_log_print(LOG_ERR, "SSL_CTX_use_certificate_file %s failed",
			      cert_file.c_str());
		return false;
	}
	r = SSL_CTX_use_PrivateKey_file(ssl_ctx.get(), key_file.c_str(),
					SSL_FILETYPE_PEM);
	if (r <= 0) {
		zcu_log_print(LOG_ERR, "SSL_CTX_use_PrivateKey_file %s failed",
			      key_file.c_str());
		return false;
	}

	r = SSL_CTX_check_private_key(ssl_ctx.get());
	if (!r) {
		zcu_log_print(LOG_ERR, "SSL_CTX_check_private_key failed");
		return false;
	}

	/* Recommended to avoid SSLv2 & SSLv3 */
	SSL_CTX_set_options(ssl_ctx.get(),
			    SSL_OP_ALL | SSL_OP_NO_SSLv2 |
				    SSL_OP_NO_SSLv3); // set ssl option
#if SSL_DISABLE_SESSION_CACHE
	// Attempt to disable session and ticket caching..
	//  SSL_CTX_set_options(ssl_ctx,
	//  SSL_OP_NO_SESSION_RESUMPTION_ON_RENEGOTIATION)
	//  SSL_CTX_set_num_tickets(ssl_ctx, 0);
	SSL_CTX_set_options(ssl_ctx, SSL_OP_NO_TICKET);
	SSL_CTX_set_session_cache_mode(ssl_ctx, SSL_SESS_CACHE_OFF);
#endif
	SSL_CTX_set_options(ssl_ctx.get(), SSL_OP_NO_COMPRESSION);
	SSL_CTX_set_mode(ssl_ctx.get(), SSL_MODE_RELEASE_BUFFERS);

	zcu_log_print(LOG_DEBUG, "SSL initialized");
	return true;
}

bool SSLContext::init(std::shared_ptr<BackendConfig> backend_config_)
{
	if (backend_config_->ctx != nullptr) {
		ssl_ctx = backend_config_->ctx;
	} else {
		const SSL_METHOD *method = TLS_client_method();
		if (method == nullptr)
			return false;
		this->ssl_ctx = std::shared_ptr<SSL_CTX>(SSL_CTX_new(method),
							 &::SSL_CTX_free);
		if (ssl_ctx == nullptr)
			return false;
		SSL_CTX_set_verify(this->ssl_ctx.get(), SSL_VERIFY_NONE,
				   nullptr);
		SSL_CTX_set_mode(this->ssl_ctx.get(), SSL_MODE_RELEASE_BUFFERS);
		SSL_CTX_set_options(this->ssl_ctx.get(), SSL_OP_ALL);
#ifdef SSL_OP_NO_COMPRESSION
		SSL_CTX_set_options(this->ssl_ctx.get(), SSL_OP_NO_COMPRESSION);
#endif
	}
	zcu_log_print(LOG_DEBUG, "Backend %s:%d SSLContext initialized",
		      backend_config_->address.data(), backend_config_->port);
	return true;
}

bool SSLContext::init(std::shared_ptr<ListenerConfig> listener_config_)
{
	initOpenssl();
	listener_config = listener_config_;
	if (listener_config->ctx != nullptr) {
#ifdef SSL_CTRL_SET_TLSEXT_SERVERNAME_CB
		if (listener_config_->ctx->next)
			if (!SSL_CTX_set_tlsext_servername_callback(
				    listener_config_->ctx->ctx.get(),
				    SNIServerName) ||
			    !SSL_CTX_set_tlsext_servername_arg(
				    listener_config_->ctx->ctx.get(),
				    listener_config_->ctx.get()))
				zcu_log_print(
					LOG_ERR,
					"ListenHTTPS: can't set SNI callback");
#endif

		ssl_ctx = listener_config->ctx->ctx;

#if ENABLE_SSL_SESSION_CACHING
		SslSessionManager::attachCallbacks(ssl_ctx);
#endif

#if SSL_DISABLE_SESSION_CACHE
		// Attempt to disable session and ticket caching..
		//      SSL_CTX_set_options(ssl_ctx,
		//                        SSL_OP_NO_SESSION_RESUMPTION_ON_RENEGOTIATION);
		//    SSL_CTX_set_num_tickets(ssl_ctx, 0);
		SSL_CTX_set_options(ssl_ctx, SSL_OP_NO_TICKET);
		SSL_CTX_set_session_cache_mode(ssl_ctx, SSL_SESS_CACHE_OFF);
#endif
		SSL_CTX_set_options(ssl_ctx.get(), SSL_OP_NO_COMPRESSION);
		SSL_CTX_set_mode(ssl_ctx.get(), SSL_MODE_RELEASE_BUFFERS);
		return true;
	}

	if (!listener_config->engine_id.empty())
		initEngine(listener_config->engine_id);

	if (!listener_config->ssl_config_file.empty()) {
		if (!loadOpensslConfig(listener_config->ssl_config_file,
				       listener_config->ssl_config_section,
				       listener_config->ctx->ctx.get()))
			return false;
	}
	zcu_log_print(LOG_DEBUG, "%s():%d: SSL initialized", __FUNCTION__,
		      __LINE__);
	return true;
}

SSLContext::SSLContext()
{
}

SSLContext::~SSLContext()
{
}

std::once_flag flag;

bool SSLContext::initOpenssl()
{
	std::call_once(flag, []() {
		int r = SSL_library_init();
		if (!r) {
			zcu_log_print(LOG_ERR, "SSL_library_init failed");
			return false;
		}
		ERR_load_crypto_strings();
		ERR_load_SSL_strings();
		SSL_load_error_strings();
		OpenSSL_add_all_algorithms();
		return true;
	});
	return true;
}

/* This function loads the OpenSSL configuration file.
 * Documentation related with the config file syntax:
 * https://www.openssl.org/docs/manmaster/man5/config.html*/
bool SSLContext::loadOpensslConfig(const std::string &config_file_path,
				   const std::string &config_file_section,
				   SSL_CTX *__ctx)
{
	/* We use FILE instead of c++ ifstream because it is not
	 * compatible with the NCONF functions. */
	FILE *fp;
	CONF *cnf = nullptr;
	long eline;

	fp = fopen(config_file_path.c_str(), "r");
	if (fp == nullptr) {
		return false;
	} else {
		cnf = NCONF_new(nullptr);
		if (NCONF_load_fp(cnf, fp, &eline) == 0) {
			zcu_log_print(
				LOG_ERR,
				"Error on line %ld of configuration file\n",
				eline);
			return false;
			/* Other malformed configuration file behaviour */
		} else if (CONF_modules_load(cnf, "zproxy",
					     CONF_MFLAGS_NO_DSO) <= 0) {
			zcu_log_print(LOG_ERR,
				      "Error configuring the application");
			ERR_print_errors_fp(stderr);
			return false;
			/* Other configuration error behaviour */
		}

		if (SSL_CTX_config(__ctx, config_file_section.c_str()) == 0) {
			zcu_log_print(LOG_ERR, "Error configuring SSL_CTX");
			ERR_print_errors_fp(stderr);
			return false;
		}
		fclose(fp);
		NCONF_free(cnf);
		return true;
	}
}

int SSLContext::SNIServerName(SSL *ssl, int dummy, SNI_CERTS_CTX *ctx)
{
	const char *server_name;
	SNI_CERTS_CTX *pc;

	if ((server_name = SSL_get_servername(
		     ssl, TLSEXT_NAMETYPE_host_name)) == nullptr)
		return SSL_TLSEXT_ERR_NOACK;

	/* logmsg(LOG_DEBUG, "Received SSL SNI Header for servername %s",
	 * servername); */

	SSL_set_SSL_CTX(ssl, nullptr);
	for (pc = ctx; pc; pc = pc->next.get()) {
		if (fnmatch(pc->server_name, server_name, 0) == 0) {
			/* logmsg(LOG_DEBUG, "Found cert for %s", servername); */
			SSL_set_SSL_CTX(ssl, pc->ctx.get());
			return SSL_TLSEXT_ERR_OK;
		} else if (pc->subjectAltNameCount > 0 &&
			   pc->subjectAltNames != nullptr) {
			size_t i;
			for (i = 0; i < pc->subjectAltNameCount; i++) {
				if (fnmatch(reinterpret_cast<char *>(
						    pc->subjectAltNames[i]),
					    server_name, 0) == 0) {
					SSL_set_SSL_CTX(ssl, pc->ctx.get());
					return SSL_TLSEXT_ERR_OK;
				}
			}
		}
	}

	/* logmsg(LOG_DEBUG, "No match for %s, default used", server_name); */
	SSL_set_SSL_CTX(ssl, ctx->ctx.get());
	return SSL_TLSEXT_ERR_OK;
}

bool SSLContext::initEngine(const std::string &engine_id)
{
	if (engine_id.empty())
		return false;

	ENGINE *e;

	if (!(e = ENGINE_by_id(engine_id.data()))) {
		zcu_log_print(LOG_ERR, "could not find engine");
		return false;
	} else if (!ENGINE_init(e)) {
		zcu_log_print(LOG_ERR, "could not init engine");
		return false;
	} else if (!ENGINE_set_default(e, ENGINE_METHOD_ALL)) {
		zcu_log_print(LOG_ERR, "could not set all defaults");
		return false;
	}

	ENGINE_finish(e);
	ENGINE_free(e);
	return true;
}
