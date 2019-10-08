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

#include "../http/http_request.h"
#include "service.h"
#include <map>
#include <ostream>
#include <vector>

/**
 * @class ServiceManager ServiceManager.h "src/service/ServiceManager.h"
 * @brief The ServiceManager class contains all the operations related with the
 * management of the services.
 */
class ServiceManager : public CtlObserver<ctl::CtlTask, std::string> {
  std::vector<Service *> services;

 public:
  /** ListenerConfig from the listener related with all the services managed by
   * the class. */
  ListenerConfig listener_config_;
  /** ServiceManager instance. */
  static std::shared_ptr<ServiceManager> instance;
  static std::shared_ptr<ServiceManager> getInstance(ListenerConfig &listener_config);
  ServiceManager(ListenerConfig &listener_config);
  ~ServiceManager();

  /**
   * @brief Gets the Service that handles the HttpRequest.
   *
   * Check which Service managed by the ServiceManager handles the @p request.
   *
   * @param request used to match the Service.
   * @return a Service or @c nullptr if there is not a Service that can handle
   * the HttpRequest.
   */
  Service *getService(HttpRequest &request);

  /**
   * @brief Returns all the Service objects that manages the ServiceManager.
   * @return a std::vector containing all the Service objects.
   */
  std::vector<Service *> getServices();

  /**
   * @brief Adds a new Service object to the ServiceManager.
   *
   * Creates a new Service from the @p service_config and adds it to the Service
   * vector.
   *
   * @param service_config to create the new Service
   * @param id used to assign the new Service id.
   * @return @c false if there is any error, @c true if not.
   */
  bool addService(ServiceConfig &service_config, int id);

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
   * @brief Checks if the ServiceManager should handle the @p task.
   *
   * @param task to check.
   * @return true if should handle the task, false if not.
   */
  bool isHandler(ctl::CtlTask &task) override;
};
