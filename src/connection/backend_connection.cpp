//
// Created by abdess on 4/30/18.
//

#include "backend_connection.h"

BackendConnection::BackendConnection() : backend_id(-1), backend(nullptr) {

}
Backend * BackendConnection::getBackend() const {
  return backend;
}

void BackendConnection::setBackend(Backend * bck) {
  backend = bck; 
}

bool BackendConnection::reConnect() {

  return false;
}
