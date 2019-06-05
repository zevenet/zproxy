#pragma once

#include "../../src/config/config.h"
#include "../lib/gtest/googletest/include/gtest/gtest.h"
#include "../../src/handlers/zlib_util.h"

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
