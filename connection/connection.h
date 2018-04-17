//
// Created by abdess on 4/5/18.
//

#ifndef NEW_ZHTTP_CONNECTION_H
#define NEW_ZHTTP_CONNECTION_H

#include <netdb.h>
#include "../util/string_buffer.h"
#include "../util/utils.h"
#include <unistd.h>

#define MAX_DATA_SIZE  65000

class Connection {
 protected:
  bool is_connected;
 public:
  int socket_fd;
  addrinfo *address;
  // StringBuffer string_buffer;
  char buffer[MAX_DATA_SIZE * 2];
  size_t buffer_size = 0;

  int getFileDescriptor() const;
  void setFileDescriptor(int fd);

  IO::IO_RESULT write(const char *data, size_t buffer_size);
  IO::IO_RESULT writeTo(int fd);
  IO::IO_RESULT read();

  void closeConnection();
  Connection();
  virtual ~Connection();

  bool listen(std::string &address_str, int port);
  bool listen(addrinfo &address);

  int doAccept();
  bool doConnect(addrinfo &address, int timeout);

};

#endif //NEW_ZHTTP_CONNECTION_H
