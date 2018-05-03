//
// Created by abdess on 4/30/18.
//

#include "backend_connection.h"

BackendConnection::BackendConnection() : backend_id(-1) {

}
int BackendConnection::getBackendId() const {
  return backend_id;
}
void BackendConnection::setBackendId(int backend_id_) {
  backend_id = backend_id_;
}
bool BackendConnection::reConnect() {

  return false;
}
