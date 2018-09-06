//
// Created by abdess on 2/22/18.
#pragma once

//#include "gmock/gmock-matchers.h"
#include "gtest/gtest.h"
#include "../src/http/http_parser.h"
#include <string>
#include "../src/debug/Debug.h"

static int bufis(const char *s, size_t l, const char *t) {
  return strlen(t) == l && memcmp(s, t, l) == 0;
}

TEST(HttpParserTest, HttpParserTest1) {
  const char *method;
  size_t method_len;
  const char *path;
  size_t path_len;
  int minor_version;
  struct phr_header headers[4];
  size_t num_headers;
  size_t last_len = 0;
  std::string s = "GET /hoge HTTP/1.1\r\nHost: example.com\r\nUser-Agent: \343\201\262\343/1.0\r\n\r\n";
  num_headers = sizeof(headers) / sizeof(headers[0]);
  auto ret =
      phr_parse_request(s.c_str(),
                        s.length(),
                        &method,
                        &method_len,
                        &path,
                        &path_len,
                        &minor_version,
                        headers,
                        &num_headers,
                        last_len);
  ASSERT_TRUE(s.length() == s.size());
  ASSERT_TRUE(ret == s.length());
  Debug::logmsg(LOG_DEBUG, "method is %.*s\n", (int) method_len, method);
  Debug::logmsg(LOG_DEBUG, "path is %.*s\n", (int) path_len, path);
  Debug::logmsg(LOG_DEBUG, "HTTP version is 1.%d\n", minor_version);
  Debug::logmsg(LOG_DEBUG, "headers:\n");
  for (auto i = 0; i != num_headers; ++i) {
    Debug::logmsg(LOG_DEBUG, "%.*s: %.*s\n", (int) headers[i].name_len,
                  headers[i].name, (int) headers[i].value_len, headers[i].value);
  }
  ASSERT_TRUE(num_headers == 2);
  ASSERT_TRUE(bufis(method, method_len, "GET"));
  ASSERT_TRUE(bufis(path, path_len, "/hoge"));
  ASSERT_TRUE(minor_version == 1);
  ASSERT_TRUE(bufis(headers[0].name, headers[0].name_len, "Host"));
  ASSERT_TRUE(bufis(headers[0].value, headers[0].value_len, "example.com"));
  ASSERT_TRUE(bufis(headers[1].name, headers[1].name_len, "User-Agent"));
  ASSERT_TRUE(bufis(headers[1].value, headers[1].value_len, "\343\201\262\343/1.0"));
}
