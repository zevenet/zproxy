//
// Created by abdess on 4/5/18.
//

#include "StreamManager.h"
#include "../util/Network.h"
#include "../util/common.h"
#include "../util/utils.h"
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
      Debug::Log("Connection closed prematurely" + std::to_string(fd));
      return;
    }
    auto io_result = stream->client_connection.write(this->e200.c_str(),
                                                     this->e200.length());
    switch (io_result) {
    case IO::ERROR:
    case IO::FD_CLOSED:
    case IO::FULL_BUFFER:
      Debug::Log("Something happend sentid e200", LOG_DEBUG);
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
      Debug::Log("Stream doesn't exist for " + std::to_string(fd));
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
    case ACCEPTOR:
      break;
    case SERVER:
      onResponseEvent(fd);
      break;
    case CLIENT:
      this->onRequestEvent(fd);
      break;
    case CONNECT_TIMEOUT:
      onConnectTimeoutEvent(fd);
      break;
    case REQUEST_TIMEOUT:
      onRequestTimeoutEvent(fd);
      break;
    case RESPONSE_TIMEOUT:
      onResponseTimeoutEvent(fd);
      break;
    case SIGNAL:
      onSignalEvent(fd);
      break;
    case MAINTENANCE: // TODO:: Handle health checkers, sessions ...
      break;
    default: // should not enter here
      break;
    }
    return;
  }
  case WRITE: {
    auto stream = streams_set[fd];
    if (stream == nullptr) {
      // We should not be here without a stream created, so we remove the fd
      // from the eventloop
      switch (event_group) {
      case ACCEPTOR:
        break;
      case SERVER:
        Debug::Log("SERVER_WRITE : Stream doesn't exist for " +
                   std::to_string(fd));
        break;
      case CLIENT:
        Debug::Log("CLIENT_WRITE : Stream doesn't exist for " +
                   std::to_string(fd));
        break;
      }

      deleteFd(fd);
      ::close(fd);
      return;
    }

    switch (event_group) {
    case ACCEPTOR:
      break;
    case SERVER: {
      onServerWriteEvent(stream);
      break;
    }
    case CLIENT: {
      onClientWriteEvent(stream);
      break;
    }
    }
    //      updateFd(fd, EVENT_TYPE::READ, event_group);
    return;
  }
  case DISCONNECT: {
    auto stream = streams_set[fd];
    if (stream == nullptr) {
      Debug::Log("Remote host closed connection prematurely ", LOG_INFO);
      deleteFd(fd);
      ::close(fd);
      return;
    }
    switch (event_group) {
    case SERVER: {
      if (!stream->backend_connection.isConnected()) {
        auto response =
            HttpStatus::getHttpResponse(HttpStatus::Code::RequestTimeout);
        stream->client_connection.write(response.c_str(), response.length());
        Debug::Log("Backend closed connection", LOG_INFO);
      }
      break;
    }
    case CLIENT: {
      Debug::Log("Client closed connection", LOG_INFO);
      break;
    }
    default:
      Debug::Log("Why this happends!!", LOG_INFO);
      break;
    }
    clearStream(stream);
    break;
  }
  default:
    Debug::Log("Unexpected  event type", LOG_DEBUG);
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

StreamManager::StreamManager(){
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
      //      Debug::Log("No events !!");
    }
    // if(needMainatance)
    //    doMaintenance();
  }
}

void StreamManager::addStream(int fd) {
  if (!this->addFd(fd, READ, EVENT_GROUP::CLIENT)) {
    Debug::Log("Error adding to epoll manager", LOG_NOTICE);
  }
}

int StreamManager::getWorkerId() { return worker_id; }

void StreamManager::onRequestEvent(int fd) {
  HttpStream *stream = streams_set[fd];
  if (stream != nullptr) {
    stream = streams_set.at(fd);
    if (fd != stream->client_connection.getFileDescriptor()) {
      Debug::Log("FOUND:: Aqui ha pasado algo raro!!", LOG_REMOVE);
    }
  } else {
    stream = new HttpStream();
    stream->client_connection.setFileDescriptor(fd);
    // set extra header to forward to the backends
    stream->request.addHeader(http::HTTP_HEADER_NAME::H_X_FORWARDED_FOR,
                              stream->client_connection.getPeerAddress());
    streams_set[fd] = stream;
    if (fd != stream->client_connection.getFileDescriptor()) {
      Debug::Log("FOUND:: Aqui ha pasado algo raro!!", LOG_DEBUG);
    }
  }

  auto result = stream->client_connection.read();
  if (result == IO::IO_RESULT::ERROR) {
    Debug::Log("Error reading request ", LOG_DEBUG);
    clearStream(stream);
    return;
  }
  //  stream->client_stadistics.update();
  // TODO::Process all buffer
  size_t parsed = 0;
  http_parser::PARSE_RESULT parse_result;
  do {
    parse_result = stream->request.parseRequest(
        stream->client_connection.buffer, stream->client_connection.buffer_size,
        &parsed); // parsing http data as response structured
    if (stream->client_connection.buffer_size != parsed) {
      Debug::Log("Buffer size: " +
                 std::to_string(stream->client_connection.buffer_size) +
                 "\nparsed data: " + std::to_string(parsed));
    }
    switch (parse_result) {
    case http_parser::PARSE_RESULT::SUCCESS: {
      auto valid = validateRequest(stream->request);
      if (UNLIKELY(validation::REQUEST_RESULT::OK != valid)) {
        char caddr[50];
        // Network::addr2str(caddr, 50 - 1, stream->client_connection.address,
        // 1);
        if (UNLIKELY(Network::getPeerAddress(fd, caddr, 50) == nullptr)) {
          Debug::Log("Error getting peer address", LOG_DEBUG);
        } else {
          Debug::logmsg(LOG_WARNING, "(%lx) e%d %s %s from %s",
                        std::this_thread::get_id(),
                        static_cast<int>(HttpStatus::Code::NotImplemented),
                        validation::request_result_reason.at(valid).c_str(),
                        stream->client_connection.buffer, caddr);
        }
        stream->replyError(HttpStatus::Code::NotImplemented,
                           validation::request_result_reason.at(valid).c_str(),
                           listener_config_.err501);
        this->clearStream(stream);
        return;
      }
      auto service = service_manager->getService(stream->request);
      if (service == nullptr) {
        char caddr[50];
        // Network::addr2str(caddr, 50 - 1, stream->client_connection.address,
        // 1);
        if (UNLIKELY(Network::getPeerAddress(fd, caddr, 50) == nullptr)) {
          Debug::Log("Error getting peer address", LOG_DEBUG);
        } else {
          Debug::logmsg(LOG_WARNING, "(%lx) e%d %s from %s",
                        std::this_thread::get_id(),
                        static_cast<int>(HttpStatus::Code::ServiceUnavailable),
                        validation::request_result_reason
                            .at(validation::REQUEST_RESULT::SERVICE_NOT_FOUND)
                            .c_str(),
                        // stream->client_connection.buffer,
                        caddr);
        }
        stream->replyError(
            HttpStatus::Code::ServiceUnavailable,
            validation::request_result_reason
                .at(validation::REQUEST_RESULT::SERVICE_NOT_FOUND)
                .c_str(),
            listener_config_.err503);
        this->clearStream(stream);
        return;
      }
      auto bck = service->getBackend(*stream);
      // if (stream->backend_connection.getFileDescriptor() ==
      // BACKEND_STATUS::NO_BACKEND) {
      if (bck == nullptr) {
        // No backend available
        char caddr[50];
        // Network::addr2str(caddr, 50 - 1, stream->client_connection.address,
        // 1);
        if (UNLIKELY(Network::getPeerAddress(fd, caddr, 50) == nullptr)) {
          Debug::Log("Error getting peer address", LOG_DEBUG);
        } else {
          Debug::logmsg(LOG_WARNING, "(%lx) e%d %s %s from %s",
                        std::this_thread::get_id(),
                        static_cast<int>(HttpStatus::Code::ServiceUnavailable),
                        validation::request_result_reason
                            .at(validation::REQUEST_RESULT::BACKEND_NOT_FOUND)
                            .c_str(),
                        stream->client_connection.buffer, caddr);
        }
        stream->replyError(
            HttpStatus::Code::ServiceUnavailable,
            validation::request_result_reason
                .at(validation::REQUEST_RESULT::BACKEND_NOT_FOUND)
                .c_str(),
            listener_config_.err503);
        this->clearStream(stream);
        return;
      } else {
        IO::IO_OP op_state = IO::IO_OP::OP_ERROR;
        //        Debug::logmsg(LOG_REMOVE, "Backend assigned %s",
        //        bck->address.c_str());
        switch (bck->backend_type) {
        case REMOTE:
          if (stream->backend_connection.getBackend() == nullptr ||
                  !stream->backend_connection.isConnected()
                  /*   stream->backend_connection.getBackend()
                              ->backen_id !=
                      bck->backen_id*/) {  // TODO::Comprobar que backend no es
                                           // null
            if (stream->backend_connection.getFileDescriptor() !=
                BACKEND_STATUS::NO_BACKEND) {
              stream->backend_connection.setBackend(
                  stream->backend_connection.getBackend(), false);
              deleteFd(stream->backend_connection
                           .getFileDescriptor()); // TODO:: Client cannot
                                                  // be connected to more
                                                  // than one backend at
                                                  // time
              streams_set.erase(stream->backend_connection.getFileDescriptor());
              stream->backend_connection.closeConnection();
            }
            stream->backend_connection.setBackend(bck, true);
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
              Debug::Log("Error connecting to backend " + bck->address,
                         LOG_NOTICE); // TODO:: respond e503
              stream->backend_connection.setBackend(bck, false);
              stream->backend_connection.closeConnection();
              return;
            }

            case IO::IO_OP::OP_IN_PROGRESS: {
              stream->timer_fd.set(bck->conn_timeout * 1000);
              stream->backend_connection.getBackend()
                  ->increaseConnTimeoutAlive();
              timers_set[stream->timer_fd.getFileDescriptor()] = stream;
              addFd(stream->timer_fd.getFileDescriptor(), EVENT_TYPE::READ,
                    EVENT_GROUP::CONNECT_TIMEOUT);
              //                     return;
            }
            case IO::IO_OP::OP_SUCCESS: {
              Network::setSocketNonBlocking(
                  stream->backend_connection.getFileDescriptor());
              // Debug::Log("Connected to backend : " + bck->address + ":"
              // + std::to_string(bck->port), LOG_DEBUG);
              streams_set[stream->backend_connection.getFileDescriptor()] =
                  stream;

              addFd(stream->backend_connection.getFileDescriptor(),
                    EVENT_TYPE::WRITE, EVENT_GROUP::SERVER);
              break;
            }
            }
          } else {
            updateFd(stream->backend_connection.getFileDescriptor(),
                     EVENT_TYPE::WRITE, EVENT_GROUP::SERVER);
          }
          break;
        case EMERGENCY_SERVER:

          break;
        case REDIRECT:
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
        case CACHE_SYSTEM:
          break;
        }
      }
      break;
    }

    case http_parser::PARSE_RESULT::FAILED:
      Debug::Log("Parser FAILED", LOG_DEBUG);
      break;
    case http_parser::PARSE_RESULT::INCOMPLETE:
      Debug::Log("Parser INCOMPLETE", LOG_DEBUG);
      break;
    case http_parser::PARSE_RESULT::TOOLONG:
      Debug::Log("Parser TOOLONG", LOG_DEBUG);
      break;
    }

    if ((stream->client_connection.buffer_size - parsed) > 0) {
      Debug::Log("Buffer size: left size: " +
                     std::to_string(stream->client_connection.buffer_size),
                 LOG_DEBUG);
      Debug::Log("Current request buffer: \n " +
                     std::string(stream->client_connection.buffer,
                                 stream->client_connection.buffer_size),
                 LOG_DEBUG);
      Debug::Log("Parsed data size: " + std::to_string(parsed), LOG_DEBUG);
    }

  } while (stream->client_connection.buffer_size > parsed &&
           parse_result ==
               http_parser::PARSE_RESULT::SUCCESS); // TODO:: Add support for
                                                    // http pipeline
  updateFd(fd, EVENT_TYPE::READ, EVENT_GROUP::CLIENT);
}

void StreamManager::onResponseEvent(int fd) {
  HttpStream *stream = streams_set[fd];
  if (stream == nullptr) {
    Debug::Log("Backend Connection, Stream closed", LOG_DEBUG);
    ::close(fd);
    return;
  }
  if (stream->backend_connection.getBackend()->response_timeout > 0) {
    stream->timer_fd.unset();
    events::EpollManager::deleteFd(stream->timer_fd.getFileDescriptor());
  }
  auto result = stream->backend_connection.read();

  stream->backend_connection.getBackend()->calculateLatency(
      std::chrono::duration_cast<std::chrono::duration<double>>(
          std::chrono::steady_clock::now() -
          stream->backend_connection.time_start)
          .count());

  if (result == IO::IO_RESULT::ERROR) {
    Debug::Log("Error reading response ", LOG_DEBUG);
    // TODO:: What to do if backend down!!
    clearStream(stream);
    return;
  }
  //  stream->backend_stadistics.update();
  size_t parsed = 0;
  auto ret = stream->response.parseResponse(
      stream->backend_connection.buffer, stream->backend_connection.buffer_size,
      &parsed); // parsing http data as response structured
  updateFd(stream->client_connection.getFileDescriptor(), EVENT_TYPE::WRITE,
           EVENT_GROUP::CLIENT);

  stream->backend_connection.getBackend()->setAvgTransferTime(
      std::chrono::duration_cast<std::chrono::duration<double>>(
          std::chrono::steady_clock::now() -
          stream->backend_connection.time_start)
          .count());

  //  switch (ret) {
  //    case http_parser::SUCCESS:
  //      updateFd(stream->client_connection.getFileDescriptor(),
  //               EVENT_TYPE::WRITE,
  //               EVENT_GROUP::CLIENT);
  //      break;
  //    case http_parser::FAILED:Debug::Log("Parser FAILED", LOG_DEBUG);
  //      break;
  //    case http_parser::INCOMPLETE:Debug::Log("Parser INCOMPLETE", LOG_DEBUG);
  //      break;
  //    case http_parser::TOOLONG:Debug::Log("Parser TOOLONG", LOG_DEBUG);
  //      break;
  //  }

  updateFd(fd, EVENT_TYPE::READ, EVENT_GROUP::SERVER);
}
void StreamManager::onConnectTimeoutEvent(int fd) {
  HttpStream *stream = timers_set[fd];
  if (stream == nullptr)
    Debug::Log("Stream null pointer", LOG_REMOVE);
  if (stream->timer_fd.isTriggered()) {
    char caddr[50];
    if (UNLIKELY(Network::getPeerAddress(
                     stream->client_connection.getFileDescriptor(), caddr,
                     50) == nullptr)) {
      Debug::Log("Error getting peer address", LOG_DEBUG);
    } else {
      Debug::logmsg(LOG_NOTICE, "(%lx) e%d %s %s from %s",
                    std::this_thread::get_id(),
                    static_cast<int>(HttpStatus::Code::ServiceUnavailable),
                    validation::request_result_reason
                        .at(validation::REQUEST_RESULT::BACKEND_NOT_FOUND)
                        .c_str(),
                    stream->client_connection.buffer, caddr);
    }
    stream->replyError(
        HttpStatus::Code::ServiceUnavailable,
        HttpStatus::reasonPhrase(HttpStatus::Code::ServiceUnavailable).c_str(),
        listener_config_.err503);
    this->clearStream(stream);
  }
}

void StreamManager::onRequestTimeoutEvent(int fd) {
  // TODO::IMPLENET
}
void StreamManager::onResponseTimeoutEvent(int fd) {
  HttpStream *stream = timers_set[fd];
  if (stream == nullptr)
    Debug::Log("Stream null pointer", LOG_REMOVE);
  if (stream->timer_fd.isTriggered()) {
    char caddr[50];
    if (UNLIKELY(Network::getPeerAddress(
                     stream->client_connection.getFileDescriptor(), caddr,
                     50) == nullptr)) {
      Debug::Log("Error getting peer address", LOG_DEBUG);
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

  //      auto result = stream->client_connection.writeTo(
  //          stream->backend_connection.getFileDescriptor());
  size_t total_writen = 0;
  auto result = stream->client_connection.writeTo(stream->backend_connection,
                                                  stream->request);

  // TODO::rewrite destination

  if (result == IO::IO_RESULT::SUCCESS) {
    stream->timer_fd.set(
        stream->backend_connection.getBackend()->response_timeout * 1000);
    timers_set[stream->timer_fd.getFileDescriptor()] = stream;
    addFd(stream->timer_fd.getFileDescriptor(), EVENT_TYPE::READ,
          EVENT_GROUP::RESPONSE_TIMEOUT);
    updateFd(fd, EVENT_TYPE::READ, SERVER);
    stream->backend_connection.time_start = std::chrono::steady_clock::now();

  } else if (result == IO::IO_RESULT::DONE_TRY_AGAIN) {
    updateFd(fd, EVENT_TYPE::WRITE, SERVER);
  } else {
    // updateFd(fd, EVENT_TYPE::ANY, event_group);
    Debug::Log("Error sending data to client", LOG_DEBUG);
    return; // TODO:: What to do??
  }
}

void StreamManager::onClientWriteEvent(HttpStream *stream) {
  int fd = stream->client_connection.getFileDescriptor();
  auto result = stream->backend_connection.writeTo(
      stream->client_connection.getFileDescriptor());
  if (result == IO::IO_RESULT::SUCCESS) {
    updateFd(fd, EVENT_TYPE::READ, CLIENT);
  } else if (result == IO::IO_RESULT::DONE_TRY_AGAIN) {
    updateFd(fd, EVENT_TYPE::WRITE, CLIENT);
  } else {
    Debug::Log("Error sending data to client", LOG_DEBUG);
    // updateFd(fd, EVENT_TYPE::ANY, event_group);
    return; // TODO:: what to do
  }
}

validation::REQUEST_RESULT
StreamManager::validateRequest(HttpRequest &request) { // TODO:: why use of e501
  regmatch_t matches[4];
  std::string request_line = request.getRequestLine();
  //  Debug::Log("Request line " + request_line, LOG_REMOVE); // TODO: remove
  if (UNLIKELY(::regexec(&listener_config_.verb, request_line.c_str(), 3,
                         matches, 0) != 0)) {
    return validation::REQUEST_RESULT::METHOD_NOT_ALLOWED;
  } else {
    request.setRequestMethod();
  }

  auto request_url = request.getUrl();
  if (request_url.find("%00") != std::string::npos) {
    return validation::REQUEST_RESULT::URL_CONTAIN_NULL;
  }

  if (listener_config_.has_pat &&
      regexec(&listener_config_.url_pat, request_url.c_str(), 0, NULL, 0)) {
    return validation::REQUEST_RESULT::BAD_URL;
  }

  // TODO:: Check reqeuest size .
  if (UNLIKELY(listener_config_.max_req > 0 &&
               request.headers_length > listener_config_.max_req &&
               request.request_method != http::REQUEST_METHOD::RM_RPC_IN_DATA &&
               request.request_method !=
                   http::REQUEST_METHOD::RM_RPC_OUT_DATA)) {
    return validation::REQUEST_RESULT::REQUEST_TOO_LARGE;
  }

  // TODO:: Check for correct headers
  for (auto i = 0; i != request.num_headers; i++) {
    std::string header(request.headers[i].name, request.headers[i].name_len);
    std::string header_value(request.headers[i].value,
                             request.headers[i].value_len);
    auto header_name = http::http_info::headers_names.at(header);
    if (header_name != http::HTTP_HEADER_NAME::H_NONE) {
      auto header_name_string =
          http::http_info::headers_names_strings.at(header_name);
      //      Debug::
      //          logmsg(LOG_DEBUG, "\t%s: %s", header_name_string,
      //          header_value.c_str());
    } else {
      // TODO::Unknown header, What to do ??
      Debug::logmsg(LOG_DEBUG, "\tUnknown: %s", header_value.c_str());
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

bool StreamManager::init(ListenerConfig &listener_config) {
  listener_config_ = listener_config;
  service_manager = ServiceManager::getInstance(listener_config);
  //  for (auto service_config = listener_config.services;
  //       service_config != nullptr; service_config = service_config->next) {
  //    if (!service_config->disabled) {
  //      service_manager->addService(*service_config);
  //    } else {
  //      Debug::Log("Backend " + std::string(service_config->name) +
  //                     " disabled in config file",
  //                 LOG_NOTICE);
  //    }
  //  }
  return true;
}

void StreamManager::clearStream(HttpStream *stream) {
  if (stream == nullptr) {
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
    deleteFd(stream->backend_connection.getFileDescriptor());
    streams_set[stream->backend_connection.getFileDescriptor()] = nullptr;
    streams_set.erase(stream->backend_connection.getFileDescriptor());
    stream->backend_connection.setBackend(
        stream->backend_connection.getBackend(), false);
  }
  delete stream;
}

void StreamManager::setListenSocket(int fd) {
  listener_connection.setFileDescriptor(fd);
}
