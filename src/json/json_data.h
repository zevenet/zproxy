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

#include "json.h"
#include "json_data_value.h"
#include <string>

namespace json
{
class JsonData : Json {
	std::string name_;
	JsonDataValue *data;

    public:
	JsonData(const JsonData &other);
	~JsonData();
	JsonData(const JsonData &&other);
	JsonData(const char *name, const char *value);
	JsonData(const char *name, const JsonDataValue &value);
	;
	bool isData() override;
	std::string stringify(bool prettyfy = false, int tabs = -1) override;
};

} // namespace json
