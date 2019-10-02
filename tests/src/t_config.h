#pragma once

#include "../../src/config/config.h"
#include "../lib/gtest/googletest/include/gtest/gtest.h"

TEST(ConfigTest, ConfigTest1) {
  std::string args[] = {"../bin/zhttp", "-f", "l7core_pound.cfg"};
  char *argv[] = {args[0].data(), args[1].data(), args[2].data()};
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
