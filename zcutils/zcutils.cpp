/*
 *   This file is part of zcutils, ZEVENET Core Utils.
 *
 *   Copyright (C) ZEVENET SL.
 *   Author: Laura Garcia <laura.garcia@zevenet.com>
 *
 *   This program is free software: you can redistribute it and/or modify
 *   it under the terms of the GNU Affero General Public License as
 *   published by the Free Software Foundation, either version 3 of the
 *   License, or any later version.
 *
 *   This program is distributed in the hope that it will be useful,
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *   GNU Affero General Public License for more details.
 *
 *   You should have received a copy of the GNU Affero General Public License
 *   along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 */

#include "zcutils.h"

char zcu_log_prefix[LOG_PREFIX_BUFSIZE] = "";
int zcu_log_level = ZCUTILS_LOG_LEVEL_DEFAULT;
int zcu_log_output = ZCUTILS_LOG_OUTPUT_DEFAULT;

void zcu_log_set_prefix(const char *string)
{
	if (strlen(string) >= LOG_PREFIX_BUFSIZE)
		zcu_log_print(
			LOG_ERR,
			"The farm name is greater than the prefix log: %d >= %d",
			strlen(string), LOG_PREFIX_BUFSIZE);
	else
		memcpy(zcu_log_prefix, string, strlen(string) + 1);
}

void zcu_log_set_level(int loglevel)
{
	zcu_log_level = loglevel;
	setlogmask(LOG_UPTO(loglevel));
}

void zcu_log_set_output(int output)
{
	switch (output) {
	case VALUE_LOG_OUTPUT_STDOUT:
		zcu_log_output = ZCUTILS_LOG_OUTPUT_STDOUT;
		break;
	case VALUE_LOG_OUTPUT_STDERR:
		zcu_log_output = ZCUTILS_LOG_OUTPUT_STDERR;
		break;
	case VALUE_LOG_OUTPUT_SYSOUT:
		zcu_log_output =
			ZCUTILS_LOG_OUTPUT_SYSLOG | ZCUTILS_LOG_OUTPUT_STDOUT;
		break;
	case VALUE_LOG_OUTPUT_SYSERR:
		zcu_log_output =
			ZCUTILS_LOG_OUTPUT_SYSLOG | ZCUTILS_LOG_OUTPUT_STDERR;
		break;
	case VALUE_LOG_OUTPUT_SYSLOG:
	default:
		zcu_log_output = ZCUTILS_LOG_OUTPUT_SYSLOG;
	}
	return;
}

int _zcu_log_print(int loglevel, const char *fmt, ...)
{
	va_list args;

#if DEBUG_ZCU_LOG == 0
	if (loglevel == LOG_DEBUG)
		return 0;
#endif

	if (loglevel > zcu_log_level)
		return 0;

	if (zcu_log_output & ZCUTILS_LOG_OUTPUT_STDOUT) {
		va_start(args, fmt);
		vfprintf(stdout, fmt, args);
		fprintf(stdout, "\n");
		va_end(args);
	}

	if (zcu_log_output & ZCUTILS_LOG_OUTPUT_STDERR) {
		va_start(args, fmt);
		vfprintf(stderr, fmt, args);
		fprintf(stderr, "\n");
		va_end(args);
	}

	if (zcu_log_output & ZCUTILS_LOG_OUTPUT_SYSLOG) {
		va_start(args, fmt);
		vsyslog(loglevel, fmt, args);
		va_end(args);
	}

	return 0;
}

/****  BACKTRACE  ****/

size_t ConvertToVMA(size_t addr)
{
	Dl_info info;
	link_map *link_map;
	dladdr1((void *)addr, &info, (void **)&link_map, RTLD_DL_LINKMAP);
	return addr - link_map->l_addr;
}

void zcu_bt_print()
{
	void *callstack[128];
	int frame_count =
		backtrace(callstack, sizeof(callstack) / sizeof(callstack[0]));
	FILE *fp;
	char path[ZCU_DEF_BUFFER_SIZE];

	if (!frame_count) {
		zcu_log_print(LOG_ERR, "No backtrace strings found!");
		exit(EXIT_FAILURE);
	} else {
		for (int i = 0; i < frame_count; i++) {
			Dl_info info;
			if (dladdr(callstack[i], &info)) {
				char command[256];
				size_t VMA_addr =
					ConvertToVMA((size_t)callstack[i]);
				VMA_addr -=
					1; // https://stackoverflow.com/questions/11579509/wrong-line-numbers-from-addr2line/63841497#63841497
				snprintf(command, sizeof(command),
					 "addr2line -e %s -Ci %zx",
					 info.dli_fname, VMA_addr);

				/* Open the command for reading. */
				fp = popen(command, "r");
				if (fp == NULL) {
					zcu_log_print(LOG_ERR,
						      "Failed to run: %s",
						      command);
					exit(EXIT_FAILURE);
				} else {
					/* Read the output a line at a time - output it. */
					while (fgets(path, sizeof(path), fp) !=
					       NULL) {
						printf("%s", path);
					}

					zcu_log_print(LOG_ERR, "Backtrace: %s",
						      path);

					/* close */
					pclose(fp);
				}
			}
		}
	}
}

/****  STRING  ****/

void zcu_str_snprintf(char *strdst, int size, char *strsrc)
{
	for (int i = 0; i < size; i++) {
		strdst[i] = *(strsrc + i);
	}
	strdst[size] = '\0';
}

/****  BUFFER  ****/

#define ZCU_DEF_BUFFER_SIZE 4096
#define EXTRA_SIZE 1024

int zcu_buf_get_size(struct zcu_buffer *buf)
{
	return buf->size;
}

char *zcu_buf_get_next(struct zcu_buffer *buf)
{
	return buf->data + buf->next;
}

int zcu_buf_resize(struct zcu_buffer *buf, int times)
{
	char *pbuf;
	int newsize;

	if (times == 0)
		return 0;

	newsize = buf->size + (times * EXTRA_SIZE) + 1;

	if (!buf->data)
		return 1;

	pbuf = (char *)realloc(buf->data, newsize);
	if (!pbuf)
		return 1;

	buf->data = pbuf;
	buf->size = newsize;
	return 0;
}

int zcu_buf_create(struct zcu_buffer *buf)
{
	buf->size = 0;
	buf->next = 0;

	buf->data = (char *)calloc(1, ZCU_DEF_BUFFER_SIZE);
	if (!buf->data) {
		return 1;
	}

	*buf->data = '\0';
	buf->size = ZCU_DEF_BUFFER_SIZE;
	return 0;
}

int zcu_buf_isempty(struct zcu_buffer *buf)
{
	return (buf->data[0] == 0);
}

char *zcu_buf_get_data(struct zcu_buffer *buf)
{
	return buf->data;
}

int zcu_buf_clean(struct zcu_buffer *buf)
{
	if (buf->data)
		free(buf->data);
	buf->size = 0;
	buf->next = 0;
	return 0;
}

int zcu_buf_reset(struct zcu_buffer *buf)
{
	buf->data[0] = 0;
	buf->next = 0;
	return 0;
}

int zcu_buf_concat_va(struct zcu_buffer *buf, int len, char *fmt, va_list args)
{
	int times = 0;
	char *pnext;

	if (buf->next + len >= buf->size)
		times = ((buf->next + len - buf->size) / EXTRA_SIZE) + 1;

	if (zcu_buf_resize(buf, times)) {
		zcu_log_print(
			LOG_ERR,
			"Error resizing the buffer %d times from a size of %d!",
			times, buf->size);
		return 1;
	}

	pnext = zcu_buf_get_next(buf);
	vsnprintf(pnext, len + 1, fmt, args);
	buf->next += len;

	return 0;
}

int zcu_buf_concat(struct zcu_buffer *buf, char *fmt, ...)
{
	int len;
	va_list args;

	va_start(args, fmt);
	len = vsnprintf(0, 0, fmt, args);
	va_end(args);

	va_start(args, fmt);
	zcu_buf_concat_va(buf, len, fmt, args);
	va_end(args);

	return 0;
}

/*
 * It replaces a chain in the original string.
 *    Returns :  n, offset where the replacement finished
 *               0,  if it didn't do anything
*/
int zcu_str_replace_regexp(char *buf, const char *ori_str, int ori_len,
			   regex_t *match, char *replace_str)
{
	//memset(buf.get(), 0, ZCU_DEF_BUFFER_SIZE);
	regmatch_t umtch[10];
	char *chptr, *enptr, *srcptr;
	int offset = -1;
	umtch[0].rm_so = 0;
	umtch[0].rm_eo = ori_len;
	if (regexec(match, ori_str, 10, umtch, REG_STARTEND)) {
		zcu_log_print(LOG_DEBUG, "String didn't match %.*s", ori_len,
			      ori_str);
		return -1;
	}

	zcu_log_print(LOG_DEBUG, "String matches %.*s", ori_len, ori_str);

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
int zcu_str_find_str(int *off_start, int *off_end, const char *ori_str,
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
int zcu_str_replace_str(char *buf, const char *ori_str, int ori_len,
			const char *match_str, int match_len, char *replace_str,
			int replace_len)
{
	int offst = -1, offend = -1, offcopy = 0,
	    buf_len = ori_len - match_len + replace_len;

	if (!zcu_str_find_str(&offst, &offend, ori_str, ori_len, match_str,
			      match_len)) {
		zcu_log_print(LOG_DEBUG, "String didn't match %.*s", ori_len,
			      ori_str);
		return 0;
	}

	zcu_log_print(LOG_DEBUG, "String matches %.*s", ori_len, ori_str);

	if (buf_len > ZCU_DEF_BUFFER_SIZE) {
		zcu_log_print(
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
