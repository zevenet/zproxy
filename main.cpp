#include <sys/resource.h>
#include <iostream>
#include "debug/Debug.h"
#include "stream/listener.h"

std::mutex Debug::log_lock;

int initListener() {
  Debug::Log("Zhttp starting");

  // Increase num file descriptor ulimit
  struct rlimit r;
  getrlimit(RLIMIT_NOFILE, &r);
  Debug::Log("current::RLIMIT_NOFILE\n\tCurrent " +
      std::to_string(r.rlim_cur));
  Debug::Log("\tMaximum " + std::to_string(r.rlim_cur));
  if (r.rlim_cur != r.rlim_max) {
    r.rlim_cur = r.rlim_max;
    if (setrlimit(RLIMIT_NOFILE, &r) == -1) {
      Debug::logmsg(LOG_ERR, "setrlimit failed ");
      return EXIT_FAILURE;
    }
  }
  Debug::Log("SetUlimit::RLIMIT_NOFILE\n\tCurrent " +
      std::to_string(r.rlim_cur));
  Debug::Log("\tMaximum " + std::to_string(r.rlim_cur));

  Listener listener;
  listener.init("127.0.0.1", 9999);
  listener.start();
  //  getchar();

}

int main() {
//  test_runner::test_stringBuffer();
  return initListener();
}
