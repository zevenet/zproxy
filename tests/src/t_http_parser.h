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

//#include "gmock/gmock-matchers.h"
#include "../../zcutils/zcutils.h"
#include "../../src/http/http_parser.h"
#include "gtest/gtest.h"
#include <string>

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

  auto ret = phr_parse_request(s.c_str(), s.length(), &method, &method_len,
                               &path, &path_len, &minor_version, headers,
                               &num_headers, last_len);
  ASSERT_TRUE(s.length() == s.size());
  ASSERT_TRUE(ret == static_cast<int>(s.length()));
  zcu_log_print(LOG_DEBUG, "method is %.*s\n", method_len, method);
  zcu_log_print(LOG_DEBUG, "path is %.*s\n", path_len, path);
  zcu_log_print(LOG_DEBUG, "HTTP version is 1.%d\n", minor_version);
  zcu_log_print(LOG_DEBUG, "headers:\n");
  for (size_t i = 0; i != num_headers; ++i) {
    zcu_log_print(LOG_DEBUG, "%.*s: %.*s\n", headers[i].name_len,
                  headers[i].name, headers[i].value_len, headers[i].value);
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
