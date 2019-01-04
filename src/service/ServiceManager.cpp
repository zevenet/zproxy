//
// Created by abdess on 4/25/18.
//

#include "ServiceManager.h"
ServiceManager *ServiceManager::instance /*= new ServiceManager()*/;

ServiceManager *ServiceManager::getInstance(ListenerConfig &listener_config) {
  if (instance == nullptr)
    instance = new ServiceManager(listener_config);
  return instance;
}

ServiceManager::ServiceManager(ListenerConfig &listener_config)
    : listener_config_(listener_config) {
  ctl::ControlManager::getInstance()->attach(std::ref(*this));
}

ServiceManager::~ServiceManager() {
  for (auto srv : services) {
    delete srv;
  }
  ctl::ControlManager::getInstance()->deAttach(std::ref(*this));
}

Service *ServiceManager::getService(HttpRequest &request) {
  for (auto srv : services) {
    if (!srv->service_config.disabled) {
      if (srv->doMatch(request)) {
        //Debug::logmsg(LOG_DEBUG, "Service found id:%d , %s", srv->id, srv->service_config.name, LOG_DEBUG);
        return srv;
      }
    }
  }
  return nullptr;
}

std::vector<Service *> ServiceManager::getServices(){
  return services;
}

bool ServiceManager::addService(ServiceConfig &service_config, int id) {
  Service *service = new Service(service_config);
  service->id = id;
  service->name = std::string(service_config.name);
  service->disabled = service_config.disabled;
  services.push_back(service);
  return true;
}

std::string ServiceManager::handleTask(ctl::CtlTask &task) {
  if (!this->isHandler(task))
    return "";
  //  Debug::logmsg(LOG_DEBUG, "Service Manager handling task");
  if (task.service_id > -1) {
    for (auto service : services) {
      if (service->isHandler(task))
        return service->handleTask(task);
    }
    return JSON_OP_RESULT::ERROR;
  }

  std::unique_ptr<json::JsonObject> root(new json::JsonObject());
  root->emplace(JSON_KEYS::ADDRESS,
                new json::JsonDataValue(listener_config_.address));
  root->emplace(JSON_KEYS::PORT,
                new json::JsonDataValue(listener_config_.port));
  root->emplace(JSON_KEYS::HTTPS,
                new json::JsonDataValue(listener_config_.ctx != nullptr));
  auto services_array = new json::JsonArray();
  for (auto service : services)
    services_array->push_back(service->getServiceJson());
  root->emplace(JSON_KEYS::SERVICES, services_array);
  auto data = root->stringify();
  return data;
}

bool ServiceManager::isHandler(ctl::CtlTask &task) {
  return task.target == ctl::CTL_HANDLER_TYPE::SERVICE_MANAGER;
}
