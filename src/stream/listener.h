//
// Created by abdess on 4/5/18.
//

#pragma once

#include "../ctl/ctl.h"
#include "../ctl/observer.h"
#include "../event/SignalFd.h"
#include "../event/epoll_manager.h"
#include "StreamManager.h"
#include <thread>
#include <vector>

/**
 * @class Listener listener.h "src/stream/listener.h"
 * @brief Manage the listener connection and the operations related with it.
 *
 * The listener class manages all the listener operations and contains the
 * ListenerConfig set in the configuration file. The have also a StreamManager
 * attached to it.
 *
 */
class Listener : public EpollManager,
                 public CtlObserver<ctl::CtlTask, std::string> {
  std::thread worker_thread;
  bool is_running;
  Connection listener_connection;
  std::map<int, StreamManager *> stream_manager_set;
  ListenerConfig listener_config;
  ServiceManager *service_manager;
  TimerFd timer_maintenance;
  SignalFd signal_fd;
  void doWork();
  StreamManager *getManager(int fd);

public:
  Listener();
  ~Listener();

  /**
   * @brief Sets the listener connetion address and port.
   *
   * The listener connection will listen in the @p address and @p port
   * specified.
   *
   * @param address to listen in a string format
   * @param port to listen
   * @return @c true if everything is ok, @c false if not.
   */
  bool init(std::string address, int port);

  /**
   * @brief Sets the listener connetion address and port specified in the
   * ListenerConfig.
   *
   * The listener connection will listen in the address and port specified in
   * the @p config.
   *
   * @param config is the ListenerConfig to use by the listener.
   * @return @c false if there is any error, if not @c true.
   */
  bool init(ListenerConfig &config);

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
  void HandleEvent(int fd, EVENT_TYPE event_type,
                   EVENT_GROUP event_group) override;

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
