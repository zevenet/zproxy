//
// Created by abdess on 4/5/18.
//

#include "StreamManager.h"
#include <functional>
#include "../debug/Debug.h"
#include "../util/Network.h"
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

      updateFd(fd, EVENT_TYPE::WRITE, EVENT_GROUP::CLIENT);
    }

    case WRITE: {
      auto stream = streams_set[fd];
      if (stream == nullptr) {
        Debug::Log("Stream doesn't exist for " + std::to_string(fd));
        return;
      }
      auto connection = stream->getConnection(fd);
      auto sent = connection->write(stream->send_e200.c_str(),
                                    stream->send_e200.length());
      if (sent != stream->send_e200.length()) {
        Debug::Log("Something happend sentid e200", LOG_DEBUG);
      }
      updateFd(fd, READ_ONESHOT, EVENT_GROUP::CLIENT);
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
      delete stream;
      streams_set.erase(fd);
      break;
    }
  }
}
#else
void StreamManager::HandleEvent(int fd, EVENT_TYPE event_type, EVENT_GROUP event_group) {
  switch (event_type) {
    case READ:
    case READ_ONESHOT: {
      HttpStream *stream = streams_set[fd];
      if (stream == nullptr) {
        stream = new HttpStream();
        stream->client_connection.setFileDescriptor(fd);
        auto service = getService(stream->request);
        auto bck = service->getBackend(stream->client_connection);
        if (bck == nullptr) {
          //No backend available
          auto response = HttpStatus::getErrorResponse(HttpStatus::Code::ServiceUnavailable);
          stream->client_connection.write(response.c_str(), response.length());
          stream->client_connection.closeConnection();
          return;;
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
        }
        streams_set[fd] = stream;
        streams_set[stream->backend_connection.getFileDescriptor()] = stream;
        addFd(stream->backend_connection.getFileDescriptor(), EVENT_TYPE::READ, EVENT_GROUP::SERVER);
      }

      switch (event_group) {
        case ACCEPTOR:break;
        case SERVER: {
          auto result = stream->backend_connection.read();
          if (result != IO::SUCCESS && result != IO::DONE_TRY_AGAIN) {
            Debug::Log("Error reading response ", LOG_DEBUG);
          }
          size_t parsed = 0;
          auto ret = stream->response.parseResponse(stream->backend_connection.buffer,
                                                    stream->backend_connection.buffer_size,
                                                    &parsed); // parsing http data as response structured
          switch (ret) {
            case http_parser::SUCCESS:
              updateFd(stream->client_connection.getFileDescriptor(),
                       EVENT_TYPE::WRITE,
                       EVENT_GROUP::CLIENT);
              break;
            case http_parser::FAILED:Debug::Log("Parser FAILED", LOG_DEBUG);
              break;
            case http_parser::INCOMPLETE:Debug::Log("Parser INCOMPLETE", LOG_DEBUG);
              break;
            case http_parser::TOOLONG:Debug::Log("Parser TOOLONG", LOG_DEBUG);
              break;
          }

          break;
        }
        case CLIENT: {
          auto result = stream->client_connection.read();
          if (result != IO::SUCCESS && result != IO::DONE_TRY_AGAIN) {
            Debug::Log("Error reading request ", LOG_DEBUG);
          }

          switch (result) {
            case IO::ERROR:break;
            case IO::SUCCESS:break;
            case IO::DONE_TRY_AGAIN:break;
            case IO::FD_CLOSED:break;
            case IO::FULL_BUFFER:break;
          }

          size_t parsed = 0;
          auto ret = stream->request.parseRequest(stream->client_connection.buffer,
                                                  stream->client_connection.buffer_size,
                                                  &parsed); // parsing http data as response structured
          switch (ret) {
            case http_parser::SUCCESS:
              updateFd(stream->backend_connection.getFileDescriptor(),
                       EVENT_TYPE::WRITE,
                       EVENT_GROUP::SERVER);

              break;
            case http_parser::FAILED:Debug::Log("Parser FAILED", LOG_DEBUG);
              break;
            case http_parser::INCOMPLETE:Debug::Log("Parser INCOMPLETE", LOG_DEBUG);
              break;
            case http_parser::TOOLONG:Debug::Log("Parser TOOLONG", LOG_DEBUG);
              break;
          }
          break;
        }
      }
      updateFd(fd, EVENT_TYPE::READ, event_group);
      break;
    }
    case WRITE: {
      auto stream = streams_set[fd];
      if (stream == nullptr) {
        Debug::Log("Stream doesn't exist for " + std::to_string(fd));
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
            updateFd(fd, EVENT_TYPE::ANY, event_group);
            Debug::Log("Error sending data to client", LOG_DEBUG);
          }
          updateFd(stream->client_connection.getFileDescriptor(), EVENT_TYPE::READ, EVENT_GROUP::CLIENT);
          break;
        }
        case CLIENT: {
          auto result = stream->backend_connection.writeTo(stream->client_connection.getFileDescriptor());
          if (result == IO::SUCCESS) {
            updateFd(fd, EVENT_TYPE::READ, event_group);
          } else if (result == IO::DONE_TRY_AGAIN) {
            updateFd(fd, EVENT_TYPE::WRITE, event_group);
          } else {
            updateFd(fd, EVENT_TYPE::ANY, event_group);
            Debug::Log("Error sending data to client", LOG_DEBUG);
          }
          updateFd(stream->backend_connection.getFileDescriptor(), EVENT_TYPE::READ, EVENT_GROUP::SERVER);
          break;
        }
      }
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
          auto response = HttpStatus::getErrorResponse(HttpStatus::Code::ServiceUnavailable);
          stream->client_connection.write(response.c_str(), response.length());
          // Debug::Log("Backend closed connection", LOG_NOTICE);
          streams_set.erase(stream->client_connection.getFileDescriptor());
          break;
        }
        case CLIENT: {
          //Debug::Log("Client closed connection", LOG_NOTICE);

          if (stream->backend_connection.getFileDescriptor() != BACKEND_STATUS::NO_BACKEND) {
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




