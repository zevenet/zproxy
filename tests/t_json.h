//
// Created by abdess on 10/4/18.
//
#pragma once

#include <string>
#include "../src/debug/Debug.h"
#include "../src/json/json.h"
#include "../src/json/JsonData.h"
#include "../src/json/JsonDataValueTypes.h"
#include "gtest/gtest.h"

using namespace json;

TEST(JSON_TEST, JSON_TEST1) {

  JsonObject<JsonDataValue> root;

  root["description"] = JsonDataValue("get services of farm");
  JsonArray<JsonObject<JsonData>> backends;
  JsonObject<JsonData> backends1;
  root["description"] = JsonDataValue("get services of farm");
  root["description"] = JsonDataValue("get services of farm");
  root["description"] = JsonDataValue("get services of farm");
  root["description"] = JsonDataValue("get services of farm");
  root["description"] = JsonDataValue("get services of farm");
  JsonObject<JsonData> backends2;
  root["services"] = JsonDataValue();

  std::string json_str = root.stringify();

  ASSERT_TRUE(true);
}
