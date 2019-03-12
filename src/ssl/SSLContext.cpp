//
// Created by abdess on 1/18/19.
//

#include "SSLContext.h"

using namespace ssl;

bool SSLContext::init(const std::string &cert_file,
                      const std::string &key_file) {
  init();
  ssl_ctx = SSL_CTX_new(SSLv23_method());
  if (ssl_ctx == nullptr) {
    Debug::LogInfo("SSL_CTX_new failed", LOG_ERR);
    return false;
  }
  int r = SSL_CTX_use_certificate_file(ssl_ctx, cert_file.c_str(),
                                       SSL_FILETYPE_PEM);
  if (r <= 0) {
    Debug::logmsg(LOG_ERR, "SSL_CTX_use_certificate_file %s failed",
                  cert_file.c_str());
    return false;
  }
  r = SSL_CTX_use_PrivateKey_file(ssl_ctx, key_file.c_str(), SSL_FILETYPE_PEM);
  if (r <= 0) {
    Debug::logmsg(LOG_ERR, "SSL_CTX_use_PrivateKey_file %s failed",
                  key_file.c_str());
    return false;
  }

  r = SSL_CTX_check_private_key(ssl_ctx);
  if (!r) {
    Debug::logmsg(LOG_ERR, "SSL_CTX_check_private_key failed");
    return false;
  }

  /* Recommended to avoid SSLv2 & SSLv3 */
  SSL_CTX_set_options(ssl_ctx, SSL_OP_ALL | SSL_OP_NO_SSLv2 |
                                   SSL_OP_NO_SSLv3); // set ssl option
  Debug::LogInfo("SSL initialized", LOG_DEBUG);
  return true;
}

bool SSLContext::init(const ListenerConfig &listener_config_) {
  init();
  listener_config = listener_config_;
  if (listener_config.ctx != nullptr) {
    ssl_ctx = listener_config.ctx->ctx;
    return true;
  }
  Debug::LogInfo("SSL initialized", LOG_DEBUG);
  return true;
}

SSLContext::SSLContext() {}

SSLContext::~SSLContext() {
  BIO_free(error_bio);
  SSL_CTX_free(ssl_ctx);
  ERR_free_strings();
}

bool SSLContext::init() {
  error_bio = BIO_new_fd(2, BIO_NOCLOSE);
  ERR_load_crypto_strings();
  ERR_load_SSL_strings();
  SSL_load_error_strings();
  OpenSSL_add_all_algorithms();
  int r = SSL_library_init();
  if (!r) {
    Debug::LogInfo("SSL_library_init failed", LOG_ERR);
    return false;
  }
  return true;
}
