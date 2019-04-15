//
// Created by abdess on 4/5/18.
//

#ifndef NEW_ZHTTP_WORKER_H
#define NEW_ZHTTP_WORKER_H

#include "../config/pound_struct.h"
#include "../event/TimerFd.h"
#include "../event/epoll_manager.h"
#include "../http/http_stream.h"
#include "../service/ServiceManager.h"
#include "../service/backend.h"
#include "../ssl/SSLConnectionManager.h"
#include <thread>
#include <unordered_map>
#include <vector>

using namespace events;
using namespace http;

class StreamManager : public EpollManager {
#if HELLO_WORLD_SERVER
  std::string e200 =
      "HTTP/1.1 200 OK\r\nServer: zhttp 1.0\r\nExpires: now\r\nPragma: "
      "no-cache\r\nCache-control: no-cache,no-store\r\nContent-Type: "
      "text/html\r\nContent-Length: 11\r\n\r\nHello World\n";
#endif

  int worker_id;
  std::thread worker;
  ServiceManager *service_manager;
  ssl::SSLConnectionManager * ssl_manager;
  Connection listener_connection;
  bool is_running;
  ListenerConfig listener_config_;
  std::unordered_map<int, HttpStream *> streams_set;
  std::unordered_map<int, HttpStream *> timers_set;
  void HandleEvent(int fd, EVENT_TYPE event_type,
                   EVENT_GROUP event_group) override;
  void doWork();

public:
  StreamManager();
  StreamManager(const StreamManager &) = delete;
  ~StreamManager();

  void addStream(int fd);
  int getWorkerId();
  bool init(ListenerConfig &listener_config);
  void start(int thread_id_ = 0);
  void stop();
  void setListenSocket(int fd);
  inline void onResponseEvent(int fd);
  inline void onRequestEvent(int fd);
  inline void onConnectTimeoutEvent(int fd);
  inline void onResponseTimeoutEvent(int fd);
  inline void onRequestTimeoutEvent(int fd);
  inline void onSignalEvent(int fd);
  inline void onServerWriteEvent(HttpStream *stream);
  inline void onClientWriteEvent(HttpStream *stream);

  validation::REQUEST_RESULT validateRequest(HttpRequest &request);
  validation::REQUEST_RESULT validateResponse(HttpStream &stream);

  static void setBackendCookie(Service *service, HttpStream *stream);
  static void applyCompression(Service *service, HttpStream *stream);
  static void setStrictTransportSecurity(Service *service, HttpStream *stream);
  static bool transferChunked(HttpStream *stream);
  void httpsHeaders(HttpStream *stream);
  void clearStream(HttpStream *stream);
  bool is_https_listener;
};

#endif // NEW_ZHTTP_WORKER_H
