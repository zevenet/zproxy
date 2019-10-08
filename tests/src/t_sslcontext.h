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

#include "../../src/ssl/ssl_context.h"
#include <gtest/gtest.h>

using namespace ssl;

TEST(SSLContextTest, LoadFileTest){
  SSLContext ssl;
  bool result;

  ssl.ssl_ctx = SSL_CTX_new(SSLv23_server_method());
  result = ssl.loadOpensslConfig("/home/ffmancera/pifostio/zevenet/zproxy/tests/data/listener_ssl.cnf", "",ssl.ssl_ctx);
  EXPECT_TRUE(result);

  result = ssl.loadOpensslConfig("this/path/is/not/valid.cnf", "", ssl.ssl_ctx);
  EXPECT_FALSE(result);
}

TEST(SSLContextTest, LoadFileTestNotInitialized){
  SSLContext ssl;
  bool result;

  result = ssl.loadOpensslConfig("/home/ffmancera/pifostio/zevenet/zproxy/tests/data/listener_ssl.cnf", "",ssl.ssl_ctx);
  EXPECT_FALSE(result);
}
