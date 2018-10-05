//
// Created by abdess on 4/25/18.
//

#include "ServiceManager.h"
ServiceManager *ServiceManager::instance /*= new ServiceManager()*/;

ServiceManager *ServiceManager::getInstance() {
  if (instance == nullptr) instance = new ServiceManager();
  return instance;
}

ServiceManager::ServiceManager() {}

ServiceManager::~ServiceManager() {
  for (auto srv : services) {
    delete srv;
  }
}

Service *ServiceManager::getService(HttpRequest &request) {
  // TODO::Impelement::
  for (auto srv : services) {
    if (!srv->service_config.disabled) {
      if (srv->doMatch(request)) {
        Debug::logmsg(LOG_DEBUG, "Service found id:%d , %s", srv->id,
                      srv->service_config.name, LOG_DEBUG);
        return srv;
      }
    }
  }
  return nullptr;
}

bool ServiceManager::addService(ServiceConfig &service_config, int id) {
  Service *service = new Service(service_config);
  service->id = id;
  services.push_back(service);
  return true;
}

std::string ServiceManager::handleTask(ctl::CtlTask &task) {
  if (!this->isHandler(task)) return "";
}

bool ServiceManager::isHandler(ctl::CtlTask &task) {
  return task.target == ctl::CTL_HANDLER_TYPE::CTL_SERVICE_MANAGER;
}
