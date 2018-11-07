//
// Created by abdess on 5/9/18.
//

// TODO:: Conver to struct with static members

#pragma once

#include <string>
#include <unordered_map>
#ifndef MAX_HEADER_LEN
#define MAX_HEADER_LEN 4096
#endif
namespace http {

enum HTTP_VERSION { HTTP_1_0, HTTP_1_1, HTTP_2_0 };

enum TRANSFER_ENCODING_TYPE {
  TE_NONE = 0,
  TE_CHUNKED = 0x1,
  TE_COMPRESS = 0x1 << 1,
  TE_DEFLATE = 0x1 << 2,
  TE_GZIP = 0x01 << 3,
  TE_IDENTITY = 0x1 << 4
};

enum class HTTP_HEADER_NAME {
  H_NONE,
  H_ACCEPT,
  H_ACCEPT_CHARSET,
  H_ACCEPT_ENCODING,
  H_ACCEPT_LANGUAGE,
  H_ACCEPT_RANGES,
  H_ACCESS_CONTROL_ALLOW_CREDENTIALS,
  H_ACCESS_CONTROL_ALLOW_HEADERS,
  H_ACCESS_CONTROL_ALLOW_METHODS,
  H_ACCESS_CONTROL_ALLOW_ORIGIN,
  H_ACCESS_CONTROL_EXPOSE_HEADERS,
  H_ACCESS_CONTROL_MAX_AGE,
  H_ACCESS_CONTROL_REQUEST_HEADERS,
  H_ACCESS_CONTROL_REQUEST_METHOD,
  H_AGE,
  H_ALLOW,
  H_AUTHORIZATION,
  H_CACHE_CONTROL,
  H_CONNECTION,
  H_CONTENT_DISPOSITION,
  H_CONTENT_ENCODING,
  H_CONTENT_LANGUAGE,
  H_CONTENT_LENGTH,
  H_CONTENT_LOCATION,
  H_CONTENT_RANGE,
  H_CONTENT_SECURITY_POLICY,
  H_CONTENT_SECURITY_POLICY_REPORT_ONLY,
  H_CONTENT_TYPE,
  H_COOKIE,
  H_COOKIE2,
  H_DNT,
  H_DATE,
  H_ETAG,
  H_EXPECT,
  H_EXPECT_CT,
  H_EXPIRES,
  H_FORWARDED,
  H_FROM,
  H_HOST,
  H_IF_MATCH,
  H_IF_MODIFIED_SINCE,
  H_IF_NONE_MATCH,
  H_IF_RANGE,
  H_IF_UNMODIFIED_SINCE,
  H_KEEP_ALIVE,
  H_LARGE_ALLOCATION,
  H_LAST_MODIFIED,
  H_LOCATION,
  H_ORIGIN,
  H_PRAGMA,
  H_PROXY_AUTHENTICATE,
  H_PROXY_AUTHORIZATION,
  H_PUBLIC_KEY_PINS,
  H_PUBLIC_KEY_PINS_REPORT_ONLY,
  H_RANGE,
  H_REFERER,
  H_REFERRER_POLICY,
  H_RETRY_AFTER,
  H_SERVER,
  H_SET_COOKIE,
  H_SET_COOKIE2,
  H_SOURCEMAP,
  H_STRICT_TRANSPORT_SECURITY,
  H_TE,
  H_TIMING_ALLOW_ORIGIN,
  H_TK,
  H_TRAILER,
  H_TRANSFER_ENCODING,
  H_UPGRADE_INSECURE_REQUESTS,
  H_USER_AGENT,
  H_VARY,
  H_VIA,
  H_WWW_AUTHENTICATE,
  H_WARNING,
  H_X_CONTENT_TYPE_OPTIONS,
  H_X_DNS_PREFETCH_CONTROL,
  H_X_FORWARDED_FOR,
  H_X_FORWARDED_HOST,
  H_X_FORWARDED_PROTO,
  H_X_FRAME_OPTIONS,
  H_X_XSS_PROTECTION,
};

enum class REQUEST_METHOD {
  // https://www.iana.org/assignments/http-methods/http-methods.xhtml
  RM_NONE,
  // Method Name    Saf,//e Idempotent                            Reference
  RM_ACL,              // no   yes        [RFC3744, Section 8.1]
  RM_BASELINE_CONTROL, // no   yes        [RFC3253, Section 12.6]
  RM_BIND,             // no   yes        [RFC5842, Section 4]
  RM_CHECKIN,          // no   yes        [RFC3253, Section 4.4, Section 9.4]
  RM_CHECKOUT,         // no   yes        [RFC3253, Section 4.3, Section 8.8]
  RM_CONNECT,          // no   no         [RFC7231, Section 4.3.6]
  RM_COPY,             // no   yes        [RFC4918, Section 9.8]
  RM_DELETE,           // no   yes        [RFC7231, Section 4.3.5]
  RM_GET,              // yes  yes        [RFC7231, Section 4.3.1]
  RM_HEAD,             // yes  yes        [RFC7231, Section 4.3.2]
  RM_LABEL,            // no   yes        [RFC3253, Section 8.2]
  RM_LINK,             // no   yes        [RFC2068, Section 19.6.1.2]
  RM_LOCK,             // no   no         [RFC4918, Section 9.10]
  RM_MERGE,            // no   yes        [RFC3253, Section 11.2]
  RM_MKACTIVITY,       // no   yes        [RFC3253, Section 13.5]
  RM_MKCALENDAR,       // no   yes        [RFC4791, Section 5.3.1][RFC8144,
                       // Section 2.3]
  RM_MKCOL,         // no   yes        [RFC4918, Section 9.3][RFC5689, Section
                    // 3][RFC8144, Section 2.3]
  RM_MKREDIRECTREF, // no   yes        [RFC4437, Section 6]
  RM_MKWORKSPACE,   // no   yes        [RFC3253, Section 6.3]
  RM_MOVE,          // no   yes        [RFC4918, Section 9.9]
  RM_OPTIONS,       // yes  yes        [RFC7231, Section 4.3.7]
  RM_ORDERPATCH,    // no   yes        [RFC3648, Section 7]
  RM_PATCH,         // no   no         [RFC5789, Section 2]
  RM_POST,          // no   no         [RFC7231, Section 4.3.3]
  RM_PRI,           // yes  yes        [RFC7540, Section 3.5]
  RM_PROPFIND,   // yes  yes        [RFC4918, Section 9.1][RFC8144, Section 2.1]
  RM_PROPPATCH,  // no   yes        [RFC4918, Section 9.2][RFC8144, Section 2.2]
  RM_PUT,        // no   yes        [RFC7231, Section 4.3.4]
  RM_REBIND,     // no   yes        [RFC5842, Section 6]
  RM_REPORT,     // yes  yes        [RFC3253, Section 3.6][RFC8144, Section 2.1]
  RM_SEARCH,     // yes  yes        [RFC5323, Section 2]
  RM_TRACE,      // yes  yes        [RFC7231, Section 4.3.8]
  RM_UNBIND,     // no   yes        [RFC5842, Section 5]
  RM_UNCHECKOUT, // no   yes        [RFC3253, Section 4.5]
  RM_UNLINK,     // no   yes        [RFC2068, Section 19.6.1.3]
  RM_UNLOCK,     // no   yes        [RFC4918, Section 9.11]
  RM_UPDATE,     // no   yes        [RFC3253, Section 7.1]
  RM_UPDATEREDIRECTREF, // no   yes        [RFC4437, Section 7]
  RM_VERSION_CONTROL,   // no   yes        [RFC3253, Section 3.5]
  RM_SUBSCRIBE,
  RM_UNSUBSCRIBE,
  RM_BPROPPATCH,
  RM_POLL,
  RM_BMOVE,
  RM_BCOPY,
  RM_BDELETE,
  RM_BPROPFIND,
  RM_NOTIFY,
  RM_X_MS_ENUMATTS,
  RM_RPC_IN_DATA,
  RM_RPC_OUT_DATA,
};
struct http_info {
  static const std::unordered_map<std::string, HTTP_HEADER_NAME> headers_names;
  static const std::unordered_map<HTTP_HEADER_NAME, const std::string >
      headers_names_strings;
  static const std::unordered_map<std::string, REQUEST_METHOD> http_verbs;
  static const std::unordered_map<REQUEST_METHOD, const std::string >
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
  TRANSFER_ENCODING_TYPE transfer_encoding_type;
  std::pair<std::string, std::string>
      autorization_data; // Authorization: Basic YWxhZGRpbjpvcGVuc2VzYW1l
                         // //base64 encoded
  bool keep_alive;
  bool CORS_request;
  bool upgrade_protocol; // TODO::transparent mode, pine connection???
};

} // namespace http
