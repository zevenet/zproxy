//
// Created by abdess on 5/7/18.
//

#include "TimerFd.h"
#include "../debug/Debug.h"

#define GET_SECONDS(ms) ms / 1000
#define GET_NSECONDS(ms) (ms % 1000) * 1000000

TimerFd::TimerFd(int timeout_ms, bool one_shot)
    : timeout_ms_(timeout_ms), one_shot_(one_shot) {
  timer_fd_ = ::timerfd_create(CLOCK_MONOTONIC, TFD_CLOEXEC | TFD_NONBLOCK);
  if (timer_fd_ < 0) {
    std::string error = "timerfd_create() failed: ";
    error += std::strerror(errno);
    Debug::Log(error, LOG_ERR);
    throw std::system_error(errno, std::system_category());
  }
  if (timeout_ms > 0) set();
}

bool TimerFd::unset() {
  if (timer_fd_ <= 0) {
    return false;
  }
  itimerspec timer_spec{{0, 0}, {0, 0}};
  ::timerfd_settime(timer_fd_, 0, &timer_spec, nullptr);
  return true;
}

bool TimerFd::set(int timeout_ms, bool one_shot) {
  if (timer_fd_ <= 0) return false;
  if (timeout_ms > 0) {
    timeout_ms_ = timeout_ms;
    one_shot_ = one_shot;
  }
  itimerspec timer_spec{};
  timer_spec.it_value.tv_sec = GET_SECONDS(timeout_ms);
  timer_spec.it_value.tv_nsec = GET_NSECONDS(timeout_ms);
  timer_spec.it_interval.tv_sec = one_shot_ ? 0 : timer_spec.it_value.tv_sec;
  timer_spec.it_interval.tv_nsec = one_shot_ ? 0 : timer_spec.it_value.tv_nsec;
  if (::timerfd_settime(timer_fd_, 0, &timer_spec, nullptr) == -1) {
    std::string error = "timerfd_settime() failed: ";
    error += std::strerror(errno);
    Debug::Log(error, LOG_ERR);
    //    throw std::system_error(errno, std::system_category());
    return false;
  }
  return true;
}

bool TimerFd::isOneShot() const { return one_shot_; }

TimerFd::~TimerFd() {
  if (timer_fd_ > 0) ::close(timer_fd_);
}

bool TimerFd::isTriggered() {
  size_t s = 0;
  return read(timer_fd_, &s, sizeof(s)) != -1;
}

int TimerFd::getFileDescriptor() const {
  if (timer_fd_ < 0) {
    Debug::Log("The timer is not valid.", LOG_REMOVE);
  }
  return timer_fd_;
}
