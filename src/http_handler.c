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

#include "http_handler.h"
#include "http_tools.h"
#include "http.h"

const char *http_headers_str[_MAX_HTTP_HEADER_NAME] = {
	"",
	"Accept",
	"Accept-Charset",
	"Accept-Encoding",
	"Accept-Language",
	"Accept-Ranges",
	"Access-Control-Allow-Credentials",
	"Access-Control-Allow-Headers",
	"Access-Control-Allow-Methods",
	"Access-Control-Allow-Origin",
	"Access-Control-Expose-Headers",
	"Access-Control-Max-Age",
	"Access-Control-Request-Headers",
	"Access-Control-Request-Method",
	"Age",
	"Allow",
	"Authorization",
	"Cache-Control",
	"Connection",
	"Content-Disposition",
	"Content-Encoding",
	"Content-Language",
	"Content-Length",
	"Content-Location",
	"Content-Range",
	"Content-Security-Policy",
	"Content-Security-Policy-Report-Only",
	"Content-Type",
	"Cookie",
	"Cookie2",
	"DNT",
	"Date",
	"Destination",
	"ETag",
	"Expect",
	"Expect-CT",
	"Expires",
	"Forwarded",
	"From",
	"Host",
	"If-Match",
	"If-Modified-Since",
	"If-None-Match",
	"If-Range",
	"If-Unmodified-Since",
	"Keep-Alive",
	"Large-Allocation",
	"Last-Modified",
	"Location",
	"Origin",
	"Pragma",
	"Proxy-Authenticate",
	"Proxy-Authorization",
	"Public-Key-Pins",
	"Public-Key-Pins-Report-Only",
	"Range",
	"Referer",
	"Referrer-Policy",
	"Retry-After",
	"Server",
	"Set-Cookie",
	"Set-Cookie2",
	"SourceMap",
	"Strict-Transport-Security",
	"TE",
	"Timing-Allow-Origin",
	"Tk",
	"Trailer",
	"Transfer-Encoding",
	"Upgrade",
	"Upgrade-Insecure-Requests",
	"User-Agent",
	"Vary",
	"Via",
	"WWW-Authenticate",
	"Warning",
	"X-Content-Type-Options",
	"X-DNS-Prefetch-Control",
	"X-Forwarded-For",
	"X-Forwarded-Host",
	"X-Forwarded-Proto",
	"X-Frame-Options",
	"X-XSS-Protection",
	"X-SSL-Subject",
	"X-SSL-Issuer",
	"X-SSL-Cipher",
	"X-SSL-notBefore",
	"X-SSL-notAfter",
	"X-SSL-Serial",
	"X-SSL-Certificate",
};

struct zproxy_http_parser *zproxy_http_parser_alloc(void)
{
	struct zproxy_http_parser *parser;

	parser = (struct zproxy_http_parser *)malloc(sizeof(struct zproxy_http_parser));
	if (!parser)
		return NULL;

	parser->state = REQ_HEADER_RCV;
	parser->chunk_state = CHUNKED_DISABLED;
	parser->service_cfg = NULL;
	parser->virtual_host_hdr.name = NULL;
	parser->virtual_host_hdr.name_len = 0;
	parser->virtual_host_hdr.value = NULL;
	parser->virtual_host_hdr.value_len = 0;
	parser->x_forwarded_for_hdr = NULL;
	parser->destination_hdr = NULL;
	parser->req.num_headers = MAX_HEADERS;
	parser->req.last_length = 0;
	parser->res.num_headers = MAX_HEADERS;
	parser->res.last_length = 0;
	return parser;
}

int zproxy_http_parser_free(struct zproxy_http_parser *parser)
{
	parser->destination_hdr = NULL;
	parser->x_forwarded_for_hdr = NULL;

	if (parser)
		free(parser);
	return 0;
}

int zproxy_http_parser_reset(struct zproxy_http_parser *parser)
{
	if (!parser)
		return -1;

	if (parser->req.method) {
		free(parser->req.method);
		parser->req.method_len = 0;
	}

	if (parser->req.path) {
		free(parser->req.path);
		parser->req.path_len = 0;
	}

	parser->req.minor_version = 0;
	parser->req.num_headers = 0;
	parser->req.last_length = 0;
	parser->state = REQ_HEADER_RCV;
	parser->chunk_state = CHUNKED_DISABLED;

	return 0;
}

static void zproxy_http_remove_header(phr_header *header, const struct list_head *m, regmatch_t *eol)
{
	struct matcher *current, *next;

	list_for_each_entry_safe(current, next, m, list) {
		if (regexec(&current->pat, header->name, 1,
				  eol, REG_STARTEND) == 0) {
			header->header_off = true;
			break;
		}
	}
}

static int zproxy_http_set_header(struct phr_header *header,
					const char *name, size_t name_len, const char *value, size_t value_len)
{
	char *buf;

	if (value_len == 0)
		return -1;

	buf = (char *) malloc(MAX_HEADER_LEN);
	if (!buf)
		return -1;

	header->name_len = name_len;
	header->value_len = value_len;
	header->header_off = false;
	if (name_len) {
		header->line_size = snprintf(buf, MAX_HEADER_LEN, "%.*s: %.*s",
					(int)name_len, name, (int)value_len, value);
		header->name = buf;
		header->value = buf + name_len + 2;
	} else {
		header->line_size = snprintf(buf, MAX_HEADER_LEN, "%.*s",
					(int)value_len, value);
		header->name = NULL;
		header->value = buf;
	}

	return 0;
}

struct phr_header * zproxy_http_add_header(
					struct phr_header *headers,
					size_t *num_headers, const char *name,
					size_t name_len, const char *value, size_t value_len)
{
	if (*num_headers >= MAX_HEADERS)
		return NULL;

	if (zproxy_http_set_header(&headers[*num_headers], name, name_len,
			value, value_len))
		return NULL;

	(*num_headers)++;
	return &headers[*num_headers];
}

static void zproxy_http_replace_header(struct zproxy_http_parser *parser,
					 phr_header *header,
					 const list_head *replace_header,
					 regmatch_t *eol)
{
	char buf[MAX_HEADER_LEN];
	struct replace_header *current, *next;

	if (header->header_off)
		return;

	list_for_each_entry_safe(current, next, replace_header, list) {
		eol->rm_eo = header->line_size;
		if (regexec(&current->name, header->name, 1, eol, REG_STARTEND) == 0 &&
				str_replace_regexp(buf, header->value, header->value_len,
					&current->match, current->replace) != -1 &&
					zproxy_http_add_header(parser->req.headers,
						&parser->req.num_headers, header->name,
						header->name_len, buf, strlen(buf))) {
			header->header_off = true;
			break;
		}
	}
}

static int zproxy_http_add_header_line(struct phr_header *headers,
					size_t *num_headers,
					const char *header_line)
{
	struct phr_header *header;
	size_t len;
	char *buf;

	if (*num_headers >= MAX_HEADERS)
		return -1;

	len = strlen(header_line);
	buf = (char *) malloc(len + 1);
	if (!buf)
		return -1;

	(*num_headers)++;
	header = &headers[*num_headers];
	header->line_size = len;
	strncpy(buf, header_line, len + 1);

	if (!(header->value = strstr(buf, ":"))) {
		header->value = buf;
		header->value_len = header->line_size;
	} else {
		header->name = buf;
		header->name_len = buf - header->value + 1;
		if (*++header->value == ' ')
			header->value++;
		header->value_len = header->line_size - (header->value - header->name) + 1;
	}

	return 0;
}

static void zproxy_http_set_x_forwarded_for_header(
				struct zproxy_http_parser *parser,
				const char *str, size_t str_len)
{
	char buf[MAX_HEADER_LEN];

	if (!str || str[0]=='\0')
		return;

	if (!parser->x_forwarded_for_hdr) {
		parser->x_forwarded_for_hdr = zproxy_http_add_header(
				parser->req.headers, &parser->req.num_headers,
				http_headers_str[X_FORWARDED_FOR],
				strlen(http_headers_str[X_FORWARDED_FOR]),
				str, str_len);
	} else {
		snprintf(buf, MAX_HEADER_LEN, "%s, %s", parser->x_forwarded_for_hdr->value, str);
		zproxy_http_set_header(parser->x_forwarded_for_hdr,
			http_headers_str[X_FORWARDED_FOR], XFORWARDEDFOR_HEADER_SIZE,
			buf, strlen(buf));
	}
}

void zproxy_http_set_virtual_host_header(
				struct zproxy_http_parser *parser,
				const char *str, size_t str_len)
{
	if (!parser->virtual_host_hdr.name_len) {
		zproxy_http_set_header(&parser->virtual_host_hdr,
				http_headers_str[HOST],
				HOST_HEADER_SIZE,
				str, str_len);
	} else {
		zproxy_http_set_header(&parser->virtual_host_hdr,
			http_headers_str[HOST], HOST_HEADER_SIZE,
			str, str_len);
	}
}

void zproxy_http_set_destination_header()
{
/*	TODO
 	regmatch_t matches[4];
	std::string proto;
	std::string host;
	std::string path;
	std::string host_addr;
	int port;
	std::string newh = http::http_info::headers_names_strings.at(http::HTTP_HEADER_NAME::DESTINATION) + ": ";

	parseUrl(request.destination_header, matches, proto, host, path, host_addr, port);

	if (host.empty() || !isHost(host_addr, port, listener->address, listener->port)) {
		newh += request.destination_header;
	} else {
		if (backend->runtime.ssl_enabled)
			newh += "https://";
		else
			newh += "http://";
		newh += std::string(backend->address) + ":" + std::to_string(backend->port) + path;
	}

	newh += http::CRLF;
	request.volatile_headers.push_back(std::move(newh));*/
}

void zproxy_http_manage_headers(struct zproxy_http_ctx *ctx,
		phr_header *header)
{
	struct zproxy_http_parser *parser = ctx->parser;

	if (!strncmp(header->name, http_headers_str[DESTINATION], header->name_len)) {
		// TODO: manage destination header
		parser->destination_hdr = header;
	} else if (!strncmp(header->name, http_headers_str[UPGRADE], header->name_len)) {
		// TODO: setHeaderUpgrade(header_value);
	} else if (!strncmp(header->name, http_headers_str[CONNECTION], header->name_len)) {
		//TODO: setHeaderConnection(header_value);
	} else if (!strncmp(header->name, http_headers_str[ACCEPT_ENCODING], header->name_len)) {
		//TODO: accept_encoding_header = true;
	} else if (!strncmp(header->name, http_headers_str[TRANSFER_ENCODING], header->name_len)) {
		//TODO: setHeaderTransferEncoding(header_value);
	} else if (!strncmp(header->name, http_headers_str[CONTENT_LENGTH], header->name_len)) {
		// TODO: setHeaderContentLength(header_value);
	} else if (!strncmp(header->name, http_headers_str[HOST], header->name_len)) {
		header->header_off = true;
		zproxy_http_set_virtual_host_header(parser, header->value, header->value_len);
	} else if (!strncmp(header->name, http_headers_str[EXPECT], header->name_len)) {
		// TODO: 100 continue function
		if (!strncmp(header->value, "100-continue", header->value_len)) {
			parser->expect_100_cont_hdr = true;
			zcu_log_print_th(
				LOG_DEBUG,
				"%s():%d: client Expects 100 continue",
				__FUNCTION__, __LINE__);
			}
			header->header_off = true;
	} else if (!strncmp(header->name, http_headers_str[X_FORWARDED_FOR], header->name_len)) {
		zproxy_http_set_x_forwarded_for_header(parser, header->value, header->value_len);
		header->header_off = true;
	}
}

int zproxy_http_handle_request_headers(struct zproxy_http_ctx *ctx)
{
	struct zproxy_http_parser *parser = ctx->parser;
	const struct zproxy_proxy_cfg *proxy = ctx->cfg;
	struct zproxy_service_cfg *service = parser->service_cfg;
	const struct list_head *remove_match = (
		!list_empty(&service->runtime.del_header_req)) ?
		&service->runtime.del_header_req :
		&proxy->runtime.del_header_req;
	const struct list_head *repl_ptr = (
		!list_empty(&service->runtime.replace_header_req)) ?
		&service->runtime.replace_header_req :
		&proxy->runtime.replace_header_req;
	const char *add_headers = (!service->header.add_header_req[0]) ?
		service->header.add_header_req :
		proxy->header.add_header_req;
	size_t i;

	for (i = 0; i != parser->req.num_headers; i++) {
		regmatch_t eol{ 0, static_cast<regoff_t>(parser->req.headers[i].line_size) };
		eol.rm_so = 0;
		eol.rm_eo = parser->req.headers[i].line_size;

		zproxy_http_remove_header(&parser->req.headers[i], remove_match, &eol);
		zproxy_http_replace_header(parser, &parser->req.headers[i], repl_ptr, &eol);
		zproxy_http_manage_headers(ctx, &parser->req.headers[i]);
	}

	if(add_headers[0])
		zproxy_http_add_header_line(parser->req.headers, &parser->req.num_headers, add_headers);

	zproxy_http_set_x_forwarded_for_header(parser, inet_ntoa(ctx->addr->sin_addr), INET_STR_SIZE);

	return 0;
}

int zproxy_http_handle_response_headers(struct zproxy_http_ctx *ctx)
{
	struct zproxy_http_parser *parser = ctx->parser;
	const struct zproxy_proxy_cfg *proxy = ctx->cfg;
	struct zproxy_service_cfg *service = parser->service_cfg;
	const struct list_head *remove_match = (
		service != NULL &&
			!list_empty(&service->runtime.del_header_res)) ?
		&service->runtime.del_header_res :
		&proxy->runtime.del_header_res;
	const struct list_head *repl_ptr = (
		service != NULL &&
			!list_empty(&service->runtime.replace_header_res)) ?
		&service->runtime.replace_header_res :
		&proxy->runtime.replace_header_res;
	const char *add_headers = (
		service != NULL &&
			parser->service_cfg && !service->header.add_header_res[0]) ?
		service->header.add_header_res :
		proxy->header.add_header_res;
	size_t i;

	for (i = 0; i != parser->res.num_headers; i++) {
		regmatch_t eol{ 0, static_cast<regoff_t>(parser->res.headers[i].line_size) };
		eol.rm_so = 0;
		eol.rm_eo = parser->res.headers[i].line_size;

		zproxy_http_remove_header(&parser->res.headers[i], remove_match, &eol);
		zproxy_http_replace_header(parser, &parser->res.headers[i], repl_ptr, &eol);
		zproxy_http_manage_headers(ctx, &parser->res.headers[i]);
	}

	if(add_headers[0])
		zproxy_http_add_header_line(parser->res.headers, &parser->res.num_headers, add_headers);

	// TODO: add other standard headers, cookies, etc

	return 0;
}

int zproxy_http_set_redirect_response(struct zproxy_http_ctx *ctx)
{
	struct zproxy_http_parser *parser = ctx->parser;
	struct zproxy_backend_redirect *redirect = &parser->service_cfg->redirect;
	char buf[MAX_HEADER_LEN] = {0};
	char new_url[MAX_HEADER_LEN] = {0};
	struct matcher *current, *next;

	snprintf(new_url, MAX_HEADER_LEN, "%s", redirect->url);
	if (redirect->redir_macro) {
		str_replace_str(
			buf, redirect->url, strlen(redirect->url),
			MACRO_VHOST, MACRO_VHOST_LEN,
			(char *) parser->virtual_host_hdr.value,
			parser->virtual_host_hdr.value_len);
		strncpy(new_url, buf, MAX_HEADER_LEN);
	}

	switch (redirect->redir_type) {
	case 1: // dynamic
		list_for_each_entry_safe(current, next, &parser->service_cfg->runtime.req_url, list) {
			if (str_replace_regexp(buf, parser->req.path,
						   parser->req.path_len,
					       &current->pat, new_url) != -1) {
				strncpy(new_url, buf, MAX_HEADER_LEN);
			}
		}
		break;
	case 2: // append
		strncat(new_url, parser->req.path, parser->req.path_len);
		break;
	default:
		break;
	}

	return 0;
}


/* TODO:
static void zproxy_http_clear_stats(struct zproxy_http_parser *parser)
{
	switch(parser->stats_state)
	{
		case NEW_CONN:
			zproxy_stats_listener_dec_conn_established(http_state);
			zproxy_stats_listener_dec_conn_pending(http_state);
			break;
		case BCK_CONN:
			zproxy_stats_listener_dec_conn_established(http_state);
			zproxy_stats_backend_dec_conn_pending(http_state, backend_config);
			break;
		case ESTABLISHED:
			zproxy_stats_listener_dec_conn_established(http_state);
			zproxy_stats_backend_dec_conn_established(http_state, backend_config);
			break;
		case UNDEF:
			streamLogDebug(this, "The stream stats are not defined");
			break;
		default:
			streamLogMessage(this, "The stream stats are not defined: %d", stats_state);
	}
	stats_state = UNDEF;
}


int zproxy_http_update_stats(struct zproxy_http_parser *parser, const STREAM_STATE new_state)
{
	int ret = 1;
	//~ streamLogDebug(this, "Changing stats: %d -> %d", stats_state, new_state);

	if (new_state == parser->stats_state)
		return ret;

	zproxy_http_clear_stats(parser);

	ret = setStats(new_state);
	if(ret < 0)
	{
		streamLogMessage(this, "Error setting stats for state: %d -> %d",
				stats_state, new_state);
	}

	return ret;
}
*/
