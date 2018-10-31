//
// Created by abdess on 5/9/18.
//

//TODO:: Conver to struct with static members

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

enum REQUEST_METHOD {
  //https://www.iana.org/assignments/http-methods/http-methods.xhtml
      RM_NONE,
//Method Name    Saf,//e Idempotent                            Reference
      RM_ACL,//no   yes        [RFC3744, Section 8.1]
  RM_BASELINE_CONTROL,//no   yes        [RFC3253, Section 12.6]
  RM_BIND,//no   yes        [RFC5842, Section 4]
  RM_CHECKIN,//no   yes        [RFC3253, Section 4.4, Section 9.4]
  RM_CHECKOUT,//no   yes        [RFC3253, Section 4.3, Section 8.8]
  RM_CONNECT,//no   no         [RFC7231, Section 4.3.6]
  RM_COPY,//no   yes        [RFC4918, Section 9.8]
  RM_DELETE,//no   yes        [RFC7231, Section 4.3.5]
  RM_GET,//yes  yes        [RFC7231, Section 4.3.1]
  RM_HEAD,//yes  yes        [RFC7231, Section 4.3.2]
  RM_LABEL,//no   yes        [RFC3253, Section 8.2]
  RM_LINK,//no   yes        [RFC2068, Section 19.6.1.2]
  RM_LOCK,//no   no         [RFC4918, Section 9.10]
  RM_MERGE,//no   yes        [RFC3253, Section 11.2]
  RM_MKACTIVITY,//no   yes        [RFC3253, Section 13.5]
  RM_MKCALENDAR,//no   yes        [RFC4791, Section 5.3.1][RFC8144, Section 2.3]
  RM_MKCOL,//no   yes        [RFC4918, Section 9.3][RFC5689, Section 3][RFC8144, Section 2.3]
  RM_MKREDIRECTREF,//no   yes        [RFC4437, Section 6]
  RM_MKWORKSPACE,//no   yes        [RFC3253, Section 6.3]
  RM_MOVE,//no   yes        [RFC4918, Section 9.9]
  RM_OPTIONS,//yes  yes        [RFC7231, Section 4.3.7]
  RM_ORDERPATCH,//no   yes        [RFC3648, Section 7]
  RM_PATCH,//no   no         [RFC5789, Section 2]
  RM_POST,//no   no         [RFC7231, Section 4.3.3]
  RM_PRI,//yes  yes        [RFC7540, Section 3.5]
  RM_PROPFIND,//yes  yes        [RFC4918, Section 9.1][RFC8144, Section 2.1]
  RM_PROPPATCH,//no   yes        [RFC4918, Section 9.2][RFC8144, Section 2.2]
  RM_PUT,//no   yes        [RFC7231, Section 4.3.4]
  RM_REBIND,//no   yes        [RFC5842, Section 6]
  RM_REPORT,//yes  yes        [RFC3253, Section 3.6][RFC8144, Section 2.1]
  RM_SEARCH,//yes  yes        [RFC5323, Section 2]
  RM_TRACE,//yes  yes        [RFC7231, Section 4.3.8]
  RM_UNBIND,//no   yes        [RFC5842, Section 5]
  RM_UNCHECKOUT,//no   yes        [RFC3253, Section 4.5]
  RM_UNLINK,//no   yes        [RFC2068, Section 19.6.1.3]
  RM_UNLOCK,//no   yes        [RFC4918, Section 9.11]
  RM_UPDATE,//no   yes        [RFC3253, Section 7.1]
  RM_UPDATEREDIRECTREF,//no   yes        [RFC4437, Section 7]
  RM_VERSION_CONTROL,//no   yes        [RFC3253, Section 3.5]
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
/*
//inline std::string
//getHeaderNameString(HTTP_HEADER_NAME
//header) {
//switch (header) {
//case H_ACCEPT: return "accept";
//case H_ACCEPT_CHARSET: return "accept-charset";
//case H_ACCEPT_ENCODING: return "accept-encoding";
//case H_ACCEPT_LANGUAGE: return "accept-language";
//case H_ACCEPT_RANGES: return "accept-ranges";
//case H_ACCESS_CONTROL_ALLOW_CREDENTIALS: return "access-control-allow-credentials";
//case H_ACCESS_CONTROL_ALLOW_HEADERS: return "access-control-allow-headers";
//case H_ACCESS_CONTROL_ALLOW_METHODS: return "access-control-allow-methods";
//case H_ACCESS_CONTROL_ALLOW_ORIGIN: return "access-control-allow-origin";
//case H_ACCESS_CONTROL_EXPOSE_HEADERS: return "access-control-expose-headers";
//case H_ACCESS_CONTROL_MAX_AGE: return "access-control-max-age";
//case H_ACCESS_CONTROL_REQUEST_HEADERS: return "access-control-request-headers";
//case H_ACCESS_CONTROL_REQUEST_METHOD: return "access-control-request-method";
//case H_AGE: return "age";
//case H_ALLOW: return "allow";
//case H_AUTHORIZATION: return "authorization";
//case H_CACHE_CONTROL: return "cache-control";
//case H_CONNECTION: return "connection";
//case H_CONTENT_DISPOSITION: return "content-disposition";
//case H_CONTENT_ENCODING: return "content-encoding";
//case H_CONTENT_LANGUAGE: return "content-language";
//case H_CONTENT_LENGTH: return "content-length";
//case H_CONTENT_LOCATION: return "content-location";
//case H_CONTENT_RANGE: return "content-range";
//case H_CONTENT_SECURITY_POLICY: return "content-security-policy";
//case H_CONTENT_SECURITY_POLICY_REPORT_ONLY: return "content-security-policy-report-only";
//case H_CONTENT_TYPE: return "content-type";
//case H_COOKIE: return "cookie";
//case H_COOKIE2: return "cookie2";
//case H_DNT: return "dnt";
//case H_DATE: return "date";
//case H_ETAG: return "etag";
//case H_EXPECT: return "expect";
//case H_EXPECT_CT: return "expect-ct";
//case H_EXPIRES: return "expires";
//case H_FORWARDED: return "forwarded";
//case H_FROM: return "from";
//case H_HOST: return "host";
//case H_IF_MATCH: return "if-match";
//case H_IF_MODIFIED_SINCE: return "if-modified-since";
//case H_IF_NONE_MATCH: return "if-none-match";
//case H_IF_RANGE: return "if-range";
//case H_IF_UNMODIFIED_SINCE: return "if-unmodified-since";
//case H_KEEP_ALIVE: return "keep-alive";
//case H_LARGE_ALLOCATION: return "large-allocation";
//case H_LAST_MODIFIED: return "last-modified";
//case H_LOCATION: return "location";
//case H_ORIGIN: return "origin";
//case H_PRAGMA: return "pragma";
//case H_PROXY_AUTHENTICATE: return "proxy-authenticate";
//case H_PROXY_AUTHORIZATION: return "proxy-authorization";
//case H_PUBLIC_KEY_PINS: return "public-key-pins";
//case H_PUBLIC_KEY_PINS_REPORT_ONLY: return "public-key-pins-report-only";
//case H_RANGE: return "range";
//case H_REFERER: return "referer";
//case H_REFERRER_POLICY: return "referrer-policy";
//case H_RETRY_AFTER: return "retry-after";
//case H_SERVER: return "server";
//case H_SET_COOKIE: return "set-cookie";
//case H_SET_COOKIE2: return "set-cookie2";
//case H_SOURCEMAP: return "sourcemap";
//case H_STRICT_TRANSPORT_SECURITY: return "strict-transport-security";
//case H_TE: return "te";
//case H_TIMING_ALLOW_ORIGIN: return "timing-allow-origin";
//case H_TK: return "tk";
//case H_TRAILER: return "trailer";
//case H_TRANSFER_ENCODING: return "transfer-encoding";
//case H_UPGRADE_INSECURE_REQUESTS: return "upgrade-insecure-requests";
//case H_USER_AGENT: return "user-agent";
//case H_VARY: return "vary";
//case H_VIA: return "via";
//case H_WWW_AUTHENTICATE: return "www-authenticate";
//case H_WARNING: return "warning";
//case H_X_CONTENT_TYPE_OPTIONS: return "x-content-type-options";
//case H_X_DNS_PREFETCH_CONTROL: return "x-dns-prefetch-control";
//case H_X_FORWARDED_FOR: return "x-forwarded-for";
//case H_X_FORWARDED_HOST: return "x-forwarded-host";
//case H_X_FORWARDED_PROTO: return "x-forwarded-proto";
//case H_X_FRAME_OPTIONS: return "x-frame-options";
//case H_X_XSS_PROTECTION: return "x-xss-protection";
//}
//}*/
const std::unordered_map<std::string, HTTP_HEADER_NAME> headers_names = {
    {"", H_NONE},
    {"Accept", H_ACCEPT},
    {"Accept-Charset", H_ACCEPT_CHARSET},
    {"Accept-Encoding", H_ACCEPT_ENCODING},
    {"Accept-Language", H_ACCEPT_LANGUAGE},
    {"Accept-Ranges", H_ACCEPT_RANGES},
    {"Access-Control-Allow-Credentials", H_ACCESS_CONTROL_ALLOW_CREDENTIALS},
    {"Access-Control-Allow-Headers", H_ACCESS_CONTROL_ALLOW_HEADERS},
    {"Access-Control-Allow-Methods", H_ACCESS_CONTROL_ALLOW_METHODS},
    {"Access-Control-Allow-Origin", H_ACCESS_CONTROL_ALLOW_ORIGIN},
    {"Access-Control-Expose-Headers", H_ACCESS_CONTROL_EXPOSE_HEADERS},
    {"Access-Control-Max-Age", H_ACCESS_CONTROL_MAX_AGE},
    {"Access-Control-Request-Headers", H_ACCESS_CONTROL_REQUEST_HEADERS},
    {"Access-Control-Request-Method", H_ACCESS_CONTROL_REQUEST_METHOD},
    {"Age", H_AGE},
    {"Allow", H_ALLOW},
    {"Authorization", H_AUTHORIZATION},
    {"Cache-Control", H_CACHE_CONTROL},
    {"Connection", H_CONNECTION},
    {"Content-Disposition", H_CONTENT_DISPOSITION},
    {"Content-Encoding", H_CONTENT_ENCODING},
    {"Content-Language", H_CONTENT_LANGUAGE},
    {"Content-Length", H_CONTENT_LENGTH},
    {"Content-Location", H_CONTENT_LOCATION},
    {"Content-Range", H_CONTENT_RANGE},
    {"Content-Security-Policy", H_CONTENT_SECURITY_POLICY},
    {"Content-Security-Policy-Report-Only", H_CONTENT_SECURITY_POLICY_REPORT_ONLY},
    {"Content-Type", H_CONTENT_TYPE},
    {"Cookie", H_COOKIE},
    {"Cookie2", H_COOKIE2},
    {"DNT", H_DNT},
    {"Date", H_DATE},
    {"ETag", H_ETAG},
    {"Expect", H_EXPECT},
    {"Expect-CT", H_EXPECT_CT},
    {"Expires", H_EXPIRES},
    {"Forwarded", H_FORWARDED},
    {"From", H_FROM},
    {"Host", H_HOST},
    {"If-Match", H_IF_MATCH},
    {"If-Modified-Since", H_IF_MODIFIED_SINCE},
    {"If-None-Match", H_IF_NONE_MATCH},
    {"If-Range", H_IF_RANGE},
    {"If-Unmodified-Since", H_IF_UNMODIFIED_SINCE},
    {"Keep-Alive", H_KEEP_ALIVE},
    {"Large-Allocation", H_LARGE_ALLOCATION},
    {"Last-Modified", H_LAST_MODIFIED},
    {"Location", H_LOCATION},
    {"Origin", H_ORIGIN},
    {"Pragma", H_PRAGMA},
    {"Proxy-Authenticate", H_PROXY_AUTHENTICATE},
    {"Proxy-Authorization", H_PROXY_AUTHORIZATION},
    {"Public-Key-Pins", H_PUBLIC_KEY_PINS},
    {"Public-Key-Pins-Report-Only", H_PUBLIC_KEY_PINS_REPORT_ONLY},
    {"Range", H_RANGE},
    {"Referer", H_REFERER},
    {"Referrer-Policy", H_REFERRER_POLICY},
    {"Retry-After", H_RETRY_AFTER},
    {"Server", H_SERVER},
    {"Set-Cookie", H_SET_COOKIE},
    {"Set-Cookie2", H_SET_COOKIE2},
    {"SourceMap", H_SOURCEMAP},
    {"Strict-Transport-Security", H_STRICT_TRANSPORT_SECURITY},
    {"TE", H_TE},
    {"Timing-Allow-Origin", H_TIMING_ALLOW_ORIGIN},
    {"Tk", H_TK},
    {"Trailer", H_TRAILER},
    {"Transfer-Encoding", H_TRANSFER_ENCODING},
    {"Upgrade-Insecure-Requests", H_UPGRADE_INSECURE_REQUESTS},
    {"User-Agent", H_USER_AGENT},
    {"Vary", H_VARY},
    {"Via", H_VIA},
    {"WWW-Authenticate", H_WWW_AUTHENTICATE},
    {"Warning", H_WARNING},
    {"X-Content-Type-Options", H_X_CONTENT_TYPE_OPTIONS},
    {"X-DNS-Prefetch-Control", H_X_DNS_PREFETCH_CONTROL},
    {"X-Forwarded-For", H_X_FORWARDED_FOR},
    {"X-Forwarded-Host", H_X_FORWARDED_HOST},
    {"X-Forwarded-Proto", H_X_FORWARDED_PROTO},
    {"X-Frame-Options", H_X_FRAME_OPTIONS},
    {"X-XSS-Protection", H_X_XSS_PROTECTION}
};
const std::unordered_map<HTTP_HEADER_NAME, const char *> headers_names_strings = {
    {H_NONE, ""},
    {H_ACCEPT, "Accept"},
    {H_ACCEPT_CHARSET, "Accept-Charset"},
    {H_ACCEPT_ENCODING, "Accept-Encoding"},
    {H_ACCEPT_LANGUAGE, "Accept-Language"},
    {H_ACCEPT_RANGES, "Accept-Ranges"},
    {H_ACCESS_CONTROL_ALLOW_CREDENTIALS, "Access-Control-Allow-Credentials"},
    {H_ACCESS_CONTROL_ALLOW_HEADERS, "Access-Control-Allow-Headers"},
    {H_ACCESS_CONTROL_ALLOW_METHODS, "Access-Control-Allow-Methods"},
    {H_ACCESS_CONTROL_ALLOW_ORIGIN, "Access-Control-Allow-Origin"},
    {H_ACCESS_CONTROL_EXPOSE_HEADERS, "Access-Control-Expose-Headers"},
    {H_ACCESS_CONTROL_MAX_AGE, "Access-Control-Max-Age"},
    {H_ACCESS_CONTROL_REQUEST_HEADERS, "Access-Control-Request-Headers"},
    {H_ACCESS_CONTROL_REQUEST_METHOD, "Access-Control-Request-Method"},
    {H_AGE, "Age"},
    {H_ALLOW, "Allow"},
    {H_AUTHORIZATION, "Authorization"},
    {H_CACHE_CONTROL, "Cache-Control"},
    {H_CONNECTION, "Connection"},
    {H_CONTENT_DISPOSITION, "Content-Disposition"},
    {H_CONTENT_ENCODING, "Content-Encoding"},
    {H_CONTENT_LANGUAGE, "Content-Language"},
    {H_CONTENT_LENGTH, "Content-Length"},
    {H_CONTENT_LOCATION, "Content-Location"},
    {H_CONTENT_RANGE, "Content-Range"},
    {H_CONTENT_SECURITY_POLICY, "Content-Security-Policy"},
    {H_CONTENT_SECURITY_POLICY_REPORT_ONLY, "Content-Security-Policy-Report-Only"},
    {H_CONTENT_TYPE, "Content-Type"},
    {H_COOKIE, "Cookie"},
    {H_COOKIE2, "Cookie2"},
    {H_DNT, "DNT"},
    {H_DATE, "Date"},
    {H_ETAG, "ETag"},
    {H_EXPECT, "Expect"},
    {H_EXPECT_CT, "Expect-CT"},
    {H_EXPIRES, "Expires"},
    {H_FORWARDED, "Forwarded"},
    {H_FROM, "From"},
    {H_HOST, "Host"},
    {H_IF_MATCH, "If-Match"},
    {H_IF_MODIFIED_SINCE, "If-Modified-Since"},
    {H_IF_NONE_MATCH, "If-None-Match"},
    {H_IF_RANGE, "If-Range"},
    {H_IF_UNMODIFIED_SINCE, "If-Unmodified-Since"},
    {H_KEEP_ALIVE, "Keep-Alive"},
    {H_LARGE_ALLOCATION, "Large-Allocation"},
    {H_LAST_MODIFIED, "Last-Modified"},
    {H_LOCATION, "Location"},
    {H_ORIGIN, "Origin"},
    {H_PRAGMA, "Pragma"},
    {H_PROXY_AUTHENTICATE, "Proxy-Authenticate"},
    {H_PROXY_AUTHORIZATION, "Proxy-Authorization"},
    {H_PUBLIC_KEY_PINS, "Public-Key-Pins"},
    {H_PUBLIC_KEY_PINS_REPORT_ONLY, "Public-Key-Pins-Report-Only"},
    {H_RANGE, "Range"},
    {H_REFERER, "Referer"},
    {H_REFERRER_POLICY, "Referrer-Policy"},
    {H_RETRY_AFTER, "Retry-After"},
    {H_SERVER, "Server"},
    {H_SET_COOKIE, "Set-Cookie"},
    {H_SET_COOKIE2, "Set-Cookie2"},
    {H_SOURCEMAP, "SourceMap"},
    {H_STRICT_TRANSPORT_SECURITY, "Strict-Transport-Security"},
    {H_TE, "TE"},
    {H_TIMING_ALLOW_ORIGIN, "Timing-Allow-Origin"},
    {H_TK, "Tk"},
    {H_TRAILER, "Trailer"},
    {H_TRANSFER_ENCODING, "Transfer-Encoding"},
    {H_UPGRADE_INSECURE_REQUESTS, "Upgrade-Insecure-Requests"},
    {H_USER_AGENT, "User-Agent"},
    {H_VARY, "Vary"},
    {H_VIA, "Via"},
    {H_WWW_AUTHENTICATE, "WWW-Authenticate"},
    {H_WARNING, "Warning"},
    {H_X_CONTENT_TYPE_OPTIONS, "X-Content-Type-Options"},
    {H_X_DNS_PREFETCH_CONTROL, "X-DNS-Prefetch-Control"},
    {H_X_FORWARDED_FOR, "X-Forwarded-For"},
    {H_X_FORWARDED_HOST, "X-Forwarded-Host"},
    {H_X_FORWARDED_PROTO, "X-Forwarded-Proto"},
    {H_X_FRAME_OPTIONS, "X-Frame-Options"},
    {H_X_XSS_PROTECTION, "X-XSS-Protection"}
};

const std::unordered_map<REQUEST_METHOD, const char *>
    http_verb_strings{
    {RM_ACL, "ACL"}, {RM_BASELINE_CONTROL, "BASELINE-CONTROL"},
    {RM_BCOPY, "BCOPY"}, {RM_BDELETE, "BDELETE"},
    {RM_BIND, "BIND"}, {RM_BMOVE, "BMOVE"},
    {RM_BPROPFIND, "BPROPFIND"}, {RM_BPROPPATCH, "BPROPPATCH"},
    {RM_CHECKIN, "CHECKIN"}, {RM_CHECKOUT, "CHECKOUT"},
    {RM_CONNECT, "CONNECT"}, {RM_COPY, "COPY"},
    {RM_DELETE, "DELETE"}, {RM_GET, "GET"},
    {RM_HEAD, "HEAD"}, {RM_LABEL, "LABEL"},
    {RM_LINK, "LINK"}, {RM_LOCK, "LOCK"},
    {RM_MERGE, "MERGE"}, {RM_MKACTIVITY, "MKACTIVITY"},
    {RM_MKCALENDAR, "MKCALENDAR"}, {RM_MKCOL, "MKCOL"},
    {RM_MKREDIRECTREF, "MKREDIRECTREF"}, {RM_MKWORKSPACE, "MKWORKSPACE"},
    {RM_MOVE, "MOVE"}, {RM_NOTIFY, "NOTIFY"},
    {RM_OPTIONS, "OPTIONS"}, {RM_ORDERPATCH, "ORDERPATCH"},
    {RM_PATCH, "PATCH"}, {RM_POLL, "POLL"},
    {RM_POST, "POST"}, {RM_PRI, "PRI"},
    {RM_PROPFIND, "PROPFIND"}, {RM_PROPPATCH, "PROPPATCH"},
    {RM_PUT, "PUT"}, {RM_REBIND, "REBIND"},
    {RM_REPORT, "REPORT"}, {RM_RPC_IN_DATA, "RPC_IN_DATA"},
    {RM_RPC_OUT_DATA, "RPC_OUT_DATA"},
    {RM_SEARCH, "SEARCH"}, {RM_SUBSCRIBE, "SUBSCRIBE"},
    {RM_TRACE, "TRACE"}, {RM_UNBIND, "UNBIND"},
    {RM_UNCHECKOUT, "UNCHECKOUT"}, {RM_UNLINK, "UNLINK"},
    {RM_UNLOCK, "UNLOCK"}, {RM_UNSUBSCRIBE, "UNSUBSCRIBE"},
    {RM_UPDATE, "UPDATE"}, {RM_UPDATEREDIRECTREF, "UPDATEREDIRECTREF"},
    {RM_VERSION_CONTROL, "VERSION-CONTROL"}, {RM_X_MS_ENUMATTS, "X_MS_ENUMATTS"}};

const std::unordered_map<std::string, REQUEST_METHOD>
    http_verbs = {
    {"ACL", RM_ACL}, {"BASELINE-CONTROL", RM_BASELINE_CONTROL},
    {"BCOPY", RM_BCOPY}, {"BDELETE", RM_BDELETE},
    {"BIND", RM_BIND}, {"BMOVE", RM_BMOVE},
    {"BPROPFIND", RM_BPROPFIND}, {"BPROPPATCH", RM_BPROPPATCH},
    {"CHECKIN", RM_CHECKIN}, {"CHECKOUT", RM_CHECKOUT},
    {"CONNECT", RM_CONNECT}, {"COPY", RM_COPY},
    {"DELETE", RM_DELETE}, {"GET", RM_GET},
    {"HEAD", RM_HEAD}, {"LABEL", RM_LABEL},
    {"LINK", RM_LINK}, {"LOCK", RM_LOCK},
    {"MERGE", RM_MERGE}, {"MKACTIVITY", RM_MKACTIVITY},
    {"MKCALENDAR", RM_MKCALENDAR}, {"MKCOL", RM_MKCOL},
    {"MKREDIRECTREF", RM_MKREDIRECTREF}, {"MKWORKSPACE", RM_MKWORKSPACE},
    {"MOVE", RM_MOVE}, {"NOTIFY", RM_NOTIFY},
    {"OPTIONS", RM_OPTIONS}, {"ORDERPATCH", RM_ORDERPATCH},
    {"PATCH", RM_PATCH}, {"POLL", RM_POLL},
    {"POST", RM_POST}, {"PRI", RM_PRI},
    {"PROPFIND", RM_PROPFIND}, {"PROPPATCH", RM_PROPPATCH},
    {"PUT", RM_PUT}, {"REBIND", RM_REBIND},
    {"REPORT", RM_REPORT}, {"RPC_IN_DATA", RM_RPC_IN_DATA},
    {"RPC_OUT_DATA", RM_RPC_OUT_DATA}, {"SEARCH", RM_SEARCH},
    {"SUBSCRIBE", RM_SUBSCRIBE}, {"TRACE", RM_TRACE},
    {"UNBIND", RM_UNBIND}, {"UNCHECKOUT", RM_UNCHECKOUT},
    {"UNLINK", RM_UNLINK}, {"UNLOCK", RM_UNLOCK},
    {"UNSUBSCRIBE", RM_UNSUBSCRIBE}, {"UPDATE", RM_UPDATE},
    {"UPDATEREDIRECTREF", RM_UPDATEREDIRECTREF},
    {"VERSION-CONTROL", RM_VERSION_CONTROL},
    {"X_MS_ENUMATTS", RM_X_MS_ENUMATTS}
};

enum HTTP_VERSION { HTTP_1_0, HTTP_1_1, HTTP_2_0 };

enum TRANSFER_ENCODING_TYPE {
  TE_NONE = 0,
  TE_CHUNKED = 0x1,
  TE_COMPRESS = 0x1 << 1,
  TE_DEFLATE = 0x1 << 2,
  TE_GZIP = 0x01 << 3,
  TE_IDENTITY = 0x1 << 4
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
