//
// Created by abdess on 10/11/18.
//
#pragma once
#include "json.h"
#include <map>
#include <vector>

namespace json {

// template <typename JsonType>
class JsonArray : public Json, protected std::vector<Json *> {
  //  typedef JsonType T;
  typedef std::vector<Json *> vector;

public:
  using vector::push_back;
  using vector::operator[];
  using vector::begin;
  using vector::end;
  using vector::erase;

  void freeJson() override;
  bool isArray() override;
  std::string stringify(bool prettyfy = false, int tabs = -1) override;
};

// template <typename JsonType>
class JsonObject : public Json, protected std::map<std::string, Json *> {
  //  typedef Json T;
  typedef std::map<std::string, Json *> map;

public:
  using map::at;
  using map::erase;
  using map::insert;
  using map::operator[];
  using map::begin;
  using map::emplace;
  using map::empty;
  using map::end;
  using map::count;

  bool isObject() override;
  void freeJson() override;
  std::string stringify(bool prettyfy = false, int tabs = -1) override;
};
} // namespace json
