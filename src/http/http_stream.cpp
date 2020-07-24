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

#include "http_stream.h"
#include "../service/service.h"
#include "../util/common.h"
#include "../util/network.h"

HttpStream::HttpStream()
    : client_connection(),
      backend_connection(),
#if USE_TIMER_FD_TIMEOUT
      timer_fd(),
#endif
      request(),
      response(),
      status(0x0),
      options(0x0) {
    static std::atomic<uint32_t > stream_id_counter;
      this->stream_id = stream_id_counter++;
#ifdef CACHE_ENABLED
    this->current_time = time_helper::gmtTimeNow();
    this->prev_time = std::chrono::steady_clock::now();
#endif
}

HttpStream::~HttpStream() {
#if WAF_ENABLED
  if (modsec_transaction != nullptr) {
    modsecurity::intervention::free(&modsec_transaction->m_it);
  }
  delete this->modsec_transaction;
#endif
}

void HttpStream::dumpDebugData(const char* debug_str , const char * data ) {
  Logger::logmsg(
      LOG_DEBUG,
      "\e[1;32m[%lu][%s][%.*s]\e[0m cl_buff: %5lu cl_off: %lu CL: %lu R: %d "
      "HS: %s CHR: %d CH: %s TP:%s RP: %s"
      " | bck_buff: %5lu\tbck_off: %lu\tCL: %lu\tR: %d "
      "HS: %s CHR: %d CH: %s TP:%s RP: %s\t%s", stream_id,
      debug_str, request.path_length, request.path,
      client_connection.buffer_size, client_connection.buffer_offset,
      request.content_length, request.message_bytes_left,
      request.getHeaderSent() ? "T" : "F", request.chunk_size_left,
      request.chunked_status != http::CHUNKED_STATUS::CHUNKED_DISABLED ? "T"
                                                                       : "F",
      this->hasStatus(STREAM_STATUS::REQUEST_PENDING) ? "T" : "F",
      this->hasStatus(STREAM_STATUS::CL_READ_PENDING) ? "T" : "F",
      backend_connection.buffer_size, backend_connection.buffer_offset,
      response.content_length, response.message_bytes_left,
      response.getHeaderSent() ? "T" : "F", response.chunk_size_left,
      response.chunked_status != http::CHUNKED_STATUS::CHUNKED_DISABLED ? "T"
                                                                        : "F",
      this->hasStatus(STREAM_STATUS::RESPONSE_PENDING) ? "T" : "F",
      this->hasStatus(STREAM_STATUS::BCK_READ_PENDING) ? "T" : "F", data);
}
