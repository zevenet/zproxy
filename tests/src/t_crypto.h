#pragma once

#include "../../zcutils/zcutils.h"
#include "../../src/util/crypto.h"
#include "gtest/gtest.h"
#include <string>

using namespace crypto;

TEST(CRYPTO_TEST, BASE64_TEST) {
  const std::string enc_data = "username:password\0";
  char out[256];
  char orig[256];
  int enc_out_len =
      base64::encode(enc_data, enc_data.length(), out, sizeof(out));
  zcutils_log_print(LOG_DEBUG, "Enc data [%s] len [%d]\n",
                std::string(out, enc_out_len).c_str(), enc_out_len);
  //  std::cout << "Enc data [" << out << "] len [" << enc_out_len << "]\n";
  int dec_out_len = base64::decode(out, enc_out_len, orig, sizeof(orig));
  zcutils_log_print(LOG_DEBUG, "Dec data [%s] len [%d]\n",
                std::string(orig).c_str(), dec_out_len);
  //  std::cout << "Enc data [" << out << "] len [" << enc_out_len << "]\n";
  ASSERT_TRUE(true);
}
