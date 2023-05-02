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

#include "http_tools.h"
#include "zcu_log.h"
#include "zcu_common.h"
#include <ctype.h>

/*
 * It replaces a chain in the original string.
 *    Returns :  n, offset where the replacement finished
 *               0,  if it didn't do anything
*/
int str_replace_regexp(char *buf, const char *ori_str, int ori_len,
			   regex_t *match, char *replace_str)
{
	regmatch_t umtch[10];
	char *chptr, *enptr, *srcptr;
	int offset = -1;
	umtch[0].rm_so = 0;
	umtch[0].rm_eo = ori_len;
	if (regexec(match, ori_str, 10, umtch, REG_STARTEND))
		return -1;

	zcu_log_print_th(LOG_DEBUG, "String matches %.*s", ori_len, ori_str);

	memcpy(buf, ori_str, umtch[0].rm_so);

	chptr = buf + umtch[0].rm_so;
	enptr = buf + ZCU_DEF_BUFFER_SIZE - 1;
	*enptr = '\0';
	srcptr = replace_str;
	for (; *srcptr && chptr < enptr - 1;) {
		if (srcptr[0] == '$' && srcptr[1] == '$') {
			*chptr++ = *srcptr++;
			srcptr++;
		}
		if (srcptr[0] == '$' && isdigit(srcptr[1])) {
			if (chptr + umtch[srcptr[1] - 0x30].rm_eo -
				    umtch[srcptr[1] - 0x30].rm_so >
			    enptr - 1)
				break;
			memcpy(chptr, ori_str + umtch[srcptr[1] - 0x30].rm_so,
			       umtch[srcptr[1] - 0x30].rm_eo -
				       umtch[srcptr[1] - 0x30].rm_so);
			chptr += umtch[srcptr[1] - 0x30].rm_eo -
				 umtch[srcptr[1] - 0x30].rm_so;
			srcptr += 2;
			continue;
		}
		*chptr++ = *srcptr++;
	}

	offset = chptr - buf;

	//copy the last part of the string
	if (umtch[0].rm_eo != umtch[0].rm_so) {
		memcpy(chptr, ori_str + umtch[0].rm_eo,
		       ori_len - umtch[0].rm_eo);
		chptr += ori_len - umtch[0].rm_eo;
	}

	*chptr = '\0';

	return offset;
}

/**
   * @brief It looks for a substring inside of a string.
   *
   * @param It is the start offset where the substrng was found
   * @param It is the end offset of the substring
   * @param It is the string where look for
   * @param It is the string lenght
   * @param It is the sub string that is going to be looked for
   * @param It is the sub string lenght
   *
   * @return 1 if the string was found of 0 if it didn't
   */
int str_find_str(int *off_start, int *off_end, const char *ori_str,
		     int ori_len, const char *match_str, int match_len)
{
	int i, flag = 0;
	*off_start = -1;
	*off_end = -1;

	for (i = 0; i < ori_len && flag < match_len; i++) {
		if (ori_str[i] == match_str[flag]) {
			if (flag == 0)
				*off_start = i;
			flag++;
		} else
			flag = 0;
	}
	if (flag == 0)
		return 0;

	*off_end = *off_start + match_len;
	return 1;
}

/**
   * @brief It replaces a substring for another inside of a string
   *
   * @param It is the buffer where the string modified will be returned
   * @param It is the original string where looks for
   * @param It is the lenght of the original string
   * @param It is the sub string that is going to be removed
   * @param It is the sub string lenght
   * @param It is the string that will be insert
   * @param It is the length of the string to insert
   *
   * @return 1 if the string was modified or 0 if it doesn't
   */
int str_replace_str(char *buf, const char *ori_str, int ori_len,
			const char *match_str, int match_len, char *replace_str,
			int replace_len)
{
	int offst = -1, offend = -1, offcopy = 0,
	    buf_len = ori_len - match_len + replace_len;

	if (!str_find_str(&offst, &offend, ori_str, ori_len, match_str,
				  match_len))
		return 0;

	zcu_log_print_th(LOG_DEBUG, "String matches %.*s", ori_len, ori_str);

	if (buf_len > ZCU_DEF_BUFFER_SIZE) {
		zcu_log_print_th(
			LOG_ERR,
			"String could not be replaced, the buffer size is not enought - %.*s",
			ori_len, ori_str);
		return 0;
	}

	if (offst != 0) {
		memcpy(buf, ori_str, offst);
	}

	offcopy += offst;
	memcpy(buf + offcopy, replace_str, replace_len);

	if (offend != ori_len) {
		offcopy += replace_len;
		memcpy(buf + offcopy, ori_str + offend, ori_len - offend);
	}
	buf[buf_len] = '\0';

	return 1;
}

int zproxy_http_encode_url(char *urldest, char *urlorig)
{
	int i = 0, j = 0;
	char c;

	while (urlorig[i]) {
		c = urlorig[i];
		if (isalnum(c) || c == '_' || c == '.' || c == ':' ||
		    c == '/' || c == '?' || c == '&' || c == ';' || c == '-' ||
		    c == '=' || c == '%')
			urldest[j] = c;
		else {
			sprintf(urldest + j, "%%%02x", c);
			j += 3;
		}
		i++;
		j++;
	}
	urldest[j] = '\0';
	return 0;
}
