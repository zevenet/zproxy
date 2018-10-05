//
// Created by abdess on 10/4/18.
//
#pragma once

#include <string>

#include <vector>
namespace json {

enum JSON_VALUE_TYPE {
  JSON_T_NULL,
  JSON_T_STRING,
  JSON_T_BOOL,
  JSON_T_NUMBER,
  JSON_T_OBJECT,
  JSON_T_ARRAY
};

class Json {
 public:
  int json_size;
  virtual bool isArray() { return false; }
  virtual bool isObject() { return false; }
  virtual bool isData() { return false; }
  virtual bool isValue() { return false; }
  virtual std::string stringify() {};
  static Json *parse(std::string data);
};

}  // namespace json
