/*
 * Copyright (C) 2023  Zevenet S.L. <support@zevenet.com>
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as
 * published by the Free Software Foundation, either version 3 of the
 * License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#include "config.h"
#include "http_protocol.h"
#include "http_request.h"
#include "zcu_common.h"

void HttpRequest::reset() {
	HttpData::resetParser();

	path_ptr=nullptr;
	path_ptr_length=0;

	method=nullptr;
	method_len=0;
	path="";
	path_ori = "";
	path_repl = "";
	path_mod = false;

	destination_header="";
	add_destination_header=false;
	add_host_header=false;
	upgrade_header=false;
	connection_header_upgrade=false;
	accept_encoding_header=false;
	expect_100_cont_header = false;
	virtual_host="" ;
}

http_parser::PARSE_RESULT
HttpRequest::parse(const char *data, const size_t data_size,
					size_t *used_bytes)
{
	char *http_message;
	size_t http_message_length;
	reset();
	buffer = const_cast<char *>(data);
	buffer_size = data_size;
	num_headers = MAX_HEADERS_SIZE;
	const char **method_ = const_cast<const char **>(&method);
	const char **path_ = const_cast<const char **>(&path_ptr);
	auto pret = phr_parse_request(data, data_size, method_, &method_len,
					  path_, &path_ptr_length, &minor_version,
					  headers, &num_headers, last_length);
	path = std::string(path_ptr, path_ptr_length);

	last_length = data_size;
	if (pret > 0) {
		*used_bytes = static_cast<size_t>(pret);
		headers_length = pret;
#if DEBUG_ZCU_LOG
		printRequest();
#endif
		http_version = minor_version == 1 ? http::HTTP_VERSION::HTTP_1_1 :
							  http::HTTP_VERSION::HTTP_1_0;
		message = &buffer[pret];
		message_length = buffer_size - static_cast<size_t>(pret);
		http_message = method;
		http_message_length = std::string_view({data, data_size}).find('\r');
		if (http_message_length > buffer_size)
			http_message_length = buffer_size;
		http_message_str =
			std::string(http_message, http_message_length);
		return http_parser::PARSE_RESULT::SUCCESS; /* successfully parsed the request */
	} else if (pret == -2) {
		if (method != nullptr && minor_version == -1)
			return http_parser::PARSE_RESULT::TOOLONG;
		else if (MAX_DATA_SIZE <= data_size) {
			zcu_log_print_th(
				LOG_INFO,
				"the request cannot be parsed, buffer is complete (%d Bytes)",
				MAX_DATA_SIZE);
			return http_parser::PARSE_RESULT::FAILED;
		} else /* request is incomplete, continue the loop */
			return http_parser::PARSE_RESULT::INCOMPLETE;
	}
	return http_parser::PARSE_RESULT::FAILED;
}

void HttpRequest::print() const
{
	zcu_log_print_th(LOG_DEBUG, "method is %.*s", method_len, method);
	zcu_log_print_th(LOG_DEBUG, "path is %.*s", path.length(), path.data());
	zcu_log_print_th(LOG_DEBUG, "HTTP version is 1.%d", minor_version);
	zcu_log_print_th(LOG_DEBUG, "headers:");
	for (size_t i = 0; i != num_headers; ++i) {
		zcu_log_print_th(LOG_DEBUG, "\t%.*s: %.*s", headers[i].name_len,
				  headers[i].name, headers[i].value_len,
				  headers[i].value);
	}
}

void HttpRequest::setRequestMethod()
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

void HttpRequest::printRequestMethod() const
{
	zcu_log_print_th(
		LOG_DEBUG, "Request method: %s",
        http::http_info::http_verb_strings.at(request_method).c_str());
}

std::string_view HttpRequest::getMethod() const
{
	return method != nullptr ? std::string_view(method, method_len) :
					 std::string_view();
}

std::string_view HttpRequest::getRequestLine() const
{
	return std::string_view(http_message_str);
}

std::string HttpRequest::getUrl() const
{
	return path;
}

void HttpRequest::manageHeaders(const struct zproxy_proxy_cfg &listener,
		phr_header *header)
{
	std::string header_name, header_value;
	header_name = std::string_view(header->name, header->name_len);
	header_value = std::string_view(header->value, header->value_len);

	auto it = http::http_info::headers_names.find(header_name);
	if (it != http::http_info::headers_names.end()) {
		switch (it->second) {
		case http::HTTP_HEADER_NAME::DESTINATION:
			if (listener.header.rw_destination != 0) {
				header->header_off = true;
				add_destination_header = true;
				destination_header = header_value;
			}
			break;
		case http::HTTP_HEADER_NAME::UPGRADE:
			setHeaderUpgrade(header_value);
			break;
		case http::HTTP_HEADER_NAME::CONNECTION: {
			setHeaderConnection(header_value);
			break;
		}
		case http::HTTP_HEADER_NAME::ACCEPT_ENCODING:
			accept_encoding_header = true;
			break;
		case http::HTTP_HEADER_NAME::TRANSFER_ENCODING:
			setHeaderTransferEncoding(header_value);
			break;
		case http::HTTP_HEADER_NAME::CONTENT_LENGTH: {
			setHeaderContentLength(header_value);
			break;
		}
		case http::HTTP_HEADER_NAME::HOST: {
			virtual_host = header_value;
			add_host_header =
				listener.header.rw_host == 1;
			// it could be disabled in the replaceheader directive
			if (!header->header_off)
				header->header_off =
					listener.header.rw_host == 1;
			break;
		}
		case http::HTTP_HEADER_NAME::EXPECT: {
			if (header_value == "100-continue") {
				expect_100_cont_header = true;
				zcu_log_print_th(
					LOG_DEBUG,
					"%s():%d: client Expects 100 continue",
					__FUNCTION__, __LINE__);
			}
			header->header_off = 1;
			break;
		}
		case http::HTTP_HEADER_NAME::X_FORWARDED_FOR: {
			x_forwarded_for_header = header_value;
			header->header_off = true;
			break;
		}
		default:
			break;
		}
	}
}

void HttpRequest::setHeaderHost(struct zproxy_backend_cfg *bck)
{
	std::string newh = http::http_info::headers_names_strings.at(http::HTTP_HEADER_NAME::HOST);
	newh += ": " + std::string(bck->address) + ":" + std::to_string(bck->port);
	newh += http::CRLF;
	volatile_headers.push_back(std::move(newh));
}
