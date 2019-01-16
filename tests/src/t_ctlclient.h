#pragma once

#include "../../src/ctl/main.cpp"
#include "gtest/gtest.h"

TEST(CTL_CLIENT, CTL_CLIENT_ARGS) {
  char *argv[] = {"../bin/zhttpctl",
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
