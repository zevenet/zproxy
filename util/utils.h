//
// Created by abdess on 4/5/18.
//
#pragma once

#include <pthread.h>
#include <string>
#include <thread>
namespace IO {

enum IO_RESULT {
  ERROR,
  SUCCESS,
  DONE_TRY_AGAIN,
  FD_CLOSED,
  FULL_BUFFER,
};
}

namespace helper {

class ThreadHelper {
 public:
  static bool setThreadAffinity(int cpu_id, pthread_t native_handle) {
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(cpu_id, &cpuset);
    int rc = pthread_setaffinity_np(native_handle,
                                    sizeof(cpu_set_t), &cpuset);
    return rc == 0;
  }

  static bool setThreadName(std::string name, pthread_t native_handle) {
    int rc = pthread_setname_np(native_handle, name.c_str());
    return rc == 0;
  }

  inline static std::string getThreadName(pthread_t native_handle) {
    int rc;
    char thread_name[100];
    rc = pthread_getname_np(native_handle, thread_name, 100);
    return rc != 0 ? "no_name" : std::string(thread_name);
  }

  static void setMaximumFilesLimit(int maximum) {
//    // Increase num file descriptor ulimit
//    //TODO:: take outside main initialization
//    struct rlimit r;
//    getrlimit(RLIMIT_NOFILE, &r);
//    Debug::Log("current::RLIMIT_NOFILE\n\tCurrent " +
//        std::to_string(r.rlim_cur));
//    Debug::Log("\tMaximum " + std::to_string(r.rlim_cur));
//    if (r.rlim_cur != r.rlim_max) {
//      r.rlim_cur = r.rlim_max;
//      if (setrlimit(RLIMIT_NOFILE, &r) == -1) {
//        Debug::logmsg(LOG_ERR, "setrlimit failed ");
//        return EXIT_FAILURE;
//      }
//    }

  }

};
}