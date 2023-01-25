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

#ifndef _ZPROXY_HTTP_STREAM_H_
#define _ZPROXY_HTTP_STREAM_H_

#include <sys/stat.h>
#include <fcntl.h>
#include <string>
#include <stdarg.h>
#include <vector>
#include <sys/time.h>

#include "config.h"
#include "http_request.h"
#include "http_response.h"
#include "http_log.h"
#include "session.h"
#include "state.h"
#include "counter.h"
#if ENABLE_WAF
#include "waf.h"
#else
#include "waf_dummy.h"
#endif

using namespace http;

/**
 * these are the possible status where
 * a connection changes of pending to established
 */
enum STREAM_STATE {
	UNDEF,            ///< Stats did not increase
	NEW_CONN,         ///< New conn received
	BCK_CONN,         ///< Connecting with a backend
	ESTABLISHED,      ///< Connection established with the backend
};

enum class HTTP_STATE : int {
	ERROR = 0,
	REQ_HEADER_RCV,
	REQ_BODY_RCV,
	RESP_HEADER_RCV,
	RESP_BODY_RCV,
	WAIT_100_CONT,
	TUNNEL,
	CLOSE,
};

/**
 * @class HttpStream http_stream.h "src/http/http_stream.h"
 *
 * @brief The HttpStream class contains both client and backend connections. It
 * also controls the requests and responses. Furthermore, it implements the
 * error replies.
 *
 */
class HttpStream final : public Counter<HttpStream> {
private:
	// it shows the next expected status for http stream
	HTTP_STATE state{ HTTP_STATE::REQ_HEADER_RCV };
	std::vector<HTTP_STATE> state_tracer;
	STREAM_STATE stats_state;

public:
#if CACHE_ENABLED
	time_t current_time;
	std::chrono::steady_clock::time_point prev_time;
#endif
	HttpStream(zproxy_proxy_cfg *listener, const sockaddr_in *client, struct zproxy_http_state *http_state);
	~HttpStream();
	// no copy allowed
	HttpStream(const HttpStream &) = delete;
	HttpStream &operator=(const HttpStream &) = delete;
	/* HttpRequest containing the request sent by the client. */
	HttpRequest request;
	/* HttpResponse containing the response sent by the backend. */
	HttpResponse response;

	/* Config */
	zproxy_proxy_cfg *listener_config{nullptr};
	zproxy_service_cfg *service_config{nullptr};
	zproxy_backend_cfg *backend_config{nullptr};
	/* HTTP should order a reconnect to a new backend if this is set*/
	zproxy_backend_cfg *new_backend{nullptr};
	std::string client_addr {""};
	int client_port {0};
	sessions::Set *session{nullptr};

	bool websocket{false};

	uint32_t stream_id{ 0 };
	int managed_requests{ 0 };

	HTTP_STATE getState()
	{
		return state;
	};
	void setState(HTTP_STATE new_state);
	inline const char *getStateString(const HTTP_STATE _state) const
	{
		const char *res;
		switch(_state)
		{
			case HTTP_STATE::ERROR:
				res = "error";
				break;
			case HTTP_STATE::REQ_HEADER_RCV:
				res = "req_header_rcv";
				break;
			case HTTP_STATE::REQ_BODY_RCV:
				res = "req_body_rcv";
				break;
			case HTTP_STATE::RESP_HEADER_RCV:
				res = "resp_head_rcv";
				break;
			case HTTP_STATE::RESP_BODY_RCV:
				res = "resp_body_rcv";
				break;
			case HTTP_STATE::WAIT_100_CONT:
				res = "wait_100_cont";
				break;
			case HTTP_STATE::TUNNEL:
				res = "tunnel";
				break;
			case HTTP_STATE::CLOSE:
				res = "close";
				break;
			default:
				res = nullptr;
				break;
		}
		return res;
	}

	struct zproxy_http_state *http_state;

	/**
	 * The connection was disrupted or finished and the stream stats
	 * should clean it clears the stream connection depending on the current
	 * status.
	 */
	void clearStats();

	/**
	 * Modify the farm stats changing the connection status.
	 *
	 * @param new_state The stats state to set.
	 * @return On success 1; on failure -1.
	 */
	int setStats(const STREAM_STATE new_state);

	/**
	 * Clears the current stats and set a new state updating the stats.
	 *
	 * @param new_state The next stat state.
	 * @return On success 1; on failure -1.
	 */
	int updateStats(const STREAM_STATE new_state);

	struct zproxy_waf_stream *waf;

	bool isTunnel()
	{
		return (websocket
		// TODO: add pinned backend
		//	|| (backend_config != nullptr && backend_config->pin_connection)
		);
	};
	bool expectNewRequest();
	std::string logTag(const int loglevel, const char *tag = nullptr) const;
	void logSuccess();
	void logComplete();
};

#endif
