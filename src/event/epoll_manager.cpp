/*
 *    Zevenet zProxy Load Balancer Software License
 *    This file is part of the Zevenet zProxy Load Balancer software package.
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

#include "epoll_manager.h"
#include "../debug/Debug.h"
#include "../util/Network.h"
#include <climits>
namespace events {

EpollManager::EpollManager() : accept_fd(-1) {
  if ((epoll_fd = epoll_create1(EPOLL_CLOEXEC)) < 0) {
    std::string error = "epoll_create(2) failed: ";
    error += std::strerror(errno);
    Debug::LogInfo(error, LOG_ERR);
    throw std::system_error(errno, std::system_category());
  }
}

/** Handles the connect events. */
void EpollManager::onConnectEvent(epoll_event &event) {
#if DEBUG_EVENT_MANAGER
  Debug::logmsg(LOG_DEBUG, "~~ONConnectEvent fd: %d",
                static_cast<int>(event.data.u64 >> CHAR_BIT));
#endif
  HandleEvent(static_cast<int>(event.data.u64 >> CHAR_BIT), EVENT_TYPE::CONNECT,
              static_cast<EVENT_GROUP>(event.data.u64 & 0xff));
}

/** Handles the write events. */
void EpollManager::onWriteEvent(epoll_event &event) {
#if DEBUG_EVENT_MANAGER
  Debug::logmsg(LOG_DEBUG, "~~ONWriteEvent fd: %d",
                static_cast<int>(event.data.u64 >> CHAR_BIT));
#endif
  HandleEvent(static_cast<int>(event.data.u64 >> CHAR_BIT), EVENT_TYPE::WRITE,
              static_cast<EVENT_GROUP>(event.data.u64 & 0xff));
}

/** Handles the read events. */
void EpollManager::onReadEvent(epoll_event &event) {
#if DEBUG_EVENT_MANAGER
  Debug::logmsg(LOG_DEBUG, "~~ONReadEvent fd: %d",
                static_cast<int>(event.data.u64 >> CHAR_BIT));
#endif
  HandleEvent(static_cast<int>(event.data.u64 >> CHAR_BIT), EVENT_TYPE::READ,
              static_cast<EVENT_GROUP>(event.data.u64 & 0xff));
}

bool EpollManager::deleteFd(int fd) {
  if (epoll_ctl(epoll_fd, EPOLL_CTL_DEL, fd, NULL) < 0) {
    if (errno == ENOENT || errno == EBADF || errno == EPERM) {
      //      std::string error = "epoll_ctl(delete) unnecessary. ";
      //      error += std::strerror(errno);
      //      Debug::LogInfo(error, LOG_DEBUG);
      return true;
    }
    std::string error = "epoll_ctl(delete) failed ";
    error += std::strerror(errno);
    Debug::LogInfo(error, LOG_DEBUG);
    return false;
  }
  return true;
}

int EpollManager::loopOnce(int time_out) {
  int fd, i, ev_count = 0;
  ev_count = epoll_wait(epoll_fd, events, MAX_EPOLL_EVENT, time_out);
  if (ev_count <= 0)
    return ev_count;
  for (i = 0; i < ev_count; ++i) {
    fd = static_cast<int>(events[i].data.u64 >> CHAR_BIT);
    if ((events[i].events & (EPOLLHUP | EPOLLERR)) != 0u) {
      HandleEvent(fd, EVENT_TYPE::DISCONNECT,
                  static_cast<EVENT_GROUP>(events[i].data.u32 & 0xff));
      continue;
    } else {
      if ((events[i].events & EPOLLIN) != 0u) {
        if (fd == accept_fd) {
          onConnectEvent(events[i]);
        } else {
          onReadEvent(events[i]);
        }
      }
      if(events[i].events &  EPOLLRDHUP){
        HandleEvent(fd, EVENT_TYPE::DISCONNECT,
                    static_cast<EVENT_GROUP>(events[i].data.u32 & 0xff));
        continue;
      }
      if ((events[i].events & EPOLLOUT) != 0u) {
        onWriteEvent(events[i]);
      }
    }
  }

return ev_count;
}

EpollManager::~EpollManager() { ::close(epoll_fd); }

bool EpollManager::handleAccept(int listener_fd) {
  accept_fd = listener_fd;
  Network::setSocketNonBlocking(listener_fd);
  return addFd(listener_fd, EVENT_TYPE::ACCEPT, EVENT_GROUP::ACCEPTOR);
}

bool EpollManager::addFd(int fd, EVENT_TYPE event_type,
                         EVENT_GROUP event_group) {
  //  std::lock_guard<std::mutex> loc(epoll_mutex);
  struct epoll_event epevent = {};
  epevent.events = static_cast<uint32_t>(event_type);
  epevent.data.u64 = static_cast<uint64_t>(fd);
  epevent.data.u64 <<= CHAR_BIT;
  epevent.data.u64 |= static_cast<char>(event_group) & 0xff;
  if (epoll_ctl(epoll_fd, EPOLL_CTL_ADD, fd, &epevent) < 0) {
    if (errno == EEXIST) {
      return updateFd(fd, event_type, event_group);
    } else {
      std::string error = "epoll_ctl(add) failed ";
      error += std::strerror(errno);
      Debug::LogInfo(error, LOG_DEBUG);
      return false;
    }
  }
#if DEBUG_EVENT_MANAGER
  Debug::LogInfo("Epoll::AddFD " + std::to_string(fd) +
                 " To EpollFD: " + std::to_string(epoll_fd),
             LOG_DEBUG);
#endif
  return true;
}

bool EpollManager::updateFd(int fd, EVENT_TYPE event_type,
                            EVENT_GROUP event_group) {
  //  std::lock_guard<std::mutex> loc(epoll_mutex);
#if DEBUG_EVENT_MANAGER
  Debug::LogInfo("Epoll::UpdateFd " + std::to_string(fd), LOG_DEBUG);
#endif
  struct epoll_event epevent = {};
  epevent.events = static_cast<uint32_t>(event_type);
  epevent.data.u64 = static_cast<uint64_t>(fd);
  epevent.data.u64 <<= CHAR_BIT;
  epevent.data.u64 |= static_cast<char>(event_group) & 0xff;
  if (epoll_ctl(epoll_fd, EPOLL_CTL_MOD, fd, &epevent) < 0) {
    if (errno == ENOENT) {
      std::string error = "epoll_ctl(update) failed, fd reopened, adding .. ";
      error += std::strerror(errno);
      Debug::LogInfo(error, LOG_DEBUG);
      return addFd(fd, event_type, event_group);
    } else {
      std::string error = "epoll_ctl(update) failed ";
      error += std::strerror(errno);
      Debug::LogInfo(error, LOG_DEBUG);
      return false;
    }
  }

  return true;
}
}; // namespace events
