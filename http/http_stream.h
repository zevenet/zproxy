//
// Created by abdess on 4/5/18.
//

#ifndef NEW_ZHTTP_HTTP_STREAM_H
#define NEW_ZHTTP_HTTP_STREAM_H

#include "../connection/connection.h"
#include "HttpRequest.h"
#include "HttpStatus.h"
#include "../connection/backend_connection.h"
#include "../event/epoll_manager.h"
#include "../config/BackendConfig.h"
#include "../event/TimerFd.h"

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
  void replyError(HttpStatus::Code code, const char *code_string, const char *string);
  void replyRedirect(BackendConfig &backend_config);
  inline void printReadStadistics(ConnectionStadistic_t &stadistic,
                                  std::string tag
  );

};

#endif  // NEW_ZHTTP_HTTP_STREAM_H
