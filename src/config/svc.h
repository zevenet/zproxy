#ifndef SVC_H
#define SVC_H
#include <malloc.h>
#include <netdb.h>
#include <openssl/ssl.h>
#include "../debug/debug.h"
#include "pound_struct.h"
#include "string.h"

/*
 * RSA ephemeral keys: how many and how often
 */
#define N_RSA_KEYS 11
#ifndef T_RSA_KEYS
#define T_RSA_KEYS 7200
#endif

static pthread_mutex_t RSA_mut;       /* mutex for RSA keygen */
static RSA *RSA512_keys[N_RSA_KEYS];  /* ephemeral RSA keys */
static RSA *RSA1024_keys[N_RSA_KEYS]; /* ephemeral RSA keys */

/*
 * return a pre-generated RSA key
 */
RSA *RSA_tmp_callback(/* not used */ SSL *ssl,
    /* not used */ int is_export, int keylength);

#if OPENSSL_VERSION_NUMBER < 0x10100000
static inline int DH_set0_pqg(DH *dh, BIGNUM *p, BIGNUM *q, BIGNUM *g);
#endif

//#include "dh512.h"

#if DH_LEN == 1024
#include "dh1024.h"
static DH *DH512_params, *DH1024_params;

DH *DH_tmp_callback(/* not used */ SSL *s, /* not used */ int is_export,
                    int keylength) {
  return keylength == 512 ? DH512_params : DH1024_params;
}
#else
//#include "dh2048.h"
static DH *DH512_params, *DH2048_params;

DH *DH_tmp_callback(/* not used */ SSL *s,
    /* not used */ int is_export, int keylength);
#endif

DH *load_dh_params(char *file);

/*
 * Search for a host name, return the addrinfo for it
 */
int get_host(char *const name, struct addrinfo *res, int ai_family);

void SSLINFO_callback(const SSL *ssl, int where, int rc);
#endif
