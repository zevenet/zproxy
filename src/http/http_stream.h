//
// Created by abdess on 4/5/18.
//

#ifndef NEW_ZHTTP_HTTP_STREAM_H
#define NEW_ZHTTP_HTTP_STREAM_H

#include "../connection/backend_connection.h"
#include "../connection/connection.h"
#include "../event/TimerFd.h"
#include "../event/epoll_manager.h"
#include "../service/backend.h"
#include "HttpRequest.h"
#include "HttpStatus.h"

class HttpStream {

public:
  HttpStream();
  ~HttpStream();

  Connection *getConnection(int fd);

  //  ConnectionStadistic_t client_stadistics;
  //  ConnectionStadistic_t backend_stadistics;

  Connection client_connection;
  BackendConnection backend_connection;
  TimerFd timer_fd;
  HttpRequest request;
  HttpResponse response;
  void replyError(HttpStatus::Code code, const char *code_string,
                  const char *string);
  void replyRedirect(BackendConfig &backend_config);
};

#endif // NEW_ZHTTP_HTTP_STREAM_H
