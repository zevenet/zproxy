/*
 *    Zevenet zproxy Load Balancer Software License
 *    This file is part of the Zevenet zproxy Load Balancer software package.
 *
 *    Copyright (C) 2019-today ZEVENET SL, Sevilla (Spain)
 *
 *    This program is free software: you can redistribute it and/or modify
 *    it under the terms of the GNU Affero General Public License as
 *    published by the Free Software Foundation, either version 3 of the
 *    License, or any later version.
 *
 *    This program is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *    GNU Affero General Public License for more details.
 *
 *    You should have received a copy of the GNU Affero General Public License
 *    along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 */

#include "service_manager.h"
#include <memory>
#include "../handlers/waf.h"

std::map<int,std::shared_ptr<ServiceManager>> ServiceManager::instance;

std::shared_ptr<ServiceManager> ServiceManager::getInstance(ListenerConfig &listener_config) {
  if (instance[listener_config.id] == nullptr)
    instance[listener_config.id] = std::make_shared<ServiceManager>(listener_config);
  return instance[listener_config.id];
}
std::map<int, std::shared_ptr<ServiceManager>> &ServiceManager::getInstance()
{
  return instance;
}

ServiceManager::ServiceManager(ListenerConfig &listener_config) : listener_config_(listener_config) {
  ctl::ControlManager::getInstance()->attach(std::ref(*this));
}

ServiceManager::~ServiceManager() {
  Logger::logmsg(LOG_REMOVE, "Destructor");
  for (auto srv : services) {
    delete srv;
  }
  //  ctl::ControlManager::getInstance()->deAttach(std::ref(*this));
}

Service *ServiceManager::getService(HttpRequest &request) {
  for (auto srv : services) {
    if (!srv->service_config.disabled) {
      if (srv->doMatch(request)) {
        // Logger::logmsg(LOG_DEBUG, "Service found id:%d , %s", srv->id, srv->service_config.name, LOG_DEBUG);
        return srv;
      }
    }
  }
  return nullptr;
}

std::vector<Service *> ServiceManager::getServices() { return services; }

bool ServiceManager::addService(ServiceConfig &service_config, int id) {
  Service *service = new Service(service_config);
  service->id = id;
  service->name = std::string(service_config.name);
  service->disabled = service_config.disabled;
  service->pinned_connection = service_config.pinned_connection == 1;

  // Information related with the setCookie
  if (service_config.becookie != nullptr) service->becookie = std::string(service_config.becookie);
  if (service_config.becdomain != nullptr) service->becdomain = std::string(service_config.becdomain);
  if (service_config.becpath != nullptr) service->becpath = std::string(service_config.becpath);
  service->becage = service_config.becage;
  services.push_back(service);
  return true;
}

std::string ServiceManager::handleTask(ctl::CtlTask &task) {
  if (!this->isHandler(task)) return "";
  if (task.service_id > -1) {
    for (auto service : services) {
      if (service->isHandler(task)) return service->handleTask(task);
    }
    return JSON_OP_RESULT::ERROR;
  }
  //  Logger::logmsg(LOG_DEBUG, "Service Manager handling task");
  switch (task.subject) {
    #if WAF_ENABLED
    case ctl::CTL_SUBJECT::RELOAD_WAF: {
      switch (task.command) {
        case ctl::CTL_COMMAND::UPDATE: {
          //          auto json_data = JsonParser::parse(task.data);
          auto new_rules = Waf::reloadRules();
          if (new_rules == nullptr) {
            return JSON_OP_RESULT::ERROR;
          }
          this->listener_config_.rules = new_rules;
          return JSON_OP_RESULT::OK;
        }
        default:
          return JSON_OP_RESULT::ERROR;
      }
    }
#endif
    case ctl::CTL_SUBJECT::DEBUG:
      return JSON_OP_RESULT::EMPTY_OBJECT;
    default: {
      std::unique_ptr<json::JsonObject> root = std::make_unique<JsonObject>();
      root->emplace(JSON_KEYS::ADDRESS,
                    std::make_unique<JsonDataValue>(listener_config_.address));
      root->emplace(JSON_KEYS::PORT,
                    std::make_unique<JsonDataValue>(listener_config_.port));
      root->emplace(JSON_KEYS::ID,
                    std::make_unique<JsonDataValue>(listener_config_.id));
      root->emplace(JSON_KEYS::HTTPS, std::make_unique<JsonDataValue>(
                                          listener_config_.ctx != nullptr));
      auto services_array = std::make_unique<JsonArray>();
      for (auto service : services)
        services_array->emplace_back(service->getServiceJson());
      root->emplace(JSON_KEYS::SERVICES, std::move(services_array));
      auto data = root->stringify();
      return data;
    } break;
  }
  return JSON_OP_RESULT::ERROR;
}

bool ServiceManager::isHandler(ctl::CtlTask &task) {
  return (task.target == ctl::CTL_HANDLER_TYPE::SERVICE_MANAGER &&
          task.listener_id == listener_config_.id) ||
         task.target == ctl::CTL_HANDLER_TYPE::ALL;
}
