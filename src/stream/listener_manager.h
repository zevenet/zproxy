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

#include "../ctl/ctl.h"
#include "../ctl/observer.h"
#include "../event/epoll_manager.h"
#include "../event/signal_fd.h"
#include "stream_manager.h"
#include <thread>
#include <vector>
#if WAF_ENABLED
#include <modsecurity/modsecurity.h>
#include <modsecurity/rules.h>
#include "../handlers/waf.h"
#endif

/**
 * @class Listener listener.h "src/stream/listener.h"
 * @brief Manage the listener connection and the operations related with it.
 *
 * The listener class manages all the listener operations and contains the
 * ListenerConfig set in the configuration file. The have also a StreamManager
 * attached to it.
 *
 */
class ListenerManager : public EpollManager, public CtlObserver<ctl::CtlTask, std::string> {
  std::thread worker_thread;
  std::atomic<bool> is_running;
  std::map<int, StreamManager *> stream_manager_set;
  std::vector<std::shared_ptr<ListenerConfig>> listener_config_set;
  TimerFd timer_maintenance;
  TimerFd ssl_maintenance_timer;
#if MALLOC_TRIM_TIMER
  TimerFd timer_internal_maintenance;
#endif
  SignalFd signal_fd;
  void doWork();
  StreamManager *getManager(int fd);

 public:
  ListenerManager();
  ~ListenerManager() final;

  /**
   * @brief Sets the listener connection address and port specified in the
   * ListenerConfig.
   *
   * The listener connection will listen in the address and port specified in
   * the @p config.
   *
   * @param config is the ListenerConfig to use by the listener.
   * @return @c false if there is any error, if not @c true.
   */
  bool init(std::shared_ptr<ListenerConfig> config);

  /**
   * @brief Starts the Listener event manager.
   */
  void start();

  /**
   * @brief Stops the Listener event manager.
   */
  void stop();

  /**
   * @brief Handles the needed operations for the event received.
   *
   * Depending on the @p event_group and @p event_type, it calls the proper
   * functions on the @p fd.
   *
   * @param fd is the file descriptor from the event comes from.
   * @param event_type is the type of the event.
   * @param event_group is the group of the event.
   */
  void HandleEvent(int fd, EVENT_TYPE event_type, EVENT_GROUP event_group) override;

  /**
   * @brief This function handles the tasks received with the API format.
   *
   * It calls the needed functions depending on the @p task received. The task
   * must be a API formatted request.
   *
   * @param task to handle by the Listener.
   * @return json formatted string with the result of the operation.
   */
  std::string handleTask(ctl::CtlTask &task) override;

  /**
   * @brief Checks if the Listener should handle the @p task.
   *
   * @param task to check.
   * @return true if should handle the task, false if not.
   */
  bool isHandler(ctl::CtlTask &task) override;
};
