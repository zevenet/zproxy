//
// Created by abdess on 4/5/18.
//

#pragma once

#include "../connection/backend_connection.h"
#include "../ssl/SSLConnectionManager.h"

#include "../event/TimerFd.h"
#include "../event/epoll_manager.h"
#include "../service/backend.h"
#include "HttpRequest.h"
#include "HttpStatus.h"
#include "../connection/client_connection.h"

struct UpgradeStatus {
  http::UPGRADE_PROTOCOLS protocol {http::UPGRADE_PROTOCOLS::NONE};
  bool pinned_connection{0};
};

/**
 * @class HttpStream http_stream.h "src/http/http_stream.h"
 *
 * @brief The HttpStream class contains both client and backend connections. It
 * also controls the requests and responses. Furthermore, it implements the
 * error replies.
 *
 */
class HttpStream: public Counter<HttpStream> {

public:
#if CACHE_ENABLED
    time_t current_time;
    std::chrono::steady_clock::time_point prev_time;
#endif
  HttpStream();
  ~HttpStream() final;
  // no copy allowed
  HttpStream(const HttpStream&) = delete;
  HttpStream& operator=(const HttpStream&) = delete;

  /** Connection between zhttp and the client. */
  ClientConnection client_connection;
  /** Connection between zhttp and the backend. */
  BackendConnection backend_connection;
  /** Timer descriptor used for the stream timeouts. */
  TimerFd timer_fd;
  /** HttpRequest containing the request sent by the client. */
  HttpRequest request;
  /** HttpResponse containing the response sent by the backend. */
  HttpResponse response;
  /** This struct indicates the upgrade mechanism status. */
  UpgradeStatus upgrade;  
};


