//
// Created by abdess on 4/5/18.
//

#include "connection.h"
#include <sys/un.h>
#include "../util/Network.h"

#define PRINT_BUFFER_SIZE \
  //  Debug::Log("BUFFER::SIZE = " + std::to_string(buffer_size), LOG_DEBUG); \
//  Debug::Log("BUFFER::STRLEN = " + std::to_string(strlen(buffer)), LOG_DEBUG);

Connection::Connection()
    : buffer_size(0),
      address(nullptr),
      last_read_(0),
      last_write_(0),
      // string_buffer(),
      socket_fd(-1),
      address_str(""),
      is_connected(false) {
  // address.ai_addr = new sockaddr();
}
Connection::~Connection() {
  is_connected = false;
  if (socket_fd > 0) this->closeConnection();
  if (address != nullptr) {
    if (address->ai_addr != nullptr) delete address->ai_addr;
  }
  delete address;
}

IO::IO_RESULT Connection::read() {
  bool done = false;
  ssize_t count;
  IO::IO_RESULT result = IO::ERROR;
  //  Debug::Log("#IN#bufer_size" +
  //  std::to_string(string_buffer.string().length()));
  PRINT_BUFFER_SIZE
  while (!done) {
    count = ::recv(socket_fd, buffer + buffer_size, MAX_DATA_SIZE - buffer_size,
                   MSG_NOSIGNAL);
    if (count == -1) {
      if (errno != EAGAIN && errno != EWOULDBLOCK) {
        std::string error = "read() failed  ";
        error += std::strerror(errno);
        Debug::Log(error, LOG_NOTICE);
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
      buffer_size += static_cast<size_t>(count);
      if ((MAX_DATA_SIZE - buffer_size) < 5) {
        Debug::Log("Buffer maximum size reached !!1", LOG_DEBUG);
        result = IO::FULL_BUFFER;
        break;
      } else
        result = IO::IO_RESULT::SUCCESS;
      done = true;
    }
  }
  PRINT_BUFFER_SIZE
  return result;
}

std::string Connection::getPeerAddress() {
  if (this->socket_fd > 0 && address_str.empty()) {
    char addr[50];
    Network::getPeerAddress(this->socket_fd, addr, 50);
    address_str = std::string(addr);
  }
  return address_str;
}

int Connection::getFileDescriptor() const {
  //  if (socket_fd < 0) {
  //    Debug::Log("Socket no valido, que hacer ....", LOG_REMOVE);
  //  }
  return socket_fd;
}

void Connection::setFileDescriptor(int fd) {
  if (fd < 0) {
    Debug::Log("Esto que es!!", LOG_REMOVE);
  }
  socket_fd = fd;
}

IO::IO_RESULT Connection::writeTo(int fd) {
  bool done = false;
  size_t sent = 0;
  ssize_t count;
  IO::IO_RESULT result = IO::ERROR;

  //  Debug::Log("#IN#bufer_size" +
  //  std::to_string(string_buffer.string().length()));
  PRINT_BUFFER_SIZE
  while (!done) {
    count = ::send(fd, buffer + sent, buffer_size - sent, MSG_NOSIGNAL);
    if (count < 0) {
      if (errno != EAGAIN && errno != EWOULDBLOCK /* && errno != EPIPE &&
          errno != ECONNRESET*/) {  // TODO:: What to do if connection closed
        std::string error = "write() failed  ";
        error += std::strerror(errno);
        Debug::Log(error, LOG_NOTICE);
        result = IO::ERROR;
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
      result = IO::SUCCESS;
    }
  }
  if (sent > 0 && result != IO::ERROR) {
    buffer_size -= sent;
    //    string_buffer.erase(static_cast<unsigned int>(sent));
  }
  //  Debug::Log("#OUT#bufer_size" +
  //  std::to_string(string_buffer.string().length()));
  PRINT_BUFFER_SIZE
  return result;
}
IO::IO_RESULT Connection::write(const char* data,
                                size_t size) {  //}, size_t *sent) {
  bool done = false;
  ssize_t count;
  IO::IO_RESULT result = IO::ERROR;
  int sent = 0;
  while (!done) {
    count = ::send(socket_fd, data + sent, size - sent, MSG_NOSIGNAL);
    if (count < 0) {
      if (errno != EAGAIN && errno != EWOULDBLOCK /* && errno != EPIPE &&
          errno != ECONNRESET*/) {  // TODO:: What to do if connection closes
        std::string error = "write() failed  ";
        error += std::strerror(errno);
        Debug::Log(error, LOG_DEBUG);
        result = IO::DONE_TRY_AGAIN;
      } else {
        result = IO::ERROR;
      }
      done = true;
      break;
    } else if (count == 0) {
      done = true;
      break;
    } else {
      sent += static_cast<size_t>(count);
      result = IO::SUCCESS;
    }
  }

  return result;
}

void Connection::closeConnection() {
  is_connected = false;
  if (socket_fd > 0) {
    ::shutdown(socket_fd, 2);
    ::close(socket_fd);
  }
}
IO::IO_OP Connection::doConnect(addrinfo& address, int timeout) {
  long arg;
  socklen_t len;
  int result = -1, valopt;
  if ((socket_fd = socket(address.ai_family, SOCK_STREAM, 0)) < 0) {
    // TODO::LOG message
    Debug::logmsg(LOG_WARNING, "socket() failed ");
    return IO::OP_ERROR;
  }
  if (timeout > 0) Network::setSocketNonBlocking(socket_fd);
  if ((result = ::connect(socket_fd, address.ai_addr, sizeof(address))) < 0) {
    if (errno == EINPROGRESS && timeout > 0) {
      return IO::OP_IN_PROGRESS;

    } else {
      Debug::logmsg(LOG_NOTICE, "connect() error %d - %s\n", errno,
                    strerror(errno));
      return IO::OP_ERROR;
    }
  }
  // Create stream object if connected
  return result != -1 ? IO::OP_SUCCESS : IO::OP_ERROR;
}

bool Connection::isConnected() {
  if (socket_fd > 0)
    return Network::isConnected(this->socket_fd);
  else
    return false;
}

int Connection::doAccept() {
  int new_fd = -1;
  sockaddr_in clnt_addr{};
  socklen_t clnt_length = sizeof(clnt_addr);

  if ((new_fd = accept4(socket_fd, (sockaddr*)&clnt_addr, &clnt_length,
                        SOCK_NONBLOCK | SOCK_CLOEXEC)) < 0) {
    if ((errno == EAGAIN) || (errno == EWOULDBLOCK)) {
      return 0;  // We have processed all incoming connections.
    }
    std::string error = "accept() failed  ";
    error += std::strerror(errno);
    Debug::Log(error);
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
bool Connection::listen(std::string address_str, int port) {
  this->address = Network::getAddress(address_str, port);
  if (this->address != nullptr) return listen(*this->address);
  return false;
}

bool Connection::listen(addrinfo& address_) {
  this->address = &address_;
  /* prepare the socket */
  if ((socket_fd =
           socket(this->address->ai_family == AF_INET ? PF_INET : PF_INET6,
                  SOCK_STREAM, 0)) < 0) {
    Debug::logmsg(LOG_ERR, "socket () failed %s s - aborted", strerror(errno));
    return false;
  }

  Network::setSoLingerOption(socket_fd);
  Network::setSoReuseAddrOption(socket_fd);
  Network::setTcpDeferAcceptOption(socket_fd);

  if (::bind(socket_fd, address->ai_addr,
             static_cast<socklen_t>(address->ai_addrlen)) < 0) {
    Debug::logmsg(LOG_ERR, "bind () failed %s s - aborted", strerror(errno));
    ::close(socket_fd);
    socket_fd = -1;
    return false;
  }

  ::listen(socket_fd, 2048);
  return true;
}
bool Connection::listen(std::string af_unix_name) {
  if (af_unix_name.empty()) return false;
  // unlink possible previously created path.
  unlink(af_unix_name.c_str());

  // Initialize AF_UNIX socket
  sockaddr_un ctrl{};
  ::memset(&ctrl, 0, sizeof(ctrl));
  ctrl.sun_family = AF_UNIX;
  ::strncpy(ctrl.sun_path, af_unix_name.c_str(), sizeof(ctrl.sun_path) - 1);

  if ((socket_fd = ::socket(PF_UNIX, SOCK_STREAM, 0)) < 0) {
    Debug::logmsg(LOG_ERR, "Control \"%s\" create: %s", ctrl.sun_path,
                  strerror(errno));
    return false;
  }
  if (::bind(socket_fd, (struct sockaddr*)&ctrl, (socklen_t)sizeof(ctrl)) < 0) {
    Debug::logmsg(LOG_ERR, "Control \"%s\" bind: %s", ctrl.sun_path,
                  strerror(errno));
    return false;
  }
  ::listen(socket_fd, 512);

  return false;
}
