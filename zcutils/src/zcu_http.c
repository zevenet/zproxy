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

#include "zcu_http.h"

const char *ws_str_responses[WS_HTTP_MAX] = {

	 "None" ,
	 "100 Continue" ,
	 "101 Switching Protocols" ,
	 "102 Processing" ,
	 "103 Early Hints" ,
	 "200 OK" ,
	 "201 Created" ,
	 "202 Accepted" ,
	 "203 Non Authoritative Information" ,
	 "204 No Content" ,
	 "205 Reset Content" ,
	 "206 Partial Content" ,
	 "207 Multi Status" ,
	 "208 Already Reported" ,
	 "226 IM Used" ,
	 "300 Multiple Choices" ,
	 "301 Moved Permanently" ,
	 "302 Found" ,
	 "303 See Other" ,
	 "304 Not Modified" ,
	 "305 Use Proxy" ,
	 "307 Temporary Redirect" ,
	 "308 Permanent Redirect" ,
	 "400 Bad Request" ,
	 "401 Unauthorized" ,
	 "402 Payment Required" ,
	 "403 Forbidden" ,
	 "404 Not Found" ,
	 "405 Method Not Allowed" ,
	 "406 Not Acceptable" ,
	 "407 Proxy Authentication Required" ,
	 "408 Request Timeout" ,
	 "409 Conflict" ,
	 "410 Gone" ,
	 "411 Length Required" ,
	 "412 Precondition Failed" ,
	 "413 Payload Too Large" ,
	 "414 URI Too Long" ,
	 "415 Unsupported Media Type" ,
	 "416 Range Not Satisfiable" ,
	 "417 Expectation Failed" ,
	 "421 Misdirected Request" ,
	 "422 Unprocessable Entity" ,
	 "423 Locked" ,
	 "424 Failed Dependency" ,
	 "425 Too Early" ,
	 "426 Upgrade Required" ,
	 "428 Precondition Required" ,
	 "429 Too Many Requests" ,
	 "431 Request Header Fields Too Large" ,
	 "451 Unavailable For Legal Reasons" ,
	 "500 Internal Server Error" ,
	 "501 Not Implemented" ,
	 "502 Bad Gateway" ,
	 "503 Service Unavailable" ,
	 "504 Gateway Timeout" ,
	 "505 HTTP Version Not Supported" ,
	 "506 Variant Also Negotiates" ,
	 "507 Insufficient Storage" ,
	 "508 Loop Detected" ,
	 "510 Not Extended" ,
	 "511 Network Authentication Required" ,
};


enum ws_responses http_to_ws(int code) {
	switch (code) {
	case 100: return WS_HTTP_100; break;
	case 101: return WS_HTTP_101; break;
	case 102: return WS_HTTP_102; break;
	case 103: return WS_HTTP_103; break;
	case 200: return WS_HTTP_200; break;
	case 201: return WS_HTTP_201; break;
	case 202: return WS_HTTP_202; break;
	case 203: return WS_HTTP_203; break;
	case 204: return WS_HTTP_204; break;
	case 205: return WS_HTTP_205; break;
	case 206: return WS_HTTP_206; break;
	case 207: return WS_HTTP_207; break;
	case 208: return WS_HTTP_208; break;
	case 226: return WS_HTTP_226; break;
	case 300: return WS_HTTP_300; break;
	case 301: return WS_HTTP_301; break;
	case 302: return WS_HTTP_302; break;
	case 303: return WS_HTTP_303; break;
	case 304: return WS_HTTP_304; break;
	case 305: return WS_HTTP_305; break;
	case 307: return WS_HTTP_307; break;
	case 308: return WS_HTTP_308; break;
	case 400: return WS_HTTP_400; break;
	case 401: return WS_HTTP_401; break;
	case 402: return WS_HTTP_402; break;
	case 403: return WS_HTTP_403; break;
	case 404: return WS_HTTP_404; break;
	case 405: return WS_HTTP_405; break;
	case 406: return WS_HTTP_406; break;
	case 407: return WS_HTTP_407; break;
	case 408: return WS_HTTP_408; break;
	case 409: return WS_HTTP_409; break;
	case 410: return WS_HTTP_410; break;
	case 411: return WS_HTTP_411; break;
	case 412: return WS_HTTP_412; break;
	case 413: return WS_HTTP_413; break;
	case 414: return WS_HTTP_414; break;
	case 415: return WS_HTTP_415; break;
	case 416: return WS_HTTP_416; break;
	case 417: return WS_HTTP_417; break;
	case 421: return WS_HTTP_421; break;
	case 422: return WS_HTTP_422; break;
	case 423: return WS_HTTP_423; break;
	case 424: return WS_HTTP_424; break;
	case 425: return WS_HTTP_425; break;
	case 426: return WS_HTTP_426; break;
	case 428: return WS_HTTP_428; break;
	case 429: return WS_HTTP_429; break;
	case 431: return WS_HTTP_431; break;
	case 451: return WS_HTTP_451; break;
	case 500: return WS_HTTP_500; break;
	case 501: return WS_HTTP_501; break;
	case 502: return WS_HTTP_502; break;
	case 503: return WS_HTTP_503; break;
	case 504: return WS_HTTP_504; break;
	case 505: return WS_HTTP_505; break;
	case 506: return WS_HTTP_506; break;
	case 507: return WS_HTTP_507; break;
	case 508: return WS_HTTP_508; break;
	case 510: return WS_HTTP_510; break;
	case 511: return WS_HTTP_511; break;
	default: return WS_HTTP_MAX; break;
	}
}

int ws_to_http(enum ws_responses wscode) {
	switch (wscode) {
	case WS_HTTP_100: return 100; break;
	case WS_HTTP_101: return 101; break;
	case WS_HTTP_102: return 102; break;
	case WS_HTTP_103: return 103; break;
	case WS_HTTP_200: return 200; break;
	case WS_HTTP_201: return 201; break;
	case WS_HTTP_202: return 202; break;
	case WS_HTTP_203: return 203; break;
	case WS_HTTP_204: return 204; break;
	case WS_HTTP_205: return 205; break;
	case WS_HTTP_206: return 206; break;
	case WS_HTTP_207: return 207; break;
	case WS_HTTP_208: return 208; break;
	case WS_HTTP_226: return 226; break;
	case WS_HTTP_300: return 300; break;
	case WS_HTTP_301: return 301; break;
	case WS_HTTP_302: return 302; break;
	case WS_HTTP_303: return 303; break;
	case WS_HTTP_304: return 304; break;
	case WS_HTTP_305: return 305; break;
	case WS_HTTP_307: return 307; break;
	case WS_HTTP_308: return 308; break;
	case WS_HTTP_400: return 400; break;
	case WS_HTTP_401: return 401; break;
	case WS_HTTP_402: return 402; break;
	case WS_HTTP_403: return 403; break;
	case WS_HTTP_404: return 404; break;
	case WS_HTTP_405: return 405; break;
	case WS_HTTP_406: return 406; break;
	case WS_HTTP_407: return 407; break;
	case WS_HTTP_408: return 408; break;
	case WS_HTTP_409: return 409; break;
	case WS_HTTP_410: return 410; break;
	case WS_HTTP_411: return 411; break;
	case WS_HTTP_412: return 412; break;
	case WS_HTTP_413: return 413; break;
	case WS_HTTP_414: return 414; break;
	case WS_HTTP_415: return 415; break;
	case WS_HTTP_416: return 416; break;
	case WS_HTTP_417: return 417; break;
	case WS_HTTP_421: return 421; break;
	case WS_HTTP_422: return 422; break;
	case WS_HTTP_423: return 423; break;
	case WS_HTTP_424: return 424; break;
	case WS_HTTP_425: return 425; break;
	case WS_HTTP_426: return 426; break;
	case WS_HTTP_428: return 428; break;
	case WS_HTTP_429: return 429; break;
	case WS_HTTP_431: return 431; break;
	case WS_HTTP_451: return 451; break;
	case WS_HTTP_500: return 500; break;
	case WS_HTTP_501: return 501; break;
	case WS_HTTP_502: return 502; break;
	case WS_HTTP_503: return 503; break;
	case WS_HTTP_504: return 504; break;
	case WS_HTTP_505: return 505; break;
	case WS_HTTP_506: return 506; break;
	case WS_HTTP_507: return 507; break;
	case WS_HTTP_508: return 508; break;
	case WS_HTTP_510: return 510; break;
	case WS_HTTP_511: return 511; break;
	default: return WS_HTTP_MAX; break;
	}
}
