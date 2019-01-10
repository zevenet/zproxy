#pragma once

#include <sstream>
#include "JsonData.h"
#include "JsonDataValue.h"
#include "JsonDataValueTypes.h"
#include <memory>

namespace json {

enum class JSON_PARSE_STATUS {
  OBJECT_START,
  OBJCT_END,
  ARRAY_START,
  ARRAY_END,
  DATA
};

class JsonParser {
public:
  JsonParser();
  static std::unique_ptr<JsonObject> parse(const std::string &json_data);
  static std::unique_ptr<JsonObject> parseJsonObject(std::istringstream &ss);
  static std::unique_ptr<JsonArray> parseJsonArray(std::istringstream &ss);
  static std::unique_ptr<JsonDataValue> parseJsonValue(std::istringstream &ss);
  static std::unique_ptr<JsonData> parseJsonData(std::istringstream &ss);
  static std::unique_ptr<JsonDataValue> parseJsonDataValue(std::istringstream &ss);

  static std::string getStringDelimitedBy(std::string str, char start_delimiter,
                                          char end_delimiter);

  static std::unique_ptr<Json> parseValue(char current_char, std::istringstream &istringstream);
};
}  // namespace json
