//
// Created by abdess on 4/5/18.
//

#include "connection.h"
#include "../util/Network.h"
#include <sys/un.h>

#define PRINT_BUFFER_SIZE                                                      \
  Debug::LogInfo("BUFFER::SIZE = " + std::to_string(buffer_size), LOG_DEBUG);
//  Debug::LogInfo("BUFFER::STRLEN = " + std::to_string(strlen(buffer)), LOG_DEBUG);

Connection::Connection()
    : buffer_size(0), address(nullptr), last_read_(0), last_write_(0),
      // string_buffer(),
      address_str(""), is_connected(false) {
  // address.ai_addr = new sockaddr();
}
Connection::~Connection() {
  is_connected = false;
  if (fd_ > 0)
    this->closeConnection();
  if (address != nullptr) {
    if (address->ai_addr != nullptr)
      delete address->ai_addr;
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
        Debug::LogInfo(error, LOG_NOTICE);
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
        PRINT_BUFFER_SIZE
        Debug::LogInfo("Buffer maximum size reached !!", LOG_DEBUG);
        return IO::IO_RESULT::FULL_BUFFER;
      } else
        result = IO::IO_RESULT::SUCCESS;
      done = true;
    }
  }
  //PRINT_BUFFER_SIZE
  return result;
}

std::string Connection::getPeerAddress() {
  if (this->fd_ > 0 && address_str.empty()) {
    char addr[50];
    Network::getPeerAddress(this->fd_, addr, 50);
    address_str = std::string(addr);
  }
  return address_str;
}



#if ENABLE_ZERO_COPY

IO::IO_RESULT Connection::zeroRead() {

  for (;;) {
    if(splice_pipe.bytes >= BUFSZ){
      return  IO::IO_RESULT::FULL_BUFFER;
    }
    auto n = splice(fd_, nullptr, splice_pipe.pipe[1], nullptr, BUFSZ,
                   SPLICE_F_NONBLOCK | SPLICE_F_MOVE);
    if (n > 0)
      splice_pipe.bytes += n;
    if (n == 0)
      return IO::IO_RESULT::FD_CLOSED;
    if (n < 0) {
      if (errno == EAGAIN || errno == EWOULDBLOCK)
        return IO::IO_RESULT::DONE_TRY_AGAIN;
      return IO::IO_RESULT::ERROR;
    }
  }
  return IO::IO_RESULT::SUCCESS;
}

IO::IO_RESULT Connection::zeroWrite(int dst_fd,
                                    http_parser::HttpData &http_data) {
//  Debug::LogInfo("ZERO_BUFFER::SIZE = " + std::to_string(splice_pipe.bytes), LOG_DEBUG);
  while (splice_pipe.bytes > 0) {
    int bytes = splice_pipe.bytes;
    if (bytes > BUFSZ)
      bytes = BUFSZ;
    auto n = ::splice(splice_pipe.pipe[0], nullptr, dst_fd, nullptr, bytes,
                     SPLICE_F_NONBLOCK | SPLICE_F_MOVE);
//    Debug::LogInfo("ZERO_BUFFER::SIZE = " + std::to_string(splice_pipe.bytes), LOG_DEBUG);
    if (n == 0)
      break;
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

#endif
IO::IO_RESULT Connection::writeTo(int fd) {

  bool done = false;
  size_t sent = 0;
  ssize_t count;
  IO::IO_RESULT result = IO::IO_RESULT::ERROR;

  //  Debug::LogInfo("#IN#bufer_size" +
  //  std::to_string(string_buffer.string().length()));
  PRINT_BUFFER_SIZE
  while (!done) {
    count = ::send(fd, buffer + sent, buffer_size - sent, MSG_NOSIGNAL);
    if (count < 0) {
      if (errno != EAGAIN && errno != EWOULDBLOCK /* && errno != EPIPE &&
          errno != ECONNRESET*/) {  // TODO:: What to do if connection closed
        std::string error = "write() failed  ";
        error += std::strerror(errno);
        Debug::LogInfo(error, LOG_NOTICE);
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
    //    string_buffer.erase(static_cast<unsigned int>(sent));
  }
  //  Debug::LogInfo("#OUT#bufer_size" +
  //  std::to_string(string_buffer.string().length()));
  PRINT_BUFFER_SIZE
  return result;
}

IO::IO_RESULT Connection::writeContentTo(const Connection &target_connection,
                                         http_parser::HttpData &http_data) {
  bool done = false;
  size_t sent = 0;
  auto total_to_send = http_data.message_bytes_left > buffer_size
                           ? buffer_size
                           : http_data.message_bytes_left;
  ssize_t count;
  IO::IO_RESULT result = IO::IO_RESULT::ERROR;
  PRINT_BUFFER_SIZE
  while (!done) {
    count = ::send(target_connection.getFileDescriptor(), buffer + sent,
                   total_to_send, MSG_NOSIGNAL);
    if (count < 0) {
      if (errno != EAGAIN && errno != EWOULDBLOCK /* && errno != EPIPE &&
          errno != ECONNRESET*/) {  // TODO:: What to do if connection closed
        std::string error = "write() failed  ";
        error += std::strerror(errno);
        Debug::LogInfo(error, LOG_NOTICE);
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
      result = IO::IO_RESULT::SUCCESS;
      sent += static_cast<size_t>(count);
      total_to_send -= count;
      buffer_size -= count;
      http_data.message_bytes_left -= count;
    }
  }
  PRINT_BUFFER_SIZE
  return result;
}

IO::IO_RESULT Connection::writeTo(int target_fd,
                                  http_parser::HttpData &http_data) {
//  PRINT_BUFFER_SIZE
  const char *return_value = "\r\n";
  auto vector_size = http_data.num_headers +
                     (http_data.message_length > 0 ? 3 : 2) +
                     http_data.extra_headers.size();
  iovec iov[vector_size];
  char *last_buffer_pos_written;

  int total_to_send = 0;
  iov[0].iov_base = http_data.http_message;
  iov[0].iov_len = http_data.http_message_length;
  total_to_send += http_data.http_message_length;
  int x = 1;
  for (size_t i = 0; i != http_data.num_headers; i++) {
    if (http_data.headers[i].header_off)
      continue; // skip unwanted headers
    if (helper::headerEqual(http_data.headers[i],
                            http::http_info::headers_names_strings.at(
                                http::HTTP_HEADER_NAME::CONTENT_LENGTH))) {
      http_data.message_bytes_left =
          static_cast<size_t>(std::atoi(http_data.headers[i].value));
    }
    iov[x].iov_base = const_cast<char *>(http_data.headers[i].name);
    iov[x++].iov_len = http_data.headers[i].line_size;
    total_to_send += http_data.headers[i].line_size;
  }
  for (auto &header :
       http_data.extra_headers) { // header must be always  used as reference,
    // it's copied it invalidate c_str() reference.
    iov[x].iov_base = const_cast<char *>(header.second.c_str());
    iov[x++].iov_len = header.second.length();
    total_to_send += header.second.length();
  }
  iov[x].iov_base = const_cast<char *>(return_value);
  iov[x++].iov_len = 2;
  total_to_send += 2;

  last_buffer_pos_written =
      const_cast<char *>(
          http_data.headers[http_data.num_headers - 1].name +
          http_data.headers[http_data.num_headers - 1].line_size) +
      2;
//  Debug::logmsg(LOG_REMOVE,"last_buffer_pos_written = %p " ,last_buffer_pos_written);
  if (http_data.message_length > 0) {
    iov[x].iov_base = http_data.message;
    iov[x++].iov_len = http_data.message_length;
    last_buffer_pos_written += http_data.message_length;
    total_to_send += http_data.message_length;
    http_data.message_bytes_left -= http_data.message_length;
  }
//  Debug::logmsg(LOG_REMOVE,"last_buffer_pos_written = %p " ,last_buffer_pos_written);
  ssize_t nwritten = ::writev(target_fd, iov, x);

  if (nwritten < 0) {
    if (errno != EAGAIN && errno != EWOULDBLOCK /* && errno != EPIPE &&
          errno != ECONNRESET*/) {  // TODO:: What to do if connection closed
      std::string error = "write() failed  ";
      error += std::strerror(errno);
      Debug::LogInfo(error, LOG_NOTICE);
      return IO::IO_RESULT::ERROR;
    } else {
      return IO::IO_RESULT::DONE_TRY_AGAIN;
    }
  } else if (nwritten != total_to_send) {
    return IO::IO_RESULT::ERROR;
  }
//  Debug::logmsg(LOG_REMOVE,"last_buffer_pos_written = %p " ,last_buffer_pos_written);
//  Debug::logmsg(LOG_REMOVE,"http_data.buffer = %p " ,http_data.buffer);
  buffer_size -=
      static_cast<size_t>(last_buffer_pos_written - http_data.buffer);
//  PRINT_BUFFER_SIZE
  return IO::IO_RESULT::SUCCESS;
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

  //  Debug::LogInfo("#IN#bufer_size" +
  //  std::to_string(string_buffer.string().length()));
//  PRINT_BUFFER_SIZE
  while (!done) {
    count = ::send(fd_, data + sent, size - sent, MSG_NOSIGNAL);
    if (count < 0) {
      if (errno != EAGAIN && errno != EWOULDBLOCK /* && errno != EPIPE &&
          errno != ECONNRESET*/) {  // TODO:: What to do if connection closed
        std::string error = "write() failed  ";
        error += std::strerror(errno);
        Debug::LogInfo(error, LOG_NOTICE);
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
    //    size -= sent;
    //    string_buffer.erase(static_cast<unsigned int>(sent));
  }
  //  Debug::LogInfo("#OUT#bufer_size" +
  //  std::to_string(string_buffer.string().length()));
//  PRINT_BUFFER_SIZE
  return result;
}

void Connection::closeConnection() {
  is_connected = false;
  if (fd_ > 0) {
    ::shutdown(fd_, 2);
    ::close(fd_);
  }
}
IO::IO_OP Connection::doConnect(addrinfo &address_, int timeout) {
  int result = -1;
  if ((fd_ = socket(address_.ai_family, SOCK_STREAM, 0)) < 0) {
    // TODO::LOG message
    Debug::logmsg(LOG_WARNING, "socket() failed ");
    return IO::IO_OP::OP_ERROR;
  }
  if (timeout > 0)
    Network::setSocketNonBlocking(fd_);
  if ((result = ::connect(fd_, address_.ai_addr, sizeof(address_))) < 0) {
    if (errno == EINPROGRESS && timeout > 0) {
      return IO::IO_OP::OP_IN_PROGRESS;

    } else {
      Debug::logmsg(LOG_NOTICE, "connect() error %d - %s\n", errno,
                    strerror(errno));
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
    // TODO::LOG message
    Debug::logmsg(LOG_WARNING, "socket() failed ");
    return IO::IO_OP::OP_ERROR;
  }
  if (timeout > 0)
    Network::setSocketNonBlocking(fd_);

  struct sockaddr_un serveraddr;
  strcpy(serveraddr.sun_path, af_unix_socket_path.c_str());
  serveraddr.sun_family = AF_UNIX;
  if ((result = ::connect(fd_, (struct sockaddr *)&serveraddr,
                          SUN_LEN(&serveraddr))) < 0) {
    if (errno == EINPROGRESS && timeout > 0) {
      return IO::IO_OP::OP_IN_PROGRESS;

    } else {
      Debug::logmsg(LOG_NOTICE, "connect() error %d - %s\n", errno,
                    strerror(errno));
      return IO::IO_OP::OP_ERROR;
    }
  }
  // Create stream object if connected
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
  sockaddr_in clnt_addr{};
  socklen_t clnt_length = sizeof(clnt_addr);

  if ((new_fd = accept4(fd_, (sockaddr *)&clnt_addr, &clnt_length,
                        SOCK_NONBLOCK | SOCK_CLOEXEC)) < 0) {
    if ((errno == EAGAIN) || (errno == EWOULDBLOCK)) {
      return 0; // We have processed all incoming connections.
    }
    std::string error = "accept() failed  ";
    error += std::strerror(errno);
    Debug::LogInfo(error);
    // break;
    return -1;
  }
  if (clnt_addr.sin_family == AF_INET || clnt_addr.sin_family == AF_INET6 ||
      clnt_addr.sin_family == AF_UNIX) {
    //   TODO::
    return new_fd;
  } else {
    ::close(new_fd);
    Debug::logmsg(LOG_WARNING, "HTTP connection prematurely closed by peer");
  }

  return -1;
}
bool Connection::listen(std::string address_str_, int port) {
  this->address = Network::getAddress(address_str_, port);
  if (this->address != nullptr)
    return listen(*this->address);
  return false;
}

bool Connection::listen(addrinfo &address_) {
  this->address = &address_;
  /* prepare the socket */
  if ((fd_ =
           socket(this->address->ai_family == AF_INET ? PF_INET : PF_INET6,
                  SOCK_STREAM, 0)) < 0) {
    Debug::logmsg(LOG_ERR, "socket () failed %s s - aborted", strerror(errno));
    return false;
  }

  Network::setSoLingerOption(fd_);
  Network::setSoReuseAddrOption(fd_);
  Network::setTcpDeferAcceptOption(fd_);

  if (::bind(fd_, address->ai_addr,
             static_cast<socklen_t>(address->ai_addrlen)) < 0) {
    Debug::logmsg(LOG_ERR, "bind () failed %s s - aborted", strerror(errno));
    ::close(fd_);
    fd_ = -1;
    return false;
  }

  ::listen(fd_, 2048);
  return true;
}
bool Connection::listen(std::string af_unix_name) {
  if (af_unix_name.empty())
    return false;
  // unlink possible previously created path.
  unlink(af_unix_name.c_str());

  // Initialize AF_UNIX socket
  sockaddr_un ctrl{};
  ::memset(&ctrl, 0, sizeof(ctrl));
  ctrl.sun_family = AF_UNIX;
  ::strncpy(ctrl.sun_path, af_unix_name.c_str(), sizeof(ctrl.sun_path) - 1);

  if ((fd_ = ::socket(PF_UNIX, SOCK_STREAM, 0)) < 0) {
    Debug::logmsg(LOG_ERR, "Control \"%s\" create: %s", ctrl.sun_path,
                  strerror(errno));
    return false;
  }
  if (::bind(fd_, (struct sockaddr *)&ctrl, (socklen_t)sizeof(ctrl)) <
      0) {
    Debug::logmsg(LOG_ERR, "Control \"%s\" bind: %s", ctrl.sun_path,
                  strerror(errno));
    return false;
  }
  ::listen(fd_, 512);

  return false;
}
