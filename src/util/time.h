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

#include <sys/time.h>

#include <cstdio>
#include <ctime>

#define SHOW_LOG_TIMESTAMP 0

#define TV_TO_MS(x) (x.tv_sec * 1000.0 + x.tv_usec / 1000.0)
#define TV_TO_S(x) (x.tv_sec + x.tv_usec / 1000000.0);

struct Time {
  inline static thread_local timeval current_time;
#if SHOW_LOG_TIMESTAMP
  inline static thread_local char current_time_str[128];
#endif
  inline static void updateTime(){
    ::gettimeofday (&Time::current_time, nullptr);
    milliseconds = TV_TO_MS(current_time);
#if SHOW_LOG_TIMESTAMP
    std::tm* time_info = std::localtime(&current_time.tv_sec);
    int string_size =
        ::strftime(current_time_str, sizeof(current_time_str), "%Y-%m-%d %H:%M:%S", time_info);
    string_size +=
        std::snprintf(current_time_str + string_size, sizeof(current_time_str) - string_size,
                      ".%03d", current_time.tv_usec);
    current_time_str[string_size] = '\0';
#endif
  }

  inline static void getTime(timeval& time_val) {
    time_val.tv_sec = current_time.tv_sec;
    time_val.tv_usec = current_time.tv_usec;
  }

  inline static time_t getTimeSec(){
    return TV_TO_S(current_time);
  }

  inline static double getTimeMs(){
   return milliseconds;
  }

  inline static double getDiff(const timeval & start_point){
    return (milliseconds - TV_TO_MS(start_point))/1000.0;
  }

  inline static double getElapsed(const timeval& start_point) {
    timeval result{};
    result.tv_sec = current_time.tv_sec - start_point.tv_sec;
    result.tv_usec = current_time.tv_usec - start_point.tv_usec;
    /* Return 1 if result is negative. */
    return TV_TO_S(result);
  }

 private:
  inline static thread_local double milliseconds;
};
