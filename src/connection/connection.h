//
// Created by abdess on 4/5/18.
//
#pragma once

#include "../event/descriptor.h"
#include "../http/HttpRequest.h"
#include "../util/string_buffer.h"
#include "../util/utils.h"
#include <atomic>
#include <fcntl.h>
#include <netdb.h>
#include <openssl/ssl.h>
#include <sys/uio.h>
#include <unistd.h>
#define MAX_DATA_SIZE 65000

#define ENABLE_ZERO_COPY 1

#if ENABLE_ZERO_COPY

#define BUFSZ MAX_DATA_SIZE

struct SplicePipe {
  int pipe[2];
  int bytes;
  SplicePipe() {
    if (pipe2(pipe, O_NONBLOCK) < 0) {
      perror("pipe");
    }
  }
  ~SplicePipe() {
    close(pipe[0]);
    close(pipe[1]);
  }
};

#endif

class Connection : public Descriptor {
  long last_read_;
  long last_write_;

protected:
  bool is_connected;
  IO::IO_RESULT writeTo(int target_fd, http_parser::HttpData &http_data);

public:
#if ENABLE_ZERO_COPY
  SplicePipe splice_pipe;
#endif
  std::string address_str;
  addrinfo *address;
  // StringBuffer string_buffer;
  char buffer[MAX_DATA_SIZE];
  size_t buffer_size;
  std::string getPeerAddress();

#if ENABLE_ZERO_COPY
  IO::IO_RESULT zeroRead();
  IO::IO_RESULT zeroWrite(int dst_fd, http_parser::HttpData &http_data);
#endif

  IO::IO_RESULT write(const char *data, size_t size);
  IO::IO_RESULT writeTo(int fd);
  IO::IO_RESULT writeContentTo(const Connection &target_connection,
                               http_parser::HttpData &http_data);
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
  IO::IO_OP doConnect(addrinfo &address, int timeout, bool async = true);
  IO::IO_OP doConnect(const std::string &af_unix_socket_path, int timeout);
  bool isConnected();
  // SSL stuff
public:
  SSL *ssl{nullptr};
  // socket bio
  BIO *sbio{nullptr};
  // buffer bio
  BIO *io{nullptr};
  // ssl bio
  BIO *ssl_bio{nullptr};

  std::atomic<bool> ssl_connected;
};
