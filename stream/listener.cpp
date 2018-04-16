//
// Created by abdess on 4/5/18.
//

#include "listener.h"
#include "../debug/Debug.h"

void Listener::HandleEvent(int fd, EVENT_TYPE event_type, EVENT_GROUP event_group) {
  switch (event_type) {
    case CONNECT: {
      int new_fd;
      do {
        new_fd = listener_connection.doAccept();
        if (new_fd > 0) {
          auto sm = getManager(new_fd);
          if (sm != nullptr) {
            sm->addStream(new_fd);
          } else {
            Debug::Log("StreamManager not found");
          }
        }
      } while (new_fd > 0);
      break;
    }
      //    case READ: {
      //      Connection cnt;
      //      cnt.setFileDescriptor(fd);
      //      cnt.read();
      //      //      Debug::Log(cnt.string_buffer.string());
      //      std::string send_e200 =
      //          "HTTP/1.1 200 OK\r\nContent-Length: 11\r\n\r\nHello World";
      //      cnt.write(send_e200.c_str(), send_e200.length());
      //    } break;
    default:Debug::Log("###################Why!!!!!!!! "); //TODO::REMOVE
      break;
  }
}

bool Listener::init(std::string address, int port) {
  if (!listener_connection.listen(address, port)) return false;
  return handleAccept(listener_connection.socket_fd);
}

Listener::Listener()
    : listener_connection(), stream_manager_set(), is_running(false) {
  auto concurrency_lever = std::thread::hardware_concurrency() - 1;
  for (int sm = 0; sm < concurrency_lever; sm++) {
    stream_manager_set[sm] = new StreamManager();
  }
}

Listener::~Listener() {
  is_running = false;
  for (auto &sm : stream_manager_set) {
    sm.second->stop();
    delete sm.second;
  }
  worker_thread.join();
}

void Listener::doWork() {
  while (is_running) {
    if (loopOnce(0) <= 0) {
      // something bad happend
      Debug::Log("No event received");
    }
  }
}

void Listener::stop() { is_running = false; }

void Listener::start() {
  for (int i = 0; i < stream_manager_set.size(); i++) {
    auto sm = stream_manager_set[i];
    if (sm != nullptr) {
//      sm->addBackend("192.168.101.253", 80);
//      sm->addBackend("192.168.101.254", 80);
      sm->addBackend("0.0.0.0", 7777);
      sm->start(i);
    } else {
      Debug::Log("StreamManager id doesn't exist : " + std::to_string(i), LOG_ERR);
    }
  }
  is_running = true;
  //  worker_thread = std::thread([this] { doWork(); });
  helper::ThreadHelper::setThreadAffinity(
      0, pthread_self());  // worker_thread.native_handle());
  helper::ThreadHelper::setThreadName("LISTENER", pthread_self());
  doWork();
}

StreamManager *Listener::getManager(int fd) {
  static unsigned long c;
  ++c;
  unsigned long id = c % stream_manager_set.size();
  return stream_manager_set[id];
};
