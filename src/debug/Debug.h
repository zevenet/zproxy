#pragma once

#include <cstdlib>
#include <cstdarg>
#include <cstring>
#include <iomanip>
#include <iostream>
#include <mutex>
#include <sstream>
#include <string>
#include <thread>
#include <type_traits>
#include <syslog.h>
#include "../util/utils.h"

#ifndef __FILENAME__
#define __FILENAME__ (strrchr(__FILE__, '/') ? strrchr(__FILE__, '/') + 1 : __FILE__)
#endif
#define LOG_REMOVE LOG_DEBUG

#define MAXBUF 4096

#define LogInfo(...) Debug::Log2(__FILENAME__, __FUNCTION__, __LINE__, __VA_ARGS__)

#define logmsg(...) \
  Debug::logmsg2(__FILENAME__, __FUNCTION__, __LINE__, __VA_ARGS__)

#define COUT_GREEN_COLOR(x) ("\e[1;32m" + (x) + "\e[0m")
#define COUT_BLUE_COLOR(x) ("\e[1;32m" + (x) + "\e[0m")
#include "fstream"
#include <unistd.h>
class Debug {
public:
  static int log_level;
  static int log_facility;
  static std::mutex log_lock;

  inline static void Log2(const std::string &file, const std::string &function,
                          int line, const std::string &str,
                          int level = LOG_NOTICE) {
    if (level > log_level) {
      return;
    }
    std::lock_guard<std::mutex> locker(log_lock);
    if (log_level >= LOG_DEBUG) {
      std::stringstream buffer;
      buffer << "[" << helper::ThreadHelper::getThreadName(pthread_self())
             << "][" << file << ":" << line << " (" << COUT_BLUE_COLOR(function) << ") " "] ";
      std::cout << std::left << std::setfill('.') << std::setw(80)
                << buffer.str() << "\033[1;32m";
    }

    if (log_level >= LOG_DEBUG) {
      // std::cout << "\033[0m";
      std::cout << COUT_GREEN_COLOR(str);
    } else {
      if (log_facility == -1) {
        fprintf(stdout, "%s", str.c_str());
      } else {
        syslog(level, "%s", str.c_str());
      }
    }
    std::cout << std::endl;
  }

  static void logmsg2(const std::string &file, const std::string &function,
                      int line, const int priority, const char *fmt, ...) {
    if (priority > log_level) {
      return;
    }
    va_list args;
    va_start(args, fmt);
    char buf[1024 * 4];
    size_t n = std::vsnprintf(buf, sizeof(buf), fmt, args);
    va_end(args);

    // Static buffer large enough?
    if (n < sizeof(buf)) {
      Log2(file, function, line, std::string(buf, n), priority);
    } else {
      // Static buffer too small
      std::string s(n + 1, 0);
      va_start(args, fmt);
      std::vsnprintf(s.data(), s.size(), fmt, args);
      va_end(args);
      Log2(file, function, line, s, priority);
    }
  }
};
