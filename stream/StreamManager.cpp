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
          Debug::Log("Connected to backend : " + bck->address + ":" + std::to_string(bck->port), LOG_DEBUG);
        }
        streams_set[fd] = stream;
        streams_set[stream->backend_connection.getFileDescriptor()] = stream;
      }
      switch (event_group) {
        case ACCEPTOR:break;
        case SERVER:break;
        case CLIENT: {
          stream->client_connection.read();
          updateFd(fd, EVENT_TYPE::WRITE, EVENT_GROUP::CLIENT);
          break;
        }
      }
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
        case SERVER:break;
        case CLIENT: {
          auto sent =
              stream->client_connection.write(stream->send_e200.c_str(), stream->send_e200.length() - 1);
          if (sent != stream->send_e200.length() - 1) {
            Debug::Log("Something happend sentid e200", LOG_DEBUG);
          }
          updateFd(fd, READ_ONESHOT, EVENT_GROUP::CLIENT);
          break;
        }
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
      streams_set.erase(stream->client_connection.getFileDescriptor());
      streams_set.erase(stream->backend_connection.getFileDescriptor());
      delete stream;
      break;
    }
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


