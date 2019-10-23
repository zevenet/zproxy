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

#include "connection.h"
#include "../util/common.h"
#include "../util/network.h"
#include <sys/un.h>

#define PRINT_BUFFER_SIZE \
  Debug::LogInfo("BUFFER::SIZE = " + std::to_string(buffer_size), LOG_DEBUG);
//  Logger::LogInfo("BUFFER::STRLEN = " + std::to_string(strlen(buffer)),
//  LOG_DEBUG);

Connection::Connection()
    : buffer_size(0),
      address(nullptr),
      last_read_(0),
      last_write_(0),
      // string_buffer(),
      address_str(""),
      is_connected(false),
      ssl(nullptr),
      ssl_connected(false) {
  // address.ai_addr = new sockaddr();
}
Connection::~Connection() {
  is_connected = false;
  if (ssl != nullptr) {
    SSL_shutdown(ssl);
    SSL_clear(ssl);
    SSL_free(ssl);
#if USE_SSL_BIO_BUFFER
    if (sbio != nullptr) {
      BIO_vfree(sbio);
      sbio = nullptr;
    }
    if (io != nullptr) {
      BIO_free(io);
      io = nullptr;
    }
    if (ssl_bio != nullptr) {
      BIO_free(ssl_bio);
      ssl_bio = nullptr;
    }
#endif
  }
  if (fd_ > 0) this->closeConnection();
  if (address != nullptr) {
    if (address->ai_addr != nullptr) delete address->ai_addr;
  }
  delete address;
}

IO::IO_RESULT Connection::read() {
  bool done = false;
  ssize_t count;
  IO::IO_RESULT result = IO::IO_RESULT::ERROR;
  //  PRINT_BUFFER_SIZE
  while (!done) {
    count = ::recv(fd_, buffer + buffer_size, MAX_DATA_SIZE - buffer_size,
                   MSG_NOSIGNAL);
    if (count < 0) {
      if (errno != EAGAIN && errno != EWOULDBLOCK) {
        std::string error = "read() failed  ";
        error += std::strerror(errno);
        Logger::LogInfo(error, LOG_NOTICE);
        result = IO::IO_RESULT::ERROR;
      } else {
        result = IO::IO_RESULT::DONE_TRY_AGAIN;
      }
      done = true;
    } else if (count == 0) {
      //  The  remote has closed the connection, wait for EPOLLRDHUP
      done = true;
      result = IO::IO_RESULT::FD_CLOSED;
    } else {
      // PRINT_BUFFER_SIZE
      buffer_size += static_cast<size_t>(count);
      // PRINT_BUFFER_SIZE
      if ((MAX_DATA_SIZE - buffer_size) == 0) {
        //        PRINT_BUFFER_SIZE
        //        Logger::LogInfo("Buffer maximum size reached !!", LOG_DEBUG);
        return IO::IO_RESULT::FULL_BUFFER;
      } else
        result = IO::IO_RESULT::SUCCESS;
      done = true;
    }
  }
  // PRINT_BUFFER_SIZE
  return result;
}

std::string Connection::getPeerAddress() {
  if (this->fd_ > 0 && address_str.empty()) {
	char addr[150];
	Network::getPeerAddress(this->fd_, addr, 150);
    address_str = std::string(addr);
  }
  return address_str;
}

std::string Connection::getLocalAddress() {
  if (this->fd_ > 0 && local_address_str.empty()) {
	char addr[150];
	Network::getlocalAddress(this->fd_, addr, 150);
    local_address_str = std::string(addr);
  }
  return local_address_str;
}

int Connection::getPeerPort() {
  if (this->fd_ > 0 && port == -1) {
    port = Network::getPeerPort(this->fd_);
  }
  return port;
}
int Connection::getLocalPort() {
  if (this->fd_ > 0 && local_port == -1) {
    local_port = Network::getlocalPort(this->fd_);
  }
  return local_port;
}

#if ENABLE_ZERO_COPY
#if !FAKE_ZERO_COPY
IO::IO_RESULT Connection::zeroRead() {
  IO::IO_RESULT result = IO::IO_RESULT::ZERO_DATA;
  for (;;) {
    if (splice_pipe.bytes >= BUFSZ) {
      result = IO::IO_RESULT::FULL_BUFFER;
      break;
    }
    auto n = splice(fd_, nullptr, splice_pipe.pipe[1], nullptr, BUFSZ,
                    SPLICE_F_NONBLOCK | SPLICE_F_MOVE);
    if (n > 0) splice_pipe.bytes += n;
    if (n == 0) break;
    if (n < 0) {
      if (errno == EAGAIN || errno == EWOULDBLOCK) {
        result = IO::IO_RESULT::DONE_TRY_AGAIN;
        break;
      }
      result = IO::IO_RESULT::ERROR;
      break;
    }
  }
  Logger::logmsg(LOG_REMOVE, "ZERO READ write %d  buffer %d", splice_pipe.bytes,
                buffer_size);
  return result;
}

IO::IO_RESULT Connection::zeroWrite(int dst_fd,
                                    http_parser::HttpData &http_data) {
  //  Logger::LogInfo("ZERO_BUFFER::SIZE = " + std::to_string(splice_pipe.bytes),
  //  LOG_DEBUG);

  Logger::logmsg(LOG_REMOVE, "ZERO WRITE write %d  left %d  buffer %d",
                splice_pipe.bytes, http_data.message_bytes_left, buffer_size);
  while (splice_pipe.bytes > 0) {
    int bytes = splice_pipe.bytes;
    if (bytes > BUFSZ) bytes = BUFSZ;
    auto n = ::splice(splice_pipe.pipe[0], nullptr, dst_fd, nullptr, bytes,
                      SPLICE_F_NONBLOCK | SPLICE_F_MOVE);
    //    Logger::LogInfo("ZERO_BUFFER::SIZE = " +
    //    std::to_string(splice_pipe.bytes), LOG_DEBUG);
    if (n == 0) break;
    if (n < 0) {
      if (errno == EAGAIN || errno == EWOULDBLOCK)
        return IO::IO_RESULT::DONE_TRY_AGAIN;
      return IO::IO_RESULT::ERROR;
    }
    splice_pipe.bytes -= n;
    http_data.message_bytes_left -= n;
  }
  /* bytes > 0, add dst to epoll set */
  /* else remove if it was added */
  return IO::IO_RESULT::SUCCESS;
}

#else
IO::IO_RESULT Connection::zeroRead() {
  IO::IO_RESULT result = IO::IO_RESULT::ZERO_DATA;
  //  Logger::logmsg(LOG_REMOVE, "ZERO READ IN %d  buffer %d", splice_pipe.bytes,
  //  buffer_size);
  for (;;) {
    if (splice_pipe.bytes >= BUFSZ) {
      result = IO::IO_RESULT::FULL_BUFFER;
      break;
    }
    auto n =
        ::read(fd_, buffer_aux + splice_pipe.bytes, BUFSZ - splice_pipe.bytes);
    if (n > 0) splice_pipe.bytes += n;
    if (n == 0) break;
    if (n < 0) {
      if (errno == EAGAIN || errno == EWOULDBLOCK) {
        result = IO::IO_RESULT::DONE_TRY_AGAIN;
        break;
      }
      result = IO::IO_RESULT::ERROR;
      break;
    }
  }
  //  Logger::logmsg(LOG_REMOVE, "ZERO READ OUT %d  buffer %d",
  //  splice_pipe.bytes, buffer_size);
  return result;
}

IO::IO_RESULT Connection::zeroWrite(int dst_fd,
                                    http_parser::HttpData &http_data) {
  //  Logger::logmsg(LOG_REMOVE, "ZERO WRITE write %d  left %d  buffer %d",
  //  splice_pipe.bytes, http_data.message_bytes_left, buffer_size);
  int sent = 0;
  while (splice_pipe.bytes > 0) {
    int bytes = splice_pipe.bytes;
    if (bytes > BUFSZ) bytes = BUFSZ;
    auto n = ::write(dst_fd, buffer_aux + sent, bytes - sent);
    if (n == 0) break;
    if (n < 0) {
      if (errno == EAGAIN || errno == EWOULDBLOCK)
        return IO::IO_RESULT::DONE_TRY_AGAIN;
      return IO::IO_RESULT::ERROR;
    }
    splice_pipe.bytes -= n;
    http_data.message_bytes_left -= n;
    sent += n;
  }
  /* bytes > 0, add dst to epoll set */
  /* else remove if it was added */
  return IO::IO_RESULT::SUCCESS;
}
#endif
#endif
IO::IO_RESULT Connection::writeTo(int fd, size_t &sent) {
  bool done = false;
  sent = 0;
  ssize_t count;
  IO::IO_RESULT result = IO::IO_RESULT::ERROR;
  //  PRINT_BUFFER_SIZE
  while (!done) {
    count = ::send(fd, buffer + sent, buffer_size - sent, MSG_NOSIGNAL);
    if (count < 0) {
      if (errno != EAGAIN && errno != EWOULDBLOCK /* && errno != EPIPE &&
          errno != ECONNRESET*/) {
        std::string error = "write() failed  ";
        error += std::strerror(errno);
        Logger::LogInfo(error, LOG_NOTICE);
        result = IO::IO_RESULT::ERROR;
      } else {
        result = IO::IO_RESULT::DONE_TRY_AGAIN;
      }
      done = true;
      break;
    } else if (count == 0) {
      done = true;
      break;
    } else {
      sent += static_cast<size_t>(count);
      result = IO::IO_RESULT::SUCCESS;
    }
  }
  if (sent > 0 && result != IO::IO_RESULT::ERROR) {
	buffer_size -= sent;
  }
  //  PRINT_BUFFER_SIZE
  return result;
}

IO::IO_RESULT Connection::writeTo(int target_fd,
                                  http_parser::HttpData &http_data) {
  //  PRINT_BUFFER_SIZE
  if (http_data.iov_size == 0) http_data.prepareToSend();

  size_t nwritten = 0;
  size_t iovec_written = 0;

  auto result = writeIOvec(target_fd, &http_data.iov[0], http_data.iov_size,
                           iovec_written, nwritten);
  //  Logger::logmsg(LOG_REMOVE, "IOV size: %d iov written %d bytes_written: %d
  //  IO RESULT: %s\n", http_data.iov.size(),
  //                iovec_written, nwritten,
  //                IO::getResultString(result).data());
  if (result != IO::IO_RESULT::SUCCESS) return result;

  buffer_size = 0;  // buffer_offset;
  http_data.message_length = 0;
  http_data.setHeaderSent(true);
#if PRINT_DEBUG_FLOW_BUFFERS
  Logger::logmsg(LOG_REMOVE, "\tbuffer offset: %d", buffer_offset);
  Logger::logmsg(LOG_REMOVE, "\tOut buffer size: %d", buffer_size);
  Logger::logmsg(LOG_REMOVE, "\tbuffer offset: %d", buffer_offset);
  Logger::logmsg(LOG_REMOVE, "\tcontent length: %d", http_data.content_length);
  Logger::logmsg(LOG_REMOVE, "\tmessage length: %d", http_data.message_length);
  Logger::logmsg(LOG_REMOVE, "\tmessage bytes left: %d",
                http_data.message_bytes_left);
#endif
  //    PRINT_BUFFER_SIZE
  return IO::IO_RESULT::SUCCESS;
}

IO::IO_RESULT Connection::writeIOvec(int target_fd, iovec *iov,
                                     size_t iovec_size, size_t &iovec_written,
                                     size_t &nwritten) {
  IO::IO_RESULT result = IO::IO_RESULT::ERROR;
  ssize_t count = 0;
  auto nvec = iovec_size;
  nwritten = 0;
  iovec_written = 0;
  do {
    count = ::writev(target_fd, &(iov[iovec_written]),
                     static_cast<int>(nvec - iovec_written));
    //    Logger::logmsg(LOG_REMOVE,
    //                  "writev() count %d errno: %d = %s iovecwritten %d",
    //                  count,
    //                  errno,
    //                  std::strerror(errno),
    //                  iovec_written);
    if (count < 0) {
      if (count == -1 && (errno == EAGAIN || errno == EWOULDBLOCK)) {
        result = IO::IO_RESULT::DONE_TRY_AGAIN;  // do not persist changes
      } else {
        std::string error = "writev() failed  ";
        error += std::strerror(errno);
        Logger::LogInfo(error, LOG_NOTICE);
        result = IO::IO_RESULT::ERROR;
      }
      break;
    } else {
      auto remaining = static_cast<size_t>(count);
      for (auto it = iovec_written; it != iovec_size; it++) {
        if (remaining >= iov[it].iov_len) {
          remaining -= iov[it].iov_len;
          //          iov.erase(it++);
          iov[it].iov_len = 0;
          iovec_written++;
        } else {
          Logger::logmsg(LOG_REMOVE,
                        "Recalculating data ... remaining %d niovec_written: "
                        "%d iov size %d",
                        remaining, iovec_written, iovec_size);
          iov[it].iov_len -= remaining;
          iov[it].iov_base =
              static_cast<char *>(iov[iovec_written].iov_base) + remaining;
          break;
        }
      }

      nwritten += static_cast<size_t>(count);
      if (errno == EINPROGRESS && remaining != 0)
        return IO::IO_RESULT::DONE_TRY_AGAIN;
      else
        result = IO::IO_RESULT::SUCCESS;
#if PRINT_DEBUG_FLOW_BUFFERS
      Logger::logmsg(
          LOG_REMOVE,
          "# Headers sent, size: %d iovec_written: %d nwritten: %d IO::RES %s",
          nvec, iovec_written, nwritten, IO::getResultString(result).data());
#endif
    }
  } while (iovec_written < nvec);

  return result;
}

IO::IO_RESULT Connection::writeTo(const Connection &target_connection,
                                  http_parser::HttpData &http_data) {
  return writeTo(target_connection.getFileDescriptor(), http_data);
}

IO::IO_RESULT Connection::write(const char *data, size_t size) {
  bool done = false;
  size_t sent = 0;
  ssize_t count;
  IO::IO_RESULT result = IO::IO_RESULT::ERROR;

  //  PRINT_BUFFER_SIZE
  while (!done) {
    count = ::send(fd_, data + sent, size - sent, MSG_NOSIGNAL);
    if (count < 0) {
      if (errno != EAGAIN && errno != EWOULDBLOCK /* && errno != EPIPE &&
          errno != ECONNRESET*/) {
        std::string error = "write() failed  ";
        error += std::strerror(errno);
        Logger::LogInfo(error, LOG_NOTICE);
        result = IO::IO_RESULT::ERROR;
      } else {
        result = IO::IO_RESULT::DONE_TRY_AGAIN;
      }
      done = true;
      break;
    } else if (count == 0) {
      done = true;
      break;
    } else {
      sent += static_cast<size_t>(count);
      result = IO::IO_RESULT::SUCCESS;
    }
  }
  //  PRINT_BUFFER_SIZE
  return result;
}

void Connection::closeConnection() {
  is_connected = false;
  if (fd_ > 0) {
    //    ::shutdown(fd_, 2);
    ::close(fd_);
  }
}
IO::IO_OP Connection::doConnect(addrinfo &address_, int timeout, bool async) {
  int result = -1;
  if ((fd_ = socket(address_.ai_family, SOCK_STREAM, 0)) < 0) {
    Logger::logmsg(LOG_WARNING, "socket() failed ");
    return IO::IO_OP::OP_ERROR;
  }
  Network::setTcpNoDelayOption(fd_);
  Network::setSoKeepAliveOption(fd_);
  Network::setSoLingerOption(fd_, true);
  if (LIKELY(async)) Network::setSocketNonBlocking(fd_);
  if ((result = ::connect(fd_, address_.ai_addr, sizeof(address_))) < 0) {
    if (errno == EINPROGRESS && timeout > 0) {
      return IO::IO_OP::OP_IN_PROGRESS;

    } else {
      Logger::logmsg(LOG_NOTICE, " %s connect()  error: %s\n",
                     this->getPeerAddress().data(), errno, strerror(errno));
      return IO::IO_OP::OP_ERROR;
    }
  }
  // Create stream object if connected
  return result != -1 ? IO::IO_OP::OP_SUCCESS : IO::IO_OP::OP_ERROR;
}

IO::IO_OP Connection::doConnect(const std::string &af_unix_socket_path,
                                int timeout) {
  int result = -1;
  if ((fd_ = socket(AF_UNIX, SOCK_STREAM, 0)) < 0) {
    Logger::logmsg(LOG_WARNING, "socket() failed ");
    return IO::IO_OP::OP_ERROR;
  }
  Network::setTcpNoDelayOption(fd_);
  Network::setSoKeepAliveOption(fd_);
  Network::setSoLingerOption(fd_, true);

  if (timeout > 0) Network::setSocketNonBlocking(fd_);

  sockaddr_un server_address{};
  strcpy(server_address.sun_path, af_unix_socket_path.c_str());
  server_address.sun_family = AF_UNIX;
  if ((result = ::connect(fd_, (struct sockaddr *) &server_address,
						  SUN_LEN(&server_address))) < 0) {
    if (errno == EINPROGRESS && timeout > 0) {
      return IO::IO_OP::OP_IN_PROGRESS;
    } else {
      Logger::logmsg(LOG_NOTICE, "connect() error %d - %s\n", errno,
                    strerror(errno));
      return IO::IO_OP::OP_ERROR;
    }
  }
  return result != -1 ? IO::IO_OP::OP_SUCCESS : IO::IO_OP::OP_ERROR;
}

bool Connection::isConnected() {
  if (fd_ > 0)
    return Network::isConnected(this->fd_);
  else
    return false;
}

int Connection::doAccept() {
  int new_fd = -1;
  sockaddr_in peer_address{};
  socklen_t peer_addr_length = sizeof(peer_address);

  if ((new_fd = accept4(fd_, (sockaddr *)&peer_address, &peer_addr_length,
                        SOCK_NONBLOCK | SOCK_CLOEXEC)) < 0) {
    if ((errno == EAGAIN) || (errno == EWOULDBLOCK)) {
      return 0;  // We have processed all incoming connections.
    }
    Logger::logmsg(LOG_NOTICE, "accept() failed  %s", std::strerror(errno));
    // break;
    return -1;
  }

  if (peer_address.sin_family == AF_INET ||
      peer_address.sin_family == AF_INET6 ||
      peer_address.sin_family == AF_UNIX) {
    Network::setTcpNoDelayOption(new_fd);
    Network::setSoKeepAliveOption(new_fd);
    Network::setSoLingerOption(new_fd, true);
    return new_fd;
  } else {
    ::close(new_fd);
    Logger::logmsg(LOG_WARNING, "HTTP connection prematurely closed by peer");
  }
  return -1;
}
bool Connection::listen(const std::string &address_str_, int port_) {
  this->address = Network::getAddress(address_str_, port_);
  if (this->address != nullptr) return listen(*this->address);
  return false;
}

bool Connection::listen(addrinfo &address_) {
  this->address = &address_;
  /* prepare the socket */
  if ((fd_ = socket(this->address->ai_family == AF_INET ? PF_INET : PF_INET6,
                    SOCK_STREAM, 0)) < 0) {
    Logger::logmsg(LOG_ERR, "socket () failed %s s - aborted", strerror(errno));
    return false;
  }

  Network::setSoLingerOption(fd_);
  Network::setSoReuseAddrOption(fd_);
  Network::setTcpDeferAcceptOption(fd_);
  Network::setTcpReusePortOption(fd_);

  if (::bind(fd_, address->ai_addr,
             static_cast<socklen_t>(address->ai_addrlen)) < 0) {
    Logger::logmsg(LOG_ERR, "bind () failed %s s - aborted", strerror(errno));
    ::close(fd_);
    fd_ = -1;
    return false;
  }
  ::listen(fd_, SOMAXCONN);
  return true;
}
bool Connection::listen(const std::string &af_unix_name) {
  if (af_unix_name.empty()) return false;
  // unlink possible previously created path.
  ::unlink(af_unix_name.c_str());

  // Initialize AF_UNIX socket
  sockaddr_un ctrl{};
  ::memset(&ctrl, 0, sizeof(ctrl));
  ctrl.sun_family = AF_UNIX;
  ::strncpy(ctrl.sun_path, af_unix_name.c_str(), sizeof(ctrl.sun_path) - 1);

  if ((fd_ = ::socket(PF_UNIX, SOCK_STREAM, 0)) < 0) {
    Logger::logmsg(LOG_ERR, "Control \"%s\" create: %s", ctrl.sun_path,
                  strerror(errno));
    return false;
  }
  if (::bind(fd_, (struct sockaddr *)&ctrl, (socklen_t)sizeof(ctrl)) < 0) {
    Logger::logmsg(LOG_ERR, "Control \"%s\" bind: %s", ctrl.sun_path,
                  strerror(errno));
    return false;
  }
  ::listen(fd_, SOMAXCONN);

  return false;
}
