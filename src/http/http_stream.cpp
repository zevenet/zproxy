//
// Created by abdess on 4/5/18.
//

#include "http_stream.h"


HttpStream::HttpStream()
    : request(), response(), client_connection(), backend_connection(),
      timer_fd() {}
void HttpStream::replyError(HttpStatus::Code code, const char *code_string,
                            const char *string) {
  auto response_ = HttpStatus::getHttpResponse(code, code_string, string);
  client_connection.write(response_.c_str(), response_.length());
}

HttpStream::~HttpStream() {}

void HttpStream::replyRedirect(BackendConfig &backend_config) {
  auto response_ = HttpStatus::getRedirectResponse(
      (HttpStatus::Code)backend_config.be_type, backend_config.url);
  client_connection.write(response_.c_str(), response_.length());
}
