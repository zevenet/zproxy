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

#ifndef _ZCU_HTTP_H_
#define _ZCU_HTTP_H_

#ifdef __cplusplus
extern "C" {
#endif

#define SRV_MAX_HEADER			300
#define HTTP_PROTO			"HTTP/1.0 "
#define HTTP_LINE_END			"\r\n"
#define HTTP_HEADER_CONTENTLEN		"Content-Length: "
#define HTTP_HEADER_KEY			"Key: "
#define HTTP_HEADER_CONTENT_PLAIN "Content-Type: text/plain" HTTP_LINE_END
#define HTTP_HEADER_CONTENT_JSON "Content-Type: application/json" HTTP_LINE_END
#define HTTP_HEADER_CONTENT_HTML "Content-Type: text/html" HTTP_LINE_END
#define HTTP_HEADER_EXPIRES "Expires: now" HTTP_LINE_END
#define HTTP_HEADER_SERVER "Server: zproxy/" HTTP_LINE_END
#define HTTP_HEADER_LOCATION "Location: "
#define HTTP_HEADER_PRAGMA_NO_CACHE "Pragma: no-cache" HTTP_LINE_END
#define HTTP_HEADER_CACHE_CONTROL "Cache-control: no-cache,no-store" HTTP_LINE_END

enum ws_responses {
	WS_HTTP_0,    	// none
	WS_HTTP_100,    // continue
	WS_HTTP_101,    // switching protocols
	WS_HTTP_102,    // processing
	WS_HTTP_103,    // early hints
	WS_HTTP_200,    // ok
	WS_HTTP_201,    // created
	WS_HTTP_202,    // accepted
	WS_HTTP_203,    // non authoritative information
	WS_HTTP_204,    // no content
	WS_HTTP_205,    // reset content
	WS_HTTP_206,    // partial content
	WS_HTTP_207,    // multi status
	WS_HTTP_208,    // already reported
	WS_HTTP_226,    // imused
	WS_HTTP_300,    // multiple choices
	WS_HTTP_301,    // moved permanently
	WS_HTTP_302,    // found
	WS_HTTP_303,    // seeother
	WS_HTTP_304,    // not modified
	WS_HTTP_305,    // use proxy
	WS_HTTP_307,    // temporary redirect
	WS_HTTP_308,    // permanent redirect
	WS_HTTP_400,    // bad request
	WS_HTTP_401,    // unauthorized
	WS_HTTP_402,    // payment required
	WS_HTTP_403,    // forbidden
	WS_HTTP_404,    // not found
	WS_HTTP_405,    // method not allowed
	WS_HTTP_406,    // not acceptable
	WS_HTTP_407,    // proxy authentication required
	WS_HTTP_408,    // request timeout
	WS_HTTP_409,    // conflict
	WS_HTTP_410,    // gone
	WS_HTTP_411,    // length required
	WS_HTTP_412,    // precondition failed
	WS_HTTP_413,    // payload too large
	WS_HTTP_414,    // uri too long
	WS_HTTP_415,    // unsupported media type
	WS_HTTP_416,    // range not satisfiable
	WS_HTTP_417,    // expectation failed
	WS_HTTP_421,    // misredirected request
	WS_HTTP_422,    // unprocessable entity
	WS_HTTP_423,    // locked
	WS_HTTP_424,    // failed dependency
	WS_HTTP_425,    // too early
	WS_HTTP_426,    // upgrade required
	WS_HTTP_428,    // precondition required
	WS_HTTP_429,    // too many requests
	WS_HTTP_431,    // request header fields too large
	WS_HTTP_451,    // unavailable for legal reasons
	WS_HTTP_500,    // internal server error
	WS_HTTP_501,    // not implemented
	WS_HTTP_502,    // bad gateway
	WS_HTTP_503,    // service unavailable
	WS_HTTP_504,    // gateway timeout
	WS_HTTP_505,    // http version not supported
	WS_HTTP_506,    // variant also negotiates
	WS_HTTP_507,    // insufficient storage
	WS_HTTP_508,    // loop detected
	WS_HTTP_510,    // not extended
	WS_HTTP_511,    // network authentication required
	WS_HTTP_MAX,
};

extern const char *ws_str_responses[WS_HTTP_MAX];

enum ws_responses http_to_ws(int code);
int ws_to_http(enum ws_responses wscode);

#ifdef __cplusplus
}
#endif

#endif /* _ZCU_HTTP_H_ */
