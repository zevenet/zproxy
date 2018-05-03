//
// Created by abdess on 4/25/18.
//

#ifndef S_ZHTTP_SERVICEMANAGER_H
#define S_ZHTTP_SERVICEMANAGER_H

#include <map>
#include <ostream>
#include <vector>
#include "Service.h"
#include "../http/HttpRequest.h"

class ServiceManager {

  std::vector<Service> services;

 public:
  ServiceManager();
  Service *getService(HttpRequest &request);
  bool addService(ServiceConfig &service_config);

};

#endif //S_ZHTTP_SERVICEMANAGER_H
