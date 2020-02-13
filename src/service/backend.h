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
#include "../ctl/control_manager.h"
#include "../ctl/ctl.h"
#include "../ctl/observer.h"
#include "../debug/logger.h"
#include "../json/json_data_value.h"
#include "../json/json_data_value_types.h"
#include "../json/json_parser.h"
#include "../ssl/ssl_connection_manager.h"
#include "../stats/backend_stats.h"
#include "../util/utils.h"
#include <atomic>
#include <netdb.h>

/** The enum Backend::BACKEND_STATUS defines the status of the Backend. */
enum class BACKEND_STATUS {
  /** There is no Backend, used for first assigned backends. */
  NO_BACKEND = -1,
  /** The Backend is up. */
  BACKEND_UP = 0,
  /** The Backend is down. */
  BACKEND_DOWN,
  /** The Backend is disabled. */
  BACKEND_DISABLED
};

/** The enum Backend::BACKEND_TYPE defines the type of the Backend. */
enum class BACKEND_TYPE {
  /** Remote backend. */
  REMOTE,
  /** Emergency backend. */
  EMERGENCY_SERVER,
  /** Redirect backend. */
  REDIRECT,
  /** Backend used for the cache system. */
  CACHE_SYSTEM,
};
using namespace Statistics;
using namespace json;
using namespace ssl;

/**
 * @class Backend backend.h "src/service/backend.h"
 *
 * @brief The Backend class contains the configuration parameters set in the
 * backend section of the configuration file.
 */
class Backend : public CtlObserver<ctl::CtlTask, std::string>, public BackendInfo {
 public:
  Backend();
  ~Backend();
  /** Backend status using the Backend::BACKEND_STATUS enum. */
  std::atomic<BACKEND_STATUS> status;
  /** Backend type using the Backend::BACKEND_TYPE enum. */
  BACKEND_TYPE backend_type;
  /** BackendConfig parameters from the backend section. */
  std::shared_ptr<BackendConfig> backend_config;
  /** Backend Address as a addrinfo type. */
  addrinfo *address_info{nullptr};
  /** Backend id. */
  int backend_id;
  /** Backend name. */
  std::string name;
  /** Backend weight, used for the balancing algorithms. */
  int weight;
  /** Backend priority, used for the balancing algorithms. */
  int priority{0};
  /** Backend Address as a std::string type. */
  std::string address;
  /** Backend port. */
  int port;
  /** Backend key if set in the configuration. */
  std::string bekey;
  /** Connection timeout time parameter. */
  int conn_timeout{};
  /** Response timeout time parameter. */
  int response_timeout{};
  /** SSL_CTX if the Backend is HTTPS. */
  std::shared_ptr<SSL_CTX> ctx{nullptr};
  bool cut;
  /**
   * @brief Checks if the Backend still alive.
   */
  void doMaintenance();

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
   * @brief Checks if the Backend should handle the @p task.
   *
   * @param task to check.
   * @return true if should handle the task, false if not.
   */
  bool isHandler(ctl::CtlTask &task) override;

  /**
   * @brief Generates a JsonObject with all the Backend information.
   * @return JsonObject with the Backend information.
   */
  std::unique_ptr<JsonObject> getBackendJson();
  int nf_mark;
  bool isHttps();
};
