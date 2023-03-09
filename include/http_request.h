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

#ifndef _ZPROXY_HTTP_REQUEST_H_
#define _ZPROXY_HTTP_REQUEST_H_

#include "config.h"
#include "http_parser.h"

class HttpRequest : public http_parser::HttpData {
public:
	char *path_ptr {nullptr}; /* Incoming URL string without modifying*/
	size_t path_ptr_length {0};

	char *method{nullptr};
	size_t method_len{0};
	std::string path{""}; /* Incoming URL that could be modified by rw_url */
	std::string path_ori{""}; /* Incoming URL string without modifying*/
	std::string path_repl{""}; /* String that replaces the original URI removed*/
	bool path_mod {false};	/* flag if path was modified */

	std::string destination_header{ "" };
	bool add_destination_header{ false };
	bool add_host_header{ false };
	bool accept_encoding_header{ false };
	bool expect_100_cont_header { false };
	std::string virtual_host{ "" };
#ifdef CACHE_ENABLED
	struct CacheRequestOptions c_opt;
#endif

	// Methods

	void reset(void);
	http_parser::PARSE_RESULT parse(const char *data, size_t data_size,
				  size_t *used_bytes);
	void print(void) const;

	void updateRequestLine(void);
	void setRequestMethod(void);
	http::REQUEST_METHOD getRequestMethod(void);
	void printRequestMethod(void) const;
	std::string_view getMethod(void) const;
	std::string_view getRequestLine(void) const;
	std::string getUrl(void) const;

	void manageHeaders(const struct zproxy_proxy_cfg &listener,
		phr_header *header, bool enabled_continue);

	void setHeaderHost(struct zproxy_backend_cfg *bck);
};

#endif
