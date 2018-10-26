//
// Created by abdess on 10/4/18.
//
#pragma once

#include <string>
#include "../src/debug/Debug.h"
#include "../src/json/JsonData.h"
#include "../src/json/JsonDataValueTypes.h"
#include "../src/json/json.h"
#include "../src/json/jsonparser.h"
#include "gtest/gtest.h"

using namespace json;

TEST(JSON_TEST, JSON_TEST1) {
  JsonObject root;
  root["description"] = new JsonDataValue("get services of farm");
  JsonObject services;
  root["services"] = &services;
  JsonArray backends;
  JsonObject backends1;
  JsonObject backends2;
  backends.push_back(&backends1);
  backends.push_back(&backends2);
  services["backends"] = &backends;

  backends1["alias"] = new JsonDataValue("http-server-1");
  backends1["id"] = new JsonDataValue(0);
  backends1["ip"] = new JsonDataValue("192.168.100.254");
  backends1["port"] = new JsonDataValue(80);
  backends1["status"] = new JsonDataValue("up");
  backends1["timeout"] = new JsonDataValue(20);
  backends1["weight"] = new JsonDataValue();

  backends2["alias"] = new JsonDataValue("http-server-2");
  backends2["id"] = new JsonDataValue(0);
  backends2["ip"] = new JsonDataValue("192.168.100.253");
  backends2["port"] = new JsonDataValue(80);
  backends2["status"] = new JsonDataValue("up");
  backends2["timeout"] = new JsonDataValue(20);
  backends2["weight"] = new JsonDataValue();

  services["cookiedomain"] = new JsonDataValue("zevenet.cpm");
  services["cookieinsert"] = new JsonDataValue("true");
  services["cookiename"] = new JsonDataValue("peasocookie");
  services["cookiepath"] = new JsonDataValue("/patfh");
  services["cookiettl"] = new JsonDataValue(20);
  services["farmguardian"] = new JsonDataValue("check_tcp-cut_conns");
  services["httpsb"] = new JsonDataValue(false);
  services["id"] = new JsonDataValue("serv");
  services["leastresp"] = new JsonDataValue(false);
  services["persistence"] = new JsonDataValue("COOKIE");
  services["redirect"] = new JsonDataValue("");
  services["redirect_code"] = new JsonDataValue("");
  services["redirecttype"] = new JsonDataValue("");
  services["sessionid"] = new JsonDataValue("JSESSIONID");
  services["sts_status"] = new JsonDataValue("false");
  services["sts_timeout"] = new JsonDataValue(0);
  services["ttl"] = new JsonDataValue(18);
  services["urlp"] = new JsonDataValue("(?i)^/music$");
  services["vhost"] = new JsonDataValue();
  std::string json_str = root.stringify();

  // TODO::fixme  root.freeJson();
  ASSERT_TRUE(true);
}

TEST(JSON_TEST, PARSER_TEST) {
  std::string json_string =
      "{\n"
      "    \"address\": \"0.0.0.0\",\n"
      "    \"port\": 8899,\n"
      "    \"services\": [\n"
      "        {\n"
      "            \"backends\": [\n"
      "                {\n"
      "                    \"address\": \"192.168.101.253\",\n"
      "                    \"connect-time\": 0,\n"
      "                    \"connections\": 0,\n"
      "                    \"id\": 1,\n"
      "                    \"name\": \"bck_1\",\n"
      "                    \"pending-connections\": 0,\n"
      "                    \"port\": 80,\n"
      "                    \"response-time\": 0,\n"
      "                    \"status\": \"active\",\n"
      "                    \"weight\": 5\n"
      "                },\n"
      "                {\n"
      "                    \"address\": \"192.168.101.254\",\n"
      "                    \"connect-time\": 0,\n"
      "                    \"connections\": 0,\n"
      "                    \"id\": 2,\n"
      "                    \"name\": \"bck_2\",\n"
      "                    \"pending-connections\": 0,\n"
      "                    \"port\": 80,\n"
      "                    \"response-time\": 0,\n"
      "                    \"status\": \"active\",\n"
      "                    \"weight\": 6\n"
      "                }\n"
      "            ],\n"
      "            \"id\": 1,\n"
      "            \"name\": \"srv1\",\n"
      "            \"sessions\": [\n"
      "                {\n"
      "                    \"backend-id\": 2,\n"
      "                    \"id\": \"127.0.0.1\",\n"
      "                    \"last-seen\": 1539952046\n"
      "                }\n"
      "            ],\n"
      "            \"status\": \"active\"\n"
      "        },\n"
      "        {\n"
      "            \"backends\": [\n"
      "                {\n"
      "                    \"address\": \"192.168.101.253\",\n"
      "                    \"connect-time\": 0,\n"
      "                    \"connections\": 0,\n"
      "                    \"id\": 1,\n"
      "                    \"name\": \"bck_1\",\n"
      "                    \"pending-connections\": 0,\n"
      "                    \"port\": 80,\n"
      "                    \"response-time\": 0,\n"
      "                    \"status\": \"active\",\n"
      "                    \"weight\": 5\n"
      "                },\n"
      "                {\n"
      "                    \"address\": \"192.168.101.254\",\n"
      "                    \"connect-time\": 0,\n"
      "                    \"connections\": 0,\n"
      "                    \"id\": 2,\n"
      "                    \"name\": \"bck_2\",\n"
      "                    \"pending-connections\": 0,\n"
      "                    \"port\": 80,\n"
      "                    \"response-time\": 0,\n"
      "                    \"status\": \"active\",\n"
      "                    \"weight\": 6\n"
      "                }\n"
      "            ],\n"
      "            \"id\": 2,\n"
      "            \"name\": \"srv2\",\n"
      "            \"sessions\": [],\n"
      "            \"status\": \"active\"\n"
      "        }\n"
      "    ]\n"
      "}";
  auto new_json = JsonParser::parse(json_string);
  auto str = new_json->stringify();
  json_string.erase(
      std::remove_if(json_string.begin(), json_string.end(), isspace),
      json_string.end());
  str.erase(std::remove_if(str.begin(), str.end(), isspace), str.end());
  ASSERT_TRUE(json_string.length() == str.length());
}
