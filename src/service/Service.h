//
// Created by abdess on 4/25/18.
//
#pragma once

#include <vector>
#include "../config/BackendConfig.h"
#include "../config/pound_struct.h"
#include "../connection/connection.h"
#include "../http/HttpRequest.h"
#include "httpsessionmanager.h"

class Service : public sessions::HttpSessionManager {
  std::vector<Backend *> backend_set;
  std::vector<Backend *> emergency_backend_set;
  //if no backend available, return an emergency backend if possible.
  Backend *getNextBackend(bool only_emergency = false);

 public:
  bool disabled;
  bool ignore_case;

 public:
  ServiceConfig &service_config;
  Backend *getBackend(HttpStream &stream);
  explicit Service(ServiceConfig &service_config_);

  void addBackend(BackendConfig *backend_config,
                  std::string address,
                  int port,
                  int backend_id, bool emergency = false);
  void addBackend(BackendConfig *backend_config, int backend_id, bool emergency = true);
  bool doMatch(HttpRequest &request);
};
