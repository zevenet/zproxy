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
#include "../http/http_request.h"
#include <string>

namespace ctl
{

	enum class CTL_COMMAND
	{
		NONE,
		ADD,
		DELETE,
		ENABLE,
		DISABLE,
		UPDATE,
		GET,
		SUSCRIBE,
		UNSUSCRIBE,
		// process commands
		EXIT,
	};

	enum class CTL_HANDLER_TYPE
	{
		NONE,
		ALL,
		BACKEND,
		SERVICE,
		LISTENER_MANAGER,
		SERVICE_MANAGER,
		GLOBAL_CONF,
		STREAM_MANAGER,
		ENVIORONMENT,
	};

	enum class CTL_SUBJECT
	{
		NONE,
		SESSION,
		BACKEND,
		SERVICE,
		LISTENER,
		CONFIG,
		STATUS,
		WEIGHT,
		DEBUG,
		S_BACKEND,
#if CACHE_ENABLED
		CACHE,
#endif
#if WAF_ENABLED
		RELOAD_WAF,
#endif
	};

	struct CtlTask
	{
		HttpRequest *request;
		CTL_COMMAND command = CTL_COMMAND::NONE;
		CTL_HANDLER_TYPE target = CTL_HANDLER_TYPE::NONE;
		CTL_SUBJECT subject = CTL_SUBJECT::NONE;

		int listener_id = -1;
		int service_id = -1;
		int backend_id = -1;

		  std::string target_subject_id = "";

		  std::string service_name;
		  std::string backend_name;
		  std::string data;
	};

	enum class CTL_INTERFACE_MODE
	{
		CTL_UNIX,
		CTL_AF_INET,
		CTL_NONE,
	};

}				// namespace ctl
