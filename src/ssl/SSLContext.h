//
// Created by abdess on 1/18/19.
//

#pragma once

#include "../config/config.h"
#include "../debug/Debug.h"
#include <openssl/bio.h>
#include <openssl/err.h>
#include <openssl/ssl.h>
namespace ssl {

  struct SSLData {
    SSL_CTX *ctx;
    char *server_name;
    unsigned char **subjectAltNames;
    unsigned int subjectAltNameCount;
    struct SSLData *next;
  };

class SSLContext {
public:
  BIO *error_bio{nullptr};
  SSL_CTX *ssl_ctx{nullptr};
  ListenerConfig listener_config;
  SSLData ctx;
  SSLContext();
  virtual ~SSLContext();
  bool init();
  bool init(const std::string &cert_file, const std::string &key_file);
  bool init(const BackendConfig &backend_config_);
  bool init(const ListenerConfig &listener_config_);
  bool loadOpensslConfig(const std::string &config_file_path, SSL_CTX *ctx);
  static int  SNIServerName(SSL *ssl, int dummy, SSLData *ctx);
};
} // namespace ssl
