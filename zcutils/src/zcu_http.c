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

#include "zcu_http.h"

const char *ws_str_responses[WS_HTTP_MAX] = {
	HTTP_PROTO "500 Internal Server Error" HTTP_LINE_END,
	HTTP_PROTO "400 Bad Request" HTTP_LINE_END,
	HTTP_PROTO "401 Unauthorized" HTTP_LINE_END,
	HTTP_PROTO "404 Not Found" HTTP_LINE_END,
	HTTP_PROTO "405 Method Not Allowed" HTTP_LINE_END,
	HTTP_PROTO "409 Conflict" HTTP_LINE_END,
	HTTP_PROTO "301 Moved Permanently" HTTP_LINE_END,
	HTTP_PROTO "302 Found" HTTP_LINE_END,
	HTTP_PROTO "307 Temporary Redirect" HTTP_LINE_END,
	HTTP_PROTO "200 OK" HTTP_LINE_END,
	HTTP_PROTO "201 Created" HTTP_LINE_END,
	HTTP_PROTO "204 No Content" HTTP_LINE_END,
};
