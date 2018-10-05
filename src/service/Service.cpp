

//
// Created by abdess on 4/25/18.
//

#include "Service.h"
#include "../debug/debug.h"
#include "../util/Network.h"
#include "../util/common.h"

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
  auto *config = new Backend();
  config->address_info = Network::getAddress(address, port);
  if (config->address_info != nullptr) {
    config->address = std::move(address);
    config->port = port;
    config->backen_id = backend_id;
    config->conn_timeout = backend_config->conn_to;
    config->response_timeout = backend_config->rw_timeout;
    config->backend_type = BACKEND_TYPE::REMOTE;
    if (emergency)
      emergency_backend_set.push_back(config);
    else
      backend_set.push_back(config);
  } else {
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
    config->backen_id = backend_id;
    config->conn_timeout = backend_config->conn_to;
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
  ctl::ControlManager::getInstance()->attach(std::ref(*this));
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

std::string Service::handleTask(ctl::CtlTask &task) {
  Debug::logmsg(LOG_DEBUG, "Service handling task");
  switch (task.command) {}

  return "{id:0;type:service}";
}

bool Service::isHandler(ctl::CtlTask &task) {
  return task.target == ctl::CTL_HANDLER_TYPE::CTL_SERVICE;
}

Backend *Service::getNextBackend(bool only_emergency) {
  // if no backend available, return next emergency backend from
  // emergency_backend_set ...
  std::lock_guard<std::mutex> locker(mtx_lock);
  Backend *bck;
  if (UNLIKELY(!only_emergency)) {
    do {
      bck = nullptr;
      static uint64_t seed;
      seed++;
      bck = backend_set[seed % backend_set.size()];
    } while (bck != nullptr && bck->disabled);
    if (bck != nullptr) return bck;
  }
  do {
    bck = nullptr;
    static uint64_t emergency_seed;
    emergency_seed++;
    bck = emergency_backend_set[emergency_seed % backend_set.size()];
  } while (bck != nullptr && bck->disabled);
}
Service::~Service() {
  ctl::ControlManager::getInstance()->deAttach(std::ref(*this));
}
