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

#include <ctype.h>
#include <netdb.h>
#include <pcreposix.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "config.h"
#include "http.h"
#include "http_handler.h"
#include "http_tools.h"
#include "pico_http_parser.h"
#include "state.h"
#include "zcu_common.h"
#include "zcu_http.h"
#include "zcu_log.h"
#include "zcu_network.h"

#define PARSER_STATE_SET(parser, var, value)                                   \
	switch (parser->state) {                                               \
	case REQ_HEADER_RCV:                                                   \
		parser->req.var = value;                                       \
		break;                                                         \
	case RESP_HEADER_RCV:                                                  \
		parser->res.var = value;                                       \
		break;                                                         \
	default:                                                               \
		zcu_log_print_th(LOG_ERR, "Invalid parser state %d",           \
				 parser->state);                               \
		break;                                                         \
	}

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
	if (parser->http_state)
		zproxy_state_free(&parser->http_state);

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
	parser->accept_encoding_header = false;
	parser->req.upgrade_header = false;
	parser->req.conn_upgr_hdr = false;
	parser->req.conn_close_pending = false;
	parser->req.conn_keep_alive = false;
	parser->res.upgrade_header = false;
	parser->res.conn_upgr_hdr = false;
	parser->res.conn_close_pending = false;
	parser->res.conn_keep_alive = false;

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
		header->line_size = snprintf(buf, MAX_HEADER_LEN, "%.*s: %.*s%s",
					(int)name_len, name, (int)value_len, value, HTTP_LINE_END);
		header->name = buf;
		header->value = buf + name_len + 2;
	} else {
		header->line_size = snprintf(buf, MAX_HEADER_LEN, "%.*s%s",
					(int)value_len, value, HTTP_LINE_END);
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

	return &headers[(*num_headers)++];
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

static struct phr_header *
zproxy_http_add_header_line(struct phr_header *headers, size_t *num_headers,
			    const char *header_line)
{
	struct phr_header *header;
	size_t len;
	char *buf;

	if (*num_headers >= MAX_HEADERS)
		return NULL;

	len = strlen(header_line) + strlen(HTTP_LINE_END);
	buf = (char *) calloc(len + 1, sizeof(char));
	if (!buf)
		return NULL;

	header = &headers[(*num_headers)++];
	header->line_size = len;
	snprintf(buf, len + 1, "%s" HTTP_LINE_END, header_line);

	if (!(header->value = strchr(buf, ':'))) {
		header->value = buf;
		header->value_len = header->line_size;
	} else {
		header->name = buf;
		header->name_len = header->value - buf;
		if (*++header->value == ' ')
			header->value++;
		header->value_len = header->line_size - (header->value - header->name) + 1;
	}

	zcu_log_print_th(LOG_DEBUG, "Add header line: %.*s", header->line_size,
			 header->name);

	return header;
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
		snprintf(buf, MAX_HEADER_LEN, "%.*s, %s",
			 (int)parser->x_forwarded_for_hdr->value_len,
			 parser->x_forwarded_for_hdr->value, str);
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

static bool is_host(const char *vaddr, int vport, const char *addr, int port)
{
	bool ret = false;

	struct addrinfo *in_addr = zcu_net_get_address(vaddr, vport);

	if (in_addr) {
		struct addrinfo *in_addr_2 = zcu_net_get_address(addr, port);

		if (zcu_soc_equal_sockaddr(in_addr->ai_addr, in_addr_2->ai_addr, 1))
			ret = true;

		freeaddrinfo(in_addr_2);
		freeaddrinfo(in_addr);
	}

	return ret;

}

static void parse_url(const char *header_value, size_t header_value_len,
		      regmatch_t *matches, const char **proto,
		      size_t *proto_len, const char **host, size_t *host_len,
		      const char **path, size_t *path_len,
		      const char **host_addr, size_t *host_addr_len,
		      int *port, size_t *port_len)
{
	regex_t reg;

	regcomp(&reg, "^(http|https)://([^/]+)(.*)", REG_EXTENDED);
	if (!regexec(&reg, header_value, 4, matches, 0)) {
		*proto = header_value + matches[1].rm_so;
		*proto_len = matches[1].rm_eo - matches[1].rm_so;

		*host = *host_addr = header_value + matches[2].rm_so;
		*host_len = *host_addr_len = matches[2].rm_eo - matches[2].rm_so;

		*path = header_value + matches[3].rm_so;
		*path_len = matches[3].rm_eo - matches[3].rm_so;

		size_t i;
		for (i = 0; i < *host_addr_len && (*host_addr)[i] != ':'; ++i);
		if (i != *host_addr_len) {
			*port = atoi(*host + i + 1);
			*port_len = *host_len - (i + 1);
			*host_len = i;
		} else if (!strncmp(*proto, "https", *proto_len)) {
			*port = 443;
			*port_len = 3;
		} else {
			*port = 80;
			*port_len = 2;
		}
	} else {
		*path = header_value;
		*path_len = header_value_len;
	}
	regfree(&reg);
}

void zproxy_http_set_destination_header(struct zproxy_http_ctx *ctx)
{
	struct zproxy_http_parser *parser = ctx->parser;

	if (!parser->destination_hdr)
		return;

	struct phr_header *header = parser->destination_hdr;
	const struct zproxy_backend_cfg *backend = ctx->backend->cfg;

	const char *loc;
	size_t loc_len;
	regmatch_t matches[4];
	const char *proto = NULL, *host = NULL, *path = NULL, *host_addr = NULL;
	size_t proto_len = 0, host_len = 0, path_len = 0, host_addr_len = 0;
	int port = -1;
	size_t port_len = 0;
	char *new_header_value = NULL;
	size_t nhv_len = 0;

	loc = strndup(header->value, header->value_len);
	loc_len = header->value_len;
	new_header_value = (char*)calloc(MAX_HEADER_LEN, sizeof(char));
	nhv_len = snprintf(new_header_value, MAX_HEADER_LEN, "%s: ",
			   http_headers_str[DESTINATION]);

	parse_url(loc, loc_len, matches, &proto, &proto_len, &host, &host_len,
		  &path, &path_len, &host_addr, &host_addr_len, &port,
		  &port_len);

	if (!host_len && !is_host(host_addr, port, ctx->cfg->address,
				 ctx->cfg->port)) {
		nhv_len += sprintf(new_header_value + nhv_len, "%.*s",
				   (int)header->value_len, header->value);
	} else {
		if (backend->runtime.ssl_enabled)
			nhv_len += sprintf(new_header_value + nhv_len, "https://");
		else
			nhv_len += sprintf(new_header_value + nhv_len, "http://");

		nhv_len += sprintf(new_header_value + nhv_len, "%s:%d%.*s",
				   backend->address, backend->port,
				   (int)path_len, path);
	}

	parser->destination_hdr =
		zproxy_http_add_header_line(parser->req.headers,
					    &parser->req.num_headers,
					    new_header_value);
	header->header_off = true;

	free((void*)loc);
	free((void*)new_header_value);
}

void zproxy_http_rewrite_url(struct zproxy_http_parser *parser)
{
	const struct zproxy_service_cfg *service_cfg = parser->service_cfg;
	char path_orig[ZCU_DEF_BUFFER_SIZE],
		buf[ZCU_DEF_BUFFER_SIZE],
		aux_buf[ZCU_DEF_BUFFER_SIZE];
	int offset = 0;
	size_t ori_size = ZCU_DEF_BUFFER_SIZE;
	bool modified = false;
	struct replace_header *current, *next;

	snprintf(path_orig, ZCU_DEF_BUFFER_SIZE, "%.*s",
		 (int)parser->req.path_len,parser->req.path);
	snprintf(aux_buf, ZCU_DEF_BUFFER_SIZE, "%.*s",
		 (int)parser->req.path_len,parser->req.path);

	list_for_each_entry_safe(current, next, &service_cfg->runtime.req_rw_url, list) {
		offset = str_replace_regexp(buf, aux_buf, strlen(aux_buf),
					    &current->match, current->replace);
		if (offset != -1) {
			modified = true;
			snprintf(aux_buf, ZCU_DEF_BUFFER_SIZE, "%s", buf);
			zcu_log_print_th(LOG_DEBUG,
					 "URL rewritten \"%s\" -> \"%s\"",
					 path_orig, buf);

			if (ori_size > parser->req.path_len - offset)
				ori_size = parser->req.path_len - offset;
		}
	}

	if (modified) {
		parser->req.path_mod = true;
		parser->req.path_repl = strdup(aux_buf);
		parser->req.path_repl_len = strlen(aux_buf);
		zcu_log_print_th(LOG_DEBUG, "URL for reverse Location \"%.*s\"",
				 parser->req.path_len, parser->req.path);
	}
}

static int rewrite_location(struct zproxy_http_ctx *ctx, phr_header *header)
{
	struct zproxy_http_parser *parser = ctx->parser;
	const struct zproxy_proxy_cfg *proxy = ctx->cfg;
	char loc[MAX_HEADER_VALUE] = { 0 };
	size_t loc_len;
	bool rw_location, rw_url_rev;

	rw_location = proxy->header.rw_location;
	rw_url_rev = proxy->header.rw_url_rev;

	if (parser->service_cfg) {
		rw_location |= parser->service_cfg->header.rw_location;
		rw_url_rev |= parser->service_cfg->header.rw_url_rev;
	}

	if (!parser->req.path_mod)
		rw_url_rev = 0;

	if (!rw_location && !rw_url_rev)
		return 1;

	snprintf(loc, MAX_HEADER_VALUE, "%.*s", (int)header->value_len,
		 header->value);
	loc_len = header->value_len;

	regmatch_t matches[4];
	const char *proto = NULL, *host = NULL, *path = NULL, *host_addr = NULL;
	size_t proto_len = 0, host_len = 0, path_len = 0, host_addr_len = 0;
	int port = -1;
	size_t port_len = 0;
	char new_header_value[MAX_HEADER_VALUE] = { 0 };

	parse_url(loc, loc_len, matches, &proto, &proto_len, &host, &host_len,
		  &path, &path_len, &host_addr, &host_addr_len, &port,
		  &port_len);

	if (parser->req.path_mod && rw_url_rev) {
		path = parser->req.path_repl;
		path_len = parser->req.path_repl_len;
	}

	if (ctx->backend && rw_location) {
		struct addrinfo *in_addr;
		{
			char aux_host[host_len];
			sprintf(aux_host, "%.*s", (int)host_len, host);
			in_addr = zcu_net_get_address(aux_host, port);
		}
		const char *new_proto = NULL;
		size_t new_proto_len = 0;
		const char *new_vhost = NULL;
		size_t new_vhost_len = 0;
		int new_port = -1;
		size_t new_port_len = 0;

		if (in_addr) {
			struct addrinfo *backend_addr =
				zcu_net_get_address(ctx->backend->cfg->address,
						    ctx->backend->cfg->port);
			struct addrinfo *listener_addr =
				zcu_net_get_address(proxy->address,
						    proxy->port);

			// rewrite location if it points to the backend
			if (zcu_soc_equal_sockaddr(in_addr->ai_addr,
						   backend_addr->ai_addr, 1)) {
				new_proto = proto;
				new_proto_len = proto_len;
			// or the listener address with different port
			} else if (rw_location &&
				   (proxy->port != port ||
				    strncmp(proto, (!proxy->runtime.ssl_enabled) ? "http" : "https", proto_len)) &&
				   (zcu_soc_equal_sockaddr(in_addr->ai_addr, listener_addr->ai_addr, 0) ||
				    !strncmp(host, parser->virtual_host_hdr.value, MIN(host_len, parser->virtual_host_hdr.value_len)))) {
				new_proto = !strncmp(proto, "https", proto_len) ? "http" : "https";
				new_proto_len = strlen(new_proto);
			}

			if (new_proto) {
				new_vhost = parser->virtual_host_hdr.value;
				new_vhost_len = parser->virtual_host_hdr.value_len;

				if ((!proxy->runtime.ssl_enabled && proxy->port != 443) ||
				    (proxy->port != 80)) {
					size_t i;
					for (i = 0; i < header->value_len && header->value[i] != ':'; ++i);
					if (i == header->value_len) {
						new_port = proxy->port;
						for (i = new_port; i > 0; i /= 10)
							new_port_len++;
					}
				}
			}

			if (new_proto && new_vhost) {
				if (new_port_len) {
					snprintf(new_header_value,
						 MAX_HEADER_VALUE,
						 "%.*s://%.*s:%d%.*s",
						 (int)new_proto_len, new_proto,
						 (int)new_vhost_len, new_vhost,
						 new_port, (int)path_len,
						 path);
				} else {
					snprintf(new_header_value,
						 MAX_HEADER_VALUE,
						 "%.*s://%.*s%.*s",
						 (int)new_proto_len, new_proto,
						 (int)new_vhost_len, new_vhost,
						 (int)path_len, path);
				}
			}

			freeaddrinfo(backend_addr);
			freeaddrinfo(listener_addr);
			freeaddrinfo(in_addr);
		}

		if (!new_header_value[0] && proto && host) {
			snprintf(new_header_value, MAX_HEADER_VALUE,
				 "%.*s://%.*s%.*s", (int)proto_len, proto,
				 (int)host_len, host, (int)path_len, path);
		}
	}

	if (!new_header_value[0] && proto_len && host_len) {
		if (!port_len) {
			snprintf(new_header_value, MAX_HEADER_VALUE,
				 "%.*s://%.*s%.*s", (int)proto_len, proto,
				 (int)host_len, host, (int)path_len, path);
		} else {
			snprintf(new_header_value, MAX_HEADER_VALUE,
				 "%.*s://%.*s:%d%.*s", (int)proto_len, proto,
				 (int)host_len, host, port, (int)path_len,
				 path);
		}
	}

	char new_header[MAX_HEADER_LEN];
	snprintf(new_header, MAX_HEADER_LEN, "%.*s: %s", (int)header->name_len,
		 header->name, new_header_value);
	zproxy_http_add_header_line(parser->res.headers,
				    &parser->res.num_headers,
				    new_header);
	header->header_off = 1;

	return 1;
}

static void zproxy_http_manage_headers(struct zproxy_http_ctx *ctx,
				       phr_header *header)
{
	struct zproxy_http_parser *parser = ctx->parser;

	if (!strncmp(header->name, http_headers_str[DESTINATION], header->name_len)) {
		parser->destination_hdr = header;
	} else if (!strncmp(header->name, http_headers_str[UPGRADE], header->name_len)) {
		char upgr_hdr[MAX_HEADER_VALUE] = { 0 };
		for (size_t i = 0; i < header->value_len; ++i)
			upgr_hdr[i] = tolower(header->value[i]);

		if (strstr(upgr_hdr, "websocket")) {
			PARSER_STATE_SET(parser, upgrade_header, true);
		} else {
			zcu_log_print_th(LOG_WARNING,
					 "Invalid upgrade value: %.*s",
					 header->value_len, header->value);
		}
	} else if (!strncmp(header->name, http_headers_str[CONNECTION], header->name_len)) {
		char conn_hdr[MAX_HEADER_VALUE] = { 0 };
		for (size_t i = 0; i < header->value_len; ++i)
			conn_hdr[i] = tolower(header->value[i]);

		if (strstr(conn_hdr, "upgrade")) {
			PARSER_STATE_SET(parser, conn_upgr_hdr, true);
		} else if (strstr(conn_hdr, "close")) {
			PARSER_STATE_SET(parser, conn_close_pending, true);
		} else if (strstr(conn_hdr, "keep-alive")) {
			PARSER_STATE_SET(parser, conn_keep_alive, true);
		} else {
			zcu_log_print_th(LOG_WARNING,
					 "Invalid upgrade value: %.*s",
					 header->value_len, header->value);
		}
	} else if (!strncmp(header->name, http_headers_str[ACCEPT_ENCODING], header->name_len)) {
		parser->accept_encoding_header = true;
	} else if (!strncmp(header->name, http_headers_str[TRANSFER_ENCODING],
			    header->name_len)) {
		int start, end;
		if (str_find_str(&start, &end, header->value, header->value_len,
				 "chunked", sizeof("chunked"))) {
			zcu_log_print_th(LOG_DEBUG, "Chunked enabled");
			parser->chunk_state = CHUNKED_ENABLED;
		}
	} else if (!strncmp(header->name, http_headers_str[CONTENT_LENGTH], header->name_len)) {
		const size_t content_len =
			strtoul(header->value, NULL, 10);

		PARSER_STATE_SET(parser, content_len, content_len);
	} else if (!strncmp(header->name, http_headers_str[HOST], header->name_len)) {
		header->header_off = true;
		zproxy_http_set_virtual_host_header(parser, header->value, header->value_len);
	} else if (!strncmp(header->name, http_headers_str[EXPECT], header->name_len)) {
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
	} else if (!strncmp(header->name, http_headers_str[LOCATION], header->name_len) ||
		   !strncmp(header->name, http_headers_str[CONTENT_LOCATION], header->name_len)) {
		if (!rewrite_location(ctx, header)) {
			zcu_log_print_th(LOG_ERR,
					 "Failed to rewrite header %.*s",
					 header->name_len, header->name);
		}
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
	size_t i;

	// copy value of num_headers since headers may be added
	const size_t num_headers = parser->req.num_headers;
	for (i = 0; i != num_headers; i++) {
		regmatch_t eol{ 0, static_cast<regoff_t>(parser->req.headers[i].line_size) };
		eol.rm_so = 0;
		eol.rm_eo = parser->req.headers[i].line_size;

		zproxy_http_remove_header(&parser->req.headers[i], remove_match, &eol);
		zproxy_http_replace_header(parser, &parser->req.headers[i], repl_ptr, &eol);
		zproxy_http_manage_headers(ctx, &parser->req.headers[i]);
	}

	if (proxy && proxy->header.add_header_req[0])
		zproxy_http_add_header_line(parser->req.headers,
					    &parser->req.num_headers,
					    proxy->header.add_header_req);
	if (service && service->header.add_header_req[0])
		zproxy_http_add_header_line(parser->req.headers,
					    &parser->req.num_headers,
					    service->header.add_header_req);

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
	size_t i;

	// copy value of num_headers since headers may be added
	const size_t num_headers = parser->res.num_headers;
	for (i = 0; i != num_headers; i++) {
		regmatch_t eol{ 0, static_cast<regoff_t>(parser->res.headers[i].line_size) };
		eol.rm_so = 0;
		eol.rm_eo = parser->res.headers[i].line_size;

		zproxy_http_remove_header(&parser->res.headers[i], remove_match, &eol);
		zproxy_http_replace_header(parser, &parser->res.headers[i], repl_ptr, &eol);
		zproxy_http_manage_headers(ctx, &parser->res.headers[i]);
	}

	if (proxy && proxy->header.add_header_res[0])
		zproxy_http_add_header_line(parser->res.headers,
					    &parser->res.num_headers,
					    proxy->header.add_header_res);
	if (service && service->header.add_header_res[0])
		zproxy_http_add_header_line(parser->res.headers,
					    &parser->res.num_headers,
					    service->header.add_header_res);

	if (parser->req.upgrade_header && parser->req.conn_upgr_hdr &&
	    parser->res.upgrade_header && parser->res.conn_upgr_hdr) {
		parser->websocket = true;
		zcu_log_print_th(LOG_DEBUG, "Websocket enabled");
	}

	// TODO: add other standard headers, cookies, etc

	return 0;
}

static int naive_search(const char *stack, int stack_size,
                        const char *needle, int needle_len, int *partial)
{
	int i = 0, j = *partial;

	while (i < stack_size) {
		/* matching, keep looking ahead. */
		if (stack[i] == needle[j]) {
			j++;
			i++;

			/* full match! */
			if (j == needle_len)
				break;

			continue;
		}
		/* backtrack */
		if (j > 0) {
			i -= j;
			j = 0;
		}

		if (i < 0)
			i = 0;
		else
			i++;
	}

	/* full match! */
	if (j == needle_len)
		return j;

	*partial = j;

	return -1;
}

static const char chunk_trailer[] = "\r\n0\r\n\r\n";
#define CHUNK_TRAILER_SIZE	7

static bool http_last_chunk(const char *data, size_t data_size, int *partial)
{
	int match;

	match = naive_search(data, data_size, chunk_trailer, CHUNK_TRAILER_SIZE,
			     partial);
	if (match == CHUNK_TRAILER_SIZE) {
		zcu_log_print_th(LOG_DEBUG, "%s():%d: last chunk",
				 __FUNCTION__, __LINE__);
		return true;
	}
	zcu_log_print_th(LOG_DEBUG, "last chunk not yet seen");

	return false;
}

/*int zproxy_http_handle_body(struct zproxy_http_parser *parser)
{
	message_length = buf_len;
	message = (char *)buf;

	message_total_bytes += bytes;


	if (parser->chunk_state == CHUNKED_ENABLED) {
		if (!http_last_chunk(message, message_length,
				     &partial_last_chunk))
			return -1;

		parser->chunk_state = CHUNKED_LAST_CHUNK;
	} else {
		if (content_length > 0)
			message_bytes_left -= message_length;
	}

	return 1;
}*/

int zproxy_http_update_stats(struct zproxy_http_parser *parser,
			     const struct zproxy_backend_cfg *backend_cfg,
			     const enum CONN_STATE new_state)
{
	struct zproxy_http_state *http_state = parser->http_state;
	int ret = 1;

	zcu_log_print_th(LOG_DEBUG, "Changing stats: %d -> %d",
			 parser->conn_state, new_state);

	if (new_state == parser->conn_state)
		return ret;

	switch (parser->conn_state) {
		case NEW_CONN:
			zproxy_stats_listener_dec_conn_established(http_state);
			zproxy_stats_listener_dec_conn_pending(http_state);
			break;
		case BCK_CONN:
			zproxy_stats_listener_dec_conn_established(http_state);
			zproxy_stats_backend_dec_conn_pending(http_state, backend_cfg);
			break;
		case ESTABLISHED:
			zproxy_stats_listener_dec_conn_established(http_state);
			zproxy_stats_backend_dec_conn_established(http_state, backend_cfg);
			break;
		case UNDEF:
			break;
		default:
			ret = -1;
			break;
	}

	if (ret < 0) {
		zcu_log_print_th(LOG_ERR,
				 "The stream stats are not defined: %d",
				 parser->conn_state);
		return ret;
	}

	parser->conn_state = new_state;

	switch (parser->conn_state) {
		case NEW_CONN:
			zproxy_stats_listener_inc_conn_established(http_state);
			zproxy_stats_listener_inc_conn_pending(http_state);
			break;
		case BCK_CONN:
			zproxy_stats_listener_inc_conn_established(http_state);
			zproxy_stats_backend_inc_conn_pending(http_state, backend_cfg);
			break;
		case ESTABLISHED:
			zproxy_stats_listener_inc_conn_established(http_state);
			zproxy_stats_backend_inc_conn_established(http_state, backend_cfg);
			break;
		case UNDEF:
			break;
		default:
			ret = -1;
			break;
	}

	if (ret < 0) {
		zcu_log_print_th(LOG_ERR,
				 "Error setting stats for state: %d -> %d",
				 parser->conn_state, new_state);
	}

	return ret;
}
