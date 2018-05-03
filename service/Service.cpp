//
// Created by abdess on 4/25/18.
//

#include "Service.h"
#include "../util/Network.h"
Backend *Service::getBackend(Connection &connection) {
  if (backend_set.size() == 0) return nullptr;
  static unsigned long long seed;
  seed++;
  return &backend_set[seed % backend_set.size()];
}

void Service::addBackend(std::string address, int port, int backend_id) {
  Backend config;
  config.address_info = Network::getAddress(address, port);
  if (config.address_info != nullptr) {
    config.address = address;
    config.port = port;
    config.backen_id = backend_id;
    config.timeout = 0;
    backend_set.push_back(config);
  } else {
    Debug::Log("Backend Configuration not valid ", LOG_NOTICE);
  }
}
void Service::addBackend(BackendConfig *backend_config) {

}
Service::Service(ServiceConfig &service_config_) :
    service_config(service_config_) {
  int backend_id = 1;
  for (auto bck = service_config_.backends;
       bck != nullptr;
       bck = bck->next) {
    if (bck->disabled != 1) {
      this->addBackend(bck->address, bck->port, backend_id++);
    } else {
      Debug::Log("Backend " + bck->address + ":" + std::to_string(bck->port) + " disabled.", LOG_NOTICE);
    }
  }
}
