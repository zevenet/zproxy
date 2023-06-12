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
#include "service.h"
#include "http_tools.h"
#include "zcu_http.h"
#include "zcu_log.h"

#include <stdlib.h>

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
		zproxy_http_set_destination_header(); // TODO
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

static int zproxy_http_event_reply_redirect_response(struct zproxy_http_ctx *ctx)
{
/*	TODO: rewrite like zproxy_http_event_reply_error().
		  call to zproxy_http_set_redirect_response()
	snprintf(body, ZCU_DEF_BUFFER_SIZE,
		"<html><head><title>Redirect</title></"
		"head><body><h1>Redirect</h1><p>You "
		"should go to <a href=%s>%s</a></p></body></html>",
		safe_url, safe_url);

	ctx->resp_buf = (char *)calloc(CONFIG_MAXBUF + CONFIG_MAXBUF, sizeof(char));
	if (!ctx->resp_buf)
		return -1;

	snprintf((char *)ctx->resp_buf, CONFIG_MAXBUF + CONFIG_MAXBUF,
		"%s%s%s%s%zu%s%s%s%s%s",
		HTTP_PROTO,
		ws_str_responses[code], HTTP_LINE_END,
		HTTP_HEADER_CONTENT_HTML
		HTTP_HEADER_CONTENTLEN, strlen(body), HTTP_LINE_END,
		HTTP_HEADER_LOCATION, safe_url,
		HTTP_LINE_END HTTP_LINE_END,
		body);
*/
	return 0;
}

int zproxy_http_request_reconnect(struct zproxy_http_ctx *ctx)
{
	zproxy_backend_cfg *backend;
	char  *buf = nullptr;

	// TODO: set down

	// clear sessions if they exist
	// PARSERTODO: Connect with the sessions table
	//~ zproxy_session_delete_backend(stream->session, &stream->backend_config->runtime.addr);

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

	ctx->buf = (char *) malloc(SRV_MAX_HEADER + CONFIG_MAXBUF);
	if (!ctx->buf)
		return -1;

	len = sprintf((char *)ctx->buf,
			"%.*s %.*s HTTP/1.%d%s",
			(int)parser->req.method_len, parser->req.method,
			(int)parser->req.path_len, parser->req.path, parser->req.minor_version,
			HTTP_LINE_END);

	if (parser->virtual_host_hdr.value_len)
		len += sprintf((char *)ctx->buf + len,
				"%.*s", (int)parser->virtual_host_hdr.line_size,
				parser->virtual_host_hdr.name);

	for (i = 0; i != parser->req.num_headers; i++) {
		if (parser->req.headers[i].header_off)
			continue;

		len += sprintf((char*)ctx->buf + len, "%.*s",
				(int)parser->req.headers[i].line_size,
				parser->req.headers[i].name);
	}

	len += sprintf((char*)ctx->buf + len, "%s", HTTP_LINE_END);

	if (parser->req.body)
		len += sprintf((char*)ctx->buf + len, "%.*s", (int)parser->req.body_len, parser->req.body);

	ctx->buf_len = len;
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

	if (parser->res.body)
		len += sprintf(buf + len, "%.*s", (int)parser->res.body_len, parser->res.body);

	zcu_log_print_th(LOG_DEBUG, "%.*s", (int)len, buf);

	if (zproxy_http_direct_proxy_reply(parser)) {
		ctx->resp_len = len;
		ctx->resp_buf = buf;
		ctx->buf = NULL;
	} else {
		ctx->buf_len = len;
		ctx->buf = buf;
	}

	return len;
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

	// TODO: Rewrite URL

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

	ctx->req_len = zproxy_http_request_send_to_backend(ctx);
	if (ctx->req_len == 0) {
		zproxy_http_event_reply_error(ctx, WS_HTTP_500);
		return -1;
	}

	ctx->buf_tail_len = ctx->buf_len;

	// TODO: manage body
	// TODO: check WAF body

	// TODO: update ctx->req_len, ctx->buf, ctx->buf_len
	// TODO: set new state
	//~ if (stream->request.expectBody())
		//~ parser->state = HTTP_PARSER_STATE::REQ_BODY_RCV;
	//~ else
		parser->state = HTTP_PARSER_STATE::RESP_HEADER_RCV;

	return 1;
}

static int zproxy_http_request_body_rcv(struct zproxy_http_ctx *ctx)
{
	// TODO
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
	}

	if (!ctx->parser)
		return -1;

	//~ TODO: streamLogDebug(ctx->stream, "->-> {bytes:%lu} %.*s", ctx->buf_len, ctx->buf_len, ctx->buf);
	//~ TODO: ctx->stream->updateStats(NEW_CONN);

	if (ctx->parser->state == HTTP_PARSER_STATE::CLOSE)
		return -1;

	if (ctx->parser->state == HTTP_PARSER_STATE::TUNNEL)
		return 1;

	if (ctx->parser->state == HTTP_PARSER_STATE::RESP_BODY_RCV)
		ctx->parser->state = HTTP_PARSER_STATE::REQ_HEADER_RCV;

	if (ctx->parser->state == HTTP_PARSER_STATE::REQ_HEADER_RCV)
		ret = zproxy_http_request_head_rcv(ctx);
	else if (ctx->parser->state == HTTP_PARSER_STATE::WAIT_100_CONT)
		ret = zproxy_http_request_100_cont(ctx);
	else if (ctx->parser->state == HTTP_PARSER_STATE::REQ_BODY_RCV)
		ret = zproxy_http_request_body_rcv(ctx);
	else
		//~ TODO: streamLogMessage(ctx->stream, "Request status not expected %s", ctx->stream->getState());
		return -1;

	//~ TODO: if (ctx->buf) {
		//~ streamLogDebug(ctx->stream, ">>>> {bytes:%lu/%lu} %.*s",
			       //~ ctx->buf_len, ctx->req_len, ctx->buf_len, ctx->buf);
	//~ }

	if (ret < 0)
		zproxy_http_parser_reset(ctx->parser);

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

	parser->res.buf_cpy_len = sprintf((char *)parser->res.buf_cpy + parser->res.buf_cpy_len, "%s", ctx->buf);
	free((char *)ctx->buf);
	ctx->buf_len = 0;

	ret = phr_parse_response(parser->res.buf_cpy, parser->res.buf_cpy_len,
								 &parser->res.minor_version,
								 &parser->res.status_code,
								 (const char **)&parser->res.message,
								 &parser->res.message_len,
								 parser->res.headers,
								 &parser->res.num_headers,
								 parser->res.last_length);

	parser->res.last_length = parser->res.buf_cpy_len;
	if (ret > 0) {
		parser->req.body = parser->req.buf_cpy + ret;
		parser->req.body_len = parser->req.buf_cpy_len - ret;
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

	//~ TODO: streamLogDebug(ctx->stream, "<-<- {bytes:%lu} %.*s", ctx->buf_len, ctx->buf_len, ctx->buf);

	//~ TODO: if (parser->state == HTTP_STATE::TUNNEL) {
		//~ streamLogDebug(ctx->stream, "tunnel: forwarding response");
		//~ return 1;
	//~ }

	//~ TODO: if (state == HTTP_STATE::REQ_BODY_RCV) {
		//~ ctx->stream->setState(HTTP_STATE::RESP_HEADER_RCV);
		//~ state = ctx->stream->getState();
	//~ }

	if (parser->state == HTTP_PARSER_STATE::RESP_HEADER_RCV) {
		//TODO: Improve parser, now it restarts the parsing if it is not completed
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

		ctx->buf_tail_len = zproxy_http_response_send_to_client(ctx);

		//~ TODO: stream->logSuccess();

	} else if (parser->state == HTTP_PARSER_STATE::RESP_BODY_RCV) {
		// TODO: add to body
		//~ ctx->stream->response.message = const_cast<char *>(&ctx->buf[ctx->buf_len - ctx->buf_tail_len]);
		//~ ctx->stream->response.message_length = ctx->buf_tail_len;
	} else {
		// TODO: ctx->stream->getStateTracer();
		//~ streamLogMessage(ctx->stream, "no valid state %s", stream->getStateString(state));
		return -1;
	}

	// TODO: manage body chunk
	// TODO: check WAF body

	// TODO: manage parser states
	//~ ctx->resp_len = ctx->res.buf_cpy_len;
/*	ctx->resp_len = ctx->stream->response.getBufferRewritedLength();

	if (stream->response.expectBody())
		ctx->stream->setState(HTTP_STATE::RESP_BODY_RCV);
	else if (stream->request.expect_100_cont_header
			&& stream->response.http_status_code == 100) {
		ctx->stream->setState(HTTP_STATE::REQ_BODY_RCV);
	} else {

		zproxy_stats_backend_inc_code(stream->http_state,
				stream->backend_config,
				stream->response.http_status_code);
		if (stream->isTunnel()) {
			ctx->stream->setState(HTTP_STATE::TUNNEL);
		} else if (stream->expectNewRequest()) {
			streamLogDebug(ctx->stream, "New request is expected");
			ctx->stream->setState(HTTP_STATE::REQ_HEADER_RCV);
		} else {
			stream->setState(HTTP_STATE::CLOSE);
			streamLogDebug(ctx->stream, "New request is NOT expected");
			ctx->http_close = 1;
			return 1;
		}
	}

	streamLogDebug(ctx->stream, "<<<< {bytes:%lu/%lu} %.*s", ctx->buf_len, ctx->resp_len, ctx->buf_len, ctx->buf);
*/
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

int zproxy_http_event_nossl(struct zproxy_http_ctx *ctx)
{
	const struct zproxy_proxy_cfg *proxy = ctx->cfg;
	if (!proxy)
		return -1;

	// TODO: rewrite like zproxy_http_event_reply_error()

	ctx->resp_buf = (char*)calloc(SRV_MAX_HEADER + CONFIG_MAXBUF, sizeof(char));
	if (!ctx->resp_buf)
		return -1;

	if (proxy->error.nosslredirect_url[0]) {
		snprintf((char*)ctx->resp_buf, SRV_MAX_HEADER + CONFIG_MAXBUF,
			 "%s%s%s%s%s%s%s", HTTP_PROTO,
			 ws_str_responses[proxy->error.nosslredirect_code], HTTP_LINE_END,
			 HTTP_HEADER_EXPIRES HTTP_HEADER_PRAGMA_NO_CACHE
			 HTTP_HEADER_LOCATION, proxy->error.nosslredirect_url, HTTP_LINE_END,
			 HTTP_HEADER_SERVER HTTP_HEADER_CACHE_CONTROL);
	} else {
		snprintf((char*)ctx->resp_buf, SRV_MAX_HEADER + CONFIG_MAXBUF,
			 "%s%s%s%s%zu%s%s%s", HTTP_PROTO,
			 ws_str_responses[proxy->error.errnossl_code], HTTP_LINE_END,
			 HTTP_HEADER_CONTENT_HTML
			 HTTP_HEADER_CONTENTLEN, strlen(ctx->cfg->runtime.errnossl_msg), HTTP_LINE_END,
			 HTTP_HEADER_EXPIRES
			 HTTP_HEADER_PRAGMA_NO_CACHE
			 HTTP_HEADER_SERVER
			 HTTP_HEADER_CACHE_CONTROL
			 HTTP_LINE_END,
			 ctx->cfg->runtime.errnossl_msg);
	}

	return 1;
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
