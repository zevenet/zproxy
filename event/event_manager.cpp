//
// Created by abdess on 4/5/18.
//

#include "event_manager.h"
#include "../debug/Debug.h"
#include "../connection/Network.h"

EventManager::EventManager() : accept_fd(-1) {
  if ((epoll_fd = epoll_create(1)) < 0) {
    std::string error = "epoll_create(2) failed: ";
    error += std::strerror(errno);
    Debug::Log(error, LOG_ERR);
    throw std::system_error(errno, std::system_category());
  }
}

void EventManager::onConnectEvent(int fd) {
  HandleEvent(fd, CONNECT);
}

void EventManager::onWriteEvent(int fd) {
  HandleEvent(fd, WRITE);
}

void EventManager::onReadEvent(int fd) {
  HandleEvent(fd, READ);
}

bool EventManager::deleteFd(int fd) {
  if (epoll_ctl(epoll_fd, EPOLL_CTL_DEL, fd, NULL) < 0) {
    std::string error = "epoll_ctl(2) failed on main server socket";
    error += std::strerror(errno);
    Debug::Log(error, LOG_DEBUG);
    return false;
  }
  return true;
}

bool EventManager::updateFd(int fd, EVENT_TYPE event_type) {
  std::lock_guard<std::mutex> loc(epoll_mutex);
  epoll_event epevent{};
  epevent.events = event_type;
  epevent.data.fd = fd;
  if (epoll_ctl(epoll_fd, EPOLL_CTL_MOD, fd, &epevent) < 0) {
    std::string error = "epoll_ctl(2) failed ";
    error += std::strerror(errno);
    Debug::Log(error, LOG_DEBUG);
    return false;
  }
  return true;
}

int EventManager::loopOnce() {
  int fd, i, ev_count = 0;
  ev_count = epoll_wait(epoll_fd, events, MAX_EPOLL_EVENT, EPOLL_TIMOUT);
  if (ev_count < 0 && EINTR == errno)
    return 0;
  if (ev_count < 0)
    return ev_count;

  for (i = 0; i < ev_count; ++i) {
    fd = events[i].data.fd;
    if (((events[i].events & EPOLLERR) != 0u) ||
        ((events[i].events & EPOLLHUP) != 0u) ||
        ((events[i].events & EPOLLIN) == 0u)) {
      if (fd != accept_fd) {
        deleteFd(fd);
      }

      HandleEvent(fd, DISCONNECT);
      std::string error = "EPOLLERR | EPOLLHUP An error has occured on fd " +
          std::to_string(fd) + " ";
      error += std::strerror(errno);
      Debug::Log(error, LOG_DEBUG);
      continue;
    }
    if ((events[i].events & EPOLLRDHUP) != 0u) {
      deleteFd(fd);
      HandleEvent(fd, DISCONNECT);
      std::string error = "EPOLLRDHUP:Peer closed the connection fd: " +
          std::to_string(fd) + " ";
      Debug::Log(error, LOG_DEBUG);
      continue;
    }
    if (fd == accept_fd) {
      Debug::Log("EPOLL::ON_ACCEPT", LOG_DEBUG);
      onConnectEvent(fd);
    }
    if ((events[i].events & EPOLLIN) != 0u) {
      Debug::Log("EPOLL::ON_READ", LOG_DEBUG);
      onReadEvent(fd);
    }
    if ((events[i].events & EPOLLOUT) != 0u) {
      Debug::Log("EPOLL::ON_WRITE", LOG_DEBUG);
      onWriteEvent(fd);
    }
  }
}

EventManager::~EventManager() {
  ::close(epoll_fd);
}

bool EventManager::handleAccept(int listener_fd) {
  accept_fd = listener_fd;
  Network::setSocketNonBlocking(listener_fd);
  return addFd(listener_fd, ACCEPT);
}

bool EventManager::addFd(int fd, EVENT_TYPE event_type) {
  struct epoll_event epevent = {};
  epevent.events = event_type;
  epevent.data.fd = fd;
  if (epoll_ctl(epoll_fd, EPOLL_CTL_ADD, fd, &epevent) < 0) {
    std::string error = "epoll_ctl(2) failed ";
    error += std::strerror(errno);
    Debug::Log(error, LOG_DEBUG);
    return false;
  }
  return true;
}

