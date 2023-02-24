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

#ifndef _ZPROXY_HTTP_LOG_H_
#define _ZPROXY_HTTP_LOG_H_

#include "zcu_log.h"


#define streamLogDebug(s, fmt, ...)                                            \
	{                                                                      \
		auto tag = const_cast<HttpStream *>(s)->logTag(LOG_DEBUG, "debug");       \
		zcu_log_print_th(LOG_DEBUG, "%s[caller/%s:%d]" fmt, tag.data(),   \
			      __FUNCTION__, __LINE__, ##__VA_ARGS__);          \
	}

#define streamLogMessage(s, fmt, ...)                                          \
	{                                                                      \
		auto tag = const_cast<HttpStream *>(s)->logTag(LOG_NOTICE);              \
		zcu_log_print_th(LOG_NOTICE, "%s " fmt, tag.data(),               \
			      ##__VA_ARGS__);                                  \
	}

#define streamLogRedirect(s, url)                                              \
	{                                                                      \
		auto tag = const_cast<HttpStream *>(s)->logTag(LOG_INFO, "responded");   \
		zcu_log_print_th(                                                 \
			LOG_INFO,                                              \
			"%s the request \"%s\" was redirected to \"%s\"",      \
			tag.data(),                                            \
			const_cast<HttpStream *>(s)                            \
				->request.http_message_str.data(),             \
			url);                                                  \
	}

// TODO: perhaps change LOG_INFO to LOG_ERR or at least LOG_WARNING
#define streamLogError(s, code, code_string)                           \
	{                                                                      \
		auto tag = const_cast<HttpStream *>(s)->logTag(LOG_INFO, "error");       \
		auto req = const_cast<HttpStream *>(s)->request;               \
		auto host = req.virtual_host;                                  \
		zcu_log_print_th(LOG_INFO, "%s e%d %s \"Host:%s\" \"%s\"",        \
			      tag.data(), static_cast<int>(code),              \
			      code_string.data(), host.data(),                 \
				  req.http_message_str.data());                \
	}

#define streamLogWaf(s, fmt, ...)                                              \
	{                                                                      \
		auto tag = const_cast<HttpStream *>(s)->logTag(LOG_WARNING, "waf");         \
		zcu_log_print_th(LOG_WARNING, "%s" fmt, tag.data(),               \
			      ##__VA_ARGS__);                                  \
	}

#define streamLogNoResponse(s, fmt, ...)                                       \
	{                                                                      \
		auto tag = const_cast<HttpStream *>(s)->logTag(LOG_NOTICE, "no-response"); \
		zcu_log_print_th(LOG_NOTICE, "%s " fmt, tag.data(),               \
			      ##__VA_ARGS__);                                  \
	}

#define streamLogState(s, fmt, ...)                                            \
	{                                                                      \
		auto tag = const_cast<HttpStream *>(s)->logTag(LOG_DEBUG, "State");       \
		zcu_log_print_th(LOG_DEBUG, "%s " fmt, tag.data(),                \
			      ##__VA_ARGS__);                                  \
	}

#endif
