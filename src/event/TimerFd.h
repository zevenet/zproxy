//
// Created by abdess on 5/7/18.
//
#pragma once

#include <sys/timerfd.h>
#include <unistd.h>

class TimerFd {
  int timer_fd_;
  bool one_shot_;
  int timeout_ms_;

 public:
  ~TimerFd();
  TimerFd(int timeout_ms = -1, bool one_shot = true);
  bool set(int timeout_ms = -1, bool one_shot = true);
  bool unset();  // TODO: Fix me
  bool isOneShot() const;
  bool isTriggered();  // TODO: Fix me
  int getFileDescriptor() const;
};
