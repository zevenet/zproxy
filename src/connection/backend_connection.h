//
// Created by abdess on 4/30/18.
//

#pragma once

#include <chrono>
#include "connection.h"
#include "../service/backend.h"

class BackendConnection : public Connection {
  int backend_id;
  Backend  * backend;
 public:
  std::chrono::steady_clock::time_point data_start;
  std::chrono::steady_clock::time_point data_end;
  std::chrono::steady_clock::time_point data_completly_end;
  std::chrono::steady_clock::time_point conn_start;
  std::chrono::steady_clock::time_point conn_end;

  Backend * getBackend() const;
  void setBackend(Backend * backend, bool connected);
 public:
  BackendConnection();

  bool reConnect();
};
