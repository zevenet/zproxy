//
// Created by abdess on 4/5/18.
//

#include "http_stream.h"

Connection *HttpStream::getConnection(int fd) {
  return fd == client_connection.getFileDescriptor() ? &client_connection
                                                     : &backend_connection;
}
HttpStream::HttpStream()
    : request(), response(),
      client_connection(),
      backend_connection() {

}
void HttpStream::replyError(HttpStatus::Code code) {
  auto response_ = HttpStatus::getErrorResponse(code);
  client_connection.write(response_.c_str(), response_.length());
}
