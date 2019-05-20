//
// Created by abdess on 4/25/18.
//

#pragma once

#include <map>
#include <ostream>
#include <vector>
#include "../http/HttpRequest.h"
#include "Service.h"

/** The ServiceManager class contains all the operations related with the
 * management of the services. */
class ServiceManager : public CtlObserver<ctl::CtlTask, std::string> {
  std::vector<Service *> services;

 public:
  /** ListenerConfig from the listener related with all the services managed by
   * the class. */
  ListenerConfig listener_config_;
  /** ServiceManager instance. */
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
