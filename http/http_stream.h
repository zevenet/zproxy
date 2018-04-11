//
// Created by abdess on 4/5/18.
//

#ifndef NEW_ZHTTP_HTTP_STREAM_H
#define NEW_ZHTTP_HTTP_STREAM_H

#include "../connection/connection.h"

class HttpStream {
 public:
  std::string send_e200 =
      "HTTP/1.1 200 OK\r\nContent-Length: 11\r\n\r\nHello World ";
  Connection *getConnection(int fd);
  Connection client_connection;
  Connection backend_connection;
};

#endif  // NEW_ZHTTP_HTTP_STREAM_H
