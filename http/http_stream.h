//
// Created by abdess on 4/5/18.
//

#ifndef NEW_ZHTTP_HTTP_STREAM_H
#define NEW_ZHTTP_HTTP_STREAM_H

#include "../connection/connection.h"
#include "HttpRequest.h"
#include "HttpStatus.h"
#include "../connection/backend_connection.h"

class HttpStream {
 public:
  HttpStream();
  Connection *getConnection(int fd);
  Connection client_connection;
  BackendConnection backend_connection;
  HttpRequest request;
  HttpResponse response;

  void replyError(HttpStatus::Code code);

  std::string send_e200 =
      "HTTP/1.1 200 OK\r\nContent-Length: 11\r\n\r\nHello World";

};

#endif  // NEW_ZHTTP_HTTP_STREAM_H
