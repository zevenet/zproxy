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

#include "http_parser.h"

#ifdef CACHE_ENABLED
#include <map>
#include "../cache/cache_commons.h"

struct CacheRequestOptions
{
	bool no_store = false;
	bool no_cache = false;
	bool only_if_cached = false;
	bool transform = true;
	int max_age = -1;
	int max_stale = -1;
	int min_fresh = -1;
};

struct CacheResponseOptions
{
	bool no_cache = false;
	bool transform = true;
	bool cacheable = true;	// Set by the request with no-store
	bool revalidate = false;
	int max_age = -1;
	  cache_commons::CACHE_SCOPE scope;
};
#endif
class HttpRequest:public http_parser::HttpData
{
  /** Service that request was generated for*/
	void *request_service
	{
	nullptr};		// fixme; hack to avoid cyclic dependency,
	// //TODO:: remove
      public:
	bool add_destination_header
	{
	false};
	bool upgrade_header
	{
	false};
	bool connection_header_upgrade
	{
	false};
	bool accept_encoding_header
	{
	false};
	bool host_header_found
	{
	false};
	std::string virtual_host;
	std::string_view x_forwarded_for_string;
#ifdef CACHE_ENABLED
	struct CacheRequestOptions c_opt;
#endif
	void setRequestMethod();
	http::REQUEST_METHOD getRequestMethod();
	void printRequestMethod();

      public:
	std::string_view getMethod();
	std::string_view getRequestLine();
	std::string getUrl();
	void setService( /*Service */ void *service);
	void *getService() const;
};

class HttpResponse:
public http_parser::HttpData {
      public:
#ifdef CACHE_ENABLED
	bool transfer_encoding_header;
	bool cached = false;
	struct CacheResponseOptions c_opt;
	cache_commons::CacheObject * c_object = nullptr;
	std::string etag;
	// Time specific headers
	long int date = -1;
	long int last_mod = -1;
	long int expires = -1;
	bool isCached();
	std::string str_buffer;
#endif
};
