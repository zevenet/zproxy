/*
 *    Zevenet zproxy Load Balancer Software License
 *    This file is part of the Zevenet zproxy Load Balancer software package.
 *
 *    Copyright (C) 2019-today ZEVENET SL, Sevilla (Spain)
 *
 *    This program is free software: you can redistribute it and/or modify
 *    it under the terms of the GNU Affero General Public License as
 *    published by the Free Software Foundation, either version 3 of the
 *    License, or any later version.
 *
 *    This program is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *    GNU Affero General Public License for more details.
 *
 *    You should have received a copy of the GNU Affero General Public License
 *    along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 */
#include "svc.h"
#include "../debug/logger.h"

RSA *RSA_tmp_callback(/* not used */ SSL *ssl, /* not used */ int is_export,
                                     int keylength) {
  RSA *res;
  std::lock_guard<std::mutex> lock__(RSA_mut);
  res = (keylength <= 512) ? RSA512_keys[rand() % N_RSA_KEYS]
                           : RSA1024_keys[rand() % N_RSA_KEYS];
  return res;
}

//int DH_set0_pqg(DH *dh, BIGNUM *p, BIGNUM *q, BIGNUM *g) {
//  /* If the fields p and g in d are NULL, the corresponding input
//   * parameters MUST be non-NULL.  q may remain NULL.
//   */
//  if ((dh->p == NULL && p == NULL) || (dh->g == NULL && g == NULL)) return 0;

//  if (p != NULL) {
//    BN_free(dh->p);
//    dh->p = p;
//  }
//  if (q != NULL) {
//    BN_free(dh->q);
//    dh->q = q;
//  }
//  if (g != NULL) {
//    BN_free(dh->g);
//    dh->g = g;
//  }

//  if (q != NULL) {
//    dh->length = BN_num_bits(q);
//  }

//  return 1;
//}
#ifndef SSL3_ST_SR_CLNT_HELLO_A
# define SSL3_ST_SR_CLNT_HELLO_A (0x110|SSL_ST_ACCEPT)
#endif
#ifndef SSL23_ST_SR_CLNT_HELLO_A
# define SSL23_ST_SR_CLNT_HELLO_A (0x210|SSL_ST_ACCEPT)
#endif

void SSLINFO_callback(const SSL *ssl, int where, int rc) {
  RENEG_STATE *reneg_state;

  /* Get our thr_arg where we're tracking this connection info */
  if ((reneg_state = static_cast<RENEG_STATE *> (SSL_get_app_data(ssl))) == nullptr)
    return;

  /* If we're rejecting renegotiations, move to ABORT if Client Hello is being
   * read. */
  if ((where & SSL_CB_ACCEPT_LOOP) && *reneg_state == RENEG_STATE::RENEG_REJECT) {
    int state;

    state = SSL_get_state(ssl);
    if (state == SSL3_ST_SR_CLNT_HELLO_A || state == SSL23_ST_SR_CLNT_HELLO_A) {
      *reneg_state = RENEG_STATE::RENEG_ABORT;
      Logger::logmsg(LOG_WARNING, "rejecting client initiated renegotiation");
    }
  } else if (where & SSL_CB_HANDSHAKE_DONE && *reneg_state == RENEG_STATE::RENEG_INIT) {
    // Reject any followup renegotiations
    *reneg_state = RENEG_STATE::RENEG_REJECT;
  }
}

int get_host(char *const name, addrinfo *res, int ai_family) {
  addrinfo *chain, *ap;
  addrinfo hints{};
  int ret_val;
  memset(&hints, 0, sizeof(hints));
  hints.ai_family = ai_family;
  hints.ai_socktype = SOCK_STREAM;
  hints.ai_flags = AI_CANONNAME;
  if ((ret_val = getaddrinfo(name, nullptr, &hints, &chain)) == 0) {
    for (ap = chain; ap != nullptr; ap = ap->ai_next)
      if (ap->ai_socktype == SOCK_STREAM) break;

    if (ap == nullptr) {
      freeaddrinfo(chain);
      return EAI_NONAME;
    }
    *res = *ap;
    if ((res->ai_addr = static_cast<sockaddr *>(malloc(ap->ai_addrlen))) == nullptr) {
      freeaddrinfo(chain);
      return EAI_MEMORY;
    }
    memcpy(res->ai_addr, ap->ai_addr, ap->ai_addrlen);
    freeaddrinfo(chain);
  }
  return ret_val;
}

DH *load_dh_params(char *file) {
  DH *dh = nullptr;
  BIO *bio;

  if ((bio = BIO_new_file(file, "r")) == nullptr) {
    Logger::logmsg(LOG_WARNING, "Unable to open DH file - %s", file);
    return nullptr;
  }

  dh = PEM_read_bio_DHparams(bio, nullptr, nullptr, nullptr);
  BIO_free(bio);
  return dh;
}

DH *DH_tmp_callback(SSL *s, int is_export, int keylength) {
  return keylength == 512 ? DH512_params : DH2048_params;
}
