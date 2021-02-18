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
#include <utility>
#ifdef WAF_ENABLED
#include "../handlers/waf.h"
#endif

std::map < int, std::shared_ptr < ServiceManager >> ServiceManager::instance;

std::shared_ptr < ServiceManager >
	&ServiceManager::getInstance(std::shared_ptr < ListenerConfig >
				     listener_config)
{
	auto it = instance.find(listener_config->id);
	if (it == instance.end())
		instance[listener_config->id] =
			std::make_shared < ServiceManager > (listener_config);
	return instance[listener_config->id];
}

std::map < int,
	std::shared_ptr < ServiceManager >> & ServiceManager::getInstance()
{
	return instance;
}

ServiceManager::ServiceManager(std::shared_ptr < ListenerConfig >
			       listener_config)
:	
listener_config_(std::move(listener_config)),
id(listener_config_->id), name(listener_config_->name),
disabled(listener_config_->disabled != 0)
{
	if (listener_config_->ctx != nullptr) {
		if (ssl_context != nullptr)
			delete ssl_context;
		ssl_context = new SSLContext();
		is_https_listener = ssl_context->init(listener_config_);
	}
#if WAF_ENABLED
	listener_config_->modsec =
		std::make_shared < modsecurity::ModSecurity > ();
	listener_config_->modsec->setConnectorInformation("zproxy_" +
							  listener_config_->name
							  + "_connector");
	listener_config_->modsec->setServerLogCb(Waf::logModsec);
#endif
	ctl_manager = ctl::ControlManager::getInstance();
	ctl_manager->attach(std::ref(*this));
}

ServiceManager::~ServiceManager()
{
	ctl_manager->deAttach(std::ref(*this));
      for (auto srv:services) {
		delete srv;
	}
	if (ssl_context != nullptr) {
		delete ssl_context;
	}
}

Service *ServiceManager::getService(HttpRequest & request)
{
      for (auto srv:services) {
		if (!srv->service_config.disabled) {
			if (srv->doMatch(request)) {
				zcutils_log_print(LOG_DEBUG,
						  "%s():%d: service found id:%d , %s",
						  __FUNCTION__, __LINE__,
						  srv->id,
						  srv->service_config.name);
				return srv;
			}
		}
	}
	return nullptr;
}

std::vector < Service * >ServiceManager::getServices()
{
	return services;
}

bool ServiceManager::addService(ServiceConfig & service_config, int _id)
{
	auto service = new Service(service_config);
	service->id = _id;
	services.push_back(service);
	return true;
}

std::string ServiceManager::handleTask(ctl::CtlTask & task)
{
	if (!this->isHandler(task))
		return "";
	if (task.service_id > -1) {
	      for (auto service:services) {
			if (service->isHandler(task))
				return service->handleTask(task);
		}
		return JSON_OP_RESULT::ERROR;
	}

	zcutils_log_print(LOG_DEBUG, "%s():%d: service Manager handling task",
			  __FUNCTION__, __LINE__);
	switch (task.command) {
	case ctl::CTL_COMMAND::GET:{
			switch (task.subject) {
			case ctl::CTL_SUBJECT::DEBUG:
				return JSON_OP_RESULT::EMPTY_OBJECT;
			default:{
					std::unique_ptr < json::JsonObject >
						root =
						std::make_unique <
						JsonObject > ();
					root->emplace(JSON_KEYS::ADDRESS,
						      std::make_unique <
						      JsonDataValue >
						      (listener_config_->address));
					root->emplace(JSON_KEYS::PORT,
						      std::make_unique <
						      JsonDataValue >
						      (listener_config_->port));
					root->emplace(JSON_KEYS::ID,
						      std::make_unique <
						      JsonDataValue >
						      (listener_config_->id));
					root->emplace(JSON_KEYS::HTTPS,
						      std::make_unique <
						      JsonDataValue >
						      (listener_config_->ctx
						       != nullptr));
					root->emplace(JSON_KEYS::STATUS,
						      std::make_unique <
						      JsonDataValue >
						      (this->disabled ?
						       JSON_KEYS::STATUS_DOWN
						       :
						       JSON_KEYS::STATUS_ACTIVE));
					root->emplace(JSON_KEYS::NAME,
						      std::make_unique <
						      JsonDataValue > (name));

					auto sm = this->weak_from_this();
					auto count =
						this->
						disabled ? sm.use_count() :
						sm.use_count() - 1;
					root->emplace(JSON_KEYS::CONNECTIONS,
						      std::make_unique <
						      JsonDataValue >
						      (established_connection));
					root->emplace("object_ref",
						      std::make_unique <
						      JsonDataValue >
						      (count));
					auto services_array =
						std::make_unique < JsonArray >
						();
				      for (auto service:services)
						services_array->emplace_back
							(service->getServiceJson
							 ());
					root->emplace(JSON_KEYS::SERVICES,
						      std::move
						      (services_array));
					auto data = root->stringify();
					return data;
				}
			}
			break;
		}
	case ctl::CTL_COMMAND::NONE:
		break;
	case ctl::CTL_COMMAND::ADD:
		break;
	case ctl::CTL_COMMAND::DELETE:
		break;
	case ctl::CTL_COMMAND::ENABLE:
		break;
	case ctl::CTL_COMMAND::DISABLE:
		break;
	case ctl::CTL_COMMAND::UPDATE:
		switch (task.subject) {
#if WAF_ENABLED
		case ctl::CTL_SUBJECT::RELOAD_WAF:{
				//          auto json_data = JsonParser::parse(task.data);
				auto new_rules = Waf::reloadRules();	// TODO:: update reload
				if (new_rules == nullptr) {
					return JSON_OP_RESULT::ERROR;
				}
				this->listener_config_->rules = new_rules;
				return JSON_OP_RESULT::OK;
			}
#endif
		case ctl::CTL_SUBJECT::CONFIG:
			// TODO:: update service config (timeouts, headers, routing policy)
			break;
		case ctl::CTL_SUBJECT::STATUS:{
				std::unique_ptr < JsonObject >
					status(JsonParser::parse(task.data));
				if (status == nullptr)
					return JSON_OP_RESULT::ERROR;
				if (status->at(JSON_KEYS::STATUS)->isValue()) {
					auto value =
						dynamic_cast <
						JsonDataValue *
						>(status->at
						  (JSON_KEYS::STATUS).get())
						->string_value;
					if (value == JSON_KEYS::STATUS_ACTIVE
					    || value ==
					    JSON_KEYS::STATUS_UP) {
						this->disabled = false;
					}
					else if (value ==
						 JSON_KEYS::STATUS_DOWN) {
						this->disabled = true;
					}
					else if (value ==
						 JSON_KEYS::STATUS_DISABLED) {
						this->disabled = true;
					}
					zcutils_log_print(LOG_NOTICE,
							  "set Service %d %s",
							  id, value.c_str());
					return JSON_OP_RESULT::OK;
				}
				break;
			}
		default:
			break;
		}
		break;
	case ctl::CTL_COMMAND::SUSCRIBE:
		break;
	case ctl::CTL_COMMAND::UNSUSCRIBE:
		break;
	case ctl::CTL_COMMAND::EXIT:
		break;
	}
	return JSON_OP_RESULT::ERROR;
}

bool ServiceManager::isHandler(ctl::CtlTask & task)
{
	return !disabled &&
		(((task.target == ctl::CTL_HANDLER_TYPE::SERVICE_MANAGER) &&
		  (task.listener_id == listener_config_->id ||
		   task.listener_id == -1)) ||
		 task.target == ctl::CTL_HANDLER_TYPE::ALL);
}
