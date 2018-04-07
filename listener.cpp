//
// Created by abdess on 4/5/18.
//

#include <thread>
#include "listener.h"
#include "debug/Debug.h"

void Listener::HandleEvent(int fd, EVENT_TYPE event_type) {
  switch (event_type) {
    case CONNECT: {
      int new_fd = -1;
      do {
        new_fd = listener_connection.doAccept();
        if (new_fd > 0) {
          addFd(new_fd, READ);
//          auto sm = getManager(new_fd);
//          if (sm != nullptr) {
//            Debug::Log("Assigned Connection to: " + std::to_string(sm->getId()));
//            sm->addStream(new_fd);
//          } else {
//            Debug::Log("StreamManager not found");
//          }
        }
      } while (new_fd > 0);
      break;
    }
    default:Debug::Log("Why!!!!!!!! ");
      break;
  }
}

bool Listener::init(std::string address, int port) {
  if (!listener_connection.listen(address, port)) return false;
  return handleAccept(listener_connection.socket_fd);
}

Listener::Listener() : listener_connection(), stream_manager_set(), is_running(false) {
  auto concurrency_lever = std::thread::hardware_concurrency() - 1;
  for (int sm = 0; sm < concurrency_lever; sm++) {
    stream_manager_set.push_back(new StreamManager());
  }
}

Listener::~Listener() {
  is_running = false;
  for (auto &sm: stream_manager_set) {
    sm->stop();
    delete sm;
  }
  worker_thread.join();
}

void Listener::doWork(Listener &listener) {
  while (listener.is_running) {
    if (listener.loopOnce() < 0) {
      //something bad happend
      Debug::Log("No event received");
    }
  }
}

void Listener::stop() {
  is_running = false;
}

void Listener::start() {

  for (int i = 1; i < stream_manager_set.size(); i++) {
    stream_manager_set[i]->start(i);
  }
  is_running = true;
  worker_thread = std::thread(doWork, std::ref(*this));
  doWork(*this);
//  //set thread affinty
//  ThreadHelper::setThreadAffinity(0, thr.native_handle());
//  ThreadHelper::setThreadName("LISTENER_0", thr.native_handle());
}

StreamManager *Listener::getManager(int fd) {
  static int c = c++ % stream_manager_set.size();
  Debug::Log("Need stream manager id: " + std::to_string(c));
  return stream_manager_set[c];

};

