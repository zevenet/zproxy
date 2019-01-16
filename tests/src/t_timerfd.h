// Created by fernando on 09/06/18.
#pragma once

#include "../../src/event/TimerFd.h"
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
