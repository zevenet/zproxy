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
#include "../event/timer_fd.h"
#include "../service/backend.h"
#include "http_request.h"
#if WAF_ENABLED
#include <modsecurity/modsecurity.h>
#include <modsecurity/rules.h>
#include <modsecurity/transaction.h>
#endif

struct UpgradeStatus {
  http::UPGRADE_PROTOCOLS protocol{http::UPGRADE_PROTOCOLS::NONE};
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
  /** Timer descriptor used for the stream timeouts. */
  TimerFd timer_fd;
  /** HttpRequest containing the request sent by the client. */
  HttpRequest request;
  /** HttpResponse containing the response sent by the backend. */
  HttpResponse response;
  /** This struct indicates the upgrade mechanism status. */
  UpgradeStatus upgrade;
};
