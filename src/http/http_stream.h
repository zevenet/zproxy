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

class HttpStream: public Counter<HttpStream> {

  struct upgrade_status {
    http::UPGRADE_PROTOCOLS protocol;
    bool pinned_connection;
  };

public:
  HttpStream();
  ~HttpStream();
  //  ConnectionStadistic_t client_stadistics;
  //  ConnectionStadistic_t backend_stadistics;

  ClientConnection client_connection;
  BackendConnection backend_connection;
  TimerFd timer_fd;
  HttpRequest request;
  HttpResponse response;
  upgrade_status upgrade;

  void replyError(HttpStatus::Code code, const char *code_string,
                  const char *string);
  void replyRedirect(BackendConfig &backend_config);
  void replyRedirect(int code, const char * url);
};

#endif // NEW_ZHTTP_HTTP_STREAM_H
