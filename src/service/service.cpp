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
#include "../util/network.h"
#include <numeric>

Backend *Service::getBackend(HttpStream &stream) {
  if (backend_set.empty()) return getEmergencyBackend();

  if (session_type != sessions::SESS_NONE) {
    auto session = getSession(stream);
    if (session != nullptr) {
      session->update();
      return session->assigned_backend;
    } else {
      // get a new backend
      // need to set a new backend server for the newly created session!!!!
      Backend *new_backend = nullptr;
      if ((new_backend = getNextBackend()) != nullptr) {
        session = addSession(stream, *new_backend);
        if (session == nullptr) {
          Logger::logmsg(LOG_DEBUG, "Error adding new session, session info not found in request");
        }
      }
      return new_backend;
    }
  } else {
    return getNextBackend();
  }
}

void Service::addBackend(BackendConfig *backend_config, std::string address, int port, int backend_id, bool emergency) {
  auto *backend = new Backend();
  backend->backend_config = *backend_config;
  backend->address_info = Network::getAddress(address, port);
  if (backend->address_info != nullptr) {
    backend->address = std::move(address);
    backend->port = port;
    backend->backend_id = backend_id;
    backend->weight = backend_config->priority;
    backend->name = "bck_" + std::to_string(backend_id);
    backend->conn_timeout = backend_config->conn_to;
    backend->response_timeout = backend_config->rw_timeout;
    backend->status = backend_config->disabled ? BACKEND_STATUS::BACKEND_DISABLED : BACKEND_STATUS::BACKEND_UP;
    backend->backend_type = BACKEND_TYPE::REMOTE;
    backend->bekey = backend_config->bekey;
    backend->nf_mark = backend_config->nf_mark;
    backend->ctx = backend_config->ctx;
    if (backend->ctx != nullptr) backend->ssl_manager.init(*backend_config);
    if (emergency)
      emergency_backend_set.push_back(backend);
    else
      backend_set.push_back(backend);
  } else {
    delete backend;
    Logger::LogInfo("Backend Configuration not valid ", LOG_NOTICE);
  }
}

void Service::addBackend(BackendConfig *backend_config, int backend_id, bool emergency) {
  if (backend_config->be_type == 0) {
    this->addBackend(backend_config, backend_config->address, backend_config->port, backend_id);
  } else {
    // Redirect
    auto *config = new Backend();
    config->backend_config = *backend_config;
    config->backend_id = backend_id;
    config->weight = backend_config->priority;
    config->name = "bck_" + std::to_string(backend_id);
    config->conn_timeout = backend_config->conn_to;
    config->status = backend_config->disabled ? BACKEND_STATUS::BACKEND_DISABLED : BACKEND_STATUS::BACKEND_UP;
    config->response_timeout = backend_config->rw_timeout;
    config->backend_type = BACKEND_TYPE::REDIRECT;
    config->nf_mark = backend_config->nf_mark;
    config->ctx = backend_config->ctx;
    if (config->ctx != nullptr) config->ssl_manager.init(*backend_config);
    if (emergency)
      emergency_backend_set.push_back(config);
    else
      backend_set.push_back(config);
  }
}

bool Service::addBackend(JsonObject *json_object) {
  if (json_object == nullptr) {
    return false;
  } else {  // Redirect
    auto *config = new Backend();
    if (json_object->count(JSON_KEYS::ID) > 0 && json_object->at(JSON_KEYS::ID)->isValue()) {
      config->backend_id = dynamic_cast<JsonDataValue *>(json_object->at(JSON_KEYS::ID).get())->number_value;
    } else {
      return false;
    }

    if (json_object->count(JSON_KEYS::WEIGHT) > 0 && json_object->at(JSON_KEYS::WEIGHT)->isValue()) {
      config->weight = dynamic_cast<JsonDataValue *>(json_object->at(JSON_KEYS::WEIGHT).get())->number_value;
    } else {
      return false;
    }

    if (json_object->count(JSON_KEYS::NAME) > 0 && json_object->at(JSON_KEYS::NAME)->isValue()) {
      config->name = dynamic_cast<JsonDataValue *>(json_object->at(JSON_KEYS::NAME).get())->string_value;
    } else {
      config->name = "bck_" + std::to_string(config->backend_id);
    }

    if (json_object->count(JSON_KEYS::ADDRESS) > 0 && json_object->at(JSON_KEYS::ADDRESS)->isValue()) {
      config->address = dynamic_cast<JsonDataValue *>(json_object->at(JSON_KEYS::ADDRESS).get())->string_value;
    } else {
      return false;
    }

    if (json_object->count(JSON_KEYS::PORT) > 0 && json_object->at(JSON_KEYS::PORT)->isValue()) {
      config->port = dynamic_cast<JsonDataValue *>(json_object->at(JSON_KEYS::PORT).get())->number_value;
    } else {
      return false;
    }

    config->status = BACKEND_STATUS::BACKEND_DISABLED;
    config->backend_type = BACKEND_TYPE::REMOTE;
    backend_set.push_back(config);
  }

  return true;
}

Service::Service(ServiceConfig &service_config_) : service_config(service_config_) {
  //  ctl::ControlManager::getInstance()->attach(std::ref(*this));
  // session data initialization
  this->session_type = static_cast<sessions::HttpSessionType>(service_config_.sess_type);
  this->ttl = static_cast<unsigned int>(service_config_.sess_ttl);
  this->sess_id = service_config_.sess_id;
  this->sess_pat = service_config_.sess_pat;
  this->sess_start = service_config_.sess_start;
#ifdef CACHE_ENABLED
  // Initialize cache manager
  if (service_config_.cache_content.re_pcre != nullptr) {
    this->cache_enabled = true;
    http_cache = make_shared<HttpCache>();
    http_cache->cacheInit(&service_config.cache_content, service_config.cache_timeout, service_config.name,
                          service_config.cache_size, service_config.cache_threshold, service_config.f_name,
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
      Logger::LogInfo("Backend " + bck->address + ":" + std::to_string(bck->port) + " disabled.", LOG_NOTICE);
    }
  }
  for (auto bck = service_config_.emergency; bck != nullptr; bck = bck->next) {
    if (!bck->disabled) {
      this->addBackend(bck, backend_id++, true);
      // this->addBackend(bck->address, bck->port, backend_id++);
    } else {
      Logger::LogInfo("Emergency Backend " + bck->address + ":" + std::to_string(bck->port) + " disabled.", LOG_NOTICE);
    }
  }
}

bool Service::doMatch(HttpRequest &request) {
  MATCHER *m;
  int i, found;

  /* check for request */
  auto url = std::string(request.path, request.path_length);
  for (m = service_config.url; m; m = m->next)
    if (regexec(&m->pat, url.data(), 0, nullptr, 0)) return false;

  /* check for required headers */
  for (m = service_config.req_head; m; m = m->next) {
    for (found = i = 0; i < static_cast<int>(request.num_headers) && !found;
         i++)
      if (!regexec(&m->pat, request.headers[i].name, 0, nullptr, 0)) found = 1;
    if (!found) return false;
  }

  /* check for forbidden headers */
  for (m = service_config.deny_head; m; m = m->next) {
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
        auto json_data = JsonParser::parse(task.data);
        if (task.subject == ctl::CTL_SUBJECT::SESSION) {
          if (!deleteSession(*json_data, backend_set)) return JSON_OP_RESULT::ERROR;
          return JSON_OP_RESULT::OK;
        } else if (task.subject == ctl::CTL_SUBJECT::BACKEND) {
          // TODO::Implement
        } else if (task.subject == ctl::CTL_SUBJECT::CONFIG) {
          // TODO::Implements
        }
        return "";
        break;
      }
      case ctl::CTL_COMMAND::ADD: {
        switch (task.subject) {
          case ctl::CTL_SUBJECT::SESSION: {
            auto json_data = JsonParser::parse(task.data);
            if (!addSession(json_data.get(), backend_set)) return JSON_OP_RESULT::ERROR;
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
                           new JsonDataValue(this->disabled ? JSON_KEYS::STATUS_DOWN : JSON_KEYS::STATUS_ACTIVE));
            return status.stringify();
          }
          case ctl::CTL_SUBJECT::BACKEND:
          default:
            auto response = std::unique_ptr<JsonObject>(getServiceJson());
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
            if (status.get() == nullptr) return "";
            if (status->at(JSON_KEYS::STATUS)->isValue()) {
              auto value = dynamic_cast<JsonDataValue *>(status->at(JSON_KEYS::STATUS).get())->string_value;
              if (value == JSON_KEYS::STATUS_ACTIVE || value == JSON_KEYS::STATUS_UP) {
                this->disabled = false;
              } else if (value == JSON_KEYS::STATUS_DOWN) {
                this->disabled = true;
              } else if (value == JSON_KEYS::STATUS_DISABLED) {
                this->disabled = true;
              }
              Logger::logmsg(LOG_NOTICE, "Set Service %d %s", id, value.c_str());
              return JSON_OP_RESULT::OK;
            }
            break;
          }
          default:
            break;
        }
        break;
      default:
        return "{\"result\",\"ok\"}";
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

JsonObject *Service::getServiceJson() {
  auto root = new JsonObject();
  root->emplace(JSON_KEYS::NAME, new JsonDataValue(this->name));
  root->emplace(JSON_KEYS::ID, new JsonDataValue(this->id));
  root->emplace(JSON_KEYS::STATUS,
                new JsonDataValue(this->disabled ? JSON_KEYS::STATUS_DISABLED : JSON_KEYS::STATUS_ACTIVE));
  auto backends_array = new JsonArray();
  for (auto backend : backend_set) {
    auto bck = backend->getBackendJson();
    backends_array->emplace_back(std::move(bck));
  }
  root->emplace(JSON_KEYS::BACKENDS, backends_array);
  root->emplace(JSON_KEYS::SESSIONS, this->getSessionsJson());
  return root;
}

/** Selects the corresponding Backend to which the connection will be routed
 * according to the established balancing algorithm. */
Backend *Service::getNextBackend() {
  // if no backend available, return next emergency backend from
  // emergency_backend_set ...
  std::lock_guard<std::mutex> locker(mtx_lock);
  Backend *bck;
  if (backend_set.empty()) return nullptr;
  switch (service_config.routing_policy) {
    default:
    case LP_ROUND_ROBIN: {
      static unsigned long long seed;
      Backend *bck_res = nullptr;
      for (auto item : backend_set) {
        seed++;
        bck_res = backend_set[seed % backend_set.size()];
        if (bck_res != nullptr) {
          if (bck_res->status != BACKEND_STATUS::BACKEND_UP) {
            bck_res = nullptr;
            continue;
          }
          break;
        }
      }
      return bck_res;
    }

    case LP_W_LEAST_CONNECTIONS: {
      Backend *selected_backend = nullptr;
      std::vector<Backend *>::iterator it;
      for (it = backend_set.begin(); it != backend_set.end(); ++it) {
        if ((*it)->weight <= 0 || (*it)->status != BACKEND_STATUS::BACKEND_UP) continue;
        if (selected_backend == nullptr) {
          selected_backend = *it;
        } else {
          Backend *current_backend = *it;
          if (selected_backend->getEstablishedConn() == 0) return selected_backend;
          if (selected_backend->getEstablishedConn() * current_backend->weight >
              current_backend->getEstablishedConn() * selected_backend->weight)
            selected_backend = current_backend;
        }
      }
      return selected_backend;
    }

    case LP_RESPONSE_TIME: {
      Backend *selected_backend = nullptr;
      for (auto &it : backend_set) {
        if (it->weight <= 0 || it->status != BACKEND_STATUS::BACKEND_UP) continue;
        if (selected_backend == nullptr) {
          selected_backend = it;
        } else {
          Backend *current_backend = it;
          if (selected_backend->getAvgLatency() < 0) return selected_backend;
          if (current_backend->getAvgLatency() * selected_backend->weight >
              selected_backend->getAvgLatency() * selected_backend->weight)
            selected_backend = current_backend;
        }
      }
      return selected_backend;
    }

    case LP_PENDING_CONNECTIONS: {
      Backend *selected_backend = nullptr;
      std::vector<Backend *>::iterator it;
      for (it = backend_set.begin(); it != backend_set.end(); ++it) {
        if ((*it)->weight <= 0 || (*it)->status != BACKEND_STATUS::BACKEND_UP) continue;
        if (selected_backend == nullptr) {
          selected_backend = *it;
        } else {
          Backend *current_backend = *it;
          if (selected_backend->getPendingConn() == 0) return selected_backend;
          if (selected_backend->getPendingConn() * selected_backend->weight >
              current_backend->getPendingConn() * selected_backend->weight)
            selected_backend = current_backend;
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
    if (bck->status == BACKEND_STATUS::BACKEND_DOWN) {
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
  for (auto tmp : emergency_backend_set) {
    static uint64_t emergency_seed;
    emergency_seed++;
    bck = emergency_backend_set[emergency_seed % backend_set.size()];
    if (bck != nullptr) {
      if (bck->status != BACKEND_STATUS::BACKEND_UP) {
        bck = nullptr;
        continue;
      }
      break;
    }
  }
  return bck;
}
Service::~Service() {
  Logger::logmsg(LOG_REMOVE, "Destructor");
  for (auto &bck : backend_set) delete bck;
  //  ctl::ControlManager::getInstance()->deAttach(std::ref(*this));
}
