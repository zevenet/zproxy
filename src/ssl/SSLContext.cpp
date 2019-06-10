//
// Created by abdess on 1/18/19.
//

#include "SSLContext.h"
#include "ssl_session.h"

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
#if SSL_DISABLE_SESSION_CACHE
  // Attempt to disable session and ticket caching..
  //  SSL_CTX_set_options(ssl_ctx,
  //  SSL_OP_NO_SESSION_RESUMPTION_ON_RENEGOTIATION)
  //  SSL_CTX_set_num_tickets(ssl_ctx, 0);
  SSL_CTX_set_options(ssl_ctx, SSL_OP_NO_TICKET);
  SSL_CTX_set_session_cache_mode(ssl_ctx, SSL_SESS_CACHE_OFF);
#endif
  SSL_CTX_set_options(ssl_ctx, SSL_OP_NO_COMPRESSION );
  SSL_CTX_set_mode(ssl_ctx,SSL_MODE_RELEASE_BUFFERS );

  Debug::LogInfo("SSL initialized", LOG_DEBUG);
  return true;
}

bool SSLContext::init(const BackendConfig &backend_config_) {
  init();
  if (backend_config_.ctx != nullptr) {
    ssl_ctx = backend_config_.ctx;
    return true;
  }
  Debug::LogInfo("SSL initialized", LOG_DEBUG);
  return true;
}


bool SSLContext::init(const ListenerConfig &listener_config_) {
  init();
  listener_config = listener_config_;
  if (listener_config.ctx != nullptr) {

#ifdef SSL_CTRL_SET_TLSEXT_SERVERNAME_CB
  if (listener_config_.ctx->next)
    if (!SSL_CTX_set_tlsext_servername_callback(listener_config_.ctx->ctx,
                                                SNIServerName) ||
            !SSL_CTX_set_tlsext_servername_arg(listener_config_.ctx->ctx,listener_config_.ctx))
      Debug::logmsg(LOG_ERR, "ListenHTTPS: can't set SNI callback");
#endif

    ssl_ctx = listener_config.ctx->ctx;

#ifdef ENABLE_SSL_SESSION_CACHING
    SslSessionManager::attachCallbacks(ssl_ctx);
#endif

#if SSL_DISABLE_SESSION_CACHE
    // Attempt to disable session and ticket caching..
//      SSL_CTX_set_options(ssl_ctx,
//                        SSL_OP_NO_SESSION_RESUMPTION_ON_RENEGOTIATION);
//    SSL_CTX_set_num_tickets(ssl_ctx, 0);
    SSL_CTX_set_options(ssl_ctx, SSL_OP_NO_TICKET);
    SSL_CTX_set_session_cache_mode(ssl_ctx, SSL_SESS_CACHE_OFF);
#endif
    SSL_CTX_set_options(ssl_ctx, SSL_OP_NO_COMPRESSION );
    SSL_CTX_set_mode(ssl_ctx,SSL_MODE_RELEASE_BUFFERS );
    return true;
  }
#if HAVE_OPENSSL_ENGINE_H
  if(listener_config.engine_id != nullptr)
    initEngine(listener_config.engine_id);
#endif
  if (!listener_config.ssl_config_file.empty()) {
          if (!loadOpensslConfig(listener_config.ssl_config_file, listener_config.ctx->ctx))
              return false;
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

/* This function loads the OpenSSL configuration file.
 * Documentation related with the config file syntax:
 * https://www.openssl.org/docs/manmaster/man5/config.html*/
bool SSLContext::loadOpensslConfig(const std::string &config_file_path,
                                   const std::string &config_file_section,
                                   SSL_CTX *ctx) {
  /* We use FILE instead of c++ ifstream because it is not
   * compatible with the NCONF functions. */
  FILE *fp;
  CONF *cnf = NULL;
  long eline;

  fp = fopen(config_file_path.c_str(), "r");
  if (fp == NULL) {
    return false;
  } else {
      cnf = NCONF_new(NULL);
      if (NCONF_load_fp(cnf, fp, &eline) == 0) {
         Debug::logmsg(LOG_ERR, "Error on line %ld of configuration file\n", eline);
         return false;
          /* Other malformed configuration file behaviour */
      } else if (CONF_modules_load(cnf, "zhttp", CONF_MFLAGS_NO_DSO) <= 0) {
        Debug::logmsg(LOG_ERR, "Error configuring the application");
        ERR_print_errors_fp(stderr);
        return false;
          /* Other configuration error behaviour */

      }

      if (SSL_CTX_config(ctx, config_file_section.c_str()) == 0) {
          Debug::logmsg(LOG_ERR, "Error configuring SSL_CTX");
          ERR_print_errors_fp(stderr);
          return false;
      }
      fclose(fp);
      NCONF_free(cnf);
  }
}

int SSLContext::SNIServerName(SSL *ssl, int dummy, SSLData *ctx) {
  const char *server_name;
  SSLData *pc;

  if ((server_name = SSL_get_servername(ssl, TLSEXT_NAMETYPE_host_name)) ==
      NULL)
    return SSL_TLSEXT_ERR_NOACK;

  /* logmsg(LOG_DEBUG, "Received SSL SNI Header for servername %s",
   * servername); */

  SSL_set_SSL_CTX(ssl, NULL);
  for (pc = ctx; pc; pc = pc->next) {
    if (fnmatch(pc->server_name, server_name, 0) == 0) {
      /* logmsg(LOG_DEBUG, "Found cert for %s", servername); */
      SSL_set_SSL_CTX(ssl, pc->ctx);
      return SSL_TLSEXT_ERR_OK;
    } else if (pc->subjectAltNameCount > 0 && pc->subjectAltNames != NULL) {
      int i;

      for (i = 0; i < pc->subjectAltNameCount; i++) {
        if (fnmatch((char*)pc->subjectAltNames[i], server_name, 0) == 0) {
          SSL_set_SSL_CTX(ssl, pc->ctx);
          return SSL_TLSEXT_ERR_OK;
        }
      }
    }
  }

  /* logmsg(LOG_DEBUG, "No match for %s, default used", server_name); */
  SSL_set_SSL_CTX(ssl, ctx->ctx);
  return SSL_TLSEXT_ERR_OK;
}

bool SSLContext::initEngine(char *engine_id) {

  if (engine_id == nullptr)
    return false;

#if HAVE_OPENSSL_ENGINE_H
  ENGINE *e;
#endif

  if (!(e = ENGINE_by_id(engine_id))) {
    Debug::logmsg(LOG_ERR, "could not find engine");
    return false;
  } else if (!ENGINE_init(e)) {
    Debug::logmsg(LOG_ERR, "could not init engine");
    return false;
  } else if (!ENGINE_set_default(e, ENGINE_METHOD_ALL)) {
    Debug::logmsg(LOG_ERR, "could not set all defaults");
    return false;
  }

  ENGINE_finish(e);
  ENGINE_free(e);
  return true;
}
