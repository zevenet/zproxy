//
// Created by abdess on 4/5/18.
//
#pragma once

#include "../http/HttpRequest.h"
#include "../util/string_buffer.h"
#include "../util/utils.h"
#include <netdb.h>
#include <sys/uio.h>
#include <unistd.h>

#define MAX_DATA_SIZE 65000

class Connection {
  long last_read_;
  long last_write_;

protected:
  int socket_fd;
  bool is_connected;

public:
  std::string address_str;
  addrinfo *address;
  // StringBuffer string_buffer;
  char buffer[MAX_DATA_SIZE];
  size_t buffer_size;
  std::string getPeerAddress();
  int getFileDescriptor() const;
  void setFileDescriptor(int fd);

  IO::IO_RESULT write(const char *data, size_t size);
  IO::IO_RESULT writeTo(int fd);
  IO::IO_RESULT writeTo(int target_fd, http_parser::HttpData &http_data);
  IO::IO_RESULT writeTo(const Connection &target_connection,
                        http_parser::HttpData &http_data);

  IO::IO_RESULT read();

  void closeConnection();
  Connection();
  virtual ~Connection();

  bool listen(std::string address_str_, int port);
  bool listen(addrinfo &address);
  bool listen(std::string af_unix_name);

  int doAccept();
  IO::IO_OP doConnect(addrinfo &address, int timeout);
  bool isConnected();
};
