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
#include "../config/pound_struct.h"
#include "../service/ServiceManager.h"

using namespace epoll_manager;

class StreamManager : public EpollManager, public ServiceManager {

  //TODO::REMOVE
  std::string e200 =
      "HTTP/1.1 200 OK\r\nServer: zhttp/1.0\r\nExpires: now\r\nPragma: no-cache\r\nCache-control: no-cache,no-store\r\nContent-Type: text/html\r\nContent-Length: 11\r\n\r\nHello World\n";

  int worker_id;
  std::thread worker;
  bool is_running;
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

  inline void onResponseEvent(int fd);
  inline void onRequestEvent(int fd);
  inline void onResponseTimeoutEvent(int fd);
  inline void onRequestTimeoutEvent(int fd);
  inline void onSignalEvent(int fd);

  bool isRequestMethodValid(HttpRequest &request);
};

#endif  // NEW_ZHTTP_WORKER_H
