//
// Created by abdess on 10/11/18.
//

#pragma once;

#include "json.h"
#include <string>
#include "JsonDataValue.h"

namespace json {
class JsonData : Json {
  std::string name_;
  JsonDataValue *data;
 public:

  JsonData(const JsonData &other);
  ~JsonData();
  JsonData(const JsonData &&other);
  JsonData(const char *name, const char *value);
  JsonData(const char *name, const JsonDataValue &value);;
  bool isData() override;
  std::string stringify() override;

};

}