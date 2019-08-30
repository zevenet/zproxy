#pragma once

#include <gtest/gtest.h>
#include "../../src/ssl/SSLContext.h"

using namespace ssl;

TEST(SSLContextTest, LoadFileTest){
  SSLContext ssl;
  bool result;

  ssl.ssl_ctx = SSL_CTX_new(SSLv23_server_method());
  result = ssl.loadOpensslConfig("/home/ffmancera/pifostio/zevenet/zhttp/tests/data/listener_ssl.cnf", "",ssl.ssl_ctx);
  EXPECT_TRUE(result);

  result = ssl.loadOpensslConfig("this/path/is/not/valid.cnf", "", ssl.ssl_ctx);
  EXPECT_FALSE(result);
}

TEST(SSLContextTest, LoadFileTestNotInitialized){
  SSLContext ssl;
  bool result;

  result = ssl.loadOpensslConfig("/home/ffmancera/pifostio/zevenet/zhttp/tests/data/listener_ssl.cnf", "",ssl.ssl_ctx);
  EXPECT_FALSE(result);
}
