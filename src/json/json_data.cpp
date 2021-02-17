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

#include "json_data.h"

json::JsonData::JsonData(const char *name, const char *value)
	:
name_(std::string(name))
{
	data = new JsonDataValue(value);
}

json::JsonData::JsonData(const char *name, const json::JsonDataValue & value)
	:
name_(std::string(name)),
data(new JsonDataValue(value))
{
}

json::JsonData::JsonData(const json::JsonData & other)
	:
name_(other.name_),
data(new JsonDataValue(other.data))
{
}

json::JsonData::JsonData(const json::JsonData && other)
	:
name_(other.name_),
data(new JsonDataValue(other.data))
{
}

bool
json::JsonData::isData()
{
	return true;
}

std::string json::JsonData::stringify(bool prettyfy, int tabs)
{
	std::string res = "";
	for (auto num = tabs; num > 0 && prettyfy; num--)
		res += '\t';
	res = "\"" + name_ + "\" : " + data->stringify(prettyfy, tabs + 1);
	if (prettyfy)
		res += "\n";
	return res;
}

json::JsonData::~JsonData()
{
	delete
		data;
}
