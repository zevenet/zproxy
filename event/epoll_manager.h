//
// Created by abdess on 4/5/18.
//

#ifndef NEW_ZHTTP_EPOLL_H
#define NEW_ZHTTP_EPOLL_H

#include <sys/epoll.h>
#include <mutex>
#include "../connection/connection.h"

#include <map>
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
};

enum EVENT_TYPE {
  CONNECT,
  DISCONNECT,
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
  virtual void HandleEvent(int fd, EVENT_TYPE event_type, EVENT_GROUP event_group) = 0;
  void onReadEvent(epoll_event &event);
  void onWriteEvent(epoll_event &event);
  void onConnectEvent(epoll_event &event);
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

#endif //NEW_ZHTTP_EPOLL_H
