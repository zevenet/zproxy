//
// Created by abdess on 4/5/18.
//

#ifndef NEW_ZHTTP_WORKER_H
#define NEW_ZHTTP_WORKER_H

#include <thread>
#include <unordered_map>
#include <vector>
#include "../event/epoll_manager.h"
#include "../http/http_stream.h"
#include "../config/BackendConfig.h"

class StreamManager : public EpollManager {
  int worker_id;
  std::thread worker;
  bool is_running;
  std::vector<BackendConfig> backend_set;
  std::unordered_map<int, HttpStream *> streams_set;

  void HandleEvent(int fd, EVENT_TYPE event_type, EVENT_GROUP event_group) override;
  void doWork();

 public:
  StreamManager();
  StreamManager(const StreamManager &) = delete;
  ~StreamManager();
  void addStream(int fd);
  int getWorkerId();
  void start(int thread_id_ = 0);
  void stop();
  void addBackend(std::string address, int port);
  BackendConfig *getBackend();

};

#endif  // NEW_ZHTTP_WORKER_H
