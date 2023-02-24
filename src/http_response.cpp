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

#include "http_response.h"
#include "zcu_common.h"
#include "config.h"
#include "session.h"

void HttpResponse::reset()
{
    HttpData::resetParser();
    http_status_code=0;
    status_message=nullptr;
    location=nullptr;
    content_location=nullptr;
}

http_parser::PARSE_RESULT
HttpResponse::parse(const char *data, const size_t data_size,
					 size_t *used_bytes)
{
	char *http_message;
	size_t http_message_length;

	reset();
	buffer = const_cast<char *>(data);
	buffer_size = data_size;
	num_headers = MAX_HEADERS_SIZE;
	const char **status_message_ =
		const_cast<const char **>(&status_message);
	auto pret = phr_parse_response(data, data_size, &minor_version,
					   &http_status_code, status_message_,
					   &message_length, headers, &num_headers,
					   last_length);
	last_length = data_size;
	if (pret > 0) {
		*used_bytes = static_cast<size_t>(pret);
		headers_length = pret;
		http_version = minor_version == 1 ? http::HTTP_VERSION::HTTP_1_1 :
							  http::HTTP_VERSION::HTTP_1_0;
		http_message = buffer;
		http_message_length = std::string_view({buffer, data_size}).find('\r');
		if (http_message_length > buffer_size)
			http_message_length = buffer_size;
		message = &buffer[pret];
		message_length = buffer_size - static_cast<size_t>(pret);
		http_message_str =
			std::string(http_message, http_message_length);
#if DEBUG_ZCU_LOG
		printResponse();
#endif
		return http_parser::PARSE_RESULT::SUCCESS; /* successfully parsed the request */
	} else if (pret == -2) {
		if (MAX_DATA_SIZE <= data_size) {
			zcu_log_print_th(
				LOG_INFO,
				"the response cannot be parsed, buffer is complete (%d Bytes)",
				MAX_DATA_SIZE);
			return http_parser::PARSE_RESULT::TOOLONG;
		} else /* response is incomplete, continue the loop */
			return http_parser::PARSE_RESULT::INCOMPLETE;
	}
	return http_parser::PARSE_RESULT::FAILED;
}

void HttpResponse::print() const
{
	zcu_log_print_th(LOG_DEBUG, "HTTP 1.%d %d %s", minor_version,
			  http_status_code, http::reasonPhrase(http_status_code));
	zcu_log_print_th(LOG_DEBUG, "headers:");
	for (size_t i = 0; i != num_headers; ++i) {
		zcu_log_print_th(LOG_DEBUG, "\t%.*s: %.*s", headers[i].name_len,
				  headers[i].name, headers[i].value_len,
				  headers[i].value);
	}
}

void HttpResponse::manageHeaders(phr_header *header,
		const struct zproxy_service_cfg *service, std::string &session){
	std::string header_name, header_value;
	header_name = std::string_view(header->name, header->name_len);
	header_value = std::string_view(header->value, header->value_len);

	if (service && service->session.sess_type == SESS_TYPE::SESS_HEADER
			&& header_name == service->session.sess_id)
		session = std::string(header->value, header->value_len);

	auto it = http::http_info::headers_names.find(header_name);
	if (it != http::http_info::headers_names.end()) {
		switch (it->second) {
			case http::HTTP_HEADER_NAME::UPGRADE:
				setHeaderUpgrade(header_value);
				break;
			case http::HTTP_HEADER_NAME::CONNECTION: {
				setHeaderConnection(header_value);
				break;
			}
			case http::HTTP_HEADER_NAME::CONTENT_LENGTH: {
				setHeaderContentLength(header_value);
				break;
			}
			case http::HTTP_HEADER_NAME::CONTENT_LOCATION:
				content_location = header;
				break;
			case http::HTTP_HEADER_NAME::LOCATION: {
				location = header;
				break;
			}
			case http::HTTP_HEADER_NAME::STRICT_TRANSPORT_SECURITY:
				if (service && service->header.sts > 0)
					header->header_off = true;
				break;
			case http::HTTP_HEADER_NAME::TRANSFER_ENCODING:
				setHeaderTransferEncoding(header_value);
				break;
			case http::HTTP_HEADER_NAME::SET_COOKIE: {
				 if (service && service->session.sess_type == SESS_TYPE::SESS_COOKIE) {
					session = sessions::getCookieValue(header_value, service->session.sess_id);
				}
				break;
			}
			default:
				break;
			}
		}
}
