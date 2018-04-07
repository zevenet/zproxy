//
// Created by abdess on 4/5/18.
//

#include "http_stream.h"
Connection &HttpStream::getConnection(int fd) {
  return fd == client_connection.getFileDescriptor() ? client_connection : backend_connection;
}
