//
// Created by abdess on 4/5/18.
//

#pragma once

#include <sys/epoll.h>
#include <mutex>
#include "../connection/connection.h"
#include <map>

namespace epoll_manager {

#define EPOLL_TIMOUT -1

#define MAX_EPOLL_EVENT 100000

//#define READ_MASK (EPOLLIN | EPOLLET | EPOLLRDHUP | EPOLLHUP)
//#define  READ_ONESHOT_MASK  (EPOLLIN | EPOLLET | EPOLLONESHOT | EPOLLRDHUP |EPOLLHUP)
//#define  WRITE_MASK  (EPOLLOUT | EPOLLET | EPOLLONESHOT | EPOLLRDHUP | EPOLLHUP) //is always one shot
//#define  ACCEPT_MASK (EPOLLIN | EPOLLET)

enum EVENT_GROUP {
  ACCEPTOR = 1,
  SERVER,
  CLIENT,
  TIMER,
};

enum EVENT_TYPE {
  CONNECT,
  DISCONNECT,
  ANY = (EPOLLONESHOT | EPOLLIN | EPOLLET | EPOLLRDHUP | EPOLLHUP | EPOLLOUT),
  READ = (EPOLLIN | EPOLLET | EPOLLRDHUP | EPOLLHUP),
  READ_ONESHOT = (EPOLLIN | EPOLLET | EPOLLONESHOT | EPOLLRDHUP | EPOLLHUP),
  WRITE = (EPOLLOUT | EPOLLET | EPOLLONESHOT | EPOLLRDHUP | EPOLLHUP), //is always one shot
  ACCEPT = (EPOLLIN | EPOLLET),
};

class EpollManager {
//  std::mutex epoll_mutex;
  int epoll_fd;
  int accept_fd;
  epoll_event events[MAX_EPOLL_EVENT];
 protected:
  inline virtual void HandleEvent(int fd, EVENT_TYPE event_type, EVENT_GROUP event_group) = 0;
  inline void onReadEvent(epoll_event &event);
  inline void onWriteEvent(epoll_event &event);
  inline void onConnectEvent(epoll_event &event);
 public:

  EpollManager();
  int loopOnce(int time_out = -1);
  virtual ~EpollManager();
  bool handleAccept(int listener_fd);
  bool addFd(int fd, EVENT_TYPE event_type, EVENT_GROUP event_group);
  bool deleteFd(int fd);
  bool updateFd(int fd, EVENT_TYPE event_type, EVENT_GROUP event_group);
//  inline unsigned int getMask(EVENT_TYPE event_type);
};
};

