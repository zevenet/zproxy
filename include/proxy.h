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

#ifndef _ZPROXY_PROXY_H
#define _ZPROXY_PROXY_H

#include <ev.h>
#include <stdint.h>
#include <netinet/in.h>
#include <openssl/ssl.h>

#include "list.h"
#include "config.h"
#include "http_stream.h"

enum zproxy_state {
	ZPROXY_CONN_RECV_HTTP_REQ,
	ZPROXY_CONN_SEND_HTTP_RESP,
	ZPROXY_CONN_SEND_HTTP_CONTINUE,
	ZPROXY_CONN_RECV_HTTP_RESP,
	ZPROXY_CONN_SPLICE_HTTP_RESP,
};

#define ZPROXY_BUFSIZ		65536

struct zproxy_backend;

struct zproxy_conn {
	struct list_head		list;
	struct ev_timer			timer;
	HttpStream 			*stream;
	enum zproxy_state		state;
	struct {
		struct ev_io		io;
		struct sockaddr_in	addr;
		char			*buf;
		uint32_t		buf_siz;
		uint32_t		buf_len;
		uint32_t		buf_sent;
		bool			ssl_enabled;
		bool			ssl_handshake;
		const char		*resp_buf;
		uint32_t		resp_buf_len;
		const char		*buf_stash;
		uint32_t		buf_stash_len;
		bool			stopped;
		bool			close;
		bool			shutdown;
		uint64_t		req_len;
		SSL			*ssl;
	} client;
	struct {
		struct ev_io		io;
		struct ev_timer		timer;
		struct sockaddr_in	addr;
		char			*buf;
		uint32_t		buf_siz;
		uint32_t		buf_len;
		uint32_t		buf_sent;
		bool			ssl_enabled;
		const char		*buf_stash;
		uint32_t		buf_stash_len;
		bool			stopped;
		uint64_t		resp_len;
		bool			setup;
		bool			connected;
		uint64_t		sent;
		uint64_t		recv;
		uint32_t		pending;
		int			reconnect;
		SSL			*ssl;
		SSL_CTX			*ssl_ctx;
		struct zproxy_backend_cfg *cfg;
	} backend;
	int				splice_fds[2];
	struct zproxy_proxy		*proxy;
};

int zproxy_conn_client_send(struct ev_loop *loop, const char *buf, uint32_t buflen,
			    uint32_t *numbytes, struct zproxy_conn *conn);
int zproxy_conn_client_recv(struct ev_loop *loop, struct zproxy_conn *conn, uint32_t *numbytes);
int zproxy_conn_backend_send(struct ev_loop *loop, struct zproxy_conn *conn, uint32_t *numbytes);
/**
 * Receive from backend connection.
 *
 * @return On success 1; on failture -1.
 */
int zproxy_conn_backend_recv(struct ev_loop *loop, struct zproxy_conn *conn, uint32_t *numbytes);
int zproxy_conn_backend_connect(struct ev_loop *loop, struct zproxy_conn *conn, struct zproxy_backend *backend);
int zproxy_conn_backend_reset(struct ev_loop *loop,
			      struct zproxy_conn *conn,
			      const struct zproxy_backend *backend);
void zproxy_conn_backend_close(struct ev_loop *loop, struct zproxy_conn *conn);
void zproxy_conn_release(struct ev_loop *loop, struct zproxy_conn *conn, int err);
void zproxy_conn_reset_state(struct ev_loop *loop, struct zproxy_conn *conn);
void zproxy_conn_reset_continue(struct ev_loop *loop, struct zproxy_conn *conn);

void zproxy_io_update(struct ev_loop *loop, struct ev_io *io,
		      void (*cb)(struct ev_loop *loop, struct ev_io *io, int events),
		      int events);

enum zproxy_proxy_type {
	ZPROXY_HTTP	= 0,
};

struct zproxy_handler {
	enum zproxy_proxy_type	type;

	void *(*init)(struct zproxy_proxy *proxy);
	void (*fini)(struct zproxy_proxy *proxy);
	void (*client)(struct ev_loop *loop, struct zproxy_conn *conn,
		       int events);
	int (*backend)(struct ev_loop *loop, struct zproxy_conn *conn,
		       int events);
	int (*reconnect)(struct ev_loop *loop, struct zproxy_conn *conn,
			 int events, struct zproxy_backend *backend);
	int (*timeout)(struct ev_loop *loop, struct zproxy_conn *conn,
		       int events);
	int (*nossl)(struct ev_loop *loop, struct zproxy_conn *conn,
		      int events);
};

struct zproxy_proxy {
	struct list_head		list;
	struct ev_io			io;
	struct zproxy_worker		*worker;
	const struct zproxy_handler	*handler;
	const struct zproxy_proxy_cfg	*cfg;
	SSL_CTX				*ssl;
	void				*state;
};

struct zproxy_proxy *zproxy_proxy_create(const struct zproxy_proxy_cfg *cfg,
					 struct zproxy_worker *worker,
					 const struct zproxy_handler *handler);
void zproxy_proxy_destroy(struct zproxy_proxy *proxy);

extern struct zproxy_handler http_proxy;

void zproxy_client_cb(struct ev_loop *loop, struct ev_io *io, int events);
void zproxy_backend_cb(struct ev_loop *loop, struct ev_io *io, int events);

struct zproxy_backend {
	struct sockaddr_in	addr;
	bool			ssl_enabled;
	struct zproxy_backend_cfg *cfg;
};

#endif
