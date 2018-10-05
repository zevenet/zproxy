//
// Created by abdess on 10/11/18.
//
#pragma once
#include <vector>
#include <map>
#include "json.h"
#include "JsonDataValue.h"

namespace json {

template <typename JsonType>
class JsonArray : public Json, private std::vector<JsonType> {
  typedef JsonType T;
  typedef std::vector<JsonType> vector;
 public:
  using vector::push_back;
  using vector::operator[];
  using vector::begin;
  using vector::erase;
  using vector::end;
//  JsonArray operator=(const JsonArray & ) const;
  JsonArray() {}
  virtual ~JsonArray() {}

  bool isArray() override { return true; }
  std::string stringify() override {
    std::string res = "[";
    for (auto it = this->begin(); it != this->end(); it++) {
      res += it->stringify();
      if (it != this->end()) res += ",";
    }
    return res + "]";
  }
};

template <typename JsonType>
class JsonObject : public Json, private std::map<std::string, JsonType> {

  typedef Json T;
  typedef std::map<std::string, JsonType> map;
 public:
  using map::insert;
  using map::at;
  using map::erase;
  using map::operator[];
  using map::begin;
  using map::end;

  JsonObject() {}
  virtual ~JsonObject() {}

  bool isObject() override { return true; }
  std::string stringify() override {
    std::string res = "{";
    for (auto it = this->begin(); it != this->end(); it++) {
      if (it != this->begin()) res += ",";
      res += "\"" + it->first +" : "+ it->second.stringify();
    }
    return res + "}";
  }

};

}