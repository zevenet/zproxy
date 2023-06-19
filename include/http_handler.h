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

#ifndef _ZPROXY_HTTP_HANDLER_H_
#define _ZPROXY_HTTP_HANDLER_H_

#include "pico_http_parser.h"
#include "session.h"
#include "state.h"

#define MAX_HEADERS				128
#define MAX_EXTRA_HEADERS		24
#define MAX_HEADER_NAME			256
#define MAX_HEADER_VALUE		1024
#define INET_STR_SIZE			16
#define MAX_HEADER_LEN			4096

#define XFORWARDEDFOR_HEADER_SIZE		15
#define HOST_HEADER_SIZE				4
#define EXPIRES_HEADER_SIZE				7
#define PRAGMA_HEADER_SIZE				6
#define LOCATION_HEADER_SIZE			8
#define CONTENTLEN_HEADER_SIZE			14
#define SERVER_HEADER_SIZE				6
#define CACHECONTROL_HEADER_SIZE		13
#define CONTENTTYPE_HEADER_SIZE			12
#define MACRO_VHOST						"${VHOST}"
#define MACRO_VHOST_LEN					8

enum REQUEST_RESULT {
	OK,
	METHOD_NOT_ALLOWED,
	BAD_REQUEST,
	BAD_URL,
	URL_CONTAIN_NULL,
	REQUEST_TOO_LARGE,
	SERVICE_NOT_FOUND,
	BACKEND_NOT_FOUND,
	BACKEND_TIMEOUT,
	GATEWAY_TIMEOUT,
};

enum HTTP_PARSER_STATE {
	ERROR = 0,
	REQ_HEADER_RCV,
	REQ_BODY_RCV,
	RESP_HEADER_RCV,
	RESP_BODY_RCV,
	WAIT_100_CONT,
	TUNNEL,
	CLOSE,
};

enum HTTP_CHUNKED_STATUS {
	CHUNKED_DISABLED = 0,
	CHUNKED_ENABLED,
	CHUNKED_LAST_CHUNK,
};

enum HTTP_REQUEST_METHOD {
	METHOD_NONE,
	ACL,
	BASELINE_CONTROL,
	BCOPY,
	BDELETE,
	BIND,
	BMOVE,
	BPROPFIND,
	BPROPPATCH,
	CHECKIN,
	CHECKOUT,
	CONNECT,
	COPY,
	DELETE,
	GET,
	HEAD,
	LABEL,
	LINK,
	LOCK,
	MERGE,
	MKACTIVITY,
	MKCALENDAR,
	MKCOL,
	MKREDIRECTREF,
	MKWORKSPACE,
	MOVE,
	NOTIFY,
	OPTIONS,
	ORDERPATCH,
	PATCH,
	POLL,
	POST,
	PRI,
	PROPFIND,
	PROPPATCH,
	PUT,
	REBIND,
	REPORT,
	RPC_IN_DATA,
	RPC_OUT_DATA,
	SEARCH,
	SUBSCRIBE,
	TRACE,
	UNBIND,
	UNCHECKOUT,
	UNLINK,
	UNLOCK,
	UNSUBSCRIBE,
	UPDATE,
	UPDATEREDIRECTREF,
	VERSION_CONTROL,
	X_MS_ENUMATTS,
	REQUEST_METHOD_MAX,
};

enum HTTP_HEADER_NAME {
	HEADER_NONE,
	ACCEPT,
	ACCEPT_CHARSET,
	ACCEPT_ENCODING,
	ACCEPT_LANGUAGE,
	ACCEPT_RANGES,
	ACCESS_CONTROL_ALLOW_CREDENTIALS,
	ACCESS_CONTROL_ALLOW_HEADERS,
	ACCESS_CONTROL_ALLOW_METHODS,
	ACCESS_CONTROL_ALLOW_ORIGIN,
	ACCESS_CONTROL_EXPOSE_HEADERS,
	ACCESS_CONTROL_MAX_AGE,
	ACCESS_CONTROL_REQUEST_HEADERS,
	ACCESS_CONTROL_REQUEST_METHOD,
	AGE,
	ALLOW,
	AUTHORIZATION,
	CACHE_CONTROL,
	CONNECTION, // hop-by-hop
	CONTENT_DISPOSITION,
	CONTENT_ENCODING,
	CONTENT_LANGUAGE,
	CONTENT_LENGTH,
	CONTENT_LOCATION,
	CONTENT_RANGE,
	CONTENT_SECURITY_POLICY,
	CONTENT_SECURITY_POLICY_REPORT_ONLY,
	CONTENT_TYPE,
	COOKIE,
	COOKIE2,
	DNT,
	DATE,
	DESTINATION,
	ETAG,
	EXPECT,
	EXPECT_CT,
	EXPIRES,
	FORWARDED,
	FROM,
	HOST,
	IF_MATCH,
	IF_MODIFIED_SINCE,
	IF_NONE_MATCH,
	IF_RANGE,
	IF_UNMODIFIED_SINCE,
	KEEP_ALIVE, // hop-by-hop
	LARGE_ALLOCATION,
	LAST_MODIFIED,
	LOCATION,
	ORIGIN,
	PRAGMA,
	PROXY_AUTHENTICATE, // hop-by-hop
	PROXY_AUTHORIZATION, // hop-by-hop
	PUBLIC_KEY_PINS,
	PUBLIC_KEY_PINS_REPORT_ONLY,
	RANGE,
	REFERER,
	REFERRER_POLICY,
	RETRY_AFTER,
	SERVER,
	SET_COOKIE,
	SET_COOKIE2,
	SOURCEMAP,
	STRICT_TRANSPORT_SECURITY,
	TE, // hop-by-hop
	TIMING_ALLOW_ORIGIN,
	TK,
	TRAILER, // hop-by-hop
	TRANSFER_ENCODING, // hop-by-hop
	UPGRADE,
	UPGRADE_INSECURE_REQUESTS, // hop-by-hop?
	USER_AGENT,
	VARY,
	VIA,
	WWW_AUTHENTICATE,
	WARNING,
	X_CONTENT_TYPE_OPTIONS,
	X_DNS_PREFETCH_CONTROL,
	X_FORWARDED_FOR,
	X_FORWARDED_HOST,
	X_FORWARDED_PROTO,
	X_FRAME_OPTIONS,
	X_XSS_PROTECTION,
	X_SSL_SUBJECT,
	X_SSL_ISSUER,
	X_SSL_CIPHER,
	X_SSL_NOTBEFORE,
	X_SSL_NOTAFTER,
	X_SSL_SERIAL,
	X_SSL_CERTIFICATE,
	_MAX_HTTP_HEADER_NAME
};

extern const char *http_headers_str[_MAX_HTTP_HEADER_NAME];

struct zproxy_http_parser {
	struct zproxy_service_cfg	*service_cfg;
	enum HTTP_PARSER_STATE		state;
	enum HTTP_CHUNKED_STATUS	chunk_state;
	bool				websocket;
	struct zproxy_http_state	*http_state;

	phr_header virtual_host_hdr;
	phr_header *destination_hdr;
	phr_header *x_forwarded_for_hdr;
	bool expect_100_cont_hdr;
	bool accept_encoding_header;

	struct {
		char *method;
		size_t method_len;
		char *path;
		size_t path_len;
		int minor_version;
		phr_header headers[MAX_HEADERS];
		size_t num_headers;
		size_t last_length;
		const char *buf_cpy;
		size_t buf_cpy_len;
		size_t buf_cpy_siz;
		const char *body;
		size_t body_len;
		size_t content_len;
	} req;

	struct {
		char *message;
		size_t message_len;
		int minor_version;
		int status_code;
		phr_header headers[MAX_HEADERS];
		size_t num_headers;
		size_t last_length;
		const char *buf_cpy;
		size_t buf_cpy_len;
		size_t buf_cpy_siz;
		const char *body;
		size_t body_len;
		size_t content_len;
	} res;
};

struct zproxy_http_parser *zproxy_http_parser_alloc(void);
int zproxy_http_parser_free(struct zproxy_http_parser *parser);
int zproxy_http_parser_reset(struct zproxy_http_parser *parser);
int zproxy_http_handle_request_headers(struct zproxy_http_ctx *ctx);
int zproxy_http_handle_response_headers(struct zproxy_http_ctx *ctx);
void zproxy_http_set_virtual_host_header(struct zproxy_http_parser *parser,
					 const char *str, size_t str_len);
void zproxy_http_set_destination_header(void);
struct phr_header * zproxy_http_add_header(struct phr_header *headers,
					   size_t *num_headers, const char *name,
					   size_t name_len, const char *value,
					   size_t value_len);

#endif
