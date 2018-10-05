//
// Created by abdess on 4/30/18.
//

#pragma once

#include "connection.h"
#include "../service/backend.h"

class BackendConnection : public Connection {
  int backend_id;
  Backend  * backend;
 public:
  Backend * getBackend() const;
  void setBackend(Backend * backend);
 public:
  BackendConnection();

  bool reConnect();
};
