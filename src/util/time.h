//
// Created by abdess on 3/5/20.
//

#pragma once

#include <sys/time.h>

#define TV_TO_MS(x) (x.tv_sec * 1000.0 + x.tv_usec/1000.0)
#define TV_TO_S(x) (x.tv_sec  + x.tv_usec/1000000.0);

struct Time {
  inline static thread_local timeval current_time;
  inline static void updateTime(){
    ::gettimeofday (&Time::current_time, nullptr);
    milliseconds = TV_TO_MS(current_time);
  }
  inline static void getTime(timeval &time_val){
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

 private:
  inline static thread_local double milliseconds;
};



