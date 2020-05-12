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

#include "service.h"
#include <numeric>
#include "../util/network.h"

Backend *Service::getBackend(Connection &source, HttpRequest &request) {
  if (backend_set.empty()) return getEmergencyBackend();

  if (session_type != sessions::SESS_NONE) {
    auto session = getSession(source, request);
    if (session != nullptr) {
      if (session->assigned_backend->getStatus() != BACKEND_STATUS::BACKEND_UP) {
        // invalidate all sessions backend is down
        deleteBackendSessions(session->assigned_backend->backend_id);
        return getBackend(source, request);
      }
      session->update();
      return session->assigned_backend;
    } else {
      // get a new backend
      // need to set a new backend server for the newly created session!!!!
      Backend *new_backend = nullptr;
      if ((new_backend = getNextBackend()) != nullptr) {
        session = addSession(source, request, *new_backend);
        if (session == nullptr) {
          Logger::logmsg(
              LOG_DEBUG,
              "Error adding new session, session info not found in request");
        }
      }
      return new_backend;
    }
  } else {
    return getNextBackend();
  }
}

void Service::addBackend(std::shared_ptr<BackendConfig> backend_config,
                         int backend_id, bool emergency) {
  auto backend = std::make_unique<Backend>();
  backend->backend_config = backend_config;
  backend->backend_id = backend_id;
  backend->weight = backend_config->weight;
  backend->priority = backend_config->priority;
  backend->name = "bck_" + std::to_string(backend_id);
  backend->setStatus( backend_config->disabled ? BACKEND_STATUS::BACKEND_DISABLED
                                             : BACKEND_STATUS::BACKEND_UP);
  if (backend_config->be_type == 0) {
    backend->address_info =
        Network::getAddress(backend_config->address, backend_config->port)
            .release();
    if (backend->address_info != nullptr) {
      backend->address = std::move(backend_config->address);
      backend->port = backend_config->port;
      backend->backend_type = BACKEND_TYPE::REMOTE;
      backend->nf_mark = backend_config->nf_mark;
      backend->ctx = backend_config->ctx;
      backend->conn_timeout = backend_config->conn_to;
      backend->response_timeout = backend_config->rw_timeout;
      if (!becookie.empty()) {
        backend->bekey = becookie;
        backend->bekey += "=";
        backend->bekey += backend_config->bekey;

        if (!becdomain.empty()) backend->bekey += "; Domain=" + becdomain;
        if (!becpath.empty()) backend->bekey += "; Path=" + becpath;

        if (becage != 0) {
          backend->bekey += "; Max-Age=";
          if (becage > 0) {
            backend->bekey += std::to_string(becage * 1000);
          } else {
            backend->bekey += std::to_string(ttl * 1000);
          }
        }
      }

    } else {
      Logger::LogInfo("Backend Configuration not valid ", LOG_NOTICE);
      return;
    }
  } else {
    // Redirect
    backend->backend_type = BACKEND_TYPE::REDIRECT;
  }
  if (emergency)
    emergency_backend_set.push_back(backend.release());
  else
    backend_set.push_back(backend.release());
  // recalculate backend maximum priorit
  if (backend_config->priority >= max_backend_priority)
    max_backend_priority = backend_config->priority;
}

bool Service::addBackend(JsonObject *json_object) {
  if (json_object == nullptr) {
    return false;
  } else {  // Redirect
    auto config = std::make_unique<Backend>();
    if (json_object->count(JSON_KEYS::ID) > 0 &&
        json_object->at(JSON_KEYS::ID)->isValue()) {
      config->backend_id =
          dynamic_cast<JsonDataValue *>(json_object->at(JSON_KEYS::ID).get())
              ->number_value;
    } else {
      return false;
    }

    if (json_object->count(JSON_KEYS::WEIGHT) > 0 &&
        json_object->at(JSON_KEYS::WEIGHT)->isValue()) {
      config->weight = dynamic_cast<JsonDataValue *>(
                           json_object->at(JSON_KEYS::WEIGHT).get())
                           ->number_value;
    } else {
      return false;
    }

    if (json_object->count(JSON_KEYS::NAME) > 0 &&
        json_object->at(JSON_KEYS::NAME)->isValue()) {
      config->name =
          dynamic_cast<JsonDataValue *>(json_object->at(JSON_KEYS::NAME).get())
              ->string_value;
    } else {
      config->name = "bck_" + std::to_string(config->backend_id);
    }

    if (json_object->count(JSON_KEYS::ADDRESS) > 0 &&
        json_object->at(JSON_KEYS::ADDRESS)->isValue()) {
      config->address = dynamic_cast<JsonDataValue *>(
                            json_object->at(JSON_KEYS::ADDRESS).get())
                            ->string_value;
    } else {
      return false;
    }

    if (json_object->count(JSON_KEYS::PORT) > 0 &&
        json_object->at(JSON_KEYS::PORT)->isValue()) {
      config->port =
          dynamic_cast<JsonDataValue *>(json_object->at(JSON_KEYS::PORT).get())
              ->number_value;
    } else {
      return false;
    }
    config->setStatus(BACKEND_STATUS::BACKEND_DISABLED);
    config->backend_type = BACKEND_TYPE::REMOTE;
    backend_set.push_back(config.release());
  }

  return true;
}

Service::Service(ServiceConfig &service_config_)
    : service_config(service_config_) {
  //  ctl::ControlManager::getInstance()->attach(std::ref(*this));
  // session data initialization
  name = std::string(service_config.name);
  disabled = service_config.disabled;
  pinned_connection = service_config.pinned_connection == 1;

  // Information related with the setCookie
  if (service_config.becookie != nullptr)
    becookie = std::string(service_config.becookie);
  if (service_config.becdomain != nullptr)
    becdomain = std::string(service_config.becdomain);
  if (service_config.becpath != nullptr)
    becpath = std::string(service_config.becpath);
  becage = service_config.becage;
  this->session_type =
      static_cast<sessions::HttpSessionType>(service_config_.sess_type);
  this->ttl = static_cast<unsigned int>(service_config_.sess_ttl);
  this->sess_id = service_config_.sess_id + '=';
  this->sess_pat = service_config_.sess_pat;
  this->sess_start = service_config_.sess_start;
  this->routing_policy =
      static_cast<ROUTING_POLICY>(service_config_.routing_policy);
#ifdef CACHE_ENABLED
  // Initialize cache manager
  if (service_config_.cache_content.re_pcre != nullptr) {
    this->cache_enabled = true;
    http_cache = make_shared<HttpCache>();
    http_cache->cacheInit(
        &service_config.cache_content, service_config.cache_timeout,
        service_config.name, service_config.cache_size,
        service_config.cache_threshold, service_config.f_name,
        service_config.cache_ram_path, service_config.cache_disk_path);
    http_cache->cache_max_size = service_config.cache_max_size;
  }
#endif
  // backend initialization
  int backend_id = 0;
  for (auto bck = service_config_.backends; bck != nullptr; bck = bck->next) {
    if (!bck->disabled) {
      this->addBackend(bck, backend_id++);
      // this->addBackend(bck->address, bck->port, backend_id++);
    } else {
      Logger::LogInfo("Backend " + bck->address + ":" +
                          std::to_string(bck->port) + " disabled.",
                      LOG_NOTICE);
    }
  }
  for (auto bck = service_config_.emergency; bck != nullptr; bck = bck->next) {
    if (!bck->disabled) {
      this->addBackend(bck, backend_id++, true);
      // this->addBackend(bck->address, bck->port, backend_id++);
    } else {
      Logger::LogInfo("Emergency Backend " + bck->address + ":" +
                          std::to_string(bck->port) + " disabled.",
                      LOG_NOTICE);
    }
  }
}

bool Service::doMatch(HttpRequest &request) {
  int i, found;

  /* check for request */
  auto url = std::string(request.path, request.path_length);
  for (auto m = service_config.url; m; m = m->next)
    if (regexec(&m->pat, url.data(), 0, nullptr, 0)) return false;

  /* check for required headers */
  for (auto m = service_config.req_head; m; m = m->next) {
    for (found = i = 0; i < static_cast<int>(request.num_headers) && !found;
         i++)
      if (!regexec(&m->pat, request.headers[i].name, 0, nullptr, 0)) found = 1;
    if (!found) return false;
  }

  /* check for forbidden headers */
  for (auto m = service_config.deny_head; m; m = m->next) {
    for (found = i = 0; i < static_cast<int>(request.num_headers); i++)
      if (!regexec(&m->pat, request.headers[i].name, 0, nullptr, 0))
        return false;
  }
  return true;
}

void Service::setBackendsPriorityBy(BACKENDSTATS_PARAMETER) {
  // TODO: DYNSCALE DEPENDING ON BACKENDSTAT PARAMETER
}

std::string Service::handleTask(ctl::CtlTask &task) {
  if (!isHandler(task)) return JSON_OP_RESULT::ERROR;
  //  Logger::logmsg(LOG_REMOVE, "Service %d handling task", id);
  if (task.backend_id > -1) {
    for (auto backend : backend_set) {
      if (backend->isHandler(task)) return backend->handleTask(task);
    }
    return JSON_OP_RESULT::ERROR;
  }
#ifdef CACHE_ENABLED
  if (this->cache_enabled && task.subject == ctl::CTL_SUBJECT::CACHE) {
    return http_cache->handleCacheTask(task);
  } else {
#endif
    switch (task.command) {
      case ctl::CTL_COMMAND::DELETE: {
        if (task.subject == ctl::CTL_SUBJECT::SESSION) {
          if (!task.data.empty()) {
            auto json_data = JsonParser::parse(task.data);
            if (!deleteSession(*json_data)) return JSON_OP_RESULT::ERROR;
          } else {
            flushSessions();
          }
          return JSON_OP_RESULT::OK;
        } else if (task.subject == ctl::CTL_SUBJECT::BACKEND) {
          // TODO::Implement
        } else if (task.subject == ctl::CTL_SUBJECT::CONFIG) {
          // TODO::Implements
        }
        return "";
      }
      case ctl::CTL_COMMAND::ADD: {
        switch (task.subject) {
          case ctl::CTL_SUBJECT::SESSION: {
            auto json_data = JsonParser::parse(task.data);
            if (!addSession(json_data.get(), backend_set))
              return JSON_OP_RESULT::ERROR;
            return JSON_OP_RESULT::OK;
          }
          case ctl::CTL_SUBJECT::S_BACKEND: {
            auto json_data = JsonParser::parse(task.data);
            if (!addBackend(json_data.get())) return JSON_OP_RESULT::ERROR;
            return JSON_OP_RESULT::OK;
          }
          default:
            break;
        }
        break;
      }
      case ctl::CTL_COMMAND::GET:
        switch (task.subject) {
          case ctl::CTL_SUBJECT::SESSION: {
            JsonObject response;
            response.emplace(JSON_KEYS::SESSIONS, getSessionsJson());
            return response.stringify();
          }
          case ctl::CTL_SUBJECT::STATUS: {
            JsonObject status;
            status.emplace(JSON_KEYS::STATUS,
                           std::make_unique<JsonDataValue>(
                               this->disabled ? JSON_KEYS::STATUS_DOWN
                                              : JSON_KEYS::STATUS_ACTIVE));
            return status.stringify();
          }
          case ctl::CTL_SUBJECT::BACKEND:
          default:
            auto response = getServiceJson();
            return response != nullptr ? response->stringify() : "";
        }
      case ctl::CTL_COMMAND::UPDATE:
        switch (task.subject) {
          case ctl::CTL_SUBJECT::CONFIG:
            // TODO:: update service config (timeouts, headers, routing policy)
            break;
          case ctl::CTL_SUBJECT::SESSION: {
            return getSessionsJson()->stringify();
          }
          case ctl::CTL_SUBJECT::STATUS: {
            std::unique_ptr<JsonObject> status(JsonParser::parse(task.data));
            if (status == nullptr) return JSON_OP_RESULT::ERROR;
            if (status->at(JSON_KEYS::STATUS)->isValue()) {
              auto value = dynamic_cast<JsonDataValue *>(
                               status->at(JSON_KEYS::STATUS).get())
                               ->string_value;
              if (value == JSON_KEYS::STATUS_ACTIVE ||
                  value == JSON_KEYS::STATUS_UP) {
                this->disabled = false;
              } else if (value == JSON_KEYS::STATUS_DOWN) {
                this->disabled = true;
              } else if (value == JSON_KEYS::STATUS_DISABLED) {
                this->disabled = true;
              }
              Logger::logmsg(LOG_NOTICE, "Set Service %d %s", id,
                             value.c_str());
              return JSON_OP_RESULT::OK;
            }
            break;
          }
          default:
            break;
        }
        break;
      default:
        return JSON_OP_RESULT::OK;
    }
#ifdef CACHE_ENABLED
  }
#endif
  return "";
}

bool Service::isHandler(ctl::CtlTask &task) {
  return /*task.target == ctl::CTL_HANDLER_TYPE::SERVICE &&*/
      (task.service_id == this->id || task.service_id == -1);
}

std::unique_ptr<JsonObject> Service::getServiceJson() {
  auto root = std::make_unique<JsonObject>();
  root->emplace(JSON_KEYS::NAME, std::make_unique<JsonDataValue>(this->name));
  root->emplace(JSON_KEYS::ID, std::make_unique<JsonDataValue>(this->id));
  root->emplace(JSON_KEYS::PRIORITY,
                std::make_unique<JsonDataValue>(this->backend_priority));
  root->emplace(JSON_KEYS::STATUS,
                std::make_unique<JsonDataValue>(
                    this->disabled ? JSON_KEYS::STATUS_DISABLED
                                   : JSON_KEYS::STATUS_ACTIVE));
  auto backends_array = std::make_unique<JsonArray>();
  for (auto backend : backend_set) {
    auto bck = backend->getBackendJson();
    backends_array->emplace_back(std::move(bck));
  }
  root->emplace(JSON_KEYS::BACKENDS, std::move(backends_array));
  root->emplace(JSON_KEYS::SESSIONS, this->getSessionsJson());
  return std::move(root);
}

/** Selects the corresponding Backend to which the connection will be routed
 * according to the established balancing algorithm. */
Backend *Service::getNextBackend() {
  if (backend_set.empty())
    return nullptr;
  else if (backend_set.size() == 1)
    return backend_set[0]->getStatus() != BACKEND_STATUS::BACKEND_UP
               ? nullptr
               : backend_set[0];
  int enabled_priority = 1;
  for (int priority_index = 1; priority_index <= enabled_priority;
       priority_index++) {
    for (auto &bck : backend_set) {
      if (bck->priority == priority_index &&
          bck->getStatus() != BACKEND_STATUS::BACKEND_UP) {
        enabled_priority++;
      }
    }
  }
  backend_priority = enabled_priority;
  switch (routing_policy) {
    default:
    case ROUTING_POLICY::ROUND_ROBIN: {
      static unsigned long long seed;
      Backend *bck_res = nullptr;
      for ([[maybe_unused]] auto &item : backend_set) {
        seed++;
        bck_res = backend_set[seed % backend_set.size()];
        if (bck_res != nullptr) {
          if (bck_res->getStatus() != BACKEND_STATUS::BACKEND_UP ||
              bck_res->priority > backend_priority) {
            bck_res = nullptr;
            continue;
          }
          break;
        }
      }
      return bck_res;
    }

    case ROUTING_POLICY::W_LEAST_CONNECTIONS: {
      Backend *selected_backend = nullptr;
      for (auto &it : backend_set) {
        if (it->weight <= 0 || (it->getStatus() != BACKEND_STATUS::BACKEND_UP ||
                                it->priority > backend_priority))
          continue;
        if (selected_backend == nullptr) {
          selected_backend = it;
        } else {
          if (selected_backend->getEstablishedConn() == 0)
            return selected_backend;
          if (selected_backend->getEstablishedConn() * it->weight >
              it->getEstablishedConn() * selected_backend->weight)
            selected_backend = it;
        }
      }
      return selected_backend;
    }

    case ROUTING_POLICY::RESPONSE_TIME: {
      Backend *selected_backend = nullptr;
      for (auto &it : backend_set) {
        if (it->weight <= 0 || (it->getStatus() != BACKEND_STATUS::BACKEND_UP ||
                                it->priority > backend_priority))
          continue;
        if (selected_backend == nullptr) {
          selected_backend = it;
        } else {
          if (selected_backend->getAvgLatency() < 0) return selected_backend;
          if (it->getAvgLatency() * selected_backend->weight >
              selected_backend->getAvgLatency() * selected_backend->weight)
            selected_backend = it;
        }
      }
      return selected_backend;
    }

    case ROUTING_POLICY::PENDING_CONNECTIONS: {
      Backend *selected_backend = nullptr;

      for (auto &it : backend_set) {
        if (it->weight <= 0 || (it->getStatus() != BACKEND_STATUS::BACKEND_UP ||
                                it->priority > backend_priority))
          continue;
        if (selected_backend == nullptr) {
          selected_backend = it;
        } else {
          if (selected_backend->getPendingConn() == 0) return selected_backend;
          if (selected_backend->getPendingConn() * selected_backend->weight >
              it->getPendingConn() * selected_backend->weight)
            selected_backend = it;
        }
      }
      return selected_backend;
    }
  }
  return getEmergencyBackend();
}

void Service::doMaintenance() {
  HttpSessionManager::doMaintenance();
  for (Backend *bck : this->backend_set) {
    bck->doMaintenance();
    if (bck->getStatus() == BACKEND_STATUS::BACKEND_DOWN) {
      deleteBackendSessions(bck->backend_id);
    }
  }
#ifdef CACHE_ENABLED
  if (this->cache_enabled) {
    http_cache->doCacheMaintenance();
  }
#endif
}

/** There is not backend available, trying to pick an emergency backend. If
 * there is not an emergency backend available it returns nullptr. */
Backend *Service::getEmergencyBackend() {
  // There is no backend available, looking for an emergency backend.
  if (emergency_backend_set.empty()) return nullptr;
  Backend *bck{nullptr};
  for ([[maybe_unused]] auto &tmp : emergency_backend_set) {
    static uint64_t emergency_seed;
    emergency_seed++;
    bck = emergency_backend_set[emergency_seed % backend_set.size()];
    if (bck != nullptr) {
      if (bck->getStatus() != BACKEND_STATUS::BACKEND_UP) {
        bck = nullptr;
        continue;
      }
      break;
    }
  }
  return bck;
}
Service::~Service() {
  for (auto &bck : backend_set) delete bck;
  //  ctl::ControlManager::getInstance()->deAttach(std::ref(*this));
}
