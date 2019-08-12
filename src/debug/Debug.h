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

#define LOG_REMOVE LOG_DEBUG

#define MAXBUF 4096

#ifndef SYSLOG_NAMES

//from sys/syslog.h
#define    INTERNAL_NOPRI    0x10    /* the "no priority" priority */
/* mark "facility" */
#define    INTERNAL_MARK    LOG_MAKEPRI(LOG_NFACILITIES << 3, 0)
typedef struct _code {
  const char *c_name;
  int c_val;
} CODE;

static CODE prioritynames[] =
    {
        {"alert", LOG_ALERT},
        {"crit", LOG_CRIT},
        {"debug", LOG_DEBUG},
        {"emerg", LOG_EMERG},
        {"err", LOG_ERR},
        {"error", LOG_ERR},        /* DEPRECATED */
        {"info", LOG_INFO},
        {"none", INTERNAL_NOPRI},        /* INTERNAL */
        {"notice", LOG_NOTICE},
        {"panic", LOG_EMERG},        /* DEPRECATED */
        {"warn", LOG_WARNING},        /* DEPRECATED */
        {"warning", LOG_WARNING},
        {nullptr, -1}
    };

static CODE facilitynames[] =
    {
        {"auth", LOG_AUTH},
        {"authpriv", LOG_AUTHPRIV},
        {"cron", LOG_CRON},
        {"daemon", LOG_DAEMON},
        {"ftp", LOG_FTP},
        {"kern", LOG_KERN},
        {"lpr", LOG_LPR},
        {"mail", LOG_MAIL},
        {"mark", INTERNAL_MARK},        /* INTERNAL */
        {"news", LOG_NEWS},
        {"security", LOG_AUTH},        /* DEPRECATED */
        {"syslog", LOG_SYSLOG},
        {"user", LOG_USER},
        {"uucp", LOG_UUCP},
        {"local0", LOG_LOCAL0},
        {"local1", LOG_LOCAL1},
        {"local2", LOG_LOCAL2},
        {"local3", LOG_LOCAL3},
        {"local4", LOG_LOCAL4},
        {"local5", LOG_LOCAL5},
        {"local6", LOG_LOCAL6},
        {"local7", LOG_LOCAL7},
        {nullptr, -1}
    };

#endif

#define LogInfo(...) Debug::Log2(__FILENAME__, __FUNCTION__, __LINE__, __VA_ARGS__)

#define logmsg(...) \
  Debug::logmsg2(__FILENAME__, __FUNCTION__, __LINE__, __VA_ARGS__)

#define COUT_GREEN_COLOR(x) "\e[1;32m" + x + "\e[0m"
#define COUT_BLUE_COLOR(x) "\e[1;32m" + x + "\e[0m"
#include "fstream"
#include <unistd.h>
class Debug {
public:
  static int log_level;
  static int log_facility;
  static std::mutex log_lock;
  static void process_mem_usage(double& vm_usage, double& resident_set)
  {
      vm_usage     = 0.0;
      resident_set = 0.0;

      // the two fields we want
      unsigned long vsize;
      long rss;
      {
          std::string ignore;
          std::ifstream ifs("/proc/self/stat", std::ios_base::in);
          ifs >> ignore >> ignore >> ignore >> ignore >> ignore >> ignore >> ignore >> ignore >> ignore >> ignore
              >> ignore >> ignore >> ignore >> ignore >> ignore >> ignore >> ignore >> ignore >> ignore >> ignore
              >> ignore >> ignore >> vsize >> rss;
      }

      long page_size_kb = sysconf(_SC_PAGE_SIZE) / 1024; // in case x86-64 is configured to use 2MB pages
      vm_usage = vsize / 1024.0;
      resident_set = rss * page_size_kb;
  }
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
        fprintf(stdout, "%s\n", str.c_str());
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
      std::vsnprintf(const_cast<char *>(s.data()), s.size(), fmt, args);
      va_end(args);
      Log2(file, function, line, s, priority);
    }
  }
};
