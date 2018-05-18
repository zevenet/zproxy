//
// Created by abdess on 4/5/18.
//

#include "StreamManager.h"
#include <functional>
#include "../util/Network.h"
#include "../util/common.h"
#if HELLO_WORLD_SERVER
void StreamManager::HandleEvent(int fd, EVENT_TYPE event_type, EVENT_GROUP event_group) {
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
      connection->buffer_size = 1; // reset buffer size to avoid buffer overflow due to not consuming buffer data.
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
      auto connection = stream->getConnection(fd);
      auto io_result = connection->write(this->e200.c_str(),
                                         this->e200.length());
      switch (io_result) {
        case IO::ERROR:
        case IO::FD_CLOSED:
        case IO::FULL_BUFFER: Debug::Log("Something happend sentid e200", LOG_DEBUG);
          break;
        case IO::SUCCESS:
        case IO::DONE_TRY_AGAIN:updateFd(fd, READ_ONESHOT, EVENT_GROUP::CLIENT);
          break;
      }

      break;
    }
    case CONNECT:break;
    case ACCEPT:break;
    case DISCONNECT: {
      auto stream = streams_set[fd];
      if (stream == nullptr) {
        Debug::Log("Stream doesn't exist for " + std::to_string(fd));
        ::close(fd);
        return;
      }
      streams_set.erase(fd);
      delete stream;
      break;
    }
  }
}
#else
void StreamManager::HandleEvent(int fd, EVENT_TYPE event_type, EVENT_GROUP event_group) {
  switch (event_type) {
    case READ:
    case READ_ONESHOT: {
      switch (event_group) {
        case ACCEPTOR:break;
        case SERVER:this->onResponseEvent(fd);
          break;
        case CLIENT:this->onRequestEvent(fd);
          break;
        case CONNECT_TIMEOUT:break;
        case REQUEST_TIMEOUT: onRequestTimeoutEvent(fd);
          break;
        case RESPONSE_TIMEOUT:onResponseTimeoutEvent(fd);
          break;
        case SIGNAL:onSignalEvent(fd);
          break;
      }
      break;
    }
    case WRITE: {
      auto stream = streams_set[fd];
      if (stream == nullptr) {
        //We should be here without an established stream, so we remove from the eventloop
        switch (event_group) {
          case ACCEPTOR:break;
          case SERVER:Debug::Log("SERVER : Stream doesn't exist for " + std::to_string(fd));

            break;
          case CLIENT:Debug::Log("CLIENT : Stream doesn't exist for " + std::to_string(fd));
            break;
        }
        return;
      }
      switch (event_group) {
        case ACCEPTOR:break;
        case SERVER: {
          auto result = stream->client_connection.writeTo(stream->backend_connection.getFileDescriptor());
          if (result == IO::SUCCESS) {
            updateFd(fd, EVENT_TYPE::READ, event_group);
          } else if (result == IO::DONE_TRY_AGAIN) {
            updateFd(fd, EVENT_TYPE::WRITE, event_group);
          } else {
            // updateFd(fd, EVENT_TYPE::ANY, event_group);
            Debug::Log("Error sending data to client", LOG_DEBUG);
            return; //TODO:: What to do??
          }
          break;
        }
        case CLIENT: {
          auto result = stream->backend_connection.writeTo(stream->client_connection.getFileDescriptor());
          if (result == IO::SUCCESS) {
            updateFd(fd, EVENT_TYPE::READ, event_group);
          } else if (result == IO::DONE_TRY_AGAIN) {
            updateFd(fd, EVENT_TYPE::WRITE, event_group);
          } else {
            Debug::Log("Error sending data to client", LOG_DEBUG);
            //updateFd(fd, EVENT_TYPE::ANY, event_group);
            return; //TODO:: what to do
          }
          break;
        }
      }
      updateFd(fd, EVENT_TYPE::READ, event_group);
      break;
    }
    case DISCONNECT: {
      auto stream = streams_set[fd];
      if (stream == nullptr) {
        Debug::Log("Remote host closed connection prematurely ");
        ::close(fd);
        return;
      }
      switch (event_group) {
        case ACCEPTOR:break;
        case SERVER: {
          auto response = HttpStatus::getErrorResponse(HttpStatus::Code::RequestTimeout);
          stream->client_connection.write(response.c_str(), response.length());
          Debug::Log("Backend closed connection", LOG_NOTICE);
          streams_set.erase(stream->client_connection.getFileDescriptor());
          break;
        }
        case CLIENT: {
          Debug::Log("Client closed connection", LOG_NOTICE);
          if (stream->backend_connection.getFileDescriptor() != BACKEND_STATUS::NO_BACKEND) {
            deleteFd(stream->backend_connection.getFileDescriptor());
            streams_set.erase(stream->backend_connection.getFileDescriptor());
          }
          break;
        }
      }
      streams_set.erase(fd);
      delete stream;
      break;
    }
    default: Debug::Log("Unexpected  event type", LOG_DEBUG);
  }
}
#endif

void StreamManager::stop() { is_running = false; }

void StreamManager::start(int thread_id_) {
  is_running = true;
  worker_id = thread_id_;
  this->worker = std::thread([this] { doWork(); });
  if (worker_id >= 0) {
    helper::ThreadHelper::setThreadAffinity(worker_id, worker.native_handle());
    helper::ThreadHelper::setThreadName("WORKER_" + std::to_string(worker_id),
                                        worker.native_handle());
  }
}

StreamManager::StreamManager() {};

StreamManager::~StreamManager() {
  stop();
  if (worker.joinable()) worker.join();

  for (auto &key_pair : streams_set) {
    delete key_pair.second;
  }
}
void StreamManager::doWork() {
  // TODO::set thread affinty
  while (is_running) {
    if (loopOnce(0) <= 0) {
      // something bad happend
      Debug::Log("No events !!");
    }
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
  if (stream == nullptr) {
    stream = new HttpStream();
    stream->client_connection.setFileDescriptor(fd);
    streams_set[fd] = stream;
  }
  auto result = stream->client_connection.read();
  if (result == IO::ERROR) {
    Debug::Log("Error reading request ", LOG_DEBUG);
    return;
  }
  stream->client_stadistics.update();
//TODO::Process all buffer
  size_t parsed = 0;
  http_parser::PARSE_RESULT parse_result;
  do {
    parse_result = stream->request.parseRequest(stream->client_connection.buffer,
                                                stream->client_connection.buffer_size,
                                                &parsed); // parsing http data as response structured
    if (stream->client_connection.buffer_size != parsed) {
      Debug::Log("Buffer size: " + std::to_string(stream->client_connection.buffer_size) + "\nparsed data: "
                     + std::to_string(parsed));
    }
    switch (parse_result) {
      case http_parser::SUCCESS: {
        auto valid = validateRequest(stream->request);
        if (UNLIKELY(validation::OK != valid)) {
          char caddr[50];
          //Network::addr2str(caddr, 50 - 1, stream->client_connection.address, 1);
          if (UNLIKELY(Network::getPeerAddress(fd, caddr, 50) == nullptr)) {
            Debug::Log("Error getting peer address", LOG_DEBUG);
          } else {
            Debug::logmsg(LOG_WARNING,
                          "(%lx) e%d %s %s from %s",
                          std::this_thread::get_id(),
                          static_cast<int>(HttpStatus::Code::NotImplemented),
                          validation::validation_reason.at(valid),
                          stream->client_connection.buffer,
                          caddr);
          }
          stream->replyError(HttpStatus::Code::NotImplemented,
                             validation::validation_reason.at(valid),
                             listener_config_.err501);
          this->clearStream(stream);
          return;
        }
        auto service = getService(stream->request);
        auto bck = service->getBackend(stream->client_connection);
        // if (stream->backend_connection.getFileDescriptor() == BACKEND_STATUS::NO_BACKEND) {
        if (bck == nullptr) {
          //No backend available
          auto response = HttpStatus::getErrorResponse(HttpStatus::Code::ServiceUnavailable);
          stream->client_connection.write(response.c_str(), response.length());
          stream->client_connection.closeConnection();
          return;;
        } else if (stream->backend_connection.getBackendId() != bck->backen_id) {
          if (stream->backend_connection.getFileDescriptor() != BACKEND_STATUS::NO_BACKEND) {
            streams_set.erase(stream->backend_connection.getFileDescriptor());
            deleteFd(stream->backend_connection.getFileDescriptor());//TODO:: Client cannot be connected to more than one backend at time
            stream->backend_connection.closeConnection();
          }
          if (!stream->backend_connection.doConnect(*bck->address_info, bck->timeout)) {
            auto response = HttpStatus::getErrorResponse(HttpStatus::Code::ServiceUnavailable);
            stream->client_connection.write(response.c_str(), response.length());
            Debug::Log("Error connecting to backend " + bck->address, LOG_NOTICE); //TODO:: respond e503
            stream->backend_connection.closeConnection();
            return;
          } else {
            Network::setSocketNonBlocking(stream->backend_connection.getFileDescriptor());
            //Debug::Log("Connected to backend : " + bck->address + ":" + std::to_string(bck->port), LOG_DEBUG);
            stream->backend_connection.setBackendId(bck->backen_id);
            streams_set[stream->backend_connection.getFileDescriptor()] = stream;

            addFd(stream->backend_connection.getFileDescriptor(), EVENT_TYPE::WRITE, EVENT_GROUP::SERVER);
          }
        } else {

          updateFd(stream->backend_connection.getFileDescriptor(),
                   EVENT_TYPE::WRITE,
                   EVENT_GROUP::SERVER);
        }
//              } else {
//                updateFd(stream->backend_connection.getFileDescriptor(),
//                         EVENT_TYPE::WRITE,
//                         EVENT_GROUP::SERVER);
//              }
        break;
      }
      case http_parser::FAILED:Debug::Log("Parser FAILED", LOG_DEBUG);
        break;
      case http_parser::INCOMPLETE:Debug::Log("Parser INCOMPLETE", LOG_DEBUG);
        break;
      case http_parser::TOOLONG:Debug::Log("Parser TOOLONG", LOG_DEBUG);
        break;
    }

    if ((stream->client_connection.buffer_size - parsed) > 0) {
      Debug::Log("Buffer size: left size: " + std::to_string(stream->client_connection.buffer_size), LOG_DEBUG);
      Debug::Log("Current request buffer: \n "
                     + std::string(stream->client_connection.buffer, stream->client_connection.buffer_size), LOG_DEBUG);
      Debug::Log("Parsed data size: " + std::to_string(parsed), LOG_DEBUG);
    }

  } while (stream->client_connection.buffer_size > parsed
      && parse_result == http_parser::SUCCESS); //TODO:: Add support for http pipeline
  updateFd(fd, EVENT_TYPE::READ, EVENT_GROUP::CLIENT);
}

void StreamManager::onResponseEvent(int fd) {
  HttpStream *stream = streams_set[fd];
  if (stream == nullptr) {
    Debug::Log("Backend Connection, Stream closed", LOG_DEBUG);
    return;
  }
  auto result = stream->backend_connection.read();
  if (result == IO::ERROR) {
    Debug::Log("Error reading response ", LOG_DEBUG);
    return;
  }
  stream->backend_stadistics.update();
  size_t parsed = 0;
  auto ret = stream->response.parseResponse(stream->backend_connection.buffer,
                                            stream->backend_connection.buffer_size,
                                            &parsed); // parsing http data as response structured
  updateFd(stream->client_connection.getFileDescriptor(),
           EVENT_TYPE::WRITE,
           EVENT_GROUP::CLIENT);

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
void StreamManager::onRequestTimeoutEvent(int fd) {
//TODO::IMPLENET
}
void StreamManager::onResponseTimeoutEvent(int fd) {
//TODO::IMPLEMENT
}
void StreamManager::onSignalEvent(int fd) {
//TODO::IMPLEMENET
}
validation::VALIDATION_RESULT StreamManager::validateRequest(HttpRequest &request) { //TODO:: why use of e501
  regmatch_t matches[4];
  std::string request_line = request.getRequestLine();
  Debug::Log("Request line " + request_line, LOG_REMOVE);//TODO: remove
  if (UNLIKELY(::regexec(&listener_config_.verb, request_line.c_str(), 3, matches, 0) != 0)) {
    return validation::METHOD_NOT_ALLOWED;
  } else {
    request.setRequestMethod();
  }

  auto request_url = request.getUrl();
  if (request_url.find("%00") != std::string::npos) {
    return validation::URL_CONTAIN_NULL;
  }

  if (listener_config_.has_pat && regexec(&listener_config_.url_pat, request_url.c_str(), 0, NULL, 0)) {
    return validation::BAD_URL;
  }

  //check for correct headers

  for (auto i = 0; i != request.num_headers; ++i) {
    std::string header(request.headers[i].name, request.headers[i].name_len);
    std::string header_value(request.headers[i].value, request.headers[i].value_len);

    auto header_name = http::headers_names[header];
    if (header_name != http::H_NONE) {
      auto header_name_string = http::headers_names_strings[header_name];
      Debug::
          logmsg(LOG_DEBUG, "\t%s: %s", header_name_string, header_value.c_str());
    } else {
      //What todo
      Debug::
          logmsg(LOG_DEBUG, "\tUnknown: %s", header_value.c_str());
    }
  }

  return validation::OK;
}

bool StreamManager::init(ListenerConfig &listener_config) {
  listener_config_ = listener_config;
  for (auto service_config = listener_config.services;
       service_config != nullptr;
       service_config = service_config->next) {
    if (service_config->disabled != 1) {
      this->addService(*service_config);
    } else {
      Debug::Log("Backend " + std::string(service_config->name) + " disabled in config file",
                 LOG_NOTICE);
    }
  }
  return true;
}
void StreamManager::clearStream(HttpStream *stream) {
  if (stream == nullptr) {
    return;
  }
  if (stream->client_connection.getFileDescriptor() != BACKEND_STATUS::NO_BACKEND) {
    deleteFd(stream->client_connection.getFileDescriptor());
    stream->client_connection.closeConnection();
    streams_set.erase(stream->backend_connection.getFileDescriptor());
  }
  if (stream->backend_connection.getFileDescriptor() != BACKEND_STATUS::NO_BACKEND) {
    deleteFd(stream->backend_connection.getFileDescriptor());
    stream->backend_connection.closeConnection();
    streams_set.erase(stream->backend_connection.getFileDescriptor());
  }
  delete stream;
}




