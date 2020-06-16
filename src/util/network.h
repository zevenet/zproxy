/*
 *    Zevenet zproxy Load Balancer Software License
 *    This file is part of the Zevenet zproxy Load Balancer software package.
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
#pragma once

#include <arpa/inet.h>
#include <fcntl.h>
#include <netdb.h>
#include <netinet/tcp.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <sys/un.h>
#include <cstring>
#include "../debug/logger.h"
class Network {
 public:
  inline static char *getPeerAddress(int socket_fd, char *buf, size_t bufsiz, bool include_port = false) {
    int result;
    sockaddr_in adr_inet{};
    socklen_t len_inet = sizeof adr_inet;
    result = ::getpeername(socket_fd, reinterpret_cast<sockaddr *>(&adr_inet), &len_inet);
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
  /*
 * Search for a host name_, return the addrinfo for it
 */
  inline static int getHost(const char *name, addrinfo *res, int ai_family) {
    struct addrinfo *chain, *ap;
    struct addrinfo hints;
    int ret_val;
    memset(&hints, 0, sizeof(hints));
    hints.ai_family = ai_family;
    hints.ai_socktype = SOCK_STREAM;
    hints.ai_flags = AI_CANONNAME;
    if ((ret_val = getaddrinfo(name, nullptr, &hints, &chain)) == 0) {
      for (ap = chain; ap != nullptr; ap = ap->ai_next)
        if (ap->ai_socktype == SOCK_STREAM) break;

      if (ap == nullptr) {
        freeaddrinfo(chain);
        return EAI_NONAME;
      }
      *res = *ap;
      if ((res->ai_addr = static_cast<sockaddr *>(
               std::malloc(ap->ai_addrlen))) == nullptr) {
        freeaddrinfo(chain);
        return EAI_MEMORY;
      }
      memcpy(res->ai_addr, ap->ai_addr, ap->ai_addrlen);
      freeaddrinfo(chain);
    }
    return ret_val;
  }

  inline static std::unique_ptr<addrinfo, decltype(&::freeaddrinfo)> getAddress(
      const std::string &address, int port = 0) {
    addrinfo hints{};
    addrinfo *result{nullptr};
    int sfd;
    memset(&hints, 0, sizeof(struct addrinfo));
    hints.ai_family = AF_UNSPEC;     /* Allow IPv4 or IPv6 */
    hints.ai_socktype = SOCK_STREAM; /* Datagram socket */
    hints.ai_flags = AI_CANONNAME;
    hints.ai_protocol = 0; /* Any protocol */
    hints.ai_canonname = nullptr;
    hints.ai_addr = nullptr;
    hints.ai_next = nullptr;

    sfd = getaddrinfo(address.data(),
                      port > 0 ? std::to_string(port).data() : nullptr, &hints,
                      &result);
    if (sfd != 0) {
      logmsg(LOG_NOTICE, "getaddrinfo: %s\n", gai_strerror(sfd));
      return std::unique_ptr<addrinfo, decltype(&::freeaddrinfo)>(nullptr,
                                                                  freeaddrinfo);
    }
    return std::unique_ptr<addrinfo, decltype(&::freeaddrinfo)>(result,
                                                                &freeaddrinfo);
  }

  inline static int getPeerPort(int socket_fd) {
    int port = -1;

    sockaddr_in adr_inet{};
    socklen_t len_inet = sizeof(adr_inet);

    if (::getpeername(socket_fd, reinterpret_cast<sockaddr *>(&adr_inet), &len_inet) != -1) {
      port = ntohs(adr_inet.sin_port);
      return port;
    }
    return -1;
  }

  inline static int getPeerPort(struct addrinfo *addr) {
    int port;
    port = ntohs((reinterpret_cast<sockaddr_in *>(addr->ai_addr))->sin_port);
    return port;
  }

  inline static int getlocalPort(int socket_fd) {
    int port = -1;
    sockaddr_in adr_inet{};
    socklen_t len_inet = sizeof(adr_inet);
    if (::getsockname(socket_fd, reinterpret_cast<sockaddr *>(&adr_inet), &len_inet) != -1) {
      port = ntohs(adr_inet.sin_port);
      return port;
    }
    return -1;
  }
  inline static char *getlocalAddress(int socket_fd, char *buf, size_t bufsiz, bool include_port = false) {
    int result;
    sockaddr_in adr_inet{};
    socklen_t len_inet = sizeof adr_inet;
    result = ::getsockname(socket_fd, reinterpret_cast<sockaddr *>(&adr_inet), &len_inet);
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

  /*
   * Translate inet/inet6 address/port into a string
   */
  static void addr2str(char *const res, size_t res_len, const struct addrinfo *addr, const int no_port) {
    char buf[MAXBUF];
    int port;
    void *src;

    ::memset(res, 0, res_len);
    switch (addr->ai_family) {
      case AF_INET:
        src = static_cast<void *>(&(reinterpret_cast<sockaddr_in *>(addr->ai_addr))->sin_addr.s_addr);
        port = ntohs((reinterpret_cast<sockaddr_in *>(addr->ai_addr))->sin_port);
        if (inet_ntop(AF_INET, src, buf, MAXBUF - 1) == nullptr) strncpy(buf, "(UNKNOWN)", MAXBUF - 1);
        break;
      case AF_INET6:
        src = static_cast<void *>(&(reinterpret_cast<sockaddr_in6 *>(addr->ai_addr))->sin6_addr.s6_addr);
        port = ntohs((reinterpret_cast<sockaddr_in6 *>(addr->ai_addr))->sin6_port);
        if (IN6_IS_ADDR_V4MAPPED(&((reinterpret_cast<sockaddr_in6 *>(addr->ai_addr))->sin6_addr))) {
          src = static_cast<void *>(&(reinterpret_cast<sockaddr_in6 *>(addr->ai_addr))->sin6_addr.s6_addr[12]);
          if (inet_ntop(AF_INET, src, buf, MAXBUF - 1) == nullptr) strncpy(buf, "(UNKNOWN)", MAXBUF - 1);
        } else {
          if (inet_ntop(AF_INET6, src, buf, MAXBUF - 1) == nullptr) strncpy(buf, "(UNKNOWN)", MAXBUF - 1);
        }
        break;
      case AF_UNIX:
        strncpy(buf, reinterpret_cast<char *>(addr->ai_addr), MAXBUF - 1);
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
  static bool HostnameToIp(const char *hostname, char *ip) {
    struct hostent *he;
    struct in_addr **addr_list;
    int i;

    if ((he = gethostbyname(hostname)) == nullptr) {
      // get the host info

      return false;
    }
    addr_list = reinterpret_cast<in_addr **>(he->h_addr_list);
    for (i = 0; addr_list[i] != nullptr; i++) {
      // Return the first one;
      strcpy(ip, inet_ntoa(*addr_list[i]));
      return true;
    }

    return false;
  }

  inline static bool equalSockAddr(sockaddr *addr1, sockaddr *addr2,
                                   bool compare_port = true) {
    if (addr1->sa_family != addr2->sa_family) return false;
    if (addr1->sa_family == AF_UNIX) {
      auto a1_un = reinterpret_cast<sockaddr_un *>(addr1);
      auto a2_un = reinterpret_cast<sockaddr_un *>(addr2);
      int r = strcmp(a1_un->sun_path, a2_un->sun_path);
      if (r != 0) return r;
    } else if (addr1->sa_family == AF_INET) {
      auto a1_in = reinterpret_cast<sockaddr_in *>(addr1);
      auto a2_in = reinterpret_cast<sockaddr_in *>(addr2);
      if (ntohl(a1_in->sin_addr.s_addr) != ntohl(a2_in->sin_addr.s_addr))
        return false;
      if (compare_port && ntohs(a1_in->sin_port) != ntohs(a2_in->sin_port))
        return false;
    } else if (addr1->sa_family == AF_INET6) {
      auto a1_in6 = reinterpret_cast<sockaddr_in6 *>(addr1);
      auto a2_in6 = reinterpret_cast<sockaddr_in6 *>(addr2);
      int r = memcmp(a1_in6->sin6_addr.s6_addr, a2_in6->sin6_addr.s6_addr,
                     sizeof(a1_in6->sin6_addr.s6_addr));
      if (r != 0) return r;
      if (compare_port && ntohs(a1_in6->sin6_port) != ntohs(a2_in6->sin6_port))
        return false;
      if (a1_in6->sin6_flowinfo != a2_in6->sin6_flowinfo) return false;
      if (a1_in6->sin6_scope_id != a2_in6->sin6_scope_id) return false;
    } else {
      return false;
    }
    return true;
  }

  inline static bool equalSockAddr(addrinfo *x, addrinfo *y,
                                   bool compare_port = true) {
    return equalSockAddr(x->ai_addr, y->ai_addr, compare_port);
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
      Logger::LogInfo(error);
      return false;
    }
    return true;
  }

  inline static bool setSocketTimeOut(int sock_fd, unsigned int seconds) {
    struct timeval tv;
    tv.tv_sec = seconds; /* 30 Secs Timeout */
    return setsockopt(sock_fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(timeval)) != -1;
  }

  inline static bool setSoReuseAddrOption(int sock_fd) {
    int flag = 1;
    return setsockopt(sock_fd, SOL_SOCKET, SO_REUSEADDR, &flag, sizeof(flag)) != -1;
  }

  inline static bool setTcpReusePortOption(int sock_fd) {
    int flag = 1;
    return setsockopt(sock_fd, SOL_SOCKET, SO_REUSEPORT, &flag, sizeof(flag)) !=
           -1;
  }

  inline static bool setTcpNoDelayOption(int sock_fd) {
    int flag = 1;
    return setsockopt(sock_fd, IPPROTO_TCP, TCP_NODELAY, &flag, sizeof(flag)) != -1;
  }

  inline static bool setTcpDeferAcceptOption(int sock_fd) {
    int flag = 5;
    return setsockopt(sock_fd, SOL_TCP, TCP_DEFER_ACCEPT, &flag, sizeof(flag)) != -1;
  }

  inline static bool setSoKeepAliveOption(int sock_fd) {
    int flag = 1;
    return setsockopt(sock_fd, SOL_SOCKET, SO_KEEPALIVE, &flag, sizeof(flag)) != -1;
  }
  inline static bool setSoLingerOption(int sock_fd, bool enable = false) {
    struct linger l {};
    l.l_onoff = enable ? 1 : 0;
    l.l_linger = enable ? 10 : 0;
    return setsockopt(sock_fd, SOL_SOCKET, SO_LINGER, &l, sizeof(l)) != -1;
  }

  inline static bool setTcpLinger2Option(int sock_fd) {
    int flag = 5;
    return setsockopt(sock_fd, SOL_SOCKET, TCP_LINGER2, &flag, sizeof(flag)) != -1;
  }

  /*useful for use with send file, wait 200 ms to to fill TCP packet*/
  inline static bool setTcpCorkOption(int sock_fd) {
    int flag = 1;
    return setsockopt(sock_fd, IPPROTO_TCP, TCP_CORK, &flag, sizeof(flag)) != -1;
  }
#ifdef SO_ZEROCOPY
  /*useful for use with send file, wait 200 ms to to fill TCP packet*/
  inline static bool setSoZeroCopy(int sock_fd) {
    int flag = 1;
    return setsockopt(sock_fd, SOL_SOCKET, SO_ZEROCOPY, &flag, sizeof(flag)) != -1;
  }
#endif
  // set netfilter mark, need root privileges
  inline static bool setSOMarkOption(int sock_fd, int nf_mark) {
    // enter_suid()/leave_suid().
    return nf_mark != 0 && setsockopt(sock_fd, SOL_SOCKET, SO_MARK, &nf_mark, sizeof(nf_mark)) != -1;
  }
  inline static bool isConnected(int sock_fd) {
    int error_code = -1;
    socklen_t error_code_size = sizeof(error_code);
    return ::getsockopt(sock_fd, SOL_SOCKET, SO_ERROR, &error_code, &error_code_size) != -1 && error_code == 0;
  }
  /*return -1 in case of erro and set errno*/
  inline static int getSocketSendBufferSize(int socket_fd) {
    int res, size;
    unsigned int m = sizeof(size);
    res = getsockopt(socket_fd, SOL_SOCKET, SO_SNDBUF, &size, &m);
    return res != 0 ? -1 : size;
  }

  /*return -1 in case of erro and set errno*/
  inline static int getSocketReceiveBufferSize(int socket_fd) {
    int res, size;
    unsigned int m = sizeof(size);
    res = getsockopt(socket_fd, SOL_SOCKET, SO_RCVBUF, &size, &m);
    return res != 0 ? -1 : size;
  }

  inline static int setSocketSendBufferSize(int socket_fd, unsigned int new_size) {
    unsigned int m = sizeof(new_size);
    return ::setsockopt(socket_fd, SOL_SOCKET, SO_SNDBUF, &new_size, m) != -1;
  }

  inline static int setSocketReceiveBufferSize(int socket_fd, unsigned int new_size) {
    unsigned int m = sizeof(new_size);
    return ::setsockopt(socket_fd, SOL_SOCKET, SO_RCVBUF, &new_size, m) != -1;
  }
};
