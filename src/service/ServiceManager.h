//
// Created by abdess on 4/25/18.
//

#pragma once

#include <map>
#include <ostream>
#include <vector>
#include "../http/HttpRequest.h"
#include "Service.h"

class ServiceManager : public CtlObserver<ctl::CtlTask, std::string> {
  std::vector<Service *> services;

 public:
  static ServiceManager *instance;
  static ServiceManager *getInstance();
  ServiceManager();
  ~ServiceManager();
  Service *getService(HttpRequest &request);
  bool addService(ServiceConfig &service_config, int id);
  std::string handleTask(ctl::CtlTask &task) override;
  bool isHandler(ctl::CtlTask &task) override;
};
