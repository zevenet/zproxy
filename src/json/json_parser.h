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

#include "json_data.h"
#include "json_data_value.h"
#include "json_data_value_types.h"
#include <memory>
#include <sstream>

namespace json
{
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
	static std::unique_ptr<JsonObject>
	parseJsonObject(std::istringstream &ss);
	static std::unique_ptr<JsonArray>
	parseJsonArray(std::istringstream &ss);
	static std::unique_ptr<JsonDataValue>
	parseJsonValue(std::istringstream &ss);
	static std::unique_ptr<JsonData> parseJsonData(std::istringstream &ss);
	static std::unique_ptr<JsonDataValue>
	parseJsonDataValue(std::istringstream &ss);

	static std::string getStringDelimitedBy(std::string str,
						char start_delimiter,
						char end_delimiter);
	static std::unique_ptr<Json>
	parseValue(char current_char, std::istringstream &istringstream);
};
} // namespace json
