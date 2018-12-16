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
  ListenerConfig listener_config_;

 public:
  static ServiceManager *instance;
  static ServiceManager *getInstance(ListenerConfig &listener_config);
  ServiceManager(ListenerConfig &listener_config);
  ~ServiceManager();
  Service *getService(HttpRequest &request);
  std::vector<Service *> getServices();
  bool addService(ServiceConfig &service_config, int id);
  std::string handleTask(ctl::CtlTask &task) override;
  bool isHandler(ctl::CtlTask &task) override;
};
