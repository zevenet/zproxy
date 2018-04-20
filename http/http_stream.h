//
// Created by abdess on 4/5/18.
//

#ifndef NEW_ZHTTP_HTTP_STREAM_H
#define NEW_ZHTTP_HTTP_STREAM_H

#include "../connection/connection.h"
#include "HttpRequest.h"

class HttpStream {
 public:
  HttpStream();
  Connection *getConnection(int fd);
  Connection client_connection;
  Connection backend_connection;
  HttpRequest request;
  HttpResponse response;
};

#endif  // NEW_ZHTTP_HTTP_STREAM_H
