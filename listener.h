//
// Created by abdess on 4/5/18.
//

#ifndef NEW_ZHTTP_LISTENER_H
#define NEW_ZHTTP_LISTENER_H

#include <vector>
#include "event/event_manager.h"
#include "StreamManager.h"

class Listener : public EpollManager {
  std::thread worker_thread;
  bool is_running;
  Connection listener_connection;
  std::vector<StreamManager *> stream_manager_set;
  static void doWork(Listener &);

  StreamManager *
  getManager(int fd);

 public:
  Listener();
  ~Listener();
  bool init(std::string address, int port);
  void start();
  void stop();
  void HandleEvent(int fd, EVENT_TYPE event_type) override;
};

#endif //NEW_ZHTTP_LISTENER_H
