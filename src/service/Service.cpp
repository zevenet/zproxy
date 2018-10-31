

//
// Created by abdess on 4/25/18.
//

#include <vector>
#include "Service.h"
#include "../debug/debug.h"
#include "../json/JsonDataValueTypes.h"
#include "../json/jsonparser.h"
#include "../util/Network.h"
#include "../util/common.h"
#include <numeric>

Backend *Service::getBackend(HttpStream &stream) {
  if (backend_set.empty())
    return getNextBackend(true);  // TODO:: return emergency backend ???

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
          Debug::logmsg(LOG_DEBUG,
                        "This should't happens, check backends list !!!");
          return nullptr;
        }
        return session->assigned_backend;
      } else {
        Debug::logmsg(LOG_DEBUG,
                      "This should't happens, check backends list !!!");
        return nullptr;
      }
    }
  } else {
    return getNextBackend();
  }
}

void Service::addBackend(BackendConfig *backend_config, std::string address,
                         int port, int backend_id, bool emergency) {
  auto *backend = new Backend();
  backend->address_info = Network::getAddress(address, port);
  if (backend->address_info != nullptr) {
    backend->address = std::move(address);
    backend->port = port;
    backend->backend_id = backend_id;
    backend->weight = backend_config->priority;
    backend->name = "bck_" + std::to_string(backend_id);
    backend->conn_timeout = backend_config->conn_to;
    backend->response_timeout = backend_config->rw_timeout;
    backend->status = backend_config->disabled ? BACKEND_DISABLED : BACKEND_UP;
    backend->backend_type = BACKEND_TYPE::REMOTE;
    if (emergency)
      emergency_backend_set.push_back(backend);
    else
      backend_set.push_back(backend);
  } else {
    delete backend;
    Debug::Log("Backend Configuration not valid ", LOG_NOTICE);
  }
}

void Service::addBackend(BackendConfig *backend_config, int backend_id,
                         bool emergency) {
  if (backend_config->be_type == 0) {
    this->addBackend(backend_config, backend_config->address,
                     backend_config->port, backend_id);
  } else {
    // Redirect
    auto *config = new Backend();
    config->backend_config = *backend_config;
    config->backend_id = backend_id;
    config->weight = backend_config->priority;
    config->name = "bck_" + backend_id;
    config->conn_timeout = backend_config->conn_to;
    config->status = backend_config->disabled ? BACKEND_DISABLED : BACKEND_UP;
    config->response_timeout = backend_config->rw_timeout;
    config->backend_type = BACKEND_TYPE::REDIRECT;
    if (emergency)
      emergency_backend_set.push_back(config);
    else
      backend_set.push_back(config);
  }
}

Service::Service(ServiceConfig &service_config_)
    : service_config(service_config_) {
  //  ctl::ControlManager::getInstance()->attach(std::ref(*this));
  // session data initialization
  this->session_type =
      static_cast<sessions::HttpSessionType>(service_config_.sess_type);
  this->ttl = static_cast<unsigned int>(service_config_.sess_ttl);
  this->sess_pat = service_config_.sess_pat;
  this->sess_start = service_config_.sess_start;

  // backend initialization
  int backend_id = 1;
  for (auto bck = service_config_.backends; bck != nullptr; bck = bck->next) {
    if (!bck->disabled) {
      this->addBackend(bck, backend_id++);
      // this->addBackend(bck->address, bck->port, backend_id++);
    } else {
      Debug::Log("Backend " + bck->address + ":" + std::to_string(bck->port) +
                     " disabled.",
                 LOG_NOTICE);
    }
  }
  for (auto bck = service_config_.emergency; bck != nullptr; bck = bck->next) {
    if (!bck->disabled) {
      this->addBackend(bck, backend_id++, true);
      // this->addBackend(bck->address, bck->port, backend_id++);
    } else {
      Debug::Log("Emergency Backend " + bck->address + ":" +
                     std::to_string(bck->port) + " disabled.",
                 LOG_NOTICE);
    }
  }
}

bool Service::doMatch(HttpRequest &request) {
  // TODO::  Benchmark
  // TODO:: Implement parallel predicates ?? benchmark
  // TODO:: Replace PCRE with RE2 --
  MATCHER *m;
  int i, found;

  /* check for request */
  for (m = service_config.url; m; m = m->next)
    if (regexec(&m->pat, request.getRequestLine().c_str(), 0, NULL, 0))
      return false;

  /* check for required headers */
  for (m = service_config.req_head; m; m = m->next) {
    for (found = i = 0; i < (request.num_headers - 1) && !found; i++)
      if (!regexec(&m->pat, request.headers[i].name, 0, NULL, 0)) found = 1;
    if (!found) return false;
  }

  /* check for forbidden headers */
  for (m = service_config.deny_head; m; m = m->next) {
    for (found = i = 0; i < (request.num_headers - 1) && !found; i++)
      if (!regexec(&m->pat, request.headers[i].name, 0, NULL, 0)) return false;
  }
  return true;
}


void Service::setBackendsPriorityBy(BACKENDSTATS_PARAMETER)
{
  //TODO: DYNSCALE DEPENDING ON BACKENDSTAT PARAMETER
}

// TODO:: Add boolean resultado (std::pair<bool[Error?], std::string[Error text
// | json response] >

std::string Service::handleTask(ctl::CtlTask &task) {
  if (!isHandler(task)) return JSON_OP_RESULT::ERROR;
//  Debug::logmsg(LOG_REMOVE, "Service %d handling task", id);
  if (task.backend_id > -1) {
    for (auto backend : backend_set) {
      if (backend->isHandler(task)) return backend->handleTask(task);
    }
    return JSON_OP_RESULT::ERROR;
  }
  switch (task.command) {
    case ctl::CTL_COMMAND::DELETE: {
      // TODO:: delete session (by id, backend_id, source_ip), delete backend,
      // delete config ??
      JsonObject *json_data = JsonParser::parse(task.data);
      if (task.subject == ctl::CTL_SUBJECT::SESSION) {
        if (json_data != nullptr) {
          return "";
        }
      } else if (task.subject == ctl::CTL_SUBJECT::BACKEND) {
      } else if (task.subject == ctl::CTL_SUBJECT::CONFIG) {
      } else
        return "";
      break;
    }
    case ctl::CTL_COMMAND::ADD: {
      // TODO::Add new Session!!
      switch (task.subject) {
        case ctl::CTL_SUBJECT::SESSION:
          break;
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
          status.emplace(
              JSON_KEYS::STATUS,
              new JsonDataValue(this->disabled ? JSON_KEYS::STATUS_DOWN
                                               : JSON_KEYS::STATUS_ACTIVE));
          return status.stringify();
        }
        case ctl::CTL_SUBJECT::BACKEND:
        default:
          auto response = std::unique_ptr<JsonObject>(
              getServiceJson());  // TODO:: importante usar un unique_ptr!!!!!!
          return response != nullptr ? response->stringify() : "";
      }
    case ctl::CTL_COMMAND::UPDATE:
      switch (task.subject) {
        case ctl::CTL_SUBJECT::CONFIG:
          // TODO:: update service config (timeouts, headers, routing policy)
          break;
        case ctl::CTL_SUBJECT::SESSION: {
          // TODO:: update / create new session
          return getSessionsJson()->stringify();
        }
        case ctl::CTL_SUBJECT::STATUS: {
          std::unique_ptr<JsonObject> status(JsonParser::parse(task.data));
          if (status.get() == nullptr) return "";
          if (status->at(JSON_KEYS::STATUS)->isValue()) {
            auto value =
                static_cast<JsonDataValue *>(status->at(JSON_KEYS::STATUS))
                    ->string_value;
            if (value == JSON_KEYS::STATUS_ACTIVE ||
                value == JSON_KEYS::STATUS_UP) {
              this->disabled = false;
            } else if (value == JSON_KEYS::STATUS_DOWN) {
              this->disabled = true;
            } else if (value == JSON_KEYS::STATUS_DISABLED) {
              this->disabled = true;
            }
            Debug::logmsg(LOG_NOTICE, "Set Backend %d %s", id, value.c_str());
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
                new JsonDataValue(this->disabled ? JSON_KEYS::STATUS_DISABLED
                                                 : JSON_KEYS::STATUS_ACTIVE));
  auto backends_array = new JsonArray();
  for (auto backend : backend_set) {
    auto bck = backend->getBackendJson();
    backends_array->push_back(bck);
  }
  root->emplace(JSON_KEYS::BACKENDS, backends_array);
  root->emplace(JSON_KEYS::SESSIONS, this->getSessionsJson());
  return root;
}

Backend *Service::  getNextBackend(bool only_emergency) {
  // if no backend available, return next emergency backend from
  // emergency_backend_set ...
  std::lock_guard<std::mutex> locker(mtx_lock);
  Backend *bck;
  if (backend_set.size() == 0) return nullptr;
    switch(service_config.routing_policy) {
      case LP_ROUND_ROBIN: {
          static unsigned long long seed;
          seed++;
          return backend_set[seed % backend_set.size()];
      };

      case LP_LEAST_CONNECTIONS: {
        Backend* selected_backend = nullptr;
//        int total_connections = std::accumulate(std::next(backend_set.begin()), backend_set.end(),
//                                         backend_set[0]->getEstablishedConn(), // start with first element
//                                         [](Backend* a, Backend* b) {
//                                             return a->getEstablishedConn() + b->getEstablishedConn();
//                                         });
        std::vector<Backend *>::iterator it;
        for (it = backend_set.begin(); it != backend_set.end(); ++it)
        {
          if((*it)->weight <= 0 || (*it)->status != BACKEND_STATUS::BACKEND_UP) continue;
          if (selected_backend == nullptr) {
            selected_backend = *it;
          } else {
            Backend* current_backend = *it;
            if (selected_backend->getEstablishedConn() == 0)
              return selected_backend;
            if (selected_backend->getEstablishedConn()*current_backend->weight >
                current_backend->getEstablishedConn()*selected_backend->weight)
              selected_backend = current_backend;
          }
        }
        return selected_backend;
      };

      case LP_RESPONSE_TIME: {
        Backend* selected_backend = nullptr;
        for (auto it = backend_set.begin(); it != backend_set.end(); ++it)
          {
            if (selected_backend == nullptr) {
              selected_backend = *it;
            } else {
              Backend* current_backend = *it;
              if (selected_backend->getAvgLatency() < 0)
                return selected_backend;
              if (current_backend->getAvgLatency()/selected_backend->weight <
                  selected_backend->getAvgLatency()/selected_backend->weight)
                selected_backend = current_backend;
            }
          }
        return selected_backend;
      };

      case LP_PENDING_CONNECTIONS: {
          Backend* selected_backend = nullptr;
          std::vector<Backend*>::iterator it;
          for (it = backend_set.begin(); it != backend_set.end(); ++it)
          {
            if (selected_backend == nullptr) {
              selected_backend = *it;
            } else {
              Backend* current_backend = *it;
              if (selected_backend->getPendingConn() == 0)
                return selected_backend;
              if (selected_backend->getPendingConn() < current_backend->getPendingConn())
                selected_backend = current_backend;
            }
          }
          return selected_backend;
      };


    }
  if (UNLIKELY(!only_emergency)) {
    do {
      bck = nullptr;
      static uint64_t seed;
      seed++;
      bck = backend_set[seed % backend_set.size()];
    } while (bck != nullptr && bck->status != BACKEND_STATUS::BACKEND_UP);
    if (bck != nullptr) return bck;
  }
  do {
    bck = nullptr;
    static uint64_t emergency_seed;
    emergency_seed++;
    bck = emergency_backend_set[emergency_seed % backend_set.size()];
  } while (bck != nullptr && bck->status != BACKEND_STATUS::BACKEND_UP);
}

Service::~Service() {
  //  ctl::ControlManager::getInstance()->deAttach(std::ref(*this));
}
