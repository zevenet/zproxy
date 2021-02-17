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
#include "http_request.h"
#include "../../zcutils/zcutils.h"

void
HttpRequest::setRequestMethod()
{
	auto sv = std::string_view(method, method_len);
	//    auto sv = std::string(method, method_len);
	auto it = http::http_info::http_verbs.find(sv);
	if (it != http::http_info::http_verbs.end())
		request_method = it->second;
}

http::REQUEST_METHOD HttpRequest::getRequestMethod()
{
	setRequestMethod();
	return request_method;
}

void
HttpRequest::printRequestMethod()
{
	zcutils_log_print(LOG_DEBUG, "Request method: %s",
			  http::http_info::http_verb_strings.
			  at(request_method).c_str());
}

std::string_view HttpRequest::getMethod()
{
	return method != nullptr ? std::string_view(method, method_len)
		: std::string_view();
}

std::string_view HttpRequest::getRequestLine()
{
	return std::string_view(http_message, http_message_length);
}

std::string HttpRequest::getUrl()
{
	return path != nullptr ? std::string(path,
					     path_length) : std::string();
}

void
HttpRequest::setService(void *service)
{
	this->request_service = service;
}

void *
HttpRequest::getService() const
{
	return request_service;
}

#ifdef CACHE_ENABLED
bool
HttpResponse::isCached()
{
	return this->cached;
}
#endif
