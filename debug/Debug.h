#ifndef DEBUG_H
#define DEBUG_H

#include <sys/syslog.h>
#include <cstdarg>
#include <cstring>
#include <iostream>
#include <mutex>
#include <string>
#include <thread>
#include <type_traits>
#include <iomanip>
#include <sstream>
#include "../util/utils.h"

//#define DEBUG_LEVEl 8
#define LOGFACILITY -1

#define LOG_REMOVE LOG_DEBUG //TODO:: REMOVE

#define MAXBUF 4096

//#ifdef MISS_FACILITYNAMES
#if 1
/* This is lifted verbatim from the Linux sys/syslog.h */

typedef struct _code {
  const char *c_name;
  int c_val;
} CODE;

static CODE facilitynames[] = {
    {"auth", LOG_AUTH},
#ifdef LOG_AUTHPRIV
    {"authpriv", LOG_AUTHPRIV},
#endif
    {"cron", LOG_CRON}, {"daemon", LOG_DAEMON},
#ifdef LOG_FTP
    {"ftp", LOG_FTP},
#endif
    {"kern", LOG_KERN}, {"lpr", LOG_LPR},
    {"mail", LOG_MAIL}, {"mark", 0},            /* never used! */
    {"news", LOG_NEWS}, {"security", LOG_AUTH}, /* DEPRECATED */
    {"syslog", LOG_SYSLOG}, {"user", LOG_USER},
    {"uucp", LOG_UUCP}, {"local0", LOG_LOCAL0},
    {"local1", LOG_LOCAL1}, {"local2", LOG_LOCAL2},
    {"local3", LOG_LOCAL3}, {"local4", LOG_LOCAL4},
    {"local5", LOG_LOCAL5}, {"local6", LOG_LOCAL6},
    {"local7", LOG_LOCAL7}, {NULL, -1}};
#endif

#define Log(...) \
Debug::Log2(__FILENAME__ ,__FUNCTION__, __LINE__ , __VA_ARGS__)

#define logmsg(...) \
Debug::logmsg2(__FILENAME__ ,__FUNCTION__, __LINE__ , __VA_ARGS__)

#define COUT_GREEN_COLOR(x)  "\033[1;32m"+ x + "\033[0m"

class Debug {
 public:
  static int log_level;
  static std::mutex log_lock;
  inline static void Log2(const std::string file,
                          const std::string function,
                          int line,
                          const std::string &str,
                          int level = -1) {
    if (level > log_level) {
      return;
    }
    std::lock_guard<std::mutex> locker(log_lock);
    if (log_level > 7) {
      std::stringstream buffer;
      buffer << "["
             << helper::ThreadHelper::getThreadName(pthread_self())
             << "]["
             << file << ":" /*<< function << ":" */<< line << "] ";
      std::cout << std::left << std::setfill('.') << std::setw(60) << buffer.str() << "\033[1;32m";
    }

    if (log_level > 7) {
      //std::cout << "\033[0m";
      std::cout << COUT_GREEN_COLOR(str);
    } else {
      std::cout << str;
    }
    std::cout << std::endl;
  }

  static
  void logmsg2(const std::string file,
               const std::string function,
               int line, const int priority, const char *fmt, ...) {
    if (priority > log_level) {
      return;
    }
    char buf[MAXBUF + 1];
    va_list ap;
    struct tm *t_now;
    struct tm t_res{};
    bool print_log = false;
    buf[MAXBUF] = '\0';
    ::va_start(ap, fmt);
    ::vsnprintf(buf, MAXBUF, fmt, ap);
    va_end(ap);
    if (LOGFACILITY == -1) {
      //      if (name)
      //        fprintf(
      //            (priority == LOG_INFO || priority == LOG_DEBUG) ? stdout :
      //            stderr,
      //            "%s, %s\n", name, buf);
      //      else
      Log2(file, function, line, std::string(buf), priority);
    } else {
      //      if (print_log)
      Log(std::string(buf));
      //      else /*if (name)*/
      //        syslog(LOGFACILITY | priority, "%s, %s\n", name, buf);
    }
  }
};

#endif  // DEBUG_H
