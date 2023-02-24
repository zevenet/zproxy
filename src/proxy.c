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

#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include <stdlib.h>
#include <stdint.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <fcntl.h>
#include <syslog.h>
#include <ev.h>
#include <errno.h>
#include <assert.h>
#include <fcntl.h>

#include "proxy.h"
#include "socket.h"
#include "worker.h"
#include "ssl.h"
#include "list.h"
#include "http_manager.h"

static int zproxy_conn_raw_client_send(struct ev_loop *loop,
				       const char *buf, uint32_t buflen,
				       uint32_t *numbytes,
				       struct zproxy_conn *conn)
{
	int ret;

	ret = send(conn->client.io.fd, buf, buflen, 0);
	if (ret < 0)
		return -1;

	*numbytes = ret;
	return 1;
}

int zproxy_conn_client_send(struct ev_loop *loop,
			    const char *buf, uint32_t buflen,
			    uint32_t *numbytes, struct zproxy_conn *conn)
{
	if (conn->client.ssl)
		return zproxy_conn_ssl_client_send(loop, buf, buflen, numbytes, conn);

	return zproxy_conn_raw_client_send(loop, buf, buflen, numbytes, conn);
}

static int __zproxy_conn_client_recv(struct ev_loop *loop,
				     struct zproxy_conn *conn,
				     uint32_t *numbytes)
{
	int ret;

	ret = recv(conn->client.io.fd, conn->client.buf + conn->client.buf_len,
		   conn->client.buf_siz - conn->client.buf_len, 0);
	if (ret < 0) {
		syslog(LOG_ERR, "error reading from client %s:%hu (%s)\n",
		       inet_ntoa(conn->client.addr.sin_addr),
		       ntohs(conn->client.addr.sin_port), strerror(errno));
		return -1;
	}
	*numbytes = ret;

	return 1;
}

int zproxy_conn_client_recv(struct ev_loop *loop, struct zproxy_conn *conn,
			    uint32_t *numbytes)
{
	if (conn->client.ssl)
		return __zproxy_conn_ssl_client_recv(loop, conn, numbytes);

	return __zproxy_conn_client_recv(loop, conn, numbytes);
}

static int __zproxy_conn_backend_send(struct ev_loop *loop,
				      struct zproxy_conn *conn,
				      uint32_t *numbytes)
{
	int ret;

	ret = send(conn->backend.io.fd, &conn->client.buf[conn->backend.buf_sent],
		   conn->client.buf_len - conn->backend.buf_sent, 0);
	if (ret < 0)
		return -1;

	*numbytes = ret;
	return 1;
}

int zproxy_conn_backend_send(struct ev_loop *loop, struct zproxy_conn *conn,
			     uint32_t *numbytes)
{
	if (conn->backend.ssl)
		return __zproxy_conn_ssl_backend_send(loop, conn, numbytes);

	return __zproxy_conn_backend_send(loop, conn, numbytes);
}

static int __zproxy_conn_backend_recv(struct ev_loop *loop,
				      struct zproxy_conn *conn,
				      uint32_t *numbytes)
{
	int ret;

	ret = recv(conn->backend.io.fd, &conn->backend.buf[conn->backend.buf_len],
		   conn->backend.buf_siz - conn->backend.buf_len, 0);
	if (ret < 0) {
		syslog(LOG_ERR, "[bk:%s:%hu] Error reading from backend: %s",
		       inet_ntoa(conn->backend.addr.sin_addr),
		       ntohs(conn->backend.addr.sin_port), strerror(errno));
		return -1;
	}
	*numbytes = ret;

	return 1;
}

int zproxy_conn_backend_recv(struct ev_loop *loop, struct zproxy_conn *conn,
			     uint32_t *numbytes)
{
	if (conn->backend.ssl)
		return __zproxy_conn_ssl_backend_recv(loop, conn, numbytes);

	return __zproxy_conn_backend_recv(loop, conn, numbytes);
}

void zproxy_conn_backend_close(struct ev_loop *loop, struct zproxy_conn *conn)
{
	if (conn->backend.setup) {
		if (conn->splice_fds[0] >= 0)
			close(conn->splice_fds[0]);
		if (conn->splice_fds[1] >= 0)
			close(conn->splice_fds[1]);

		ev_timer_stop(loop, &conn->backend.timer);
		ev_io_stop(loop, &conn->backend.io);
		shutdown(conn->backend.io.fd, SHUT_RDWR);
		close(conn->backend.io.fd);
	}
	zproxy_conn_backend_ssl_free(conn);
}

void zproxy_conn_release(struct ev_loop *loop, struct zproxy_conn *conn, int err)
{
	int error = errno, level;

	list_del(&conn->list);
	ev_timer_stop(loop, &conn->timer);

	ev_io_stop(loop, &conn->client.io);
	shutdown(conn->client.io.fd, SHUT_RDWR);
	free(conn->client.buf);
	free((void *)conn->client.buf_stash);
	close(conn->client.io.fd);
	free((void *)conn->client.resp_buf);
	zproxy_conn_client_ssl_free(conn);

	free((void *)conn->backend.buf_stash);
	free(conn->backend.buf);
	zproxy_conn_backend_close(loop, conn);

	delete conn->stream;

	if (err < 0)
		level = LOG_ERR;
	else
		level = LOG_DEBUG;

	syslog(level, "[%lx] connection release for client %s:%hu (result=%s)\n",
	       conn->proxy->worker->thread_id, inet_ntoa(conn->client.addr.sin_addr),
	       ntohs(conn->client.addr.sin_port), err < 0 ? strerror(error) : "ok");

	conn->proxy->worker->num_conn--;
	free(conn);
}

void zproxy_conn_reset_continue(struct ev_loop *loop, struct zproxy_conn *conn)
{
	conn->client.buf_sent = 0;
	free((char *)conn->client.resp_buf);
	conn->client.resp_buf = NULL;
	conn->client.resp_buf_len = 0;
}

void zproxy_conn_reset_state(struct ev_loop *loop, struct zproxy_conn *conn)
{
	// TODO: perhaps reset the stats here as well
	zproxy_conn_reset_continue(loop, conn);
	conn->client.buf_len = 0;
	free((char *)conn->client.buf_stash);
	conn->client.buf_stash = NULL;
	conn->client.buf_stash_len = 0;
	conn->client.req_len = 0;

	conn->backend.buf_len = 0;
	conn->backend.buf_sent = 0;
	free((char *)conn->backend.buf_stash);
	conn->backend.buf_stash = NULL;
	conn->backend.buf_stash_len = 0;
	conn->backend.resp_len = 0;
	conn->backend.sent = 0;
	conn->backend.recv = 0;
	conn->backend.pending = 0;
	conn->backend.reconnect = 0;

	ev_io_stop(loop, &conn->client.io);
	ev_io_set(&conn->client.io, conn->client.io.fd, EV_READ);
	ev_io_start(loop, &conn->client.io);

	ev_io_stop(loop, &conn->backend.io);
}

static int zproxy_conn_splice_setup(struct zproxy_conn *conn)
{
	int flags;

	if (conn->client.ssl_enabled ||
	    conn->backend.ssl_enabled)
		return 0;

	if (pipe(conn->splice_fds) < 0)
		return -1;

	fcntl(conn->splice_fds[0], F_SETPIPE_SZ, 30000);
	flags = fcntl(conn->splice_fds[0], F_GETFL);
	fcntl(conn->splice_fds[0], F_SETFL, flags | O_NONBLOCK);
	flags = fcntl(conn->splice_fds[1], F_GETFL);
	fcntl(conn->splice_fds[1], F_SETFL, flags | O_NONBLOCK);

	return 0;
}

static void zproxy_conn_splice_release(struct zproxy_conn *conn)
{
	if (conn->client.ssl_enabled ||
	    conn->backend.ssl_enabled)
		return;

	close(conn->splice_fds[0]);
	close(conn->splice_fds[1]);
	conn->splice_fds[0] = -1;
	conn->splice_fds[1] = -1;
}

#define MAX_BACKEND_RECONNECT	16

static int __zproxy_backend_reconnect(struct ev_loop *loop, struct zproxy_conn *conn)
{
	struct zproxy_backend backend;
	int ret;

	while (conn->backend.reconnect < MAX_BACKEND_RECONNECT) {
		conn->backend.reconnect++;

		memset(&backend, 0, sizeof(backend));
		ret = conn->proxy->handler->reconnect(loop, conn, 0, &backend);
		if (ret < 0)
			goto err_too_many;
		else if (ret == 0)
			return -1;

		ret = zproxy_conn_backend_connect(loop, conn, &backend);
		if (ret >= 0)
			break;
	}

	if (conn->backend.reconnect >= MAX_BACKEND_RECONNECT) {
		errno = EMLINK;
		ret = -1;
		goto err_too_many;
	}

	return 0;

err_too_many:
	return -1;
}

static bool zproxy_sockaddr_cmp(const struct sockaddr_in *cur_addr,
				const struct sockaddr_in *new_addr)
{
	return cur_addr->sin_family == new_addr->sin_family &&
	       cur_addr->sin_addr.s_addr == new_addr->sin_addr.s_addr &&
	       cur_addr->sin_port == new_addr->sin_port;
}

int zproxy_conn_backend_reset(struct ev_loop *loop,
			      struct zproxy_conn *conn,
			      const struct zproxy_backend *backend)
{
	struct sockaddr_in addr;
	socklen_t addrlen = sizeof(addr);
	int err;

	err = getpeername(conn->backend.io.fd, (struct sockaddr *)&addr, &addrlen);
	if (err < 0)
		return err;

	if (addrlen != sizeof(addr)) {
		errno = EINVAL;
		return -1;
	}

	if (zproxy_sockaddr_cmp(&addr, &backend->addr) &&
	    conn->backend.ssl_enabled == backend->ssl_enabled)
		return 0;

	zproxy_conn_backend_close(loop, conn);

	conn->backend.setup = false;
	conn->backend.connected = false;

	conn->backend.ssl_enabled = false;
	conn->backend.ssl = NULL;
	conn->backend.ssl_ctx = NULL;

	conn->backend.cfg = NULL;

	return 0;
}

void zproxy_io_update(struct ev_loop *loop, struct ev_io *io,
		      void (*cb)(struct ev_loop *loop, struct ev_io *io, int events),
		      int events)
{
	ev_io_stop(loop, io);
	ev_io_init(io, cb, io->fd, events);
	ev_io_start(loop, io);
}

void zproxy_backend_cb(struct ev_loop *loop, struct ev_io *io, int events)
{
	struct zproxy_conn *conn;
	int ret;
	conn = container_of(io, struct zproxy_conn, backend.io);

	if (events & EV_ERROR)
		return;
	ret = conn->proxy->handler->backend(loop, conn, events);
	if (ret <= 0)
		goto err_conn;

	return;
err_conn:
	zproxy_conn_release(loop, conn, ret);
}

static int zproxy_backend_reconnect(struct ev_loop *loop, struct zproxy_conn *conn)
{
	ev_timer_stop(loop, &conn->backend.timer);
	ev_io_stop(loop, &conn->backend.io);
	close(conn->backend.io.fd);
	zproxy_conn_splice_release(conn);
	conn->backend.setup = false;
	conn->stream->updateStats(NEW_CONN);
	if (__zproxy_backend_reconnect(loop, conn) < 0) {
		if (!conn->client.resp_buf)
			return -1;
	}

	return 0;
}

static void zproxy_conn_backend_timer_cb(struct ev_loop *loop, ev_timer *timer, int events)
{
	struct zproxy_conn *conn;

	conn = container_of(timer, struct zproxy_conn, backend.timer);

	syslog(LOG_ERR, "timeout request to backend %s:%hu\n",
	       inet_ntoa(conn->backend.addr.sin_addr),
	       ntohs(conn->backend.addr.sin_port));

	errno = ETIMEDOUT;
	if (conn->proxy->handler->timeout(loop, conn, events) < 0) {
		zproxy_conn_release(loop, conn, events);
		return;
	}
}

static void zproxy_backend_connect_cb(struct ev_loop *loop, struct ev_io *io, int events)
{
	struct zproxy_conn *conn;
	int len, ret;

	conn = container_of(io, struct zproxy_conn, backend.io);

	if (events & EV_ERROR)
		return;

	len = sizeof(conn->backend.addr);
	ret = connect(conn->backend.io.fd, (struct sockaddr *)&conn->backend.addr, len);
	if (ret < 0 && errno != EISCONN)
		goto reconnect;

	conn->backend.connected = true;

	ev_timer_stop(loop, &conn->backend.timer);
	ev_init(&conn->backend.timer, zproxy_conn_backend_timer_cb);
	conn->backend.timer.repeat = conn->backend.cfg->timer.backend;
	ev_timer_again(loop, &conn->backend.timer);

	if (conn->backend.ssl_enabled) {
		ret = zproxy_ssl_backend_init(conn);
		if (ret < 0)
			goto err_conn;

		zproxy_io_update(loop, &conn->backend.io, zproxy_backend_ssl_cb,
				 EV_WRITE);
	} else {
		zproxy_io_update(loop, &conn->backend.io, zproxy_backend_cb,
				 EV_WRITE);
	}

	conn->stream->updateStats(ESTABLISHED);

	return;

reconnect:
	if (zproxy_backend_reconnect(loop, conn) >= 0)
		return;
err_conn:
	zproxy_conn_release(loop, conn, ret);
}

static void zproxy_conn_connect_timer_cb(struct ev_loop *loop, ev_timer *timer, int events)
{
	struct zproxy_conn *conn;

	conn = container_of(timer, struct zproxy_conn, backend.timer);

	syslog(LOG_ERR, "timeout connect to backend %s:%hu\n",
	       inet_ntoa(conn->backend.addr.sin_addr),
	       ntohs(conn->backend.addr.sin_port));

	if (zproxy_backend_reconnect(loop, conn) >= 0)
		return;

	errno = ETIMEDOUT;
	if (conn->proxy->handler->timeout(loop, conn, events) < 0) {
		zproxy_conn_release(loop, conn, -1);
		return;
	}
}

int zproxy_conn_backend_connect(struct ev_loop *loop, struct zproxy_conn *conn,
				struct zproxy_backend *backend)
{
	int backend_sd, ret;
	if (zproxy_conn_splice_setup(conn) < 0)
		return -1;

	memcpy(&conn->backend.addr, &backend->addr, sizeof(backend->addr));
	conn->backend.cfg = backend->cfg;

	ret = zproxy_client_connect(&conn->backend.addr, &backend_sd, backend->cfg->nf_mark);
	if (ret < 0 && errno != EINPROGRESS) {
		zproxy_conn_splice_release(conn);
		if (backend_sd >= 0)
			close(backend_sd);

		return __zproxy_backend_reconnect(loop, conn);
	}

	conn->stream->updateStats(BCK_CONN);

	conn->backend.setup = true;
	conn->backend.ssl_enabled = backend->ssl_enabled;
	ev_io_init(&conn->backend.io, zproxy_backend_connect_cb, backend_sd, EV_WRITE);
	ev_io_start(loop, &conn->backend.io);

	ev_init(&conn->backend.timer, zproxy_conn_connect_timer_cb);
	conn->backend.timer.repeat = backend->cfg->timer.connect;
	ev_timer_again(loop, &conn->backend.timer);

	return 0;
}

void zproxy_client_cb(struct ev_loop *loop, struct ev_io *io, int events)
{
	struct zproxy_conn *conn;

	if (events & EV_ERROR)
		return;

	conn = container_of(io, struct zproxy_conn, client.io);

	conn->proxy->handler->client(loop, conn, events);
}

static void zproxy_conn_timer_cb(struct ev_loop *loop, ev_timer *timer, int events)
{
	struct zproxy_conn *conn;

	conn = container_of(timer, struct zproxy_conn, timer);

	syslog(LOG_ERR, "timeout request for client %s:%hu\n",
	       inet_ntoa(conn->client.addr.sin_addr),
	       ntohs(conn->client.addr.sin_port));

	errno = ETIMEDOUT;
	if (conn->proxy->handler->timeout(loop, conn, events) < 0) {
		zproxy_conn_release(loop, conn, events);
		return;
	}
}

static int zproxy_proxy_new_conn(struct ev_loop *loop, int sd,
				 const struct sockaddr_in *client_addr,
				 struct zproxy_proxy *proxy)
{
	struct zproxy_conn *conn;

	conn = (struct zproxy_conn *)calloc(1, sizeof(struct zproxy_conn));
	if (!conn)
		return -1;

	conn->client.buf = (char *)malloc(ZPROXY_BUFSIZ);
	if (!conn->client.buf)
		goto err_client_buf;

	conn->client.buf_siz = ZPROXY_BUFSIZ;

	conn->backend.buf = (char *)malloc(ZPROXY_BUFSIZ);
	if (!conn->backend.buf)
		goto err_backend_buf;

	conn->backend.buf_siz = ZPROXY_BUFSIZ;

	memcpy(&conn->client.addr, client_addr, sizeof(*client_addr));

	ev_init(&conn->timer, zproxy_conn_timer_cb);
	conn->timer.repeat = proxy->cfg->timer.client;

	ev_timer_again(loop, &conn->timer);

	conn->splice_fds[0] = -1;
	conn->splice_fds[1] = -1;
	conn->proxy = proxy;

	list_add_tail(&conn->list, &proxy->worker->conn_list);

	if (proxy->cfg->runtime.ssl_enabled) {
		conn->client.ssl = zproxy_ssl_client_init((zproxy_proxy_cfg *)proxy->cfg, sd);
		if (!conn->client.ssl)
			goto err_ssl_client;

		conn->client.ssl_enabled = true;
		ev_io_init(&conn->client.io, zproxy_client_ssl_cb, sd, EV_READ);
	} else {
		ev_io_init(&conn->client.io, zproxy_client_cb, sd, EV_READ);
	}

	proxy->worker->num_conn++;
	ev_io_start(loop, &conn->client.io);

	return 0;

err_ssl_client:
	list_del(&conn->list);
	ev_timer_stop(loop, &conn->timer);
err_backend_buf:
	free(conn->client.buf);
err_client_buf:
	free(conn);

	return -1;
}

void zproxy_proxy_accept_cb(struct ev_loop *loop, struct ev_io *io, int events)
{
	struct sockaddr_in client_addr;
	socklen_t addrlen = sizeof(client_addr);
	struct zproxy_proxy *proxy;
	int sd, flags;

	if (events & EV_ERROR)
		return;

	proxy = container_of(io, struct zproxy_proxy, io);

	sd = accept(io->fd, (struct sockaddr *)&client_addr, &addrlen);
	if (sd < 0) {
		syslog(LOG_ERR, "[%lx] cannot accept client connection: %s\n",
		       proxy->worker->thread_id, strerror(errno));
		return;
	}

	syslog(LOG_DEBUG, "[%lx] accepting client connection from %s:%hu",
	       proxy->worker->thread_id, inet_ntoa(client_addr.sin_addr),
	       htons(client_addr.sin_port));

	flags = fcntl(sd, F_GETFL);
	fcntl(sd, F_SETFL, flags | O_NONBLOCK);

	if (zproxy_proxy_new_conn(loop, sd, &client_addr, proxy) < 0) {
		close(sd);
		return;
	}
}

struct zproxy_proxy *zproxy_proxy_create(const struct zproxy_proxy_cfg *cfg,
					 struct zproxy_worker *worker,
					 const struct zproxy_handler *handler)
{
	struct zproxy_proxy *proxy;
	void *state;
	int sd;

	proxy = (struct zproxy_proxy *)calloc(1, sizeof(*proxy));
	if (!proxy)
		return NULL;

	proxy->cfg = cfg;
	proxy->handler = handler;
	proxy->worker = worker;

	sd = zproxy_socket_server_setup(&cfg->runtime.addr);
	if (sd < 0) {
		free(proxy);
		return NULL;
	}

	state = proxy->handler->init(proxy);
	if (!state) {
		zproxy_ssl_ctx_free(proxy->ssl);
		free(proxy);
		close(sd);
		return NULL;
	}

	proxy->state = state;
	proxy->cfg = cfg;

	ev_io_init(&proxy->io, zproxy_proxy_accept_cb, sd, EV_READ);

	return proxy;
}

void zproxy_proxy_destroy(struct zproxy_proxy *proxy)
{
	proxy->handler->fini(proxy);
	list_del(&proxy->list);
	close(proxy->io.fd);
	free(proxy);
}
