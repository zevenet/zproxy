//
// Created by abdess on 4/30/18.
//

#pragma once

#include "connection.h"

class BackendConnection : public Connection {
  int backend_id;
 public:
  int getBackendId() const;
  void setBackendId(int backend_id);
 public:
  BackendConnection();

  bool reConnect();
};
