#include "jsonparser.h"
#include <algorithm>
#include "../util/utils.h"
json::JsonParser::JsonParser() {}

std::string json::JsonParser::getStringDelimitedBy(std::string str,
                                                   char start_delimiter,
                                                   char end_delimiter) {
  auto first = str.find_first_of(start_delimiter);
  auto last = str.find_last_of(end_delimiter);
  return str.substr(first + 1, (last - 1) - first);
}
json::JsonObject *json::JsonParser::parse(const std::string &json_data) {
  // remove spaces
  std::string str(json_data);
  if (str.empty()) return nullptr;
  str.erase(std::remove_if(str.begin(), str.end(), isspace), str.end());
  std::istringstream ss(str);
  return parseJsonObject(ss);
}
json::JsonObject *json::JsonParser::parseJsonObject(std::istringstream &ss) {
  while ((ss.get()) != '{')
    ;
  char next_char;

  auto json_object = new JsonObject();
  if (ss.peek() == '}') return json_object;
  do {
    std::string key;
    if (!getline(ss, key, ':')) return nullptr;
    key = getStringDelimitedBy(key, '\"', '\"');
    next_char = ss.peek();
    auto value = parseValue(next_char, ss);
    json_object->emplace(key, value);
    if ((next_char = ss.get()) == '}') break;
  } while (true);

  return json_object;
}
json::JsonArray *json::JsonParser::parseJsonArray(std::istringstream &ss) {
  while ((ss.get()) != '[')
    ;
  char next_char = ss.peek();
  auto json_array = new JsonArray();
  if (ss.peek() == ']') return json_array;
  do {
    if (next_char == ',') {
      next_char = ss.peek();
      continue;
    }
    if (next_char == ']') break;
    auto value = parseValue(next_char, ss);
    if (value != nullptr) {
      json_array->push_back(value);
    }
    next_char = ss.get();
    if (next_char == ']') break;
  } while (true);
  return json_array;
}

json::JsonDataValue *json::JsonParser::parseJsonValue(std::istringstream &ss) {
  return nullptr;
}
json::JsonData *json::JsonParser::parseJsonData(std::istringstream &ss) {
  return nullptr;
}
json::JsonDataValue *json::JsonParser::parseJsonDataValue(
    std::istringstream &ss) {
  return nullptr;
}
json::Json *json::JsonParser::parseValue(char current_char,
                                         std::istringstream &ss) {
  char next_char = current_char;
  switch (next_char) {
    case '{': {
      return parseJsonObject(ss);
    }
    case '[': {
      return parseJsonArray(ss);
    }
    case '"': {
      ss.get();
      std::string value = "null";
      if (!getline(ss, value, '"')) return nullptr;
      if (value == "true" || value == "false")
        return new JsonDataValue(value == "true");
      else
        return new JsonDataValue(value);
    }
    case 'n': {
      return new JsonDataValue();
    }
    case '0':
    case '1':
    case '2':
    case '3':
    case '4':
    case '5':
    case '6':
    case '7':
    case '8':
    case '9': {
      std::string number = "";
      number += ss.get();
      bool is_double = false;
      bool done = false;
      while (!done) {
        next_char = ss.peek();
        int num;
        if (next_char == '.') {
          number += ss.get();
          is_double = true;
        } else if (::isdigit(next_char)) {
          number += ss.get();
        } else {
          done = true;
        }
      }
      if (is_double) {
        return new JsonDataValue(std::stod(number));
      } else {
        return new JsonDataValue(std::stol(number));
      }
    }
    default:
      break;
  }
  return nullptr;
}
