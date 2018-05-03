
#include "http_parser.h"
#include "../debug/Debug.h"
#include "HttpStatus.h"

#define DEBUG_HTTP_PARSER 0

http_parser::HttpParser::HttpParser()
    : method(nullptr),
      method_len(0),
      path(nullptr),
      path_len(0),
      minor_version(-1),
      num_headers(0),
      last_length(0),
      http_status_code(0),
      message(nullptr),
      message_length(0) {}

void http_parser::HttpParser::clean() {
  method = nullptr;
  method_len = 0;
  path = nullptr;
  path_len = 0;
  minor_version = -1;
  num_headers = 0;
  last_length = 0;
  http_status_code = 0;
  message = nullptr;
  message_length = 0;
}

http_parser::PARSE_RESULT http_parser::HttpParser::parseRequest(const std::string &data, size_t *used_bytes) {
  return parseRequest(data.c_str(), data.length(), used_bytes);
}

http_parser::PARSE_RESULT http_parser::HttpParser::parseRequest(const char *data,
                                                                const size_t data_size,
                                                                size_t *used_bytes) {

  num_headers = sizeof(headers) / sizeof(headers[0]);
  auto pret = phr_parse_request(data, data_size, &method,
                                &method_len, &path, &path_len, &minor_version,
                                headers, &num_headers, last_length);
  last_length = data_size;
//  Debug::logmsg(LOG_DEBUG, "request is %d bytes long\n", pret);
  if (pret > 0) {
    *used_bytes = static_cast<size_t>(pret);
#if DEBUG_HTTP_PARSER
    printRequest();
#endif
    return PARSE_RESULT::SUCCESS; /* successfully parsed the request */
  } else if (pret == -1) {    /* request is incomplete, continue the loop */
    return PARSE_RESULT::INCOMPLETE;
  } else if (pret == -2) {
#if DEBUG_HTTP_PARSER
    printRequest();
#endif
    return PARSE_RESULT::SUCCESS;
  }
  return PARSE_RESULT::FAILED;
}
http_parser::PARSE_RESULT http_parser::HttpParser::parseResponse(const std::string &data, size_t *used_bytes) {
  return parseResponse(data.c_str(), data.length(), used_bytes);
}
http_parser::PARSE_RESULT http_parser::HttpParser::parseResponse(const char *data,
                                                                 const size_t data_size,
                                                                 size_t *used_bytes) {
  num_headers = sizeof(headers) / sizeof(headers[0]);
  auto pret = phr_parse_response(data, data_size, &minor_version, &http_status_code, &message, &message_length,
                                 headers, &num_headers, last_length);
  last_length = data_size;
//  Debug::logmsg(LOG_DEBUG, "request is %d bytes long\n", pret);
  if (pret > 0) {
    *used_bytes = static_cast<size_t>(pret);
#if DEBUG_HTTP_PARSER
    printResponse();
#endif
    return PARSE_RESULT::SUCCESS; /* successfully parsed the request */
  } else if (pret == -1) {    /* request is incomplete, continue the loop */
    return PARSE_RESULT::INCOMPLETE;
  } else if (pret == -2) {
#if DEBUG_HTTP_PARSER
    printRequest();
#endif
    return PARSE_RESULT::SUCCESS;
  }
  return PARSE_RESULT::FAILED;
}
void http_parser::HttpParser::printResponse() {
  Debug::logmsg(LOG_DEBUG,
                "HTTP 1.%d %d %s",
                minor_version,
                http_status_code,
                HttpStatus::reasonPhrase(http_status_code).c_str());
  Debug::logmsg(LOG_DEBUG, "headers:");
  for (auto i = 0; i != num_headers; ++i) {
    Debug::logmsg(LOG_DEBUG, "\t%.*s: %.*s", (int) headers[i].name_len,
                  headers[i].name, (int) headers[i].value_len, headers[i].value);
  }
}
void http_parser::HttpParser::printRequest() {
  Debug::logmsg(LOG_DEBUG, "method is %.*s", (int) method_len, method);
  Debug::logmsg(LOG_DEBUG, "path is %.*s", (int) path_len, path);
  Debug::logmsg(LOG_DEBUG, "HTTP version is 1.%d", minor_version);
  Debug::logmsg(LOG_DEBUG, "headers:");
  for (auto i = 0; i != num_headers; ++i) {
    Debug::logmsg(LOG_DEBUG, "\t%.*s: %.*s", (int) headers[i].name_len,
                  headers[i].name, (int) headers[i].value_len, headers[i].value);
  }
}