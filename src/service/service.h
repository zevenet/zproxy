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
#pragma once

#include "../config/config_data.h"
#include "../connection/connection.h"
#include "../ctl/ctl.h"
#include "../ctl/observer.h"
#include "../json/json_data_value_types.h"
#include "backend.h"
#include "http_session_manager.h"
#include <vector>
#if CACHE_ENABLED
#include "../cache/http_cache.h"
#endif
using namespace json;

/**
 * @class Service Service.h "src/service/Service.h"
 * @brief The Service class contains the configuration parameters set in the
 * service section.
 *
 * This class contains the backend set in the configuration file and inherits
 * from sessions::HttpSessionManager to be able to manage all the sessions of
 * this Service.
 */
class Service : public sessions::HttpSessionManager,
                public CtlObserver<ctl::CtlTask, std::string> {
  std::vector<Backend *> backend_set;
  std::vector<Backend *> emergency_backend_set;
  // if no backend available, return an emergency backend if possible.
  Backend *getNextBackend();
  std::mutex mtx_lock;
  /** The enum Service::LOAD_POLICY defines the different types of load
   * balancing available. All the methods are weighted except the Round Robin
   * one.
   */
  enum class ROUTING_POLICY {
    /** Selects the next backend following the Round Robin algorithm. */
    ROUND_ROBIN,
    /** Selects the backend with less stablished connections. */
    W_LEAST_CONNECTIONS,  // we are using weighted
    /** Selects the backend with less response time. */
    RESPONSE_TIME,
    /** Selects the backend with less pending connections. */
    PENDING_CONNECTIONS,
  };

 public:
  /** True if the Service is disabled, false if it is enabled. */
#if CACHE_ENABLED
  bool cache_enabled = false;
  std::shared_ptr<HttpCache> http_cache;
#endif
  std::atomic<bool> disabled{false};
  std::atomic<int> backend_priority{0};
  int max_backend_priority = 0;
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
  ROUTING_POLICY routing_policy;

 private:
  bool addBackend(JsonObject *json_object);

 public:
  /** ServiceConfig from the Service. */
  ServiceConfig &service_config;

  /**
   * @brief Checks if we need a new backend or not.
   *
   * If we already have a session it returns the backend associated to the
   * session. If not, it returns a new Backend.
   *
   * @param stream to get the information to decide if we have already a session
   * for it.
   * @return always a Backend. A new one or the associated to the session.
   */
  Backend *getBackend(Connection &source, HttpRequest &request);
  explicit Service(ServiceConfig &service_config_);
  ~Service() final;

  /**
   * @brief Creates a new Backend from a BackendConfig.
   *
   * Creates a new Backend from the @p backend_config and adds it to the
   * service's backend vector.
   *
   * @param backend_config to get the Backend information.
   * @param backend_id to assign the Backend.
   * @param emergency set the Backend as emergency.
   */
  void addBackend(std::shared_ptr<BackendConfig> backend_config, int backend_id,
                  bool emergency = false);

  /**
   * @brief Checks if the backends still alive and deletes the expired sessions.
   */
  void doMaintenance();

  /**
   * @brief Check if the Service should handle the HttpRequest.
   *
   * It checks the request line, required headers and the forbidden headers. If
   * the Service should handle it, returns true if not false.
   *
   * @param request to check.
   * @return @c true or @c false if the Service should handle the @p request or
   * not.
   */
  bool doMatch(HttpRequest &request);
  static void setBackendsPriorityBy(BACKENDSTATS_PARAMETER);
  Backend *getEmergencyBackend();

  /**
   * @brief This function handles the @p tasks received with the API format.
   *
   * It calls the needed functions depending on the @p task received. The task
   * must be a API formatted request.
   *
   * @param task to check.
   * @return json formatted string with the result of the operation.
   */
  std::string handleTask(ctl::CtlTask &task) override;

  /**
   * @brief Checks if the Service should handle the @p task.
   *
   * @param task to check.
   * @return true if should handle the task, false if not.
   */
  bool isHandler(ctl::CtlTask &task) override;

  /**
   * @brief Generates a JsonObject with all the Service information.
   * @return JsonObject with the Service information.
   */
  std::unique_ptr<JsonObject> getServiceJson();
  inline int getBackendSetSize(){return backend_set.size();}
  bool setBackendHostInfo(Backend *backend);
};
