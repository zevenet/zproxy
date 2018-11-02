//
// Created by abdess on 4/30/18.
//

#pragma once

#include "../service/backend.h"
#include "connection.h"
#include <chrono>

class BackendConnection : public Connection {
  int backend_id;
  Backend *backend;

public:
  std::chrono::steady_clock::time_point time_start;
  Backend *getBackend() const;
  void setBackend(Backend *backend, bool connected);

public:
  BackendConnection();
  bool reConnect();
};
