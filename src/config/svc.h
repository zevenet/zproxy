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
#pragma once

#include <malloc.h>
#include <netdb.h>
#include <openssl/ssl.h>
#include <cstring>
#include <mutex>
#include "../debug/debug.h"
#include "pound_struct.h"
/*
 * RSA ephemeral keys: how many and how often
 */
constexpr int N_RSA_KEYS = 11;
#ifndef T_RSA_KEYS /* Timeout for RSA ephemeral keys generation */
constexpr int T_RSA_KEYS = 7200;
#endif
static std::mutex RSA_mut;            /*Mutex for RSA keygen*/
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

//#include "dh512.h"//TODO::

#if DH_LEN == 1024
#include "dh1024.h"
static DH *DH512_params, *DH1024_params;

DH *DH_tmp_callback(/* not used */ SSL *s, /* not used */ int is_export, int keylength) {
  return keylength == 512 ? DH512_params : DH1024_params;
}
#else
//#include "dh2048.h" //TODO
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
