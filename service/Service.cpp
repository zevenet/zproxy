//
// Created by abdess on 4/25/18.
//

#include "Service.h"
#include "../util/Network.h"
Backend *Service::getBackend(Connection &connection) {
  if (backend_set.size() == 0) return nullptr;
  static unsigned long long seed;
  seed++;
  return backend_set[seed % backend_set.size()];
}

void Service::addBackend(std::string address, int port, int backend_id) {
  Backend *config = new Backend();
  config->address_info = Network::getAddress(address, port);
  if (config->address_info != nullptr) {
    config->address = address;
    config->port = port;
    config->backen_id = backend_id;
    config->timeout = 0;
    config->backend_type = BACKEND_TYPE::REMOTE;
    backend_set.push_back(config);
  } else {
    Debug::Log("Backend Configuration not valid ", LOG_NOTICE);
  }
}

void Service::addBackend(BackendConfig *backend_config, int backend_id) {
  if (backend_config->be_type == 0) {
    this->addBackend(backend_config->address, backend_config->port, backend_id);
  } else {
    //Redirect
    Backend *config = new Backend();
    config->backend_config = *backend_config;
    config->backen_id = backend_id;
    config->timeout = 0;
    config->backend_type = BACKEND_TYPE::REDIRECT;
    backend_set.push_back(config);
  }
}

Service::Service(ServiceConfig &service_config_) :
    service_config(service_config_) {
  int backend_id = 1;
  for (auto bck = service_config_.backends;
       bck != nullptr;
       bck = bck->next) {
    if (!bck->disabled) {
      this->addBackend(bck, backend_id++);
      //this->addBackend(bck->address, bck->port, backend_id++);
    } else {
      Debug::Log("Backend " + bck->address + ":" + std::to_string(bck->port) + " disabled.", LOG_NOTICE);
    }
  }
}
bool Service::doMatch(HttpRequest &request) {
  //TODO::  Benchmark
  //TODO:: Implement parallel predicates ?? benchmark
  //TODO:: Replace PCRE with RE2 --
  MATCHER *m;
  int i, found;

  /* check for request */
  for (m = service_config.url; m; m = m->next)
    if (regexec(&m->pat, request.getRequestLine().c_str(), 0, NULL, 0))
      return false;

  /* check for required headers */
  for (m = service_config.req_head; m; m = m->next) {
    for (found = i = 0; i < (request.num_headers - 1) && !found; i++)
      if (!regexec(&m->pat, request.headers[i].name, 0, NULL, 0))
        found = 1;
    if (!found)
      return false;
  }

  /* check for forbidden headers */
  for (m = service_config.deny_head; m; m = m->next) {
    for (found = i = 0; i < (request.num_headers - 1) && !found; i++)
      if (!regexec(&m->pat, request.headers[i].name, 0, NULL, 0))
        found = 1;
    if (found)
      return false;
  }
  return true;
}
