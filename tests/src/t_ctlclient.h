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

#include "../../src/ctl/main.cpp"
#include "gtest/gtest.h"

TEST(CTL_CLIENT, CTL_CLIENT_ARGS) {
  char *argv[] = {"../bin/zproxyctl",
                  "-X",
                  "-H",
                  "-c",
                  "/tmp/l7core_pound.socket",
                  "-N",
                  "1",
                  "2",
                  "192.168.0.1",
                  "3"};
  int argc = 10;
  ASSERT_TRUE(setArgumentsOptions(argc, argv));
}
