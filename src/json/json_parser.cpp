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
#include "json_parser.h"
#include "../util/utils.h"
#include <algorithm>
json::JsonParser::JsonParser()
{
}

std::string json::JsonParser::getStringDelimitedBy(std::string str,
						   char start_delimiter,
						   char end_delimiter)
{
	auto first = str.find_first_of(start_delimiter);
	auto last = str.find_last_of(end_delimiter);
	return str.substr(first + 1, (last - 1) - first);
}

std::unique_ptr<json::JsonObject>
json::JsonParser::parse(const std::string &json_data)
{
	// remove spaces
	std::string str(json_data);
	if (str.empty())
		return nullptr;
	str.erase(std::remove_if(str.begin(), str.end(), isspace), str.end());
	std::istringstream ss(str);
	return parseJsonObject(ss);
}

std::unique_ptr<json::JsonObject>
json::JsonParser::parseJsonObject(std::istringstream &ss)
{
	while ((ss.get()) != '{')
		;
	char next_char;

	std::unique_ptr<JsonObject> json_object(new JsonObject());
	if (ss.peek() == '}')
		return json_object;
	do {
		std::string key;
		if (!getline(ss, key, ':'))
			return nullptr;
		key = getStringDelimitedBy(key, '\"', '\"');
		next_char = static_cast<char>(ss.peek());
		auto value = parseValue(next_char, ss);
		json_object->emplace(key, std::move(value));
		if ((next_char = static_cast<char>(ss.get())) == '}')
			break;
	} while (true);

	return json_object;
}

std::unique_ptr<json::JsonArray>
json::JsonParser::parseJsonArray(std::istringstream &ss)
{
	while ((ss.get()) != '[')
		;
	char next_char = static_cast<char>(ss.peek());
	std::unique_ptr<JsonArray> json_array(new JsonArray());
	if (ss.peek() == ']') {
		ss.get();
		return json_array;
	}
	do {
		if (next_char == ',') {
			next_char = static_cast<char>(ss.peek());
			continue;
		}
		if (next_char == ']')
			break;
		auto value = parseValue(next_char, ss);
		if (value != nullptr) {
			json_array->emplace_back(std::move(value));
		}
		next_char = static_cast<char>(ss.get());
		if (next_char == ']')
			break;
	} while (true);
	return json_array;
}

std::unique_ptr<json::JsonDataValue>
json::JsonParser::parseJsonValue(std::istringstream &ss)
{
	return nullptr;
}

std::unique_ptr<json::JsonData>
json::JsonParser::parseJsonData(std::istringstream &ss)
{
	return nullptr;
}

std::unique_ptr<json::JsonDataValue>
json::JsonParser::parseJsonDataValue(std::istringstream &ss)
{
	return nullptr;
}

std::unique_ptr<json::Json> json::JsonParser::parseValue(char current_char,
							 std::istringstream &ss)
{
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
		if (!getline(ss, value, '"'))
			return nullptr;
		if (value == "true" || value == "false")
			return std::unique_ptr<JsonDataValue>(
				new JsonDataValue(value == "true"));
		else
			return std::unique_ptr<JsonDataValue>(
				new JsonDataValue(value));
	}
	case 'n': {
		return std::unique_ptr<JsonDataValue>(new JsonDataValue());
		;
	}
	case '-':
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
			next_char = static_cast<char>(ss.peek());
			int num;
			if (next_char == '.') {
				// bugfix: a dot already was found.
				// example: "id": 127.0.0.2
				if (is_double)
					return nullptr;
				number += ss.get();
				is_double = true;
			} else if (::isdigit(next_char)) {
				number += ss.get();
			} else {
				done = true;
			}
		}
		if (is_double) {
			return std::unique_ptr<JsonDataValue>(
				new JsonDataValue(std::stod(number)));
		} else {
			return std::unique_ptr<JsonDataValue>(
				new JsonDataValue(std::stol(number)));
		}
	}
	case 't':
		return std::unique_ptr<JsonDataValue>(new JsonDataValue(true));
	case 'f':
		return std::unique_ptr<JsonDataValue>(new JsonDataValue(false));
	default:
		break;
	}
	return nullptr;
}
