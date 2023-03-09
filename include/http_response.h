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

#ifndef _ZPROXY_HTTP_RESPONSE_H_
#define _ZPROXY_HTTP_RESPONSE_H_

#include "http_parser.h"
#include "config.h"

class HttpResponse : public http_parser::HttpData {
    public:
    int http_status_code{0};
    char *status_message{nullptr};

    phr_header *location{nullptr};
    phr_header *content_location{nullptr};

    void reset();
	http_parser::PARSE_RESULT parse(const char *data, size_t data_size,
				   size_t *used_bytes);

    void print(void) const;
    std::string_view getResponseLine();

    void manageHeaders(phr_header *header,
			const struct zproxy_service_cfg *service,
			std::string &session_key, bool enabled_continue);
};

#endif
