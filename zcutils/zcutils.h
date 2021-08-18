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
#include <pcreposix.h>
#include <ctype.h>
#include <string.h>
#include <pthread.h>

/****  LOG  ****/

#define ZCUTILS_LOG_OUTPUT_SYSLOG (1 << 0)
#define ZCUTILS_LOG_OUTPUT_STDOUT (1 << 1)
#define ZCUTILS_LOG_OUTPUT_STDERR (1 << 2)

enum zcu_log_output {
	VALUE_LOG_OUTPUT_SYSLOG,
	VALUE_LOG_OUTPUT_STDOUT,
	VALUE_LOG_OUTPUT_STDERR,
	VALUE_LOG_OUTPUT_SYSOUT,
	VALUE_LOG_OUTPUT_SYSERR,
};

#define ZCUTILS_LOG_LEVEL_DEFAULT LOG_NOTICE
#define ZCUTILS_LOG_OUTPUT_DEFAULT ZCUTILS_LOG_OUTPUT_SYSLOG

extern int zcu_log_level;
extern int zcu_log_output;

void zcu_log_set_level(int loglevel);

void zcu_log_set_output(int output);

int zcu_log_print(int loglevel, const char *fmt, ...);

/****  BACKTRACE  ****/

void zcu_bt_print();

/****  STRING  ****/

void zcu_str_snprintf(char *strdst, int size, char *strsrc);

/****  BUFFER  ****/

#define ZCU_DEF_BUFFER_SIZE 4096
#define EXTRA_SIZE 1024

struct zcu_buffer {
	int size;
	int next;
	char *data;
};

int zcu_buf_get_size(struct zcu_buffer *buf);

char *zcu_buf_get_next(struct zcu_buffer *buf);

int zcu_buf_resize(struct zcu_buffer *buf, int times);

int zcu_buf_create(struct zcu_buffer *buf);

int zcu_buf_isempty(struct zcu_buffer *buf);

char *zcu_buf_get_data(struct zcu_buffer *buf);

int zcu_buf_clean(struct zcu_buffer *buf);

int zcu_buf_reset(struct zcu_buffer *buf);

int zcu_buf_concat_va(struct zcu_buffer *buf, int len, char *fmt, va_list args);

int zcu_buf_concat(struct zcu_buffer *buf, char *fmt, ...);

/*
 * It replaces a chain in the original string.
 *    Returns :  1 if the function did some action
 *               0 if it didn't do anything
*/
int zcu_str_replace_regexp(char *buf, const char *ori_str, int ori_len,
			   regex_t *match, char *replace_str);

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
		     int ori_len, const char *match_str, int match_len);

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
			int replace_len);

#endif /* _ZCUTILS_H_ */
