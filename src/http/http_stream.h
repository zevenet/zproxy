//
// Created by abdess on 4/5/18.
//

#ifndef NEW_ZHTTP_HTTP_STREAM_H
#define NEW_ZHTTP_HTTP_STREAM_H

#include "../connection/backend_connection.h"

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

class HttpStream: public Counter<HttpStream> {

public:
  HttpStream();
  ~HttpStream();
  // no copy allowed
  HttpStream(const HttpStream&) = delete;
  HttpStream& operator=(const HttpStream&) = delete;

  ClientConnection client_connection;
  BackendConnection backend_connection;
  TimerFd timer_fd;
  HttpRequest request;
  HttpResponse response;
  UpgradeStatus upgrade;
  http::CHUNKED_STATUS chunked_status;

  void replyError(HttpStatus::Code code, const char *code_string,
                  const char *string);
  void replyRedirect(BackendConfig &backend_config);
  void replyRedirect(int code, const char * url);
};

#endif // NEW_ZHTTP_HTTP_STREAM_H
