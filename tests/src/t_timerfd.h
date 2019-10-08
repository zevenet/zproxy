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

#include "../../src/event/timer_fd.h"
#include "gtest/gtest.h"

TEST(TimerFdTest, TimerFdTest1) {
  TimerFd t_fd;

  t_fd.set(2 *1000);
  EXPECT_FALSE(t_fd.isTriggered());
  sleep(3);
  EXPECT_TRUE(t_fd.isTriggered());
  EXPECT_GT(t_fd.getFileDescriptor(), 0);

  t_fd.set(2 * 1000);
  t_fd.unset();
  sleep(3);
  EXPECT_FALSE(t_fd.isTriggered());
}
