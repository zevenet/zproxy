//
// Created by abdess on 4/5/18.
//

#ifndef NEW_ZHTTP_HTTP_STREAM_H
#define NEW_ZHTTP_HTTP_STREAM_H

#include "../connection/connection.h"

class HttpStream {
 public:
  Connection &getConnection(int fd);
  Connection client_connection;
  Connection backend_connection;

};

#endif //NEW_ZHTTP_HTTP_STREAM_H
