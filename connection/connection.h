//
// Created by abdess on 4/5/18.
//

#ifndef NEW_ZHTTP_CONNECTION_H
#define NEW_ZHTTP_CONNECTION_H

#include <netdb.h>
#include "../string_buffer.h"
#include <unistd.h>

#define MAX_DATA_SIZE  65000

class Connection {
 protected:
  bool is_connected;
  StringBuffer string_buffer;
 public:
  int socket_fd;
  addrinfo address;

  int getFileDescriptor() const;
  void setFileDescriptor(int fd);

  int write(const char *data, size_t buffer_size);
  int writeTo(int fd);
  int read();
  void closeConnection();
  Connection();
  virtual ~Connection();

  bool listen(std::string &address_str, int port);
  bool listen(addrinfo &address);

  int doAccept();
  bool doConnect(addrinfo &address, int timeout);

};

#endif //NEW_ZHTTP_CONNECTION_H
