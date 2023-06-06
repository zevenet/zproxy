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

#ifndef _ZPROXY_HTTP_PARSER_H_
#define _ZPROXY_HTTP_PARSER_H_

#include <map>
#include <string>
#include <sys/uio.h>
#include <regex>

#include "http_protocol.h"
#include "pico_http_parser.h"

#define cmp_header_name(header, val) {                                           \
	header->name_len == strlen(val) &&                                     \
		strncasecmp(header->name, val, header->name_len) == 0 \
}
#define cmp_header_value(header, val) {                                          \
	header->value_len == strlen(val) &&                                    \
		strncasecmp(header->value, val, header->value_len) == 0 \
}

namespace http_parser
{
enum class PARSE_RESULT : uint8_t { SUCCESS, FAILED, INCOMPLETE, TOOLONG };

using namespace http;

class HttpData {
private:
	bool headers_sent{ false };

public:
	std::vector<std::string> volatile_headers;	// it is used to save backend information that can change if a new backend is set. It allows to not remove all headers
	std::vector<std::string> extra_headers;
	std::vector<std::string> permanent_extra_headers;

#ifdef CACHE_ENABLED
	bool pragma = false;
	bool cache_control = false;
#endif
	phr_header headers[MAX_HEADERS_SIZE];
	size_t header_length_new{0}; // number of byte of headers after rewritting the buffer

	char *buffer{nullptr};
	size_t buffer_size{0};
	size_t last_length{0};
	size_t num_headers{0};
	// indicate firl line of a http request / response
	std::string http_message_str{""};
	size_t headers_length{0};
	int minor_version{-1};

	char *message{nullptr}; // body data start
	size_t message_length{0}; // length of body data length in current received message
	ssize_t message_bytes_left{0}; // content-length minus already body received
	size_t message_total_bytes{0}; // total bytes read for the body in different frames
	size_t content_length{0};  // value of the content-length received in the header
	bool message_undefined{false}; // received body data but there is not content-length or chunk defined

	bool connection_close_pending{false};
	bool connection_keep_alive{false};
	bool connection_header_upgrade{false};
	bool upgrade_header{false};
	std::string x_forwarded_for_header{""};

	/* This enumerate indicates the chunked mechanism status. */
	int partial_last_chunk{0};
	http::CHUNKED_STATUS chunked_status{ CHUNKED_STATUS::CHUNKED_DISABLED };

	http::HTTP_VERSION http_version{HTTP_VERSION::NONE};
	http::REQUEST_METHOD request_method{REQUEST_METHOD::NONE};
	http::TRANSFER_ENCODING_TYPE transfer_encoding_type{TRANSFER_ENCODING_TYPE::NONE};

	// Methods
	HttpData();
	virtual ~HttpData()
	{
		extra_headers.clear();
		permanent_extra_headers.clear();
	}

	void resetParser(void);
	bool getHeaderValue(const http::HTTP_HEADER_NAME header_name,
			std::string & out_key) const;
	bool getHeaderValue(const std::string &, std::string & out_key) const;
	void setBuffer(char *ext_buffer, size_t ext_buffer_size);

	size_t prepareToSend(char **buf, bool trim_parm = false);

	void addHeader(http::HTTP_HEADER_NAME header_name,
			   const std::string & header_value, bool permanent = false);
	void addHeader(const std::string & header_value, bool permanent = false);
	void removeHeader(http::HTTP_HEADER_NAME header_name);

	/* There are pending body data to receive */
	bool hasPendingData(void) const;

	char *getBuffer(void) const;
	bool getHeaderSent(void) const;
	void setHeaderSent(bool value, size_t len = 0);

	std::string getHttpVersion() const;

	/* It copies the buffer pointer and size to the message field.
	 * This function is used when every received data is body or has to be
	 * sent to the another peer without any modification or parsing
	 */
	void updateMessageBuffer(void);
	void updateMessageLeft(void);
	void updateMessageTotalBytes(size_t bytes);

	void setHeaderTransferEncoding(std::string header_value);
	void setHeaderConnection(std::string header_value);
	void setHeaderUpgrade(std::string header_value);
	void setHeaderContentLength(std::string &header_value);
	void setHeaderXForwardedFor(const std::string &cl_addr);
	void setHeaderStrictTransportSecurity(int sts);

	ssize_t parseChunk(const char *data, size_t data_size, bool *end);
	ssize_t handleChunkedData(void);
	void manageBody(const char *buf, int buf_len);

	bool expectBody(void) const;
	size_t getBufferRewritedLength(void) const;

};
} // namespace http_parser

#endif
