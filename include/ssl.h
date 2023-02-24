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

#ifndef _ZPROXY_SSL_H_
#define _ZPROXY_SSL_H_

#include <openssl/ssl.h>

enum SSL_errors {
	SSL_CERTFILE_ERR,
	SSL_INIT_ERR,
	SSL_SERVERNAME_ERR,
	SSL_LOADCB_ERR,
};

void zproxy_conn_backend_ssl_free(struct zproxy_conn *conn);
void zproxy_conn_client_ssl_free(struct zproxy_conn *conn);

int zproxy_ssl_ctx_alloc(struct zproxy_proxy_cfg *cfg, const char *cert_path, int *err);
int zproxy_ssl_ctx_configure(const struct zproxy_proxy_cfg *cfg);
void zproxy_ssl_ctx_free(SSL_CTX *ctx);

SSL *zproxy_ssl_client_init(zproxy_proxy_cfg *cfg, int sd);
void zproxy_client_ssl_cb(struct ev_loop *loop, struct ev_io *io, int events);

int __zproxy_conn_ssl_client_recv(struct ev_loop *loop, struct zproxy_conn *conn, uint32_t *numbytes);
int zproxy_conn_ssl_client_send(struct ev_loop *loop, const char *buf,
				uint32_t buflen, uint32_t *numbytes,
				struct zproxy_conn *conn);

int zproxy_ssl_backend_ctx_alloc(struct zproxy_backend_cfg *cfg);
int zproxy_ssl_backend_init(struct zproxy_conn *conn);
void zproxy_backend_ssl_cb(struct ev_loop *loop, struct ev_io *io, int events);
int __zproxy_conn_ssl_backend_send(struct ev_loop *loop, struct zproxy_conn *conn,
				   uint32_t *numbytes);
int __zproxy_conn_ssl_backend_recv(struct ev_loop *loop, struct zproxy_conn *conn,
				   uint32_t *numbytes);

DH *load_dh_params(const char *file);

#endif
