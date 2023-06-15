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

#include "http.h"
#include "http_handler.h"
#include "http_tools.h"
#include "pico_http_parser.h"
#include "service.h"
#include "session.h"
#include "state.h"
#include "zcu_common.h"
#include "zcu_http.h"
#include "zcu_log.h"

#include <stdlib.h>
#include <string.h>

static const char *request_method_str[] = {
	NULL,
	"ACL",
	"BASELINE-CONTROL",
	"BCOPY",
	"BDELETE",
	"BIND",
	"BMOVE",
	"BPROPFIND",
	"BPROPPATCH",
	"CHECKIN",
	"CHECKOUT",
	"CONNECT",
	"COPY",
	"DELETE",
	"GET",
	"HEAD",
	"LABEL",
	"LINK",
	"LOCK",
	"MERGE",
	"MKACTIVITY",
	"MKCALENDAR",
	"MKCOL",
	"MKREDIRECTREF",
	"MKWORKSPACE",
	"MOVE",
	"NOTIFY",
	"OPTIONS",
	"ORDERPATCH",
	"PATCH",
	"POLL",
	"POST",
	"PRI",
	"PROPFIND",
	"PROPPATCH",
	"PUT",
	"REBIND",
	"REPORT",
	"RPC_IN_DATA",
	"RPC_OUT_DATA",
	"SEARCH",
	"SUBSCRIBE",
	"TRACE",
	"UNBIND",
	"UNCHECKOUT",
	"UNLINK",
	"UNLOCK",
	"UNSUBSCRIBE",
	"UPDATE",
	"UPDATEREDIRECTREF",
	"VERSION-CONTROL",
	"X_MS_ENUMATTS",
	NULL,
};

void zproxy_http_set_header_rewrite_backend(struct zproxy_http_ctx *ctx)
{
	struct zproxy_http_parser *parser = ctx->parser;
	const struct zproxy_proxy_cfg *proxy = ctx->cfg;

	if (proxy->header.rw_host)
		zproxy_http_set_virtual_host_header(parser, inet_ntoa(ctx->backend->addr.sin_addr), INET_STR_SIZE);

	if (proxy->header.rw_destination)
		zproxy_http_set_destination_header(ctx);
}

static void zproxy_set_backend(struct zproxy_backend_cfg *backend, struct zproxy_http_ctx *ctx)
{
	memcpy(&ctx->backend->addr, &backend->runtime.addr, sizeof(backend->runtime.addr));
	ctx->backend->ssl_enabled = backend->runtime.ssl_enabled;
	ctx->backend->cfg = backend;
	zproxy_http_set_header_rewrite_backend(ctx);
}

static int zproxy_http_validate_max_request(struct zproxy_http_ctx *ctx)
{
	const struct zproxy_proxy_cfg *proxy = ctx->cfg;
	struct zproxy_http_parser *parser = ctx->parser;

	if (proxy->max_req > 0 &&
		ctx->buf_len > proxy->max_req &&
		!strncmp(parser->req.method, request_method_str[RPC_IN_DATA], parser->req.method_len) &&
		!strncmp(parser->req.method, request_method_str[RPC_OUT_DATA], parser->req.method_len))
		return 0;

	return 1;
}

int zproxy_http_request_reconnect(struct zproxy_http_ctx *ctx)
{
	struct zproxy_http_parser *parser = ctx->parser;
	zproxy_backend_cfg *backend;
	char  *buf = nullptr;

	// TODO: set down

	// clear sessions if they exist
	{
		const struct zproxy_http_state *state =
			(struct zproxy_http_state*)ctx->state;
		struct zproxy_sessions *sessions =
			zproxy_state_get_service_sessions(parser->service_cfg->name,
							  &state->services);
		zproxy_session_delete_backend(sessions, &ctx->backend->addr);
	}

	// getting a new backend
	backend = zproxy_service_select_backend(ctx);
	if (backend == nullptr) {
		zproxy_http_event_reply_error(ctx, WS_HTTP_503);
		return -1;
	}

	zproxy_set_backend(backend, ctx);

	if (ctx->buf_len == 0) {
		zproxy_http_event_reply_error(ctx, WS_HTTP_500);
		return -1;
	}
	ctx->buf = buf;
	ctx->buf_tail_len = ctx->buf_len;

	return 0;
}

static enum RETURN_HTTP zproxy_http_request_head_rcv_parse(struct zproxy_http_ctx *ctx)
{
	struct zproxy_http_parser *parser = ctx->parser;
	int ret;

	if (!parser->req.last_length) {
		parser->req.buf_cpy = (const char *) malloc(ctx->buf_siz);
		parser->req.buf_cpy_siz = ctx->buf_siz;
		if (!parser->req.buf_cpy) {
			return PROXY_RESPONSE;
		}
	}

	parser->req.buf_cpy_len = sprintf((char *)parser->req.buf_cpy + parser->req.buf_cpy_len, "%s", ctx->buf);
	ret = phr_parse_request(parser->req.buf_cpy, parser->req.buf_cpy_len,
				(const char **)&parser->req.method,
				&parser->req.method_len,
				(const char **)&parser->req.path,
				&parser->req.path_len,
				&parser->req.minor_version,
				parser->req.headers, &parser->req.num_headers,
				parser->req.last_length);

	parser->req.last_length = parser->req.buf_cpy_len;
	if (ret > 0) {
		parser->req.body = parser->req.buf_cpy + ret;
		parser->req.body_len = parser->req.buf_cpy_len - ret;
		return RETURN_HTTP::SUCCESS;
	}

	if (ret == -1)
		return RETURN_HTTP::PROXY_RESPONSE;

	return RETURN_HTTP::INCOMPLETE;
}

static size_t zproxy_http_request_send_to_backend(struct zproxy_http_ctx *ctx)
{
	struct zproxy_http_parser *parser = ctx->parser;
	size_t i;
	size_t len = 0;
	char *path = parser->req.path_mod ? parser->req.path_repl :
		parser->req.path;
	size_t path_len = parser->req.path_mod ? parser->req.path_repl_len :
		parser->req.path_len;
	size_t body_len = 0;
	char *buf;

	buf = (char *) calloc(ctx->buf_siz, sizeof(char));
	if (!buf)
		return -1;

	len = sprintf(buf, "%.*s %.*s HTTP/1.%d%s",
		      (int)parser->req.method_len, parser->req.method,
		      (int)path_len, path, parser->req.minor_version,
		      HTTP_LINE_END);

	// free memory allocated for replacement path once used
	if (parser->req.path_mod)
		free(parser->req.path_repl);

	if (parser->virtual_host_hdr.value_len) {
		len += sprintf(buf + len, "%.*s",
			       (int)parser->virtual_host_hdr.line_size,
			       parser->virtual_host_hdr.name);
	}

	for (i = 0; i < parser->req.num_headers; i++) {
		if (parser->req.headers[i].header_off)
			continue;

		len += sprintf(buf + len, "%.*s",
			       (int)parser->req.headers[i].line_size,
			       parser->req.headers[i].name);
	}

	len += sprintf(buf + len, "%s", HTTP_LINE_END);

	parser->req.len = len + parser->req.content_len;

	if (parser->req.body_len) {
		body_len = parser->req.body_len;
		if (len + body_len > ctx->buf_siz) {
			body_len = ctx->buf_siz - len;
			ctx->buf_tail_len = parser->req.body_len - body_len;
			parser->req.body_len -= parser->req.body_len - body_len;
		}

		len += sprintf(buf + len, "%.*s", (int)body_len,
			       parser->req.body);
	}

	ctx->buf = buf;
	ctx->buf_len = len;
	ctx->req_len = parser->req.len;

	zcu_log_print_th(LOG_DEBUG, "%.*s", ctx->buf_len, ctx->buf);

	return len;
}

static int zproxy_http_direct_proxy_reply(struct zproxy_http_parser *parser)
{
	return (parser->state == HTTP_PARSER_STATE::CLOSE ||
		parser->state == HTTP_PARSER_STATE::ERROR ||
		parser->state == HTTP_PARSER_STATE::WAIT_100_CONT);
}

static size_t zproxy_http_response_send_to_client(struct zproxy_http_ctx *ctx)
{
	struct zproxy_http_parser *parser = ctx->parser;
	size_t i;
	uint64_t len;
	char *buf;

	buf = (char *) malloc(SRV_MAX_HEADER + CONFIG_MAXBUF);
	if (!buf)
		return -1;

	len = sprintf(buf,
			"HTTP/1.%d %d %.*s" HTTP_LINE_END,
			parser->res.minor_version,
			parser->res.status_code,
			(int)parser->res.message_len,
			parser->res.message);

	for (i = 0; i <= parser->res.num_headers; i++) {
		if (parser->res.headers[i].header_off)
			continue;

		len += sprintf(buf + len, "%.*s",
				(int)parser->res.headers[i].line_size,
				parser->res.headers[i].name);
	}
	len += sprintf(buf + len, "%s", HTTP_LINE_END);

	if (parser->chunk_state == CHUNKED_ENABLED) {
		parser->res.len = len + parser->res.body_len;
		memcpy(buf + len, parser->res.body, parser->res.body_len);
		len += parser->res.body_len;
	} else {
		parser->res.len = len + parser->res.content_len;
		memcpy(buf + len, parser->res.body, parser->res.content_len);
		len += parser->res.content_len;
	}

	zcu_log_print_th(LOG_DEBUG, "%.*s", (int)len, buf);

	if (zproxy_http_direct_proxy_reply(parser)) {
		ctx->resp_len = len;
		ctx->resp_buf = buf;
		ctx->buf = NULL;
	} else {
		ctx->resp_len = parser->res.len;
		//~ ctx->resp_buf = NULL;
		ctx->buf_len = len;
		ctx->buf = buf;
		ctx->buf_tail_len = len;
	}
	return len;
}

static int zproxy_http_event_reply_redirect(struct zproxy_http_ctx *ctx,
					    enum ws_responses code,
					    const char *url)
{
	const struct zproxy_proxy_cfg *proxy = ctx->cfg;
	struct zproxy_http_parser *parser;
	const char *custom_msg;
	char custom_msg_len[MAX_HEADER_VALUE];

	if (!proxy)
		return -1;

	parser = ctx->parser;

	parser->res.num_headers = 0;
	parser->res.minor_version = parser->req.minor_version;
	parser->res.status_code = ws_to_http(code);
	parser->res.message = (char *)ws_str_responses[code] + 4;
	parser->res.message_len = strlen(parser->res.message);

	zproxy_stats_listener_inc_code((struct zproxy_http_state*)ctx->state,
				       ws_to_http(code));

	zproxy_http_add_header(parser->res.headers,
			       &parser->res.num_headers,
			       http_headers_str[CONTENT_TYPE],
			       CONTENTTYPE_HEADER_SIZE, "text/html", 9);

	custom_msg = zproxy_cfg_get_errmsg(&proxy->error.err_msgs,
					   ws_to_http(code));
	if (!custom_msg || !custom_msg[0]) {
		char *tmp_buf = (char*)calloc(ZCU_DEF_BUFFER_SIZE, sizeof(char));
		snprintf(tmp_buf, ZCU_DEF_BUFFER_SIZE,
			"<html><head><title>Redirect</title></"
			"head><body><h1>Redirect</h1><p>You "
			"should go to <a href=%s>%s</a></p></body></html>",
			url, url);
		custom_msg = tmp_buf;
	}
	sprintf(custom_msg_len, "%d", (int)strlen(custom_msg));
	zproxy_http_add_header(parser->res.headers, &parser->res.num_headers,
			       http_headers_str[CONTENT_LENGTH],
			       CONTENTLEN_HEADER_SIZE, custom_msg_len,
			       strlen(custom_msg_len));
	parser->res.body = custom_msg;

	zproxy_http_add_header(parser->res.headers, &parser->res.num_headers,
			       http_headers_str[LOCATION], LOCATION_HEADER_SIZE,
			       url, strlen(url));

	// Process the headers as a response
	parser->state = RESP_HEADER_RCV;
	zproxy_http_handle_response_headers(ctx);
	// Then set to close the connection after redirect
	parser->state = HTTP_PARSER_STATE::CLOSE;
	zproxy_http_response_send_to_client(ctx);

	return 1;
}

static int zproxy_http_event_reply_redirect_response(struct zproxy_http_ctx *ctx)
{
	struct zproxy_http_parser *parser = ctx->parser;
	struct zproxy_backend_redirect *redirect =
		&parser->service_cfg->redirect;
	enum ws_responses code = http_to_ws(redirect->be_type);
	char buf[MAX_HEADER_LEN] = { 0 };
	char new_url[MAX_HEADER_LEN] = { 0 };
	struct matcher *current, *next;

	snprintf(new_url, MAX_HEADER_LEN, "%s", redirect->url);
	if (redirect->redir_macro) {
		str_replace_str(buf, redirect->url, strlen(redirect->url),
				MACRO_VHOST, MACRO_VHOST_LEN,
				(char*)parser->virtual_host_hdr.value,
				parser->virtual_host_hdr.value_len);
		strncpy(new_url, buf, MAX_HEADER_LEN);
	}

	switch (redirect->redir_type) {
	case 1: { // dynamic
		list_for_each_entry_safe(current, next,
					 &parser->service_cfg->runtime.req_url,
					 list) {
			if (str_replace_regexp(buf, parser->req.path,
					       parser->req.path_len,
					       &current->pat, new_url) != -1) {
				strncpy(new_url, buf, MAX_HEADER_LEN);
			}
		}
		break;
	}
	case 2: { // append
		strncat(new_url, parser->req.path, parser->req.path_len);
		break;
	}
	default:
		break;
	}

	return zproxy_http_event_reply_redirect(ctx, code, new_url);
}

static int zproxy_http_request_100_cont(struct zproxy_http_ctx *ctx)
{
	struct zproxy_http_parser *parser = ctx->parser;

	parser->res.num_headers = 0;
	parser->res.minor_version = parser->req.minor_version;
	parser->res.status_code = ws_to_http(WS_HTTP_100);
	parser->res.message = (char *)ws_str_responses[WS_HTTP_100] + 4;
	parser->res.message_len = strlen(parser->res.message);

	zproxy_http_handle_response_headers(ctx);
	zproxy_http_response_send_to_client(ctx);

	return 1;
}

static int zproxy_http_request_head_rcv(struct zproxy_http_ctx *ctx)
{
	struct zproxy_backend_cfg *backend;
	struct zproxy_http_parser *parser = ctx->parser;
	RETURN_HTTP parse_status;
	size_t len;

	parse_status = zproxy_http_request_head_rcv_parse(ctx);

	if (parse_status == RETURN_HTTP::INCOMPLETE) {
		if (ctx->buf_len >= ctx->buf_siz) {
			zproxy_http_event_reply_error(ctx, WS_HTTP_414);
			return -1;
		}
		// keep reading from client
		return 0;
	}

	if (parse_status == RETURN_HTTP::PROXY_RESPONSE) {
		if (ctx->buf_len >= ctx->buf_siz)
			zproxy_http_event_reply_error(ctx, WS_HTTP_414);
		else
			zproxy_http_event_reply_error(ctx, WS_HTTP_400);
		return -1;
	}

	zproxy_service_select(ctx);
	if (!parser->service_cfg) {
		zproxy_http_event_reply_error(ctx, WS_HTTP_503);
		return -1;
	}

	if (!list_empty(&parser->service_cfg->runtime.req_rw_url))
		zproxy_http_rewrite_url(parser);

	if (!zproxy_http_validate_max_request(ctx)) {
		zproxy_http_event_reply_error(ctx, WS_HTTP_400);
		return -1;
	}

	if (zproxy_http_handle_request_headers(ctx)) {
		zproxy_http_event_reply_error(ctx, WS_HTTP_501);
		return -1;
	}

	// TODO: Expect Body? Populate parser->req.body

	// TODO: check WAF Req Headers

	if (parser->service_cfg->redirect.enabled) {
		zproxy_http_event_reply_redirect_response(ctx);
		return -1;
	}

	backend = zproxy_service_select_backend(ctx);
	if (backend == nullptr) {
		zproxy_http_event_reply_error(ctx, WS_HTTP_503);
		return -1;
	}
	zproxy_set_backend(backend, ctx);

	if (parser->expect_100_cont_hdr) {
		parser->state = WAIT_100_CONT;
		ctx->http_continue = true;
		zproxy_http_request_100_cont(ctx);
		return -1;
	}

	if (zproxy_http_request_send_to_backend(ctx) == 0) {
		zproxy_http_event_reply_error(ctx, WS_HTTP_500);
		return -1;
	}

	ctx->buf_tail_len = ctx->buf_len;

	// TODO: manage body
	// TODO: check WAF body

	// TODO: update ctx->req_len, ctx->buf, ctx->buf_len
	// TODO: set new state

	len = parser->req.content_len - parser->req.body_len;
	if (len < 0) {
		zproxy_http_event_reply_error(ctx, WS_HTTP_500);
		return -1;
	}

	if (parser->chunk_state == CHUNKED_ENABLED || (len > 0))
		parser->state = HTTP_PARSER_STATE::REQ_BODY_RCV;
	else
		parser->state = HTTP_PARSER_STATE::RESP_HEADER_RCV;

	return 1;
}

static int zproxy_http_request_body_rcv(struct zproxy_http_ctx *ctx)
{
	struct zproxy_http_parser *parser = ctx->parser;
	/*size_t len = 0;*/

	ctx->req_len = parser->req.len;
	ctx->buf_tail_len = 0;

	// TODO WAF (CAREFUL WITH PARTIAL MATCHES)
	return 1;
}

int zproxy_http_request_parser(struct zproxy_http_ctx *ctx)
{
	int ret = 1;

	if (!zcu_log_prefix[0]) {
		char prefix[CONFIG_IDENT_MAX+4] = {0};
		sprintf(prefix, "[f:%s]", ctx->cfg->name);
		zcu_log_set_prefix(prefix);
	}

	if (!ctx->parser) {
		if (!(ctx->parser = zproxy_http_parser_alloc())) {
			zcu_log_print(LOG_ERR, "unable to create http parser");
			return -1;
		}
		ctx->parser->http_state =
			zproxy_state_getref((struct zproxy_http_state*)ctx->state);
	}


	if (!ctx->parser)
		return -1;

	//~ TODO: streamLogDebug(ctx->stream, "->-> {bytes:%lu} %.*s", ctx->buf_len, ctx->buf_len, ctx->buf);
	zproxy_http_update_stats(ctx->parser, ctx->backend->cfg, NEW_CONN);

	switch (ctx->parser->state) {
	case HTTP_PARSER_STATE::CLOSE:
		return -1;
		break;
	case HTTP_PARSER_STATE::TUNNEL:
		return 1;
		break;
	case HTTP_PARSER_STATE::RESP_BODY_RCV:
		ctx->parser->state = HTTP_PARSER_STATE::REQ_HEADER_RCV;
		break;
	case HTTP_PARSER_STATE::REQ_HEADER_RCV:
		ret = zproxy_http_request_head_rcv(ctx);
		break;
	case HTTP_PARSER_STATE::WAIT_100_CONT:
		ret = zproxy_http_request_100_cont(ctx);
		break;
	case HTTP_PARSER_STATE::REQ_BODY_RCV:
		ret = zproxy_http_request_body_rcv(ctx);
		break;
	default:
		//~ TODO: streamLogMessage(ctx->stream, "Request status not expected %s", ctx->stream->getState());
		return -1;
	}

	//~ TODO: if (ctx->buf) {
		//~ streamLogDebug(ctx->stream, ">>>> {bytes:%lu/%lu} %.*s",
			       //~ ctx->buf_len, ctx->req_len, ctx->buf_len, ctx->buf);
	//~ }

	//~ if (ret < 0)
		//~ zproxy_http_parser_reset(ctx->parser);

	return ret;
}

static enum RETURN_HTTP zproxy_http_response_head_rcv_parse(struct zproxy_http_ctx *ctx)
{
	struct zproxy_http_parser *parser = ctx->parser;
	int ret;

	if (!parser->res.last_length) {
		parser->res.buf_cpy = (const char*) malloc(ctx->buf_len + 1);
		parser->res.buf_cpy_siz = ctx->buf_siz;
		if (!parser->res.buf_cpy)
			return PROXY_RESPONSE;
	}
	memcpy((void*)(parser->res.buf_cpy + parser->res.buf_cpy_len), ctx->buf,
	       ctx->buf_len);
	parser->res.buf_cpy_len = ctx->buf_len;
	free((char *)ctx->buf);
	ctx->buf_len = 0;

	ret = phr_parse_response(parser->res.buf_cpy, parser->res.buf_cpy_len,
				 &parser->res.minor_version,
				 &parser->res.status_code,
				 (const char**)&parser->res.message,
				 &parser->res.message_len, parser->res.headers,
				 &parser->res.num_headers,
				 parser->res.last_length);

	parser->res.last_length = parser->res.buf_cpy_len;
	if (ret > 0) {
		parser->res.body = parser->res.buf_cpy + ret;
		parser->res.body_len = parser->res.buf_cpy_len - ret;
		return RETURN_HTTP::SUCCESS;
	}

	if (ret == -1)
		return RETURN_HTTP::PROXY_RESPONSE;

	return RETURN_HTTP::INCOMPLETE;
}

int zproxy_http_response_parser(struct zproxy_http_ctx *ctx)
{
	struct zproxy_http_parser *parser = ctx->parser;
	enum RETURN_HTTP state;
	size_t len;

	//~ TODO: streamLogDebug(ctx->stream, "<-<- {bytes:%lu} %.*s", ctx->buf_len, ctx->buf_len, ctx->buf);

	switch (parser->state) {
	case HTTP_PARSER_STATE::TUNNEL: {
		//~ streamLogDebug(ctx->stream, "tunnel: forwarding response");
		return 1;
		break;
	}
	case HTTP_PARSER_STATE::REQ_BODY_RCV: {
		//~ ctx->stream->setState(HTTP_STATE::RESP_HEADER_RCV);
		//~ state = ctx->stream->getState();
		break;
	}
	case HTTP_PARSER_STATE::RESP_HEADER_RCV: {
		state = zproxy_http_response_head_rcv_parse(ctx);

		/* Return 0 if you want core to keep reading data from client. */
		if (state == RETURN_HTTP::INCOMPLETE)
			return 0;

		if (state == RETURN_HTTP::PROXY_RESPONSE) {
			zproxy_http_event_reply_error(ctx, WS_HTTP_500);
			return -1;
		}

		// TODO: check WAF response headers

		if (zproxy_http_handle_response_headers(ctx)) {
			zproxy_http_event_reply_error(ctx, WS_HTTP_501);
			return -1;
		}

		if ((len = zproxy_http_response_send_to_client(ctx)) == 0) {
			zproxy_http_event_reply_error(ctx, WS_HTTP_500);
			return -1;
		}

		ctx->buf_tail_len = ctx->buf_len;

		// TODO: manage body
		// TODO: check WAF body

		// TODO: update ctx->req_len, ctx->buf, ctx->buf_len
		// TODO: set new state

		//~ len = parser->res.len - len;
		parser->res.len -= len;
		if (parser->res.len < 0) {
			zproxy_http_event_reply_error(ctx, WS_HTTP_500);
			return -1;
		}

		zproxy_stats_backend_inc_code(parser->http_state,
					      ctx->backend->cfg,
					      parser->res.status_code);

		if (parser->chunk_state == CHUNKED_ENABLED) {
			ssize_t res;
			char *buf_cpy;
			size_t buf_cpy_len;

			parser->chunked_decoder = { 0 };

			buf_cpy = strndup(parser->res.body,
					  parser->res.body_len);
			buf_cpy_len = parser->res.body_len;
			res = phr_decode_chunked(&parser->chunked_decoder,
						 buf_cpy, &buf_cpy_len);
			free(buf_cpy);

			if (res == -2) {
				zcu_log_print_th(LOG_DEBUG, "Continue chunked");
				parser->state = HTTP_PARSER_STATE::RESP_BODY_RCV;
			} else if (res == -1) {
				zproxy_http_event_reply_error(ctx, WS_HTTP_500);
				zcu_log_print_th(LOG_WARNING,
						 "Error parsing chunked data.");
				return -1;
			} else {
				zcu_log_print_th(LOG_DEBUG, "Last chunk found");
				parser->chunk_state = CHUNKED_LAST_CHUNK;
				parser->state = HTTP_PARSER_STATE::CLOSE;
				ctx->http_close = true;
			}
			//~ ctx->resp_len = ;
		} else if (parser->expect_100_cont_hdr &&
			   parser->res.status_code == 100) {
			parser->state = REQ_BODY_RCV;
		} else {
			if (parser->websocket) {
				parser->state = TUNNEL;
			} else if (zproxy_http_expect_new_req(parser)) {
				zcu_log_print_th(LOG_DEBUG, "New request is expected");
				parser->state = REQ_HEADER_RCV;
			} else {
				zcu_log_print_th(LOG_DEBUG, "New request is NOT expected");
				parser->state = CLOSE;
				ctx->http_close = true;
				return 1;
			}
		}
		//~ TODO: stream->logSuccess();
		break;
	}
	case HTTP_PARSER_STATE::RESP_BODY_RCV: {
		// TODO: add to body
		//~ ctx->stream->response.message = const_cast<char *>(&ctx->buf[ctx->buf_len - ctx->buf_tail_len]);
		//~ ctx->stream->response.message_length = ctx->buf_tail_len;

		//~ ctx->buf_len = parser->res.buf_cpy_len;
		ctx->resp_len = parser->res.buf_cpy_len;
		parser->res.len -= parser->res.buf_cpy_len;
		ctx->buf_tail_len = 0;

		// TODO WAF (CAREFUL WITH PARTIAL MATCHES)
		break;
	}
	default: {
		// TODO: ctx->stream->getStateTracer();
		//~ streamLogMessage(ctx->stream, "no valid state %s", stream->getStateString(state));
		return -1;
	}
	}

	//~ ctx->resp_len = ctx->res.buf_cpy_len;
	//ctx->resp_len = ctx->stream->response.getBufferRewritedLength();

	zcu_log_print_th(LOG_DEBUG, "<<<< {bytes:%lu/%lu} %.*s", ctx->buf_len,
			 ctx->resp_len, ctx->buf_len, ctx->buf);
	return 1;
}

int zproxy_http_event_timeout(struct zproxy_http_ctx *ctx)
{
	// TODO: clear sessions if they exist
	//~ zproxy_session_delete_backend(stream->session, &stream->backend_config->runtime.addr);

	// TODO: did the client already send us a full http request? If not
	//	 better return -1 to close connection immediately?

	zproxy_http_event_reply_error(ctx, WS_HTTP_504);
	return 0;
}

int zproxy_http_event_reply_error(struct zproxy_http_ctx *ctx, enum ws_responses code)
{
	const struct zproxy_proxy_cfg *proxy = ctx->cfg;
	struct zproxy_http_parser *parser = ctx->parser;
	const char *custom_msg;
	char custom_msg_len[MAX_HEADER_VALUE];

	if (!proxy)
		return -1;

	parser->res.num_headers = 0;
	parser->res.minor_version = parser->req.minor_version;
	parser->res.status_code = ws_to_http(code);
	parser->res.message = (char *)ws_str_responses[code] + 4;
	parser->res.message_len = strlen(parser->res.message);

	zproxy_stats_listener_inc_code((struct zproxy_http_state*)ctx->state,
				       ws_to_http(code));

	custom_msg = zproxy_cfg_get_errmsg(&proxy->error.err_msgs,
					   ws_to_http(code));
	if (!custom_msg || !custom_msg[0]) {
		zproxy_http_add_header(parser->res.headers,
			&parser->res.num_headers, http_headers_str[CONTENT_LENGTH],
				CONTENTLEN_HEADER_SIZE, "0", 1);
		parser->res.body = NULL;
	} else {
		zproxy_http_add_header(parser->res.headers,
				&parser->res.num_headers, http_headers_str[CONTENT_TYPE],
				CONTENTTYPE_HEADER_SIZE, "text/html", 9);
		sprintf(custom_msg_len, "%d", (int)strlen(custom_msg));
		zproxy_http_add_header(parser->res.headers,
			&parser->res.num_headers, http_headers_str[CONTENT_LENGTH],
				CONTENTLEN_HEADER_SIZE, custom_msg_len, strlen(custom_msg_len));
		parser->res.body = custom_msg;
	}

	zproxy_http_add_header(parser->res.headers,
			&parser->res.num_headers, http_headers_str[EXPIRES],
			EXPIRES_HEADER_SIZE, "now", 3);
	zproxy_http_add_header(parser->res.headers,
			&parser->res.num_headers, http_headers_str[PRAGMA],
			PRAGMA_HEADER_SIZE, "no-cache", 8);
	zproxy_http_add_header(parser->res.headers,
			&parser->res.num_headers, http_headers_str[SERVER],
			SERVER_HEADER_SIZE, "zproxy", 6);
	zproxy_http_add_header(parser->res.headers,
			&parser->res.num_headers, http_headers_str[CACHE_CONTROL],
			CACHECONTROL_HEADER_SIZE, "no-cache,no-store", 17);

	parser->state = HTTP_PARSER_STATE::CLOSE;
	zproxy_http_handle_response_headers(ctx);
	zproxy_http_response_send_to_client(ctx);

	return 0;
}

int zproxy_http_event_nossl(struct zproxy_http_ctx *ctx)
{
	const struct zproxy_proxy_cfg *proxy = ctx->cfg;
	enum ws_responses code;
	const char *url;
	int ret;

	if (!(ctx->parser = zproxy_http_parser_alloc())) {
		ctx->parser->http_state =
			zproxy_state_getref((struct zproxy_http_state*)ctx->state);
		zcu_log_print_th(LOG_ERR, "OOM when allocating parser.");
		return -1;
	}

	if (proxy->error.nosslredirect_url[0]) {
		code = proxy->error.nosslredirect_code;
		url = proxy->error.nosslredirect_url;
		ret = zproxy_http_event_reply_redirect(ctx, code, url);
	} else {
		code = proxy->error.errnossl_code;
		ret = zproxy_http_event_reply_error(ctx, code);
	}

	return ret;
}
