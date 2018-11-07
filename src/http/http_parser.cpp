#include "http_parser.h"
#include <strings.h>
#include "../debug/Debug.h"
#include "../util/common.h"
#include "HttpStatus.h"

#define DEBUG_HTTP_PARSER 0

http_parser::HttpData::HttpData()
    : buffer(nullptr),
      buffer_size(0),
      last_length(0),
      num_headers(0),
      method(nullptr),
      method_len(0),
      minor_version(-1),
      path(nullptr),
      path_length(0),
      http_status_code(0),
      status_message(nullptr),
      message_length(0) {}

void http_parser::HttpData::reset_parser() {
  method = nullptr;
  method_len = 0;
  path = nullptr;
  path_length = 0;
  minor_version = -1;
  num_headers = 0;
  last_length = 0;
  http_status_code = 0;
  status_message = nullptr;
  message_length = 0;
  message_bytes_left = 0;
}

void http_parser::HttpData::setBuffer(char *ext_buffer,
                                      size_t ext_buffer_size) {
  buffer = ext_buffer;
  buffer_size = ext_buffer_size;
}

char *http_parser::HttpData::getBuffer() const { return buffer; }

bool http_parser::HttpData::getHeaderValue(http::HTTP_HEADER_NAME header_name, std::string &out_key)
{
  for (auto i = 0; i != num_headers; ++i) {
    std::string header(headers[i].name, headers[i].name_len);
    std::string header_value(headers[i].value,
                             headers[i].value_len);
    auto header_name_ = http_info::headers_names[header];
    if (header_name_ == header_name) {
        out_key = header_value;
        return true;
    }
  }

  return false;
}

bool http_parser::HttpData::getHeaderValue(std::string header_name, std::string &out_key)
{
  for (auto i = 0; i != num_headers; ++i) {
    std::string header(headers[i].name, headers[i].name_len);

    if (header_name == header) {
      out_key = std::string(headers[i].value, headers[i].value_len);
      return true;
    }
  }
  out_key = "";
  return false;
}

std::string http_parser::HttpData::getUrlParameter(std::string url) {
  std::string expr_= "[;][^?]*";
  std::smatch match;
  std::regex rgx(expr_);
  if (std::regex_search(url, match, rgx)) {
    std::string result = match[0];
    return result.substr(1);
  } else {
    return std::string();
  }
}

std::string http_parser::HttpData::getQueryParameter(std::string url, std::string sess_id) {
  std::string expr_= "[?&]" + sess_id +"=[^&;#]*";
  std::smatch match;
  //TODO: Sacarlo y hacerlo por test para comprobarlo por PCREPOSIX en bench
  std::regex rgx (expr_);
  if (std::regex_search(url, match, rgx)) {
    std::string result = match[0];
    return result.substr(1);
  } else {
    return std::string();
  }
}

http_parser::PARSE_RESULT http_parser::HttpData::parseRequest(
    const std::string &data, size_t *used_bytes, bool reset) {
  return parseRequest(data.c_str(), data.length(), used_bytes, reset);
}

http_parser::PARSE_RESULT http_parser::HttpData::parseRequest(
    const char *data, const size_t data_size, size_t *used_bytes, bool reset) {
  if (LIKELY(reset)) reset_parser();
  buffer = const_cast<char *>(data);
  buffer_size = data_size;
  num_headers = sizeof(headers) / sizeof(headers[0]);
  auto pret = phr_parse_request(data, data_size, &method, &method_len, &path,
                                &path_length, &minor_version, headers,
                                &num_headers, last_length);
  last_length = data_size;
  //  Debug::logmsg(LOG_DEBUG, "request is %d bytes long\n", pret);
  if (pret > 0) {
    *used_bytes = static_cast<size_t>(pret);
    headers_length = pret;
#if DEBUG_HTTP_PARSER
    printRequest();
#endif
    http_version = minor_version == 1 ? HTTP_1_1 : HTTP_1_0;
    message = &buffer[pret];
    message_length = buffer_size - static_cast<size_t>(pret);
    http_message = const_cast<char *>(method);
    http_message_length = static_cast<size_t>(headers[0].name - method);
    //    for (auto i = 0; i < static_cast<int>(num_headers); i++) {
    //      if (std::string(headers[i].name, headers[i].name_len) !=
    //          http::http_info::headers_names_strings.at(
    //              http::HTTP_HEADER_NAME::H_CONTENT_LENGTH))
    //        continue;
    //      message_bytes_left =
    //      static_cast<size_t>(std::atoi(headers[i].value)); break;
    //    }
    return PARSE_RESULT::SUCCESS; /* successfully parsed the request */
  } else if (pret == -2) {        /* request is incomplete, continue the loop */
    return PARSE_RESULT::INCOMPLETE;
  }
  return PARSE_RESULT::FAILED;
}
http_parser::PARSE_RESULT http_parser::HttpData::parseResponse(const std::string &data, size_t *used_bytes, bool reset) {
  return parseResponse(data.c_str(), data.length(), used_bytes);
}
http_parser::PARSE_RESULT http_parser::HttpData::parseResponse(
    const char *data, const size_t data_size, size_t *used_bytes, bool reset) {
  if (LIKELY(reset)) reset_parser();
  buffer = const_cast<char *>(data);
  buffer_size = data_size;
  num_headers = sizeof(headers) / sizeof(headers[0]);
  auto pret = phr_parse_response(
      data, data_size, &minor_version, &http_status_code, &status_message,
      &message_length, headers, &num_headers, last_length);
  last_length = data_size;
  //  Debug::logmsg(LOG_DEBUG, "request is %d bytes long\n", pret);
  if (pret > 0) {
    *used_bytes = static_cast<size_t>(pret);
    headers_length = pret;
    http_message = const_cast<char *>(buffer);
    http_message_length = static_cast<size_t>(headers[0].name - buffer);
    //    for (auto i = 0; i < static_cast<int>(num_headers); i++) {
    //      if (std::string(headers[i].name, headers[i].name_len) !=
    //          http::http_info::headers_names_strings.at(
    //              http::HTTP_HEADER_NAME::H_CONTENT_LENGTH))
    //        continue;
    //      message_bytes_left =
    //      static_cast<size_t>(std::atoi(headers[i].value)); break;
    //    }
    message = &buffer[pret];
    message_length = buffer_size - static_cast<size_t>(pret);
#if DEBUG_HTTP_PARSER
    printResponse();
#endif
    return PARSE_RESULT::SUCCESS; /* successfully parsed the request */
  } else if (pret == -1) { /* response is incomplete, continue the loop */
    return PARSE_RESULT::INCOMPLETE;
  }
  return PARSE_RESULT::FAILED;
}
void http_parser::HttpData::printResponse() {
  Debug::logmsg(LOG_DEBUG, "HTTP 1.%d %d %s", minor_version, http_status_code,
                HttpStatus::reasonPhrase(http_status_code).c_str());
  Debug::logmsg(LOG_DEBUG, "headers:");
  for (auto i = 0; i != num_headers; ++i) {
    Debug::logmsg(LOG_DEBUG, "\t%.*s: %.*s", (int)headers[i].name_len,
                  headers[i].name, (int)headers[i].value_len, headers[i].value);
  }
}
void http_parser::HttpData::printRequest() {
  Debug::logmsg(LOG_DEBUG, "method is %.*s", (int)method_len, method);
  Debug::logmsg(LOG_DEBUG, "path is %.*s", (int)path_length, path);
  Debug::logmsg(LOG_DEBUG, "HTTP version is 1.%d", minor_version);
  Debug::logmsg(LOG_DEBUG, "headers:");
  for (auto i = 0; i != num_headers; ++i) {
    Debug::logmsg(LOG_DEBUG, "\t%.*s: %.*s", (int)headers[i].name_len,
                  headers[i].name, (int)headers[i].value_len, headers[i].value);
  }
}
