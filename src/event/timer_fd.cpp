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

#include "timer_fd.h"
#include "../debug/logger.h"

#define GET_SECONDS(ms) ms / 1000
#define GET_NSECONDS(ms) (ms % 1000) * 1000000

TimerFd::TimerFd(int timeout_ms, bool one_shot) : timeout_ms_(timeout_ms), one_shot_(one_shot) {
  fd_ = ::timerfd_create(CLOCK_MONOTONIC, TFD_CLOEXEC | TFD_NONBLOCK);
  if (fd_ < 0) {
    std::string error = "timerfd_create() failed: ";
    error += std::strerror(errno);
    Logger::LogInfo(error, LOG_ERR);
    throw std::system_error(errno, std::system_category());
  }
  if (timeout_ms > 0) set();
}

bool TimerFd::unset() {
  if (fd_ <= 0) {
    return false;
  }
  itimerspec timer_spec{{0, 0}, {0, 0}};
  ::timerfd_settime(fd_, 0, &timer_spec, nullptr);
  is_set = false;
  return true;
}

bool TimerFd::set(int timeout_ms, bool one_shot) {
  if (fd_ <= 0) return false;
  if (timeout_ms > 0) {
    timeout_ms_ = timeout_ms;
    one_shot_ = one_shot;
  }
  itimerspec timer_spec{};
  timer_spec.it_value.tv_sec = GET_SECONDS(timeout_ms);
  timer_spec.it_value.tv_nsec = GET_NSECONDS(timeout_ms);
  timer_spec.it_interval.tv_sec = one_shot_ ? 0 : timer_spec.it_value.tv_sec;
  timer_spec.it_interval.tv_nsec = one_shot_ ? 0 : timer_spec.it_value.tv_nsec;
  if (::timerfd_settime(fd_, 0, &timer_spec, nullptr) == -1) {
    std::string error = "timerfd_settime() failed: ";
    error += std::strerror(errno);
    Logger::LogInfo(error, LOG_ERR);
    //    throw std::system_error(errno, std::system_category());
    return false;
  }
  is_set = true;
  return true;
}

bool TimerFd::isOneShot() const { return one_shot_; }

TimerFd::~TimerFd() {
  if (fd_ > 0) ::close(fd_);
}

bool TimerFd::isTriggered() {
  size_t s = 0;
  return read(fd_, &s, sizeof(s)) != -1;
}
