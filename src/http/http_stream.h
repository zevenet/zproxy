/*
 *    Zevenet zproxy Load Balancer Software License
 *    This file is part of the Zevenet zproxy Load Balancer software package.
 *
 *    Copyright (C) 2019-today ZEVENET SL, Sevilla (Spain)
 *
 *    This program is free software: you can redistribute it and/or modify
 *    it under the terms of the GNU Affero General Public License as
 *    published by the Free Software Foundation, either version 3 of the
 *    License, or any later version.
 *
 *    This program is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *    GNU Affero General Public License for more details.
 *
 *    You should have received a copy of the GNU Affero General Public License
 *    along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 */

#pragma once

#include "../connection/backend_connection.h"
#include "../connection/client_connection.h"
#include "../event/epoll_manager.h"
#include "../event/timer_fd.h"
#include "../service/backend.h"
#include "../service/service_manager.h"
#include "../ssl/ssl_connection_manager.h"
#include "http_request.h"
#if WAF_ENABLED
#include <modsecurity/modsecurity.h>
#include <modsecurity/rules.h>
#include <modsecurity/transaction.h>
#endif


enum class STREAM_OPTION:uint32_t {
  NO_OPT = 0x0,
  PINNED_CONNECTION = 0x1,
  H2 = 0x1 << 1,
  H2C = 0x1 << 2,
  WS = 0x1 << 3 ,//web socket
};

enum class STREAM_STATUS : uint32_t {
  ERROR = 0x0,
  BCK_CONN_PENDING = 0x1,
  BCK_CONN_ERROR = 0x1 << 1,
  BCK_READ_PENDING = 0x1 << 2,
  BCK_WRITE_PENDING = 0x1 << 3,
  CL_READ_PENDING = 0x1 << 4,
  CL_WRITE_PENDING= 0x1 << 5,
  REQUEST_PENDING = 0x1 << 6,
  RESPONSE_PENDING = 0x1 << 7,
  CLOSE_CONNECTION = 0x1 << 8
};

/**
 * @class HttpStream http_stream.h "src/http/http_stream.h"
 *
 * @brief The HttpStream class contains both client and backend connections. It
 * also controls the requests and responses. Furthermore, it implements the
 * error replies.
 *
 */
class HttpStream : public Counter<HttpStream> {
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
#if WAF_ENABLED
  //    modsecurity::ModSecurityIntervention *intervention{nullptr};
  modsecurity::Transaction *modsec_transaction{nullptr};
  std::shared_ptr<modsecurity::Rules> waf_rules{nullptr};
#endif
  /** Connection between zproxy and the client. */
  ClientConnection client_connection;
  /** Connection between zproxy and the backend. */
  BackendConnection backend_connection;
#if USE_TIMER_FD_TIMEOUT
  /** Timer descriptor used for the stream timeouts. */
  TimerFd timer_fd;
#endif
  /** HttpRequest containing the request sent by the client. */
  HttpRequest request;
  /** HttpResponse containing the response sent by the backend. */
  HttpResponse response;

  uint32_t status{0x0};
  uint32_t options{0x0};
  uint32_t stream_id{0};
  inline bool hasOption(STREAM_OPTION _option) const{
    return (options & helper::to_underlying(_option)) != 0u;
  }

  inline bool hasStatus(STREAM_STATUS _status) const{
    return (status & helper::to_underlying(_status)) != 0u;
  }

  inline void clearOption(STREAM_OPTION _option){
    options &= ~helper::to_underlying(_option);
  }

  inline void clearStatus(STREAM_STATUS _status){
    status &= ~helper::to_underlying(_status);
  }

  std::shared_ptr<ServiceManager> service_manager;

  static void dumpDebugData(HttpStream * stream, const char* debug_str, const char * data);
};
