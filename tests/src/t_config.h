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

TEST(ConfigTest, ConfigTest1) {
  std::string args[] = {"../bin/zproxy", "-f", "l7core_pound.cfg"};
  char *argv[] = {args[0].data(), args[1].data(), args[2].data()};
  int argc = 3;
  Config config;

  config.init(argc, argv);
  // auto fname = config.f_name;
  auto backend_config = config.listeners;
  auto nnn = backend_config->services;
  auto nn = nnn->backends[0];

  EXPECT_TRUE(config.listeners != NULL);
  EXPECT_TRUE(config.listeners->services != NULL);
  EXPECT_TRUE(config.listeners->services->backends != NULL);
}
