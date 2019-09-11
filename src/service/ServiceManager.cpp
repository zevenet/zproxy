//
// Created by abdess on 4/25/18.
//

#include "ServiceManager.h"
std::shared_ptr<ServiceManager> ServiceManager::instance;

std::shared_ptr<ServiceManager> ServiceManager::getInstance(ListenerConfig &listener_config) {
  if (instance == nullptr)
    instance =std::shared_ptr<ServiceManager>(new ServiceManager(listener_config));
  return instance;
}

ServiceManager::ServiceManager(ListenerConfig &listener_config)
    : listener_config_(listener_config) {
  ctl::ControlManager::getInstance()->attach(std::ref(*this));
}

ServiceManager::~ServiceManager() {
  Debug::logmsg(LOG_REMOVE, "Destructor");
  for (auto srv : services) {
    delete srv;
  }
//  ctl::ControlManager::getInstance()->deAttach(std::ref(*this));
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
  service->pinned_connection = service_config.pinned_connection == 1;

  // Information related with the setCookie
  if(service_config.becookie != nullptr)
    service->becookie = std::string(service_config.becookie);
  if(service_config.becdomain != nullptr)
    service->becdomain = std::string(service_config.becdomain);
  if(service_config.becpath != nullptr)
    service->becpath = std::string(service_config.becpath);
  service->becage = service_config.becage;
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

  std::unique_ptr<json::JsonObject> root = std::make_unique<JsonObject>();
  root->emplace(JSON_KEYS::ADDRESS,std::make_unique<JsonDataValue>(
                 json::JsonDataValue(listener_config_.address)));
  root->emplace(JSON_KEYS::PORT,std::make_unique<JsonDataValue>(
                 json::JsonDataValue(listener_config_.port)));
  root->emplace(JSON_KEYS::HTTPS,std::make_unique<JsonDataValue>(
                 json::JsonDataValue(listener_config_.ctx != nullptr)));
  auto services_array = std::make_unique<JsonArray>();
  for (auto service : services)
    services_array->emplace_back(service->getServiceJson());
  root->emplace(JSON_KEYS::SERVICES,std::move(services_array));
  auto data = root->stringify();
  return data;
}

bool ServiceManager::isHandler(ctl::CtlTask &task) {
  return task.target == ctl::CTL_HANDLER_TYPE::SERVICE_MANAGER || task.target == ctl::CTL_HANDLER_TYPE::ALL;
}
