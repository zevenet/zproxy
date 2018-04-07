//
// Created by abdess on 4/5/18.
//

#ifndef NEW_ZHTTP_EPOLL_H
#define NEW_ZHTTP_EPOLL_H

#include <sys/epoll.h>
#include <mutex>
#include <map>

#define EPOLL_TIMOUT 500
#define MAX_EPOLL_EVENT 100000

#include "../connection/connection.h"

enum EVENT_TYPE {
  READ = EPOLLIN | EPOLLET | EPOLLRDHUP,
  READ_ONESHOT = EPOLLIN | EPOLLET | EPOLLONESHOT | EPOLLRDHUP,
  WRITE = EPOLLOUT | EPOLLET | EPOLLONESHOT | EPOLLRDHUP, //is always one shot
  CONNECT,
  DISCONNECT,
  ACCEPT = EPOLLIN | EPOLLET,
};

class EventManager {

  std::mutex epoll_mutex;
  int epoll_fd;
  int accept_fd;
  epoll_event events[MAX_EPOLL_EVENT];
 protected:
  virtual void HandleEvent(int fd, EVENT_TYPE event_type) = 0;
  void onReadEvent(int fd);
  void onWriteEvent(int fd);
  int loopOnce();
  void onConnectEvent(int fd);

 public:
  EventManager();
  virtual ~EventManager();
  bool handleAccept(int listener_fd);
  bool addFd(int fd, EVENT_TYPE event_type);
  bool deleteFd(int fd);
  bool updateFd(int fd, EVENT_TYPE event_type);

};

#endif //NEW_ZHTTP_EPOLL_H
