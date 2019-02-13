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
  if (ssl_connection.ssl != nullptr) {
    SSL_shutdown(ssl_connection.ssl);
    SSL_free(ssl_connection.ssl);
  }
  ssl_connection.ssl = SSL_new(ssl_context->ssl_ctx);
  if (ssl_connection.ssl == nullptr) {
    Debug::logmsg(LOG_ERR, "SSL_new failed");
    return false;
  }
  int r = SSL_set_fd(ssl_connection.ssl,
                     ssl_connection.getFileDescriptor());
  if (!r) {
    Debug::logmsg(LOG_ERR, "SSL_set_fd failed");
    return false;
  }

  Debug::logmsg(LOG_DEBUG, "SSL_HANDSHAKE: SSL_set_accept_state for fd %d",
                ssl_connection.getFileDescriptor());
  // let the SSL object know it should act as server
  !client_mode ? SSL_set_accept_state(ssl_connection.ssl)
               : SSL_set_connect_state(ssl_connection.ssl);
  return true;
}

bool SSLConnectionManager::initSslConnection_BIO(Connection &ssl_connection, bool client_mode)
{
  if (ssl_connection.ssl != nullptr) {
    SSL_shutdown(ssl_connection.ssl);
    SSL_free(ssl_connection.ssl);
  }
  ssl_connection.ssl=SSL_new(ssl_context->ssl_ctx);
  if (ssl_connection.ssl == nullptr) {
    Debug::logmsg(LOG_ERR, "SSL_new failed");
    return false;
  }
  ssl_connection.sbio=BIO_new_socket(ssl_connection.getFileDescriptor(),BIO_CLOSE);
  SSL_set_bio(ssl_connection.ssl,ssl_connection.sbio,ssl_connection.sbio);
  ssl_connection.io=BIO_new(BIO_f_buffer());
  ssl_connection.ssl_bio=BIO_new(BIO_f_ssl());
  BIO_set_ssl(ssl_connection.ssl_bio,ssl_connection.ssl,BIO_CLOSE);
  BIO_push(ssl_connection.io,ssl_connection.ssl_bio);
  Debug::logmsg(LOG_DEBUG, "SSL_HANDSHAKE: SSL_set_accept_state for fd %d",
                  ssl_connection.getFileDescriptor());
    // let the SSL object know it should act as server
  !client_mode ? SSL_set_accept_state(ssl_connection.ssl)
                 : SSL_set_connect_state(ssl_connection.ssl);
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
      BIO_read(ssl_connection.io,
               ssl_connection.buffer + ssl_connection.buffer_size,
               static_cast<int>(MAX_DATA_SIZE - ssl_connection.buffer_size));
  if (rc > 0) {
    ssl_connection.buffer_size += static_cast<size_t>(rc);
    result = IO::IO_RESULT::SUCCESS;
  }
  int ssle = SSL_get_error(ssl_connection.ssl, rc);
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
  int rc = -1;
  int sent = 0;
  //FIXME: Buggy, used just for test
   Debug::logmsg(LOG_DEBUG,"> handleWrite");
  do{
      rc = BIO_write(ssl_connection.io, data + sent, static_cast<int>(data_size - sent)); //, &written);
      Debug::logmsg(LOG_DEBUG,"BIO_write return code %d sent %d",rc, sent);
      if(rc > 0) sent += rc;
    }
  while(rc > 0 && rc < (data_size - sent));

  if(BIO_should_retry(ssl_connection.io)){
      return IO::IO_RESULT::DONE_TRY_AGAIN;
    }
  BIO_flush(ssl_connection.io);
  if (rc > 0) {
    written = rc;
    result = IO::IO_RESULT::SUCCESS;
  }
  int ssle = SSL_get_error(ssl_connection.ssl, rc);
  if (rc < 0 && ssle != SSL_ERROR_WANT_WRITE) {
      //Renegotiation is not possible in a TLSv1.3 connection
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
  if (ssl_connection.ssl == nullptr) {
    if (!initSslConnection_BIO(ssl_connection)) {
      return false;
    }
  }
  int r = SSL_do_handshake(ssl_connection.ssl);
  if (r == 1) {
    ssl_connection.ssl_connected = true;
    Debug::logmsg(LOG_DEBUG, "SSL_HANDSHAKE: ssl connected fd %d",
                  ssl_connection.getFileDescriptor());
    ssl_connection.enableReadEvent();
    return true;
  }
  int err = SSL_get_error(ssl_connection.ssl, r);
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

IO::IO_RESULT
SSLConnectionManager::getSslErrorResult(SSL *ssl_connection_context, int &rc) {
  rc = SSL_get_error(ssl_connection_context, rc);
  switch (rc) {
  case SSL_ERROR_ZERO_RETURN: /* Received a close_notify alert. */
  case SSL_ERROR_WANT_READ:   /* We need more data to finish the frame. */
    return IO::IO_RESULT::DONE_TRY_AGAIN;
  case SSL_ERROR_WANT_WRITE:{
      //Warning - Renegotiation is not possible in a TLSv1.3 connection!!!!
      // handle renegotiation, after a want write ssl
                             // error,
    Debug::logmsg(LOG_NOTICE,
                  "Renegotiation of SSL connection requested by peer");
    return IO::IO_RESULT::SSL_WANT_RENEGOTIATION;
  }case SSL_ERROR_SSL:
    Debug::logmsg(LOG_ERR, "corrupted data detected while reading");
    logSslErrorStack();
  default:
    Debug::logmsg(LOG_ERR, "SSL_read failed with error %s.",
                  getErrorString(rc));
    return IO::IO_RESULT::ERROR;
  }
  //  int ssle = SSL_get_error(ssl_connection.ssl_context, rc);
 //  if (rc < 0 && ssle != SSL_ERROR_WANT_WRITE) {
  //    Debug::logmsg(LOG_NOTICE,
  //                  "Renegotiation of SSL connection requested by peer");
  //    return IO::IO_RESULT::SSL_WANT_RENEGOTIATION;
  //  }
  //  if (rc == 0) {
  //    if (ssle == SSL_ERROR_ZERO_RETURN)
  //      Debug::logmsg(LOG_NOTICE, "SSL connection has been shutdown.");
  //    else
  //      Debug::logmsg(LOG_NOTICE, "Connection has been aborted.");
  //    result = IO::IO_RESULT::FD_CLOSED;
  //  }
}
