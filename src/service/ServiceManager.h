//
// Created by abdess on 4/25/18.
//

#pragma once

#include <map>
#include <ostream>
#include <vector>
#include "../http/HttpRequest.h"
#include "Service.h"

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
  static ServiceManager *instance;
  static ServiceManager *getInstance(ListenerConfig &listener_config);
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
