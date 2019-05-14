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

#if DEBUG_STREAM_EVENTS_COUNT

#include "../stats/counter.h"

namespace debug__ {
#define DEBUG_COUNTER_HIT(x) std::unique_ptr<x> debug_stream_status(new x);

DEFINE_OBJECT_COUNTER(on_client_connect);
DEFINE_OBJECT_COUNTER(on_backend_connect);
DEFINE_OBJECT_COUNTER(on_backend_connect_timeout)
DEFINE_OBJECT_COUNTER(on_backend_disconnect);
DEFINE_OBJECT_COUNTER(on_handshake);
DEFINE_OBJECT_COUNTER(on_request);
DEFINE_OBJECT_COUNTER(on_response);
DEFINE_OBJECT_COUNTER(on_request_timeout);
DEFINE_OBJECT_COUNTER(on_response_timeout);
DEFINE_OBJECT_COUNTER(on_send_request);
DEFINE_OBJECT_COUNTER(on_send_response);
DEFINE_OBJECT_COUNTER(on_client_disconnect);
}
#else
#define DEBUG_COUNTER_HIT(x)
#endif

using namespace events;
using namespace http;

/** The StreamManager class is going to manage the streams and the
 * operations related with them. It is event-driven and in order to
 * accomplish that it inherits from EpollManager.
 */
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
  static bool transferChunked(HttpStream *stream);
  void clearStream(HttpStream *stream);

  /** True if the listener is HTTPS, false if not. */
  bool is_https_listener;
};

#endif // NEW_ZHTTP_WORKER_H
