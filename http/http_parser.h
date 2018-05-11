#ifndef HTTPPARSER_H
#define HTTPPARSER_H
#include <string>
#include "picohttpparser.h"

namespace http_parser {

enum PARSE_RESULT { SUCCESS, FAILED, INCOMPLETE, TOOLONG };

enum EVENT_TYPE {
  ON_ALL = 0xff,
  ON_HEADERS = 0x01,
  ON_CONTENT = 0x01 << 1,
  ON_HEADER_FIELD = 0x01 << 2,
};

class HttpParser {
 public:
  HttpParser();

  PARSE_RESULT parseRequest(const std::string &data, size_t *used_bytes, bool reset = true);
  PARSE_RESULT parseRequest(const char *data, const size_t data_size, size_t *used_bytes, bool reset = true);

  PARSE_RESULT parseResponse(const std::string &data, size_t *used_bytes, bool reset = true);
  PARSE_RESULT parseResponse(const char *data, const size_t data_size, size_t *used_bytes, bool reset = true);

  void printRequest();
  void printResponse();
  void reset_parser();

 private:

  phr_header headers[50];
  size_t num_headers;
  size_t last_length;

  //request
  const char *method;
  size_t method_len;
  int minor_version;
  const char *path;
  size_t path_len;

  //response
  int http_status_code;
  const char *message;
  size_t message_length;

  //headers
  EVENT_TYPE events;
};
}  // namespace http_parser
#endif  // HTTPPARSER_H
