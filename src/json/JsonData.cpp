//
// Created by abdess on 10/11/18.
//

#include "JsonData.h"

json::JsonData::JsonData(const char *name, const char *value)
    : name_(std::string(name)) {
  data = new JsonDataValue(value);
}
json::JsonData::JsonData(const char *name, const json::JsonDataValue &value)
    : name_(std::string(name)), data(new JsonDataValue(value)) {}

json::JsonData::JsonData(const json::JsonData &other)
    : name_(other.name_), data(new JsonDataValue(other.data)) {}
json::JsonData::JsonData(const json::JsonData &&other)
    : name_(other.name_), data(new JsonDataValue(other.data)) {}
bool json::JsonData::isData() { return true; }

std::string json::JsonData::stringify(bool prettyfy, int tabs) {
  std::string res = "";
  for (auto num = tabs; num > 0 && prettyfy; num--) res += '\t';
  res = "\"" + name_ + "\" : " + data->stringify(prettyfy, tabs + 1);
  if (prettyfy) res += "\n";
  return res;
}

json::JsonData::~JsonData() { delete data; }
