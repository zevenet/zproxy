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
#include "json_data_value_types.h"

namespace json {

std::string JsonArray::stringify(bool prettyfy, int tabs) {
  std::string res = "";
  if (prettyfy) {
    res += '\n';
    for (auto num = tabs; num > 0; num--) res += '\t';
  }
  res += "[";
  if (prettyfy) res += '\n';
  for (auto it = this->begin(); it != this->end(); it++) {
    for (auto num = tabs; num > 0 && prettyfy; num--) res += '\t';
    if ((*it) == nullptr) continue;
    res += (*it)->stringify(prettyfy, tabs + 1);
    if (it != --this->end()) {
      res += ",";
    }
    if (prettyfy) res += '\n';
  }
  for (auto num = tabs; num > 0 && prettyfy; num--) res += '\t';
  return res + "]";
}

bool JsonArray::isArray() { return true; }
JsonArray::JsonArray(const JsonArray &json_array) {
  // TODO::Implement
}

std::string JsonObject::stringify(bool prettyfy, int tabs) {
  std::string res = "";
  if (prettyfy) {
    res += '\n';
    for (auto num = tabs; num > 0 && prettyfy; num--) res += '\t';
  }
  res += "{";
  if (prettyfy) res += '\n';
  for (auto it = this->begin(); it != this->end(); it++) {
    for (auto num = tabs; num > 0 && prettyfy; num--) res += '\t';
    if (it->second == nullptr) continue;
    res += "\"" + it->first + "\" : " + it->second->stringify(prettyfy, tabs + 1);
    if (it != --this->end()) {
      res += ",";
    }
    if (prettyfy) res += '\n';
  }
  for (auto num = tabs; num > 0 && prettyfy; num--) res += '\t';
  return res + "}";
}

bool JsonObject::isObject() { return true; }
JsonObject::JsonObject(const JsonObject &json_object) {
  // TODO:: implement
}
}  // namespace json
