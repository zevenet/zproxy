//
// Created by abdess on 4/25/18.
//

#include "ServiceManager.h"

ServiceManager::ServiceManager() {}
Service *ServiceManager::getService(HttpRequest &request) {
  //TODO::Impelement::

  auto service = &services[0];

  return service;
}

bool ServiceManager::addService(ServiceConfig &service_config) {
  Service service(service_config);
  services.push_back(service);
  return true;
}
