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

#ifndef _ZPROXY_HTTP_H_
#define _ZPROXY_HTTP_H_

#include "proxy.h"

#include <stdint.h>

enum class RETURN_HTTP {
	// * http wants to send a error/redirect to client and closes the connection
	// * it will respond 100 continue to the client and next, it will receive the
	//		same request with the body appended. The HTTP lib should remove the
	//      100 continue header and send the client buffer to the backend
	PROXY_RESPONSE = -1,
	// The request/response is not complete, it needs to continue reading
	INCOMPLETE = 0,
	// The http managing was properly. If a ctx->backend is set, the core will connect
	SUCCESS = 1,
};

enum zproxy_http_origin {
	ZPROXY_HTTP_CLIENT	= 0,
	ZPROXY_HTTP_BACKEND,
};

struct zproxy_http_ctx {
	const struct zproxy_proxy_cfg	*cfg;
	HttpStream			*stream;
	void				*state;

	const char			*buf;
	uint32_t			buf_len;
	uint32_t			buf_siz;
	enum zproxy_http_origin		from;
	const struct sockaddr_in	*addr;
	uint64_t			resp_len;

	/* custom reply to client. */
	const char			*resp_buf;
	bool				http_continue;
	bool				http_close;

	/* selected backend to connect to. */
	struct zproxy_backend		*backend;
	uint64_t			req_len;
};

int zproxy_http_request_parser(struct zproxy_http_ctx *ctx);
int zproxy_http_request_reconnect(struct zproxy_http_ctx *ctx);
int zproxy_http_response_parser(struct zproxy_http_ctx *ctx);
int zproxy_http_event_timeout(struct zproxy_http_ctx *ctx);
int zproxy_http_event_nossl(struct zproxy_http_ctx *ctx);

#endif
