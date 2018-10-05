//
// Created by abdess on 4/5/18.
//

#pragma once

#include <thread>
#include <vector>
#include "../ctl/ctl.h"
#include "../ctl/observer.h"
#include "../event/epoll_manager.h"
#include "StreamManager.h"

class Listener : public EpollManager,
                 public CtlObserver<ctl::CtlTask, std::string> {
  std::thread worker_thread;
  bool is_running;
  Connection listener_connection;
  std::map<int, StreamManager *> stream_manager_set;
  ListenerConfig listener_config;
  TimerFd timer_maintenance;
  void doWork();
  StreamManager *getManager(int fd);

 public:
  Listener();
  ~Listener();
  bool init(std::string address, int port);
  bool init(ListenerConfig &config);
  void start();
  void stop();
  void HandleEvent(int fd, EVENT_TYPE event_type,
                   EVENT_GROUP event_group) override;
  std::string handleTask(ctl::CtlTask &task) override;
  bool isHandler(ctl::CtlTask &task) override;
};
