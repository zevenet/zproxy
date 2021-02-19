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

#include "cache_manager.h"
void CacheManager::handleResponse(HttpStream * stream, Service * service)
{
	if (!service->cache_enabled) {
		return;
	}
	if (!stream->response.hasPendingData()) {
		CacheManager::validateCacheResponse(stream->response);
		regex_t *pattern = service->http_cache->getCachePattern();
		regmatch_t matches[2];
		if (pattern != nullptr) {
			if (regexec
			    (pattern, stream->request.getUrl().data(), 1,
			     matches, 0) == 0) {
				if (stream->request.c_opt.no_store == false) {
					service->
						http_cache->handleResponse
						(stream->response,
						 stream->request);
				}
				else {
					service->http_cache->
						stats.cache_not_stored++;
				}
			}
		}
	}
	else {
		if (service->cache_enabled
		    && service->http_cache->getCacheObject(stream->request) !=
		    nullptr && !stream->request.c_opt.no_store
		    && stream->response.c_opt.cacheable) {
			service->http_cache->addData(stream->response,
						     std::
						     string_view
						     (stream->backend_connection.buffer,
						      stream->backend_connection.buffer_size),
						     stream->
						     request.getUrl());
		}
	}
}

int CacheManager::handleRequest(HttpStream * stream, Service * service,
				ListenerConfig & listener_config_)
{
	if (service->cache_enabled) {
		std::chrono::steady_clock::time_point current_time =
			std::chrono::steady_clock::now();
		std::chrono::duration < long >time_span =
			std::chrono::duration_cast < std::chrono::duration <
			long >>(current_time - stream->prev_time);
		stream->prev_time = current_time;
		stream->current_time += time_span.count();
		service->http_cache->t_stamp = stream->current_time;
		CacheManager::validateCacheRequest(stream->request);
		if (service->cache_enabled
		    && service->http_cache->
		    canBeServedFromCache(stream->request) != nullptr) {
			DEBUG_COUNTER_HIT(cache_stats__::cache_match);
			stream->response.reset_parser();
			if (service->
			    http_cache->getResponseFromCache(stream->request,
							     stream->response,
							     stream->
							     backend_connection.str_buffer)
			    == 0) {
				http_manager::validateResponse(*stream,
							       listener_config_);

				if (http::http_info::
				    http_verbs.at(std::string
						  (stream->request.method,
						   stream->request.
						   method_len)) ==
				    http::REQUEST_METHOD::HEAD) {
					// If HTTP verb is HEAD, just send headers
					stream->response.buffer_size =
						stream->response.buffer_size -
						stream->
						response.message_length;
					stream->response.message = nullptr;
					stream->response.message_length = 0;
					stream->response.message_bytes_left =
						0;
				}
				stream->client_connection.buffer_size = 0;
				stream->request.setHeaderSent(false);
				stream->backend_connection.buffer_size =
					stream->response.buffer_size;
				stream->client_connection.enableWriteEvent();
				// Return 0, we are using cache
				return 0;
			}
		}
		if (stream->request.c_opt.only_if_cached) {
			// If the directive only-if-cached is in the request and the content
			// is not cached, reply an error 504 as stated in the rfc7234
			return -1;
		}
		service->http_cache->stats.cache_miss++;
	}
	DEBUG_COUNTER_HIT(cache_stats__::cache_miss);
	stream->response.reset_parser();
	stream->response.cached = false;
	stream->response.setHeaderSent(false);
	stream->backend_connection.buffer_size = 0;
	// Return 1, we can't serve from cache
	return 1;
}

void CacheManager::validateCacheResponse(HttpResponse & response)
{
	for (auto i = 0; i != static_cast < int >(response.num_headers); i++) {
		// check header values length

		auto header = std::string_view(response.headers[i].name,
					       response.headers[i].name_len);
		auto header_value =
			std::string_view(response.headers[i].value,
					 response.headers[i].value_len);
		auto it = http::http_info::headers_names.find(header);
		if (it != http::http_info::headers_names.end()) {
			const auto header_name = it->second;
			switch (header_name) {
			case http::HTTP_HEADER_NAME::CONTENT_LENGTH:{
					response.content_length =
						static_cast <
						size_t >(std::
							 atoi(response.
							      headers[i].
							      value));
					continue;
				}
			case http::HTTP_HEADER_NAME::CACHE_CONTROL:{
					std::vector < string >
						cache_directives;
					helper::splitString(std::string
							    (header_value),
							    cache_directives,
							    ' ');
					response.cache_control = true;
					// Lets iterate over the directives array
					for (unsigned long l = 0;
					     l < cache_directives.size();
					     l++) {
						// split using = to obtain the directive value, if supported

						if (cache_directives[l].back()
						    == ',')
							cache_directives[l] =
								cache_directives
								[l].substr(0,
									   cache_directives
									   [l].length
									   ()
									   -
									   1);
						string_view
							directive
							(cache_directives
							 [l].substr(0,
								    cache_directives
								    [l].find
								    ('=')));
						string_view
							directive_value
							(cache_directives
							 [l].substr
							 (cache_directives
							  [l].find('=') + 1,
							  cache_directives
							  [l].size() - 1));

						if (http::
						    http_info::cache_control_values.count
						    (directive.data()) > 0) {
							switch (http::http_info::cache_control_values.at(directive.data())) {
							case http::CACHE_CONTROL::MAX_AGE:
								if (directive_value.size() != 0 && response.c_opt.max_age == -1)
									response.c_opt.max_age
										=
										stoi
										(directive_value.data
										 ());
								break;
							case http::CACHE_CONTROL::PUBLIC:
								response.c_opt.scope = cache_commons::CACHE_SCOPE::PUBLIC;
								break;
							case http::CACHE_CONTROL::PRIVATE:
								response.c_opt.scope = cache_commons::CACHE_SCOPE::PRIVATE;
								break;
							case http::CACHE_CONTROL::PROXY_REVALIDATE:
								response.c_opt.revalidate = true;
								break;
							case http::CACHE_CONTROL::S_MAXAGE:
								if (directive_value.size() != 0)
									response.c_opt.max_age
										=
										stoi
										(directive_value.data
										 ());
								break;
							case http::CACHE_CONTROL::NO_CACHE:
								response.c_opt.no_cache = true;
								response.c_opt.cacheable
									=
									false;
								break;
							case http::CACHE_CONTROL::NO_STORE:
								response.c_opt.cacheable = false;
								break;
							}
						}
					}
					break;
				}
			case http::HTTP_HEADER_NAME::PRAGMA:{
					if (header_value.compare("no-cache")
					    == 0) {
						response.pragma = true;
					}
					break;
				}
			case http::HTTP_HEADER_NAME::ETAG:
				response.etag = header_value;
				break;
			case http::HTTP_HEADER_NAME::EXPIRES:
				response.expires =
					time_helper::strToTime(std::string
							       (header_value));
				break;
			case http::HTTP_HEADER_NAME::DATE:
				response.date =
					time_helper::strToTime(std::string
							       (header_value));
				break;
			case http::HTTP_HEADER_NAME::LAST_MODIFIED:
				response.last_mod =
					time_helper::strToTime(std::string
							       (header_value));
				break;
			case http::HTTP_HEADER_NAME::TRANSFER_ENCODING:
				response.transfer_encoding_header = true;
				switch (header_value[0]) {
				case 'c':{
						if (header_value[1] == 'h') {	// no content-length
							response.transfer_encoding_type
								=
								http::TRANSFER_ENCODING_TYPE::CHUNKED;
							response.chunked_status
								=
								http::CHUNKED_STATUS::CHUNKED_ENABLED;
						}
						else if (header_value[2] ==
							 'o') {
							response.transfer_encoding_type
								=
								http::TRANSFER_ENCODING_TYPE::COMPRESS;
						}
						break;
					}
				case 'd':	// deflate
					response.transfer_encoding_type =
						http::
						TRANSFER_ENCODING_TYPE::DEFLATE;
					break;
				case 'g':	// gzip
					response.transfer_encoding_type =
						http::
						TRANSFER_ENCODING_TYPE::GZIP;
					break;
				case 'i':	// identity
					response.transfer_encoding_type =
						http::
						TRANSFER_ENCODING_TYPE::IDENTITY;
					break;
				}
				break;
			default:
				continue;
			}
		}
	}
	return;
}

void CacheManager::validateCacheRequest(HttpRequest & request)
{
	// Check for correct headers
	for (auto i = 0; i != static_cast < int >(request.num_headers); i++) {
		// check header values length
		auto header = std::string_view(request.headers[i].name,
					       request.headers[i].name_len);
		auto header_value = std::string_view(request.headers[i].value,
						     request.headers[i].
						     value_len);

		auto it = http::http_info::headers_names.find(header);
		if (it != http::http_info::headers_names.end()) {
			auto header_name = it->second;
			switch (header_name) {
			case http::HTTP_HEADER_NAME::TRANSFER_ENCODING:
				// TODO
				break;
			case http::HTTP_HEADER_NAME::CACHE_CONTROL:{
					std::vector < string >
						cache_directives;
					helper::splitString(std::string
							    (header_value),
							    cache_directives,
							    ' ');
					request.cache_control = true;

					// Lets iterate over the directives array
					for (unsigned long l = 0;
					     l < cache_directives.size();
					     l++) {
						// split using = to obtain the directive value, if supported
						if (cache_directives[l].back()
						    == ',')
							cache_directives[l] =
								cache_directives
								[l].substr(0,
									   cache_directives
									   [l].length
									   ()
									   -
									   1);
						string_view
							directive
							(cache_directives
							 [l].substr(0,
								    cache_directives
								    [l].find
								    ('=')));
						string_view
							directive_value
							(cache_directives
							 [l].substr
							 (cache_directives
							  [l].find('=') + 1,
							  cache_directives
							  [l].size() - 1));

						// To separe directive from the token
						if (http::
						    http_info::cache_control_values.count
						    (directive.data()) > 0) {
							switch (http::http_info::cache_control_values.at(directive.data())) {
							case http::CACHE_CONTROL::MAX_AGE:
								if (directive_value.size() != 0)
									request.c_opt.max_age = stoi(directive_value.data());
								break;
							case http::CACHE_CONTROL::MAX_STALE:
								if (directive_value.size() != 0)
									request.c_opt.max_stale = stoi(directive_value.data());
								break;
							case http::CACHE_CONTROL::MIN_FRESH:
								if (directive_value.size() != 0)
									request.c_opt.min_fresh = stoi(directive_value.data());
								break;
							case http::CACHE_CONTROL::NO_CACHE:
								request.c_opt.no_cache = true;
								break;
							case http::CACHE_CONTROL::NO_STORE:
								request.c_opt.no_store = true;
								break;
							case http::CACHE_CONTROL::NO_TRANSFORM:
								request.c_opt.transform = false;
								break;
							case http::CACHE_CONTROL::ONLY_IF_CACHED:
								request.c_opt.only_if_cached = true;
								break;
							default:
								zcu_log_print(LOG_ERR, "Malformed cache-control, found response directive %s in the request", directive.data());
								break;
							}
						}
						else {
							zcu_log_print
								(LOG_ERR,
								 "Unrecognized directive %s in the request",
								 directive.data
								 ());
						}
					}
					break;
				}
			case http::HTTP_HEADER_NAME::AGE:
				break;
			case http::HTTP_HEADER_NAME::PRAGMA:{
					if (header_value.compare("no-cache")
					    == 0) {
						request.pragma = true;
					}
					break;
				}
			default:
				continue;
			}
		}
	}

	return;
}

void CacheManager::handleStreamClose(HttpStream * stream)
{
	if (stream->response.c_object != nullptr
	    && stream->response.c_object->dirty) {
		auto service =
			static_cast <
			Service * >(stream->request.getService());
		if (service != nullptr && service->cache_enabled) {
			service->http_cache->deleteEntry(stream->request);
		}
	}
}
