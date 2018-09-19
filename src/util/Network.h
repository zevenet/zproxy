#ifndef NETWORK_H
#define NETWORK_H
#include <arpa/inet.h>
#include <fcntl.h>
#include <netdb.h>
#include <netinet/tcp.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <cstring>
#include "../debug/Debug.h"

class Network {
 public:
  inline static char* getPeerAddress(int socket_fd,
                                     char* buf,
                                     size_t bufsiz,
                                     bool include_port = false) {
    int result;
    sockaddr_in adr_inet{};
    int len_inet = sizeof adr_inet;
    result = getpeername(socket_fd, (struct sockaddr*)&adr_inet, &len_inet);
    if (result == -1) {
      return nullptr;
    }

    if (snprintf(buf, bufsiz, "%s", inet_ntoa(adr_inet.sin_addr)) == -1) {
      return nullptr; /* Buffer too small */
    }
    if (include_port) {
      //      result = snprintf(buf, bufsiz, "%s:%u",
      //                        inet_ntoa(adr_inet.sin_addr),
      //                        (unsigned) ntohs(adr_inet.sin_port));
      //      if (result == -1) {
      //        return nullptr; /* Buffer too small */
      //      }
    }
    return buf;
  }

  inline static int getHost(const char* name, addrinfo* res, int ai_family) {
    struct addrinfo *chain, *ap;
    struct addrinfo hints;
    int ret_val;
    memset(&hints, 0, sizeof(hints));
    hints.ai_family = ai_family;
    hints.ai_socktype = SOCK_STREAM;
    hints.ai_flags = AI_CANONNAME;
    if ((ret_val = getaddrinfo(name, NULL, &hints, &chain)) == 0) {
      for (ap = chain; ap != NULL; ap = ap->ai_next)
        if (ap->ai_socktype == SOCK_STREAM)
          break;

      if (ap == NULL) {
        freeaddrinfo(chain);
        return EAI_NONAME;
      }
      *res = *ap;
      if ((res->ai_addr = (struct sockaddr*)malloc(ap->ai_addrlen)) == NULL) {
        freeaddrinfo(chain);
        return EAI_MEMORY;
      }
      memcpy(res->ai_addr, ap->ai_addr, ap->ai_addrlen);
      freeaddrinfo(chain);
    }
    return ret_val;
  }

  inline static addrinfo* getAddress(std::string& address, int port) {
    struct sockaddr_in in {};
    struct sockaddr_in6 in6 {};
    auto* addr = new addrinfo(); /* IPv4/6 address */

    if (getHost(address.c_str(), addr, PF_UNSPEC)) {
      Debug::Log("Unknown Listener address");
      delete addr;
      return nullptr;
    }
    if (addr->ai_family != AF_INET && addr->ai_family != AF_INET6) {
      Debug::Log("Unknown Listener address family");
      delete addr;
      return nullptr;
    }
    switch (addr->ai_family) {
      case AF_INET:
        memcpy(&in, addr->ai_addr, sizeof(in));
        in.sin_port = (in_port_t)htons(port);
        memcpy(addr->ai_addr, &in, sizeof(in));
        break;
      case AF_INET6:
        memcpy(&in6, addr->ai_addr, sizeof(in6));
        in6.sin6_port = htons(port);
        memcpy(addr->ai_addr, &in6, sizeof(in6));
        break;
      default:
        Debug::Log("Unknown Listener address family", LOG_ERR);
    }
    return addr;
  }

  /*
   * Translate inet/inet6 address/port into a string
   */
  static void addr2str(char* const res,
                       const int res_len,
                       const struct addrinfo* addr,
                       const int no_port) {
    char buf[MAXBUF];
    int port;
    void* src;

    ::memset(res, 0, res_len);
    switch (addr->ai_family) {
      case AF_INET:
        src = (void*)&((struct sockaddr_in*)addr->ai_addr)->sin_addr.s_addr;
        port = ntohs(((struct sockaddr_in*)addr->ai_addr)->sin_port);
        if (inet_ntop(AF_INET, src, buf, MAXBUF - 1) == NULL)
          strncpy(buf, "(UNKNOWN)", MAXBUF - 1);
        break;
      case AF_INET6:
        src = (void*)&((struct sockaddr_in6*)addr->ai_addr)->sin6_addr.s6_addr;
        port = ntohs(((struct sockaddr_in6*)addr->ai_addr)->sin6_port);
        if (IN6_IS_ADDR_V4MAPPED(
                &(((struct sockaddr_in6*)addr->ai_addr)->sin6_addr))) {
          src = (void*)&((struct sockaddr_in6*)addr->ai_addr)
                    ->sin6_addr.s6_addr[12];
          if (inet_ntop(AF_INET, src, buf, MAXBUF - 1) == NULL)
            strncpy(buf, "(UNKNOWN)", MAXBUF - 1);
        } else {
          if (inet_ntop(AF_INET6, src, buf, MAXBUF - 1) == NULL)
            strncpy(buf, "(UNKNOWN)", MAXBUF - 1);
        }
        break;
      case AF_UNIX:
        strncpy(buf, (char*)addr->ai_addr, MAXBUF - 1);
        port = 0;
        break;
      default:
        strncpy(buf, "(UNKNOWN)", MAXBUF - 1);
        port = 0;
        break;
    }
    if (no_port)
      ::snprintf(res, res_len, "%s", buf);
    else
      ::snprintf(res, res_len, "%s:%d", buf, port);
    return;
  }

  static bool setSocketNonBlocking(int fd, bool blocking = false) {
    // set socket non blocking
    int flags;
    flags = ::fcntl(fd, F_GETFL, NULL);
    if (blocking) {
      flags &= (~O_NONBLOCK);
    } else {
      flags |= O_NONBLOCK;
    }
    if (::fcntl(fd, F_SETFL, flags) < 0) {
      std::string error = "fcntl(2) failed";
      error += std::strerror(errno);
      Debug::Log(error);
      return false;
    }
    return true;
  }

  inline static bool setSocketTimeOut(int sock_fd, unsigned int seconds) {
    struct timeval tv;
    tv.tv_sec = seconds; /* 30 Secs Timeout */
    return setsockopt(sock_fd, SOL_SOCKET, SO_RCVTIMEO, (struct timeval*)&tv,
                      sizeof(struct timeval)) != -1;
  }

  inline static bool setSoReuseAddrOption(int sock_fd) {
    int flag = 1;
    return setsockopt(sock_fd, SOL_SOCKET, SO_REUSEADDR, &flag, sizeof(flag)) !=
           -1;
  }

  inline static bool setTcpNoDelayOption(int sock_fd) {
    int flag = 1;
    return setsockopt(sock_fd, IPPROTO_TCP, TCP_NODELAY, &flag, sizeof(flag)) !=
           -1;
  }

  inline static bool setTcpDeferAcceptOption(int sock_fd) {
    int flag = 5;
    return setsockopt(sock_fd, SOL_TCP, TCP_DEFER_ACCEPT, &flag,
                      sizeof(flag)) != -1;
  }

  inline static bool setSoKeepAliveOption(int sock_fd) {
    int flag = 1;
    return setsockopt(sock_fd, SOL_SOCKET, SO_KEEPALIVE, &flag, sizeof(flag)) !=
           -1;
  }
  inline static bool setSoLingerOption(int sock_fd, bool enable = false) {
    struct linger l {};
    l.l_onoff = 1;
    l.l_linger = enable ? 10 : 0;
    return setsockopt(sock_fd, SOL_SOCKET, SO_LINGER, &l, sizeof(l)) != -1;
  }

  inline static bool setTcpLinger2Option(int sock_fd) {
    int flag = 5;
    return setsockopt(sock_fd, SOL_SOCKET, TCP_LINGER2, &flag, sizeof(flag)) !=
           -1;
  }

  /*useful for use with send file, wait 200 ms to to fill TCP packet*/
  inline static bool setTcpCorkOption(int sock_fd) {
    int flag = 1;
    return setsockopt(sock_fd, IPPROTO_TCP, TCP_CORK, &flag, sizeof(flag)) !=
           -1;
  }

  /*useful for use with send file, wait 200 ms to to fill TCP packet*/
  inline static bool setSoZeroCopy(int sock_fd) {
    int flag = 1;
    return setsockopt(sock_fd, SOL_SOCKET, SO_ZEROCOPY, &flag, sizeof(flag)) !=
           -1;
  }

  inline static bool isConnected(int sock_fd) {
    int error_code = -1;
    int error_code_size = sizeof(error_code);
    return ::getsockopt(sock_fd, SOL_SOCKET, SO_ERROR, &error_code,
                        &error_code_size) != -1 &&
           error_code == 0;
  }

  static std::string read(int fd) {
    int size = 65536;
    char buffer[size];
    bool should_close = false, done = false;
    ssize_t count = -1;
    size_t buffer_size = 0;

    while (!done) {
      count = ::recv(fd, buffer + buffer_size, size, MSG_NOSIGNAL);
      if (count == -1) {
        if (errno != EAGAIN && errno != EWOULDBLOCK) {
          std::string error = "read() failed  ";
          error += std::strerror(errno);
          Debug::Log(error, LOG_NOTICE);
          should_close = true;
        }
        done = true;
      } else if (count == 0) {
        //  The  remote has closed the connection, wait for EPOLLRDHUP
        should_close = true;
        done = true;
      } else {
        buffer_size += static_cast<size_t>(count);
      }
    }
    return std::string(buffer);
  }

  /*return -1 in case of erro and set errno*/
  static int getSocketSendBufferSize_(int socket_fd) {
    int res, size;
    unsigned int m = sizeof(size);
    res = getsockopt(socket_fd, SOL_SOCKET, SO_SNDBUF, (void*)&size, &m);
    return res != 0 ? -1 : size;
  }

  /*return -1 in case of erro and set errno*/
  static int getSocketReceiveBufferSize_(int socket_fd) {
    int res, size;
    unsigned int m = sizeof(size);
    res = getsockopt(socket_fd, SOL_SOCKET, SO_RCVBUF, (void*)&size, &m);
    return res != 0 ? -1 : size;
  }
};
#endif  // NETWORK_H
