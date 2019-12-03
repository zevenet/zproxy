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
#include <openssl/engine.h>
#include <openssl/lhash.h>
#include <openssl/ssl.h>
#include <openssl/x509v3.h>
#include <mutex>
#include "../debug/logger.h"

#include "dh512.h"
#if DH_LEN == 1024
#include "dh1024.h"
#else
#include "dh2048.h"
#endif

namespace global {
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

#if OPENSSL_VERSION_NUMBER >= 0x10100000L
#define general_name_string(n)                                             \
  reinterpret_cast<unsigned char *>(strndup(                               \
      reinterpret_cast<const char *>(ASN1_STRING_get0_data(n->d.dNSName)), \
      ASN1_STRING_length(n->d.dNSName) + 1))
#else
#define general_name_string(n)                                     \
  (unsigned char *)strndup((char *)ASN1_STRING_data(n->d.dNSName), \
                           ASN1_STRING_length(n->d.dNSName) + 1)
#endif

struct SslHelper {
  /*
   * return a pre-generated RSA key
   */
  static RSA *RSA_tmp_callback(/* not used */ SSL *ssl,
                               /* not used */ int is_export, int keylength);
  static DH *load_dh_params(char *file);
  static void SSLINFO_callback(const SSL *ssl, int where, int rc);
  static int generate_key(RSA **ret_rsa, unsigned long bits);
#if DH_LEN == 1024
  static DH *DH512_params, *DH1024_params;
  static DH *DH_tmp_callback(/* not used */ SSL *s,
                             /* not used */ int is_export, int keylength) {
    return keylength == 512 ? DH512_params : DH1024_params;
  }
#else
  static DH *DH512_params, *DH2048_params;
  static DH *DH_tmp_callback(/* not used */ SSL *s,
                             /* not used */ int is_export, int keylength) {
    return keylength == 512 ? DH512_params : DH2048_params;
  }
#endif

  /*
   * initialise DH and RSA keys
   */
  static void initDhParams();

  /*
   * Periodically regenerate ephemeral RSA keys
   * runs every T_RSA_KEYS seconds
   */
  static void doRSAgen();
  /*
   * Dummy certificate verification - always OK
   */
  static int verifyCertificate_OK([[maybe_unused]] int pre_ok, 
                                  [[maybe_unused]] X509_STORE_CTX *ctx);
  SslHelper() { initDhParams(); }
  static SslHelper &getCurrent();

 private:
  static SslHelper current;
};
};  // namespace global