//
// Created by abdess on 10/11/18.
//

#include "JsonData.h"

json::JsonData::JsonData(const char *name, const char *value) : name_(std::string(name)
) {
  data = new JsonDataValue(value);
}
json::JsonData::JsonData(const char *name, const json::JsonDataValue &value)
    : name_(std::string(name)), data(new JsonDataValue(value)) {}
json::JsonData::JsonData(const json::JsonData &other) : name_(other.name_), data(new JsonDataValue(other.data)) {}
json::JsonData::JsonData(const json::JsonData &&other) : name_(other.name_), data(new JsonDataValue(other.data)) {}
bool json::JsonData::isData() { return true; }
std::string json::JsonData::stringify() {
  return name_ + " : " + data->stringify();
}
json::JsonData::~JsonData() {
  delete data;
}
