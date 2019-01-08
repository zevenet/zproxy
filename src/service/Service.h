//
// Created by abdess on 4/25/18.
//
#pragma once

#include <vector>
#include "../config/pound_struct.h"
#include "../connection/connection.h"
#include "../ctl/ctl.h"
#include "../ctl/observer.h"
#include "../http/HttpRequest.h"
#include "../json/JsonDataValueTypes.h"
#include "backend.h"
#include "httpsessionmanager.h"

using namespace json;

class Service : public sessions::HttpSessionManager,
                public CtlObserver<ctl::CtlTask, std::string> {
  std::vector<Backend *> backend_set;
  std::vector<Backend *> emergency_backend_set;
  // if no backend available, return an emergency backend if possible.
  Backend *getNextBackend();
  std::mutex mtx_lock;

 public:
  std::atomic<bool> disabled;
  int id;
  bool ignore_case;
  std::string name;
  std::string becookie,      /* Backend Cookie Name */
      becdomain,      /* Backend Cookie domain */
      becpath;        /* Backend cookie path */
  int becage;         /* Backend cookie age */

  enum LOAD_POLICY {
    LP_ROUND_ROBIN,
    LP_W_LEAST_CONNECTIONS, //we are using weighted
    LP_RESPONSE_TIME,
    LP_PENDING_CONNECTIONS,
  };

 public:
  ServiceConfig &service_config;
  Backend *getBackend(HttpStream &stream);
  explicit Service(ServiceConfig &service_config_);
  ~Service();
  void addBackend(BackendConfig *backend_config, std::string address, int port,
                  int backend_id, bool emergency = false);
  void addBackend(BackendConfig *backend_config, int backend_id,
                  bool emergency = true);
  void doMaintenance();
  bool doMatch(HttpRequest &request);
  static void setBackendsPriorityBy(BACKENDSTATS_PARAMETER);
  Backend * getEmergencyBackend();

  std::string handleTask(ctl::CtlTask &task) override;
  bool isHandler(ctl::CtlTask &task) override;
  JsonObject *getServiceJson();
};
