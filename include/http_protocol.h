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

#ifndef _ZPROXY_HTTP_PROTOCOL_H_
#define _ZPROXY_HTTP_PROTOCOL_H_

#include <map>
#include <string>
#include <unordered_map>
#include <memory>
#include "zcu_log.h"
#include "zcu_common.h"

#ifndef MAX_HEADER_LEN
#define MAX_HEADER_LEN 4096
#define MAX_HEADERS_SIZE 100
#endif

namespace http
{
constexpr const char *CRLF = "\r\n";
constexpr int CRLF_LEN = 2;

enum class HTTP_VERSION : uint8_t { NONE, HTTP_1_0, HTTP_1_1, HTTP_2_0 };

enum class CHUNKED_STATUS : uint8_t {
	CHUNKED_DISABLED = 0,
	CHUNKED_ENABLED,
	CHUNKED_LAST_CHUNK,
};

enum class CONNECTION_VALUES : uint8_t {
	CLOSE,
	UPGRADE,
	KEEP_ALIVE,
};

enum class UPGRADE_PROTOCOLS : uint8_t {
	NONE,
	WEBSOCKET,
	H2C,
	TLS,
};

enum class TRANSFER_ENCODING_TYPE : uint8_t {
	NONE = 0,
	CHUNKED = 0x1,
	COMPRESS = 0x1 << 1,
	DEFLATE = 0x1 << 2,
	GZIP = 0x01 << 3,
	IDENTITY = 0x1 << 4,
	BR = 0x1 << 5,
};

enum class HTTP_HEADER_NAME : uint16_t {
	NONE,
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
};
#if CACHE_ENABLED
enum WARNING_CODE {
	RESPONSE_STALE = 110, // "Response is Stale"
	REVALIDATION_FAILED = 111, // "Revalidation Failed"
	DISCONNECTED = 112, // "Disconnected Operation"
	HEURISTIC_EXPIRATION = 113, // "Heuristic Expiration"
	MISCELLANEOUS = 199, // "Miscellaneous Warning"
	TRANSFORMATION_APPLIED = 214, // "Transformation Applied"
	PERSISTENT_WARNING = 299, // "Miscellaneous Persistent Warning"
};

enum class CACHE_CONTROL : uint16_t {
	// HTTP Request directives
	MAX_AGE,
	MAX_STALE,
	MIN_FRESH,
	NO_CACHE,
	NO_STORE,
	NO_TRANSFORM,
	ONLY_IF_CACHED,
	// HTTP Response directives
	MUST_REVALIDATE,
	PUBLIC,
	PRIVATE,
	PROXY_REVALIDATE,
	S_MAXAGE,
	// Extension directives if any
};
#endif
enum class REQUEST_METHOD : uint16_t {
	// https://www.iana.org/assignments/http-methods/http-methods.xhtml
	NONE,
	// Method Name    Saf,//e Idempotent                            Reference
	ACL, // no   yes        [RFC3744, Section 8.1]
	BASELINE_CONTROL, // no   yes        [RFC3253, Section 12.6]
	BIND, // no   yes        [RFC5842, Section 4]
	CHECKIN, // no   yes        [RFC3253, Section 4.4, Section 9.4]
	CHECKOUT, // no   yes        [RFC3253, Section 4.3, Section 8.8]
	CONNECT, // no   no         [RFC7231, Section 4.3.6]
	COPY, // no   yes        [RFC4918, Section 9.8]
	DELETE, // no   yes        [RFC7231, Section 4.3.5]
	GET, // yes  yes        [RFC7231, Section 4.3.1]
	HEAD, // yes  yes        [RFC7231, Section 4.3.2]
	LABEL, // no   yes        [RFC3253, Section 8.2]
	LINK, // no   yes        [RFC2068, Section 19.6.1.2]
	LOCK, // no   no         [RFC4918, Section 9.10]
	MERGE, // no   yes        [RFC3253, Section 11.2]
	MKACTIVITY, // no   yes        [RFC3253, Section 13.5]
	MKCALENDAR, // no   yes        [RFC4791, Section 5.3.1][RFC8144,
	// Section 2.3]
	MKCOL, // no   yes        [RFC4918, Section 9.3][RFC5689, Section
	// 3][RFC8144, Section 2.3]
	MKREDIRECTREF, // no   yes        [RFC4437, Section 6]
	MKWORKSPACE, // no   yes        [RFC3253, Section 6.3]
	MOVE, // no   yes        [RFC4918, Section 9.9]
	OPTIONS, // yes  yes        [RFC7231, Section 4.3.7]
	ORDERPATCH, // no   yes        [RFC3648, Section 7]
	PATCH, // no   no         [RFC5789, Section 2]
	POST, // no   no         [RFC7231, Section 4.3.3]
	PRI, // yes  yes        [RFC7540, Section 3.5]
	PROPFIND, // yes  yes        [RFC4918, Section 9.1][RFC8144, Section 2.1]
	PROPPATCH, // no   yes        [RFC4918, Section 9.2][RFC8144, Section 2.2]
	PUT, // no   yes        [RFC7231, Section 4.3.4]
	REBIND, // no   yes        [RFC5842, Section 6]
	REPORT, // yes  yes        [RFC3253, Section 3.6][RFC8144, Section 2.1]
	SEARCH, // yes  yes        [RFC5323, Section 2]
	TRACE, // yes  yes        [RFC7231, Section 4.3.8]
	UNBIND, // no   yes        [RFC5842, Section 5]
	UNCHECKOUT, // no   yes        [RFC3253, Section 4.5]
	UNLINK, // no   yes        [RFC2068, Section 19.6.1.3]
	UNLOCK, // no   yes        [RFC4918, Section 9.11]
	UPDATE, // no   yes        [RFC3253, Section 7.1]
	UPDATEREDIRECTREF, // no   yes        [RFC4437, Section 7]
	VERSION_CONTROL, // no   yes        [RFC3253, Section 3.5]
	SUBSCRIBE,
	UNSUBSCRIBE,
	BPROPPATCH,
	POLL,
	BMOVE,
	BCOPY,
	BDELETE,
	BPROPFIND,
	NOTIFY,
	X_MS_ENUMATTS,
	RPC_IN_DATA,
	RPC_OUT_DATA,
};

struct validation {
	enum class REQUEST_RESULT {
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

	static const std::unordered_map<REQUEST_RESULT, const std::string>
		request_result_reason;

}; // namespace validation

enum class Code {
	NONE = 0,
	Continue = 100 /*[RFC7231, Section 6.2.1] */,
	SwitchingProtocols = 101 /*[RFC7231, Section 6.2.2] */,
	Processing = 102 /*[RFC2518] */,
	EarlyHints = 103 /*[RFC8297] */,
	// 104-199    Unassigned
	OK = 200 /*[RFC7231, Section 6.3.1] */,
	Created = 201 /*[RFC7231, Section 6.3.2] */,
	Accepted = 202 /*[RFC7231, Section 6.3.3] */,
	NonAuthoritativeInformation = 203 /*[RFC7231, Section 6.3.4] */,
	NoContent = 204 /*[RFC7231, Section 6.3.5] */,
	ResetContent = 205 /*[RFC7231, Section 6.3.6] */,
	PartialContent = 206 /*[RFC7233, Section 4.1] */,
	MultiStatus = 207 /*[RFC4918] */,
	AlreadyReported = 208 /*[RFC5842] */,
	// 209-225    Unassigned
	IMUsed = 226 /*[RFC3229] */,
	// 227-299    Unassigned
	MultipleChoices = 300 /*[RFC7231, Section 6.4.1] */,
	MovedPermanently = 301 /*[RFC7231, Section 6.4.2] */,
	Found = 302 /*[RFC7231, Section 6.4.3] */,
	SeeOther = 303 /*[RFC7231, Section 6.4.4] */,
	NotModified = 304 /*[RFC7232, Section 4.1] */,
	UseProxy = 305 /*[RFC7231, Section 6.4.5] */,
	//  (Unused)   = 306 /*[RFC7231, Section 6.4.6]*/,
	TemporaryRedirect = 307 /*[RFC7231, Section 6.4.7] */,
	PermanentRedirect = 308 /*[RFC7538] */,
	// 309-399    Unassigned
	BadRequest = 400 /*[RFC7231, Section 6.5.1] */,
	Unauthorized = 401 /*[RFC7235, Section 3.1] */,
	PaymentRequired = 402 /*[RFC7231, Section 6.5.2] */,
	Forbidden = 403 /*[RFC7231, Section 6.5.3] */,
	NotFound = 404 /*[RFC7231, Section 6.5.4] */,
	MethodNotAllowed = 405 /*[RFC7231, Section 6.5.5] */,
	NotAcceptable = 406 /*[RFC7231, Section 6.5.6] */,
	ProxyAuthenticationRequired = 407 /*[RFC7235, Section 3.2] */,
	RequestTimeout = 408 /*[RFC7231, Section 6.5.7] */,
	Conflict = 409 /*[RFC7231, Section 6.5.8] */,
	Gone = 410 /*[RFC7231, Section 6.5.9] */,
	LengthRequired = 411 /*[RFC7231, Section 6.5.10] */,
	PreconditionFailed = 412 /*[RFC8144, Section 3.2] */,
	PayloadTooLarge = 413 /*[RFC7231, Section 6.5.11] */,
	URITooLong = 414 /*[RFC7231, Section 6.5.12] */,
	UnsupportedMediaType = 415
	/*[RFC7231, Section 6.5.13] [RFC7694, Section 3] */,
	RangeNotSatisfiable = 416 /*[RFC7233, Section 4.4] */,
	ExpectationFailed = 417 /*[RFC7231, Section 6.5.14] */,
	/*418-420     Unassigned */
	MisdirectedRequest = 421 /*[RFC7540, Section 9.1.2] */,
	UnprocessableEntity = 422 /*[RFC4918] */,
	Locked = 423 /*[RFC4918] */,
	FailedDependency = 424 /*[RFC4918] */,
	TooEarly = 425 /*[RFC8470] */,
	UpgradeRequired = 426 /*[RFC7231, Section 6.5.15] */,
	// 427 Unassigned
	PreconditionRequired = 428 /*[RFC6585] */,
	TooManyRequests = 429 /*[RFC6585] */,
	// 430        Unassigned
	RequestHeaderFieldsTooLarge = 431 /*[RFC6585] */,
	// 432-450    Unassigned
	UnavailableForLegalReasons = 451 /*[RFC7725] */,
	// 452-499    Unassigned
	InternalServerError = 500 /*[RFC7231, Section 6.6.1] */,
	NotImplemented = 501 /*[RFC7231, Section 6.6.2] */,
	BadGateway = 502 /*[RFC7231, Section 6.6.3] */,
	ServiceUnavailable = 503 /*[RFC7231, Section 6.6.4] */,
	GatewayTimeout = 504 /*[RFC7231, Section 6.6.5] */,
	HTTPVersionNotSupported = 505 /*[RFC7231, Section 6.6.6] */,
	VariantAlsoNegotiates = 506 /*[RFC2295] */,
	InsufficientStorage = 507 /*[RFC4918] */,
	LoopDetected = 508 /*[RFC5842] */,
	// 509        Unassigned
	NotExtended = 510 /*[RFC2774] */,
	NetworkAuthenticationRequired = 511 /*[RFC6585] */,
	// 512-599    Unassigned
};
struct http_info {
	static const std::map<std::string, HTTP_HEADER_NAME,
#if ENABLE_CI_HEADERS
			      helper::ci_less>
#else
			      std::less<> >
#endif
		headers_names;
	static const std::unordered_map<HTTP_HEADER_NAME, const std::string>
		headers_names_strings;
	static const std::map<std::string, REQUEST_METHOD, std::less<> >
		http_verbs;
	static const std::unordered_map<REQUEST_METHOD, const std::string>
		http_verb_strings;
	static const std::map<std::string, UPGRADE_PROTOCOLS, std::less<> >
		upgrade_protocols;
	static const std::unordered_map<UPGRADE_PROTOCOLS, const std::string>
		upgrade_protocols_strings;
	static const std::unordered_map<http::CONNECTION_VALUES,
					const std::string>
		connection_values_strings;
	static const std::map<std::string, CONNECTION_VALUES, std::less<> >
		connection_values;
	static const std::unordered_map<TRANSFER_ENCODING_TYPE,
					const std::string>
		compression_types_strings;
	static const std::map<std::string, TRANSFER_ENCODING_TYPE, std::less<> >
		compression_types;
#if CACHE_ENABLED
	static const std::unordered_map<CACHE_CONTROL, const std::string>
		cache_control_values_strings;
	static const std::unordered_map<std::string, CACHE_CONTROL>
		cache_control_values;
	static const std::unordered_map<WARNING_CODE, const std::string>
		warning_code_values_strings;
	static const std::unordered_map<std::string, WARNING_CODE>
		warning_code_values;
#endif
	static const std::map<Code, std::string> http_status_code_strings;
	static const std::unordered_map<HTTP_VERSION, const std::string>
		http_version_strings;
};
static const char *reasonPhrase(Code code)
{
	auto it = http_info::http_status_code_strings.find(code);
	if (it != http_info::http_status_code_strings.end())
		return it->second.data();
	else
		return "(UNKNOWN)";
}

static const char *reasonPhrase(int code)
{
	return reasonPhrase(static_cast<Code>(code));
}


static std::string getHttp100ContinueResponse(void)
{
	int http_code = 100;

	std::string response = "HTTP/1.1 ";
	response += std::to_string(http_code);
	response += " ";
	response += reasonPhrase(Code::Continue);
	response += "\r\n\r\n";
	return response;
}

static std::string getHttpResponse(Code status_code,
					  const std::string &status_code_string,
					  const std::string &content_message)
{
	std::string code_error_string;
	if (status_code_string.empty()) {
		code_error_string = reasonPhrase(status_code);
	} else {
		code_error_string = status_code_string;
	}
	std::string body;
	if (content_message.empty()) {
		body += "<html>\n<head><title>";
		body += std::to_string(static_cast<int>(status_code));
		body += " ";
		body += code_error_string;
		body += "</title></head>\n<body bgcolor=\"white\">\n<center><h1>";
		body += std::to_string(static_cast<int>(status_code));
		body += " " + code_error_string;
		body += "</h1></center>\n<hr><center>";
		body += PROJECT_GENERICNAME;
		body += "</center>\n</body>\n</html>";
	} else {
		body += content_message;
	}
	std::string err_response = "HTTP/1.0 ";
	err_response += std::to_string(static_cast<int>(status_code));
	err_response += " ";
	err_response += code_error_string;
	err_response += "\r\nContent-Type: text/html\r\nContent-Length: ";
	err_response += std::to_string(body.length() + 1);
	err_response += "\r\nExpires: now\r\nPragma: no-cache\r\nServer: ";
	err_response += PROJECT_GENERICNAME;
	err_response += "\r\nCache-control: no-cache,no-store\r\n\r\n";
	err_response += body;
	err_response += "\n";
	return err_response;
}
static std::string getRedirectResponse(Code code,
					      const std::string &redirect_url)
{
	// make sure it a safe url
	auto safe_url = std::make_unique<char[]>(ZCU_DEF_BUFFER_SIZE);
	int j = 0;
	for (auto c : redirect_url) {
		if (isalnum(c) || c == '_' || c == '.' || c == ':' ||
		    c == '/' || c == '?' || c == '&' || c == ';' || c == '-' ||
		    c == '=' || c == '%')
			safe_url[j++] = c;
		else {
			sprintf(safe_url.get() + j, "%%%02x", c);
			j += 3;
		}
	}
	safe_url[j] = '\0';
	std::string body = "<html><head><title>Redirect</title></"
			   "head><body><h1>Redirect</h1><p>You "
			   "should go to <a href=";
	body += safe_url.get();
	body += ">";
	body += safe_url.get();
	body += "</a></p></body></html>";

	std::string redirect_response = "HTTP/1.0 ";
	redirect_response += std::to_string(static_cast<int>(code));
	redirect_response += " ";
	redirect_response += reasonPhrase(code);
	redirect_response += "\r\nContent-Type: text/html\r\nContent-Length: ";
	redirect_response += std::to_string(body.length() + 1);
	redirect_response += "\r\nLocation: ";
	redirect_response += safe_url.get();
	redirect_response += "\r\n\r\n";
	redirect_response += body;
	redirect_response += "\n";
	return redirect_response;
}
} // namespace http

#endif
