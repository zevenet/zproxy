#pragma once

#include "../src/config/config.h"
#include "gtest/gtest.h"

TEST(ConfigTest, ConfigTest1) {
  char *argv[] = {"../bin/zhttp", "-f",
                  "/home/ffmancera/pifostio/zevenet/zhttp/tests/l7core_pound.cfg"};
  int argc = 3;
  Config config;

  config.parseConfig(argc, argv);
  // auto fname = config.f_name;
  auto backend_config = config.listeners;
  auto nnn = backend_config->services;
  auto nn = nnn->backends[0];

  EXPECT_TRUE(config.listeners != NULL);
  EXPECT_TRUE(config.listeners->services != NULL);
  EXPECT_TRUE(config.listeners->services->backends != NULL);
}
