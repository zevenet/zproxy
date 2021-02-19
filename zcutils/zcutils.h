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

#ifndef _ZCUTILS_H_
#define _ZCUTILS_H_

#include <stdio.h>
#include <stdarg.h>
#include <syslog.h>
#include <cstdlib>
#include <execinfo.h>
#include <cassert>
#include <sys/resource.h>

/****  LOG  ****/

#define ZCUTILS_LOG_OUTPUT_SYSLOG			(1 << 0)
#define ZCUTILS_LOG_OUTPUT_STDOUT			(1 << 1)
#define ZCUTILS_LOG_OUTPUT_STDERR			(1 << 2)

enum zcu_log_output
{
	VALUE_LOG_OUTPUT_SYSLOG,
	VALUE_LOG_OUTPUT_STDOUT,
	VALUE_LOG_OUTPUT_STDERR,
	VALUE_LOG_OUTPUT_SYSOUT,
	VALUE_LOG_OUTPUT_SYSERR,
};

#define ZCUTILS_LOG_LEVEL_DEFAULT			LOG_NOTICE
#define ZCUTILS_LOG_OUTPUT_DEFAULT			ZCUTILS_LOG_OUTPUT_SYSLOG

static inline int zcu_log_level = ZCUTILS_LOG_LEVEL_DEFAULT;
static inline int zcu_log_output = ZCUTILS_LOG_OUTPUT_DEFAULT;

static inline void zcu_log_set_level(int loglevel)
{
	zcu_log_level = loglevel;
	setlogmask(LOG_UPTO(loglevel));
}

static inline void zcu_log_set_output(int output)
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

static inline int zcu_log_print(int loglevel, const char *fmt, ...)
{
	va_list args;

#ifndef DEBUG_ZCU_LOG
	if (loglevel == LOG_DEBUG)
		return 0;
#endif

	if (zcu_log_output & ZCUTILS_LOG_OUTPUT_STDOUT
	    && loglevel <= zcu_log_level) {
		va_start(args, fmt);
		vfprintf(stdout, fmt, args);
		fprintf(stdout, "\n");
		va_end(args);
	}

	if (zcu_log_output & ZCUTILS_LOG_OUTPUT_STDERR
	    && loglevel <= zcu_log_level) {
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

static inline void zcu_bt_print()
{
	void *buffer[255];
	char **str;
	int i;
	const int calls = backtrace(buffer, sizeof(buffer) / sizeof(void *));

	backtrace_symbols_fd(buffer, calls, 1);

	str = backtrace_symbols(buffer, calls);
	if (!str) {
		zcu_log_print(LOG_ERR, "No backtrace strings found!");
		exit(EXIT_FAILURE);
	}

	for (i = 0; i < calls; i++)
		zcu_log_print(LOG_ERR, "%s", str[i]);
	free(str);

	exit(EXIT_FAILURE);
}

/****  STRING  ****/

static inline void zcu_str_snprintf(char *strdst, int size, char *strsrc)
{
	for (int i = 0; i < size; i++) {
		strdst[i] = *(strsrc + i);
	}
	strdst[size] = '\0';
}



/****  BUFFER  ****/

#define ZCU_DEF_BUFFER_SIZE		4096
#define EXTRA_SIZE				1024

struct zcu_buffer
{
	int size;
	int next;
	char *data;
};

static inline int zcu_buf_get_size(struct zcu_buffer *buf)
{
	return buf->size;
}

static inline char *zcu_buf_get_next(struct zcu_buffer *buf)
{
	return buf->data + buf->next;
}

static inline int zcu_buf_resize(struct zcu_buffer *buf, int times)
{
	char *pbuf;
	int newsize;

	if (times == 0)
		return 0;

	newsize = buf->size + (times * EXTRA_SIZE) + 1;

	if (!buf->data)
		return 1;

	pbuf = (char *) realloc(buf->data, newsize);
	if (!pbuf)
		return 1;

	buf->data = pbuf;
	buf->size = newsize;
	return 0;
}

static inline int zcu_buf_create(struct zcu_buffer *buf)
{
	buf->size = 0;
	buf->next = 0;

	buf->data = (char *) calloc(1, ZCU_DEF_BUFFER_SIZE);
	if (!buf->data) {
		return 1;
	}

	*buf->data = '\0';
	buf->size = ZCU_DEF_BUFFER_SIZE;
	return 0;
}

static inline int zcu_buf_isempty(struct zcu_buffer *buf)
{
	return (buf->data[0] == 0);
}

static inline char *zcu_buf_get_data(struct zcu_buffer *buf)
{
	return buf->data;
}

static inline int zcu_buf_clean(struct zcu_buffer *buf)
{
	if (buf->data)
		free(buf->data);
	buf->size = 0;
	buf->next = 0;
	return 0;
}

static inline int zcu_buf_reset(struct zcu_buffer *buf)
{
	buf->data[0] = 0;
	buf->next = 0;
	return 0;
}

static inline int
zcu_buf_concat_va(struct zcu_buffer *buf, int len, char *fmt,
		      va_list args)
{
	int times = 0;
	char *pnext;

	if (buf->next + len >= buf->size)
		times = ((buf->next + len - buf->size) / EXTRA_SIZE) + 1;

	if (zcu_buf_resize(buf, times)) {
		zcu_log_print(LOG_ERR,
				  "Error resizing the buffer %d times from a size of %d!",
				  times, buf->size);
		return 1;
	}

	pnext = zcu_buf_get_next(buf);
	vsnprintf(pnext, len + 1, fmt, args);
	buf->next += len;

	return 0;
}

static inline int
zcu_buf_concat(struct zcu_buffer *buf, char *fmt, ...)
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


#endif /* _ZCUTILS_H_ */
