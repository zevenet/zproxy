//
// Created by abdess on 4/5/18.
//

#include "StreamManager.h"
#include <functional>
#include "../debug/Debug.h"

void StreamManager::HandleEvent(int fd, EVENT_TYPE event_type) {
  switch (event_type) {
    case READ_ONESHOT: {
      HttpStream *stream = streams_set[fd];
      if (stream == nullptr) {
//        Debug::Log("Stream doesn't exist for " + std::to_string(fd), LOG_DEBUG);
        stream = new HttpStream();
        stream->client_connection.setFileDescriptor(fd);
        streams_set[fd] = stream;
      }
      auto connection = stream->getConnection(fd);
      connection->read();
      updateFd(fd, EVENT_TYPE::WRITE);
      break;
    }

    case READ: {
      HttpStream *stream = streams_set[fd];
      if (stream == nullptr) {
//        Debug::Log("Stream doesn't exist for " + std::to_string(fd), LOG_DEBUG);
        stream = new HttpStream();
        stream->client_connection.setFileDescriptor(fd);
        streams_set[fd] = stream;
      }
      auto connection = stream->getConnection(fd);
      connection->read();
      //connection->write(stream->send_e200.c_str(), stream->send_e200.length());
      updateFd(fd, EVENT_TYPE::WRITE);
      break;
    }

    case WRITE: {
      auto stream = streams_set[fd];
      if (stream == nullptr) {
        Debug::Log("Stream doesn't exist for " + std::to_string(fd));
        return;
      }
      auto connection = stream->getConnection(fd);
      connection->write(stream->send_e200.c_str(), stream->send_e200.length());
      updateFd(fd, READ_ONESHOT);
      break;
    }
    case CONNECT:break;
    case ACCEPT:break;
    case DISCONNECT: {
      auto stream = streams_set[fd];
      if (stream == nullptr) {
        Debug::Log("Stream doesn't exist for " + std::to_string(fd));
        return;
      }
      delete stream;
      streams_set.erase(fd);
      break;
    }
  }
}
void StreamManager::stop() { is_running = false; }

void StreamManager::start(int thread_id_) {
  is_running = true;
  thread_id = thread_id_;
  this->worker = std::thread([this] { doWork(); });
  if (thread_id >= 0) {
    ThreadHelper::setThreadAffinity(thread_id, worker.native_handle());
    ThreadHelper::setThreadName("WORKER_" + std::to_string(thread_id),
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
    if (loopOnce() <= 0) {
      // something bad happend
      Debug::Log("No events!!");
    }
  }
}

void StreamManager::addStream(int fd) {
  if (!this->addFd(fd, READ)) {
    Debug::Log("Error adding to epoll manager", LOG_NOTICE);
  }
}

int StreamManager::getId() { return thread_id; }
