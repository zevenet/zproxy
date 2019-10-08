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

#include "../../src/debug/logger.h"
#include "../../src/json/json.h"
#include "../../src/json/json_data.h"
#include "../../src/json/json_data_value_types.h"
#include "../../src/json/json_parser.h"
#include "../../src/util/common.h"
#include "gtest/gtest.h"
#include <string>

using namespace json;

TEST(JSON_TEST, JSON_TEST1) {
  JsonObject root;
  root.emplace("description",std::make_unique<JsonDataValue>("get services of farm"));
  auto services = std::make_unique<JsonObject>();

  auto backends = std::make_unique<JsonArray>();
  auto backends1= std::make_unique<JsonObject>();
  auto backends2= std::make_unique<JsonObject>();


  backends1->emplace("alias",std::make_unique<JsonDataValue>("http-server-1"));
  backends1->emplace("id",std::make_unique<JsonDataValue>(0));
  backends1->emplace("ip",std::make_unique<JsonDataValue>("192.168.100.254"));
  backends1->emplace("port",std::make_unique<JsonDataValue>(80));
  backends1->emplace("status",std::make_unique<JsonDataValue>("up"));
  backends1->emplace("timeout",std::make_unique<JsonDataValue>(20));
  backends1->emplace("weight",std::make_unique<JsonDataValue>());

  backends2->emplace("alias",std::make_unique<JsonDataValue>("http-server-2"));
  backends2->emplace("id",std::make_unique<JsonDataValue>(0));
  backends2->emplace("ip",std::make_unique<JsonDataValue>("192.168.100.253"));
  backends2->emplace("port",std::make_unique<JsonDataValue>(80));
  backends2->emplace("status",std::make_unique<JsonDataValue>("up"));
  backends2->emplace("timeout",std::make_unique<JsonDataValue>(20));
  backends2->emplace("weight",std::make_unique<JsonDataValue>());

  backends->emplace_back(std::move(backends1));
  backends->emplace_back(std::move(backends2));
  services->emplace("backends",std::move(backends));

  services->emplace("cookiedomain",std::make_unique<JsonDataValue>("zevenet.cpm"));
  services->emplace("cookieinsert",std::make_unique<JsonDataValue>("true"));
  services->emplace("cookiename",std::make_unique<JsonDataValue>("peasocookie"));
  services->emplace("cookiepath",std::make_unique<JsonDataValue>("/patfh"));
  services->emplace("cookiettl",std::make_unique<JsonDataValue>(20));
  services->emplace("farmguardian",std::make_unique<JsonDataValue>("check_tcp-cut_conns"));
  services->emplace("httpsb",std::make_unique<JsonDataValue>(false));
  services->emplace("id",std::make_unique<JsonDataValue>("serv"));
  services->emplace("leastresp",std::make_unique<JsonDataValue>(false));
  services->emplace("persistence",std::make_unique<JsonDataValue>("COOKIE"));
  services->emplace("redirect",std::make_unique<JsonDataValue>(""));
  services->emplace("redirect_code",std::make_unique<JsonDataValue>(""));
  services->emplace("redirecttype",std::make_unique<JsonDataValue>(""));
  services->emplace("sessionid",std::make_unique<JsonDataValue>("JSESSIONID"));
  services->emplace("sts_status",std::make_unique<JsonDataValue>("false"));
  services->emplace("sts_timeout",std::make_unique<JsonDataValue>(0));
  services->emplace("ttl",std::make_unique<JsonDataValue>(18));
  services->emplace("vhost",std::make_unique<JsonDataValue>());

  root.emplace("services",std::move(services));
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
