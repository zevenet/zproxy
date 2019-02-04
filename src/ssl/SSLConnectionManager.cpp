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

bool SSLConnectionManager::initSslConnection(Connection &ssl_connection,
                                             bool client_mode) {
  if (ssl_connection.ssl_context != nullptr) {
    SSL_shutdown(ssl_connection.ssl_context);
    SSL_free(ssl_connection.ssl_context);
  }
  ssl_connection.ssl_context = SSL_new(ssl_context->ssl_ctx);
  if (ssl_connection.ssl_context == nullptr) {
    Debug::logmsg(LOG_ERR, "SSL_new failed");
    return false;
  }
  int r = SSL_set_fd(ssl_connection.ssl_context,
                     ssl_connection.getFileDescriptor());
  if (!r) {
    Debug::logmsg(LOG_ERR, "SSL_set_fd failed");
    return false;
  }

  Debug::logmsg(LOG_DEBUG, "SSL_HANDSHAKE: SSL_set_accept_state for fd %d",
                ssl_connection.getFileDescriptor());
  // let the SSL object know it should act as server
  !client_mode ? SSL_set_accept_state(ssl_connection.ssl_context)
               : SSL_set_connect_state(ssl_connection.ssl_context);
  return true;
}

void SSLConnectionManager::setSslInfoCallback(Connection &ssl_connection,
                                              SslInfoCallback callback) {
  // TODO::SSL implement
  // SSL_set_info_callback(ssl_connection.ssl_context, callback);
}

IO::IO_RESULT SSLConnectionManager::handleDataRead(Connection &ssl_connection) {
  if (!ssl_connection.ssl_connected) {
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
      Debug::logmsg(LOG_NOTICE, "SSL has been shutdown.");
    else
      Debug::logmsg(LOG_NOTICE, "Connection has been aborted.");
    result = IO::IO_RESULT::FD_CLOSED;
  }
  return result;
}

IO::IO_RESULT SSLConnectionManager::handleWrite(Connection &ssl_connection,
                                                const char *data,
                                                size_t data_size,
                                                size_t &written) {
  if (!ssl_connection.ssl_connected) {
    return IO::IO_RESULT::SSL_NEED_HANDSHAKE;
  }
  IO::IO_RESULT result = IO::IO_RESULT::ERROR;
  auto rc =
      SSL_write(ssl_connection.ssl_context, data, data_size); //, &written);
  if (rc > 0) {
    written = rc;
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
      Debug::logmsg(LOG_NOTICE, "SSL connection has been shutdown.");
    else
      Debug::logmsg(LOG_NOTICE, "Connection has been aborted.");
    result = IO::IO_RESULT::FD_CLOSED;
  }
  return result;
}

bool SSLConnectionManager::handleHandshake(Connection &ssl_connection) {
  if (ssl_connection.ssl_context == nullptr) {
    if (!initSslConnection(ssl_connection)) {
      return false;
    }
  }
  int r = SSL_do_handshake(ssl_connection.ssl_context);
  if (r == 1) {
    ssl_connection.ssl_connected = true;
    Debug::logmsg(LOG_DEBUG, "SSL_HANDSHAKE: ssl connected fd %d",
                  ssl_connection.getFileDescriptor());
    ssl_connection.enableReadEvent();
    return true;
  }
  int err = SSL_get_error(ssl_connection.ssl_context, r);
  if (err == SSL_ERROR_WANT_WRITE) {
    Debug::logmsg(LOG_DEBUG, "SSL_HANDSHAKE: return want write set events %d",
                  ssl_connection.getFileDescriptor());
    ssl_connection.enableWriteEvent();

  } else if (err == SSL_ERROR_WANT_READ) {
    Debug::logmsg(LOG_DEBUG, "SSL_HANDSHAKE: Want read, fd %d",
                  ssl_connection.getFileDescriptor());
    ssl_connection.enableReadEvent();

  } else {
    Debug::logmsg(LOG_ERR,
                  "SSL_do_handshake return %d error %d errno %d msg %s", r, err,
                  errno, strerror(errno));
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
