#pragma once

#include <openssl/ssl.h>
#include <mutex>
#include <cstring>
#include <list>


#define MAX_ENCODING_SIZE 4096
#define MAX_ID_SIZE 512

typedef struct {
    unsigned int sess_id_size;
    unsigned char sess_id[MAX_ID_SIZE];
    int encoding_length;
    unsigned char encoding_data[MAX_ENCODING_SIZE];
} SslSessionData;


class SslSessionManager {
public:
  std::list<SslSessionData*> sessions;
  static SslSessionManager* getInstance();
    int addSession(SSL *ssl, SSL_SESSION *session);
    SSL_SESSION * getSession(SSL *ssl, unsigned char *id, int id_length, int *do_copy);
    void deleteSession(SSL_CTX *sctx, SSL_SESSION *session);
    void attachCallbacks(SSL_CTX * sctx);
private:
    static SslSessionManager *ssl_session_manager;
    std::mutex data_mtx;

    SslSessionManager();
    virtual  ~SslSessionManager();
    void removeSessionId(const unsigned char* id, int idLength);

};



