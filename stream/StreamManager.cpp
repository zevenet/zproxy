//
// Created by abdess on 4/5/18.
//

#include "StreamManager.h"
#include <functional>
#include "../debug/Debug.h"
#include "../util/Network.h"

void StreamManager::HandleEvent(int fd, EVENT_TYPE event_type, EVENT_GROUP event_group) {
  switch (event_type) {
    case READ:
    case READ_ONESHOT: {
      HttpStream *stream = streams_set[fd];
      if (stream == nullptr) {
        stream = new HttpStream();
        stream->client_connection.setFileDescriptor(fd);
        auto bck = getBackend();
        if (!stream->backend_connection.doConnect(*bck->address_info, bck->timeout)) {
          Debug::Log("Error connecting to backend " + bck->address, LOG_NOTICE); //TODO:: respond e503
          stream->backend_connection.closeConnection();
          return;
        } else {
          Network::setSocketNonBlocking(stream->backend_connection.getFileDescriptor());
          Debug::Log("Connected to backend : " + bck->address + ":" + std::to_string(bck->port), LOG_DEBUG);
        }
        streams_set[fd] = stream;
        streams_set[stream->backend_connection.getFileDescriptor()] = stream;
        addFd(stream->backend_connection.getFileDescriptor(), EVENT_TYPE::READ, EVENT_GROUP::SERVER);
      }
      switch (event_group) {
        case ACCEPTOR:break;
        case SERVER: {
          auto result = stream->backend_connection.read();
          if (result != IO::SUCCESS && result != IO::FD_BLOCKED) {
            Debug::Log("Erorr reading response ", LOG_DEBUG);
          }

          updateFd(stream->client_connection.getFileDescriptor(), EVENT_TYPE::WRITE, EVENT_GROUP::CLIENT);
          break;
        }
        case CLIENT: {
          auto result = stream->client_connection.read();
          if (result != IO::SUCCESS && result != IO::FD_BLOCKED) {
            Debug::Log("Erorr reading request ", LOG_DEBUG);
          }
          updateFd(stream->backend_connection.getFileDescriptor(), EVENT_TYPE::WRITE, EVENT_GROUP::SERVER);
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
          } else if (result == IO::FD_BLOCKED) {
            updateFd(fd, EVENT_TYPE::WRITE, event_group);
          } else {
            updateFd(fd, EVENT_TYPE::ANY, event_group);
            Debug::Log("Erorr sending data to client", LOG_DEBUG);
          }
          updateFd(stream->client_connection.getFileDescriptor(), EVENT_TYPE::READ, EVENT_GROUP::CLIENT);
          break;
        }
        case CLIENT: {
          auto result = stream->backend_connection.writeTo(stream->client_connection.getFileDescriptor());
          if (result == IO::SUCCESS) {
            updateFd(fd, EVENT_TYPE::READ, event_group);
          } else if (result == IO::FD_BLOCKED) {
            updateFd(fd, EVENT_TYPE::WRITE, event_group);
          } else {
            updateFd(fd, EVENT_TYPE::ANY, event_group);
            Debug::Log("Erorr sending data to client", LOG_DEBUG);
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
        Debug::Log("Stream doesn't exist for " + std::to_string(fd));
        ::close(fd);
        return;
      }
      streams_set.erase(fd);
      streams_set.erase(stream->client_connection.getFileDescriptor());
      streams_set.erase(stream->backend_connection.getFileDescriptor());
      delete stream;
      break;
    }
    default: Debug::Log("Unexpected  event type", LOG_DEBUG);
  }
}
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

void StreamManager::addBackend(std::string address, int port) {
  static int backend_id;
  backend_id++;
  BackendConfig config;
  config.address_info = Network::getAddress(address, port);
  if (config.address_info != nullptr) {
    config.address = address;
    config.port = port;
    config.backen_id = backend_id;
    config.timeout = 0;
    backend_set.push_back(config);
  } else {
    Debug::Log("Backend Configuration not valid ", LOG_NOTICE);
  }
}

BackendConfig *StreamManager::getBackend() {
  static unsigned int seed;
  seed++;
  return &backend_set[seed % backend_set.size()];
}


