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

#include "stream_manager.h"
#include <cstdio>
#include <thread>
#include "../handlers/https_manager.h"
#include "../util/network.h"
#include "stream_data_logger.h"

#ifdef ON_FLY_COMRESSION
#include "../handlers/compression.h"
#endif

void StreamManager::HandleEvent(int fd, EVENT_TYPE event_type,
                                EVENT_GROUP event_group) {
  switch (event_type) {
#if SM_HANDLE_ACCEPT
    case EVENT_TYPE::CONNECT: {
      DEBUG_COUNTER_HIT(debug__::event_connect);

      int new_fd;
      do {
        new_fd = Connection::doAccept(fd);
        if (new_fd > 0) {
          auto spt = service_manager_set[fd].lock();
          if (!spt) {
            deleteFd(fd);  // remove listener from epoll manager.
            ::close(fd);   // we close the listening socket
            return;
          }
          addStream(new_fd, std::move(spt));
        } else {
          DEBUG_COUNTER_HIT(debug__::event_connect_fail);
        }
      } while (new_fd > 0);

      return;
    }
#endif
    case EVENT_TYPE::READ:
    case EVENT_TYPE::READ_ONESHOT: {
      switch (event_group) {
        case EVENT_GROUP::ACCEPTOR:
          break;
        case EVENT_GROUP::SERVER: {
          DEBUG_COUNTER_HIT(debug__::event_backend_read);
          onResponseEvent(fd);
          break;
        }
        case EVENT_GROUP::CLIENT: {
          DEBUG_COUNTER_HIT(debug__::event_client_read);
          onRequestEvent(fd);
          break;
        }
        case EVENT_GROUP::CONNECT_TIMEOUT:
          onConnectTimeoutEvent(fd);
          break;
        case EVENT_GROUP::REQUEST_TIMEOUT:
          onRequestTimeoutEvent(fd);
          break;
        case EVENT_GROUP::RESPONSE_TIMEOUT:
          onResponseTimeoutEvent(fd);
          break;
        case EVENT_GROUP::SIGNAL:
          onSignalEvent(fd);
          break;
        case EVENT_GROUP::MAINTENANCE:
          break;
        default:
          deleteFd(fd);
          close(fd);
          break;
      }
      return;
    }
    case EVENT_TYPE::WRITE: {

      switch (event_group) {
        case EVENT_GROUP::ACCEPTOR:
          break;
        case EVENT_GROUP::SERVER: {
          DEBUG_COUNTER_HIT(debug__::event_backend_write);
          auto stream = bck_streams_set[fd];
          if (stream == nullptr) {
            deleteFd(fd);
            ::close(fd);
            return;
          }
          onServerWriteEvent(stream);
          break;
        }
        case EVENT_GROUP::CLIENT: {
          DEBUG_COUNTER_HIT(debug__::event_client_write);
          auto stream = cl_streams_set[fd];
          if (stream == nullptr) {
            deleteFd(fd);
            ::close(fd);
            return;
          }
          onClientWriteEvent(stream);
          break;
        }
        default: {
          deleteFd(fd);
          ::close(fd);
        }
      }

      return;
    }
    case EVENT_TYPE::DISCONNECT: {
      DEBUG_COUNTER_HIT(debug__::event_disconnect);

      switch (event_group) {
        case EVENT_GROUP::SERVER: {
          DEBUG_COUNTER_HIT(debug__::event_backend_disconnect);
          auto stream = bck_streams_set[fd];
          if (stream == nullptr) {
            char addr[150];
            Logger::logmsg(
                LOG_DEBUG,
                "Remote backend host %s closed connection prematurely ",
                Network::getPeerAddress(fd, addr, 150) != nullptr ? addr : "");
            deleteFd(fd);
            ::close(fd);
            return;
          }
          onServerDisconnect(stream);
          return;
        }
        case EVENT_GROUP::CLIENT: {
          DEBUG_COUNTER_HIT(debug__::event_client_disconnect);
          auto stream = cl_streams_set[fd];
          if (stream == nullptr) {
            char addr[150];
            Logger::logmsg(
                LOG_DEBUG,
                "Remote client host %s closed connection prematurely ",
                Network::getPeerAddress(fd, addr, 150) != nullptr ? addr : "");
            deleteFd(fd);
            ::close(fd);
            return;
          }
          onClientDisconnect(stream);
          return;
        }
        default:
          deleteFd(fd);
          ::close(fd);
          return;
      }
      break;
    }
    default:
      Logger::LogInfo("Unexpected  event type", LOG_DEBUG);
      deleteFd(fd);
      ::close(fd);
  }
}

void StreamManager::stop() {
  is_running = false;
  if (this->worker.joinable()) this->worker.join();
}

void StreamManager::start(int thread_id_) {
  ctl::ControlManager::getInstance()->attach(std::ref(*this));

  is_running = true;
  worker_id = thread_id_;

  for (auto& [sm_id, sm] : ServiceManager::getInstance()) {
    if (sm->disabled) continue;
    if (!this->registerListener(sm)) {
      Logger::logmsg(LOG_ERR, "Error initializing StreamManager for farm %s",
                     sm->listener_config_->name.data());
      return;
    }
  }

  this->worker = std::thread([this] {
    StreamDataLogger::resetLogData();
    doWork();
  });
  if (worker_id >= 0) {
    //    helper::ThreadHelper::setThreadAffinity(worker_id,
    //    worker.native_handle());
    helper::ThreadHelper::setThreadName("WORKER_" + std::to_string(worker_id),
                                        worker.native_handle());
  }
}

StreamManager::StreamManager(){
    // TODO:: do attach for config changes
};

StreamManager::~StreamManager() {
  ctl::ControlManager::getInstance()->deAttach(std::ref(*this));
  stop();
  if (worker.joinable()) worker.join();
  for (auto& key_pair : cl_streams_set) {
    delete key_pair.second;
  }
  for (auto& key_pair : bck_streams_set) {
    delete key_pair.second;
  }
}

void StreamManager::doWork() {
  while (is_running) {
    if (loopOnce(EPOLL_WAIT_TIMEOUT) <= 0) {
      //       something bad happend
    }
    // if(needMainatance)
    //    doMaintenance();
  }
}

void StreamManager::addStream(int fd,
                              std::shared_ptr<ServiceManager> service_manager) {
  DEBUG_COUNTER_HIT(debug__::on_client_connect);
#if SM_HANDLE_ACCEPT
  HttpStream* stream = cl_streams_set[fd];
  if (UNLIKELY(stream != nullptr)) {
    clearStream(stream);
  }
  stream = new HttpStream();
  stream->client_connection.setFileDescriptor(fd);
  stream->service_manager = std::move(service_manager);  // TODO::benchmark!!
  cl_streams_set[fd] = stream;
  auto& listener_config = *stream->service_manager->listener_config_;
  // update log info
  StreamDataLogger logger(stream, listener_config);
  stream->status |= helper::to_underlying(STREAM_STATUS::CL_READ_PENDING);
#if USE_TIMER_FD_TIMEOUT
  stream->timer_fd.set(listener_config.to * 1000);
  addFd(stream->timer_fd.getFileDescriptor(), EVENT_TYPE::TIMEOUT,
        EVENT_GROUP::REQUEST_TIMEOUT);
  timers_set[stream->timer_fd.getFileDescriptor()] = stream;
#else
  this->setTimeOut(fd, TIMEOUT_TYPE::CLIENT_READ_TIMEOUT,listener_config.to);
#endif
  stream->client_connection.enableEvents(this, EVENT_TYPE::READ,
                                         EVENT_GROUP::CLIENT);
  //increment connections
  stream->service_manager->established_connection++;
  // Add requested header to the stream permanent header set, not cleared during
  // the http stream lifetime
  if (!listener_config.add_head.empty()) {
    stream->request.addHeader(listener_config.add_head, true);
  }
  if (!listener_config.response_add_head.empty()) {
    stream->response.addHeader(listener_config.response_add_head, true);
  }
  if (stream->service_manager->is_https_listener) {
    stream->client_connection.ssl_conn_status = ssl::SSL_STATUS::NEED_HANDSHAKE;
  }
#if WAF_ENABLED
  if (listener_config.rules) {
    stream->waf_rules = listener_config.rules;
  }
#endif
// configurar
#else
  if (!this->addFd(fd, EVENT_TYPE::READ, EVENT_GROUP::CLIENT)) {
    Logger::LogInfo("Error adding to epoll manager", LOG_NOTICE);
  }
#endif
}

int StreamManager::getWorkerId() { return worker_id; }

void StreamManager::onRequestEvent(int fd) {
  HttpStream* stream = cl_streams_set[fd];

  if (stream == nullptr) {
    deleteFd(fd);
    ::close(fd);
    return;
  }
#if EXTENDED_DEBUG_LOG
  std::string extra_log;
  ScopeExit logStream{
      [stream, &extra_log] {  HttpStream::dumpDebugData(stream,"OnRequest",extra_log.data()); }};
#endif
  auto& listener_config_ = *stream->service_manager->listener_config_;
  // update log info
  StreamDataLogger logger(stream, listener_config_);
  DEBUG_COUNTER_HIT(debug__::on_request);
// TODO::ENABLE if (stream->hasStatus(STREAM_STATUS::REQUEST_PENDING)) {
//    stream->dumpDebugData("Request pending", "PENDING");
//    stream->status |= helper::to_underlying(STREAM_STATUS::CL_READ_PENDING);
////    stream->client_connection.disableEvents();
////    stream->backend_connection.enableWriteEvent();
//    return;
//  }
#if PRINT_DEBUG_FLOW_BUFFERS
  Logger::logmsg(
      LOG_REMOVE, "IN buffer size: %8lu\tContent-length: %lu\tleft: %lu",
      stream->client_connection.buffer_size, stream->request.content_length,
      stream->request.message_bytes_left);
#endif
  IO::IO_RESULT result = IO::IO_RESULT::ERROR;
  if (stream->service_manager->is_https_listener) {
    result =
        ssl::SSLConnectionManager::handleDataRead(stream->client_connection);
  } else {
    result = stream->client_connection.read();
  }
#if EXTENDED_DEBUG_LOG
  extra_log = IO::getResultString(result);
#endif
  switch (result) {
    case IO::IO_RESULT::SSL_HANDSHAKE_ERROR:
    case IO::IO_RESULT::SSL_NEED_HANDSHAKE: {
      if (!ssl::SSLConnectionManager::handleHandshake(
              *stream->service_manager->ssl_context,
              stream->client_connection)) {
        Logger::logmsg(LOG_DEBUG, "fd: %d:%d Handshake error with %s ",
                       stream->client_connection.getFileDescriptor(),
                       stream->backend_connection.getFileDescriptor(),
                       stream->client_connection.getPeerAddress().c_str());
        clearStream(stream);
        return;
      }
      if (stream->client_connection.ssl_connected) {
        DEBUG_COUNTER_HIT(debug__::on_handshake);
        httpsHeaders(stream, listener_config_.clnt_check);
        stream->backend_connection.server_name =
            stream->client_connection.server_name;
        onRequestEvent(fd);
        return;
      } else if ((ERR_GET_REASON(ERR_peek_error()) == SSL_R_HTTP_REQUEST) &&
                 (ERR_GET_LIB(ERR_peek_error()) == ERR_LIB_SSL)) {
        /* the client speaks plain HTTP on our HTTPS port */
        Logger::logmsg(LOG_NOTICE,
                       "Client %s sent a plain HTTP message to an SSL port",
                       stream->client_connection.getPeerAddress().c_str());
        if (listener_config_.nossl_redir > 0) {
          Logger::logmsg(LOG_NOTICE,
                         "(%lx) errNoSsl from %s redirecting to \"%s\"",
                         pthread_self(),
                         stream->client_connection.getPeerAddress().c_str(),
                         listener_config_.nossl_url.data());
          if (http_manager::replyRedirect(listener_config_.nossl_redir,
                                          listener_config_.nossl_url, *stream))
            clearStream(stream);
          return;
        } else {
          Logger::logmsg(LOG_NOTICE, "(%lx) errNoSsl from %s sending error",
                         pthread_self(),
                         stream->client_connection.getPeerAddress().c_str());
          http_manager::replyError(http::Code::BadRequest,
                                   http::reasonPhrase(http::Code::BadRequest),
                                   listener_config_.errnossl,
                                   stream->client_connection);
          clearStream(stream);
        }
      }
      return;
    }
    case IO::IO_RESULT::SUCCESS:
    case IO::IO_RESULT::DONE_TRY_AGAIN:
    case IO::IO_RESULT::ZERO_DATA:     
      break;
    case IO::IO_RESULT::FULL_BUFFER:
      stream->status |= helper::to_underlying(STREAM_STATUS::CL_READ_PENDING);
      break;
    case IO::IO_RESULT::FD_CLOSED:
      break;
    case IO::IO_RESULT::ERROR:
    case IO::IO_RESULT::CANCELLED:
    default: {
      Logger::LogInfo("Error reading request ", LOG_DEBUG);
      clearStream(stream);
      return;
    }
  }

  DEBUG_COUNTER_HIT(debug__::on_request);
  if (stream->client_connection.buffer_size == 0) {
    stream->client_connection.enableReadEvent();
    return;
  }
  this->stopTimeOut(stream->client_connection.getFileDescriptor());
  stream->clearStatus(STREAM_STATUS::CL_READ_PENDING);
  if (stream->hasOption(STREAM_OPTION::PINNED_CONNECTION) || stream->request.hasPendingData()) {
#ifdef CACHE_ENABLED
    if (stream->request.chunked_status != CHUNKED_STATUS::CHUNKED_DISABLED) {
      auto pending_chunk_bytes = http_manager::handleChunkedData(
          stream->client_connection, stream->request);
      if (pending_chunk_bytes < 0) {  // we don't have enough data to get next
        // chunk size, so we wait for more data
        stream->client_connection.enableReadEvent();
        return;
      }
    }
#endif
#if PRINT_DEBUG_FLOW_BUFFERS
    Logger::logmsg(
        LOG_REMOVE,
        "OUT buffer size: %8lu\tContent-length: %lu\tleft: %lu\tIO: %s",
        stream->client_connection.buffer_size, stream->request.content_length,
        stream->request.message_bytes_left, IO::getResultString(result).data());
#endif
#if ENABLE_QUICK_RESPONSE
    onServerWriteEvent(stream);
#else
    stream->backend_connection.enableWriteEvent();
#endif
    return;
  }
#if PRINT_DEBUG_FLOW_BUFFERS
  Logger::logmsg(
      LOG_DEBUG,
      "IN buffer size: %8lu\tContent-length: %lu\tleft: %lu\tIO: "
      "%s Header sent: %s",
      stream->client_connection.buffer_size, stream->request.content_length,
      stream->request.message_bytes_left, IO::getResultString(result).data(),
      stream->request.getHeaderSent() ? "true" : "false");
#endif
  size_t parsed = 0;
  http_parser::PARSE_RESULT parse_result;
  // do {
  parse_result = stream->request.parseRequest(
      stream->client_connection.buffer + stream->client_connection.buffer_offset, stream->client_connection.buffer_size,
      &parsed);  // parsing http data as response structured

  switch (parse_result) {
    case http_parser::PARSE_RESULT::SUCCESS: {
      auto valid = http_manager::validateRequest(*stream);
      if (UNLIKELY(validation::REQUEST_RESULT::OK != valid)) {
        http_manager::replyError(http::Code::NotImplemented,
                                 validation::request_result_reason.at(valid),
                                 listener_config_.err501,
                                 stream->client_connection);
        this->clearStream(stream);
        return;
      }
      stream->status |= helper::to_underlying(STREAM_STATUS::REQUEST_PENDING);
      break;
    }
    case http_parser::PARSE_RESULT::TOOLONG:
      Logger::LogInfo("Parser TOOLONG", LOG_DEBUG);
      [[fallthrough]];
    case http_parser::PARSE_RESULT::FAILED:
      http_manager::replyError(
          http::Code::BadRequest, http::reasonPhrase(http::Code::BadRequest),
          listener_config_.err501, stream->client_connection);
      this->clearStream(stream);
      return;
    case http_parser::PARSE_RESULT::INCOMPLETE:
      Logger::LogInfo("Parser INCOMPLETE", LOG_DEBUG);
      return;
  }

#if WAF_ENABLED
      if (stream->waf_rules) {  // rule struct is unitializate if no
        // rulesets are configured
        delete stream->modsec_transaction;
        stream->modsec_transaction =
            new modsecurity::Transaction(listener_config_.modsec.get(),
                                         listener_config_.rules.get(), nullptr);
        if (Waf::checkRequestWaf(*stream)) {
          if (stream->modsec_transaction->m_it.url != nullptr) {
            Logger::logmsg(
                LOG_WARNING, "(%lx) WAF redirected a request from %s",
                pthread_self(), stream->client_connection.address_str.c_str());
            // send redirect
            if (http_manager::replyRedirect(
                stream->modsec_transaction->m_it.status,
                stream->modsec_transaction->m_it.url, *stream))
              clearStream(stream);
            return;
          } else {
            // reject the request
            auto code = static_cast<http::Code>(
                stream->modsec_transaction->m_it.status);
            http_manager::replyError(code, reasonPhrase(code),
                                     listener_config_.err403,
                                     stream->client_connection);
            Logger::logmsg(LOG_WARNING, "(%lx) WAF rejected a request from %s",
                           pthread_self(),
                           stream->client_connection.address_str.c_str());
          }
          clearStream(stream);
          return;
        }
      }
#endif
      std::string x_forwarded_for_header;
      if (!stream->request.x_forwarded_for_string.empty()) {
        // set extra header to forward to the backends
        x_forwarded_for_header = stream->request.x_forwarded_for_string;
        x_forwarded_for_header += ", ";
      }
      x_forwarded_for_header += stream->client_connection.getPeerAddress();
      stream->request.addHeader(http::HTTP_HEADER_NAME::X_FORWARDED_FOR,
                                x_forwarded_for_header);
#if USE_TIMER_FD_TIMEOUT
      stream->timer_fd.unset();
      deleteFd(stream->timer_fd.getFileDescriptor());
      timers_set[stream->timer_fd.getFileDescriptor()] = nullptr;
#else
      stopTimeOut(fd);
#endif
      auto service = stream->service_manager->getService(stream->request);
      if (service == nullptr) {
        http_manager::replyError(
            http::Code::ServiceUnavailable,
            validation::request_result_reason.at(
                validation::REQUEST_RESULT::SERVICE_NOT_FOUND),
            listener_config_.err503, stream->client_connection);
        this->clearStream(stream);
        return;
      }
      auto last_service_ptr = stream->request.getService();
      stream->request.setService(service);
      // update log info
      StreamDataLogger::setLogData(stream, listener_config_);

#ifdef CACHE_ENABLED
      // If the cache is enabled and the request is cached and it is also fresh
      auto ret =
          CacheManager::handleRequest(stream, service, listener_config_set);
      // Must return error
      if (ret == -1) {
        // If the directive only-if-cached is in the request and the content
        // is not cached, reply an error 504 as stated in the rfc7234
        http_manager::replyError(http::Code::GatewayTimeout,
                                 http::reasonPhrase(http::Code::GatewayTimeout),
                                 "", stream->client_connection,
                                 this->ssl_manager);
        this->clearStream(stream);
        return;
      }
      // Return, using the cache from response
      if (ret == 0) {
        return;
      }

#endif
  auto bck = service->getBackend(stream->client_connection, stream->request);
  if (bck == nullptr) {
    // No backend available
    http_manager::replyError(http::Code::ServiceUnavailable,
                             validation::request_result_reason.at(
                                 validation::REQUEST_RESULT::BACKEND_NOT_FOUND),
                             listener_config_.err503,
                             stream->client_connection);
    this->clearStream(stream);
    return;
  }
  // update log info
  StreamDataLogger::setLogData(stream, listener_config_);
  IO::IO_OP op_state = IO::IO_OP::OP_ERROR;
  static size_t total_request;
  total_request++;
  stream->response.reset_parser();
  switch (bck->backend_type) {
    case BACKEND_TYPE::REMOTE: {
      bool need_new_backend = true;
      if (last_service_ptr != nullptr) {
        auto last_service = static_cast<Service*>(last_service_ptr);
        if (last_service->id == service->id &&
            stream->backend_connection.isConnected() &&
            stream->backend_connection.getBackend() != nullptr) {
          need_new_backend = false;
        }
      }
      if (need_new_backend) {
        // null
        if (stream->backend_connection.getFileDescriptor() > 0) {
          deleteFd(
              stream->backend_connection.getFileDescriptor());  // Client cannot
          // Client cannot  be connected to more than one backend at
          // time
          bck_streams_set.erase(stream->backend_connection.getFileDescriptor());
          if (stream->backend_connection.isConnected() &&
              stream->backend_connection.getBackend() != nullptr)
            stream->backend_connection.getBackend()->decreaseConnection();
        }
        stream->backend_connection.reset();
        stream->backend_connection.setBackend(bck);
        Time::getTime(stream->backend_connection.time_start);
        op_state = stream->backend_connection.doConnect(*bck->address_info,
                                                        bck->conn_timeout);
        switch (op_state) {
          case IO::IO_OP::OP_ERROR: {
            Logger::logmsg(LOG_NOTICE, "Error connecting to backend %s",
                           bck->address.data());
            onBackendConnectionError(stream);
            return;
        }
          case IO::IO_OP::OP_IN_PROGRESS: {
            stream->status |=
                helper::to_underlying(STREAM_STATUS::BCK_CONN_PENDING);
#if USE_TIMER_FD_TIMEOUT
            stream->timer_fd.set(bck->conn_timeout * 1000);
            this->addFd(stream->timer_fd.getFileDescriptor(),
                        EVENT_TYPE::READ_ONESHOT, EVENT_GROUP::CONNECT_TIMEOUT);
#else
            setTimeOut(stream->backend_connection.getFileDescriptor(),
                       events::TIMEOUT_TYPE::SERVER_WRITE_TIMEOUT,
                       bck->conn_timeout);
#endif
            stream->backend_connection.getBackend()->increaseConnTimeoutAlive();
            break;
          }
          case IO::IO_OP::OP_SUCCESS: {
            DEBUG_COUNTER_HIT(debug__::on_backend_connect);
            stream->backend_connection.getBackend()->increaseConnection();
            break;
          }
        }
        auto bck_stream = bck_streams_set.find(
            stream->backend_connection.getFileDescriptor());
        if (bck_stream != bck_streams_set.end()) {
          Logger::logmsg(LOG_DEBUG, "## BCK Stream exists in set");
          // delete bck_stream->second;
        }
        bck_streams_set[stream->backend_connection.getFileDescriptor()] =
            stream;
        stream->backend_connection.enableEvents(this, EVENT_TYPE::WRITE,
                                                EVENT_GROUP::SERVER);
      }

      Logger::logmsg(LOG_DEBUG, "%s %lu [%s] %.*s [%s (%d) -> %s:%d (%d)]",
                     need_new_backend ? "NEW" : "REUSED", total_request,
                     service->name.c_str(), stream->request.http_message_length,
                     stream->request.http_message,
                     stream->client_connection.getPeerAddress().c_str(),
                     stream->client_connection.getFileDescriptor(),
                     bck->address.c_str(), bck->port,
                     stream->backend_connection.getFileDescriptor());
      if (stream->backend_connection.getBackend()->nf_mark > 0)
        Network::setSOMarkOption(
            stream->backend_connection.getFileDescriptor(),
            stream->backend_connection.getBackend()->nf_mark);
      // Rewrite destination
      if (stream->request.add_destination_header) {
        std::string header_value =
            stream->backend_connection.getBackend()->isHttps() ? "https://"
                                                               : "http://";
        header_value += stream->backend_connection.getPeerAddress();
        header_value += ':';
        header_value += stream->request.path;
        stream->request.addHeader(http::HTTP_HEADER_NAME::DESTINATION,
                                  header_value);
      }
      if (!stream->request.host_header_found) {
        std::string header_value;
        header_value += stream->backend_connection.getBackend()->address;
        header_value += ':';
        header_value +=
            std::to_string(stream->backend_connection.getBackend()->port);
        stream->request.addHeader(http::HTTP_HEADER_NAME::HOST, header_value);
      }
      /* After setting the backend and the service in the first request,
       * pin the connection if the PinnedConnection service config
       * parameter is true. Note: The first request must be HTTP. */
      if (service->service_config.pinned_connection) {
        stream->options |= helper::to_underlying(STREAM_OPTION::PINNED_CONNECTION);
      }
      stream->backend_connection.enableWriteEvent();
      break;
    }

    case BACKEND_TYPE::EMERGENCY_SERVER:

      break;
    case BACKEND_TYPE::REDIRECT: {
      Logger::logmsg(LOG_INFO, " (%s) %.*s < REDIRECT %s",
                     stream->client_connection.getPeerAddress().c_str(),
                     stream->request.http_message_length,
                     stream->request.http_message,
                     bck->backend_config->url.data());
      if (http_manager::replyRedirect(*stream, *bck)) clearStream(stream);
      return;
    }
    case BACKEND_TYPE::CACHE_SYSTEM:
      break;
    case BACKEND_TYPE::TEST_SERVER:
      http_manager::replyTestServer(*stream);
      return;
  }
  stream->client_connection.enableReadEvent();
}

void StreamManager::onResponseEvent(int fd) {
  HttpStream* stream = bck_streams_set[fd];
  if (stream == nullptr) {
    deleteFd(fd);
    ::close(fd);
    return;
  }
#if EXTENDED_DEBUG_LOG
  std::string extra_log;
  ScopeExit logStream{[stream, &extra_log] {
    //check not null
     HttpStream::dumpDebugData(stream,"OnResponse", extra_log.data());
  }};
#endif
  auto& listener_config_ = *stream->service_manager->listener_config_;
  // update log info
  StreamDataLogger logger(stream, listener_config_);
  if (stream->hasStatus(STREAM_STATUS::RESPONSE_PENDING)) {
#if EXTENDED_DEBUG_LOG
    extra_log = "RESPONSE_PENDING";
#endif
    stream->status |= helper::to_underlying(STREAM_STATUS::BCK_READ_PENDING);
    stream->client_connection.enableWriteEvent();
    stream->backend_connection.disableEvents();
    return;
  }
#if PRINT_DEBUG_FLOW_BUFFERS
  auto buffer_size_in = stream->backend_connection.buffer_size;
  if (stream->backend_connection.buffer_size != 0)
    Logger::logmsg(
        LOG_REMOVE,
        "fd:%d IN\tbuffer size: %8lu\tContent-length: %lu\tleft: %lu "
        "header_sent: %s chunk left: %d chunked: %s",
        stream->backend_connection.getFileDescriptor(),
        stream->backend_connection.buffer_size, stream->response.content_length,
        stream->response.message_bytes_left,
        stream->response.getHeaderSent() ? "true" : "false",
        stream->response.chunk_size_left,
        stream->response.chunked_status != CHUNKED_STATUS::CHUNKED_DISABLED
            ? "TRUE"
            : "false");
#endif


  DEBUG_COUNTER_HIT(debug__::on_response);
  IO::IO_RESULT result;

  if (stream->backend_connection.getBackend()->isHttps()) {
    result =
        ssl::SSLConnectionManager::handleDataRead(stream->backend_connection);
  } else {
#if ENABLE_ZERO_COPY
    if (stream->response.message_bytes_left > 0 &&
        !stream->backend_connection.getBackend()->isHttps() &&
        !this->is_https_listener
        /*&& stream->response.transfer_encoding_header*/) {
      result = stream->backend_connection.zeroRead();
      if (result == IO::IO_RESULT::ERROR) {
        Logger::LogInfo("Error reading response ", LOG_DEBUG);
        clearStream(stream);
        return;
      }
#if ENABLE_QUICK_RESPONSE
      result = stream->backend_connection.zeroWrite(
          stream->client_connection.getFileDescriptor(), stream->response);
      switch (result) {
        case IO::IO_RESULT::FD_CLOSED:
        case IO::IO_RESULT::ERROR: {
          Logger::LogInfo("Error Writing response ", LOG_NOTICE);
          clearStream(stream);
          return;
        }
        case IO::IO_RESULT::SUCCESS:
          return;
        case IO::IO_RESULT::DONE_TRY_AGAIN:
          stream->client_connection.enableWriteEvent();
          return;
        case IO::IO_RESULT::FULL_BUFFER:
          break;
      }
#endif
    } else
#endif
      result = stream->backend_connection.read();
  }
#if PRINT_DEBUG_FLOW_BUFFERS
  Logger::logmsg(
      LOG_REMOVE,
      "fd:%d IN\tbuffer size: %8lu\tContent-length: %lu\tleft: %lu "
      "header_sent: %s chunk_size_left: %d IO RESULT: %s",
      stream->backend_connection.getFileDescriptor(),
      stream->backend_connection.buffer_size, stream->response.content_length,
      stream->response.message_bytes_left,
      stream->response.getHeaderSent() ? "true" : "false",
      stream->response.chunk_size_left, IO::getResultString(result).data());
#endif
#if EXTENDED_DEBUG_LOG
  extra_log = IO::getResultString(result);
#endif
  switch (result) {
    case IO::IO_RESULT::SSL_HANDSHAKE_ERROR:
    case IO::IO_RESULT::SSL_NEED_HANDSHAKE: {
      stream->backend_connection.server_name =
          stream->client_connection.server_name;
      if (!ssl::SSLConnectionManager::handleHandshake(
              stream->backend_connection.getBackend()->ctx.get(),
              stream->backend_connection, true)) {
        Logger::logmsg(LOG_INFO, "Backend handshake error with %s ",
                      stream->backend_connection.address_str.c_str());
        http_manager::replyError(
            http::Code::ServiceUnavailable,
            http::reasonPhrase(http::Code::ServiceUnavailable),
            listener_config_.err503, stream->client_connection);
        clearStream(stream);
      }
      if (stream->backend_connection.ssl_connected) {
        stream->backend_connection.enableWriteEvent();
      }
      return;
    }
    case IO::IO_RESULT::ZERO_DATA:
    case IO::IO_RESULT::SUCCESS:
    case IO::IO_RESULT::DONE_TRY_AGAIN: {
      if (stream->backend_connection.buffer_size == 0) {
        stream->backend_connection.enableReadEvent();
        return;
      }
      break;
    }
    case IO::IO_RESULT::FULL_BUFFER:    
        break;  
    case IO::IO_RESULT::FD_CLOSED:
      if(!stream->backend_connection.ssl_connected)
      onServerDisconnect(stream);
      return;
    case IO::IO_RESULT::ERROR:
    case IO::IO_RESULT::CANCELLED:
    default: {
      Logger::logmsg(LOG_INFO, "Backend read error with %s, closing stream ",
                     stream->backend_connection.address_str.c_str());
      clearStream(stream);
      return;
    }
  }
#if PRINT_DEBUG_FLOW_BUFFERS
  if (buffer_size_in > 0)
    Logger::logmsg(
        LOG_REMOVE,
        "%.*s IN\tbuffer size: %lu:%8lu \tContent-length: %lu\tleft: %lu "
        "header_sent: %s chunk_size_left: %d IO RESULT: %s CH= %s",
        stream->request.http_message_length, stream->request.http_message,
        buffer_size_in, stream->backend_connection.buffer_size,
        stream->response.content_length, stream->response.message_bytes_left,
        stream->response.getHeaderSent() ? "true" : "false",
        stream->response.chunk_size_left, IO::getResultString(result).data(),
        stream->response.chunked_status != CHUNKED_STATUS::CHUNKED_DISABLED
            ? "T"
            : "F");
#endif
  // disable response timeout timerfd
#if USE_TIMER_FD_TIMEOUT
  if (stream->backend_connection.getBackend()->response_timeout > 0) {
    stream->timer_fd.unset();
    events::EpollManager::deleteFd(stream->timer_fd.getFileDescriptor());
  }
#else
  this->stopTimeOut(fd);
#endif
  if(result == IO::IO_RESULT::FULL_BUFFER) {
    stream->status |= helper::to_underlying(STREAM_STATUS::BCK_READ_PENDING);
    stream->backend_connection.disableEvents();
  }else {
    stream->clearStatus(STREAM_STATUS::BCK_READ_PENDING);
  }
  if (stream->hasOption(STREAM_OPTION::PINNED_CONNECTION) || stream->response.hasPendingData()) {
#ifdef CACHE_ENABLED
    if (stream->response.chunked_status != CHUNKED_STATUS::CHUNKED_DISABLED) {
      auto pending_chunk_bytes = http_manager::handleChunkedData(
          stream->backend_connection, stream->response);
      if (pending_chunk_bytes < 0) {  // we don't have enough data to get next
                                      // chunk size, so we wait for more data
        stream->backend_connection.enableReadEvent();
        return;
      }
    }
    auto service = static_cast<Service*>(stream->request.getService());
    if (service->cache_enabled) {
      CacheManager::handleResponse(stream, service);
    }
#endif

#if PRINT_DEBUG_FLOW_BUFFERS
    Logger::logmsg(
        LOG_REMOVE,
        "OUT buffer size: %8lu\tContent-length: %lu\tleft: %lu\tIO: %s",
        stream->backend_connection.buffer_size, stream->response.content_length,
        stream->response.message_bytes_left,
        IO::getResultString(result).data());
#endif
#if ENABLE_QUICK_RESPONSE
    onClientWriteEvent(stream);
#else
    stream->client_connection.enableWriteEvent();
#endif
    return;
  } else {
    if (stream->backend_connection.buffer_size == 0) return;
    size_t parsed = 0;
    auto ret = stream->response.parseResponse(
        stream->backend_connection.buffer,
        stream->backend_connection.buffer_size, &parsed);
    static size_t total_responses;
    switch (ret) {
      case http_parser::PARSE_RESULT::SUCCESS: {
        stream->backend_connection.getBackend()->calculateLatency(
            stream->backend_connection.time_start
        );
        stream->request.chunked_status = CHUNKED_STATUS::CHUNKED_DISABLED;
        stream->backend_connection.buffer_offset = 0;
        stream->client_connection.buffer_offset = 0;
        stream->client_connection.buffer_size = 0;
        break;
      }
      case http_parser::PARSE_RESULT::TOOLONG:
      case http_parser::PARSE_RESULT::FAILED: {
        Logger::logmsg(
            LOG_REMOVE,
            "%d (%d - %d) PARSE FAILED \nRESPONSE DATA IN\n\t\t buffer "
            "size: %lu \n\t\t Content length: %lu \n\t\t "
            "left: %lu\n%.*s header sent: %s \n",
            total_responses, stream->client_connection.getFileDescriptor(),
            stream->backend_connection.getFileDescriptor(),
            stream->backend_connection.buffer_size,
            stream->response.content_length,
            stream->response.message_bytes_left,
            stream->backend_connection.buffer_size,
            stream->backend_connection.buffer,
            stream->response.getHeaderSent() ? "true" : "false");
        clearStream(stream);
        return;
      }
      case http_parser::PARSE_RESULT::INCOMPLETE:
        stream->backend_connection.enableReadEvent();
        return;
    }

    total_responses++;
    Logger::logmsg(
        LOG_DEBUG, " %lu [%s] %s -> %s [%s (%d) <- %s (%d)]", total_responses,
        static_cast<Service*>(stream->request.getService())->name.c_str(),
        stream->response.http_message_str.data(),
        stream->request.http_message_str.data(),
        stream->client_connection.getPeerAddress().c_str(),
        stream->client_connection.getFileDescriptor(),
        stream->backend_connection.getBackend()->address.c_str(),
        stream->backend_connection.getFileDescriptor());

    stream->backend_connection.getBackend()->setAvgTransferTime(
        stream->backend_connection.time_start);

    if (http_manager::validateResponse(*stream) !=
        validation::REQUEST_RESULT::OK) {
      Logger::logmsg(LOG_NOTICE,
                     "(%lx) backend %s response validation error\n %.*s",
                     /*std::this_thread::get_id()*/ pthread_self(),
                     stream->backend_connection.getBackend()->address.c_str(),
                     stream->backend_connection.buffer_size,
                     stream->backend_connection.buffer);
      http_manager::replyError(
          http::Code::ServiceUnavailable,
          http::reasonPhrase(http::Code::ServiceUnavailable),
          listener_config_.err503, stream->client_connection);
      this->clearStream(stream);
      return;
    }
    stream->status |= helper::to_underlying(STREAM_STATUS::RESPONSE_PENDING);

#if WAF_ENABLED
    if (stream->modsec_transaction != nullptr) {
      if (Waf::checkResponseWaf(*stream)) {
        if (stream->modsec_transaction->m_it.url != nullptr) {
          Logger::logmsg(LOG_WARNING, "(%lx) WAF redirected a request from %s",
                         pthread_self(),
                         stream->client_connection.address_str.c_str());
          // send redirect
          if (http_manager::replyRedirect(
                  stream->modsec_transaction->m_it.status,
                  stream->modsec_transaction->m_it.url, *stream))
            clearStream(stream);
          return;
        } else {
          // reject the request
          auto code =
              static_cast<http::Code>(stream->modsec_transaction->m_it.status);
          http_manager::replyError(code, reasonPhrase(code),
                                   listener_config_.err403,
                                   stream->client_connection);
          Logger::logmsg(LOG_WARNING, "(%lx) WAF rejected a request from %s",
                         pthread_self(),
                         stream->client_connection.address_str.c_str());
        }
        clearStream(stream);
        return;
      }
    }
#endif

    auto service = static_cast<Service*>(stream->request.getService());
#ifdef CACHE_ENABLED
    if (service->cache_enabled) {
      CacheManager::handleResponse(stream, service);
    }
#endif
    http_manager::setBackendCookie(service, stream);
    setStrictTransportSecurity(service, stream);
#if ON_FLY_COMRESSION
    if (!this->is_https_listener) {
      Compression::applyCompression(service, stream);
    }
#endif
    StreamDataLogger::logTransaction(*stream);
#if ENABLE_QUICK_RESPONSE
    onClientWriteEvent(stream);
#else
    stream->client_connection.enableWriteEvent();
#endif
  }
}
void StreamManager::onConnectTimeoutEvent(int fd) {
  DEBUG_COUNTER_HIT(debug__::on_backend_connect_timeout);
#if USE_TIMER_FD_TIMEOUT
  HttpStream* stream = timers_set[fd];
#else
  HttpStream* stream = bck_streams_set[fd];
#endif
  if (stream == nullptr) {
    //Logger::LogInfo("Stream null pointer", LOG_REMOVE);
    deleteFd(fd);
    ::close(fd);
    return;
  }
  auto& listener_config_ = *stream->service_manager->listener_config_;
  // update log info
  StreamDataLogger logger(stream, listener_config_);
  if (stream->hasStatus(STREAM_STATUS::BCK_CONN_PENDING)
#if USE_TIMER_FD_TIMEOUT
      && stream->timer_fd.isTriggered()
#endif
      ) {
      Logger::logmsg(LOG_NOTICE, "(%lx) backend %s connection timeout after %d",
                     /*std::this_thread::get_id()*/ pthread_self(),
                     stream->backend_connection.getBackend()->address.c_str(),
                     stream->backend_connection.getBackend()->conn_timeout);
      onBackendConnectionError(stream);
      return;
  }
}

void StreamManager::onRequestTimeoutEvent(int fd) {
  DEBUG_COUNTER_HIT(debug__::on_request_timeout);
#if USE_TIMER_FD_TIMEOUT
  HttpStream* stream = timers_set[fd];
#else
  HttpStream* stream = cl_streams_set[fd];
#endif
  if (stream == nullptr) {
    deleteFd(fd);
    ::close(fd);
    return;
  }
  auto& listener_config_ = *stream->service_manager->listener_config_;
  // update log info
  StreamDataLogger logger(stream, listener_config_);

  Logger::logmsg(LOG_NOTICE, "(%lx) client request timeout after %d seconds",
                 pthread_self(),
                 stream->service_manager->listener_config_->to);
#if USE_TIMER_FD_TIMEOUT
  if (stream->timer_fd.isTriggered()) {
#endif
    clearStream(stream);
#if USE_TIMER_FD_TIMEOUT
  }
#endif

}

void StreamManager::onResponseTimeoutEvent(int fd) {
  DEBUG_COUNTER_HIT(debug__::on_response_timeout);
#if USE_TIMER_FD_TIMEOUT
  HttpStream* stream = timers_set[fd];
#else
  HttpStream* stream = bck_streams_set[fd];
#endif
  if (stream == nullptr) {
    //Logger::LogInfo("Stream null pointer", LOG_REMOVE);
    deleteFd(fd);
    ::close(fd);
    return;
  }
  auto& listener_config_ = *stream->service_manager->listener_config_;
  // update log info
  StreamDataLogger logger(stream, listener_config_);
#if USE_TIMER_FD_TIMEOUT
  if (stream->timer_fd.isTriggered()) {
#endif
    char caddr[50];
    if (UNLIKELY(Network::getPeerAddress(
                     stream->client_connection.getFileDescriptor(), caddr,
                     50) == nullptr)) {
      Logger::LogInfo("Error getting peer address", LOG_DEBUG);
    } else {
      Logger::logmsg(LOG_NOTICE, "(%lx) e%d %s %.*s from %s",
                    std::this_thread::get_id(),
                    static_cast<int>(http::Code::GatewayTimeout),
                    validation::request_result_reason
                        .at(validation::REQUEST_RESULT::BACKEND_TIMEOUT)
                        .c_str(),
                    stream->request.http_message_length, stream->request.http_message, caddr);
    }
    http_manager::replyError(http::Code::GatewayTimeout,
                             http::reasonPhrase(http::Code::GatewayTimeout),
                             http::reasonPhrase(http::Code::GatewayTimeout),
                             stream->client_connection);
    this->clearStream(stream);
#if USE_TIMER_FD_TIMEOUT
  }
#endif
}
void StreamManager::onSignalEvent([[maybe_unused]] int fd) {
  // TODO::IMPLEMENET
}

void StreamManager::setStreamBackend(HttpStream* stream) {
  auto service = static_cast<Service*>(stream->request.getService());
  this->stopTimeOut(stream->client_connection.getFileDescriptor());

  auto& listener_config_ = *stream->service_manager->listener_config_;
  if (service == nullptr) {
    service = stream->service_manager->getService(stream->request);
    if (service == nullptr) {
      http_manager::replyError(
          http::Code::ServiceUnavailable,
          validation::request_result_reason.at(
              validation::REQUEST_RESULT::SERVICE_NOT_FOUND),
          listener_config_.err503, stream->client_connection);
      this->clearStream(stream);
      return;
    }
    stream->request.setService(service);
  }

  if(stream->backend_connection.connection_retries >= service->getBackendSetSize()){
      // No backend available
      Logger::logmsg(LOG_INFO, "Service connection limit reached");
      http_manager::replyError(http::Code::ServiceUnavailable,
                               validation::request_result_reason.at(
                                   validation::REQUEST_RESULT::BACKEND_NOT_FOUND),
                               listener_config_.err503,
                               stream->client_connection);
      this->clearStream(stream);
      return;
  }
  if (stream->backend_connection.getFileDescriptor() > 0) { //TODO::
      if (stream->hasStatus(STREAM_STATUS::BCK_CONN_PENDING)) {
          stream->backend_connection.getBackend()->decreaseConnTimeoutAlive();
      }else{
          stream->backend_connection.getBackend()->decreaseConnection();
      }
    deleteFd(stream->backend_connection.getFileDescriptor());
    bck_streams_set[stream->backend_connection.getFileDescriptor()] = nullptr;
    bck_streams_set.erase(stream->backend_connection.getFileDescriptor());
    stream->backend_connection.closeConnection();
  }
  stream->backend_connection.reset();
  auto bck = service->getBackend(stream->client_connection, stream->request);
  if (bck == nullptr) {
    // No backend available
    http_manager::replyError(http::Code::ServiceUnavailable,
                             validation::request_result_reason.at(
                                 validation::REQUEST_RESULT::BACKEND_NOT_FOUND),
                             listener_config_.err503,
                             stream->client_connection);
    this->clearStream(stream);
    return;
  } else {
    // update log info
    StreamDataLogger logger(stream, listener_config_);
    IO::IO_OP op_state;
    stream->backend_connection.reset();
    stream->response.reset_parser();
    Logger::logmsg(LOG_DEBUG, "RETRY [%s] %.*s [%s (%d) -> %s (%d)]",
                   service->name.c_str(), stream->request.http_message_length,
                   stream->request.http_message,
                   stream->client_connection.getPeerAddress().c_str(),
                   stream->client_connection.getFileDescriptor(),
                   bck->address.c_str(),
                   stream->backend_connection.getFileDescriptor());
    switch (bck->backend_type) {
      case BACKEND_TYPE::REMOTE: {
        stream->backend_connection.setBackend(bck);
        Time::getTime(stream->backend_connection.time_start);
        stream->status |= helper::to_underlying(STREAM_STATUS::BCK_CONN_PENDING);
        op_state = stream->backend_connection.doConnect(*bck->address_info,
                                                        bck->conn_timeout);
        switch (op_state) {
          case IO::IO_OP::OP_ERROR: {
            Logger::logmsg(LOG_NOTICE, "Error connecting to backend %s",
                           bck->address.data());           
            onBackendConnectionError(stream);
            return;
          }
          case IO::IO_OP::OP_IN_PROGRESS: {
            stream->status |=
                helper::to_underlying(STREAM_STATUS::BCK_CONN_PENDING);
#if USE_TIMER_FD_TIMEOUT
            stream->timer_fd.set(bck->conn_timeout * 1000);
            addFd(stream->timer_fd.getFileDescriptor(),
                  EVENT_TYPE::READ_ONESHOT, EVENT_GROUP::CONNECT_TIMEOUT);
#else
            setTimeOut(stream->backend_connection.getFileDescriptor(),
                       TIMEOUT_TYPE::SERVER_WRITE_TIMEOUT, bck->conn_timeout);
#endif
            stream->backend_connection.getBackend()->increaseConnTimeoutAlive();
          }
          break;
          case IO::IO_OP::OP_SUCCESS: {
            DEBUG_COUNTER_HIT(debug__::on_backend_connect);
            stream->backend_connection.getBackend()->increaseConnection();
            break;
          }
        }
        bck_streams_set[stream->backend_connection.getFileDescriptor()] =
            stream;
        stream->backend_connection.enableEvents(this, EVENT_TYPE::WRITE,
                                                EVENT_GROUP::SERVER);
        if (stream->backend_connection.getBackend()->nf_mark > 0)
          Network::setSOMarkOption(
              stream->backend_connection.getFileDescriptor(),
              stream->backend_connection.getBackend()->nf_mark);
        // Rewrite destination
        if (stream->request.add_destination_header) {
          // remove previously added headers
          stream->request.removeHeader(http::HTTP_HEADER_NAME::DESTINATION);
          std::string header_value =
              stream->backend_connection.getBackend()->isHttps() ? "https://"
                                                                 : "http://";
          header_value += stream->backend_connection.getPeerAddress();
          header_value += ':';
          header_value += stream->request.path;
          stream->request.addHeader(http::HTTP_HEADER_NAME::DESTINATION,
                                    header_value);
        }
        if (!stream->request.host_header_found) {
          stream->request.removeHeader(http::HTTP_HEADER_NAME::HOST);
          std::string header_value = "";
          header_value += stream->backend_connection.getBackend()->address;
          header_value += ':';
          header_value +=
              std::to_string(stream->backend_connection.getBackend()->port);
          stream->request.addHeader(http::HTTP_HEADER_NAME::HOST, header_value);
        }
        /* After setting the backend and the service in the first request,
         * pin the connection if the PinnedConnection service config
         * parameter is true. Note: The first request must be HTTP. */
        if (service->service_config.pinned_connection) {
          stream->options |= helper::to_underlying(STREAM_OPTION::PINNED_CONNECTION);
        }
        break;
      }

      case BACKEND_TYPE::EMERGENCY_SERVER:

        break;
      case BACKEND_TYPE::REDIRECT: {
        if(http_manager::replyRedirect(*stream, *bck))
          clearStream(stream);
        return;
      }
      case BACKEND_TYPE::CACHE_SYSTEM:
        break;
    }
  }
}

void StreamManager::onServerWriteEvent(HttpStream* stream) {
  DEBUG_COUNTER_HIT(debug__::on_send_request);
#if EXTENDED_DEBUG_LOG
  std::string extra_log;
  ScopeExit logStream{[stream, &extra_log] {
     HttpStream::dumpDebugData(stream,"onServerW", extra_log.data());
  }};
#endif
  auto& listener_config_ = *stream->service_manager->listener_config_;
  // update log info
  StreamDataLogger logger(stream, listener_config_);
  int fd = stream->backend_connection.getFileDescriptor();
  // Send client request to backend server
#if USE_TIMER_FD_TIMEOUT
  this->deleteFd(stream->timer_fd.getFileDescriptor());
  stream->timer_fd.unset();
#else
  stopTimeOut(fd);
#endif
  if (stream->hasStatus(STREAM_STATUS::BCK_CONN_PENDING)) {
    DEBUG_COUNTER_HIT(debug__::on_backend_connect);
    stream->clearStatus(STREAM_STATUS::BCK_CONN_PENDING);
    stream->backend_connection.getBackend()->decreaseConnTimeoutAlive();
    stream->backend_connection.getBackend()->increaseConnection();
    stream->backend_connection.getBackend()->setAvgConnTime(
            stream->backend_connection.time_start);

  }
  /*Check if the buffer has data to be send */
  if (stream->client_connection.buffer_size == 0) {
    stream->client_connection.enableReadEvent();
    stream->backend_connection.enableReadEvent();
    return;
  }
  /* If the connection is pinned or we have content length remaining to send
   * , then we need to write the buffer content without
   * applying any kind of modification. */
  IO::IO_RESULT result = IO::IO_RESULT::ERROR;
  if (stream->hasOption(STREAM_OPTION::PINNED_CONNECTION)
      || stream->request.hasPendingData()) {
    size_t written = 0;

    if (stream->backend_connection.getBackend()->isHttps()) {
      result = ssl::SSLConnectionManager::handleWrite(
          stream->backend_connection, stream->client_connection, written);
    } else {
      if (stream->client_connection.buffer_size > 0)
        result = stream->client_connection.writeTo(
            stream->backend_connection.getFileDescriptor(), written);
#if ENABLE_ZERO_COPY
      else if (stream->client_connection.splice_pipe.bytes > 0)
        result = stream->client_connection.zeroWrite(
            stream->backend_connection.getFileDescriptor(), stream->request);
#endif
    }
#if EXTENDED_DEBUG_LOG
    extra_log = IO::getResultString(result);
#endif
    switch (result) {
      case IO::IO_RESULT::SSL_HANDSHAKE_ERROR:
      case IO::IO_RESULT::SSL_NEED_HANDSHAKE: {
        if (!ssl::SSLConnectionManager::handleHandshake(
                stream->backend_connection.getBackend()->ctx.get(),
                stream->backend_connection, true)) {
          Logger::logmsg(
              LOG_DEBUG, "Handshake error with %s ",
              stream->backend_connection.getBackend()->address.data());
          http_manager::replyError(
              http::Code::ServiceUnavailable,
              http::reasonPhrase(http::Code::ServiceUnavailable),
              listener_config_.err503, stream->client_connection);
          clearStream(stream);
        }
        if (stream->backend_connection.ssl_connected) {
          stream->backend_connection.enableWriteEvent();
        }
        return;
      }
      case IO::IO_RESULT::FD_CLOSED:
      case IO::IO_RESULT::CANCELLED:
      case IO::IO_RESULT::FULL_BUFFER:
      case IO::IO_RESULT::ERROR:
      default:
        Logger::LogInfo("Error sending request ", LOG_DEBUG);
        clearStream(stream);
        return;
      case IO::IO_RESULT::SUCCESS:
      case IO::IO_RESULT::DONE_TRY_AGAIN:
        break;
    }
#if PRINT_DEBUG_FLOW_BUFFERS
    Logger::logmsg(LOG_REMOVE,
                   "OUT buffer size: %8lu\tContent-length: %lu\tleft: "
                   "%lu\twritten: %d\tIO: %s",
                   stream->client_connection.buffer_size,
                   stream->request.content_length,
                   stream->request.message_bytes_left, written,
                   IO::getResultString(result).data());
#endif
    if (!stream->hasOption(STREAM_OPTION::PINNED_CONNECTION)) {
      if (stream->request.chunked_status ==
              http::CHUNKED_STATUS::CHUNKED_LAST_CHUNK &&
          stream->client_connection.buffer_size == 0) {
        stream->request.reset_parser();
      } else if (stream->request.message_bytes_left > 0) {
        stream->request.message_bytes_left -= written;
        if (stream->request.message_bytes_left == 0) {
          stream->request.reset_parser();
        }
      }
    }
    if (stream->client_connection.buffer_size > 0) {
      stream->client_connection.buffer_offset += written;
      stream->backend_connection.enableWriteEvent();
      return;
    } else {
      stream->client_connection.buffer_offset = 0;
      stream->backend_connection.enableReadEvent();
      stream->client_connection.enableReadEvent();
    }
    return;
  }

  if (stream->backend_connection.getBackend()->isHttps()) {
    result = ssl::SSLConnectionManager::handleDataWrite(
        stream->backend_connection, stream->client_connection, stream->request);
  } else {
    result = stream->client_connection.writeTo(stream->backend_connection,
                                               stream->request);
  }
#if EXTENDED_DEBUG_LOG
  extra_log = IO::getResultString(result);
#endif
  switch (result) {
    case IO::IO_RESULT::SSL_HANDSHAKE_ERROR:
    case IO::IO_RESULT::SSL_NEED_HANDSHAKE: {
      stream->backend_connection.server_name =
          stream->client_connection.server_name;
      if (!ssl::SSLConnectionManager::handleHandshake(
              stream->backend_connection.getBackend()->ctx.get(),
              stream->backend_connection, true)) {
        Logger::logmsg(LOG_DEBUG, "Handshake error with %s ",
                       stream->backend_connection.getBackend()->address.data());
        clearStream(stream);
        return;
      }
      if (!stream->backend_connection.ssl_connected) {
        stream->backend_connection.enableReadEvent();
        return;
      } else {
        stream->backend_connection.enableWriteEvent();
      }
      return;
    }
    case IO::IO_RESULT::FD_CLOSED:
    case IO::IO_RESULT::CANCELLED:
    case IO::IO_RESULT::FULL_BUFFER:
    case IO::IO_RESULT::ERROR:
      Logger::LogInfo("Error sending request to backend ", LOG_DEBUG);
      clearStream(stream);
      return;
    case IO::IO_RESULT::SUCCESS:
    case IO::IO_RESULT::DONE_TRY_AGAIN:
      if (!stream->request.getHeaderSent()) {
        stream->backend_connection.enableWriteEvent();
        return;
      }
      break;
    default:
      Logger::LogInfo("Error sending data to backend server", LOG_DEBUG);
      clearStream(stream);
      return;
  }
#if USE_TIMER_FD_TIMEOUT
  stream->timer_fd.set(
      stream->backend_connection.getBackend()->response_timeout * 1000);
  addFd(stream->timer_fd.getFileDescriptor(), EVENT_TYPE::READ_ONESHOT,
        EVENT_GROUP::RESPONSE_TIMEOUT);
#else
  setTimeOut(stream->backend_connection.getFileDescriptor(),
             TIMEOUT_TYPE::SERVER_READ_TIMEOUT,
             stream->backend_connection.getBackend()->response_timeout);
#endif
#if PRINT_DEBUG_FLOW_BUFFERS
  Logger::logmsg(
      LOG_REMOVE,
      "OUT buffer size: %8lu\tContent-length: %lu\tleft: "
      "%lu\tIO: %s",
      stream->client_connection.buffer_size, stream->request.content_length,
      stream->request.message_bytes_left, IO::getResultString(result).data());
#endif
  Time::getTime(stream->backend_connection.time_start);
  stream->client_connection.enableReadEvent();
  stream->backend_connection.enableReadEvent();
  stream->clearStatus(STREAM_STATUS::REQUEST_PENDING);
  if (stream->hasStatus(STREAM_STATUS::CL_READ_PENDING)) {
#if EXTENDED_DEBUG_LOG
    HttpStream::dumpDebugData(stream, "ClientW-ReadPending", "WROTE REQ PENDING ");
#endif
    onRequestEvent(stream->client_connection.getFileDescriptor());
  }
}

void StreamManager::onClientWriteEvent(HttpStream* stream) {
  if(stream == nullptr) return;
  DEBUG_COUNTER_HIT(debug__::on_send_response);
#if EXTENDED_DEBUG_LOG
  std::string extra_log;
  ScopeExit logStream{
      [stream, &extra_log] {  HttpStream::dumpDebugData(stream,"onClientW",extra_log.data()); }};
#endif
  auto& listener_config_ = *stream->service_manager->listener_config_;
  // update log info
  StreamDataLogger logger(stream, listener_config_);

#if PRINT_DEBUG_FLOW_BUFFERS
  Logger::logmsg(
      LOG_REMOVE, "IN\tbuffer size: %8lu\tContent-length: %lu\tleft: %lu",
      stream->backend_connection.buffer_size, stream->response.content_length,
      stream->response.message_bytes_left);
  auto buffer_size_in = stream->backend_connection.buffer_size;
#endif
  IO::IO_RESULT result = IO::IO_RESULT::ERROR;
  /* If the connection is pinned, then we need to write the buffer
   * content without applying any kind of modification. */
  if (stream->hasOption(STREAM_OPTION::PINNED_CONNECTION) || stream->response.hasPendingData()) {
    size_t written = 0;

    if (stream->service_manager->is_https_listener) {
      result = ssl::SSLConnectionManager::handleWrite(
          stream->client_connection, stream->backend_connection, written);
    } else {
      if (stream->backend_connection.buffer_size > 0)
        result = stream->backend_connection.writeTo(
            stream->client_connection.getFileDescriptor(), written);
#if ENABLE_ZERO_COPY
      else if (stream->backend_connection.splice_pipe.bytes > 0)
        result = stream->backend_connection.zeroWrite(
            stream->client_connection.getFileDescriptor(), stream->response);
#endif
    }
#if EXTENDED_DEBUG_LOG
    extra_log = IO::getResultString(result);
#endif
    switch (result) {
      case IO::IO_RESULT::SSL_HANDSHAKE_ERROR:
      case IO::IO_RESULT::SSL_NEED_HANDSHAKE: {
        if (!ssl::SSLConnectionManager::handleHandshake(
                *stream->service_manager->ssl_context,
                stream->client_connection)) {
          Logger::logmsg(LOG_INFO, "Handshake error with %s ",
                         stream->client_connection.getPeerAddress().c_str());
          clearStream(stream);
        }
        if (stream->client_connection.ssl_connected) {
          stream->backend_connection.server_name =
              stream->client_connection.server_name;
          onRequestEvent(stream->client_connection.getFileDescriptor());
          return;
        }
        return;
      }
      case IO::IO_RESULT::ZERO_DATA:
      case IO::IO_RESULT::SUCCESS:
      case IO::IO_RESULT::DONE_TRY_AGAIN:
        break;
      case IO::IO_RESULT::FD_CLOSED:
      case IO::IO_RESULT::CANCELLED:
      case IO::IO_RESULT::FULL_BUFFER:
      case IO::IO_RESULT::ERROR:
      default:
        Logger::logmsg(
            LOG_DEBUG,
            "fd: %d:%d %.*s Error sending response IN\tbuffer size: "
            "%8lu\tContent-length: %lu\tleft: %lu "
            "header_sent: %s chunk_size_left: %d IO RESULT: %s CH= %s",
            stream->client_connection.getFileDescriptor(),
            stream->backend_connection.getFileDescriptor(),
            stream->request.http_message_length, stream->request.http_message,
            stream->backend_connection.buffer_size,
            stream->response.content_length,
            stream->response.message_bytes_left,
            stream->response.getHeaderSent() ? "true" : "false",
            stream->response.chunk_size_left,
            IO::getResultString(result).data(),
            stream->response.chunked_status != CHUNKED_STATUS::CHUNKED_DISABLED
                ? "T"
                : "F");
        clearStream(stream);
        return;
    }
    if (!stream->hasOption(STREAM_OPTION::PINNED_CONNECTION)) {
      if (stream->response.chunked_status ==
              http::CHUNKED_STATUS::CHUNKED_LAST_CHUNK &&
          stream->backend_connection.buffer_size == 0) {
        stream->response.reset_parser();
      } else if (stream->response.message_bytes_left > 0) {
        stream->response.message_bytes_left -= written;
        if (stream->response.message_bytes_left <= 0)
          stream->response.reset_parser();
      }
    }
#if PRINT_DEBUG_FLOW_BUFFERS
    if (stream->backend_connection.buffer_size != 0)
      Logger::logmsg(
          LOG_DEBUG,
          " OUT EAGAIN %.*s buffer size: %lu > %8lu \tContent-length: "
          "%lu\tleft: "
          "%lu\twritten: %d\tIO: %s",
          stream->request.http_message_length, stream->request.http_message,
          buffer_size_in, stream->backend_connection.buffer_size,
          stream->response.content_length, stream->response.message_bytes_left,
          written, IO::getResultString(result).data());
#endif
#ifdef CACHE_ENABLED
    if (!stream->response.isCached())
#endif
      if (stream->backend_connection.buffer_size > 0) {
        stream->backend_connection.buffer_offset = written;
        stream->client_connection.enableWriteEvent();
      } else {
        if(stream->hasStatus(STREAM_STATUS::CLOSE_CONNECTION)){
          clearStream(stream);
          return;
        }
        stream->backend_connection.buffer_offset = 0;
        stream->backend_connection.enableReadEvent();
        stream->client_connection.enableReadEvent();
      }
    stream->client_connection.enableReadEvent();
    stream->backend_connection.enableReadEvent();

    if (stream->hasStatus(STREAM_STATUS::BCK_READ_PENDING)) {
#if EXTENDED_DEBUG_LOG
      HttpStream::dumpDebugData(stream, "ClientW-ReadPending", "WROTE RESP PENDING ");
#endif
      onResponseEvent(stream->backend_connection.getFileDescriptor());
    }
    return;
  }

  if (stream->backend_connection.buffer_size == 0
#ifdef CACHE_ENABLED
      && !stream->response.isCached()
#endif
  )
    return;

  if (stream->service_manager->is_https_listener) {
    result = ssl::SSLConnectionManager::handleDataWrite(
        stream->client_connection, stream->backend_connection,
        stream->response);
  } else {
    result = stream->backend_connection.writeTo(stream->client_connection,
                                                stream->response);
  }
#if EXTENDED_DEBUG_LOG
  extra_log = IO::getResultString(result);
#endif
  switch (result) {
    case IO::IO_RESULT::SSL_HANDSHAKE_ERROR:
    case IO::IO_RESULT::SSL_NEED_HANDSHAKE: {
      if (!ssl::SSLConnectionManager::handleHandshake(
              *stream->service_manager->ssl_context,
              stream->client_connection)) {
        if ((ERR_GET_REASON(ERR_peek_error()) == SSL_R_HTTP_REQUEST) &&
            (ERR_GET_LIB(ERR_peek_error()) == ERR_LIB_SSL)) {
          /* the client speaks plain HTTP on our HTTPS port */
          Logger::logmsg(LOG_NOTICE,
                         "Client %s sent a plain HTTP message to an SSL port",
                         stream->client_connection.getPeerAddress().c_str());
          if (listener_config_.nossl_redir > 0) {
            Logger::logmsg(LOG_NOTICE,
                           "(%lx) errNoSsl from %s redirecting to \"%s\"",
                           pthread_self(),
                           stream->client_connection.getPeerAddress().c_str(),
                           listener_config_.nossl_url.data());
            if (http_manager::replyRedirect(listener_config_.nossl_redir,
                                            listener_config_.nossl_url,
                                            *stream))
              clearStream(stream);
            return;
          } else {
            Logger::logmsg(LOG_NOTICE, "(%lx) errNoSsl from %s sending error",
                           pthread_self(),
                           stream->client_connection.getPeerAddress().c_str());
            http_manager::replyError(http::Code::BadRequest,
                                     http::reasonPhrase(http::Code::BadRequest),
                                     listener_config_.errnossl,
                                     stream->client_connection);
          }
        } else {
          Logger::logmsg(LOG_DEBUG, "fd: %d:%d Handshake error with %s ",
                         stream->client_connection.getFileDescriptor(),
                         stream->backend_connection.getFileDescriptor(),
                         stream->client_connection.getPeerAddress().c_str());
        }
        clearStream(stream);
      }
      if (stream->client_connection.ssl_connected) {
        DEBUG_COUNTER_HIT(debug__::on_handshake);
        httpsHeaders(stream, listener_config_.clnt_check);
        stream->backend_connection.server_name =
            stream->client_connection.server_name;
      }
      return;
    }
    case IO::IO_RESULT::FD_CLOSED:
    case IO::IO_RESULT::CANCELLED:
    case IO::IO_RESULT::FULL_BUFFER:
    case IO::IO_RESULT::ERROR:
      Logger::logmsg(LOG_DEBUG, "Error sending response: %s",
                    IO::getResultString(result).data());
      clearStream(stream);
      return;
    case IO::IO_RESULT::SUCCESS:
    case IO::IO_RESULT::DONE_TRY_AGAIN:
      if (!stream->response.getHeaderSent()) {
        // TODO:: retry with left headers data in response.
        stream->client_connection.enableWriteEvent();
        return;
      }
      break;
    default:
      Logger::logmsg(
          LOG_DEBUG,
          "fd: %d:%d %.*s Error sending response IN\tbuffer size: "
          "%8lu\tContent-length: %lu\tleft: %lu "
          "header_sent: %s chunk_size_left: %d IO RESULT: %s CH= %s",
          stream->client_connection.getFileDescriptor(),
          stream->backend_connection.getFileDescriptor(),
          stream->request.http_message_length, stream->request.http_message,
          stream->backend_connection.buffer_size,
          stream->response.content_length, stream->response.message_bytes_left,
          stream->response.getHeaderSent() ? "true" : "false",
          stream->response.chunk_size_left, IO::getResultString(result).data(),
          stream->response.chunked_status != CHUNKED_STATUS::CHUNKED_DISABLED
              ? "T"
              : "F");
      clearStream(stream);
      return;
  }
#if PRINT_DEBUG_FLOW_BUFFERS
  if (stream->backend_connection.buffer_size != 0)
    Logger::logmsg(
        LOG_REMOVE,
        " OUT EAGAIN  %.*s buffer size: %lu > %8lu \tContent-length: "
        "%lu\tleft: "
        "%lu\tIO: %s",
        stream->request.http_message_length, stream->request.http_message,
        buffer_size_in, stream->backend_connection.buffer_size,
        stream->response.content_length, stream->response.message_bytes_left,
        IO::getResultString(result).data());
#endif
  if (stream->request.upgrade_header &&
      stream->request.connection_header_upgrade &&
      stream->response.http_status_code == 101) {
    stream->options |= helper::to_underlying(STREAM_OPTION::PINNED_CONNECTION);
    std::string upgrade_header_value;
    stream->request.getHeaderValue(http::HTTP_HEADER_NAME::UPGRADE,
                                   upgrade_header_value);
    auto it = http::http_info::upgrade_protocols.find(upgrade_header_value);
    if (it != http::http_info::upgrade_protocols.end()) {
      switch (it->second) {
        case UPGRADE_PROTOCOLS::NONE:
          break;
        case UPGRADE_PROTOCOLS::WEBSOCKET:
          stream->options |= helper::to_underlying(STREAM_OPTION::WS);
          break;
        case UPGRADE_PROTOCOLS::H2C:
          stream->options |= helper::to_underlying(STREAM_OPTION::H2C);
          break;
        case UPGRADE_PROTOCOLS::TLS:
          break;
      }
    }
  }

  if (stream->backend_connection.buffer_size > 0)
    stream->client_connection.enableWriteEvent();
  else {
    if (stream->hasStatus(STREAM_STATUS::CLOSE_CONNECTION)) {
      clearStream(stream);
      return;
    }
#ifdef CACHE_ENABLED
    if (!stream->response.isCached())
#endif
      stream->backend_connection.enableReadEvent();
    stream->client_connection.enableReadEvent();
  }
  stream->clearStatus(STREAM_STATUS::RESPONSE_PENDING);
  if (stream->hasStatus(STREAM_STATUS::BCK_READ_PENDING)) {
#if EXTENDED_DEBUG_LOG
     HttpStream::dumpDebugData(stream,"ClientW-ReadPending", "PENDING ");
#endif
    stream->backend_connection.enableReadEvent();
    onResponseEvent(stream->backend_connection.getFileDescriptor());
  }
}

bool StreamManager::registerListener(
    std::weak_ptr<ServiceManager> service_manager) {
  auto& listener_config = service_manager.lock()->listener_config_;
  auto address =
      Network::getAddress(listener_config->address, listener_config->port);
  listener_config->addr_info = address.release();
  int listen_fd = Connection::listen(*listener_config->addr_info);

  if (listen_fd > 0) {
    service_manager_set[listen_fd] = service_manager;
    return handleAccept(listen_fd);
  }
  return false;
}

/** Clears the HttpStream. It deletes all the timers and events. Finally,
 * deletes the HttpStream.
 */
void StreamManager::clearStream(HttpStream* stream) {
  if (stream == nullptr) {
    return;
  }
#ifdef CACHE_ENABLED
  CacheManager::handleStreamClose(stream);
#endif
#if USE_TIMER_FD_TIMEOUT
  if (stream->timer_fd.getFileDescriptor() > 0) {
    deleteFd(stream->timer_fd.getFileDescriptor());
    stream->timer_fd.unset();
    timers_set[stream->timer_fd.getFileDescriptor()] = nullptr;
    timers_set.erase(stream->timer_fd.getFileDescriptor());
#if DEBUG_STREAM_EVENTS_COUNT
    clear_timer++;
#endif
  }
#endif
  if (stream->client_connection.getFileDescriptor() > 0) {
    deleteFd(stream->client_connection.getFileDescriptor());
    cl_streams_set[stream->client_connection.getFileDescriptor()] = nullptr;
    cl_streams_set.erase(stream->client_connection.getFileDescriptor());
    stream->client_connection.closeConnection();
#if DEBUG_STREAM_EVENTS_COUNT
    clear_client++;
#endif
  }
  if (stream->backend_connection.getFileDescriptor() > 0) {
    if (stream->hasStatus(STREAM_STATUS::BCK_CONN_PENDING)) {
      stream->backend_connection.getBackend()->decreaseConnTimeoutAlive();
    }else{
      stream->backend_connection.getBackend()->decreaseConnection();
    }
#if DEBUG_STREAM_EVENTS_COUNT
    clear_backend++;
#endif
    deleteFd(stream->backend_connection.getFileDescriptor());
    bck_streams_set[stream->backend_connection.getFileDescriptor()] = nullptr;
    bck_streams_set.erase(stream->backend_connection.getFileDescriptor());
    stream->backend_connection.closeConnection();
  }
#if DEBUG_STREAM_EVENTS_COUNT
  clear_stream++;
#endif
  DEBUG_COUNTER_HIT(debug__::on_clear_stream);
  stream->service_manager->established_connection--;
  delete stream;
}

void StreamManager::onClientDisconnect(HttpStream* stream) {
  if (stream == nullptr) return;
  DEBUG_COUNTER_HIT(debug__::on_client_disconnect);
  auto& listener_config_ = *stream->service_manager->listener_config_;
  // update log info
  StreamDataLogger logger(stream, listener_config_);
//  Logger::logmsg(LOG_DEBUG, "fd: %d:%d Client closed connection",
//                 stream->client_connection.getFileDescriptor(),
//                 stream->backend_connection.getFileDescriptor());
  clearStream(stream);
}

std::string StreamManager::handleTask(ctl::CtlTask& task) {
  if (!isHandler(task)) return JSON_OP_RESULT::ERROR;

  if (task.command == ctl::CTL_COMMAND::EXIT) {
    Logger::logmsg(LOG_REMOVE, "Exit command received");
    stop();

    return JSON_OP_RESULT::OK;
  }
#if DEBUG_STREAM_EVENTS_COUNT
  switch (task.subject) {
    case ctl::CTL_SUBJECT::DEBUG: {
      std::unique_ptr<JsonObject> root{new JsonObject()};
      std::unique_ptr<JsonObject> status{new JsonObject()};
      status->emplace(
          "HttpSteam",
          std::make_unique<JsonDataValue>(cl_streams_set.size()));
      status->emplace(
          "clear_stream",
          std::make_unique<JsonDataValue>(clear_stream));
      status->emplace(
          "clear_client",
          std::make_unique<JsonDataValue>(clear_client));
      status->emplace(
          "clear_backend",
          std::make_unique<JsonDataValue>(clear_backend));
      status->emplace(
          "clear_timer",
          std::make_unique<JsonDataValue>(clear_timer));
      root->emplace("W_"+std::to_string(this->getWorkerId()), std::move(status));
      return root->stringify();
    }
  }
#endif
  return JSON_OP_RESULT::ERROR;
}

bool StreamManager::isHandler(ctl::CtlTask& task) {
  return task.target == ctl::CTL_HANDLER_TYPE::ALL ||
         task.target == ctl::CTL_HANDLER_TYPE::STREAM_MANAGER;
}

void StreamManager::onServerDisconnect(HttpStream* stream) {
  if (stream == nullptr) return;
  DEBUG_COUNTER_HIT(debug__::on_backend_disconnect);
  auto& listener_config_ = *stream->service_manager->listener_config_;
  // update log info
  StreamDataLogger logger(stream, listener_config_);
#if EXTENDED_DEBUG_LOG
  HttpStream::dumpDebugData(stream, "onServerDisconnect", "DISCONNECT");
#endif
  if(stream->backend_connection.getFileDescriptor() > 0) {
#if DEBUG_STREAM_EVENTS_COUNT
    clear_backend++;
#endif
    deleteFd(stream->backend_connection.getFileDescriptor());
    bck_streams_set[stream->backend_connection.getFileDescriptor()] = nullptr;
    bck_streams_set.erase(stream->backend_connection.getFileDescriptor());
    stream->backend_connection.closeConnection();
  }

  if (stream->backend_connection.getBackend() != nullptr && stream->hasStatus(STREAM_STATUS::BCK_CONN_PENDING)) {
    onBackendConnectionError(stream);
    return;
  }else {
      if(stream->backend_connection.getBackend() != nullptr)
         stream->backend_connection.getBackend()->decreaseConnection();
    if (stream->backend_connection.buffer_size > 0
#if ENABLE_ZERO_COPY
      || stream->backend_connection.splice_pipe.bytes > 0
#endif
        ) {
      stream->status |= helper::to_underlying(STREAM_STATUS::CLOSE_CONNECTION);
      stream->client_connection.enableWriteEvent();
      return;
    }

  }
  clearStream(stream);
}

void StreamManager::stopListener(int listener_id, bool cut_connection) {
  for (const auto& lc : service_manager_set) {
    auto spt = lc.second.lock();
    if (spt && listener_id == spt->id) {
      this->stopAccept(lc.first);

      ::close(lc.first);
    }
  }
  for (auto it = service_manager_set.begin();
       it != service_manager_set.end();) {
    auto spt = it->second.lock();
    if (spt && listener_id == spt->id) {
      this->stopAccept(it->first);
      ::close(it->first);
      //      it = listener_config_set.erase(it);
      break;
    } else {
      it++;
    }
  }
  if (cut_connection) {
    for (auto it = cl_streams_set.begin(); it != cl_streams_set.end();) {
      if (it->second->service_manager->id == listener_id) {
        auto item = it++;
        clearStream(item->second);
      } else
        it++;
    }
  }
}
#if USE_TIMER_FD_TIMEOUT==0
void StreamManager::onTimeOut(int fd, TIMEOUT_TYPE type) {
  switch (type) {
    case TIMEOUT_TYPE::SERVER_WRITE_TIMEOUT:
      onConnectTimeoutEvent(fd);
      break;
    case TIMEOUT_TYPE::CLIENT_READ_TIMEOUT:
      onRequestTimeoutEvent(fd);
      break;
    case TIMEOUT_TYPE::SERVER_READ_TIMEOUT:
      onResponseTimeoutEvent(fd);
      break;
    case TIMEOUT_TYPE::CLIENT_WRITE_TIMEOUT:
      break;
    }
}
#endif

void StreamManager::onBackendConnectionError(HttpStream *stream)
{
  DEBUG_COUNTER_HIT(debug__::on_backend_connect_error);
  auto& listener_config_ = *stream->service_manager->listener_config_;
  if (stream->backend_connection.getBackend()->getEstablishedConn() == 0 &&
      stream->backend_connection.getBackend()->getPendingConn() == 0) {
    stream->backend_connection.getBackend()->setStatus(
        BACKEND_STATUS::BACKEND_DOWN);
    Logger::logmsg(
        LOG_NOTICE,
        "(%lx) BackEnd %s:%d dead (killed) in farm: '%s', service: '%s'",
        pthread_self(), stream->backend_connection.getBackend()->address.data(),
        stream->backend_connection.getBackend()->port,
        listener_config_.name.data(),
        stream->backend_connection.getBackend()
            ->backend_config->srv_name.data());
  }
  stream->backend_connection.getBackend()->decreaseConnTimeoutAlive();
  setStreamBackend(stream);

  //  // No backend available
  //  http_manager::replyError(http::Code::ServiceUnavailable,
  //                           validation::request_result_reason.at(
  //                               validation::REQUEST_RESULT::BACKEND_NOT_FOUND),
  //                           listener_config_.err503,
  //                           stream->client_connection);
  //  this->clearStream(stream);
}
