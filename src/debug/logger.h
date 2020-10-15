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

#include <syslog.h>
#include <unistd.h>
#include <cstdarg>
#include <cstdlib>
#include <cstring>
#include <iomanip>
#include <iostream>
#include <map>
#include <mutex>
#include <sstream>
#include <string>
#include <thread>
#include <type_traits>

#include "../util/utils.h"
#include <fstream>
#include "../util/time.h"


#define MAXBUF 4096
#define LOG_REMOVE LOG_DEBUG
#if LOGGER_DEBUG
#ifndef __FILENAME__
#define __FILENAME__ (strrchr(__FILE__, '/') ? strrchr(__FILE__, '/') + 1 : __FILE__)
#endif
#define LogInfo(...) Logger::Log2(__FILENAME__, __FUNCTION__, __LINE__, __VA_ARGS__)
#define logmsg(...) Logger::logmsg2(__FILENAME__, __FUNCTION__, __LINE__, __VA_ARGS__)
#define COUT_GREEN_COLOR(x) ("\e[1;32m" + (x) + "\e[0m")
#define COUT_BLUE_COLOR(x) ("\e[1;32m" + (x) + "\e[0m")
#else
#define LogInfo(...) Logger::Log2(__VA_ARGS__)
#define logmsg(...) Logger::logmsg2(__VA_ARGS__)
#endif

struct thread_info {
  std::string_view farm_name, service_name;
  int backend_id;
};

class Logger {
 public:
  static int log_level;
  static int log_facility;
  static std::mutex log_lock;
  static std::map<std::thread::id, thread_info> log_info;

  inline static void init_log_info() {
    log_info.insert({std::this_thread::get_id(), thread_info({std::string_view(), std::string_view(), -1})});
  }
  inline static void Log2(
#if LOGGER_DEBUG
      const std::string &file, const std::string &function, int line,
#endif
      const std::string &str, int level = LOG_NOTICE) {
    if (level > log_level) {
      return;
    }
    std::string buffer;
#if LOGGER_DEBUG
    if (log_level >= LOG_DEBUG) {
      buffer += "[";
      buffer += helper::ThreadHelper::getThreadName(pthread_self());
      buffer += "][";
      buffer += file;
      buffer += ":";
      buffer += std::to_string(line);
      buffer += " (";
      buffer += COUT_GREEN_COLOR(function);
      buffer += ")] ";
      //        buffer += "\033[1;32m";
      //<< std::left << std::setfill('.')
      //              << std::setw(80)
      //        buffer += COUT_GREEN_COLOR(log_tag);
      //        buffer += COUT_GREEN_COLOR(str);
    }
#endif
    auto it = log_info.find(std::this_thread::get_id());
    if (it != log_info.end() && !it->second.farm_name.empty()) {
      buffer += "(";
      buffer += it->second.farm_name;
      if (!it->second.service_name.empty()) {
        buffer += ",";
        buffer += log_info[std::this_thread::get_id()].service_name;
        if (it->second.backend_id != -1) {
          buffer += ",";
          buffer += std::to_string(it->second.backend_id);
        }
      }
      buffer += ") ";
    }
    std::lock_guard<std::mutex> locker(log_lock);
    if (log_facility == -1) {
#if SHOW_LOG_TIMESTAMP
      fprintf(stdout, "%s %s %s\n", Time::current_time_str, buffer.data(), str.data());
#else
      fprintf(stdout, "%s %s\n", buffer.data(), str.data());
#endif
      fflush(stdout);
    } else {
#if SHOW_LOG_TIMESTAMP
      syslog(level, "%s %s %s", Time::current_time_str, buffer.data(), str.data());
#else
      syslog(level, "%s %s", buffer.data(), str.data());
#endif
    }

    //    fflush(stdout);
  }

  static void logmsg2(
#if LOGGER_DEBUG
      const std::string &file, const std::string &function, int line,
#endif
      const int priority, const char *fmt, ...) {
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
      Log2(
#if LOGGER_DEBUG
          file, function, line,
#endif
          std::string(buf, n), priority);
    } else {
      // Static buffer too small
      std::string s(n + 1, 0);
      va_start(args, fmt);
      std::vsnprintf(s.data(), s.size(), fmt, args);
      va_end(args);
      Log2(
#if LOGGER_DEBUG
          file, function, line,
#endif
          s, priority);
    }
  }
};
