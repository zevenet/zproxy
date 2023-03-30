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
#include <sys/time.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <fcntl.h>
#include <syslog.h>
#include <ev.h>
#include <errno.h>
#include <assert.h>
#include <fcntl.h>

#include "proxy.h"
#include "http.h"
#include "list.h"
#include "state.h"
#include "zcu_log.h"

static uint32_t client_resp_buflen(const struct zproxy_conn *conn)
{
	return conn->client.resp_buf_len - conn->client.buf_sent;
}

static const char *client_resp_buf(const struct zproxy_conn *conn)
{
	return &conn->client.resp_buf[conn->client.buf_sent];
}

static uint32_t backend_buflen(const struct zproxy_conn *conn)
{
	return conn->backend.buf_len - conn->client.buf_sent;
}

static const char *backend_buf(const struct zproxy_conn *conn)
{
	return &conn->backend.buf[conn->client.buf_sent];
}

/*
 * zproxy_http_response_parser() is the HTTP response parser:
 *
 * - if it returns -1, then proxy sends a custom HTTP response to the client,
 *   which replaces the original HTTP response coming from the backend.
 * - if it returns 1, then the HTTP response parser accepts the HTTP response.
 *   ctx.resp_len tells the length of the HTTP response. The HTTP response
 *   parser might provide a new buffer containing a (mangled) HTTP response
 *   through ctx.buf.
 * - if it returns 0, then the HTTP response parser needs more of the HTTP
 *   response coming from the backend to decide what to do.
 *
 * If ctx.http_close is true, the proxy has to close the HTTP connection after
 * the HTTP response has been sent.
 */
static int zproxy_conn_recv_http_resp(struct ev_loop *loop,
				      struct zproxy_conn *conn,
				      uint32_t numbytes)
{
	struct zproxy_http_ctx ctx = {
		.cfg		= conn->proxy->cfg,
		.stream		= conn->stream,
		.state		= conn->proxy->state,
		.buf		= conn->backend.buf,
		.buf_len	= conn->backend.buf_len,
		.buf_tail_len	= numbytes,
		.buf_siz	= conn->backend.buf_siz,
		.from		= ZPROXY_HTTP_BACKEND,
		.addr		= &conn->client.addr,
	};
	int ret;

	ret = zproxy_http_response_parser(&ctx);
	if (ret < 0) {
		assert(ctx.resp_buf);
		conn->client.resp_buf = ctx.resp_buf;
		conn->client.resp_buf_len = strlen(ctx.resp_buf);

		ev_io_stop(loop, &conn->backend.io);
		conn->state = ZPROXY_CONN_SEND_HTTP_RESP;
		ev_io_stop(loop, &conn->client.io);
		ev_io_set(&conn->client.io, conn->client.io.fd, EV_WRITE);
		ev_io_start(loop, &conn->client.io);

		if (ctx.http_close)
			conn->client.close = true;
	} else if (ret > 0) {
		if (ctx.resp_len > 0) {
			if (ctx.buf != conn->backend.buf) {
				conn->backend.buf_stash = conn->backend.buf;
				conn->backend.buf_stash_len = conn->backend.buf_len;
				conn->backend.buf = (char *)ctx.buf;
				conn->backend.buf_len = ctx.buf_len;
				conn->backend.recv = ctx.buf_len;
			}
			conn->backend.resp_len = ctx.resp_len;
		}

		if (ctx.http_close)
			conn->client.close = true;
	}

	return ret;
}

static int zproxy_backend_read(struct ev_loop *loop, struct zproxy_conn *conn, int events)
{
	uint32_t numbytes;
	int ret = 0;

	ev_timer_again(loop, &conn->backend.timer);

	switch (conn->state) {
	case ZPROXY_CONN_PROXY_SPLICE:
		ret = zproxy_conn_backend_recv(loop, conn, &numbytes);
		if (ret < 0)
			return ret;
		else if (ret == 0)
			return 1;

		if (numbytes == 0) {
			if (backend_buflen(conn) > 0) {
				ev_io_stop(loop, &conn->backend.io);
				conn->client.shutdown = true;
				return 1;
			}
			return 0;
		}

		if (conn->backend.buf_len == 0) {
			ev_io_stop(loop, &conn->client.io);
			ev_io_set(&conn->client.io, conn->client.io.fd,
				  EV_READ | EV_WRITE);
			ev_io_start(loop, &conn->client.io);
		}

		conn->backend.recv += numbytes;
		conn->backend.buf_len += numbytes;

		if (conn->backend.buf_len >= conn->backend.buf_siz) {
			ev_io_stop(loop, &conn->backend.io);
			conn->backend.stopped = true;
		}
		break;
	case ZPROXY_CONN_RECV_HTTP_RESP:
		ret = zproxy_conn_backend_recv(loop, conn, &numbytes);
		if (ret < 0)
			return ret;
		else if (ret == 0)
			return 1;

		if (numbytes == 0) {
			if (backend_buflen(conn) > 0) {
				ev_io_stop(loop, &conn->backend.io);
				conn->client.shutdown = true;
				return 1;
			}
			return 0;
		}

		if (conn->backend.buf_len == 0) {
			ev_io_stop(loop, &conn->client.io);
			ev_io_set(&conn->client.io, conn->client.io.fd, EV_READ | EV_WRITE);
			ev_io_start(loop, &conn->client.io);
		}

		conn->backend.recv += numbytes;
		conn->backend.buf_len += numbytes;

		if (!conn->backend.resp_len ||
		    conn->backend.resp_len == UINT64_MAX) {
			ret = zproxy_conn_recv_http_resp(loop, conn, numbytes);
			if (ret <= 0)
				return 1;
		}

		if (conn->backend.buf_len >= conn->backend.buf_siz) {
			ev_io_stop(loop, &conn->backend.io);
			conn->backend.stopped = true;
		}
		break;
	case ZPROXY_CONN_SPLICE_HTTP_RESP:
		ret = splice(conn->backend.io.fd, NULL, conn->splice_fds[1],
			     NULL, 30000, SPLICE_F_MOVE | SPLICE_F_NONBLOCK);
		if (ret > 0) {
			conn->backend.pending += ret;
			conn->backend.recv += ret;
			/* Wake up client write side to send data. */
			ev_io_stop(loop, &conn->client.io);
			ev_io_set(&conn->client.io, conn->client.io.fd, EV_READ|EV_WRITE);
			ev_io_start(loop, &conn->client.io);
		} else if (ret < 0 && errno == EAGAIN) {
			/* splice has filled up the pipe, disable backend side
			 * until client catches up with pending data.
			 */
			conn->backend.stopped = true;
			ev_io_stop(loop, &conn->backend.io);
			ret = 1;
		} else if (ret == 0) {
			if (conn->backend.pending > 0) {
				ev_io_stop(loop, &conn->backend.io);
				conn->client.shutdown = true;
				return 1;
			}
		}
		break;
	default:
		syslog(LOG_ERR, "unexpected state in %s: %u", __func__, conn->state);
		break;
	}

	return ret;

}

static int zproxy_backend_write(struct ev_loop *loop, struct zproxy_conn *conn, int events)
{
	uint32_t numbytes;
	int ret = 0;

	ev_timer_again(loop, &conn->backend.timer);

	switch (conn->state) {
	case ZPROXY_CONN_PROXY_SPLICE:
		ret = zproxy_conn_backend_send(loop, conn, &numbytes);
		if (ret < 0)
			return ret;
		else if (ret == 0)
			return 1;

		conn->backend.buf_sent += numbytes;

		if (conn->backend.buf_sent < conn->client.buf_len) {
			if (!conn->client.stopped) {
				conn->client.stopped = true;
				ev_io_stop(loop, &conn->client.io);
			}
		} else {
			if (conn->client.stopped) {
				conn->client.stopped = false;
				ev_io_start(loop, &conn->client.io);
			}
			conn->backend.buf_sent = 0;
			conn->client.buf_len = 0;

			ev_io_stop(loop, &conn->backend.io);
			ev_io_set(&conn->backend.io, conn->backend.io.fd, EV_READ);
			ev_io_start(loop, &conn->backend.io);
		}
		break;
	case ZPROXY_CONN_RECV_HTTP_REQ:
		ret = zproxy_conn_backend_send(loop, conn, &numbytes);
		if (ret < 0)
			return ret;
		else if (ret == 0)
			return 1;

		conn->backend.buf_sent += numbytes;

		if (conn->backend.buf_sent < conn->client.buf_len) {
			if (!conn->client.stopped) {
				conn->client.stopped = true;
				ev_io_stop(loop, &conn->client.io);
			}
		} else {
			if (conn->client.stopped) {
				conn->client.stopped = false;
				ev_io_start(loop, &conn->client.io);
			}
			conn->backend.buf_sent = 0;
			conn->client.buf_len = 0;

			ev_io_stop(loop, &conn->backend.io);
			ev_io_set(&conn->backend.io, conn->backend.io.fd, EV_READ);
			ev_io_start(loop, &conn->backend.io);
		}

		conn->backend.sent += numbytes;

		if (conn->backend.sent >= conn->client.req_len) {
			conn->state = ZPROXY_CONN_RECV_HTTP_RESP;
			ev_io_stop(loop, &conn->backend.io);
			ev_io_set(&conn->backend.io, conn->backend.io.fd, EV_READ);
			ev_io_start(loop, &conn->backend.io);
		}
		break;
	default:
		syslog(LOG_ERR, "unexpected state in %s: %u", __func__, conn->state);
		break;
	}

	return ret;
}

static int zproxy_http_backend(struct ev_loop *loop, struct zproxy_conn *conn,
			       int events)
{
	if (events & EV_READ)
		return zproxy_backend_read(loop, conn, events);
	if (events & EV_WRITE)
		return zproxy_backend_write(loop, conn, events);

	return 0;
}

/*
 * zproxy_http_request_parser() is the HTTP request parser:
 *
 * - if it returns -1, then proxy sends a custom HTTP response to the client,
 *   before connecting to the backend. If ctx.http_continue is true, the proxy
 *   sends a HTTP continue response to the client.
 * - if it returns 1, then the HTTP response parser accepts the HTTP request.
 *   ctx.req_len specifies the length of the HTTP request. The HTTP parser might
 *   provide a new buffer containing the HTTP request through ctx.buf.
 * - if it returns 0, then the HTTP request parser needs more of the HTTP
 *   request coming from the client to decide what to do.
 *
 * The HTTP parser might update the private HTTP connection state (the
 * so-called stream object) anytime. This is private to the HTTP parsers, not
 * used by the core.
 */
static int zproxy_conn_recv_http_req(struct ev_loop *loop,
				     struct zproxy_conn *conn,
				     struct zproxy_backend *backend,
				     uint32_t numbytes)
{
	struct zproxy_http_ctx ctx = {
		.cfg		= conn->proxy->cfg,
		.stream		= conn->stream,
		.state		= conn->proxy->state,
		.buf		= conn->client.buf,
		.buf_len	= conn->client.buf_len,
		.buf_tail_len	= numbytes,
		.buf_siz	= conn->client.buf_siz,
		.from		= ZPROXY_HTTP_CLIENT,
		.addr		= &conn->client.addr,
		.backend	= backend,
	};
	int ret;

	ret = zproxy_http_request_parser(&ctx);

	if (ctx.stream != conn->stream)
		conn->stream = ctx.stream;

	if (ret < 0) {
		conn->client.resp_buf = ctx.resp_buf;
		conn->client.resp_buf_len = strlen(ctx.resp_buf);

		if (ctx.http_continue)
			conn->state = ZPROXY_CONN_SEND_HTTP_CONTINUE;
		else
			conn->state = ZPROXY_CONN_SEND_HTTP_RESP;

		ev_io_stop(loop, &conn->client.io);
		ev_io_set(&conn->client.io, conn->client.io.fd, EV_WRITE);
		ev_io_start(loop, &conn->client.io);

		return 0;
	} else if (ret == 0) {
		if (conn->client.buf_len >= conn->client.buf_siz &&
		    !conn->backend.connected)
			return -1;

		return ret;
	}

	if (ctx.buf != conn->client.buf) {
		conn->client.buf_stash = conn->client.buf;
		conn->client.buf_stash_len = conn->client.buf_len;
		conn->client.buf = (char *)ctx.buf;
		conn->client.buf_len = ctx.buf_len;
	}

	conn->client.req_len = ctx.req_len;

	return 1;
}

static bool zproxy_backend_is_set(const struct zproxy_backend *backend)
{
	return backend->addr.sin_family != AF_UNSPEC &&
	       backend->addr.sin_addr.s_addr != 0 &&
	       backend->addr.sin_port != 0;
}

static void zproxy_client_read(struct ev_loop *loop, struct zproxy_conn *conn, int events)
{
	struct zproxy_backend backend = {};
	uint32_t numbytes;
	int ret;

	ret = zproxy_conn_client_recv(loop, conn, &numbytes);
	if (ret < 0)
		goto err_close;
	else if (ret == 0)
		return;

	if (numbytes == 0)
		goto err_close;

	ev_timer_again(loop, &conn->timer);

	conn->client.buf_len += numbytes;

	switch (conn->state) {
	case ZPROXY_CONN_PROXY_SPLICE:
		if (conn->client.buf_len >= conn->client.buf_siz) {
			conn->client.stopped = true;
			ev_io_stop(loop, &conn->client.io);
		}

		ev_io_stop(loop, &conn->backend.io);
		ev_io_set(&conn->backend.io, conn->backend.io.fd,
			  EV_READ | EV_WRITE);
		ev_io_start(loop, &conn->backend.io);
		break;
	case ZPROXY_CONN_RECV_HTTP_REQ:
		ret = zproxy_conn_recv_http_req(loop, conn, &backend, numbytes);
		if (ret < 0)
			goto err_close;
		else if (ret == 0)
			return;

		if (conn->backend.connected && zproxy_backend_is_set(&backend)) {
			ret = zproxy_conn_backend_reset(loop, conn, &backend);
			if (ret < 0)
				goto err_close;
		}

		if (!conn->backend.connected) {
			ret = zproxy_conn_backend_connect(loop, conn, &backend);
			if (ret < 0) {
				if (conn->client.resp_buf)
					break;

				goto err_close;
			}
			conn->client.stopped = true;
			ev_io_stop(loop, &conn->client.io);
		} else {
			if (conn->client.buf_len >= conn->client.buf_siz) {
				conn->client.stopped = true;
				ev_io_stop(loop, &conn->client.io);
			}

			ev_io_stop(loop, &conn->backend.io);
			ev_io_set(&conn->backend.io, conn->backend.io.fd, EV_WRITE);
			ev_io_start(loop, &conn->backend.io);
		}
		break;
	default:
		syslog(LOG_ERR, "unexpected state in %s: %u", __func__, conn->state);
		break;
	}

	return;
err_close:
	zproxy_conn_release(loop, conn, ret);
}

static void zproxy_client_write(struct ev_loop *loop, struct zproxy_conn *conn, int events)
{
	uint32_t numbytes;
	int ret;

	ev_timer_again(loop, &conn->timer);

	switch (conn->state) {
	case ZPROXY_CONN_SEND_HTTP_CONTINUE:
	case ZPROXY_CONN_SEND_HTTP_RESP:
		ret = zproxy_conn_client_send(loop, client_resp_buf(conn),
					      client_resp_buflen(conn),
					      &numbytes, conn);
		if (ret < 0)
			goto err_close;
		else if (ret == 0)
			return;

		conn->client.buf_sent += numbytes;
		if (conn->client.buf_sent >= conn->client.resp_buf_len) {
			if (conn->client.close) {
				ret = 0;
				goto err_close;
			}
			if (conn->state == ZPROXY_CONN_SEND_HTTP_RESP) {
				zproxy_conn_reset_state(loop, conn);
			} else {
				zproxy_conn_reset_continue(loop, conn);
			}

			conn->state = ZPROXY_CONN_RECV_HTTP_REQ;
			ev_io_stop(loop, &conn->client.io);
			ev_io_set(&conn->client.io, conn->client.io.fd, EV_READ);
			ev_io_start(loop, &conn->client.io);
		}
		break;
	case ZPROXY_CONN_PROXY_SPLICE:
		ret = zproxy_conn_client_send(loop, backend_buf(conn),
					      backend_buflen(conn), &numbytes,
					      conn);
		if (ret < 0)
			goto err_close;
		else if (ret == 0)
			return;

		conn->client.buf_sent += numbytes;

		if (conn->client.buf_sent < conn->backend.buf_len) {
			ev_io_stop(loop, &conn->backend.io);
			conn->backend.stopped = true;
		} else {
			if (conn->client.shutdown) {
				ret = 0;
				goto err_close;
			}
			if (conn->backend.stopped) {
				conn->backend.stopped = false;
				ev_io_start(loop, &conn->backend.io);
			}
			conn->client.buf_sent = 0;
			conn->backend.buf_len = 0;

			ev_io_stop(loop, &conn->client.io);
			ev_io_set(&conn->client.io, conn->client.io.fd, EV_READ);
			ev_io_start(loop, &conn->client.io);
		}
		break;
	case ZPROXY_CONN_RECV_HTTP_RESP:
		ret = zproxy_conn_client_send(loop, backend_buf(conn),
					      backend_buflen(conn), &numbytes,
					      conn);
		if (ret < 0)
			goto err_close;
		else if (ret == 0)
			return;

		conn->client.buf_sent += numbytes;

		if (conn->client.buf_sent < conn->backend.buf_len) {
			ev_io_stop(loop, &conn->backend.io);
			conn->backend.stopped = true;
		} else {
			if (conn->client.shutdown) {
				ret = 0;
				goto err_close;
			}
			if (conn->backend.stopped) {
				conn->backend.stopped = false;
				ev_io_start(loop, &conn->backend.io);
			}
			conn->client.buf_sent = 0;
			conn->backend.buf_len = 0;

			ev_io_stop(loop, &conn->client.io);
			ev_io_set(&conn->client.io, conn->client.io.fd, EV_READ);
			ev_io_start(loop, &conn->client.io);

			if (!conn->client.ssl_enabled &&
			    !conn->backend.ssl_enabled &&
			     conn->backend.resp_len != UINT64_MAX)
				conn->state = ZPROXY_CONN_SPLICE_HTTP_RESP;
		}

		conn->client.sent += numbytes;

		if (conn->client.sent >= conn->backend.resp_len) {
			if (conn->client.close) {
				ret = 0;
				goto err_close;
			}
			zproxy_conn_reset_state(loop, conn);

			if (conn->stream && conn->stream->isTunnel()) {
				zcu_log_print_th(LOG_DEBUG, "Switching to WebSocket mode");
				conn->state = ZPROXY_CONN_PROXY_SPLICE;
			} else {
				conn->state = ZPROXY_CONN_RECV_HTTP_REQ;
			}
			ev_io_stop(loop, &conn->client.io);
			ev_io_set(&conn->client.io, conn->client.io.fd, EV_READ);
			ev_io_start(loop, &conn->client.io);
		}
		break;
	case ZPROXY_CONN_SPLICE_HTTP_RESP:
		ret = splice(conn->splice_fds[0], NULL, conn->client.io.fd,
			     NULL, 30000, SPLICE_F_MOVE | SPLICE_F_NONBLOCK);
		if (ret <= 0) {
			/* This should not ever happen: the client write side
			 * should not be awaken if there is no data in the pipe
			 * to be spliced to the client.
			 */
			if (errno == EAGAIN) {
				syslog(LOG_ERR, "pipe is unexpectedly empty!");
				return;
			}
			goto err_close;
		}

		if (conn->backend.stopped) {
			conn->backend.stopped = false;
			ev_io_start(loop, &conn->backend.io);
		}

		conn->backend.pending -= ret;
		if (conn->backend.pending == 0) {
			if (conn->client.shutdown) {
				ret = 0;
				goto err_close;
			}
			ev_io_stop(loop, &conn->client.io);
			ev_io_set(&conn->client.io, conn->client.io.fd, EV_READ);
			ev_io_start(loop, &conn->client.io);
		}

		conn->client.sent += ret;

		if (conn->client.sent >= conn->backend.resp_len) {
			if (conn->client.close) {
				ret = 0;
				goto err_close;
			}
			zproxy_conn_reset_state(loop, conn);
			conn->state = ZPROXY_CONN_RECV_HTTP_REQ;
			ev_io_stop(loop, &conn->client.io);
			ev_io_set(&conn->client.io, conn->client.io.fd, EV_READ);
			ev_io_start(loop, &conn->client.io);
		}
		break;
	default:
		syslog(LOG_ERR, "unexpected state in %s: %u", __func__, conn->state);
		break;
	}
	return;

err_close:
	zproxy_conn_release(loop, conn, ret);
}

void zproxy_http_client(struct ev_loop *loop, struct zproxy_conn *conn, int events)
{
	if (events & EV_READ)
		return zproxy_client_read(loop, conn, events);
	if (events & EV_WRITE)
		return zproxy_client_write(loop, conn, events);
}

static int zproxy_http_backend_reconnect(struct ev_loop *loop,
					 struct zproxy_conn *conn, int events,
					 struct zproxy_backend *backend)
{
	struct zproxy_http_ctx ctx = {
		.cfg		= conn->proxy->cfg,
		.stream		= conn->stream,
		.state		= conn->proxy->state,
		.buf		= conn->client.buf_stash,
		.buf_len	= conn->client.buf_stash_len,
		.buf_siz	= conn->client.buf_siz,
		.from		= ZPROXY_HTTP_CLIENT,
		.addr		= &conn->client.addr,
		.backend	= backend,
	};
	int ret;

	ret = zproxy_http_request_reconnect(&ctx);
	if (ret < 0) {
		if (ctx.resp_buf) {
			conn->client.resp_buf = ctx.resp_buf;
			conn->client.resp_buf_len = strlen(ctx.resp_buf);
			conn->state = ZPROXY_CONN_SEND_HTTP_RESP;
			ev_io_stop(loop, &conn->client.io);
			ev_io_set(&conn->client.io, conn->client.io.fd, EV_WRITE);
			ev_io_start(loop, &conn->client.io);

			return 0;
		}
		return ret;
	}

	if (ctx.buf != conn->client.buf_stash) {
		free(conn->client.buf);
		conn->client.buf = (char *)ctx.buf;
		conn->client.buf_len = ctx.buf_len;
		conn->client.req_len = ctx.req_len;
		assert(ctx.buf_len >= ctx.req_len);
	}

	return 1;
}

static void zproxy_http_error_response(struct zproxy_http_ctx *ctx,
				       struct ev_loop *loop,
				       struct zproxy_conn *conn)
{
	/* Ignore ctx.http_close, always close this connection, do not allow to
	 * recycle the existing connection if request has timeout or speaks no ssl.
	 */
	conn->client.close = true;

	assert(ctx->resp_buf);
	conn->client.resp_buf = ctx->resp_buf;
	conn->client.resp_buf_len = strlen(ctx->resp_buf);
	conn->state = ZPROXY_CONN_SEND_HTTP_RESP;

	ev_io_stop(loop, &conn->client.io);
	ev_io_set(&conn->client.io, conn->client.io.fd, EV_WRITE);
	ev_io_start(loop, &conn->client.io);
}

static int __zproxy_http_timeout(struct ev_loop *loop, struct zproxy_conn *conn)
{
	struct zproxy_http_ctx ctx = {
		.cfg		= conn->proxy->cfg,
		.stream		= conn->stream,
		.state		= conn->proxy->state,
		.buf		= conn->client.buf,
		.buf_len	= conn->client.buf_len,
		.buf_siz	= conn->client.buf_siz,
		.from		= ZPROXY_HTTP_CLIENT,
		.addr		= &conn->client.addr,
	};

	if (zproxy_http_event_timeout(&ctx) < 0)
		return -1;

	zproxy_http_error_response(&ctx, loop, conn);

	/* Stop backend, it might interfer with our custom timeout response. */
	if (conn->backend.connected &&
	    !conn->backend.stopped) {
		conn->backend.stopped = true;
		ev_io_stop(loop, &conn->backend.io);
	}

	return 0;
}

static int zproxy_http_timeout(struct ev_loop *loop, struct zproxy_conn *conn,
			       int events)
{
	/* timeout while trying to send custom response to client, close
	 * connection immediately.
	 */
	if (conn->client.resp_buf)
		return -1;

	/* already received partial response from the backend, it is too late,
	 * close connection immediately.
	 */
	if (conn->backend.connected &&
	    conn->backend.recv > 0)
		return -1;

	return __zproxy_http_timeout(loop, conn);
}

static int zproxy_http_nossl(struct ev_loop *loop, struct zproxy_conn *conn,
			     int events)
{
	struct zproxy_http_ctx ctx = {
		.cfg		= conn->proxy->cfg,
		.stream		= conn->stream,
		.state		= conn->proxy->state,
		.buf		= conn->client.buf,
		.buf_len	= conn->client.buf_len,
		.buf_siz	= conn->client.buf_siz,
		.from		= ZPROXY_HTTP_CLIENT,
		.addr		= &conn->client.addr,
	};

	zcu_log_print_th(LOG_WARNING, "HTTP client tried connecting to HTTPS listener.");

	if (zproxy_http_event_nossl(&ctx) < 0) {
		zcu_log_print_th(LOG_WARNING, "Failed to generate NoSSL response");
		return -1;
	}

	zproxy_http_error_response(&ctx, loop, conn);

	return 0;
}

static void *zproxy_http_init(struct zproxy_proxy *proxy)
{
	return zproxy_state_init(proxy->cfg);
}

static void zproxy_http_fini(struct zproxy_proxy *proxy)
{
	zproxy_state_purge((struct zproxy_proxy_cfg*)proxy->cfg);
}

struct zproxy_handler http_proxy = {
	.type		= ZPROXY_HTTP,
	.init		= zproxy_http_init,
	.fini		= zproxy_http_fini,
	.client		= zproxy_http_client,
	.backend	= zproxy_http_backend,
	.reconnect	= zproxy_http_backend_reconnect,
	.timeout	= zproxy_http_timeout,
	.nossl		= zproxy_http_nossl,
};
