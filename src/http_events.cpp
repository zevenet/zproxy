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

#include <cstdlib>
#include <netinet/in.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <string.h>
#include <assert.h>
#include <stdio.h>

#include "http.h"
#include "http_log.h"
#include "http_stream.h"
#include "http_manager.h"
#include "service.h"
#include "session.h"
#include "state.h"
#include "config.h"
#include "zcu_http.h"


static void zproxy_set_backend(zproxy_backend_cfg *backend, zproxy_http_ctx *ctx, HttpStream *stream)
{
	stream->new_backend = nullptr;
	stream->backend_config = backend;
	memcpy(&ctx->backend->addr, &backend->runtime.addr, sizeof(backend->runtime.addr));
	ctx->backend->ssl_enabled = backend->runtime.ssl_enabled;
	ctx->backend->cfg = backend;

	http_manager::setHeadersRewrBck(stream);
}

int zproxy_http_request_reconnect(struct zproxy_http_ctx *ctx)
{
	auto stream = ctx->stream;
	zproxy_backend_cfg *backend;
	char  *buf = nullptr;

	// set down
	// TODO: set down

	// clear sessions if they exist
	zproxy_session_delete_backend(stream->session, &stream->backend_config->runtime.addr);

	// getting a new backend
	backend = zproxy_service_select_backend(stream->service_config,
			stream->request, stream->client_addr, stream->session,
			static_cast<struct zproxy_http_state*>(ctx->state));
	if (backend == nullptr) {
		ctx->resp_buf = http_manager::replyError(
			stream, http::Code::ServiceUnavailable,
				validation::request_result_reason.at(
					validation::REQUEST_RESULT::
						BACKEND_NOT_FOUND),
				std::string(stream->listener_config->runtime.err503_msg));
		return -1;
	}
	zproxy_set_backend(backend, ctx, stream);

	stream->request.setHeaderSent(false);
	ctx->buf_len = ctx->stream->request.prepareToSend(&buf);
	if (ctx->buf_len == 0) {
		ctx->resp_buf = http_manager::replyError(
			stream, http::Code::InternalServerError,
				http::reasonPhrase(http::Code::InternalServerError),
				std::string(stream->listener_config->runtime.err500_msg));
		return -1;
	}
	ctx->buf = buf;
	ctx->buf_tail_len = ctx->buf_len;

	return 0;
}

static int zproxy_http_request_head_rcv(struct zproxy_http_ctx *ctx)
{
	struct zproxy_http_state *state = (struct zproxy_http_state *)ctx->state;
	const struct zproxy_proxy_cfg *cfg = ctx->cfg;
	struct zproxy_service_cfg *service;
	struct zproxy_backend_cfg *backend;
	int new_bck_flag = 1;
	int reconnect_bck_flag = 0;
	size_t parsed_bytes;
	char *buf = nullptr;

	auto stream = ctx->stream;

	//TODO: Improve parser, now it restarts the parsing if it is not completed
	http_parser::PARSE_RESULT parse_status = stream->request.parse(ctx->buf, ctx->buf_len,
					&parsed_bytes);
	stream->response.reset();

	/* Return 0 if you want core to keep reading data from client. */
	if (parse_status == http_parser::PARSE_RESULT::INCOMPLETE) {
		if(ctx->buf_len == ctx->buf_siz ) {
			ctx->resp_buf = http_manager::replyError(
					stream, http::Code::BadRequest,
					http::reasonPhrase(http::Code::BadRequest),
					std::string(stream->listener_config->error.parse_req_msg));
			return -1;
		} else
			return 0;
	}
	if (parse_status == http_parser::PARSE_RESULT::TOOLONG) {
		ctx->resp_buf = http_manager::replyError(
			stream, http::Code::URITooLong,
			http::reasonPhrase(http::Code::URITooLong),
			std::string(stream->listener_config->runtime.err414_msg));
		return -1;
	}
	if (parse_status == http_parser::PARSE_RESULT::FAILED) {
		ctx->resp_buf = http_manager::replyError(
			stream, http::Code::BadRequest,
			http::reasonPhrase(http::Code::BadRequest),
			std::string(stream->listener_config->error.parse_req_msg));
		return -1;
	}

	auto valid = http_manager::validateRequestLine(stream);

	if (valid == validation::REQUEST_RESULT::METHOD_NOT_ALLOWED) {
		ctx->resp_buf = http_manager::replyError(
			stream, http::Code::MethodNotAllowed,
			validation::request_result_reason.at(valid),
			std::string(stream->listener_config->runtime.err501_msg));
		return -1;
	} else if (valid != validation::REQUEST_RESULT::OK) {
		ctx->resp_buf = http_manager::replyError(
			stream, http::Code::ServiceUnavailable,
			validation::request_result_reason.at(valid),
			std::string(stream->listener_config->runtime.err503_msg));
		return -1;
	}

	// validate if a new request goes to the same service
	auto latest_svc = stream->service_config;

	if (latest_svc != nullptr)
		new_bck_flag = 0;
	list_for_each_entry(service, &cfg->service_list, list) {
		if (zproxy_service_select(&stream->request, service)) {
			stream->service_config = service;
			stream->session = zproxy_state_get_session(service->name, &state->services);
			break;
		}
	}

	if (stream->service_config == nullptr) {
		ctx->resp_buf = http_manager::replyError(
			stream, http::Code::ServiceUnavailable,
			validation::request_result_reason.at(
				validation::REQUEST_RESULT::SERVICE_NOT_FOUND),
			std::string(stream->listener_config->runtime.err503_msg));
		return -1;
	}

	// a backend disconnection is required
	if (latest_svc != nullptr && latest_svc != stream->service_config &&
			stream->backend_config != nullptr) {
		new_bck_flag = 1;
	}

	// Rewrite URL
	http_manager::rewriteUrl(stream);

	valid = http_manager::validateRequest(stream);
	if (valid != validation::REQUEST_RESULT::OK) {
		ctx->resp_buf = http_manager::replyError(
			stream, http::Code::NotImplemented,
			validation::request_result_reason.at(valid),
			std::string(stream->listener_config->runtime.err501_msg));
		return -1;
	}

	if (stream->waf.checkRequestHeaders(stream)) {
		ctx->resp_buf = stream->waf.response(stream);
		return -1;
	}

	if (stream->service_config->redirect.enabled) {
		ctx->resp_buf = http_manager::replyRedirectBackend(*stream, stream->service_config->redirect);
		return -1;
	}

	if (new_bck_flag || reconnect_bck_flag) {
		backend = zproxy_service_select_backend(stream->service_config,
				stream->request, stream->client_addr, stream->session,
				state);
		if (backend == nullptr) {
			ctx->resp_buf = http_manager::replyError(
				stream, http::Code::ServiceUnavailable,
				validation::request_result_reason.at(
					validation::REQUEST_RESULT::
					BACKEND_NOT_FOUND),
				std::string(stream->listener_config->runtime.err503_msg));
			return -1;
		}
		stream->new_backend = backend;
		if (!stream->request.expect_100_cont_header)
			zproxy_set_backend(backend, ctx, stream);
	}

	if (stream->request.expect_100_cont_header) {
		ctx->stream->setState(HTTP_STATE::WAIT_100_CONT);
		ctx->http_continue = true;
		std::string ret = getHttp100ContinueResponse();
		char *buf_resp = (char *)malloc((ret.length()+1)*sizeof(char));
		strncpy (buf_resp, ret.c_str(), ret.length()+1);
		ctx->resp_buf = buf_resp;
		return -1;
	}

	ctx->buf_len = ctx->stream->request.prepareToSend(&buf);
	if (ctx->buf_len == 0) {
		ctx->resp_buf = http_manager::replyError(
			ctx->stream, http::Code::InternalServerError,
			http::reasonPhrase(http::Code::InternalServerError),
			std::string(ctx->stream->listener_config->runtime.err500_msg));
		return -1;
	}
	ctx->buf_tail_len = ctx->buf_len;

	if (ctx->stream->request.message_length > 0) {
		ctx->stream->request.manageBody(ctx->stream->request.message, ctx->stream->request.message_length);
		if (stream->waf.checkRequestBody(stream)) {
			free(buf);
			ctx->resp_buf = stream->waf.response(stream);
			return -1;
		}
	}
	ctx->buf = buf;

	/* Do we know the total request length? */
	ctx->req_len = ctx->stream->request.getBufferRewritedLength();

	if (stream->request.expectBody())
		ctx->stream->setState(HTTP_STATE::REQ_BODY_RCV);
	else
		ctx->stream->setState(HTTP_STATE::RESP_HEADER_RCV);

	return 1;
}

static int zproxy_http_request_100_cont(struct zproxy_http_ctx *ctx)
{
	char  *buf = nullptr;

	if (ctx->buf_len < ctx->stream->request.last_length+4) {
		syslog(LOG_DEBUG, "100 continue does not receive body data yet");
		return 0;
	}
	ctx->stream->request.message_length = ctx->buf_tail_len;
	ctx->buf_len = ctx->stream->request.prepareToSend(&buf);

	if (ctx->buf_len == 0) {
		ctx->resp_buf = http_manager::replyError(
			ctx->stream, http::Code::InternalServerError,
			http::reasonPhrase(http::Code::InternalServerError),
			std::string(ctx->stream->listener_config->runtime.err500_msg));
		return -1;
	}
	ctx->buf_tail_len = ctx->buf_len;

	ctx->stream->request.manageBody(ctx->stream->request.message, ctx->stream->request.message_length);

	if (ctx->stream->waf.checkRequestBody(ctx->stream)) {
		free(buf);
		ctx->resp_buf = ctx->stream->waf.response(ctx->stream);
		return -1;
	}
	ctx->buf = buf;

	if (ctx->stream->new_backend)
		zproxy_set_backend(ctx->stream->new_backend, ctx, ctx->stream);

	if(ctx->stream->request.expectBody())
		ctx->stream->setState(HTTP_STATE::REQ_BODY_RCV);
	else
		ctx->stream->setState(HTTP_STATE::RESP_HEADER_RCV);
	ctx->req_len = ctx->stream->request.getBufferRewritedLength();

	return 1;
}

static int zproxy_http_request_body_rcv(struct zproxy_http_ctx *ctx)
{
	auto stream = ctx->stream;

	stream->request.manageBody(&ctx->buf[ctx->buf_len - ctx->buf_tail_len], ctx->buf_tail_len);

	if (stream->waf.checkRequestBody(stream)) {
		ctx->resp_buf = stream->waf.response(stream);
		return -1;
	}

	if (stream->request.chunked_status == CHUNKED_STATUS::CHUNKED_LAST_CHUNK
			|| stream->request.content_length == stream->request.message_total_bytes)
		stream->setState(HTTP_STATE::RESP_HEADER_RCV);

	ctx->req_len = ctx->stream->request.getBufferRewritedLength();

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

	if (ctx->stream == nullptr) {
		ctx->stream = new HttpStream(const_cast<zproxy_proxy_cfg *>(ctx->cfg),
						  ctx->addr, static_cast<struct zproxy_http_state*>(ctx->state));
	}
	auto state = ctx->stream->getState();

	streamLogDebug(ctx->stream, "->-> {bytes:%lu} %.*s", ctx->buf_len, ctx->buf_len, ctx->buf);
	ctx->stream->updateStats(NEW_CONN);

	if (state == HTTP_STATE::TUNNEL) {
		streamLogDebug(ctx->stream, "tunnel: forwarding request");
		return 1;
	}

	if (state == HTTP_STATE::RESP_BODY_RCV) {
		ctx->stream->setState(HTTP_STATE::REQ_HEADER_RCV);
		state = ctx->stream->getState();
	}

	if (state == HTTP_STATE::REQ_HEADER_RCV) {
		ret = zproxy_http_request_head_rcv(ctx);
	} else if (state == HTTP_STATE::WAIT_100_CONT) {
		ret = zproxy_http_request_100_cont(ctx);
	} else if (state == HTTP_STATE::REQ_BODY_RCV) {
		ret = zproxy_http_request_body_rcv(ctx);
	} else {
		// TODO: ctx->stream->getStateTracer();
		streamLogMessage(ctx->stream, "Request status not expected %s", ctx->stream->getState());
		return -1;
	}

	if (ctx->buf) {
		streamLogDebug(ctx->stream, ">>>> {bytes:%lu/%lu} %.*s",
			       ctx->buf_len, ctx->req_len, ctx->buf_len, ctx->buf);
	}

	return ret;
}

int zproxy_http_response_parser(struct zproxy_http_ctx *ctx)
{
	size_t parsed_bytes;
	auto stream = ctx->stream;
	char  *buf = nullptr;

	streamLogDebug(ctx->stream, "<-<- {bytes:%lu} %.*s", ctx->buf_len, ctx->buf_len, ctx->buf);

	auto state = stream->getState();
	if (state == HTTP_STATE::TUNNEL) {
		streamLogDebug(ctx->stream, "tunnel: forwarding response");
		return 1;
	}

	if (state == HTTP_STATE::REQ_BODY_RCV) {
		ctx->stream->setState(HTTP_STATE::RESP_HEADER_RCV);
		state = ctx->stream->getState();
	}

	if (state == HTTP_STATE::RESP_HEADER_RCV) {
		//TODO: Improve parser, now it restarts the parsing if it is not completed
		http_parser::PARSE_RESULT parse_status = stream->response.parse(ctx->buf, ctx->buf_len,
						&parsed_bytes);

		/* Return 0 if you want core to keep reading data from client. */
		if (parse_status == http_parser::PARSE_RESULT::INCOMPLETE)
			return 0;
		if (parse_status == http_parser::PARSE_RESULT::FAILED) {
			ctx->buf = http_manager::replyError(
				stream, http::Code::InternalServerError,
				http::reasonPhrase(http::Code::InternalServerError),
				std::string(stream->listener_config->runtime.err500_msg));
			ctx->buf_len = strlen(ctx->buf);
			return -1;
		}

		http_manager::validateResponse(stream);

		if (stream->waf.checkResponseHeaders(stream)) {
			ctx->resp_buf = stream->waf.response(stream);
			return -1;
		}

		// build the response
		ctx->buf_len = ctx->stream->response.prepareToSend(&buf);
		if (ctx->buf_len == 0) {
			ctx->buf = http_manager::replyError(
				ctx->stream, http::Code::InternalServerError,
					http::reasonPhrase(http::Code::InternalServerError),
					std::string(ctx->stream->listener_config->runtime.err500_msg));
			ctx->buf_len = strlen(ctx->buf);
			return -1;
		}
		ctx->buf = buf;
		ctx->buf_tail_len = ctx->buf_len;

		stream->logSuccess();

	} else if (state == HTTP_STATE::RESP_BODY_RCV) {
		ctx->stream->response.message = const_cast<char *>(&ctx->buf[ctx->buf_len - ctx->buf_tail_len]);
		ctx->stream->response.message_length = ctx->buf_tail_len;
	} else {
		// TODO: ctx->stream->getStateTracer();
		streamLogMessage(ctx->stream, "no valid state %s", stream->getStateString(state));
		return -1;
	}

	stream->response.manageBody(&ctx->buf[ctx->buf_len - ctx->buf_tail_len], ctx->buf_tail_len);

	if (stream->waf.checkResponseBody(stream)) {
		if (buf)
			free(buf);
		ctx->resp_buf = stream->waf.response(stream);
		return -1;
	}

	/* Do we know the total response length? */
	ctx->resp_len = ctx->stream->response.getBufferRewritedLength();

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

	return 1;
}

int zproxy_http_event_timeout(struct zproxy_http_ctx *ctx)
{
	auto stream = ctx->stream;

	if (!stream || !stream->session)
		return -1;

	// clear sessions if they exist
	zproxy_session_delete_backend(stream->session, &stream->backend_config->runtime.addr);

	// TODO: did the client already send us a full http request? If not
	//	 better return -1 to close connection immediately?

	ctx->resp_buf = http_manager::replyError(
		stream, http::Code::GatewayTimeout,
			validation::request_result_reason.at(
				validation::REQUEST_RESULT::
					GATEWAY_TIMEOUT), std::string(""));

	return 0;
}

int zproxy_http_event_nossl(struct zproxy_http_ctx *ctx)
{
	const struct zproxy_proxy_cfg *proxy = ctx->cfg;
	if (!proxy)
		return -1;

	ctx->resp_buf = (char*)calloc(SRV_MAX_HEADER + CONFIG_MAXBUF, sizeof(char));
	if (!ctx->resp_buf)
		return -1;

	if (proxy->error.nosslredirect_url[0]) {
		snprintf((char*)ctx->resp_buf, SRV_MAX_HEADER + CONFIG_MAXBUF,
			 "%s%s%s%s%s",
			 ws_str_responses[proxy->error.nosslredirect_code],
			 HTTP_HEADER_EXPIRES HTTP_HEADER_PRAGMA_NO_CACHE
			 HTTP_HEADER_LOCATION, proxy->error.nosslredirect_url, HTTP_LINE_END,
			 HTTP_HEADER_SERVER HTTP_HEADER_CACHE_CONTROL);
	} else {
		snprintf((char*)ctx->resp_buf, SRV_MAX_HEADER + CONFIG_MAXBUF,
			 "%s%s%zu%s%s%s",
			 ws_str_responses[proxy->error.errnossl_code],
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
