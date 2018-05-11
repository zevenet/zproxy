//
// Created by abdess on 5/9/18.
//
#pragma once
/*//TODO::HTTPHEADER
 *
 * {
      {"Accept", false},
      {"Accept-Charset", false},
      {"Accept-Language", false},
      {"Accept-Encoding", false},
      {"Accept-Ranges", false},    //TODO::partial request
      {"Access-Control-Allow-Credentials", false},
      {"Access-Control-Allow-Headers", false},
      {"Access-Control-Allow-Methods", false},
      {"Access-Control-Allow-Origin", false},
      {"Access-Control-Expose-Headers", false},
      {"Access-Control-Max-Age", false},
      {"Access-Control-Request-Headers", false},
      {"Access-Control-Request-Method", false},
      {"Age", false},
      {"Allow", false},
      {"Authorization", false},
      {"Cache-Control", false},
      {"Connection", false},
      {"Content-Disposition", false},
      {"Content-Encoding", false},
      {"Content-Language", false},
      {"Content-Length", false},
      {"Content-Location", false},
      {"Content-Range", false},
      {"Content-Security-Policy", false},
      {"Content-Security-Policy-Report-Only", false},
      {"Content-Type", false},
      {"Cookie", false},
      {"Cookie2", false},
      {"DNT", false},
      {"Date", false},
      {"ETag", false},
      {"Expect", false},
      {"Expect-CT", false},
      {"Expires", false},
      {"Forwarded", false},
      {"From", false},
      {"Host", false},
      {"If-Match", false},
      {"If-Modified-Since", false},
      {"If-None-Match", false},
      {"If-Range", false},
      {"If-Unmodified-Since", false},
      {"Keep-Alive", false},
      {"Large-Allocation", false},
      {"Last-Modified", false},
      {"Location", false},
      {"Origin", false},
      {"Pragma", false},
      {"Proxy-Authenticate", false},
      {"Proxy-Authorization", false},
      {"Public-Key-Pins", false},
      {"Public-Key-Pins-Report-Only", false},
      {"Range", false},
      {"Referer", false},
      {"Referrer-Policy", false},
      {"Retry-After", false},
      {"Server", false},
      {"Set-Cookie", false},
      {"Set-Cookie2", false},
      {"SourceMap", false},
      {"Strict-Transport-Security", false},
      {"TE", false},
      {"Timing-Allow-Origin", false},
      {"Tk", false},
      {"Trailer", false},
      {"Transfer-Encoding", false},
      {"Upgrade-Insecure-Requests", false},
      {"User-Agent", false},
      {"Vary", false},
      {"Via", false},
      {"WWW-Authenticate", false},
      {"Warning", false},
      {"X-Content-Type-Options", false},
      {"X-DNS-Prefetch-Control", false},
      {"X-Forwarded-For", false},
      {"X-Forwarded-Host", false},
      {"X-Forwarded-Proto", false},
      {"X-Frame-Options", false},
      {"X-XSS-Protection", false},
  }
 * */
#include <string>
#include <unordered_map>
namespace http {

enum HTTP_HEADER_NAME {
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

//extern std::unordered_map<HTTP_HEADER_NAME, std::string> HEADERS_NAMES = {
//    {H_ACCEPT, "accept"},
//    {H_ACCEPT_CHARSET, "accept-charset"},
//    {H_ACCEPT_ENCODING, "accept-encoding"},
//    {H_ACCEPT_LANGUAGE, "accept-language"},
//    {H_ACCEPT_RANGES, "accept-ranges"},
//    {H_ACCESS_CONTROL_ALLOW_CREDENTIALS, "access-control-allow-credentials"},
//    {H_ACCESS_CONTROL_ALLOW_HEADERS, "access-control-allow-headers"},
//    {H_ACCESS_CONTROL_ALLOW_METHODS, "access-control-allow-methods"},
//    {H_ACCESS_CONTROL_ALLOW_ORIGIN, "access-control-allow-origin"},
//    {H_ACCESS_CONTROL_EXPOSE_HEADERS, "access-control-expose-headers"},
//    {H_ACCESS_CONTROL_MAX_AGE, "access-control-max-age"},
//    {H_ACCESS_CONTROL_REQUEST_HEADERS, "access-control-request-headers"},
//    {H_ACCESS_CONTROL_REQUEST_METHOD, "access-control-request-method"},
//    {H_AGE, "age"},
//    {H_ALLOW, "allow"},
//    {H_AUTHORIZATION, "authorization"},
//    {H_CACHE_CONTROL, "cache-control"},
//    {H_CONNECTION, "connection"},
//    {H_CONTENT_DISPOSITION, "content-disposition"},
//    {H_CONTENT_ENCODING, "content-encoding"},
//    {H_CONTENT_LANGUAGE, "content-language"},
//    {H_CONTENT_LENGTH, "content-length"},
//    {H_CONTENT_LOCATION, "content-location"},
//    {H_CONTENT_RANGE, "content-range"},
//    {H_CONTENT_SECURITY_POLICY, "content-security-policy"},
//    {H_CONTENT_SECURITY_POLICY_REPORT_ONLY, "content-security-policy-report-only"},
//    {H_CONTENT_TYPE, "content-type"},
//    {H_COOKIE, "cookie"},
//    {H_COOKIE2, "cookie2"},
//    {H_DNT, "dnt"},
//    {H_DATE, "date"},
//    {H_ETAG, "etag"},
//    {H_EXPECT, "expect"},
//    {H_EXPECT_CT, "expect-ct"},
//    {H_EXPIRES, "expires"},
//    {H_FORWARDED, "forwarded"},
//    {H_FROM, "from"},
//    {H_HOST, "host"},
//    {H_IF_MATCH, "if-match"},
//    {H_IF_MODIFIED_SINCE, "if-modified-since"},
//    {H_IF_NONE_MATCH, "if-none-match"},
//    {H_IF_RANGE, "if-range"},
//    {H_IF_UNMODIFIED_SINCE, "if-unmodified-since"},
//    {H_KEEP_ALIVE, "keep-alive"},
//    {H_LARGE_ALLOCATION, "large-allocation"},
//    {H_LAST_MODIFIED, "last-modified"},
//    {H_LOCATION, "location"},
//    {H_ORIGIN, "origin"},
//    {H_PRAGMA, "pragma"},
//    {H_PROXY_AUTHENTICATE, "proxy-authenticate"},
//    {H_PROXY_AUTHORIZATION, "proxy-authorization"},
//    {H_PUBLIC_KEY_PINS, "public-key-pins"},
//    {H_PUBLIC_KEY_PINS_REPORT_ONLY, "public-key-pins-report-only"},
//    {H_RANGE, "range"},
//    {H_REFERER, "referer"},
//    {H_REFERRER_POLICY, "referrer-policy"},
//    {H_RETRY_AFTER, "retry-after"},
//    {H_SERVER, "server"},
//    {H_SET_COOKIE, "set-cookie"},
//    {H_SET_COOKIE2, "set-cookie2"},
//    {H_SOURCEMAP, "sourcemap"},
//    {H_STRICT_TRANSPORT_SECURITY, "strict-transport-security"},
//    {H_TE, "te"},
//    {H_TIMING_ALLOW_ORIGIN, "timing-allow-origin"},
//    {H_TK, "tk"},
//    {H_TRAILER, "trailer"},
//    {H_TRANSFER_ENCODING, "transfer-encoding"},
//    {H_UPGRADE_INSECURE_REQUESTS, "upgrade-insecure-requests"},
//    {H_USER_AGENT, "user-agent"},
//    {H_VARY, "vary"},
//    {H_VIA, "via"},
//    {H_WWW_AUTHENTICATE, "www-authenticate"},
//    {H_WARNING, "warning"},
//    {H_X_CONTENT_TYPE_OPTIONS, "x-content-type-options"},
//    {H_X_DNS_PREFETCH_CONTROL, "x-dns-prefetch-control"},
//    {H_X_FORWARDED_FOR, "x-forwarded-for"},
//    {H_X_FORWARDED_HOST, "x-forwarded-host"},
//    {H_X_FORWARDED_PROTO, "x-forwarded-proto"},
//    {H_X_FRAME_OPTIONS, "x-frame-options"},
//    {H_X_XSS_PROTECTION, "x-xss-protection"},
//
//};

inline std::string getHeaderNameString(HTTP_HEADER_NAME header) {
  switch (header) {
    case H_ACCEPT: return "accept";
    case H_ACCEPT_CHARSET: return "accept-charset";
    case H_ACCEPT_ENCODING: return "accept-encoding";
    case H_ACCEPT_LANGUAGE: return "accept-language";
    case H_ACCEPT_RANGES: return "accept-ranges";
    case H_ACCESS_CONTROL_ALLOW_CREDENTIALS: return "access-control-allow-credentials";
    case H_ACCESS_CONTROL_ALLOW_HEADERS: return "access-control-allow-headers";
    case H_ACCESS_CONTROL_ALLOW_METHODS: return "access-control-allow-methods";
    case H_ACCESS_CONTROL_ALLOW_ORIGIN: return "access-control-allow-origin";
    case H_ACCESS_CONTROL_EXPOSE_HEADERS: return "access-control-expose-headers";
    case H_ACCESS_CONTROL_MAX_AGE: return "access-control-max-age";
    case H_ACCESS_CONTROL_REQUEST_HEADERS: return "access-control-request-headers";
    case H_ACCESS_CONTROL_REQUEST_METHOD: return "access-control-request-method";
    case H_AGE: return "age";
    case H_ALLOW: return "allow";
    case H_AUTHORIZATION: return "authorization";
    case H_CACHE_CONTROL: return "cache-control";
    case H_CONNECTION: return "connection";
    case H_CONTENT_DISPOSITION: return "content-disposition";
    case H_CONTENT_ENCODING: return "content-encoding";
    case H_CONTENT_LANGUAGE: return "content-language";
    case H_CONTENT_LENGTH: return "content-length";
    case H_CONTENT_LOCATION: return "content-location";
    case H_CONTENT_RANGE: return "content-range";
    case H_CONTENT_SECURITY_POLICY: return "content-security-policy";
    case H_CONTENT_SECURITY_POLICY_REPORT_ONLY: return "content-security-policy-report-only";
    case H_CONTENT_TYPE: return "content-type";
    case H_COOKIE: return "cookie";
    case H_COOKIE2: return "cookie2";
    case H_DNT: return "dnt";
    case H_DATE: return "date";
    case H_ETAG: return "etag";
    case H_EXPECT: return "expect";
    case H_EXPECT_CT: return "expect-ct";
    case H_EXPIRES: return "expires";
    case H_FORWARDED: return "forwarded";
    case H_FROM: return "from";
    case H_HOST: return "host";
    case H_IF_MATCH: return "if-match";
    case H_IF_MODIFIED_SINCE: return "if-modified-since";
    case H_IF_NONE_MATCH: return "if-none-match";
    case H_IF_RANGE: return "if-range";
    case H_IF_UNMODIFIED_SINCE: return "if-unmodified-since";
    case H_KEEP_ALIVE: return "keep-alive";
    case H_LARGE_ALLOCATION: return "large-allocation";
    case H_LAST_MODIFIED: return "last-modified";
    case H_LOCATION: return "location";
    case H_ORIGIN: return "origin";
    case H_PRAGMA: return "pragma";
    case H_PROXY_AUTHENTICATE: return "proxy-authenticate";
    case H_PROXY_AUTHORIZATION: return "proxy-authorization";
    case H_PUBLIC_KEY_PINS: return "public-key-pins";
    case H_PUBLIC_KEY_PINS_REPORT_ONLY: return "public-key-pins-report-only";
    case H_RANGE: return "range";
    case H_REFERER: return "referer";
    case H_REFERRER_POLICY: return "referrer-policy";
    case H_RETRY_AFTER: return "retry-after";
    case H_SERVER: return "server";
    case H_SET_COOKIE: return "set-cookie";
    case H_SET_COOKIE2: return "set-cookie2";
    case H_SOURCEMAP: return "sourcemap";
    case H_STRICT_TRANSPORT_SECURITY: return "strict-transport-security";
    case H_TE: return "te";
    case H_TIMING_ALLOW_ORIGIN: return "timing-allow-origin";
    case H_TK: return "tk";
    case H_TRAILER: return "trailer";
    case H_TRANSFER_ENCODING: return "transfer-encoding";
    case H_UPGRADE_INSECURE_REQUESTS: return "upgrade-insecure-requests";
    case H_USER_AGENT: return "user-agent";
    case H_VARY: return "vary";
    case H_VIA: return "via";
    case H_WWW_AUTHENTICATE: return "www-authenticate";
    case H_WARNING: return "warning";
    case H_X_CONTENT_TYPE_OPTIONS: return "x-content-type-options";
    case H_X_DNS_PREFETCH_CONTROL: return "x-dns-prefetch-control";
    case H_X_FORWARDED_FOR: return "x-forwarded-for";
    case H_X_FORWARDED_HOST: return "x-forwarded-host";
    case H_X_FORWARDED_PROTO: return "x-forwarded-proto";
    case H_X_FRAME_OPTIONS: return "x-frame-options";
    case H_X_XSS_PROTECTION: return "x-xss-protection";
  }
}

enum HTTP_VERSION { HTTP_1_0, HTTP_1_1, HTTP_2_0 };

enum TRANSFER_ENCODING_TYPE {
  NONE = 0,
  CHUNKED = 0x1,
  COMPRESS = 0x1 << 1,
  DEFLATE = 0x1 << 2,
  GZIP = 0x01 << 3,
  IDENTITY = 0x1 << 4
};

enum REQUEST_METHOD {
  CONNECT,
  DELETE,
  GET,
  HEAD,
  OPTIONS,
  PATCH,
  POST,
  PUT,
  TRACE,
};

class http_request_data {
 public:
  HTTP_VERSION http_version;
  REQUEST_METHOD request_method;
  TRANSFER_ENCODING_TYPE transfer_encoding_type;
  std::pair<std::string, std::string>
      autorization_data; //Authorization: Basic YWxhZGRpbjpvcGVuc2VzYW1l //base64 encoded
  bool keep_alive;
  bool CORS_request;
  bool upgrade_protocol; //TODO::transparent mode, pine connection???

};

}