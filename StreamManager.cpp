//
// Created by abdess on 4/5/18.
//

#include <functional>
#include <thread>
#include "StreamManager.h"
#include "util/utils.h"

void StreamManager::HandleEvent(int fd, EVENT_TYPE event_type) {
  switch (event_type) {
    case READ:break;
    case READ_ONESHOT:break;
    case WRITE:break;
    case CONNECT:break;
    case DISCONNECT:break;
    case ACCEPT:break;
  }
}
void StreamManager::stop() {
  is_running = false;
}

void StreamManager::start(int thread_id) {
  is_running = true;
  auto thr = std::thread(doWork, std::ref(*this));
  if (thread_id > 0) {
    ThreadHelper::setThreadAffinity(thread_id, thr.native_handle());
    ThreadHelper::setThreadName("WORKER_" + std::to_string(thread_id), thr.native_handle());
  }
  thr.detach();
}

StreamManager::StreamManager() = default;

StreamManager::~StreamManager() {
  stop();
  for (auto &key_pair: streams) {
    delete key_pair.second;
  }
}
void StreamManager::doWork(StreamManager &sm) {
  //TODO::set thread affinty

  while (true) {
    if (!sm.is_running) break;
    if (sm.loopOnce() < 0) {
      //something bad happend
    }
  }
}
