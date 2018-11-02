#ifndef HTTPPARSER_H
#define HTTPPARSER_H
#include "http.h"
#include "picohttpparser.h"
#include <map>
#include <string>

namespace http_parser {

#define cmp_header_name(header, val)                                           \
  header->name_len == strlen(val) &&                                           \
      strncasecmp(header->name, val, header->name_len) == 0
#define cmp_header_value(header, val)                                          \
  header->value_len == strlen(val) &&                                          \
      strncasecmp(header->value, val, header->value_len) == 0

enum class PARSE_RESULT { SUCCESS, FAILED, INCOMPLETE, TOOLONG };

using namespace http;

class HttpData {
public:
  HttpData();

  PARSE_RESULT parseRequest(const std::string &data, size_t *used_bytes,
                            bool reset = true);
  PARSE_RESULT parseRequest(const char *data, const size_t data_size,
                            size_t *used_bytes, bool reset = true);

  PARSE_RESULT parseResponse(const std::string &data, size_t *used_bytes,
                             bool reset = true);
  PARSE_RESULT parseResponse(const char *data, const size_t data_size,
                             size_t *used_bytes, bool reset = true);

  void printRequest();
  void printResponse();
  void reset_parser();
  void setBuffer(char *ext_buffer, int buffer_size);

public:
  std::map<http::HTTP_HEADER_NAME, const std::string> extra_headers;
  inline void addHeader(http::HTTP_HEADER_NAME header_name,
                        const std::string &header_value) {
    char extra_header[MAX_HEADER_LEN];
    sprintf(extra_header, "%s: %s\r\n",
            http::http_info::headers_names_strings.at(header_name),
            header_value.c_str());
    extra_headers.emplace(header_name, std::string(extra_header));
  }
  phr_header headers[50];
  char *buffer;
  size_t buffer_size;
  size_t last_length;
  size_t num_headers;
  char *request_line;
  size_t request_line_length;
  size_t headers_length;
  // request
  const char *method;
  size_t method_len;
  int minor_version;

  const char *path;
  size_t path_length;
  // response
  int http_status_code;

  const char *status_message;
  char *message;
  size_t message_length;

  // TODO::
  http::HTTP_VERSION http_version;
  http::REQUEST_METHOD request_method;
  http::TRANSFER_ENCODING_TYPE transfer_encoding_type;
  char *getBuffer() const;
};
} // namespace http_parser
#endif // HTTPPARSER_H
