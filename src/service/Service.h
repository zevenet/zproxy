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

/** The Service class contains the configuration parameters set in the service
 * section. This class contains the backends set in the configuration file.
 */
class Service : public sessions::HttpSessionManager,
                public CtlObserver<ctl::CtlTask, std::string> {
  std::vector<Backend *> backend_set;
  std::vector<Backend *> emergency_backend_set;
  // if no backend available, return an emergency backend if possible.
  Backend *getNextBackend();
  std::mutex mtx_lock;

 public:
  /** True if the Service is disabled, false if it is enabled. */
  std::atomic<bool> disabled;
  /** Service id. */
  int id;
  bool ignore_case;
  std::string name;
  /** Backend Cookie Name */
  std::string becookie,
      /** Backend Cookie domain */
      becdomain,
      /** Backend cookie path */
      becpath;
  /** Backend cookie age */
  int becage;
  /** True if the connection if pinned, false if not. */
  bool pinned_connection;

  /** The enum Service::LOAD_POLICY defines the different types of load balancing
   * available. All the methods are weighted except the Round Robin one.
   */
  enum LOAD_POLICY {
    /** Selects the next backend following the Round Robin algorithm. */
    LP_ROUND_ROBIN,
    /** Selects the backend with less stablished connections. */
    LP_W_LEAST_CONNECTIONS, //we are using weighted
    /** Selects the backend with less response time. */
    LP_RESPONSE_TIME,
    /** Selects the backend with less pending connections. */
    LP_PENDING_CONNECTIONS,
  };
private:
  void addBackend(BackendConfig *backend_config, std::string address, int port,
                  int backend_id, bool emergency = false);
 public:
  /** ServiceConfig from the Service. */
  ServiceConfig &service_config;
  Backend *getBackend(HttpStream &stream);
  explicit Service(ServiceConfig &service_config_);
  ~Service();

  void addBackend(BackendConfig *backend_config, int backend_id,
                  bool emergency = false);
  void doMaintenance();
  bool doMatch(HttpRequest &request);
  static void setBackendsPriorityBy(BACKENDSTATS_PARAMETER);
  Backend * getEmergencyBackend();

  std::string handleTask(ctl::CtlTask &task) override;
  bool isHandler(ctl::CtlTask &task) override;
  JsonObject *getServiceJson();
};
