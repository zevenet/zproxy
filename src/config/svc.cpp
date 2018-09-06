#include "svc.h"
#include "../debug/Debug.h"
RSA *RSA_tmp_callback(/* not used */ SSL *ssl, /* not used */ int is_export,
                                     int keylength) {
  RSA *res;
  int ret_val;

  if (ret_val = pthread_mutex_lock(&RSA_mut))
    Debug::logmsg(LOG_WARNING, "RSA_tmp_callback() lock: %s",
                  strerror(ret_val));
  res = (keylength <= 512) ? RSA512_keys[rand() % N_RSA_KEYS]
                           : RSA1024_keys[rand() % N_RSA_KEYS];
  if (ret_val = pthread_mutex_unlock(&RSA_mut))
    Debug::logmsg(LOG_WARNING, "RSA_tmp_callback() unlock: %s",
                  strerror(ret_val));
  return res;
}

int DH_set0_pqg(DH *dh, BIGNUM *p, BIGNUM *q, BIGNUM *g) {
  /* If the fields p and g in d are NULL, the corresponding input
   * parameters MUST be non-NULL.  q may remain NULL.
   */
  if ((dh->p == NULL && p == NULL) || (dh->g == NULL && g == NULL)) return 0;

  if (p != NULL) {
    BN_free(dh->p);
    dh->p = p;
  }
  if (q != NULL) {
    BN_free(dh->q);
    dh->q = q;
  }
  if (g != NULL) {
    BN_free(dh->g);
    dh->g = g;
  }

  if (q != NULL) {
    dh->length = BN_num_bits(q);
  }

  return 1;
}

void SSLINFO_callback(const SSL *ssl, int where, int rc) {
  RENEG_STATE *reneg_state;

  /* Get our thr_arg where we're tracking this connection info */
  if ((reneg_state = (RENEG_STATE *) SSL_get_app_data(ssl)) == NULL) return;

  /* If we're rejecting renegotiations, move to ABORT if Client Hello is being
   * read. */
  if ((where & SSL_CB_ACCEPT_LOOP) && *reneg_state == RENEG_REJECT) {
    int state;

    state = SSL_get_state(ssl);
    if (state == SSL3_ST_SR_CLNT_HELLO_A || state == SSL23_ST_SR_CLNT_HELLO_A) {
      *reneg_state = RENEG_ABORT;
      Debug::logmsg(LOG_WARNING, "rejecting client initiated renegotiation");
    }
  } else if (where & SSL_CB_HANDSHAKE_DONE && *reneg_state == RENEG_INIT) {
    // Reject any followup renegotiations
    *reneg_state = RENEG_REJECT;
  }
}

int get_host(char *const name, addrinfo *res, int ai_family) {
  struct addrinfo *chain, *ap;
  struct addrinfo hints;
  int ret_val;
  memset(&hints, 0, sizeof(hints));
  hints.ai_family = ai_family;
  hints.ai_socktype = SOCK_STREAM;
  hints.ai_flags = AI_CANONNAME;
  if ((ret_val = getaddrinfo(name, NULL, &hints, &chain)) == 0) {
    for (ap = chain; ap != NULL; ap = ap->ai_next)
      if (ap->ai_socktype == SOCK_STREAM) break;

    if (ap == NULL) {
      freeaddrinfo(chain);
      return EAI_NONAME;
    }
    *res = *ap;
    if ((res->ai_addr = (struct sockaddr *) malloc(ap->ai_addrlen)) == NULL) {
      freeaddrinfo(chain);
      return EAI_MEMORY;
    }
    memcpy(res->ai_addr, ap->ai_addr, ap->ai_addrlen);
    freeaddrinfo(chain);
  }
  return ret_val;
}

DH *load_dh_params(char *file) {
  DH *dh = NULL;
  BIO *bio;

  if ((bio = BIO_new_file(file, "r")) == NULL) {
    Debug::logmsg(LOG_WARNING, "Unable to open DH file - %s", file);
    return NULL;
  }

  dh = PEM_read_bio_DHparams(bio, NULL, NULL, NULL);
  BIO_free(bio);
  return dh;
}

DH *DH_tmp_callback(SSL *s, int is_export, int keylength) {
  return keylength == 512 ? DH512_params : DH2048_params;
}
