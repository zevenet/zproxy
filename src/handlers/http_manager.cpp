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

#include "http_manager.h"
#include "../config/regex_manager.h"
#include "../../zcutils/zcu_network.h"
#include "../../zcutils/zcutils.h"

ssize_t http_manager::handleChunkedData(Connection &connection,
					http_parser::HttpData &http_data)
{
	auto last_chunk_size = http_data.chunk_size_left;
	if (last_chunk_size >= connection.buffer_size) {
		http_data.chunk_size_left -= connection.buffer_size;
	} else {
		size_t data_offset = last_chunk_size;
		size_t new_chunk_left = 0;
		auto chunk_size = http_manager::getLastChunkSize(
			connection.buffer + last_chunk_size,
			connection.buffer_size - http_data.chunk_size_left,
			data_offset, new_chunk_left, http_data.content_length);
		const char *status = chunk_size < 0  ? "*" :
				     chunk_size == 0 ? "/" :
							     "";
		zcu_log_print(
			LOG_DEBUG,
			"%s():%d: [%s] buffer size: %6lu chunk left: %8d => Chunk size: %8d "
			"Data offset: %6lu Content_length: %8d  next chunk left %8d",
			__FUNCTION__, __LINE__, status, connection.buffer_size,
			last_chunk_size, chunk_size, data_offset,
			http_data.content_length, new_chunk_left);
		if (chunk_size < 0) {
			//          const char *new_chunk_buff = connection.buffer
			//+ http_data.chunk_size_left - 5;
			/* here we have a tricky situation, we have received the last pendind part
			 * of last chunk, bute not enough data to process next chunk size */
			//          http_data.chunk_buffer_size_offset =
			// connection.buffer_size -
			// http_data.chunk_size_left;
			return -1;
		} else if (chunk_size == 0) {
			http_data.chunk_size_left = 0;
			http_data.chunked_status =
				CHUNKED_STATUS::CHUNKED_LAST_CHUNK;
#if DEBUG_ZCU_LOG
			zcu_log_print(LOG_DEBUG, "%s():%d: last chunk",
				      __FUNCTION__, __LINE__);
#endif
			return 0;
		} else {
			http_data.chunk_size_left = new_chunk_left;
		}
		return static_cast<ssize_t>(new_chunk_left);
	}
	return static_cast<ssize_t>(http_data.chunk_size_left);
}

ssize_t http_manager::getChunkSize(const std::string &data, size_t data_size,
				   int &chunk_size_line_len)
{
	auto pos = data.find(http::CRLF);
	if (pos != std::string::npos && pos < data_size) {
		chunk_size_line_len = static_cast<int>(pos) + http::CRLF_LEN;
		auto hex = data.substr(0, pos);
		char *error;
		auto chunk_length = ::strtol(hex.data(), &error, 16);
		if (*error != 0) {
			zcu_log_print(
				LOG_NOTICE,
				"strtol() failed: Data size: %d  Buffer: %.*s",
				data_size, 10, data.data());
			return -1;
		} else {
#if DEBUG_ZCU_LOG
			zcu_log_print(LOG_DEBUG, "CHUNK found size %s => %d ",
				      hex.data(), chunk_length);
#endif
			return static_cast<ssize_t>(chunk_length);
		}
	}
	//  zcu_log_print(LOG_NOTICE, "Chunk not found, need more data: Buff size: %d
	//  Buff %.*s ",data_size, 5, data.data());
	return -1;
}

ssize_t http_manager::getLastChunkSize(const char *data, size_t data_size,
				       size_t &data_offset,
				       size_t &chunk_size_bytes_left,
				       size_t &content_length)
{
	int chunk_size_len = 0;
	auto chunk_size = getChunkSize(data, data_size, chunk_size_len);
	if (chunk_size > 0) {
		content_length += static_cast<size_t>(chunk_size);
		auto offset = chunk_size + chunk_size_len + http::CRLF_LEN;
		if (data_size >
		    (static_cast<size_t>(offset) + http::CRLF_LEN)) {
			data_offset += static_cast<size_t>(offset);
			auto data_ptr = data + offset;
			return getLastChunkSize(
				data_ptr,
				data_size - static_cast<size_t>(offset),
				data_offset, chunk_size_bytes_left,
				content_length);
		} else {
			data_offset += data_size;
			chunk_size_bytes_left =
				static_cast<size_t>(offset) - data_size;
			return chunk_size;
		}
	} else if (chunk_size == 0) {
		return 0;
	} else {
		// an error has ocurred;
		return chunk_size;
	}
}

void http_manager::setBackendCookie(Service *service, HttpStream *stream)
{
	if (!service->becookie.empty() &&
	    !stream->backend_connection.getBackend()->bekey.empty()) {
		//    std::string set_cookie_header =
		//        service->becookie + "=" +
		//        stream->backend_connection.getBackend()->bekey;
		//    if (!service->becdomain.empty())
		//      set_cookie_header += "; Domain=" + service->becdomain;
		//    if (!service->becpath.empty())
		//      set_cookie_header += "; Path=" + service->becpath;
		//    time_t time = std::time(nullptr);
		//    if(service->becage != 0) {
		//      if (service->becage > 0) {
		//        time += service->becage;
		//      } else {
		//        time += service->ttl;
		//      }
		//      char time_string[ZCU_DEF_BUFFER_SIZE];
		//      strftime(time_string, ZCU_DEF_BUFFER_SIZE - 1, "%a, %e-%b-%Y %H:%M:%S GMT",
		//               gmtime(&time));
		//      set_cookie_header += "; expires=";
		//      set_cookie_header += time_string;
		//    }
		service->updateSession(
			stream->client_connection, stream->request,
			stream->backend_connection.getBackend()->bekey,
			*stream->backend_connection.getBackend());
		stream->response.addHeader(
			http::HTTP_HEADER_NAME::SET_COOKIE,
			stream->backend_connection.getBackend()->bekey);
	}
}

void rewriteUrl(HttpStream &stream, Service *service)
{
	char buf[ZCU_DEF_BUFFER_SIZE];
	HttpRequest &request = stream.request;
	bool rewr = (service->rewr_loc_path == 1 ||
		     service->rewr_loc_path == -1 &&
			     stream.service_manager->listener_config_
					     ->rewr_loc_path == 1);
	int offset = 0, ori_size = ZCU_DEF_BUFFER_SIZE;
	if (service->rewr_url == nullptr)
		return;

	std::string path_orig = request.path;

	int flag = 0;
	for (auto m = service->rewr_url; m; m = m->next) {
		offset = zcu_str_replace_regexp(
			buf, request.path.data(), request.path.length(),
			&m->match, const_cast<char *>(m->replace.c_str()));
		if (offset != -1) {
			request.path = buf;
			zcu_log_print(LOG_DEBUG,
				      "URL rewrited \"%s\" -> \"%s\"",
				      path_orig.data(), request.path.data());

			if (ori_size > request.path.length() - offset) {
				ori_size = request.path.length() - offset;
			}

			if (m->last)
				break;
		}
	}

	if (ori_size != ZCU_DEF_BUFFER_SIZE && rewr) {
		stream.rewr_loc_str_repl = std::string(
			request.path.data(), request.path.length() - ori_size);
		stream.rewr_loc_str_ori = std::string(
			path_orig.data(), path_orig.length() - ori_size);
		zcu_log_print(LOG_DEBUG, "URL for reverse Location\"%s\"",
			      stream.rewr_loc_str_repl.data());
	}

	request.http_message_str =
		std::string_view(request.method, request.method_len);
	request.http_message_str +=
		" " + request.path + " HTTP/" + request.getHttpVersion();
}

void http_manager::replaceHeaderHttp(http_parser::HttpData *http,
				     phr_header *header,
				     ReplaceHeader *replace_header,
				     regmatch_t *eol)
{
	char buf[ZCU_DEF_BUFFER_SIZE];

	if (header->header_off)
		return;

	for (auto m = replace_header; m; m = m->next) {
		eol->rm_eo = header->line_size;
		if (::regexec(&m->name, header->name, 1, eol, REG_STARTEND) ==
		    0) {
			if (zcu_str_replace_regexp(
				    buf, header->value, header->value_len,
				    &m->match,
				    const_cast<char *>(m->replace.c_str())) !=
			    -1) {
				auto new_header_value = std::string(
					header->name, header->name_len);
				new_header_value += ": ";
				new_header_value += buf;
				http->addHeader(new_header_value);
				header->header_off = true;
				// Maybe modify for doing several sustitutions over the header
				break;
			}
		}
	}
}

validation::REQUEST_RESULT http_manager::validateRequest(HttpStream &stream)
{
	char buf[ZCU_DEF_BUFFER_SIZE];
	std::string header, header_value;
	auto &listener_config_ = *stream.service_manager->listener_config_;
	auto service = static_cast<Service *>(stream.request.getService());
	HttpRequest &request = stream.request;
	MATCHER *m = nullptr;
	regmatch_t eol{ 0, static_cast<regoff_t>(
				   request.http_message_str.length()) };
	auto res = ::regexec(&listener_config_.verb,
			     request.http_message_str.data(),
			     1, // include validation data package
			     &eol, REG_STARTEND);
	if (UNLIKELY(res != 0)) {
		// TODO:: check RPC
		/*
		 * if(!strncasecmp(request + matches[1].rm_so, "RPC_IN_DATA",
		 matches[1].rm_eo - matches[1].rm_so)) is_rpc = 1; else
		 if(!strncasecmp(request + matches[1].rm_so, "RPC_OUT_DATA",
		 matches[1].rm_eo - matches[1].rm_so)) is_rpc = 0;
		 *
		 */
		return validation::REQUEST_RESULT::METHOD_NOT_ALLOWED;
	} else {
		request.setRequestMethod();
	}

	// URL
	if (request.path.find("%00") != std::string::npos) {
		return validation::REQUEST_RESULT::URL_CONTAIN_NULL;
	}
	eol.rm_so = 0;
	eol.rm_eo = request.path.length();
	if (listener_config_.has_pat &&
	    regexec(&listener_config_.url_pat, request.path.data(), 1, &eol,
		    REG_STARTEND)) {
		return validation::REQUEST_RESULT::BAD_URL;
	}

	// Rewrite URL
	rewriteUrl(stream, service);

	// Check request size .
	if (UNLIKELY(listener_config_.max_req > 0 &&
		     request.headers_length >
			     static_cast<size_t>(listener_config_.max_req) &&
		     request.request_method !=
			     http::REQUEST_METHOD::RPC_IN_DATA &&
		     request.request_method !=
			     http::REQUEST_METHOD::RPC_OUT_DATA)) {
		return validation::REQUEST_RESULT::REQUEST_TOO_LARGE;
	}
	bool connection_close_pending = false;

	// Check for correct headers
	for (size_t i = 0; i != request.num_headers; i++) {
#if DEBUG_ZCU_LOG
		zcu_log_print(LOG_DEBUG, "%s():%d: %.*s", __FUNCTION__,
			      __LINE__,
			      request.headers[i].name_len +
				      request.headers[i].value_len + 2,
			      request.headers[i].name);
#endif

		header = std::string_view(request.headers[i].name,
					  request.headers[i].name_len);
		header_value = std::string_view(request.headers[i].value,
						request.headers[i].value_len);

		/* maybe header to be removed */
		eol.rm_so = 0;
		eol.rm_eo = request.headers[i].line_size;
		if (service->service_config.head_off_req != nullptr) {
			m = service->service_config.head_off_req;
		} else if (listener_config_.head_off_req != nullptr) {
			m = listener_config_.head_off_req;
		}
		for (; m; m = m->next) {
			if (::regexec(&m->pat, request.headers[i].name, 1, &eol,
				      REG_STARTEND) == 0) {
				request.headers[i].header_off = true;
				break;
			}
		}

		// check for header to be replaced in request
		replaceHeaderHttp(
			&request, &request.headers[i],
			service->service_config.replace_header_request, &eol);
		replaceHeaderHttp(&request, &request.headers[i],
				  listener_config_.replace_header_request,
				  &eol);

		// check header values length
		if (request.headers[i].value_len > MAX_HEADER_VALUE_SIZE)
			return http::validation::REQUEST_RESULT::REQUEST_TOO_LARGE;

		auto it = http::http_info::headers_names.find(header);
		if (it != http::http_info::headers_names.end()) {
			auto header_name = it->second;
			switch (header_name) {
			case http::HTTP_HEADER_NAME::DESTINATION:
				if (listener_config_.rewr_dest != 0) {
					request.headers[i].header_off = true;
					request.add_destination_header = true;
				}
				break;
			case http::HTTP_HEADER_NAME::UPGRADE:
				request.upgrade_header = true;

				break;
			case http::HTTP_HEADER_NAME::CONNECTION: {
				if (http_info::connection_values.count(
					    std::string(header_value)) > 0 &&
				    http_info::connection_values.at(
					    std::string(header_value)) ==
					    CONNECTION_VALUES::UPGRADE)
					request.connection_header_upgrade =
						true;
				else if (header_value.find("close") !=
					 std::string::npos) {
					connection_close_pending = true;
				}
				break;
			}
			case http::HTTP_HEADER_NAME::ACCEPT_ENCODING:
				request.accept_encoding_header = true;
				//          request.headers[i].header_off = true;
				break;
			case http::HTTP_HEADER_NAME::TRANSFER_ENCODING:
				//   if (listener_config_.ignore100continue)
				//   request.headers[i].header_off = true;
				switch (header_value[0]) {
				case 'c': {
					if (header_value[1] ==
					    'h') { // no content-length
						request.transfer_encoding_type =
							TRANSFER_ENCODING_TYPE::
								CHUNKED;
						request.chunked_status =
							http::CHUNKED_STATUS::
								CHUNKED_ENABLED;
#ifdef CACHE_ENABLED
						if (request.message_length >
						    0) {
							size_t data_offset = 0;
							size_t new_chunk_left =
								0;
							auto chunk_size = http_manager::getLastChunkSize(
								request.message,
								request.message_length,
								data_offset,
								new_chunk_left,
								request.content_length);
#if DEBUG_ZCU_LOG
							zcu_log_print(
								LOG_DEBUG,
								"%s():%d: >>>> Chunk size %d left %d ",
								__FUNCTION__,
								__LINE__,
								chunk_size,
								new_chunk_left);
#endif
							request.content_length +=
								static_cast<
									size_t>(
									chunk_size);
							if (chunk_size == 0) {
#if DEBUG_ZCU_LOG
								zcu_log_print(
									LOG_DEBUG,
									"%s():%d: set last chunk",
									__FUNCTION__,
									__LINE__);
#endif
								request.chunk_size_left =
									0;
								request.chunked_status =
									CHUNKED_STATUS::
										CHUNKED_LAST_CHUNK;
							} else {
								request.chunk_size_left =
									new_chunk_left;
							}
						}
#endif
					} else if (header_value[2] == 'o') {
						request.transfer_encoding_type =
							TRANSFER_ENCODING_TYPE::
								COMPRESS;
					}
					break;
				}
				case 'd': // deflate
					request.transfer_encoding_type =
						TRANSFER_ENCODING_TYPE::DEFLATE;
					break;
				case 'g': // gzip
					request.transfer_encoding_type =
						TRANSFER_ENCODING_TYPE::GZIP;
					break;
				case 'i': // identity
					request.transfer_encoding_type =
						TRANSFER_ENCODING_TYPE::IDENTITY;
					break;
				}
				break;
			case http::HTTP_HEADER_NAME::CONTENT_LENGTH: {
				request.content_length = static_cast<size_t>(
					std::atoi(header_value.data()));
				continue;
			}
			case http::HTTP_HEADER_NAME::HOST: {
				stream.request.virtual_host = header_value;
				request.host_header_found =
					listener_config_.rewr_host == 0;
				// it could be disabled in the replaceheader directive
				if (!request.headers[i].header_off)
					request.headers[i].header_off =
						listener_config_.rewr_host == 1;
				continue;
			}
			case http::HTTP_HEADER_NAME::EXPECT: {
				if (header_value == "100-continue") {
					zcu_log_print(
						LOG_DEBUG,
						"%s():%d: client Expects 100 continue",
						__FUNCTION__, __LINE__);
				}
				request.headers[i].header_off =
					listener_config_.ignore100continue;
				break;
			}
			case http::HTTP_HEADER_NAME::X_FORWARDED_FOR: {
				request.x_forwarded_for_string = header_value;
				request.headers[i].header_off = true;
				break;
			}
			default:
				continue;
			}
		}
	}
	if (request.content_length > 0 &&
	    (request.content_length - request.message_length) > 0) {
		request.message_bytes_left =
			request.content_length - request.message_length;
	}
	if (connection_close_pending && request.content_length == 0 &&
	    request.chunked_status == http::CHUNKED_STATUS::CHUNKED_DISABLED) {
		//we have unknown amount of body data pending, wait until connection is closed
		//FIXME:: As workaround we use chunked
		request.transfer_encoding_type =
			TRANSFER_ENCODING_TYPE::CHUNKED;
		request.chunked_status = http::CHUNKED_STATUS::CHUNKED_ENABLED;
	}
	return validation::REQUEST_RESULT::OK;
}

int rewriteHeaderLocation(phr_header *header,
			  http::HTTP_HEADER_NAME header_name,
			  HttpStream &stream, ListenerConfig *listener_config_,
			  Service *service)
{
	auto header_value = std::string_view(header->value, header->value_len);
	int rewr_loc = (service->rewr_loc != -1) ? service->rewr_loc :
							 listener_config_->rewr_loc;
	int rewr_loc_path = (service->rewr_loc_path != -1) ?
					  service->rewr_loc_path :
					  listener_config_->rewr_loc_path;

	if (stream.rewr_loc_str_repl == "")
		rewr_loc_path = 0;

	if (rewr_loc == 0 && rewr_loc_path == 0)
		return 0;

	auto backend_addr =
		stream.backend_connection.getBackend()->address_info;
	if (backend_addr->ai_family != AF_INET &&
	    backend_addr->ai_family != AF_INET6)
		return 0;
	// Rewrite location
	std::string location_header_value(header->value, header->value_len);
	regmatch_t matches[4];
	//std::memset(matches,0,4);
	matches[0].rm_so = 0;
	matches[0].rm_eo = header->value_len;
	if (regexec(&regex_set::LOCATION, header->value, 4, matches,
		    REG_STARTEND)) {
		return 0;
	}

	std::string proto(
		location_header_value.data() + matches[1].rm_so,
		static_cast<size_t>(matches[1].rm_eo - matches[1].rm_so));
	std::string host(
		location_header_value.data() + matches[2].rm_so,
		static_cast<size_t>(matches[2].rm_eo - matches[2].rm_so));

	//          if (location_header_value[matches[3].rm_so] == '/') {
	//            matches[3].rm_so++;
	//          }
	std::string path(
		location_header_value.data() + matches[3].rm_so,
		static_cast<size_t>(matches[3].rm_eo - matches[3].rm_so));
	std::string header_value_ = "";

	if (rewr_loc != 0) {
		int port = 0;
		std::string host_addr = host;
		auto port_it = host.find(':');
		if (port_it != std::string::npos) {
			port = std::stoul(
				host.substr(port_it + 1, host.length()));
			host_addr = host.substr(0, port_it);
		} else {
			port = proto == "https" ? 443 : 80;
		}
		auto in_addr = zcu_net_get_address(host_addr, port);
		if (in_addr == nullptr) {
			zcu_log_print(LOG_WARNING, "Couldn't get host ip");
		} else {
			/* rewrite location if it points to the backend */
			if (zcu_net_equal_sockaddr(in_addr.get(),
						   backend_addr)) {
				header_value_ = proto;

				/* or the listener address with different port */
			} else if (rewr_loc == 1 &&
				   (listener_config_->port != port ||
				    ((listener_config_->ctx == nullptr) ?
						   "http" :
						   "https") != proto) &&
				   (zcu_net_equal_sockaddr(
					    in_addr.get(),
					    stream.service_manager
						    ->listener_config_
						    ->addr_info,
					    false) ||
				    host == stream.request.virtual_host)) {
				header_value_ =
					(proto == "https") ? "http" : "https";
			}

			if (header_value_ != "") {
				header_value_ += "://";
				header_value_ += stream.request.virtual_host;
				if ((stream.service_manager->listener_config_
						     ->ctx != nullptr &&
				     listener_config_->port != 443) ||
				    (listener_config_->port != 80)) {
					if (header_value.find(':') ==
					    std::string::npos) {
						header_value_ += ":";
						header_value_ += std::to_string(
							listener_config_->port);
					}
				}
			}
		}
	}

	if (header_value_ == "")
		header_value_ = proto + "://" + host;

	if (stream.rewr_loc_str_repl != "" || stream.rewr_loc_str_ori != "") {
		// the string to remove must be at the begining
		if (path.find(stream.rewr_loc_str_repl.data()) == 0)
			path.replace(0, stream.rewr_loc_str_repl.length(),
				     stream.rewr_loc_str_ori);
	}

	header_value_ += path;
	stream.response.addHeader(header_name, header_value_);
	header->header_off = true;
	return 1;
}

validation::REQUEST_RESULT http_manager::validateResponse(HttpStream &stream)
{
	auto &listener_config_ = *stream.service_manager->listener_config_;
	auto service = static_cast<Service *>(stream.request.getService());
	HttpResponse &response = stream.response;
	char buf[ZCU_DEF_BUFFER_SIZE];
	MATCHER *m = nullptr;

	/* If the response is 100 continue we need to enable chunked transfer. */
	if (response.http_status_code < 200) {
		//    stream.response.chunked_status =
		//    http::CHUNKED_STATUS::CHUNKED_ENABLED; zcu_log_print(LOG_DEBUG,
		//    "Chunked transfer enabled");
		return validation::REQUEST_RESULT::OK;
	}

#ifdef CACHE_ENABLED
	stream.request.c_opt.no_store ? response.c_opt.cacheable = false :
					      response.c_opt.cacheable = true;
#endif
	bool connection_close_pending = false;
	for (size_t i = 0; i != response.num_headers; i++) {
#if DEBUG_ZCU_LOG
		zcu_log_print(LOG_DEBUG, "%s():%d: %.*s", __FUNCTION__,
			      __LINE__,
			      response.headers[i].name_len +
				      response.headers[i].value_len + 2,
			      response.headers[i].name);
#endif

		/* maybe header to be removed from response */
		regmatch_t eol{ 0, static_cast<regoff_t>(
					   response.headers[i].line_size) };
		if (service->service_config.head_off_resp != nullptr) {
			m = service->service_config.head_off_resp;
		} else if (listener_config_.head_off_resp != nullptr) {
			m = listener_config_.head_off_resp;
		}
		for (; m; m = m->next) {
			if (::regexec(&m->pat, response.headers[i].name, 1,
				      &eol, REG_STARTEND) == 0) {
				response.headers[i].header_off = true;
				break;
			}
		}

		// check for header to be replaced in response
		replaceHeaderHttp(
			&response, &response.headers[i],
			service->service_config.replace_header_response, &eol);
		replaceHeaderHttp(&response, &response.headers[i],
				  listener_config_.replace_header_response,
				  &eol);

		if (response.headers[i].header_off)
			continue;

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
			case http::HTTP_HEADER_NAME::CONNECTION: {
				if (header_value.find("close") !=
				    std::string::npos) {
					connection_close_pending = true;
				}
				continue;
			}
			case http::HTTP_HEADER_NAME::CONTENT_LENGTH: {
				stream.response.content_length =
					static_cast<size_t>(
						strtol(header_value.data(),
						       nullptr, 10));
				continue;
			}
			case http::HTTP_HEADER_NAME::CONTENT_LOCATION:
			case http::HTTP_HEADER_NAME::LOCATION: {
				rewriteHeaderLocation(&response.headers[i],
						      header_name, stream,
						      &listener_config_,
						      service);
				break;
			}
			case http::HTTP_HEADER_NAME::STRICT_TRANSPORT_SECURITY:
				if (static_cast<Service *>(
					    stream.request.getService())
					    ->service_config.sts > 0)
					response.headers[i].header_off = true;
				break;
			case http::HTTP_HEADER_NAME::TRANSFER_ENCODING:
				switch (header_value[0]) {
				case 'c': {
					if (header_value[1] ==
					    'h') { // no content-length
						response.transfer_encoding_type =
							TRANSFER_ENCODING_TYPE::
								CHUNKED;
						response.chunked_status =
							http::CHUNKED_STATUS::
								CHUNKED_ENABLED;
#ifdef CACHE_ENABLED
						if (stream.response
							    .message_length >
						    0) {
							size_t data_offset = 0;
							size_t new_chunk_left =
								0;
							auto chunk_size = http_manager::getLastChunkSize(
								stream.response
									.message,
								stream.response
									.message_length,
								data_offset,
								new_chunk_left,
								response.content_length);
#if DEBUG_ZCU_LOG
							zcu_log_print(
								LOG_DEBUG,
								"%s():%d: >>>> Chunk size %d left %d",
								__FUNCTION__,
								__LINE__,
								chunk_size,
								new_chunk_left);
#endif
							stream.response
								.content_length +=
								static_cast<
									size_t>(
									chunk_size);
							if (chunk_size == 0) {
#if DEBUG_ZCU_LOG
								zcu_log_print(
									LOG_DEBUG,
									"%s():%d: set last chunk",
									__FUNCTION__,
									__LINE__);
#endif
								stream.response
									.chunk_size_left =
									0;
								stream.response
									.chunked_status =
									CHUNKED_STATUS::
										CHUNKED_LAST_CHUNK;
							} else {
								stream.response
									.chunk_size_left =
									new_chunk_left;
							}
						}
#endif
					} else if (header_value[2] == 'o') {
						response.transfer_encoding_type =
							TRANSFER_ENCODING_TYPE::
								COMPRESS;
					}
					break;
				}
				case 'd': // deflate
					response.transfer_encoding_type =
						TRANSFER_ENCODING_TYPE::DEFLATE;
					break;
				case 'g': // gzip
					response.transfer_encoding_type =
						TRANSFER_ENCODING_TYPE::GZIP;
					break;
				case 'i': // identity
					response.transfer_encoding_type =
						TRANSFER_ENCODING_TYPE::IDENTITY;
					break;
				}
				break;
			case http::HTTP_HEADER_NAME::SET_COOKIE: {
				if (service->session_type ==
				    SESS_TYPE::SESS_COOKIE) {
					service->updateSession(
						stream.client_connection,
						stream.request,
						std::string(response.headers[i]
								    .value,
							    response.headers[i]
								    .value_len),
						*stream.backend_connection
							 .getBackend());
				}
				break;
			}
			default:
				break;
			}
		}

		if (service->session_type == SESS_TYPE::SESS_HEADER &&
		    service->sess_id == header) {
			service->updateSession(
				stream.client_connection, stream.request,
				std::string(response.headers[i].value,
					    response.headers[i].value_len),
				*stream.backend_connection.getBackend());
		}
	}
	if (stream.response.content_length > 0 &&
	    (stream.response.content_length - stream.response.message_length) >
		    0) {
		stream.response.message_bytes_left =
			stream.response.content_length -
			stream.response.message_length;
	}
	if (connection_close_pending && response.content_length == 0 &&
	    response.chunked_status == http::CHUNKED_STATUS::CHUNKED_DISABLED) {
		//we have unknown amount of body data pending, wait until connection is closed
		//FIXME:: As workaround we use chunked
		response.transfer_encoding_type =
			TRANSFER_ENCODING_TYPE::CHUNKED;
		response.chunked_status = http::CHUNKED_STATUS::CHUNKED_ENABLED;
	}
	return validation::REQUEST_RESULT::OK;
}

void http_manager::replyError(HttpStream *stream, http::Code code,
			      const std::string &code_string,
			      const std::string &str, Connection &target,
			      Statistics::HttpResponseHits &resp_stats)
{
	auto tag = StreamDataLogger::logTag(stream, "error");
	auto request_data_len = std::string_view(target.buffer).find('\r');

	zcu_log_print(LOG_INFO, "%s e%d %s \"%.*s\"", tag.data(),
		      static_cast<int>(code), code_string.data(),
		      request_data_len, target.buffer);

	auto response_ = http::getHttpResponse(code, code_string, str);
	size_t written = 0;
	IO::IO_RESULT result = IO::IO_RESULT::ERROR;

	do {
		size_t sent = 0;
		if (!target.ssl_connected) {
			result = target.write(response_.c_str() + written,
					      response_.length() - written,
					      sent);
		} else if (target.ssl != nullptr) {
			result = ssl::SSLConnectionManager::handleWrite(
				target, response_.c_str() + written,
				response_.length() - written, written, true);
		}
		if (sent > 0)
			written += sent;
	} while (result == IO::IO_RESULT::DONE_TRY_AGAIN &&
		 written < response_.length());

	resp_stats.increaseCode(code);
}

bool http_manager::replyRedirect(HttpStream &stream,
				 const Backend &redirect_backend)
{
	/* 0 - redirect is absolute,
	 * 1 - the redirect should include the request path, or
	 * 2 if it should use perl dynamic replacement */
	std::string new_url(redirect_backend.backend_config->url.data());
	auto service = static_cast<Service *>(stream.request.getService());
	char buf[ZCU_DEF_BUFFER_SIZE];

	if (stream.replaceVhostMacro(
		    buf, redirect_backend.backend_config->url.data(),
		    redirect_backend.backend_config->url.length()),
	    redirect_backend.backend_config->redir_macro)
		new_url = buf;

	switch (redirect_backend.backend_config->redir_req) {
	case 1:
		new_url += stream.request.path;
		break;
	case 2: { // Dynamic redirect
		if (zcu_str_replace_regexp(buf, stream.request.path.data(),
					   stream.request.path.length(),
					   &service->service_config.url->pat,
					   new_url.data()) != -1) {
			new_url = buf;
		}
		break;
	}
	case 0:
	default:
		break;
	}
	int redirect_code = redirect_backend.backend_config->be_type;
	switch (redirect_backend.backend_config->be_type) {
	case 301:
	case 307:
		break;
	default:
		redirect_code = 302; // FOUND
		break;
	}
	return replyRedirect(redirect_code, new_url, stream);
}

bool http_manager::replyRedirect(int code, const std::string &url,
				 HttpStream &stream)
{
	auto response_ =
		http::getRedirectResponse(static_cast<http::Code>(code), url);

	auto service = static_cast<Service *>(stream.request.getService());
	zcu_log_print(
		LOG_INFO,
		"[redirect][%lx][%lu][%s][%s] the request \"%s\" from %s was redirected to \"%s\"",
		pthread_self(), stream.stream_id,
		stream.service_manager->listener_config_->name.data(),
		(service != nullptr) ? service->name.c_str() : "null",
		stream.request.http_message_str.data(),
		stream.client_connection.getPeerAddress().c_str(), url.data());

	IO::IO_RESULT result = IO::IO_RESULT::ERROR;
	size_t sent = 0;
	if (!stream.client_connection.ssl_connected) {
		result = stream.client_connection.write(
			response_.c_str(), response_.length(), sent);
	} else if (stream.client_connection.ssl != nullptr) {
		result = ssl::SSLConnectionManager::handleWrite(
			stream.client_connection, response_.c_str(),
			response_.length(), sent, true);
	}

	if (result == IO::IO_RESULT::DONE_TRY_AGAIN &&
	    sent < response_.length()) {
		std::strncpy(stream.backend_connection.buffer,
			     response_.data() + sent, response_.size() - sent);
		stream.backend_connection.buffer_size = response_.size() - sent;
		stream.response.setHeaderSent(true);
		stream.response.chunked_status =
			CHUNKED_STATUS::CHUNKED_ENABLED;
		stream.client_connection.enableWriteEvent();
		return false;
	}

	stream.service_manager->listener_config_->response_stats.increaseCode(
		static_cast<http::Code>(code));

	return true;
}

bool http_manager::replyTestServer(HttpStream &stream, bool async)
{
	const std::string response_ =
		"HTTP/1.1 200 OK\r\nServer: zproxy 1.0\r\nExpires: now\r\nPragma: "
		"no-cache\r\nCache-control: no-cache,no-store\r\nContent-Type: "
		"text/html\r\nContent-Length: 11\r\n\r\nHello World\n";
	if (async) {
		IO::IO_RESULT result = IO::IO_RESULT::ERROR;
		size_t sent = 0;
		if (!stream.client_connection.ssl_connected) {
			result = stream.client_connection.write(
				response_.c_str(), response_.length() - 1,
				sent);
		} else if (stream.client_connection.ssl != nullptr) {
			result = ssl::SSLConnectionManager::handleWrite(
				stream.client_connection, response_.c_str(),
				response_.length() - 1, sent, true);
		}

		if (result == IO::IO_RESULT::DONE_TRY_AGAIN &&
		    sent < response_.length() - 1) {
			std::strncpy(stream.backend_connection.buffer,
				     response_.data() + sent,
				     response_.size() - 1 - sent);
			stream.backend_connection.buffer_size =
				response_.size() - sent - 1;
			stream.response.chunked_status =
				CHUNKED_STATUS::CHUNKED_ENABLED;
			stream.status |= helper::to_underlying(
				STREAM_STATUS::REQUEST_PENDING);
			stream.client_connection.buffer_size = 0;
			stream.client_connection.buffer_offset = 0;
			stream.client_connection.enableWriteEvent();
			return false;
		}
	} else {
		std::strncpy(stream.backend_connection.buffer, response_.data(),
			     response_.size());
		stream.backend_connection.buffer_size = response_.size() - 1;
		stream.response.setHeaderSent(true);
		stream.response.chunked_status =
			CHUNKED_STATUS::CHUNKED_ENABLED;
		stream.status |=
			helper::to_underlying(STREAM_STATUS::REQUEST_PENDING);
		stream.client_connection.buffer_size = 0;
		stream.client_connection.buffer_offset = 0;
		stream.client_connection.enableWriteEvent();
	}
	return true;
}
