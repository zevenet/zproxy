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

#include <string>
namespace json
{
// JSON Keys

	struct JSON_OP_RESULT
	{
		static const std::string OK;
		static const std::string ERROR;
		static const std::string WRONG_JSON_FORMAT;
		static const std::string EMPTY_OBJECT;
		static const std::string NONE;
	};

	struct JSON_KEYS
	{
		static const std::string LISTENER;
		static const std::string SERVICE;
		static const std::string BACKEND;
		static const std::string SESSION;

		static const std::string SERVICES;
		static const std::string BACKENDS;
		static const std::string SESSIONS;

		static const std::string ID;
		static const std::string NAME;
		static const std::string UNKNOWN;

		static const std::string STATUS;
		static const std::string STATUS_ACTIVE;
		static const std::string STATUS_UP;
		static const std::string STATUS_DOWN;
		static const std::string STATUS_DISABLED;

		static const std::string ADDRESS;
		static const std::string PORT;
		static const std::string HTTPS;
		static const std::string BACKEND_ID;
		static const std::string FROM;
		static const std::string TO;
		static const std::string LAST_SEEN_TS;
		static const std::string CONNECTIONS;
		static const std::string PENDING_CONNS;
		static const std::string RESPONSE_TIME;
		static const std::string CONNECT_TIME;
		static const std::string WEIGHT;
		static const std::string PRIORITY;
		static const std::string CONFIG;
		static const std::string TYPE;
#if WAF_ENABLED
		static const std::string WAF;
#endif

		static const std::string RESULT;
#if CACHE_ENABLED
		static const std::string CACHE;
		static const std::string CACHE_MISS;
		static const std::string CACHE_HIT;
		static const std::string CACHE_STALE;
		static const std::string CACHE_RAM;
		static const std::string CACHE_RAM_USAGE;
		static const std::string CACHE_RAM_PATH;
		static const std::string CACHE_DISK;
		static const std::string CACHE_DISK_PATH;
		static const std::string CACHE_DISK_USAGE;
		static const std::string CACHE_AVOIDED;
		static const std::string CACHE_CONTENT;
#endif
		static const std::string DEBUG;
		static const std::string DEBUG1;
		static const std::string DEBUG2;
		static const std::string DEBUG3;
		static const std::string DEBUG4;
		static const std::string DEBUG5;
	};

	enum class JSON_VALUE_TYPE
	{
		JSON_T_NULL,
		JSON_T_STRING,
		JSON_T_BOOL,
		JSON_T_NUMBER,
		JSON_T_DOUBLE,
		JSON_T_OBJECT,
		JSON_T_ARRAY
	};

	class Json
	{
	      public:
		Json() = default;
		Json(Json &) = default;
		virtual ~ Json();
		int json_size;
		virtual bool isArray();
		virtual bool isObject()
		{
			return false;
		}
		virtual bool isData()
		{
			return false;
		}
		virtual bool isValue()
		{
			return false;
		}
		virtual std::string stringify(bool prettyfy =
					      false, int tabs = -1) {
			return std::string();
		}
	};

}				// namespace json
