//
// Created by abdess on 4/5/18.
//

#ifndef NEW_ZHTTP_WORKER_H
#define NEW_ZHTTP_WORKER_H

#include <deque>
#include <thread>
#include <unordered_map>
#include "../event/event_manager.h"
#include "../http/http_stream.h"

class StreamManager : public EpollManager {
  int thread_id;
  std::thread worker;
  bool is_running;

  std::unordered_map<int, HttpStream *> streams_set;
  void HandleEvent(int fd, EVENT_TYPE event_type) override;
  void doWork();

 public:
  StreamManager();
  StreamManager(const StreamManager &) = delete;
  ~StreamManager();
  void addStream(int fd);

  int getId();
  void start(int thread_id_ = 0);
  void stop();
};

#endif  // NEW_ZHTTP_WORKER_H
