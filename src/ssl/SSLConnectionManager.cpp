//
// Created by abdess on 1/18/19.
//

#include "SSLConnectionManager.h"
#include "../util/common.h"
using namespace ssl;

bool SSLConnectionManager::init(SSLContext &context) {
  // TODO:: not impelemented
  return false;
}

bool SSLConnectionManager::init(const ListenerConfig &listener_config) {
  if (listener_config.ctx != nullptr) {
    if (ssl_context != nullptr)
      delete ssl_context;
    ssl_context = new SSLContext();
    return ssl_context->init(listener_config);
  }
  return false;
}

IO::IO_RESULT SSLConnectionManager::handleDataRead(Connection &ssl_connection) {
  if (!ssl_connection.sslConnected_) {
    return IO::IO_RESULT::SSL_NEED_HANDSHAKE;
  }

  IO::IO_RESULT result = IO::IO_RESULT::ERROR;
  auto rc =
      SSL_read(ssl_connection.ssl_context,
               ssl_connection.buffer + ssl_connection.buffer_size,
               static_cast<int>(MAX_DATA_SIZE - ssl_connection.buffer_size));
  if (rc > 0) {
    ssl_connection.buffer_size += static_cast<size_t>(rc);
    result = IO::IO_RESULT::SUCCESS;
  }
  int ssle = SSL_get_error(ssl_connection.ssl_context, rc);
  if (rc < 0 && ssle != SSL_ERROR_WANT_READ) {
    Debug::logmsg(LOG_DEBUG, "SSL_read return %d error %d errno %d msg %s", rc,
                  ssle, errno, strerror(errno));
    result = IO::IO_RESULT::DONE_TRY_AGAIN; // TODO::  check want read
  }
  if (rc == 0) {
    if (ssle == SSL_ERROR_ZERO_RETURN)
      Debug::logmsg(LOG_NOTICE, "SSL has been shutdown.\n");
    else
      Debug::logmsg(LOG_NOTICE, "Connection has been aborted.\n");
    result = IO::IO_RESULT::FD_CLOSED;
  }
  return result;
}

IO::IO_RESULT SSLConnectionManager::handleWrite(Connection &ssl_connection,
                                                const char *data,
                                                size_t data_size,
                                                size_t &written) {
  if (!ssl_connection.sslConnected_) {
    return IO::IO_RESULT::SSL_NEED_HANDSHAKE;
  }
  IO::IO_RESULT result = IO::IO_RESULT::ERROR;
  auto rc = SSL_write_ex(ssl_connection.ssl_context, data, data_size, &written);
  if (rc > 0) {
    result = IO::IO_RESULT::SUCCESS;
  }
  int ssle = SSL_get_error(ssl_connection.ssl_context, rc);
  if (rc < 0 && ssle != SSL_ERROR_WANT_WRITE) {
    Debug::logmsg(LOG_DEBUG, "SSL_read return %d error %d errno %d msg %s", rc,
                  ssle, errno, strerror(errno));
    result = IO::IO_RESULT::DONE_TRY_AGAIN;
  }
  if (rc == 0) {
    if (ssle == SSL_ERROR_ZERO_RETURN)
      Debug::logmsg(LOG_NOTICE, "SSL has been shutdown.\n");
    else
      Debug::logmsg(LOG_NOTICE, "Connection has been aborted.\n");
    result = IO::IO_RESULT::FD_CLOSED;
  }
  return result;
}

bool SSLConnectionManager::handleHandshake(Connection &ssl_connection) {
  if (ssl_connection.ssl_context == nullptr) {
    ssl_connection.ssl_context = SSL_new(ssl_context->ssl_ctx);
    if (ssl_connection.ssl_context == nullptr)
      Debug::logmsg(LOG_ERR, "SSL_new failed");
    int r = SSL_set_fd(ssl_connection.ssl_context,
                       ssl_connection.getFileDescriptor());
    if (!r)
      Debug::logmsg(LOG_ERR, "SSL_set_fd failed");
    Debug::logmsg(LOG_DEBUG, "SSL_HANDSHAKE: SSL_set_accept_state for fd %d\n",
                  ssl_connection.getFileDescriptor());
    SSL_set_accept_state(ssl_connection.ssl_context);
  }
  int r = SSL_do_handshake(ssl_connection.ssl_context);
  if (r == 1) {
    ssl_connection.sslConnected_ = true;
    Debug::logmsg(LOG_DEBUG, "SSL_HANDSHAKE: ssl connected fd %d\n",
                  ssl_connection.getFileDescriptor());
    ssl_connection.enableReadEvent();
    return true;
  }
  int err = SSL_get_error(ssl_connection.ssl_context, r);
  if (err == SSL_ERROR_WANT_WRITE) {
    Debug::logmsg(LOG_DEBUG, "SSL_HANDSHAKE: return want write set events %d\n",
                  ssl_connection.getFileDescriptor());
    ssl_connection.enableWriteEvent();

  } else if (err == SSL_ERROR_WANT_READ) {
    Debug::logmsg(LOG_DEBUG, "SSL_HANDSHAKE: Want read, fd %d\n",
                  ssl_connection.getFileDescriptor());
    ssl_connection.enableReadEvent();

  } else {
    Debug::logmsg(LOG_ERR,
                  "SSL_do_handshake return %d error %d errno %d msg %s\n", r,
                  err, errno, strerror(errno));
    ERR_print_errors(ssl_context->error_bio);
    return false;
  }
  return true;
}
SSLConnectionManager::~SSLConnectionManager() {
  if (ssl_context != nullptr) {
    delete ssl_context;
  }
}

SSLConnectionManager::SSLConnectionManager() : ssl_context(nullptr) {}