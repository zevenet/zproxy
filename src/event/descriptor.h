//
// Created by abdess on 12/26/18.
//

#pragma once

#include "epoll_manager.h"
#include "../debug/Debug.h"
#include <atomic>
namespace events {
class Descriptor {

  events::EpollManager *event_manager_{nullptr};
  events::EVENT_TYPE current_event{events::EVENT_TYPE::NONE};
  events::EVENT_GROUP event_group_{events::EVENT_GROUP::NONE};
  bool cancelled{false};

protected:
  int fd_;

public:
  Descriptor() : event_manager_(nullptr), cancelled(true), fd_(-1) {}
  virtual ~Descriptor() {
    if (event_manager_ != nullptr && fd_ > 0)
      event_manager_->deleteFd(fd_);
  }

  inline void setEventManager(events::EpollManager &event_manager) {
    event_manager_ = &event_manager;
  }
  inline bool isCancelled() const { return cancelled; }
  inline bool disableEvents() {
    current_event = events::EVENT_TYPE::NONE;
    cancelled = true;
    if (fd_ > 0)
      return event_manager_->deleteFd(fd_);
    return false;
  }

  inline bool enableEvents(events::EpollManager *epoll_manager,
                           events::EVENT_TYPE event_type,
                           events::EVENT_GROUP event_group) {
    if (epoll_manager != nullptr && fd_ > 0) {
      cancelled = false;
      current_event = event_type;
      event_manager_ = epoll_manager;
      event_group_ = event_group;
      return event_manager_->addFd(fd_, event_type, event_group_);
    }
    return false;
  }

  inline bool setEvents(
      events::EVENT_TYPE event_type,
      events::EVENT_GROUP event_group) {
    if (event_manager_ != nullptr && fd_ > 0) {
      cancelled = false;
      current_event = event_type;
      event_group_ = event_group;
      return event_manager_->updateFd(fd_, event_type, event_group_);
    }
    return false;
  }

  inline bool setEvent(events::EVENT_TYPE event_type) {
    if (event_manager_ != nullptr && fd_ > 0) {
      cancelled = false;
      current_event = event_type;
      return event_manager_->updateFd(fd_, event_type, event_group_);
    }
    return false;
  }

  inline bool enableReadEvent(bool one_shot = false) {
    if (cancelled)
      return false;
    if (event_manager_ !=
            nullptr /* && current_event != (!one_shot
                                          ? events::EVENT_TYPE::READ
                                          : events::EVENT_TYPE::READ_ONESHOT)*/
        && fd_ > 0) {
      current_event = !one_shot
                      ? events::EVENT_TYPE::READ
                      : events::EVENT_TYPE::READ_ONESHOT;

      return event_manager_->updateFd(fd_,
                                      !one_shot
                                      ? events::EVENT_TYPE::READ
                                      : events::EVENT_TYPE::READ_ONESHOT,
                                      event_group_);
    }
//    Debug::LogInfo("InReadModeAlready", LOG_REMOVE);
    return false;
  }

  inline bool enableWriteEvent() {
    if (cancelled)
      return false;
    if (event_manager_ != nullptr /*&& current_event != events::WRITE */ &&
        fd_ > 0) {
      current_event = events::EVENT_TYPE::WRITE;
      return event_manager_->updateFd(fd_, events::EVENT_TYPE::WRITE,
                                      event_group_);
    }
//    Debug::LogInfo("InWriteModeAlready", LOG_REMOVE);
    return false;
  }

  inline int getFileDescriptor() const { return fd_; }

  inline void setFileDescriptor(int fd) {
    if (fd < 0) {
      Debug::LogInfo("Esto que es!!", LOG_REMOVE);
      return;
    }

    fd_ = fd;
  }
};
}
