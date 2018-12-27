//
// Created by abdess on 4/5/18.
//

#pragma once

#include <map>
#include <mutex>
#include <sys/epoll.h>
#include <unistd.h>

namespace events {

#define MAX_EPOLL_EVENT 100000

enum class EVENT_GROUP: char {
  ACCEPTOR = 0x1,
  SERVER,
  CLIENT,
  CONNECT_TIMEOUT,
  REQUEST_TIMEOUT,
  RESPONSE_TIMEOUT,
  SIGNAL,
  MAINTENANCE,
  CTL_INTERFACE,
  NONE,
};

enum EVENT_TYPE {
  TIMEOUT = EPOLLIN,
#if SM_HANDLE_ACCEPT
  ACCEPT = (EPOLLIN | EPOLLEXCLUSIVE),
#else
  ACCEPT = (EPOLLIN | EPOLLET),
#endif
  READ = (EPOLLIN | EPOLLET | EPOLLRDHUP | EPOLLHUP),
  READ_ONESHOT = (EPOLLIN | EPOLLET | EPOLLONESHOT | EPOLLRDHUP | EPOLLHUP),
  WRITE = (EPOLLOUT | EPOLLET | EPOLLONESHOT | EPOLLRDHUP |
           EPOLLHUP), // is always one shot
  ANY = (EPOLLONESHOT | EPOLLIN | EPOLLET | EPOLLRDHUP | EPOLLHUP | EPOLLOUT),
  CONNECT,
  DISCONNECT,
  NONE
};

// TODO:: Make it static polimorphosm, template<typename Handler>
class EpollManager {
  //  std::mutex epoll_mutex;
  int epoll_fd;
  int accept_fd;
  epoll_event events[MAX_EPOLL_EVENT];

protected:
  inline virtual void HandleEvent(int fd, EVENT_TYPE event_type,
                                  EVENT_GROUP event_group) = 0;
  inline void onReadEvent(epoll_event &event);
  inline void onWriteEvent(epoll_event &event);
  inline void onConnectEvent(epoll_event &event);

public:
  EpollManager();
  int loopOnce(int time_out = -1);
  ~EpollManager();
  bool handleAccept(int listener_fd);
  bool addFd(int fd, EVENT_TYPE event_type, EVENT_GROUP event_group);
  bool deleteFd(int fd);
  bool updateFd(int fd, EVENT_TYPE event_type, EVENT_GROUP event_group);
};
}; // namespace events
