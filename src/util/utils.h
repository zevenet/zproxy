/*
 *    Zevenet zproxy Load Balancer Software License
 *    This file is part of the Zevenet zproxy Load Balancer software package.
 *
 *    Copyright (C) 2019-today ZEVENET SL, Sevilla (Spain)
 *
 *    This program is free software: you can redistribute it and/or modify
 *    it under the terms of the GNU Affero General Public License as
 *    published by the Free Software Foundation, either version 3 of the
 *    License, or any later version.
 *
 *    This program is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *    GNU Affero General Public License for more details.
 *
 *    You should have received a copy of the GNU Affero General Public License
 *    along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 */
#pragma once

#include "../http/pico_http_parser.h"
#include <cstring>
#include <iomanip>
#include <iostream>
#include <pthread.h>
#include <sstream>
#include <string>
#include <string_view>
#include <thread>

namespace IO {

enum class IO_RESULT {
  ERROR,
  SUCCESS,
  DONE_TRY_AGAIN,
  ZERO_DATA,
  FD_CLOSED,
  FULL_BUFFER,
  CANCELLED,
  SSL_NEED_HANDSHAKE,
  SSL_HANDSHAKE_ERROR,
  SSL_WANT_RENEGOTIATION,
  // SSL_HANDSHAKE_START,
  // SSL_HANDSHAKE_DONE,

};

inline std::string getResultString(IO_RESULT result) {
  switch (result) {
  case IO_RESULT::ERROR:
    return "ERROR";
  case IO_RESULT::SUCCESS:
    return "SUCCESS";
  case IO_RESULT::DONE_TRY_AGAIN:
    return "DONE_TRY_AGAIN";
  case IO_RESULT::ZERO_DATA:
    return "ZERO_DATA";
  case IO_RESULT::FD_CLOSED:
    return "FD_CLOSED";
  case IO_RESULT::FULL_BUFFER:
    return "FULL_BUFFER";
  case IO_RESULT::CANCELLED:
    return "CANCELLED";
  case IO_RESULT::SSL_NEED_HANDSHAKE:
    return "SSL_NEED_HANDSHAKE";
  case IO_RESULT::SSL_HANDSHAKE_ERROR:
    return "SSL_HANDSHAKE_ERROR";
  case IO_RESULT::SSL_WANT_RENEGOTIATION:
    return "SSL_WANT_RENEGOTIATION";
  // case  IO_RESULT::SSL_HANDSHAKE_START: return "// SSL_HANDSHAKE_START";
  // case  IO_RESULT::SSL_HANDSHAKE_DONE: return "// SSL_HANDSHAKE_DONE";
  default:
    return "result reason not found";
  }
}

enum class IO_OP {
  OP_ERROR,
  OP_SUCCESS,
  OP_IN_PROGRESS,
};
} // namespace IO

namespace helper {
/*
 * return true if c is CR (carriage return) or LF (line feed)
*/
inline bool isCRorLF(char c){ return c == '\n' || c == '\r'; }

inline bool stringEqual(const std::string &str1, const std::string &str2) {
  if (str1.size() == str2.size() /*&& str1[0] == str2[0]*/ &&
      std::strncmp(str1.c_str(), str2.c_str(), str1.length()) == 0) {
    return true;
  }
  return false;
}

template <class Container>
void splitString(const std::string &str, Container &cont, char delim) {
  std::stringstream ss(str);
  std::string token;
  while (std::getline(ss, token, delim)) {
    cont.push_back(token);
  }
}

inline bool headerEqual(const phr_header &header,
                        const std::string &header_name) {
  if (header.name == nullptr)
    return false;
  if (header.name_len != header_name.size() || header.name[0] != header_name[0])
    return false;
  return std::strncmp(header.name, header_name.c_str(), header.name_len) == 0;
}

template <typename T> T try_lexical_cast(const std::string &s, T &out) {
  std::stringstream ss(s);
  return !((ss >> out).fail() || !(ss >> std::ws).eof());
}

struct DateTime {
  inline static std::string getDayTime() {
    auto now = std::time(nullptr);
    return std::ctime(&now);
  }
};

struct ThreadHelper {
  static bool setThreadAffinity(int cpu_id, pthread_t native_handle) {
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(cpu_id, &cpuset);
    int rc = pthread_setaffinity_np(native_handle, sizeof(cpu_set_t), &cpuset);
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
    //    // Increase num file descriptor ulimit    //
    //    struct rlimit r;
    //    getrlimit(RLIMIT_NOFILE, &r);
    //    Logger::LogInfo("current::RLIMIT_NOFILE\n\tCurrent " +
    //        std::to_string(r.rlim_cur));
    //    Logger::LogInfo("\tMaximum " + std::to_string(r.rlim_cur));
    //    if (r.rlim_cur != r.rlim_max) {
    //      r.rlim_cur = r.rlim_max;
    //      if (setrlimit(RLIMIT_NOFILE, &r) == -1) {
    //        Logger::logmsg(LOG_ERR, "setrlimit failed ");
    //        return EXIT_FAILURE;
    //      }
    //    }
  }
};
} // namespace helper

namespace conversionHelper {
template <typename T>
std::string toStringWithPrecision(const T a_value, const int n = 4) {
  std::ostringstream out;
  out.precision(n);
  out << std::fixed << a_value;
  return out.str();
}
} // namespace conversionHelper

namespace time_helper {
    inline struct std::tm strToStruct(const std::string &str_date) {
      std::stringstream ss(str_date);
      std::tm tm = {};
      ss >> std::get_time(&tm, "%a, %d %b %Y %H:%M:%S GMT");
      return tm;
    }

    inline time_t strToTime(const std::string &str_date) {
      std::tm tm = strToStruct(str_date);
      return std::mktime(&tm);
    };

    inline time_t gmtTimeNow() {
      time_t now = std::time(&now);
      now = std::mktime(gmtime(&now));
      return now;
    };

    inline std::string strTimeNow() {
      time_t now = gmtTimeNow();
      char buff[30];
      strftime(buff, 30, "%a, %d %b %Y %H:%M:%S GMT", localtime(&now));
      std::string str_time_now(buff, 30);
      return str_time_now;
    }

    inline std::string strTime( time_t time) {
      char buff[30];
      strftime(buff, 30, "%a, %d %b %Y %H:%M:%S GMT", localtime(&time));
      std::string str_time(buff, 30);
      return str_time;
    }

    inline std::time_t getAge(time_t creation) { return gmtTimeNow() - creation; }
}
