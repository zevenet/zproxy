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
#include "json.h"
#include "json_data_value_types.h"
namespace json {

class JsonDataValue : public Json {
 public:
  JSON_VALUE_TYPE json_type = JSON_VALUE_TYPE::JSON_T_NULL;
  //  union {
  std::string string_value;
  bool bool_value;
  long number_value;
  double double_value;
  std::unique_ptr<JsonArray> array_value;
  std::unique_ptr<JsonObject> object_value;
  //  };

  JsonDataValue() : double_value(0), number_value(0), bool_value(false), json_type(JSON_VALUE_TYPE::JSON_T_NULL) {
    setNullValue();
  }
  ~JsonDataValue() override = default;

  JsonDataValue(const JsonDataValue &value);
  JsonDataValue(const JsonDataValue &&value) noexcept;
  explicit JsonDataValue(const std::string &value);
  explicit JsonDataValue(const char *value);
  explicit JsonDataValue(int value);
  explicit JsonDataValue(unsigned long value);
  explicit JsonDataValue(unsigned int value);
  explicit JsonDataValue(long value);
  explicit JsonDataValue(double value);
  explicit JsonDataValue(bool value);
  explicit JsonDataValue(const JsonArray &json_array);
  explicit JsonDataValue(const JsonObject &json_object);
  JsonDataValue &operator=(const JsonDataValue &other);

  bool isValue() override;
  void setValue(const JsonDataValue &value);
  void setValue(const std::string &value);
  void setValue(const char *value);
  void setValue(double value);
  void setValue(long value);
  void setValue(bool value);
  void setNullValue();
  void setValue(const JsonArray &json_arry);
  void setValue(const JsonObject &json_object);

  std::string stringify(bool prettyfy = false, int tabs = -1) override;
};

}  // namespace json
