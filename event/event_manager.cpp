//
// Created by abdess on 4/5/18.
//

#include "event_manager.h"
#include "../debug/Debug.h"
#include "../util/Network.h"

#define DEBUG_EPOLL 0

EpollManager::EpollManager() : accept_fd(-1) {
  if ((epoll_fd = epoll_create1(0)) < 0) {
    std::string error = "epoll_create(2) failed: ";
    error += std::strerror(errno);
    Debug::Log(error, LOG_ERR);
    throw std::system_error(errno, std::system_category());
  }
  Debug::Log("created epoll fd " + std::to_string(epoll_fd));

}

void EpollManager::onConnectEvent(int fd) {
  HandleEvent(fd, CONNECT);
}

void EpollManager::onWriteEvent(int fd) {
  HandleEvent(fd, WRITE);
}

void EpollManager::onReadEvent(int fd) {
  HandleEvent(fd, READ);
}

bool EpollManager::deleteFd(int fd) {
  if (epoll_ctl(epoll_fd, EPOLL_CTL_DEL, fd, NULL) < 0) {
    std::string error = "epoll_ctl(2) failed on main server socket";
    error += std::strerror(errno);
    Debug::Log(error, LOG_DEBUG);
    return false;
  }
  return true;
}

int EpollManager::loopOnce() {
  int fd, i, ev_count = 0;
  ev_count = epoll_wait(epoll_fd, events, MAX_EPOLL_EVENT, EPOLL_TIMOUT);
  if (ev_count < 0 && EINTR == errno)
    return 0;
  if (ev_count < 0)
    return ev_count;
  if (ev_count == 0) Debug::Log("Epoll timeout ");
  for (i = 0; i < ev_count; ++i) {
    fd = events[i].data.fd;
//    if ((events[i].events & EPOLLERR) ||
//        (events[i].events & EPOLLHUP) ||
//        (!(events[i].events & EPOLLIN))) {
//      std::string error = "EPOLLERR | EPOLLHUP An error has occured on fd " +
//          std::to_string(fd) + " ";
//      error += std::strerror(errno);
//      Debug::Log(error, LOG_DEBUG);
//      HandleEvent(fd, DISCONNECT);
//      if (fd != accept_fd) {
//        deleteFd(fd);
//      }
//      continue;
//    } else
    if ((events[i].events & EPOLLRDHUP) != 0u) {
      std::string error = "EPOLLRDHUP:Peer closed the connection fd: " +
          std::to_string(fd) + " ";
      Debug::Log(error, LOG_DEBUG);
      HandleEvent(fd, DISCONNECT);
      //deleteFd(fd);
      continue;
    }
    if (fd == accept_fd) {
#if DEBUG_EPOLL
      Debug::Log("EPOLL::ON_ACCEPT", LOG_DEBUG);
#endif
      onConnectEvent(fd);
      continue;
    }
    if ((events[i].events & EPOLLIN) != 0u) {
#if DEBUG_EPOLL
      Debug::Log("EPOLL::ON_READ", LOG_DEBUG);
#endif
      onReadEvent(fd);
    }
    if ((events[i].events & EPOLLOUT) != 0u) {
#if DEBUG_EPOLL
      Debug::Log("EPOLL::ON_WRITE", LOG_DEBUG);
#endif
      onWriteEvent(fd);
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
  return addFd(listener_fd, ACCEPT);
}

bool EpollManager::addFd(int fd, EVENT_TYPE event_type) {
//  std::lock_guard<std::mutex> loc(epoll_mutex);
  struct epoll_event epevent = {};
  epevent.events = event_type;
  epevent.data.fd = fd;
  if (epoll_ctl(epoll_fd, EPOLL_CTL_ADD, fd, &epevent) < 0) {
    std::string error = "epoll_ctl(2) failed ";
    error += std::strerror(errno);
    Debug::Log(error, LOG_DEBUG);
    return false;
  }
#if DEBUG_EPOLL
  Debug::Log("Epoll::AddFD " + std::to_string(fd) + " To EpollFD: " + std::to_string(epoll_fd));
#endif
  return true;
}

bool EpollManager::updateFd(int fd, EVENT_TYPE event_type) {
//  std::lock_guard<std::mutex> loc(epoll_mutex);
  epoll_event epevent{};
  epevent.events = event_type;
  epevent.data.fd = fd;
  if (epoll_ctl(epoll_fd, EPOLL_CTL_MOD, fd, &epevent) < 0) {
    std::string error = "epoll_ctl(2) failed ";
    error += std::strerror(errno);
    Debug::Log(error, LOG_DEBUG);
    return false;
  }
#if DEBUG_EPOLL
  Debug::Log("Epoll::UpdateFd " + std::to_string(fd));
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


