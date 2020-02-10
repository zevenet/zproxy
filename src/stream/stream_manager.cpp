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

#if HELLO_WORLD_SERVER
void StreamManager::HandleEvent(int fd, EVENT_TYPE event_type,
                                EVENT_GROUP event_group) {
  switch (event_type) {
    case READ_ONESHOT: {
      HttpStream* stream = streams_set[fd];
      if (stream == nullptr) {
        stream = new HttpStream();
        stream->client_connection.setFileDescriptor(fd);
        streams_set[fd] = stream;
      }
      auto connection = stream->getConnection(fd);
      connection->read();
      connection->buffer_size = 1;  // reset buffer size to avoid buffer
                                    // overflow due to not consuming buffer
                                    // data.
      updateFd(fd, EVENT_TYPE::WRITE, EVENT_GROUP::CLIENT);
      break;
    }

    case READ: {
      HttpStream* stream = streams_set[fd];
      if (stream == nullptr) {
        stream = new HttpStream();
        stream->client_connection.setFileDescriptor(fd);
        streams_set[fd] = stream;
      }
      auto connection = stream->getConnection(fd);
      connection->read();
      connection->buffer_size = 1;
      updateFd(fd, EVENT_TYPE::WRITE, EVENT_GROUP::CLIENT);
    }

    case WRITE: {
      auto stream = streams_set[fd];
      if (stream == nullptr) {
        Logger::LogInfo("Connection closed prematurely" + std::to_string(fd));
        return;
      }
      auto io_result = stream->client_connection.write(this->e200.c_str(),
                                                       this->e200.length());
      switch (io_result) {
        case IO::ERROR:
        case IO::FD_CLOSED:
        case IO::FULL_BUFFER:
          Logger::LogInfo("Something happend sentid e200", LOG_DEBUG);
          break;
        case IO::SUCCESS:
        case IO::DONE_TRY_AGAIN:
          updateFd(fd, READ, EVENT_GROUP::CLIENT);
          break;
      }

      break;
    }
    case CONNECT: {
      int new_fd;
      //      do {
      new_fd = listener_connection.doAccept();
      if (new_fd > 0) {
        addStream(new_fd);
      }
      //      } while (new_fd > 0);
      return;
    }
    case ACCEPT:
      break;
    case DISCONNECT: {
      auto stream = streams_set[fd];
      if (stream == nullptr) {
        Logger::LogInfo("Stream doesn't exist for " + std::to_string(fd));
        deleteFd(fd);
        ::close(fd);
        return;
      }
      /*      streams_set.erase(fd);
      delete stream*/
      ;
      clearStream(stream);
      break;
    }
  }
}
#else
void StreamManager::HandleEvent(int fd, EVENT_TYPE event_type,
                                EVENT_GROUP event_group) {
  switch (event_type) {
#if SM_HANDLE_ACCEPT
    case EVENT_TYPE::CONNECT: {
      DEBUG_COUNTER_HIT(debug__::event_connect);
      auto spt = service_manager_set[fd].lock();
      if (!spt) {
        deleteFd(fd);  // remove listener from epoll manager.
        ::close(fd);   // we close the listening socket
        return;
      }
      int new_fd;
#ifndef EPOLLEXCLUSIVE
      do {
#endif
        new_fd = Connection::doAccept(fd);
        if (new_fd > 0) {
          addStream(new_fd, std::move(spt));
        } else {
          DEBUG_COUNTER_HIT(debug__::event_connect_fail);
        }
#ifndef EPOLLEXCLUSIVE
      } while (new_fd > 0);
#endif
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
      auto stream = streams_set[fd];
      if (stream == nullptr) {
        switch (event_group) {
          case EVENT_GROUP::ACCEPTOR:
            break;
          case EVENT_GROUP::SERVER:
            Logger::LogInfo("SERVER_WRITE : Stream doesn't exist for " +
                           std::to_string(fd));
            break;
          case EVENT_GROUP::CLIENT:
            Logger::LogInfo("CLIENT_WRITE : Stream doesn't exist for " +
                           std::to_string(fd));
            break;
          default:
            break;
        }
        deleteFd(fd);
        ::close(fd);
        return;
      }

      switch (event_group) {
        case EVENT_GROUP::ACCEPTOR:
          break;
        case EVENT_GROUP::SERVER: {
          DEBUG_COUNTER_HIT(debug__::event_backend_write);
          onServerWriteEvent(stream);
          break;
        }
        case EVENT_GROUP::CLIENT: {
          DEBUG_COUNTER_HIT(debug__::event_client_write);
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
      auto stream = streams_set[fd];
      if (stream == nullptr) {
        char addr[150];
        Network::getPeerAddress(fd, addr, 150);
        Logger::logmsg(LOG_DEBUG,
                       "Remote host %s closed connection prematurely ", addr);
        deleteFd(fd);
        ::close(fd);
        return;
      }
      switch (event_group) {
        case EVENT_GROUP::SERVER: {
          onServerDisconnect(stream);
          return;
        }
        case EVENT_GROUP::CLIENT: {
          onClientDisconnect(stream);
          return;
        }
        default:
          Logger::LogInfo("Why this happens!!", LOG_DEBUG);
          break;
      }
      clearStream(stream);
      break;
    }
    default:
      Logger::LogInfo("Unexpected  event type", LOG_DEBUG);
      deleteFd(fd);
      ::close(fd);
  }
}
#endif

void StreamManager::stop() { is_running = false; }

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
  for (auto& key_pair : streams_set) {
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
  HttpStream *stream = streams_set[fd];

  if (UNLIKELY(stream != nullptr)) {
    clearStream(stream);
  }
  stream = new HttpStream();
  stream->client_connection.setFileDescriptor(fd);
  stream->service_manager = std::move(service_manager);  // TODO::benchmark!!
  streams_set[fd] = stream;
  auto& listener_config = *stream->service_manager->listener_config_;
  // update log info
  StreamDataLogger logger(stream, listener_config);

  stream->timer_fd.set(listener_config.to * 1000);
  addFd(stream->timer_fd.getFileDescriptor(), EVENT_TYPE::TIMEOUT,
        EVENT_GROUP::REQUEST_TIMEOUT);
  timers_set[stream->timer_fd.getFileDescriptor()] = stream;
  stream->client_connection.enableEvents(this, EVENT_TYPE::READ,
                                         EVENT_GROUP::CLIENT);

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
  HttpStream* stream = streams_set[fd];

  if (stream != nullptr) {
    if (stream->client_connection.isCancelled()) {
      clearStream(stream);
      return;
    }
    if (UNLIKELY(fd != stream->client_connection.getFileDescriptor())) {
      Logger::LogInfo("stream connection data inconsistency detected",
                      LOG_DEBUG);
      clearStream(stream);
      return;
    }
  } else {
#if !SM_HANDLE_ACCEPT
    stream = new HttpStream();
    stream->client_connection.setFileDescriptor(fd);
    streams_set[fd] = stream;
    if (fd != stream->client_connection.getFileDescriptor()) {
      Logger::LogInfo("stream connection data inconsistency detected",
                      LOG_DEBUG);
      clearStream(stream);
      return;
    }
#endif
    deleteFd(fd);
    ::close(fd);
    return;
  }
  auto& listener_config_ = *stream->service_manager->listener_config_;
  // update log info
  StreamDataLogger logger(stream, listener_config_);

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
        }
      }
      return;
    }
    case IO::IO_RESULT::SUCCESS:
    case IO::IO_RESULT::DONE_TRY_AGAIN:
    case IO::IO_RESULT::FULL_BUFFER:
      break;
    case IO::IO_RESULT::ZERO_DATA:
      return;
    case IO::IO_RESULT::FD_CLOSED:
      return;
    case IO::IO_RESULT::ERROR:
    case IO::IO_RESULT::CANCELLED:
    default: {
      Logger::LogInfo("Error reading request ", LOG_DEBUG);
      clearStream(stream);
      return;
    }
  }

  DEBUG_COUNTER_HIT(debug__::on_request);
  if (stream->upgrade.pinned_connection || stream->request.hasPendingData()) {
#if PRINT_DEBUG_FLOW_BUFFERS
    Logger::logmsg(
        LOG_REMOVE,
        "OUT buffer size: %8lu\tContent-length: %lu\tleft: %lu\tIO: %s",
        stream->client_connection.buffer_size, stream->request.content_length,
        stream->request.message_bytes_left, IO::getResultString(result).data());
#endif
    stream->backend_connection.enableWriteEvent();
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
      stream->client_connection.buffer, stream->client_connection.buffer_size,
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
        x_forwarded_for_header += stream->request.x_forwarded_for_string;
        x_forwarded_for_header += ", ";
      }
      x_forwarded_for_header += stream->client_connection.getPeerAddress();
      stream->request.addHeader(http::HTTP_HEADER_NAME::X_FORWARDED_FOR,
                                x_forwarded_for_header);
      stream->timer_fd.unset();
      deleteFd(stream->timer_fd.getFileDescriptor());
      timers_set[stream->timer_fd.getFileDescriptor()] = nullptr;
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

      stream->request.setService(service);
      // update log info
      logger.setLogData(stream, listener_config_);

#ifdef CACHE_ENABLED
      // If the cache is enabled and the request is cached and it is also fresh
      auto ret = CacheManager::handleRequest(stream, service,
                                             listener_config_set);
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
      auto bck =
          service->getBackend(stream->client_connection, stream->request);
      if (bck == nullptr) {
        // No backend available
        http_manager::replyError(
            http::Code::ServiceUnavailable,
            validation::request_result_reason.at(
                validation::REQUEST_RESULT::BACKEND_NOT_FOUND),
            listener_config_.err503, stream->client_connection);
        this->clearStream(stream);
        return;
      } else {
        // update log info
        StreamDataLogger::setLogData(stream, listener_config_);
        IO::IO_OP op_state = IO::IO_OP::OP_ERROR;
        static size_t total_request;
        total_request++;
        stream->response.reset_parser();
        stream->backend_connection.buffer_offset = 0;
        stream->client_connection.buffer_offset = 0;
        stream->backend_connection.buffer_size = 0;
        Logger::logmsg(
            LOG_DEBUG, "%lu [%s] %.*s [%s (%d) -> %s (%d)]", total_request,
            service->name.c_str(), stream->request.http_message_length,
            stream->request.http_message,
            stream->client_connection.getPeerAddress().c_str(),
            stream->client_connection.getFileDescriptor(), bck->address.c_str(),
            stream->backend_connection.getFileDescriptor());
        switch (bck->backend_type) {
          case BACKEND_TYPE::REMOTE: {
            if (stream->backend_connection.getBackend() == nullptr ||
                !stream->backend_connection.isConnected()) {
              // null
              if (stream->backend_connection.getFileDescriptor() > 0) {  //

                deleteFd(stream->backend_connection
                             .getFileDescriptor());  // Client cannot
                // be connected to more
                // than one backend at
                // time
                streams_set.erase(
                    stream->backend_connection.getFileDescriptor());
                stream->backend_connection.closeConnection();
                if (stream->backend_connection.isConnected())
                  stream->backend_connection.getBackend()->decreaseConnection();
              }
              stream->backend_connection.setBackend(bck);
              stream->backend_connection.time_start =
                  std::chrono::steady_clock::now();
              op_state = stream->backend_connection.doConnect(
                  *bck->address_info, bck->conn_timeout);
              switch (op_state) {
                case IO::IO_OP::OP_ERROR: {
                  Logger::logmsg(LOG_NOTICE, "Error connecting to backend %s",
                                bck->address.data());
                  http_manager::replyError(
                      http::Code::ServiceUnavailable,
                      http::reasonPhrase(http::Code::ServiceUnavailable),
                      listener_config_.err503, stream->client_connection);
                  stream->backend_connection.getBackend()->status =
                      BACKEND_STATUS::BACKEND_DOWN;
                  stream->backend_connection.closeConnection();
                  clearStream(stream);
                  return;
                }

                case IO::IO_OP::OP_IN_PROGRESS: {
                  stream->timer_fd.set(bck->conn_timeout * 1000);
                  stream->backend_connection.getBackend()
                      ->increaseConnTimeoutAlive();
                  timers_set[stream->timer_fd.getFileDescriptor()] = stream;
                  addFd(stream->timer_fd.getFileDescriptor(), EVENT_TYPE::READ,
                        EVENT_GROUP::CONNECT_TIMEOUT);
                  if (stream->backend_connection.getBackend()->nf_mark > 0)
                    Network::setSOMarkOption(
                        stream->backend_connection.getFileDescriptor(),
                        stream->backend_connection.getBackend()->nf_mark);
                }
                  [[fallthrough]];
                case IO::IO_OP::OP_SUCCESS: {
                  DEBUG_COUNTER_HIT(debug__::on_backend_connect);
                  stream->backend_connection.getBackend()->increaseConnection();
                  streams_set[stream->backend_connection.getFileDescriptor()] =
                      stream;
                  /*
                              if
                     (stream->backend_connection.getBackend()->backend_config.ctx
                     != nullptr)
                                ssl_manager->init(stream->backend_connection.getBackend()->backend_config);
                  */
                  stream->backend_connection.enableEvents(
                      this, EVENT_TYPE::WRITE, EVENT_GROUP::SERVER);
                  break;
                }
              }
            }

            // Rewrite destination
            if (stream->request.add_destination_header) {
              std::string header_value =
                  stream->backend_connection.getBackend()->isHttps()
                      ? "https://"
                      : "http://";
              header_value += stream->backend_connection.getPeerAddress();
              header_value += ':';
              header_value += stream->request.path;
              stream->request.addHeader(http::HTTP_HEADER_NAME::DESTINATION,
                                        header_value);
            }
            if (!stream->request.host_header_found) {
              std::string header_value = "";
              header_value += stream->backend_connection.getBackend()->address;
              header_value += ':';
              header_value +=
                  std::to_string(stream->backend_connection.getBackend()->port);
              stream->request.addHeader(http::HTTP_HEADER_NAME::HOST,
                                        header_value);
            }
            /* After setting the backend and the service in the first request,
             * pin the connection if the PinnedConnection service config
             * parameter is true. Note: The first request must be HTTP. */
            if (service->service_config.pinned_connection) {
              stream->upgrade.pinned_connection = true;
            }

            stream->backend_connection.enableWriteEvent();
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
      stream->client_connection.enableReadEvent();
      return;
  }

  /*if ((stream->client_connection.buffer_size - parsed) > 0) {
    Logger::LogInfo("Buffer size: left size: " +
        std::to_string(stream->client_connection.buffer_size),
                   LOG_DEBUG);
    Logger::LogInfo("Current request buffer: \n " +
        std::string(stream->client_connection.buffer,
                    stream->client_connection.buffer_size),
                   LOG_DEBUG);
    Logger::LogInfo("Parsed data size: " + std::to_string(parsed), LOG_DEBUG);
  }
*/
  //} while (stream->client_connection.buffer_size > parsed &&
  //  parse_result ==
  //     http_parser::PARSE_RESULT::SUCCESS);

  stream->client_connection.enableReadEvent();
}

void StreamManager::onResponseEvent(int fd) {
  HttpStream* stream = streams_set[fd];

  if (stream == nullptr) {
    Logger::LogInfo("Backend Connection, Stream closed", LOG_DEBUG);
    deleteFd(fd);
    ::close(fd);
    return;
  }
  auto& listener_config_ = *stream->service_manager->listener_config_;
  // update log info
  StreamDataLogger logger(stream, listener_config_);
  if (UNLIKELY(stream->client_connection.isCancelled() ||
               stream->backend_connection
                   .isCancelled())) {  // check if client is still active
    clearStream(stream);
    return;
  }
  if (stream->backend_connection.buffer_size == MAX_DATA_SIZE) {
    stream->client_connection.enableWriteEvent();
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
  // disable response timeout timerfd
  if (stream->backend_connection.getBackend()->response_timeout > 0) {
    stream->timer_fd.unset();
    events::EpollManager::deleteFd(stream->timer_fd.getFileDescriptor());
  }
  if (stream->backend_connection.buffer_size > 0 &&
      stream->response.getHeaderSent()) {
    stream->client_connection.enableWriteEvent();
    return;
  }
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
// TODO::Evaluar
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
    case IO::IO_RESULT::FD_CLOSED:
      if (stream->backend_connection.buffer_size > 0)
        break;
      else
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
  stream->backend_connection.getBackend()->calculateLatency(
      std::chrono::duration_cast<std::chrono::duration<double>>(
          std::chrono::steady_clock::now() -
          stream->backend_connection.time_start)
          .count());
  // TODO:  stream->backend_stadistics.update();

  if (stream->upgrade.pinned_connection || stream->response.hasPendingData()) {
#ifdef CACHE_ENABLED
    if (stream->response.chunked_status != CHUNKED_STATUS::CHUNKED_DISABLED) {
      auto pending_chunk_bytes = http_manager::handleChunkedData(*stream);
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
      case http_parser::PARSE_RESULT::SUCCESS:
        break;
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
        LOG_DEBUG, " %lu [%s] %.*s -> %.*s [%s (%d) <- %s (%d)]",
        total_responses,
        static_cast<Service*>(stream->request.getService())->name.c_str(),
        stream->response.http_message_length - 2, stream->response.http_message,
        stream->request.http_message_length - 2, stream->request.http_message,
        stream->client_connection.getPeerAddress().c_str(),
        stream->client_connection.getFileDescriptor(),
        stream->backend_connection.getBackend()->address.c_str(),
        stream->backend_connection.getFileDescriptor());

    stream->backend_connection.getBackend()->setAvgTransferTime(
        std::chrono::duration_cast<std::chrono::duration<double>>(
            std::chrono::steady_clock::now() -
            stream->backend_connection.time_start)
            .count());

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
  HttpStream* stream = timers_set[fd];
  if (stream == nullptr) {
    Logger::LogInfo("Stream null pointer", LOG_REMOVE);
    deleteFd(fd);
    ::close(fd);
    return;
  }
  auto& listener_config_ = *stream->service_manager->listener_config_;
  // update log info
  StreamDataLogger logger(stream, listener_config_);
  if (stream->timer_fd.isTriggered()) {
    stream->backend_connection.getBackend()->status =
        BACKEND_STATUS::BACKEND_DOWN;
    Logger::logmsg(LOG_NOTICE, "(%lx) backend %s connection timeout after %d",
                   /*std::this_thread::get_id()*/ pthread_self(),
                   stream->backend_connection.getBackend()->address.c_str(),
                   stream->backend_connection.getBackend()->conn_timeout);
    stream->backend_connection.getBackend()->decreaseConnTimeoutAlive();
    setStreamBackend(stream);
  }
}

void StreamManager::onRequestTimeoutEvent(int fd) {
  DEBUG_COUNTER_HIT(debug__::on_request_timeout);
  HttpStream* stream = timers_set[fd];
  if (stream == nullptr) {
    Logger::LogInfo("Stream null pointer", LOG_REMOVE);
    deleteFd(fd);
    ::close(fd);
    return;
  }
  auto& listener_config_ = *stream->service_manager->listener_config_;
  // update log info
  StreamDataLogger logger(stream, listener_config_);
  if (stream->timer_fd.isTriggered()) {
    clearStream(stream);
  }
}

void StreamManager::onResponseTimeoutEvent(int fd) {
  DEBUG_COUNTER_HIT(debug__::on_response_timeout);

  HttpStream* stream = timers_set[fd];

  if (stream == nullptr) {
    Logger::LogInfo("Stream null pointer", LOG_REMOVE);
    deleteFd(fd);
    ::close(fd);
  }
  auto& listener_config_ = *stream->service_manager->listener_config_;
  // update log info
  StreamDataLogger logger(stream, listener_config_);
  if (stream->timer_fd.isTriggered()) {
    char caddr[50];
    if (UNLIKELY(Network::getPeerAddress(
                     stream->client_connection.getFileDescriptor(), caddr,
                     50) == nullptr)) {
      Logger::LogInfo("Error getting peer address", LOG_DEBUG);
    } else {
      Logger::logmsg(LOG_NOTICE, "(%lx) e%d %s %s from %s",
                    std::this_thread::get_id(),
                    static_cast<int>(http::Code::GatewayTimeout),
                    validation::request_result_reason
                        .at(validation::REQUEST_RESULT::BACKEND_TIMEOUT)
                        .c_str(),
                    stream->client_connection.buffer, caddr);
    }
    http_manager::replyError(http::Code::GatewayTimeout,
                             http::reasonPhrase(http::Code::GatewayTimeout),
                             http::reasonPhrase(http::Code::GatewayTimeout),
                             stream->client_connection);
    this->clearStream(stream);
  }
}
void StreamManager::onSignalEvent([[maybe_unused]] int fd) {
  // TODO::IMPLEMENET
}

void StreamManager::setStreamBackend(HttpStream* stream) {
  auto service = static_cast<Service*>(stream->request.getService());
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
  if (stream->backend_connection.getBackend() != nullptr) {
    // remove previously added headers
    stream->request.removeHeader(http::HTTP_HEADER_NAME::DESTINATION);
    stream->request.removeHeader(http::HTTP_HEADER_NAME::HOST);
    // remove backend from stream_set
    if (stream->backend_connection.getFileDescriptor() > 0) {
      if (stream->backend_connection.isConnected())
        stream->backend_connection.getBackend()->decreaseConnection();
      streams_set[stream->backend_connection.getFileDescriptor()] = nullptr;
      streams_set.erase(stream->backend_connection.getFileDescriptor());
    }
    stream->backend_connection.reset();
    stream->backend_connection.setBackend(nullptr);
  }
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
        stream->backend_connection.time_start =
            std::chrono::steady_clock::now();
        op_state = stream->backend_connection.doConnect(*bck->address_info,
                                                        bck->conn_timeout);
        switch (op_state) {
          case IO::IO_OP::OP_ERROR: {
            Logger::logmsg(LOG_NOTICE, "Error connecting to backend %s",
                           bck->address.data());
            http_manager::replyError(
                http::Code::ServiceUnavailable,
                http::reasonPhrase(http::Code::ServiceUnavailable),
                listener_config_.err503, stream->client_connection);
            stream->backend_connection.getBackend()->status =
                BACKEND_STATUS::BACKEND_DOWN;
            stream->backend_connection.closeConnection();
            clearStream(stream);
            return;
          }

          case IO::IO_OP::OP_IN_PROGRESS: {
            stream->timer_fd.set(bck->conn_timeout * 1000);
            stream->backend_connection.getBackend()->increaseConnTimeoutAlive();
            timers_set[stream->timer_fd.getFileDescriptor()] = stream;
            addFd(stream->timer_fd.getFileDescriptor(), EVENT_TYPE::READ,
                  EVENT_GROUP::CONNECT_TIMEOUT);
            if (stream->backend_connection.getBackend()->nf_mark > 0)
              Network::setSOMarkOption(
                  stream->backend_connection.getFileDescriptor(),
                  stream->backend_connection.getBackend()->nf_mark);
          }
            [[fallthrough]];
          case IO::IO_OP::OP_SUCCESS: {
            DEBUG_COUNTER_HIT(debug__::on_backend_connect);
            stream->backend_connection.getBackend()->increaseConnection();
            streams_set[stream->backend_connection.getFileDescriptor()] =
                stream;
            stream->backend_connection.enableEvents(this, EVENT_TYPE::WRITE,
                                                    EVENT_GROUP::SERVER);
            break;
          }
        }

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
          stream->upgrade.pinned_connection = true;
        }

        stream->backend_connection.enableWriteEvent();
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
  auto& listener_config_ = *stream->service_manager->listener_config_;
  // update log info
  StreamDataLogger logger(stream, listener_config_);
  if (UNLIKELY(stream->backend_connection.isCancelled())) {
    clearStream(stream);
    return;
  }
  // StreamWatcher watcher(*stream);
  int fd = stream->backend_connection.getFileDescriptor();
  // Send client request to backend server
  if (stream->backend_connection.getBackend()->conn_timeout > 0 &&
      Network::isConnected(fd) && stream->timer_fd.is_set) {
    stream->timer_fd.unset();
    stream->backend_connection.getBackend()->decreaseConnTimeoutAlive();

    stream->backend_connection.getBackend()->setAvgConnTime(
        std::chrono::duration_cast<std::chrono::duration<double>>(
            std::chrono::steady_clock::now() -
            stream->backend_connection.time_start)
            .count());
    this->deleteFd(stream->timer_fd.getFileDescriptor());
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
  if (stream->upgrade.pinned_connection || stream->request.hasPendingData()) {
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
        if (!stream->backend_connection.ssl_connected) {
          stream->backend_connection.enableReadEvent();
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
    if (!stream->upgrade.pinned_connection) {
      if (stream->request.chunked_status ==
              http::CHUNKED_STATUS::CHUNKED_LAST_CHUNK &&
          stream->client_connection.buffer_size == 0) {
        stream->response.reset_parser();
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

  switch (result) {
    case IO::IO_RESULT::SSL_HANDSHAKE_ERROR:
    case IO::IO_RESULT::SSL_NEED_HANDSHAKE: {
      stream->backend_connection.server_name =
          stream->client_connection.server_name;
      if (!ssl::SSLConnectionManager::handleHandshake(
              stream->backend_connection.getBackend()->ctx.get(),
              stream->backend_connection, true)) {
        Logger::logmsg(LOG_DEBUG, "Handshake error with %s ",
                       stream->backend_connection.address_str.data());
        clearStream(stream);
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
      break;
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

  stream->timer_fd.set(
      stream->backend_connection.getBackend()->response_timeout * 1000);
  timers_set[stream->timer_fd.getFileDescriptor()] = stream;
  addFd(stream->timer_fd.getFileDescriptor(), EVENT_TYPE::READ,
        EVENT_GROUP::RESPONSE_TIMEOUT);
  stream->backend_connection.enableReadEvent();
  stream->backend_connection.time_start = std::chrono::steady_clock::now();
}

void StreamManager::onClientWriteEvent(HttpStream* stream) {
  DEBUG_COUNTER_HIT(debug__::on_send_response);
  auto& listener_config_ = *stream->service_manager->listener_config_;
  // update log info
  StreamDataLogger logger(stream, listener_config_);

  if (UNLIKELY(stream->client_connection.isCancelled())) {
    clearStream(stream);
    return;
  }

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
  if (stream->upgrade.pinned_connection || stream->response.hasPendingData()) {
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
        }
        return;
      }
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
    if (!stream->upgrade.pinned_connection) {
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
        stream->backend_connection.buffer_offset = 0;
        stream->backend_connection.enableReadEvent();
        stream->client_connection.enableReadEvent();
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
      break;
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
    stream->upgrade.pinned_connection = true;
    std::string upgrade_header_value;
    stream->request.getHeaderValue(http::HTTP_HEADER_NAME::UPGRADE,
                                   upgrade_header_value);
    auto it = http::http_info::upgrade_protocols.find(upgrade_header_value);
    if (it != http::http_info::upgrade_protocols.end())
      stream->upgrade.protocol = it->second;
  }

  if (stream->backend_connection.buffer_size > 0)
    stream->client_connection.enableWriteEvent();
  else {
#ifdef CACHE_ENABLED
    if (!stream->response.isCached())
#endif
      stream->backend_connection.enableReadEvent();
    stream->client_connection.enableReadEvent();
  }
}

bool StreamManager::registerListener(
    std::weak_ptr<ServiceManager> service_manager) {
  auto& listener_config = service_manager.lock()->listener_config_;
  auto address =
      Network::getAddress(listener_config->address, listener_config->port);
  int listen_fd = Connection::listen(*address);

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
#ifdef CACHE_ENABLED
  CacheManager::handleStreamClose(stream);
#endif
  // TODO:: add connection closing reason for logging purpose
  if (stream == nullptr) {
    return;
  }
  //  logSslErrorStack();

  if (stream->timer_fd.getFileDescriptor() > 0) {
    deleteFd(stream->timer_fd.getFileDescriptor());
    stream->timer_fd.unset();
    timers_set[stream->timer_fd.getFileDescriptor()] = nullptr;
    timers_set.erase(stream->timer_fd.getFileDescriptor());
  }
  if (stream->client_connection.getFileDescriptor() > 0) {
    //      if (this->is_https_listener &&
    //      stream->client_connection.isConnected()) { //FIXME
    //          ssl_manager->sslShutdown(stream->client_connection);
    //      }
    deleteFd(stream->client_connection.getFileDescriptor());
    streams_set[stream->client_connection.getFileDescriptor()] = nullptr;
    streams_set.erase(stream->client_connection.getFileDescriptor());

    DEBUG_COUNTER_HIT(debug__::on_client_disconnect);
  }
  if (stream->backend_connection.getFileDescriptor() > 0) {
    if (stream->backend_connection.isConnected()) {
      //          if (stream->backend_connection.getBackend()->isHttps()) {
      //          //FIXME
      //              ssl_manager->sslShutdown(stream->client_connection);
      //          }
      stream->backend_connection.getBackend()->decreaseConnection();
    }
    deleteFd(stream->backend_connection.getFileDescriptor());
    streams_set[stream->backend_connection.getFileDescriptor()] = nullptr;
    streams_set.erase(stream->backend_connection.getFileDescriptor());
    DEBUG_COUNTER_HIT(debug__::on_backend_disconnect);
  }
  delete stream;
}

void StreamManager::onClientDisconnect(HttpStream* stream) {
  DEBUG_COUNTER_HIT(debug__::event_client_disconnect);
  auto& listener_config_ = *stream->service_manager->listener_config_;
  // update log info
  StreamDataLogger logger(stream, listener_config_);
  Logger::logmsg(LOG_DEBUG, "fd: %d:%d Client closed connection",
                 stream->client_connection.getFileDescriptor(),
                 stream->backend_connection.getFileDescriptor());
  clearStream(stream);
}

std::string StreamManager::handleTask(ctl::CtlTask& task) {
  if (!isHandler(task)) return JSON_OP_RESULT::ERROR;

  if (task.command == ctl::CTL_COMMAND::EXIT) {
    Logger::logmsg(LOG_REMOVE, "Exit command received");
    is_running = false;
    return JSON_OP_RESULT::OK;
  }
  return JSON_OP_RESULT::ERROR;
}

bool StreamManager::isHandler(ctl::CtlTask& task) {
  return task.target == ctl::CTL_HANDLER_TYPE::ALL ||
         task.target == ctl::CTL_HANDLER_TYPE::STREAM_MANAGER;
}

void StreamManager::onServerDisconnect(HttpStream* stream) {
  DEBUG_COUNTER_HIT(debug__::event_backend_disconnect);
  if (stream == nullptr) {
    return;
  }
  auto& listener_config_ = *stream->service_manager->listener_config_;
  // update log info
  StreamDataLogger logger(stream, listener_config_);

  Logger::LogInfo("Backend closed connection", LOG_DEBUG);
  if (stream->backend_connection.buffer_size > 0
#if ENABLE_ZERO_COPY
      || stream->backend_connection.splice_pipe.bytes > 0
#endif
  ) {
    stream->backend_connection.disableEvents();
    stream->client_connection.enableWriteEvent();
    return;
  }
  if (!stream->backend_connection.isConnected() &&
      !stream->request.getHeaderSent()) {
    Logger::logmsg(
        LOG_NOTICE,
        "(%lx) BackEnd %s:%d dead (killed) in farm: '%s', service: '%s'",
        pthread_self(), stream->backend_connection.getBackend()->address.data(),
        stream->backend_connection.getBackend()->port,
        listener_config_.name.data(),
        stream->backend_connection.getBackend()
            ->backend_config->srv_name.data());
    stream->backend_connection.getBackend()->status =
        BACKEND_STATUS::BACKEND_DOWN;
    stream->backend_connection.getBackend()->decreaseConnTimeoutAlive();
    setStreamBackend(stream);
    return;
  } else if (!stream->request.getHeaderSent()) {
    http_manager::replyError(http::Code::ServiceUnavailable,
                             validation::request_result_reason.at(
                                 validation::REQUEST_RESULT::SERVICE_NOT_FOUND),
                             listener_config_.err503,
                             stream->client_connection);
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
    for (auto it = streams_set.begin(); it != streams_set.end();) {
      if (it->second->service_manager->id == listener_id) {
        auto item = it++;
        clearStream(item->second);
      } else
        it++;
    }
  }
}
