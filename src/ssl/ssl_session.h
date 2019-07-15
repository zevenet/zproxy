#pragma once

#include <openssl/ssl.h>
#include <mutex>
#include <cstring>
#include <list>


#define MAX_ENCODING_SIZE 4096
#define MAX_ID_SIZE 512
namespace ssl {
typedef struct {
    unsigned int sess_id_size;
    unsigned char sess_id[MAX_ID_SIZE];
    size_t encoding_length;
    unsigned char encoding_data[MAX_ENCODING_SIZE];
} SslSessionData;


class SslSessionManager {
public:
    std::list<SslSessionData *> sessions;
    static std::mutex singleton_mtx;
    static SslSessionManager *getInstance();
    int addSession(SSL *ssl, SSL_SESSION *session);
    SSL_SESSION *getSession(SSL *ssl,const unsigned char *id, int id_length,
                            int *do_copy);
    void deleteSession(SSL_CTX *sctx, SSL_SESSION *session);
    static void attachCallbacks(SSL_CTX *sctx);
    static int addSessionCb(SSL *ssl, SSL_SESSION *session);
    static SSL_SESSION *getSessionCb(SSL *ssl,const unsigned char *id, int id_length,
                                     int *do_copy);
    static void deleteSessionCb(SSL_CTX *sctx, SSL_SESSION *session);

private:
    static SslSessionManager *ssl_session_manager;
    std::mutex data_mtx;

    SslSessionManager();
    virtual  ~SslSessionManager();
    void removeSessionId(const unsigned char* id, int idLength);
};
}

