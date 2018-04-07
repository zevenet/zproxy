//
// Created by abdess on 4/5/18.
//

#include <thread>
#include "listener.h"
#include "util/utils.h"
void Listener::HandleEvent(int fd, EVENT_TYPE event_type) {
  switch (event_type) {
    case CONNECT: {
      int new_fd = -1;
      do {
        new_fd = listener_connection.doAccept();

      } while (new_fd > 0);
      break;
    }
    default:
      //something very bad happend
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
  for (auto &sm: stream_manager_set) {
    sm->stop();
    delete sm;
  }
}
void Listener::doWork(Listener &listener) {
//TODO::set thread affinty
  while (true) {
    if (!listener.is_running) break;
    if (listener.loopOnce() < 0) {
      //something bad happend
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
  auto thr = std::thread(doWork, std::ref(*this));
  ThreadHelper::setThreadAffinity(0, thr.native_handle());
  ThreadHelper::setThreadName("LISTENER_0", thr.native_handle());
  thr.detach();
};

