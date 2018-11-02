//
// Created by abdess on 4/5/18.
//
#pragma once

#include <netdb.h>
#include <sys/uio.h>
#include <unistd.h>
#include "../http/HttpRequest.h"
#include "../util/string_buffer.h"
#include "../util/utils.h"

#define MAX_DATA_SIZE 65000
struct ConnectionStadistic_t {
  long last_read = 0;
  double avr_read_time = 0;
  double max_read_time = 0;
  double min_read_time = 0;
  void update() {
    if (last_read != 0) {
      auto elapsed = (clock() - last_read);
      if (avr_read_time != 0) {
        if (elapsed < min_read_time) min_read_time = elapsed;
        if (elapsed > max_read_time) max_read_time = elapsed;
        avr_read_time = (avr_read_time + elapsed) / 2;
      }
    }
    last_read = clock();
    avr_read_time = 0;
    min_read_time = 0;
    max_read_time = 0;
  }
};
class Connection {
  long last_read_;
  long last_write_;

 protected:
  int socket_fd;
  bool is_connected;

 public:
  std::string address_str;
  addrinfo* address;
  // StringBuffer string_buffer;
  char buffer[MAX_DATA_SIZE];
  size_t buffer_size;
  std::string getPeerAddress();
  int getFileDescriptor() const;
  void setFileDescriptor(int fd);

  IO::IO_RESULT write(const char* data, size_t size);
  IO::IO_RESULT writeTo(int fd);
  IO::IO_RESULT writeRequest(HttpRequest& request, ssize_t& out_total_written);

  IO::IO_RESULT read();

  void closeConnection();
  Connection();
  virtual ~Connection();

  bool listen(std::string address_str, int port);
  bool listen(addrinfo& address);
  bool listen(std::string af_unix_name);

  int doAccept();
  IO::IO_OP doConnect(addrinfo& address, int timeout);
  bool isConnected();
};
