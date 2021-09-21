/*
 *    Zevenet zproxy Load Balancer Software License
 *    This file is part of the Zevenet zproxy Load Balancer software package.
 *
 *    Copyright (C) 2019-today ZEVENET SL, Sevilla (Spain)
 *
 *    This program is free software: you can redistribute it and/or modify
 *    it under the terms of the GNU Affero General Public License as
 *    published by the Free Software Foundation, either version 3 of the
 *    License, or any later version.
 *
 *    This program is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *    GNU Affero General Public License for more details.
 *
 *    You should have received a copy of the GNU Affero General Public License
 *    along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 */

#pragma once

#include <string>
#include <stdarg.h>
#include "../config/macro.h"
#include "../connection/backend_connection.h"
#include "../connection/client_connection.h"
#include "../event/epoll_manager.h"
#include "../event/timer_fd.h"
#include "../service/backend.h"
#include "../service/service_manager.h"
#include "../ssl/ssl_connection_manager.h"
#include "http_request.h"
#include "../../zcutils/zcutils.h"
#if WAF_ENABLED
#include <modsecurity/modsecurity.h>
#include <modsecurity/rules.h>
#include <modsecurity/transaction.h>
#endif

enum class STREAM_OPTION : uint32_t {
	NO_OPT = 0x0,
	PINNED_CONNECTION = 0x1,
	H2 = 0x1 << 1,
	H2C = 0x1 << 2,
	WS = 0x1 << 3, //web socket
};

enum class STREAM_STATUS : uint32_t {
	ERROR = 0x0,
	BCK_CONN_PENDING = 0x1,
	BCK_CONN_ERROR = 0x1 << 1,
	BCK_READ_PENDING = 0x1 << 2,
	BCK_WRITE_PENDING = 0x1 << 3,
	CL_READ_PENDING = 0x1 << 4,
	CL_WRITE_PENDING = 0x1 << 5,
	REQUEST_PENDING = 0x1 << 6,
	RESPONSE_PENDING = 0x1 << 7,
	CLOSE_CONNECTION = 0x1 << 8
};

/**
 * @class HttpStream http_stream.h "src/http/http_stream.h"
 *
 * @brief The HttpStream class contains both client and backend connections. It
 * also controls the requests and responses. Furthermore, it implements the
 * error replies.
 *
 */
class HttpStream : public Counter<HttpStream> {
    public:
#if CACHE_ENABLED
	time_t current_time;
	std::chrono::steady_clock::time_point prev_time;
#endif
	HttpStream();
	~HttpStream() final;
	// no copy allowed
	HttpStream(const HttpStream &) = delete;
	HttpStream &operator=(const HttpStream &) = delete;
#if WAF_ENABLED
	//    modsecurity::ModSecurityIntervention *intervention{nullptr};
	modsecurity::Transaction *modsec_transaction{ nullptr };
	std::shared_ptr<modsecurity::Rules> waf_rules{ nullptr };
#endif
	/** Connection between zproxy and the client. */
	ClientConnection client_connection;
	/** Connection between zproxy and the backend. */
	BackendConnection backend_connection;
#if USE_TIMER_FD_TIMEOUT
	/** Timer descriptor used for the stream timeouts. */
	TimerFd timer_fd;
#endif
	/** HttpRequest containing the request sent by the client. */
	HttpRequest request;
	/** HttpResponse containing the response sent by the backend. */
	HttpResponse response;
	uint32_t status{ 0x0 };
	uint32_t options{ 0x0 };
	uint32_t stream_id{ 0 };

	/* sub-string from the URL that was removed in a rewriteurl action */
	std::string rewr_loc_str_ori{ "" };
	/* sub-string from the URL that was added in a rewriteurl action */
	std::string rewr_loc_str_repl{ "" };

	/* Params:
	 *  - string where replace the macro. This same string will be replaced
	 *	- string to replace
	 *  - string to replace length
	 *  - flag to enable or disable the replacement
	 *
	 *  Returns:
	 *		1 if the replacement was applied, 0 in other case
	 *
	*/
	inline int replaceVhostMacro(char *buf, char *ori_str, int ori_len,
				     bool enabled = true) const
	{
		if (!enabled)
			return 0;
		return zcu_str_replace_str(
			buf, ori_str, ori_len, MACRO::VHOST_STR,
			MACRO::VHOST_LEN,
			const_cast<char *>(this->request.virtual_host.data()),
			this->request.virtual_host.length());
	}

	inline bool hasOption(STREAM_OPTION _option) const
	{
		return (options & helper::to_underlying(_option)) != 0u;
	}

	inline bool hasStatus(STREAM_STATUS _status) const
	{
		return (status & helper::to_underlying(_status)) != 0u;
	}

	inline void clearOption(STREAM_OPTION _option)
	{
		options &= ~helper::to_underlying(_option);
	}

	inline void clearStatus(STREAM_STATUS _status)
	{
		status &= ~helper::to_underlying(_status);
	}

	std::shared_ptr<ServiceManager> service_manager;

	static void debugBufferData(const std::string &function, int line,
				    HttpStream *stream, const char *debug_str,
				    const char *data);

	std::string logTag(const char *tag = nullptr);
	void logSuccess();
};

#define streamLogDebug(s, fmt, ...)                                            \
	{                                                                      \
		auto tag = const_cast<HttpStream *>(s)->logTag("debug");       \
		zcu_log_print(LOG_DEBUG, "%s[caller/%s:%d]" fmt, tag.data(),   \
			      __FUNCTION__, __LINE__, ##__VA_ARGS__);          \
	}

#define streamLogMessage(s, fmt, ...)                                          \
	{                                                                      \
		auto tag = const_cast<HttpStream *>(s)->logTag();              \
		zcu_log_print(LOG_NOTICE, "%s " fmt, tag.data(),               \
			      ##__VA_ARGS__);                                  \
	}

#define streamLogRedirect(s, url)                                              \
	{                                                                      \
		auto tag = const_cast<HttpStream *>(s)->logTag("responded");   \
		zcu_log_print(                                                 \
			LOG_INFO,                                              \
			"%s the request \"%s\" was redirected to \"%s\"",      \
			tag.data(),                                            \
			const_cast<HttpStream *>(s)                            \
				->request.http_message_str.data(),             \
			url);                                                  \
	}

#define streamLogError(s, code, code_string, target)                           \
	{                                                                      \
		auto tag = const_cast<HttpStream *>(s)->logTag("error");       \
		auto request_data_len =                                        \
			std::string_view(target.buffer).find('\r');            \
		zcu_log_print(LOG_INFO, "%s e%d %s \"%.*s\"", tag.data(),      \
			      static_cast<int>(code), code_string.data(),      \
			      request_data_len, target.buffer);                \
	}

#define streamLogWaf(s, fmt, ...)                                              \
	{                                                                      \
		auto tag = const_cast<HttpStream *>(s)->logTag("waf");         \
		zcu_log_print(LOG_WARNING, "%s %s", fmt, tag.data(),           \
			      ##__VA_ARGS__);                                  \
	}

#define streamLogNoResponse(s, fmt, ...)                                       \
	{                                                                      \
		auto tag = const_cast<HttpStream *>(s)->logTag("no-response"); \
		zcu_log_print(LOG_NOTICE, "%s " fmt, tag.data(),               \
			      ##__VA_ARGS__);                                  \
	}
