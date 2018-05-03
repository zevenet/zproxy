//
// Created by abdess on 4/5/18.
//

#include <climits>
#include "epoll_manager.h"
#include "../debug/Debug.h"
#include "../util/Network.h"
namespace epoll_manager {

EpollManager::EpollManager() : accept_fd(-1) {
  if ((epoll_fd = epoll_create1(EPOLL_CLOEXEC)) < 0) {
    std::string error = "epoll_create(2) failed: ";
    error += std::strerror(errno);
    Debug::Log(error, LOG_ERR);
    throw std::system_error(errno, std::system_category());
  }
}

void EpollManager::onConnectEvent(epoll_event &event) {
  HandleEvent(static_cast<int>(event.data.u64 >> CHAR_BIT), CONNECT, static_cast<EVENT_GROUP> (event.data.u64 & 0xff));
}

void EpollManager::onWriteEvent(epoll_event &event) {
  HandleEvent(static_cast<int>(event.data.u64 >> CHAR_BIT), WRITE, static_cast<EVENT_GROUP> (event.data.u64 & 0xff));
}

void EpollManager::onReadEvent(epoll_event &event) {
  HandleEvent(static_cast<int>(event.data.u64 >> CHAR_BIT), READ, static_cast<EVENT_GROUP> (event.data.u64 & 0xff));
}

bool EpollManager::deleteFd(int fd) {
  if (epoll_ctl(epoll_fd, EPOLL_CTL_DEL, fd, NULL) < 0) {
    if (errno == ENOENT || errno == EBADF || errno == EPERM) {
      std::string error = "epoll_ctl(delete) unnecessary. ";
      error += std::strerror(errno);
      Debug::Log(error, LOG_DEBUG);
      return true;
    }
    std::string error = "epoll_ctl(delete) failed ";
    error += std::strerror(errno);
    Debug::Log(error, LOG_DEBUG);
    return false;
  }
  return true;
}

int EpollManager::loopOnce(int time_out) {
  int fd, i, ev_count = 0;
  ev_count = epoll_wait(epoll_fd, events, MAX_EPOLL_EVENT, EPOLL_TIMOUT);
  if (ev_count < 0 && EINTR == errno)
    return 0;
  if (ev_count < 0)
    return ev_count;
  if (ev_count == 0) Debug::Log("Epoll timeout ");
  for (i = 0; i < ev_count; ++i) {
    fd = static_cast<int>(events[i].data.u64 >> CHAR_BIT);
//    if ((events[i].events & EPOLLERR) ||
//        (events[i].events & EPOLLHUP))//||
////        (!(events[i].events & EPOLLIN)))
//    {
//#if DEBUG_EVENT_MANAGER
//      std::string error = "EPOLLERR | EPOLLHUP An error has occured on fd " +
//          std::to_string(fd) + " ";
//      error += std::strerror(errno);
//      Debug::Log(error, LOG_DEBUG);
//#endif
//      if (fd != accept_fd) {
//        deleteFd(fd);
//      }
//      HandleEvent(fd, DISCONNECT, static_cast<EVENT_GROUP >(events[i].data.u32 & 0xff));
//      continue;
//    } else
    if ((events[i].events & (EPOLLHUP | EPOLLERR | EPOLLRDHUP)) != 0u) {
#if DEBUG_EVENT_MANAGER
      std::string error = "\n>>EPOLLRDHUP:Peer closed the connection fd: " +
          std::to_string(fd) + " ";
      Debug::Log(error, LOG_DEBUG);
#endif
      HandleEvent(fd, DISCONNECT, static_cast<EVENT_GROUP >(events[i].data.u32 & 0xff));
      //deleteFd(fd);
      continue;
    }
    if (fd == accept_fd) {
#if DEBUG_EVENT_MANAGER
      Debug::Log("\n>>EPOLL::ON_ACCEPT::FD=" + std::to_string(fd), LOG_DEBUG);
#endif
      onConnectEvent(events[i]);
      continue;
    }
    if ((events[i].events & EPOLLIN) != 0u) {
#if DEBUG_EVENT_MANAGER
      Debug::Log("\n>>EPOLL::ON_READ::FD=" + std::to_string(fd), LOG_DEBUG);
#endif
      onReadEvent(events[i]);
    }
    if ((events[i].events & EPOLLOUT) != 0u) {
#if DEBUG_EVENT_MANAGER
      Debug::Log("\n>>EPOLL::ON_WRITE::FD=" + std::to_string(fd), LOG_DEBUG);
#endif
      onWriteEvent(events[i]);
    }
  }
  return ev_count;
}

EpollManager::~EpollManager() {
  ::close(epoll_fd);
}

bool EpollManager::handleAccept(int listener_fd) {
  accept_fd = listener_fd;
  Network::setSocketNonBlocking(listener_fd);
  return addFd(listener_fd, ACCEPT, EVENT_GROUP::ACCEPTOR);
}

bool EpollManager::addFd(int fd, EVENT_TYPE event_type, EVENT_GROUP event_group) {
//  std::lock_guard<std::mutex> loc(epoll_mutex);
  struct epoll_event epevent = {};
  epevent.events = event_type;
  epevent.data.u64 = static_cast<uint64_t>(fd);
  epevent.data.u64 <<= CHAR_BIT;
  epevent.data.u64 |= event_group & 0xff;
  if (epoll_ctl(epoll_fd, EPOLL_CTL_ADD, fd, &epevent) < 0) {
    if (errno == EEXIST) { return updateFd(fd, event_type, event_group); }
    else {
      std::string error = "epoll_ctl(add) failed ";
      error += std::strerror(errno);
      Debug::Log(error, LOG_DEBUG);
      return false;
    }
  }
#if DEBUG_EVENT_MANAGER
  Debug::Log("Epoll::AddFD " + std::to_string(fd) + " To EpollFD: " + std::to_string(epoll_fd), LOG_DEBUG);
#endif
  return true;
}

bool EpollManager::updateFd(int fd, EVENT_TYPE event_type, EVENT_GROUP event_group) {
//  std::lock_guard<std::mutex> loc(epoll_mutex);
  struct epoll_event epevent = {};
  epevent.events = event_type;
  epevent.data.u64 = static_cast<uint64_t>(fd);
  epevent.data.u64 <<= CHAR_BIT;
  epevent.data.u64 |= event_group & 0xff;
  if (epoll_ctl(epoll_fd, EPOLL_CTL_MOD, fd, &epevent) < 0) {
    if (errno == ENOENT) {
      std::string error = "epoll_ctl(update) failed, fd reopened, adding .. ";
      error += std::strerror(errno);
      Debug::Log(error, LOG_DEBUG);
      return addFd(fd, event_type, event_group);
    } else {
      std::string error = "epoll_ctl(update) failed ";
      error += std::strerror(errno);
      Debug::Log(error, LOG_DEBUG);
      return false;
    }
  }
#if DEBUG_EVENT_MANAGER
  Debug::Log("Epoll::UpdateFd " + std::to_string(fd), LOG_DEBUG);
#endif
  return true;
}
//unsigned int EpollManager::getMask(EVENT_TYPE event_type) {
//  switch (event_type) {
//    case DISCONNECT:
//    case READ: return READ_MASK;
//      break;
//    case READ_ONESHOT: return READ_ONESHOT_MASK;
//      break;
//    case WRITE:return WRITE_MASK;
//      break;
//    case CONNECT:
//    case ACCEPT: return ACCEPT_MASK;
//      break;
//  }
//}


};