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

#include "../../src/config/config.h"
#include "../lib/gtest/googletest/include/gtest/gtest.h"
#include "../../src/util/zlib_util.h"

TEST(CompressionTest, CompressionTestDeflate) {

  std::string message = "Normal message, this message is going to be compressed.";
  std::string message_compressed;
  std::string message_after_decompression;

  EXPECT_TRUE(zlib::compress_message_deflate(message, message_compressed));
  EXPECT_TRUE(zlib::decompress_message_deflate(message_compressed, message_after_decompression));

  EXPECT_TRUE(message.compare(message_after_decompression) == 0);
}

TEST(CompressionTest, CompressionTestGzip) {

  std::string message = "Normal message, this message is going to be compressed.";
  std::string message_compressed;
  std::string message_after_decompression;

  EXPECT_TRUE(zlib::compress_message_gzip(message, message_compressed));
  EXPECT_TRUE(zlib::decompress_message_gzip(message_compressed, message_after_decompression));

  EXPECT_TRUE(message.compare(message_after_decompression) == 0);
}
