//
// Created by abdess on 4/5/18.
//

#include "StreamManager.h"
#include "../util/Network.h"
#include "../util/common.h"
#include "../util/string_view.h"
#include "../util/utils.h"
#include "../util/zlib_util.h"
#include <cstdio>
#include <functional>
#if HELLO_WORLD_SERVER
void StreamManager::HandleEvent(int fd, EVENT_TYPE event_type,
                                EVENT_GROUP event_group) {
  switch (event_type) {
  case READ_ONESHOT: {
    HttpStream *stream = streams_set[fd];
    if (stream == nullptr) {
      stream = new HttpStream();
      stream->client_connection.setFileDescriptor(fd);
      streams_set[fd] = stream;
    }
    auto connection = stream->getConnection(fd);
    connection->read();
    connection->buffer_size = 1; // reset buffer size to avoid buffer
                                 // overflow due to not consuming buffer
                                 // data.
    updateFd(fd, EVENT_TYPE::WRITE, EVENT_GROUP::CLIENT);
    break;
  }

  case READ: {
    HttpStream *stream = streams_set[fd];
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
      Debug::LogInfo("Connection closed prematurely" + std::to_string(fd));
      return;
    }
    auto io_result = stream->client_connection.write(this->e200.c_str(),
                                                     this->e200.length());
    switch (io_result) {
    case IO::ERROR:
    case IO::FD_CLOSED:
    case IO::FULL_BUFFER:
      Debug::LogInfo("Something happend sentid e200", LOG_DEBUG);
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
      Debug::LogInfo("Stream doesn't exist for " + std::to_string(fd));
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
#endif
  case READ:
  case READ_ONESHOT: {
    switch (event_group) {
    case EVENT_GROUP::ACCEPTOR:break;
    case EVENT_GROUP::SERVER:onResponseEvent(fd);
      break;
    case EVENT_GROUP::CLIENT:onRequestEvent(fd);
      break;
    case EVENT_GROUP::CONNECT_TIMEOUT:onConnectTimeoutEvent(fd);
      break;
    case EVENT_GROUP::REQUEST_TIMEOUT:onRequestTimeoutEvent(fd);
      break;
    case EVENT_GROUP::RESPONSE_TIMEOUT:onResponseTimeoutEvent(fd);
      break;
    case EVENT_GROUP::SIGNAL:onSignalEvent(fd);
      break;
    case EVENT_GROUP::MAINTENANCE:break;
    default:deleteFd(fd);
      close(fd);
      break;
    }
    return;
  }
  case WRITE: {
    auto stream = streams_set[fd];
    if (stream == nullptr) {
      switch (event_group) {
      case EVENT_GROUP::ACCEPTOR:break;
      case EVENT_GROUP::SERVER:
        Debug::LogInfo("SERVER_WRITE : Stream doesn't exist for " +
            std::to_string(fd));
        break;
      case EVENT_GROUP::CLIENT:
        Debug::LogInfo("CLIENT_WRITE : Stream doesn't exist for " +
            std::to_string(fd));
        break;
      default: break;
      }
      deleteFd(fd);
      ::close(fd);
      return;
    }

    switch (event_group) {
    case EVENT_GROUP::ACCEPTOR:break;
    case EVENT_GROUP::SERVER: {
      onServerWriteEvent(stream);
      break;
    }
    case EVENT_GROUP::CLIENT: {
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
  case DISCONNECT: {
    auto stream = streams_set[fd];
    if (stream == nullptr) {
      Debug::LogInfo("Remote host closed connection prematurely ", LOG_INFO);
      deleteFd(fd);
      ::close(fd);
      return;
    }
    switch (event_group) {
    case EVENT_GROUP::SERVER: {
      if (!stream->backend_connection.isConnected()) {
        auto response =
            HttpStatus::getHttpResponse(HttpStatus::Code::RequestTimeout);
        stream->client_connection.write(response.c_str(), response.length());
        Debug::LogInfo("Backend closed connection", LOG_DEBUG);
      }
      break;
    }
    case EVENT_GROUP::CLIENT: {
      Debug::LogInfo("Client closed connection", LOG_DEBUG);
      break;
    }
    default:Debug::LogInfo("Why this happends!!", LOG_DEBUG);
      break;
    }
    clearStream(stream);
    break;
  }
  default:Debug::LogInfo("Unexpected  event type", LOG_DEBUG);
    deleteFd(fd);
    ::close(fd);
  }
}
#endif

void StreamManager::stop() { is_running = false; }

void StreamManager::start(int thread_id_) {
  is_running = true;
  worker_id = thread_id_;
  this->worker = std::thread([this] { doWork(); });
  if (worker_id >= 0) {
    //    helper::ThreadHelper::setThreadAffinity(worker_id,
    //    worker.native_handle());
    helper::ThreadHelper::setThreadName("WORKER_" + std::to_string(worker_id),
                                        worker.native_handle());
  }
#if SM_HANDLE_ACCEPT
  handleAccept(listener_connection.getFileDescriptor());
#endif
}

StreamManager::StreamManager() : is_https_listener(false) {
  // TODO:: do attach for config changes
};

StreamManager::~StreamManager() {
  stop();
  if (worker.joinable())
    worker.join();
  for (auto &key_pair : streams_set) {
    delete key_pair.second;
  }
}
void StreamManager::doWork() {
  while (is_running) {
    if (loopOnce() <= 0) {
      // something bad happend
      //      Debug::LogInfo("No events !!");
    }
    // if(needMainatance)
    //    doMaintenance();
  }
}

void StreamManager::addStream(int fd) {
#if SM_HANDLE_ACCEPT
  HttpStream *stream = streams_set[fd];
  if (UNLIKELY(stream != nullptr)) {
    clearStream(stream);
  }
  stream = new HttpStream();
  stream->client_connection.setFileDescriptor(fd);
  streams_set[fd] = stream;
  stream->timer_fd.set(listener_config_.to * 1000);
  addFd(stream->timer_fd.getFileDescriptor(), TIMEOUT,
        EVENT_GROUP::REQUEST_TIMEOUT);
  timers_set[stream->timer_fd.getFileDescriptor()] = stream;
  stream->client_connection.enableEvents(this, READ, EVENT_GROUP::CLIENT);
  // set extra header to forward to the backends
  stream->request.addHeader(http::HTTP_HEADER_NAME::X_FORWARDED_FOR,
                            stream->client_connection.getPeerAddress(), true);
  if (listener_config_.add_head != NULL) {
    stream->request.addHeader(listener_config_.add_head, true);
  }
  // configurar
#else
  if (!this->addFd(fd, READ, EVENT_GROUP::CLIENT)) {
    Debug::LogInfo("Error adding to epoll manager", LOG_NOTICE);
  }
#endif
}

int StreamManager::getWorkerId() { return worker_id; }

void StreamManager::onRequestEvent(int fd) {
  HttpStream *stream = streams_set[fd];
  if (stream != nullptr) {
    if (stream->client_connection.isCancelled()) {
      clearStream(stream);
      return;
    }
    if (UNLIKELY(fd != stream->client_connection.getFileDescriptor())) {
      Debug::LogInfo("FOUND:: Aqui ha pasado algo raro!!", LOG_REMOVE);
    }
  } else {
    stream = new HttpStream();
    stream->client_connection.setFileDescriptor(fd);
    streams_set[fd] = stream;
    if (fd != stream->client_connection.getFileDescriptor()) {
      Debug::LogInfo("FOUND:: Aqui ha pasado algo raro!!", LOG_DEBUG);
    }
  }
  IO::IO_RESULT result = IO::IO_RESULT::ERROR;
  if (this->is_https_listener) {
    result = this->ssl_manager->handleDataRead(stream->client_connection);

  } else {
    result = stream->client_connection.read();
  }
  switch (result) {
  case IO::IO_RESULT::SSL_HANDSHAKE_ERROR:
  case IO::IO_RESULT::SSL_NEED_HANDSHAKE: {

    if (!this->ssl_manager->handleHandshake(stream->client_connection)) {
      if ((ERR_GET_REASON(ERR_peek_error()) == SSL_R_HTTP_REQUEST)
          && (ERR_GET_LIB(ERR_peek_error()) == ERR_LIB_SSL)) {
        /* the client speaks plain HTTP on our HTTPS port */
        Debug::logmsg(LOG_NOTICE,
                      "Client %s sent a plain HTTP message to an SSL port",
                      stream->client_connection.getPeerAddress().c_str());
        if (listener_config_.nossl_redir > 0) {
          Debug::logmsg(LOG_NOTICE, "(%lx) errNoSsl from %s redirecting to \"%s\"", pthread_self(),
                        stream->client_connection.getPeerAddress().c_str(), listener_config_.nossl_url);
          stream->replyRedirect(listener_config_.nossl_redir, listener_config_.nossl_url);
        } else {
          Debug::logmsg(LOG_NOTICE, "(%lx) errNoSsl from %s sending error",
                        pthread_self(), stream->client_connection.getPeerAddress().c_str());
          stream->replyError(HttpStatus::Code::BadRequest,
                             HttpStatus::reasonPhrase(HttpStatus::Code::BadRequest).c_str(),
                             listener_config_.errnossl);
        }
      } else {
        Debug::logmsg(LOG_INFO, "Handshake error with %s ",
                      stream->client_connection.getPeerAddress().c_str());
      }
      clearStream(stream);
    }

    return;
  }
  case IO::IO_RESULT::SUCCESS:break;
  case IO::IO_RESULT::DONE_TRY_AGAIN:break;
  case IO::IO_RESULT::FULL_BUFFER:break;
  case IO::IO_RESULT::ZERO_DATA: return;
  case IO::IO_RESULT::FD_CLOSED:return; //wait for EPOLLRDHUP
  case IO::IO_RESULT::ERROR:
  case IO::IO_RESULT::CANCELLED:
  default: {
    Debug::LogInfo("Error reading request ", LOG_DEBUG);
    clearStream(stream);
    return;
  }
  }

  if (stream->upgrade.pinned_connection) {
    stream->backend_connection.enableWriteEvent();
    return;
  }

  /* Check if chunked transfer encoding is enabled. */
  if (transferChunked(stream)) {
    stream->backend_connection.enableWriteEvent();
    return;
  }

  size_t parsed = 0;
  http_parser::PARSE_RESULT parse_result;
  // do {
  parse_result = stream->request.parseRequest(
      stream->client_connection.buffer, stream->client_connection.buffer_size,
      &parsed); // parsing http data as response structured

  switch (parse_result) {
  case http_parser::PARSE_RESULT::SUCCESS: {
    auto valid = validateRequest(stream->request);
    if (UNLIKELY(validation::REQUEST_RESULT::OK != valid)) {
      stream->replyError(HttpStatus::Code::NotImplemented,
                         validation::request_result_reason.at(valid).c_str(),
                         listener_config_.err501);
      this->clearStream(stream);
      return;
    }
    stream->timer_fd.unset();
    deleteFd(stream->timer_fd.getFileDescriptor());
    timers_set[stream->timer_fd.getFileDescriptor()] = nullptr;
    auto service = service_manager->getService(stream->request);
    if (service == nullptr) {
      stream->replyError(HttpStatus::Code::ServiceUnavailable,
                         validation::request_result_reason
                             .at(validation::REQUEST_RESULT::SERVICE_NOT_FOUND)
                             .c_str(),
                         listener_config_.err503);
      this->clearStream(stream);
      return;
    }
    auto bck = service->getBackend(*stream);
    if (bck == nullptr) {
      // No backend available
      stream->replyError(HttpStatus::Code::ServiceUnavailable,
                         validation::request_result_reason
                             .at(validation::REQUEST_RESULT::BACKEND_NOT_FOUND)
                             .c_str(),
                         listener_config_.err503);
      this->clearStream(stream);
      return;
    } else {
      IO::IO_OP op_state = IO::IO_OP::OP_ERROR;
      Debug::logmsg(LOG_DEBUG, "[%s] %s (%.*s) -> %s", service->name.c_str(),
                    stream->client_connection.getPeerAddress().c_str(),
                    stream->request.getRequestLine().length() - 2,
                    stream->request.getRequestLine().c_str(),
                    bck->address.c_str());
      switch (bck->backend_type) {
      case BACKEND_TYPE::REMOTE: {
        if (stream->backend_connection.getBackend() == nullptr ||
            !stream->backend_connection.isConnected()) {
          // null
          if (stream->backend_connection.getFileDescriptor() > 0) { //

            deleteFd(stream->backend_connection
                         .getFileDescriptor()); // Client cannot
            // be connected to more
            // than one backend at
            // time
            streams_set.erase(stream->backend_connection.getFileDescriptor());
            stream->backend_connection.closeConnection();
            if (stream->backend_connection.isConnected())
              stream->backend_connection.getBackend()->decreaseConnection();
          }
          stream->backend_connection.setBackend(bck);
          stream->backend_connection.time_start =
              std::chrono::steady_clock::now();
          op_state = stream->backend_connection.doConnect(*bck->address_info,
                                                          bck->conn_timeout);
          switch (op_state) {
          case IO::IO_OP::OP_ERROR: {
            auto response = HttpStatus::getHttpResponse(
                HttpStatus::Code::ServiceUnavailable);
            stream->client_connection.write(response.c_str(),
                                            response.length());
            Debug::LogInfo("Error connecting to backend " + bck->address,
                           LOG_NOTICE);

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
              Network::setSOMarkOption(stream->backend_connection.getFileDescriptor(),
                                       stream->backend_connection.getBackend()->nf_mark);
          }
          case IO::IO_OP::OP_SUCCESS: {
            stream->backend_connection.getBackend()->increaseConnection();
            streams_set[stream->backend_connection.getFileDescriptor()] =
                stream;
            stream->backend_connection.enableEvents(this, EVENT_TYPE::WRITE,
                                                    EVENT_GROUP::SERVER);
            break;
          }
          }
        }

        // Rewrite destination
        if (stream->request.add_destination_header) {
          std::string destination_value;
          std::string header_value = "http://";
          header_value += stream->backend_connection.getPeerAddress();
          header_value += ':';
          header_value += stream->request.path;
          stream->request.addHeader(http::HTTP_HEADER_NAME::DESTINATION,
                                    header_value);
        }

        /* After setting the backend and the service in the first request,
         * pin the connection if the PinnedConnection service config parameter
         * is true. Note: The first request must be HTTP. */
        if (service->service_config.pinned_connection) {
          stream->upgrade.pinned_connection = true;
        }

        stream->backend_connection.enableWriteEvent();
        break;
      }
      case BACKEND_TYPE::EMERGENCY_SERVER:

        break;
      case BACKEND_TYPE::REDIRECT: {
        /*Check redirect request type ::> 0 - redirect is absolute, 1 -
         * the redirect should include the request path, or 2 if it should
         * use perl dynamic replacement */
        //              switch (bck->backend_config.redir_req) {
        //                case 1:
        //
        //                  break;
        //                case 2: break;
        //                case 0:
        //                default: break;
        //              }
        stream->replyRedirect(bck->backend_config);
        clearStream(stream);
        return;
      }
      case BACKEND_TYPE::CACHE_SYSTEM:break;
      }
    }
    break;
  }
  case http_parser::PARSE_RESULT::TOOLONG:Debug::LogInfo("Parser TOOLONG", LOG_DEBUG);
  case http_parser::PARSE_RESULT::FAILED:
    stream->replyError(
        HttpStatus::Code::BadRequest,
        HttpStatus::reasonPhrase(HttpStatus::Code::BadRequest).c_str(),
        listener_config_.err501);
    this->clearStream(stream);
    return;
  case http_parser::PARSE_RESULT::INCOMPLETE:Debug::LogInfo("Parser INCOMPLETE", LOG_DEBUG);
    stream->client_connection.enableReadEvent();
    return;
  }

  /*if ((stream->client_connection.buffer_size - parsed) > 0) {
    Debug::LogInfo("Buffer size: left size: " +
        std::to_string(stream->client_connection.buffer_size),
                   LOG_DEBUG);
    Debug::LogInfo("Current request buffer: \n " +
        std::string(stream->client_connection.buffer,
                    stream->client_connection.buffer_size),
                   LOG_DEBUG);
    Debug::LogInfo("Parsed data size: " + std::to_string(parsed), LOG_DEBUG);
  }
*/
  //} while (stream->client_connection.buffer_size > parsed &&
  //  parse_result ==
  //     http_parser::PARSE_RESULT::SUCCESS);

  stream->client_connection.enableReadEvent();
}

void StreamManager::onResponseEvent(int fd) {
  HttpStream *stream = streams_set[fd];
  if (stream == nullptr) {
    Debug::LogInfo("Backend Connection, Stream closed", LOG_DEBUG);
    deleteFd(fd);
    ::close(fd);
    return;
  }
  if (UNLIKELY(stream->backend_connection.isCancelled())) {
    clearStream(stream);
    return;
  }
  if (stream->backend_connection.getBackend()->response_timeout > 0) {
    stream->timer_fd.unset();
    events::EpollManager::deleteFd(stream->timer_fd.getFileDescriptor());
  }
  IO::IO_RESULT result;
  if (stream->response.message_bytes_left > 0 && !this->is_https_listener
      && stream->response.transfer_encoding_header) {
    result = stream->backend_connection.zeroRead();
    if (result == IO::IO_RESULT::ERROR) {
      Debug::LogInfo("Error reading response ", LOG_DEBUG);
      clearStream(stream);
      return;
    }
    // TODO::Evaluar
#ifdef ENABLE_QUICK_RESPONSE
    result = stream->backend_connection.zeroWrite(
        stream->client_connection.getFileDescriptor(), stream->response);
    switch (result) {
    case IO::IO_RESULT::FD_CLOSED:
    case IO::IO_RESULT::ERROR: {
      Debug::LogInfo("Error Writing response ", LOG_NOTICE);
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
  } else {
    result = stream->backend_connection.read();
    switch (result) {
    case IO::IO_RESULT::SSL_HANDSHAKE_ERROR:
    case IO::IO_RESULT::SSL_NEED_HANDSHAKE: {
      if (!this->ssl_manager->handleHandshake(stream->client_connection)) {
        Debug::logmsg(LOG_INFO, "Backend handshake error with %s ",
                      stream->client_connection.getPeerAddress().c_str());
        clearStream(stream);
      }
      return;
    }
    case IO::IO_RESULT::SUCCESS:break;
    case IO::IO_RESULT::DONE_TRY_AGAIN:break;
    case IO::IO_RESULT::FULL_BUFFER:Debug::logmsg(LOG_DEBUG, "Backend buffer full");
      break;
    case IO::IO_RESULT::ZERO_DATA: return;
    case IO::IO_RESULT::FD_CLOSED: return; //wait for EPOLLRDHUP
    case IO::IO_RESULT::ERROR:
    case IO::IO_RESULT::CANCELLED:
    default: {
      Debug::LogInfo("Error reading response ", LOG_DEBUG);
      clearStream(stream);
      return;
    }
    }
    // TODO::FERNANDO::REPASAR, toma de muestras de tiempo, solo se debe de
    // tomar muestra si se la lectura ha sido success.
    stream->backend_connection.getBackend()->calculateLatency(
        std::chrono::duration_cast<std::chrono::duration<double>>(
            std::chrono::steady_clock::now() -
                stream->backend_connection.time_start)
            .count());
    //  stream->backend_stadistics.update();

    if (stream->upgrade.pinned_connection) {
      stream->client_connection.enableWriteEvent();
      return;
    }

    size_t parsed = 0;
    if (stream->response.message_bytes_left < 1) {
      auto ret = stream->response.parseResponse(
          stream->backend_connection.buffer,
          stream->backend_connection.buffer_size,
          &parsed); // parsing http data as response structured
      //    Debug::logmsg(
      //        LOG_REMOVE,
      //        "PARSE buffer_size: %d bytes left: %d current_message_size=%d",
      //        stream->backend_connection.buffer_size,
      //        stream->response.message_bytes_left,
      //        stream->response.message_length);
      // get content-lengt
    }

    stream->backend_connection.getBackend()->setAvgTransferTime(
        std::chrono::duration_cast<std::chrono::duration<double>>(
            std::chrono::steady_clock::now() -
                stream->backend_connection.time_start)
            .count());

    if (validateResponse(*stream) != validation::REQUEST_RESULT::OK) {
      Debug::logmsg(LOG_NOTICE,
                    "(%lx) backend %s response validation error\n %.*s",
                    std::this_thread::get_id(),
                    stream->backend_connection.getBackend()->address.c_str(),
                    stream->backend_connection.buffer_size,
                    stream->backend_connection.buffer);
      stream->replyError(
          HttpStatus::Code::ServiceUnavailable,
          HttpStatus::reasonPhrase(HttpStatus::Code::ServiceUnavailable)
              .c_str(),
          listener_config_.err503);
      this->clearStream(stream);
      return;
    }

    Service *service = service_manager->getService(stream->request); // FIXME:: Do not loop!!
    setBackendCookie(service, stream);
    setStrictTransportSecurity(service, stream);
    applyCompression(service, stream);
  }
  stream->client_connection.enableWriteEvent();
}
void StreamManager::onConnectTimeoutEvent(int fd) {
  HttpStream *stream = timers_set[fd];
  if (stream == nullptr) {
    Debug::LogInfo("Stream null pointer", LOG_REMOVE);
    deleteFd(fd);
    ::close(fd);
  } else if (stream->timer_fd.isTriggered()) {
    stream->backend_connection.getBackend()->status =
        BACKEND_STATUS::BACKEND_DOWN;
    Debug::logmsg(LOG_NOTICE, "(%lx) backend %s connection timeout after %d",
                  std::this_thread::get_id(),
                  stream->backend_connection.getBackend()->address.c_str(),
                  stream->backend_connection.getBackend()->conn_timeout);
    stream->replyError(
        HttpStatus::Code::ServiceUnavailable,
        HttpStatus::reasonPhrase(HttpStatus::Code::ServiceUnavailable).c_str(),
        listener_config_.err503);
    this->clearStream(stream);
  }
}

void StreamManager::onRequestTimeoutEvent(int fd) {
  HttpStream *stream = timers_set[fd];
  if (stream == nullptr) {
    Debug::LogInfo("Stream null pointer", LOG_REMOVE);
    deleteFd(fd);
    ::close(fd);
  } else if (stream->timer_fd.isTriggered()) {
    clearStream(stream); //FIXME::
  }
}

void StreamManager::onResponseTimeoutEvent(int fd) {
  HttpStream *stream = timers_set[fd];
  if (stream == nullptr) {
    Debug::LogInfo("Stream null pointer", LOG_REMOVE);
    deleteFd(fd);
    ::close(fd);
  } else if (stream->timer_fd.isTriggered()) {
    char caddr[50];
    if (UNLIKELY(Network::getPeerAddress(
        stream->client_connection.getFileDescriptor(), caddr,
        50) == nullptr)) {
      Debug::LogInfo("Error getting peer address", LOG_DEBUG);
    } else {
      Debug::logmsg(LOG_NOTICE, "(%lx) e%d %s %s from %s",
                    std::this_thread::get_id(),
                    static_cast<int>(HttpStatus::Code::GatewayTimeout),
                    validation::request_result_reason
                        .at(validation::REQUEST_RESULT::BACKEND_TIMEOUT)
                        .c_str(),
                    stream->client_connection.buffer, caddr);
    }
    stream->replyError(
        HttpStatus::Code::GatewayTimeout,
        HttpStatus::reasonPhrase(HttpStatus::Code::GatewayTimeout).c_str(),
        HttpStatus::reasonPhrase(HttpStatus::Code::GatewayTimeout).c_str());
    this->clearStream(stream);
  }
}
void StreamManager::onSignalEvent(int fd) {
  // TODO::IMPLEMENET
}

void StreamManager::onServerWriteEvent(HttpStream *stream) {
  if (UNLIKELY(stream->backend_connection.isCancelled())) {
    clearStream(stream);
    return;
  }
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
    events::EpollManager::deleteFd(stream->timer_fd.getFileDescriptor());
  }

  /* If the connection is pinned, then we need to write the buffer
   * content without applying any kind of modification. */
  if (stream->upgrade.pinned_connection) {
    stream->client_connection.writeTo(stream->backend_connection.getFileDescriptor());
    stream->client_connection.enableReadEvent();
    stream->backend_connection.enableReadEvent();
    return;
  }

  IO::IO_RESULT result;
  /* Check if chunked transfer encoding is enabled. */
  if (stream->chunked_status != http::CHUNKED_STATUS::CHUNKED_DISABLED) {
    stream->chunked_status = stream->chunked_status == http::CHUNKED_STATUS::CHUNKED_LAST_CHUNK ?
                             http::CHUNKED_STATUS::CHUNKED_DISABLED :
                             http::CHUNKED_STATUS::CHUNKED_ENABLED;

    result = stream->backend_connection.write(stream->client_connection.buffer, stream->client_connection.buffer_size);
    /* We need to indicate that all the buffer content has been written. */
    stream->client_connection.buffer_size = 0;
  } else {
    result = stream->client_connection.writeTo(stream->backend_connection, stream->request);
  }

  if (result == IO::IO_RESULT::SUCCESS) {
    stream->timer_fd.set(
        stream->backend_connection.getBackend()->response_timeout * 1000);
    timers_set[stream->timer_fd.getFileDescriptor()] = stream;
    addFd(stream->timer_fd.getFileDescriptor(), EVENT_TYPE::READ,
          EVENT_GROUP::RESPONSE_TIMEOUT);
    stream->backend_connection.enableReadEvent();
    stream->backend_connection.time_start = std::chrono::steady_clock::now();

  } else if (result == IO::IO_RESULT::DONE_TRY_AGAIN) {
    stream->backend_connection.enableWriteEvent();
  } else {
    Debug::LogInfo("Error sending data to client", LOG_DEBUG);
    clearStream(stream);
    return;
  }
}

void StreamManager::onClientWriteEvent(HttpStream *stream) {
  if (UNLIKELY(stream->client_connection.isCancelled())) {
    clearStream(stream);
    return;
  }

  IO::IO_RESULT result = IO::IO_RESULT::ERROR;
  /* If the connection is pinned, then we need to write the buffer
   * content without applying any kind of modification. */
  if (stream->upgrade.pinned_connection) {
    size_t written = 0;
    if (this->is_https_listener) {
      result = this->ssl_manager->handleWrite(
          stream->client_connection, stream->backend_connection.buffer,
          stream->backend_connection.buffer_size, written);

    } else {
      result = stream->backend_connection.writeTo(stream->client_connection.getFileDescriptor());
    }
    switch (result) {
    case IO::IO_RESULT::SSL_HANDSHAKE_ERROR:
    case IO::IO_RESULT::SSL_NEED_HANDSHAKE: {
      if (!this->ssl_manager->handleHandshake(stream->client_connection)) {
        Debug::logmsg(LOG_INFO, "Handshake error with %s ",
                      stream->client_connection.getPeerAddress().c_str());
        clearStream(stream);
      }
      return;
    }
    case IO::IO_RESULT::FD_CLOSED:
    case IO::IO_RESULT::CANCELLED:
    case IO::IO_RESULT::ERROR:Debug::LogInfo("Error reading request ", LOG_DEBUG);
      clearStream(stream);
      return;
    case IO::IO_RESULT::SUCCESS:
    case IO::IO_RESULT::DONE_TRY_AGAIN:
      if (this->is_https_listener)
        stream->backend_connection.buffer_size -= written;
    case IO::IO_RESULT::FULL_BUFFER:break;
    }

    stream->backend_connection.enableReadEvent();
    stream->client_connection.enableReadEvent();

    return;
  }

  if (stream->backend_connection.buffer_size > 0)
    if (this->is_https_listener) {
      result = ssl_manager->handleDataWrite(stream->client_connection, stream->backend_connection, stream->response);
    } else {
      result = stream->backend_connection.writeTo(stream->client_connection,
                                                  stream->response);
    }
  if (stream->backend_connection.splice_pipe.bytes > 0 )
    result = stream->backend_connection.zeroWrite(
        stream->client_connection.getFileDescriptor(), stream->response);

  switch (result) {
  case IO::IO_RESULT::SSL_HANDSHAKE_ERROR:
  case IO::IO_RESULT::SSL_NEED_HANDSHAKE: {
    if (!this->ssl_manager->handleHandshake(stream->client_connection)) {
      Debug::logmsg(LOG_INFO, "Handshake error with %s ",
                    stream->client_connection.getPeerAddress().c_str());
      clearStream(stream);
    }
    return;
  }
  case IO::IO_RESULT::FD_CLOSED:
  case IO::IO_RESULT::CANCELLED:
  case IO::IO_RESULT::ERROR:Debug::LogInfo("Error reading request ", LOG_DEBUG);
    clearStream(stream);
    return;
  case IO::IO_RESULT::SUCCESS:stream->backend_connection.enableReadEvent();
    stream->client_connection.enableReadEvent();
    break;
  case IO::IO_RESULT::DONE_TRY_AGAIN:stream->backend_connection.enableReadEvent();
    stream->client_connection.enableWriteEvent();
    break;
  case IO::IO_RESULT::FULL_BUFFER:break;
  default:Debug::LogInfo("Error sending data to client", LOG_DEBUG);
    clearStream(stream);
    return;
  }

  if (stream->request.upgrade_header && stream->request.connection_header_upgrade
      && stream->response.http_status_code == 101) {
    stream->upgrade.pinned_connection = true;
    std::string upgrade_header_value;
    stream->request.getHeaderValue(http::HTTP_HEADER_NAME::UPGRADE, upgrade_header_value);
    if (http_info::upgrade_protocols.count(upgrade_header_value) > 0)
      stream->upgrade.protocol = http_info::upgrade_protocols.at(upgrade_header_value);
  }
}

validation::REQUEST_RESULT
StreamManager::validateRequest(HttpRequest &request) {
  regmatch_t matches[4];
  const auto &request_line =
      nonstd::string_view(request.http_message,
                          request.http_message_length - 2)
          .to_string(); // request.getRequestLine();

  if (UNLIKELY(::regexec(&listener_config_.verb, request_line.c_str(), 3,
                         matches, 0) != 0)) {
    // TODO:: check RPC

    /*
     * if(!strncasecmp(request + matches[1].rm_so, "RPC_IN_DATA",
       matches[1].rm_eo - matches[1].rm_so)) is_rpc = 1; else
       if(!strncasecmp(request + matches[1].rm_so, "RPC_OUT_DATA",
       matches[1].rm_eo - matches[1].rm_so)) is_rpc = 0;
      *
      */

    // TODO:: Content lentgh required on POST command
    // error 411 Length Required
    return validation::REQUEST_RESULT::METHOD_NOT_ALLOWED;
  } else {
    request.setRequestMethod();
  }
  const auto &request_url =
      nonstd::string_view(request.path, request.path_length);
  if (request_url.find("%00") != std::string::npos) {
    return validation::REQUEST_RESULT::URL_CONTAIN_NULL;
  }

  if (listener_config_.has_pat &&
      regexec(&listener_config_.url_pat, request.path, 0, NULL, 0)) {
    return validation::REQUEST_RESULT::BAD_URL;
  }

  // Check reqeuest size .
  if (UNLIKELY(listener_config_.max_req > 0 &&
      request.headers_length > listener_config_.max_req &&
      request.request_method != http::REQUEST_METHOD::RPC_IN_DATA &&
      request.request_method != http::REQUEST_METHOD::RPC_OUT_DATA)) {
    return validation::REQUEST_RESULT::REQUEST_TOO_LARGE;
  }

  // Check for correct headers
  for (auto i = 0; i != request.num_headers; i++) {
    // check header values length
    if (request.headers[i].value_len > MAX_HEADER_VALUE_SIZE)
      return http::validation::REQUEST_RESULT::REQUEST_TOO_LARGE;
    const auto &header = nonstd::string_view(request.headers[i].name,
                                             request.headers[i].name_len);
    const auto &header_value = nonstd::string_view(
        request.headers[i].value, request.headers[i].value_len);
    if (http::http_info::headers_names.count(header.to_string()) > 0) {
      const auto &header_name =
          http::http_info::headers_names.at(header.to_string());
      const auto &header_name_string =
          http::http_info::headers_names_strings.at(header_name);

      switch (header_name) {
      case http::HTTP_HEADER_NAME::DESTINATION:
        if (listener_config_.rewr_dest != 0) {
          request.headers[i].header_off = true;
          request.add_destination_header = true;
        }
        break;
      case http::HTTP_HEADER_NAME::UPGRADE:request.upgrade_header = true;
        break;
      case http::HTTP_HEADER_NAME::CONNECTION:
        if (http_info::connection_values.count(std::string(header_value)) > 0
            && http_info::connection_values.at(std::string(header_value)) == CONNECTION_VALUES::UPGRADE)
          request.connection_header_upgrade = true;
        break;
      case http::HTTP_HEADER_NAME::ACCEPT_ENCODING:request.accept_encoding_header = true;
        break;
      case http::HTTP_HEADER_NAME::TRANSFER_ENCODING:
        if (listener_config_.ignore100continue)
          request.headers[i].header_off = true;
        break;
      case http::HTTP_HEADER_NAME::CONTENT_LENGTH: {
        request.message_bytes_left =
            static_cast<size_t>(std::atoi(request.headers[i].value));
        continue;
      }
      }

    }

    /* maybe header to be removed */
    MATCHER *m;
    for (m = listener_config_.head_off; m; m = m->next) {
      if ((request.headers[i].header_off =
               ::regexec(&m->pat, request.headers[i].name, 0, nullptr, 0) != 0))
        break;
    }
  }
  // waf

  return validation::REQUEST_RESULT::OK;
}

validation::REQUEST_RESULT StreamManager::validateResponse(HttpStream &stream) {
  HttpResponse &response = stream.response;
  /* If the response is 100 continue we need to enable chunked transfer. */
  if (response.http_status_code == 100) {
    stream.chunked_status = http::CHUNKED_STATUS::CHUNKED_ENABLED;
    return validation::REQUEST_RESULT::OK;
  }

  for (auto i = 0; i != response.num_headers; i++) {
    // check header values length

    const auto &header = nonstd::string_view(response.headers[i].name,
                                             response.headers[i].name_len);
    const auto &header_value = nonstd::string_view(
        response.headers[i].value, response.headers[i].value_len);
    if (http::http_info::headers_names.count(header.to_string()) > 0) {
      const auto &header_name =
          http::http_info::headers_names.at(header.to_string());
      const auto &header_name_string =
          http::http_info::headers_names_strings.at(header_name);

      switch (header_name) {
      case http::HTTP_HEADER_NAME::CONTENT_LENGTH: {
        stream.response.message_bytes_left =
            static_cast<size_t>(std::atoi(response.headers[i].value));
        continue;
      }
      case http::HTTP_HEADER_NAME::LOCATION: {
        // Rewrite location
        std::string location_header_value;
        std::string protocol;

        if (listener_config_.rewr_loc > 0) {
          std::string expr_ = "[A-Za-z.0-9-]+";
          std::smatch match;
          std::regex rgx(expr_);
          if (std::regex_search(location_header_value, match, rgx)) {
            std::string result = match[1];
            if (listener_config_.rewr_loc == 1) {
              if (result == listener_config_.address ||
                  result == stream.backend_connection.getBackend()->address) {
                std::string header_value = "http://";
                header_value += listener_config_.address;
                header_value += response.path;
                response.addHeader(http::HTTP_HEADER_NAME::LOCATION,
                                   header_value);
                response.addHeader(http::HTTP_HEADER_NAME::CONTENT_LOCATION,
                                   header_value);
                response.headers[i].header_off = true;
              }
            } else {
              if (result == stream.backend_connection.getBackend()->address) {
                std::string header_value = "http://";
                header_value += listener_config_.address;
                header_value += response.path;
                response.addHeader(http::HTTP_HEADER_NAME::LOCATION,
                                   header_value);
                response.addHeader(http::HTTP_HEADER_NAME::CONTENT_LOCATION,
                                   header_value);
                response.headers[i].header_off = true;
              }
            }
          } else {
            Debug::LogInfo("Invalid location header", LOG_REMOVE);
          }
        }
        break;
      }
      case http::HTTP_HEADER_NAME::STRICT_TRANSPORT_SECURITY:
          if (service_manager->getService(stream.request)->service_config.sts > 0)
            response.headers[i].header_off;
      break;
      default:continue;
      }

    }
    /* maybe header to be removed from responses */
    //  MATCHER *m;
    // for (m = listener_config_.head_off; m; m = m->next) {
    //  if ((response.headers[i].header_off =
    //          ::regexec(&m->pat, response.headers[i].name, 0, nullptr, 0) !=
    //          0))
    //    break;
    // }
  }
  return validation::REQUEST_RESULT::OK;
}

bool StreamManager::init(ListenerConfig &listener_config) {
  listener_config_ = listener_config;
  service_manager = ServiceManager::getInstance(listener_config);
  //  for (auto service_config = listener_config.services;
  //       service_config != nullptr; service_config = service_config->next) {
  //    if (!service_config->disabled) {
  //      service_manager->addService(*service_config);
  //    } else {
  //      Debug::LogInfo("Backend " + std::string(service_config->name) +
  //                     " disabled in config file",
  //                 LOG_NOTICE);
  //    }
  //  }
  if (listener_config.ctx != nullptr || !listener_config.ssl_config_file.empty()) {
    this->is_https_listener = true;
    ssl_manager = new ssl::SSLConnectionManager();
    this->is_https_listener = ssl_manager->init(listener_config);
  }
  return true;
}

bool StreamManager::transferChunked(HttpStream *stream) {
  if (stream->chunked_status != http::CHUNKED_STATUS::CHUNKED_DISABLED) {
    size_t pos = std::string(stream->client_connection.buffer).find("\r\n");
    auto hex = std::string(stream->client_connection.buffer).substr(0, pos);
    int chunk_length = std::stoul(hex, nullptr, 16);
    stream->chunked_status =
        chunk_length != 0 ? http::CHUNKED_STATUS::CHUNKED_ENABLED : http::CHUNKED_STATUS::CHUNKED_LAST_CHUNK;
    return true;
  }

  return false;
}

void StreamManager::setStrictTransportSecurity(Service *service, HttpStream *stream) {
  if (service->service_config.sts > 0) {
    std::string sts_header_value = "max-age=";
    sts_header_value += std::to_string(service->service_config.sts);
    stream->response.addHeader(http::HTTP_HEADER_NAME::STRICT_TRANSPORT_SECURITY,
                               sts_header_value);
  }
}

void StreamManager::setBackendCookie(Service *service, HttpStream *stream) {
  if (!service->becookie.empty()) {
    std::string set_cookie_header =
        service->becookie + "=" +
            stream->backend_connection.getBackend()->bekey;
    if (!service->becdomain.empty())
      set_cookie_header += "; Domain=" + service->becdomain;
    if (!service->becpath.empty())
      set_cookie_header += "; Path=" + service->becpath;
    time_t time = std::time(nullptr);
    if (service->becage > 0) {
      time += service->becage;
    } else {
      time += service->ttl;
    }
    char time_string[MAXBUF];
    strftime(time_string, MAXBUF - 1, "%a, %e-%b-%Y %H:%M:%S GMT",
             gmtime(&time));
    set_cookie_header += "; expires=";
    set_cookie_header += time_string;
    stream->response.addHeader(http::HTTP_HEADER_NAME::SET_COOKIE,
                               set_cookie_header);
  }
}

void StreamManager::applyCompression(Service *service, HttpStream *stream) {
  http::TRANSFER_ENCODING_TYPE compression_type;
  /* Check if we have found the accept encoding header in the request but not the transfer encoding in the response. */
  if ((!stream->response.transfer_encoding_header) && stream->request.accept_encoding_header) {
    std::string compression_value;
    stream->request.getHeaderValue(http::HTTP_HEADER_NAME::ACCEPT_ENCODING, compression_value);

    /* Check if we accept any of the compression algorithms. */
    size_t initial_pos;
    initial_pos = compression_value.find(service->service_config.compression_algorithm);
    if (initial_pos != std::string::npos) {
      compression_value = service->service_config.compression_algorithm;
      stream->response.addHeader(http::HTTP_HEADER_NAME::TRANSFER_ENCODING, compression_value);
      stream->response.transfer_encoding_header = true;
      compression_type = http_info::compression_types.at(compression_value);

      /* Get the message_uncompressed. */
      std::string message_no_compressed = std::string(stream->response.message, stream->response.message_length);
      /* We are going to do the compression depending on the compression algorithm. */
      switch (compression_type) {
      case http::TRANSFER_ENCODING_TYPE::GZIP: {
        std::string message_compressed_gzip;
        if (!zlib::compress_message_gzip(message_no_compressed, message_compressed_gzip))
          Debug::logmsg(LOG_ERR, "Error while compressing.");
        strncpy(stream->response.message, message_compressed_gzip.c_str(), stream->response.message_length);
        break;
      }
      case http::TRANSFER_ENCODING_TYPE::DEFLATE: {
        std::string message_compressed_deflate;
        if (!zlib::compress_message_deflate(message_no_compressed, message_compressed_deflate))
          Debug::logmsg(LOG_ERR, "Error while compressing.");
        strncpy(stream->response.message, message_compressed_deflate.c_str(), stream->response.message_length);
        break;
      }
      default: break;
      }
    }
  }
}

void StreamManager::clearStream(HttpStream *stream) {
  //TODO:: add connection closing reason for logging purpose
  if (stream == nullptr) {
    return;
  }
  if (stream->backend_connection.buffer_size > 0 || stream->backend_connection.splice_pipe.bytes > 0) {
    //TODO:: remove and create enum with READY_TO_SEND_RESPONSE
    stream->backend_connection.disableEvents();
    return;
  }

  if (stream->timer_fd.getFileDescriptor() > 0) {
    deleteFd(stream->timer_fd.getFileDescriptor());
    stream->timer_fd.unset();
    timers_set[stream->timer_fd.getFileDescriptor()] = nullptr;
    timers_set.erase(stream->timer_fd.getFileDescriptor());
  }
  if (stream->client_connection.getFileDescriptor() > 0) {
    deleteFd(stream->client_connection.getFileDescriptor());
    streams_set[stream->client_connection.getFileDescriptor()] = nullptr;
    streams_set.erase(stream->client_connection.getFileDescriptor());
  }
  if (stream->backend_connection.getFileDescriptor() > 0) {
    if (stream->backend_connection.isConnected())
      stream->backend_connection.getBackend()->decreaseConnection();
    deleteFd(stream->backend_connection.getFileDescriptor());
    streams_set[stream->backend_connection.getFileDescriptor()] = nullptr;
    streams_set.erase(stream->backend_connection.getFileDescriptor());
  }
  delete stream;
}

void StreamManager::setListenSocket(int fd) {
  listener_connection.setFileDescriptor(fd);
}
