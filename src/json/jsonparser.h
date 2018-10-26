#pragma once

#include <sstream>
#include "JsonData.h"
#include "JsonDataValue.h"
#include "JsonDataValueTypes.h"

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
  static JsonObject *parse(const std::string &json_data);
  static JsonObject *parseJsonObject(std::istringstream &ss);
  static JsonArray *parseJsonArray(std::istringstream &ss);
  static JsonDataValue *parseJsonValue(std::istringstream &ss);
  static JsonData *parseJsonData(std::istringstream &ss);
  static JsonDataValue *parseJsonDataValue(std::istringstream &ss);

  static std::string getStringDelimitedBy(std::string str, char start_delimiter,
                                          char end_delimiter);

  static Json *parseValue(char current_char, std::istringstream &istringstream);
};
}  // namespace json
