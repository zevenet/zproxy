//
// Created by abdess on 10/18/18.
//
#include "JsonDataValueTypes.h"

namespace json {

std::string JsonArray::stringify(bool prettyfy, int tabs) {
  std::string res = "";
  if (prettyfy) {
    res += '\n';
    for (auto num = tabs; num > 0; num--)
      res += '\t';
  }
  res += "[";
  if (prettyfy)
    res += '\n';
  for (auto it = this->begin(); it != this->end(); it++) {
    for (auto num = tabs; num > 0 && prettyfy; num--)
      res += '\t';
    if ((*it) == nullptr)
      continue;
    res += (*it)->stringify(prettyfy, tabs + 1);
    if (it != --this->end()) {
      res += ",";
    }
    if (prettyfy)
      res += '\n';
  }
  for (auto num = tabs; num > 0 && prettyfy; num--)
    res += '\t';
  return res + "]";
}

bool JsonArray::isArray() { return true; }
JsonArray::JsonArray(const JsonArray &json_array) {
  //TODO::Implement
}

std::string JsonObject::stringify(bool prettyfy, int tabs) {
  std::string res = "";
  if (prettyfy) {
    res += '\n';
    for (auto num = tabs; num > 0 && prettyfy; num--)
      res += '\t';
  }
  res += "{";
  if (prettyfy)
    res += '\n';
  for (auto it = this->begin(); it != this->end(); it++) {
    for (auto num = tabs; num > 0 && prettyfy; num--)
      res += '\t';
    if (it->second == nullptr)
      continue;
    res += "\"" + it->first + "\" : " + it->second->stringify(prettyfy, tabs + 1);
    if (it != --this->end()) {
      res += ",";
    }
    if (prettyfy)
      res += '\n';
  }
  for (auto num = tabs; num > 0 && prettyfy; num--)
    res += '\t';
  return res + "}";
}

bool JsonObject::isObject() { return true; }
JsonObject::JsonObject(const JsonObject &json_object) {
//TODO:: implement
}
} // namespace json
