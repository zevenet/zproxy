#ifndef HTTPPARSER_H
#define HTTPPARSER_H
#include <string>
#include "picohttpparser.h"

namespace http_parser {

enum HTTP_VERSION { HTTP_1_0, HTTP_1_1, HTTP_2_0 };
enum PARSE_RESULT { SUCCESS, FAILED, INCOMPLETE, TOOLONG };

enum EVENT_TYPE {
  ON_ALL = 0xff,
  ON_HEADERS = 0x01,
  ON_CONTENT = 0x01 << 1,
  ON_HEADER_FIELD = 0x01 << 2,
};

class HttpParser {
  void onHeaders();
  void onContent();
  void onHeaderField();

 public:
  HttpParser();

  PARSE_RESULT parseRequest(const std::string &data, size_t *used_bytes);
  PARSE_RESULT parseRequest(const char *data, const size_t data_size, size_t *used_bytes);

  PARSE_RESULT parseResponse(const std::string &data, size_t *used_bytes);
  PARSE_RESULT parseResponse(const char *data, const size_t data_size, size_t *used_bytes);

  void printRequest();
  void printResponse();
  void clean();

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

  EVENT_TYPE events;
};
}  // namespace http_parser
#endif  // HTTPPARSER_H
