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

#include "json_data_value.h"
#include <functional>

json::JsonDataValue::JsonDataValue(const json::JsonDataValue &value)
{
	setValue(value);
}

json::JsonDataValue::JsonDataValue(const json::JsonDataValue &&value) noexcept
{
	setValue(value);
}

json::JsonDataValue::JsonDataValue(const std::string &value)
{
	setValue(value);
}

json::JsonDataValue::JsonDataValue(const char *value)
{
	setValue(value);
}

json::JsonDataValue::JsonDataValue(int value)
{
	setValue(static_cast<long>(value));
}

json::JsonDataValue::JsonDataValue(unsigned int value)
{
	setValue(static_cast<long>(value));
}

json::JsonDataValue::JsonDataValue(double value)
{
	setValue(value);
}

json::JsonDataValue::JsonDataValue(bool value)
{
	setValue(value);
}

json::JsonDataValue::JsonDataValue(const json::JsonArray &json_array)
{
	setValue(json_array);
}

json::JsonDataValue::JsonDataValue(const json::JsonObject &json_object)
{
	setValue(json_object);
}

json::JsonDataValue::JsonDataValue(long value)
{
	setValue(value);
}

json::JsonDataValue::JsonDataValue(unsigned long value)
{
	setValue(static_cast<long>(value));
}

json::JsonDataValue &
json::JsonDataValue::operator=(const json::JsonDataValue &other)
{
	setValue(other);
	return *this;
}

bool json::JsonDataValue::isValue()
{
	return true;
}

void json::JsonDataValue::setValue(const json::JsonDataValue &value)
{
	switch (value.json_type) {
	case JSON_VALUE_TYPE::JSON_T_NULL:
		setNullValue();
		break;
	case JSON_VALUE_TYPE::JSON_T_STRING:
		setValue(value.string_value);
		break;
	case JSON_VALUE_TYPE::JSON_T_BOOL:
		setValue(value.bool_value);
		break;
	case JSON_VALUE_TYPE::JSON_T_NUMBER:
		setValue(value.number_value);
		break;
	case JSON_VALUE_TYPE::JSON_T_OBJECT:
		setValue(*value.object_value);
		break;
	case JSON_VALUE_TYPE::JSON_T_ARRAY:
		setValue(*value.array_value);
		break;
	}
}

void json::JsonDataValue::setValue(const std::string &value)
{
	string_value = std::string(value);
	json_type = JSON_VALUE_TYPE::JSON_T_STRING;
}

void json::JsonDataValue::setValue(const char *value)
{
	string_value = std::string(value);
	json_type = JSON_VALUE_TYPE::JSON_T_STRING;
}

void json::JsonDataValue::setValue(double value)
{
	double_value = value;
	json_type = JSON_VALUE_TYPE::JSON_T_DOUBLE;
}

void json::JsonDataValue::setValue(long value)
{
	number_value = value;
	json_type = JSON_VALUE_TYPE::JSON_T_NUMBER;
}

void json::JsonDataValue::setValue(bool value)
{
	bool_value = value;
	json_type = JSON_VALUE_TYPE::JSON_T_BOOL;
}

void json::JsonDataValue::setNullValue()
{
	string_value = "null";
	json_type = JSON_VALUE_TYPE::JSON_T_NULL;
}

void json::JsonDataValue::setValue(const json::JsonArray &json_arry)
{
	array_value.reset(new JsonArray(json_arry));
	json_type = JSON_VALUE_TYPE::JSON_T_ARRAY;
}

void json::JsonDataValue::setValue(const json::JsonObject &json_object)
{
	object_value.reset(new JsonObject(json_object));
	json_type = JSON_VALUE_TYPE::JSON_T_OBJECT;
}

std::string json::JsonDataValue::stringify(bool prettyfy, int tabs)
{
	switch (json_type) {
	case JSON_VALUE_TYPE::JSON_T_NULL:
		break;
	case JSON_VALUE_TYPE::JSON_T_STRING:
		return "\"" + string_value + "\"";
	case JSON_VALUE_TYPE::JSON_T_BOOL:
		return bool_value ? "true" : "false";
	case JSON_VALUE_TYPE::JSON_T_NUMBER:
		return std::to_string(number_value);
	case JSON_VALUE_TYPE::JSON_T_DOUBLE:
		return std::to_string(double_value);
	case JSON_VALUE_TYPE::JSON_T_OBJECT:
		return object_value->stringify(prettyfy, tabs + 1);
	case JSON_VALUE_TYPE::JSON_T_ARRAY:
		return array_value->stringify(prettyfy, tabs + 1);
	}
	return std::string("null");
}
