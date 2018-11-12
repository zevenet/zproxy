//
// Created by abdess on 5/9/18.
//

// TODO:: Conver to struct with static members

#pragma once

#include <string>
#include <unordered_map>
#ifndef MAX_HEADER_LEN
#define MAX_HEADER_LEN 4096
#define MAX_HEADERS_SIZE 50
#endif

namespace http {

enum class HTTP_VERSION { HTTP_1_0, HTTP_1_1, HTTP_2_0 };

enum class TRANSFER_ENCODING_TYPE : uint8_t {
  NONE = 0,
  CHUNKED = 0x1,
  COMPRESS = 0x1 << 1,
  DEFLATE = 0x1 << 2,
  GZIP = 0x01 << 3,
  IDENTITY = 0x1 << 4
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
  PROXY_AUTHENTICATE,  // hop-by-hop
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
  TRAILER,                   // hop-by-hop
  TRANSFER_ENCODING,         // hop-by-hop
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
};

enum class REQUEST_METHOD : uint16_t {
  // https://www.iana.org/assignments/http-methods/http-methods.xhtml
  NONE,
  // Method Name    Saf,//e Idempotent                            Reference
  ACL,              // no   yes        [RFC3744, Section 8.1]
  BASELINE_CONTROL, // no   yes        [RFC3253, Section 12.6]
  BIND,             // no   yes        [RFC5842, Section 4]
  CHECKIN,          // no   yes        [RFC3253, Section 4.4, Section 9.4]
  CHECKOUT,         // no   yes        [RFC3253, Section 4.3, Section 8.8]
  CONNECT,          // no   no         [RFC7231, Section 4.3.6]
  COPY,             // no   yes        [RFC4918, Section 9.8]
  DELETE,           // no   yes        [RFC7231, Section 4.3.5]
  GET,              // yes  yes        [RFC7231, Section 4.3.1]
  HEAD,             // yes  yes        [RFC7231, Section 4.3.2]
  LABEL,            // no   yes        [RFC3253, Section 8.2]
  LINK,             // no   yes        [RFC2068, Section 19.6.1.2]
  LOCK,             // no   no         [RFC4918, Section 9.10]
  MERGE,            // no   yes        [RFC3253, Section 11.2]
  MKACTIVITY,       // no   yes        [RFC3253, Section 13.5]
  MKCALENDAR,       // no   yes        [RFC4791, Section 5.3.1][RFC8144,
                    // Section 2.3]
  MKCOL,            // no   yes        [RFC4918, Section 9.3][RFC5689, Section
                    // 3][RFC8144, Section 2.3]
  MKREDIRECTREF,    // no   yes        [RFC4437, Section 6]
  MKWORKSPACE,      // no   yes        [RFC3253, Section 6.3]
  MOVE,             // no   yes        [RFC4918, Section 9.9]
  OPTIONS,          // yes  yes        [RFC7231, Section 4.3.7]
  ORDERPATCH,       // no   yes        [RFC3648, Section 7]
  PATCH,            // no   no         [RFC5789, Section 2]
  POST,             // no   no         [RFC7231, Section 4.3.3]
  PRI,              // yes  yes        [RFC7540, Section 3.5]
  PROPFIND,   // yes  yes        [RFC4918, Section 9.1][RFC8144, Section 2.1]
  PROPPATCH,  // no   yes        [RFC4918, Section 9.2][RFC8144, Section 2.2]
  PUT,        // no   yes        [RFC7231, Section 4.3.4]
  REBIND,     // no   yes        [RFC5842, Section 6]
  REPORT,     // yes  yes        [RFC3253, Section 3.6][RFC8144, Section 2.1]
  SEARCH,     // yes  yes        [RFC5323, Section 2]
  TRACE,      // yes  yes        [RFC7231, Section 4.3.8]
  UNBIND,     // no   yes        [RFC5842, Section 5]
  UNCHECKOUT, // no   yes        [RFC3253, Section 4.5]
  UNLINK,     // no   yes        [RFC2068, Section 19.6.1.3]
  UNLOCK,     // no   yes        [RFC4918, Section 9.11]
  UPDATE,     // no   yes        [RFC3253, Section 7.1]
  UPDATEREDIRECTREF, // no   yes        [RFC4437, Section 7]
  VERSION_CONTROL,   // no   yes        [RFC3253, Section 3.5]
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
struct http_info {
  static const std::unordered_map<std::string, HTTP_HEADER_NAME> headers_names;
  static const std::unordered_map<HTTP_HEADER_NAME, const std::string>
      headers_names_strings;
  static const std::unordered_map<std::string, REQUEST_METHOD> http_verbs;
  static const std::unordered_map<REQUEST_METHOD, const std::string>
      http_verb_strings;
};

struct validation { // TODO::FIX this
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
  };

  static const std::unordered_map<REQUEST_RESULT, const std::string>
      request_result_reason;

}; // namespace validation

class http_request_data {
public:
  HTTP_VERSION http_version;
  REQUEST_METHOD request_method;
  http::TRANSFER_ENCODING_TYPE transfer_encoding_type;
  std::pair<std::string, std::string>
      autorization_data; // Authorization: Basic YWxhZGRpbjpvcGVuc2VzYW1l
                         // //base64 encoded
  bool keep_alive;
  bool CORS_request;
  bool upgrade_protocol; // TODO::transparent mode, pine connection???
};

} // namespace http
