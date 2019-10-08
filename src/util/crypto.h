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

#include <openssl/bio.h>
#include <openssl/evp.h>
#include <string>

namespace crypto {
struct base64 {
  static int encode(const std::string &str_in, int str_in_len, char *str_out,
                    int str_out_len) {
    int ret = 0;
    BIO *bio = BIO_new(BIO_s_mem());
    BIO *b64 = BIO_new(BIO_f_base64());
    //    BIO_set_flags(b64, BIO_FLAGS_BASE64_NO_NL);
    BIO_push(b64, bio);
    ret = BIO_write(b64, str_in.c_str(), str_in_len);
    BIO_flush(b64);
    if (ret > 0) {
      ret = BIO_read(bio, str_out, str_out_len);
    }

    BIO_free(b64);
    return ret;
  }

  static int decode(const std::string &str_in, int str_in_len, char *str_out,
                    int str_out_len) {
    int ret = 0;
    BIO *bio = BIO_new(BIO_s_mem());
    BIO *b64 = BIO_new(BIO_f_base64());
    //    BIO_set_flags(b64, BIO_FLAGS_BASE64_NO_NL);
    BIO_push(b64, bio);

    ret = BIO_write(bio, str_in.c_str(), str_in_len);
    BIO_flush(bio);
    if (ret) {
      ret = BIO_read(b64, str_out, str_out_len);
    }
    BIO_free(b64);
    return ret;
  }
};
} // namespace crypto
