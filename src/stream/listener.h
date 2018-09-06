//
// Created by abdess on 4/5/18.
//

#ifndef NEW_ZHTTP_LISTENER_H
#define NEW_ZHTTP_LISTENER_H

#include <vector>
#include <thread>
#include "../event/epoll_manager.h"
#include "StreamManager.h"

class Listener : public EpollManager {
  std::thread worker_thread;
  bool is_running;
  Connection listener_connection;
  std::map<int, StreamManager *> stream_manager_set;
  ListenerConfig listener_config;

  void doWork();
  StreamManager *
  getManager(int fd);

 public:
  Listener();
  ~Listener();
  bool init(std::string address, int port);
  bool init(ListenerConfig &config);
  void start();
  void stop();
  void HandleEvent(int fd, EVENT_TYPE event_type, EVENT_GROUP event_group) override;
};

#endif //NEW_ZHTTP_LISTENER_H
