//
// Created by abdess on 4/30/18.
//

#include "backend_connection.h"

BackendConnection::BackendConnection() : backend_id(-1), backend(nullptr) {

}
Backend * BackendConnection::getBackend() const {
  return backend;
}

void BackendConnection::setBackend(Backend * bck, bool connected) {
  backend = bck;
  if (bck != nullptr) {
    backend = bck;
    if (connected) {
      bck->increaseConnection();
    } else {
      bck->decreaseConnection();
    }
  }
}

bool BackendConnection::reConnect() {

  return false;
}
