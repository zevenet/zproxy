//
// Created by abdess on 5/7/18.
//
#pragma once

#include <sys/timerfd.h>
#include <unistd.h>
#include "../event/descriptor.h"
using namespace events;
class TimerFd : public Descriptor {
  bool one_shot_;
  int timeout_ms_;
 public:
  virtual ~TimerFd();
  explicit TimerFd(int timeout_ms = -1, bool one_shot = true);
  bool set(int timeout_ms = -1, bool one_shot = true);
  bool unset();
  bool isOneShot() const;
  bool isTriggered();
  bool is_set;
};
