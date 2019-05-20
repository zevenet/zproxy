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

/** The enum EVENT_GROUP defines the different group types. */
enum class EVENT_GROUP: char {
  /** This group accept connections. */
  ACCEPTOR = 0x1,
  /** This group handles the events of the server. */
  SERVER,
  /** This group handles the events of the client. */
  CLIENT,
  /** This group handles the connection timeout events. */
  CONNECT_TIMEOUT,
  /** This group handles the request timeout events. */
  REQUEST_TIMEOUT,
  /** This group handles the response timeout events. */
  RESPONSE_TIMEOUT,
  //TODO: Documentar Abdess
  SIGNAL,
  /** This groups handles the maintenance events. */
  MAINTENANCE,
  /** This groups handles the CTL events. */
  CTL_INTERFACE,
  NONE,
};

/** The enum EVENT_TYPE defines the different event types. */
enum EVENT_TYPE {
  /** Timeout reached. */
  TIMEOUT = EPOLLIN,
#if SM_HANDLE_ACCEPT && EPOLLEXCLUSIVE
  ACCEPT = (EPOLLIN | EPOLLEXCLUSIVE),
#else
  /** Accept the connection. */
  ACCEPT = (EPOLLIN | EPOLLET),
#endif
  /** Read from the connection. */
  READ = (EPOLLIN | EPOLLET | EPOLLRDHUP | EPOLLHUP),
  /** Read from the connection. */
  READ_ONESHOT = (EPOLLIN | EPOLLET | EPOLLONESHOT | EPOLLRDHUP | EPOLLHUP),
  /** Write to the connection. */
  WRITE = (EPOLLOUT | EPOLLET | EPOLLONESHOT | EPOLLRDHUP |
           EPOLLHUP), // is always one shot
  //TODO: Documentar abdess
  ANY = (EPOLLONESHOT | EPOLLIN | EPOLLET | EPOLLRDHUP | EPOLLHUP | EPOLLOUT),
  CONNECT,
  DISCONNECT,
  NONE
};

// TODO:: Make it static polimorphosm, template<typename Handler>
/** The EpollManager is a wrapper class over the EPOLL system. It handles all
 * the operations needed. */
class EpollManager {
  //  std::mutex epoll_mutex;
  /** Epoll file descriptor. */
  int epoll_fd;
  //TODO: Documentar abdess
  int accept_fd;
  /** Array of epoll_event. This array contains all the events. */
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
