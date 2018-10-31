//
// Created by abdess on 10/11/18.
//
#pragma once
#include "JsonDataValueTypes.h"
#include "json.h"
namespace json {

class JsonDataValue : public Json {
 public:
  JSON_VALUE_TYPE json_type = JSON_VALUE_TYPE::JSON_T_NULL;
  //  union {
  std::string string_value;
  bool bool_value;
  long number_value;
  double double_value;
  JsonArray *array_value;
  JsonObject *object_value;
  //  };

  JsonDataValue() { setNullValue(); }
  virtual ~JsonDataValue();

  JsonDataValue(const JsonDataValue &value);
  JsonDataValue(const JsonDataValue &&value);
  JsonDataValue(const std::string &value);
  JsonDataValue(const char *value);
  JsonDataValue(int value);
    JsonDataValue(unsigned int value);
  JsonDataValue(long value);
  JsonDataValue(double value);
  JsonDataValue(bool value);
  JsonDataValue(const JsonArray &json_array);
  JsonDataValue(const JsonObject &json_object);
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

  void freeJson() override;
  std::string stringify(bool prettyfy = false, int tabs = -1) override;
};

}  // namespace json
