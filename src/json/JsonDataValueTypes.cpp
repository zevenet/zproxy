//
// Created by abdess on 10/18/18.
//
#include "JsonDataValueTypes.h"

namespace json {

void JsonArray::freeJson() {
  for (auto data : *this) {
    Json *data_ptr = data;
    data_ptr->freeJson();
    delete data_ptr;
  }
  this->clear();
}

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
    res += (*it)->stringify(tabs + 1);
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

void JsonObject::freeJson() {
  for (auto &data : *this) {
    data.second->freeJson();
    Json *data_ptr = data.second;
    delete data_ptr; // TODO:: FIX SIGABRT
  }
  this->clear();
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
    res += "\"" + it->first + "\" : " + it->second->stringify(tabs + 1);
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
} // namespace json
