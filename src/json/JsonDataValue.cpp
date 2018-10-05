//
// Created by abdess on 10/11/18.
//

#include "JsonDataValue.h"
json::JsonDataValue::JsonDataValue(const json::JsonDataValue &value) { setValue(value); }
json::JsonDataValue::JsonDataValue(const json::JsonDataValue &&value) { setValue(value); }
json::JsonDataValue::JsonDataValue(const std::string &value) { setValue(value); }
json::JsonDataValue::JsonDataValue(const char *value) { setValue(value); }
json::JsonDataValue::JsonDataValue(int value) { setValue(value); }
json::JsonDataValue::JsonDataValue(double value) { setValue(value); }
json::JsonDataValue::JsonDataValue(bool value) { setValue(value); }
json::JsonDataValue::JsonDataValue(const json::JsonArray<json::JsonDataValue> &json_array) { setValue(json_array); }
json::JsonDataValue::JsonDataValue(const json::JsonObject<json::JsonDataValue> &json_object) { setValue(json_object); }

json::JsonDataValue::~JsonDataValue() {
//  if (array_value != nullptr) delete array_value;
//  if (object_value != nullptr)delete object_value;
}
json::JsonDataValue &json::JsonDataValue::operator=(const json::JsonDataValue &other) {
  setValue(other);
  return *this;
}
bool json::JsonDataValue::isValue() { return true; }
void json::JsonDataValue::setValue(const json::JsonDataValue &value) {
  switch (value.json_type) {
    case JSON_T_NULL:setNullValue();
      break;
    case JSON_T_STRING:setValue(value.value_);
      break;
    case JSON_T_BOOL: setValue(value.bool_value);
      break;
    case JSON_T_NUMBER: setValue(value.number_value);
      break;
    case JSON_T_OBJECT: setValue(value.object_value);
      break;
    case JSON_T_ARRAY:setValue(value.array_value);
      break;
  }
}
void json::JsonDataValue::setValue(const std::string &value) {
  value_ = std::string(value);
  json_type = JSON_T_STRING;
}
void json::JsonDataValue::setValue(const char *value) {
  value_ = std::string(value);
  json_type = JSON_T_STRING;
}
void json::JsonDataValue::setValue(double value) {
  number_value = value;
  json_type = JSON_T_NUMBER;
}
void json::JsonDataValue::setValue(int value) {
  number_value = value;
  json_type = JSON_T_NUMBER;
}
void json::JsonDataValue::setValue(bool value) {
  bool_value = value;
  json_type = JSON_T_BOOL;
}
void json::JsonDataValue::setNullValue() {
  value_ = "null";
  json_type = JSON_T_NULL;
}
void json::JsonDataValue::setValue(const json::JsonArray<json::JsonDataValue> &json_arry) {

  array_value = JsonArray<JsonDataValue>(json_arry);
  json_type = JSON_T_ARRAY;
}
void json::JsonDataValue::setValue(const json::JsonObject<json::JsonDataValue> &json_object) {

  object_value = JsonObject<JsonDataValue>(json_object);
  json_type = JSON_T_OBJECT;
}
std::string json::JsonDataValue::stringify() {
  switch (json_type) {
    case JSON_T_NULL:break;
    case JSON_T_STRING: return "\"" + value_ + "\"";
    case JSON_T_BOOL: return bool_value ? "true" : "false";
    case JSON_T_NUMBER:return std::to_string(number_value);
    case JSON_T_OBJECT: return object_value.stringify();
    case JSON_T_ARRAY: return array_value.stringify();
  }

  return std::string();
}
