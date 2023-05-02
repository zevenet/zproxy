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

#ifndef _ZPROXY_HTTP_TOOLS_H_
#define _ZPROXY_HTTP_TOOLS_H_

#include <pcreposix.h>

int str_replace_regexp(char *buf, const char *ori_str, int ori_len,
			   regex_t *match, char *replace_str);

int str_find_str(int *off_start, int *off_end, const char *ori_str,
		     int ori_len, const char *match_str, int match_len);

int str_replace_str(char *buf, const char *ori_str, int ori_len,
			const char *match_str, int match_len, char *replace_str,
			int replace_len);

int zproxy_http_encode_url(char *urldest, char *urlorig);


#endif
