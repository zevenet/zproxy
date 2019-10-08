/*
 *    Zevenet zproxy Load Balancer Software License
 *    This file is part of the Zevenet zproxy Load Balancer software package.
 *
 *    Copyright (C) 2019-today ZEVENET SL, Sevilla (Spain)
 *
 *    This program is free software: you can redistribute it and/or modify
 *    it under the terms of the GNU Affero General Public License as
 *    published by the Free Software Foundation, either version 3 of the
 *    License, or any later version.
 *
 *    This program is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *    GNU Affero General Public License for more details.
 *
 *    You should have received a copy of the GNU Affero General Public License
 *    along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 */
#pragma once
#include <map>
#include <memory>
#include <vector>
#include "json.h"

namespace json {

// template <typename JsonType>
class JsonArray : public Json, private std::vector<std::unique_ptr<Json>> {
  typedef std::unique_ptr<Json> T;
  typedef std::vector<std::unique_ptr<Json>> vector_;

 public:
  using vector_::at;
  using vector_::begin;
  using vector_::cbegin;
  using vector_::cend;
  using vector_::clear;
  using vector_::const_iterator;
  using vector_::crbegin;
  using vector_::crend;
  using vector_::empty;
  using vector_::end;
  using vector_::iterator;
  using vector_::reserve;
  using vector_::size;
  using vector_::operator[];
  using vector_::assign;
  using vector_::back;
  using vector_::emplace_back;
  using vector_::erase;
  using vector_::front;
  using vector_::insert;
  using vector_::pop_back;
  using vector_::push_back;
  using vector_::resize;

  bool isArray() override;
  JsonArray() = default;
  virtual ~JsonArray() = default;
  JsonArray(const JsonArray& json_array);
  std::string stringify(bool prettyfy = false, int tabs = -1) override;
};

// template <typename JsonType>
class JsonObject : public Json, private std::map<std::string, std::unique_ptr<Json>> {
  typedef std::unique_ptr<Json> T;
  typedef std::map<std::string, std::unique_ptr<Json>> map_;

 public:
  using map_::at;
  using map_::erase;
  using map_::insert;
  using map_::operator[];
  using map_::begin;
  using map_::cbegin;
  using map_::cend;
  using map_::clear;
  using map_::const_iterator;
  using map_::count;
  using map_::crbegin;
  using map_::crend;
  using map_::emplace;
  using map_::empty;
  using map_::end;
  using map_::iterator;
  using map_::size;

  ~JsonObject() = default;
  JsonObject() = default;
  JsonObject(const JsonObject& json_object);
  bool isObject() override;

  std::string stringify(bool prettyfy = false, int tabs = -1) override;
};
}  // namespace json
