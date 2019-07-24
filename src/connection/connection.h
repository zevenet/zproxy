//
// Created by abdess on 4/5/18.
//
#pragma once

#include "../event/descriptor.h"
#include "../http/HttpRequest.h"
#include "../experimental/string_buffer.h"
#include "../util/utils.h"
#include <atomic>
#include <fcntl.h>
#include <netdb.h>
#include "../ssl/ssl_common.h"
#include <sys/uio.h>
#include <unistd.h>

#define MAX_DATA_SIZE (67000*2)
#define FAKE_ZERO_COPY 0

#if ENABLE_ZERO_COPY

#define BUFSZ MAX_DATA_SIZE

struct SplicePipe {
  int pipe[2];
  int bytes{0};
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
#if FAKE_ZERO_COPY
  char buffer_aux[MAX_DATA_SIZE];
#endif
#endif
    std::string address_str;
    addrinfo *address;

  // StringBuffer string_buffer;
  char buffer[MAX_DATA_SIZE];
  size_t buffer_size{0};
  size_t buffer_offset{0};
  std::string getPeerAddress();

#if ENABLE_ZERO_COPY
  IO::IO_RESULT zeroRead();
  IO::IO_RESULT zeroWrite(int dst_fd, http_parser::HttpData &http_data);
#endif

  IO::IO_RESULT write(const char *data, size_t size);
  IO::IO_RESULT writeTo(int fd, size_t & sent);
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
  ssl::SSL_STATUS ssl_conn_status{ssl::SSL_STATUS::NONE};
  SSL *ssl{nullptr};
  // socket bio
  BIO *sbio{nullptr};
  // buffer bio
  BIO *io{nullptr};
  // ssl bio
  BIO *ssl_bio{nullptr};

  std::atomic<bool> ssl_connected;
};
