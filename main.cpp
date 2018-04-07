#include <iostream>
#include "debug/Debug.h"
#include "listener.h"

std::mutex Debug::log_lock;

int main() {
  Debug::Log("Zhttp starting");
  Listener listener;
  listener.init("0.0.0.0", 7777);
  listener.start();
  getchar();
  return 0;
}