#pragma once

#include "../debug/Debug.h"
#include <openssl/err.h>
#include <openssl/ssl.h>

namespace ssl {
typedef void (*SslInfoCallback)();

inline static void logSslErrorStack(void) {
  unsigned long err;
  while ((err = ERR_get_error()) != 0) {
    char details[256];
    ERR_error_string_n(static_cast<uint32_t>(err), details, sizeof(details));
    Debug::logmsg(LOG_ERR, "%s", details);
  }
}
static const char *getErrorString(int error) {
  switch (error) {
  case SSL_ERROR_NONE:
    return "SSL_ERROR_NONE";
  case SSL_ERROR_ZERO_RETURN:
    return "SSL_ERROR_ZERO_RETURN";
  case SSL_ERROR_WANT_READ:
    return "SSL_ERROR_WANT_READ";
  case SSL_ERROR_WANT_WRITE:
    return "SSL_ERROR_WANT_WRITE";
  case SSL_ERROR_WANT_CONNECT:
    return "SSL_ERROR_WANT_CONNECT";
  case SSL_ERROR_WANT_ACCEPT:
    return "SSL_ERROR_WANT_ACCEPT";
  case SSL_ERROR_WANT_X509_LOOKUP:
    return "SSL_ERROR_WANT_X509_LOOKUP";
  case SSL_ERROR_SYSCALL:
    return "SSL_ERROR_SYSCALL";
  case SSL_ERROR_SSL:
    return "SSL_ERROR_SSL";
  default:
    return "Unknown error";
  }
}
} // namespace ssl
