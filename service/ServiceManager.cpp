//
// Created by abdess on 4/25/18.
//

#include "ServiceManager.h"

ServiceManager::ServiceManager() {}
Service *ServiceManager::getService(HttpRequest &request) {
  //TODO::Impelement::
  for (auto &srv : services) {
    if (!srv.service_config.disabled) {
      if (srv.doMatch(request)) {
        Debug::Log("Service found " + std::string(srv.service_config.name), LOG_DEBUG);
        return &srv;
      }
    }
  }
  return nullptr;
}

bool ServiceManager::addService(ServiceConfig &service_config) {
  Service service(service_config);
  services.push_back(service);
  return true;
}
