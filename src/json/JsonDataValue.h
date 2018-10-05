//
// Created by abdess on 10/11/18.
//
#pragma  once
#include "json.h"
#include "JsonDataValueTypes.h"

namespace json {

class JsonDataValue : public Json {
 public:
  JSON_VALUE_TYPE json_type = JSON_T_NULL;
 // union {
    std::string value_ = "null";
    bool bool_value;
    double number_value;
    JsonArray<JsonDataValue> array_value;
    JsonObject<JsonDataValue> object_value;
  //};

  JsonDataValue() { setNullValue(); }
  virtual ~JsonDataValue();

  JsonDataValue(const JsonDataValue &value);
  JsonDataValue(const JsonDataValue &&value);
  JsonDataValue(const std::string &value);
  JsonDataValue(const char *value);
  JsonDataValue(int value);
  JsonDataValue(double value);
  JsonDataValue(bool value);
  JsonDataValue(const JsonArray<JsonDataValue> &json_array);
  JsonDataValue(const JsonObject<JsonDataValue> &json_object);

  JsonDataValue &operator=(const JsonDataValue &other);

  bool isValue() override;
  void setValue(const JsonDataValue &value);
  void setValue(const std::string &value);
  void setValue(const char *value);
  void setValue(double value);
  void setValue(int value);
  void setValue(bool value);
  void setNullValue();
  void setValue(const JsonArray<JsonDataValue> &json_arry);
  void setValue(const JsonObject<JsonDataValue> &json_object);

  std::string stringify() override;

};

}