//
// Created by abdess on 1/18/19.
//

#pragma once

#include "SSLContext.h"
#include "../connection/connection.h"
namespace ssl {
class SSLConnectionManager {
public:
  SSLContext *ssl_context;
  IO::IO_RESULT handleDataRead(Connection &ssl_connection);
  bool handleHandshake(Connection &ssl_connection);
  IO::IO_RESULT handleWrite(Connection &ssl_connection, const char *data,
                            size_t data_size,
                            size_t &written);

  SSLConnectionManager();
  virtual ~SSLConnectionManager();
  bool init(SSLContext &context);
  bool init(const ListenerConfig &listener_config);

};
}