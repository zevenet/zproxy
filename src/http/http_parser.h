#ifndef HTTPPARSER_H
#define HTTPPARSER_H
#include "http.h"
#include "picohttpparser.h"
#include <string>

namespace http_parser {

#define cmp_header_name(header, val)                                           \
  header->name_len == strlen(val) &&                                           \
    strncasecmp(header->name, val, header->name_len) == 0
#define cmp_header_value(header, val)                                          \
  header->value_len == strlen(val) &&                                          \
    strncasecmp(header->value, val, header->value_len) == 0

enum PARSE_RESULT
{
  SUCCESS,
  FAILED,
  INCOMPLETE,
  TOOLONG
};

enum EVENT_TYPE
{
  ON_ALL = 0xff,
  ON_HEADERS = 0x01,
  ON_CONTENT = 0x01 << 1,
  ON_HEADER_FIELD = 0x01 << 2,
};
using namespace http;

class HttpParser
{
public:
  HttpParser();

  PARSE_RESULT parseRequest(const std::string& data,
                            size_t* used_bytes,
                            bool reset = true);
  PARSE_RESULT parseRequest(const char* data,
                            const size_t data_size,
                            size_t* used_bytes,
                            bool reset = true);

  PARSE_RESULT parseResponse(const std::string& data,
                             size_t* used_bytes,
                             bool reset = true);
  PARSE_RESULT parseResponse(const char* data,
                             const size_t data_size,
                             size_t* used_bytes,
                             bool reset = true);

  void printRequest();
  void printResponse();
  void reset_parser();
  void setBuffer(char* ext_buffer, int buffer_size);

public:
  phr_header headers[50];
  char* buffer;
  size_t buffer_size;
  size_t last_length;
  size_t num_headers;
  char* request_line;
  size_t request_line_length;
  size_t headers_length;
  // request
  const char* method;
  size_t method_len;
  int minor_version;

  const char* path;
  size_t path_length;
  // response
  int http_status_code;

  const char* status_message;
  char* message;
  size_t message_length;
  // headers
  EVENT_TYPE events;
  // TODO::
  http::HTTP_VERSION http_version;
  http::REQUEST_METHOD request_method;
  http::TRANSFER_ENCODING_TYPE transfer_encoding_type;
  char* getBuffer() const;
};
} // namespace http_parser
#endif // HTTPPARSER_H
