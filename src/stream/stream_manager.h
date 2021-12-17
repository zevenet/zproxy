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
#include "../config/config_data.h"
#include "../event/epoll_manager.h"
#include "../event/timer_fd.h"
#include "../handlers/cache_manager.h"
#include "../handlers/http_manager.h"
#include "../http/http_stream.h"
#include "../service/backend.h"
#include "../service/service_manager.h"
#include "../ssl/ssl_connection_manager.h"
#include "../stats/counter.h"
#include "../../zcutils/zcutils.h"
#if WAF_ENABLED
#include "../handlers/waf.h"
#endif
#include <thread>
#include <unordered_map>
#include <vector>

#if DEBUG_ZCU_LOG

struct StreamWatcher {
	HttpStream *stream{ nullptr };
	StreamWatcher(HttpStream &http_stream) : stream(&http_stream)
	{
		if (stream == nullptr) {
			zcu_log_print(LOG_DEBUG, "%s():%d: IN Null HttpStream",
				      __FUNCTION__, __LINE__);
		} else {
			zcu_log_print(LOG_DEBUG, "%s():%d: IN Stream data",
				      __FUNCTION__, __LINE__);
			showData();
		}
	}
	void showData()
	{
		zcu_log_print(LOG_DEBUG,
			      "%s():%d: \n\tRequest"
			      "\n\t\tBuffer size: %d"
			      "\n\t\tContent-length: %d"
			      "\n\t\tMessage bytes: %d"
			      "\n\t\tBytes left: %d"
			      "\n\tResponse"
			      "\n\t\tBuffer size: %d"
			      "\n\t\tContent-length: %lu"
			      "\n\t\tMessage bytes: %d"
			      "\n\t\tBytes left: %d",
			      __FUNCTION__, __LINE__,
			      stream->client_connection.buffer_size,
			      stream->request.content_length,
			      stream->request.message_length,
			      stream->request.message_bytes_left,
			      stream->backend_connection.buffer_size,
			      stream->response.content_length,
			      stream->response.message_length,
			      stream->response.message_bytes_left);
	}
	virtual ~StreamWatcher()
	{
		if (stream == nullptr) {
			zcu_log_print(LOG_DEBUG, "%s():%d: OUT Null HttpStream",
				      __FUNCTION__, __LINE__);
		} else {
			zcu_log_print(LOG_DEBUG, "%s():%d: OUT Stream data",
				      __FUNCTION__, __LINE__);
			showData();
		}
	}
};

namespace debug__
{
DEFINE_OBJECT_COUNTER(on_client_connect)
DEFINE_OBJECT_COUNTER(on_backend_connect)
DEFINE_OBJECT_COUNTER(on_backend_connect_timeout)
DEFINE_OBJECT_COUNTER(on_backend_disconnect)
DEFINE_OBJECT_COUNTER(on_handshake)
DEFINE_OBJECT_COUNTER(on_request)
DEFINE_OBJECT_COUNTER(on_response)
DEFINE_OBJECT_COUNTER(on_request_timeout)
DEFINE_OBJECT_COUNTER(on_response_timeout)
DEFINE_OBJECT_COUNTER(on_send_request)
DEFINE_OBJECT_COUNTER(on_send_response)
DEFINE_OBJECT_COUNTER(on_client_disconnect)
DEFINE_OBJECT_COUNTER(on_clear_stream)
DEFINE_OBJECT_COUNTER(on_backend_connect_error)
DEFINE_OBJECT_COUNTER(event_client_read)
DEFINE_OBJECT_COUNTER(event_client_disconnect)
DEFINE_OBJECT_COUNTER(event_client_write)
DEFINE_OBJECT_COUNTER(event_backend_read)
DEFINE_OBJECT_COUNTER(event_backend_write)
DEFINE_OBJECT_COUNTER(event_disconnect)
DEFINE_OBJECT_COUNTER(event_backend_disconnect)
DEFINE_OBJECT_COUNTER(event_connect)
DEFINE_OBJECT_COUNTER(event_connect_fail)
} // namespace debug__
#endif

using namespace events;
using namespace http;

/**
 * @class StreamManager StreamManager.h "src/stream/StreamManager.h"
 * @brief Manage the streams and the operations related with them.CtlObserver
 *
 * It is event-driven and in order to accomplish that it inherits from
 * EpollManager. This class is the main core of the project, managing all the
 * operations with the clients and the backends. It is used to manage both HTTP
 * and HTTPS connections.
 */
class StreamManager : public EpollManager,
		      public CtlObserver<ctl::CtlTask, std::string> {
#if HELLO_WORLD_SERVER
	std::string e200 =
		"HTTP/1.1 200 OK\r\nServer: zproxy 1.0\r\nExpires: now\r\nPragma: "
		"no-cache\r\nCache-control: no-cache,no-store\r\nContent-Type: "
		"text/html\r\nContent-Length: 11\r\n\r\nHello World\n";
#endif
#if DEBUG_ZCU_LOG
	int clear_stream{ 0 };
	int clear_timer{ 0 };
	int clear_backend{ 0 };
	int clear_client{ 0 };
#endif
	int worker_id{};
	std::thread worker;
	std::map<int, std::weak_ptr<ServiceManager> > service_manager_set;
	std::atomic<bool> is_running{};
	std::unordered_map<int, HttpStream *> cl_streams_set;
	std::unordered_map<int, HttpStream *> bck_streams_set;
#if USE_TIMER_FD_TIMEOUT
	std::unordered_map<int, HttpStream *> timers_set;
#endif
	void HandleEvent(int fd, EVENT_TYPE event_type,
			 EVENT_GROUP event_group) override;
	void doWork();

    public:
	StreamManager();
	StreamManager(const StreamManager &) = delete;
	~StreamManager() final;

	/**
   * @brief Adds a HttpStream to the stream set of the StreamManager.registerListener
   *
   * If the @p fd is already stored in the set it clears the
   * older one and adds the new one. In addition sets the connect timeout
   * TimerFd.
   *
   * @param fd is the file descriptor to add.
   * @param listener_config of the accepted connection to add.
   */
	void addStream(int fd, std::shared_ptr<ServiceManager> service_manager);

	/**
   * @brief Returns the worker id associated to the StreamManager.
   *
   * As there is a StreamManager attached to each worker, this function gets the
   * worker of this StreamManager.
   *
   * @return worker_id of the StreamManager.
   */
	int getWorkerId();

	/**
   * @brief Initialize the StreamManager.
   *
   * Initialize the StreamManager with the configuration set in the
   * @p listener_config. If the listener_config is a HTTPS one, the
   * StreamManager initializes ssl::SSLConnectionManager too.
   *
   * @param listener_config from the configuration file.
   * @returns @c true if everything is fine.
   */
	bool registerListener(std::weak_ptr<ServiceManager> service_manager);

	/**
   * @brief Starts the StreamManager event manager.
   *
   * Sets the thread name to WORKER_"{worker_id}" and call doWork().
   *
   * @param thread_id_ thread id to call functions on them.
   */
	void start(int thread_id_ = 0);

	/**
   * @brief Stops the StreamManager event manager.
   */
	void stop();

	/**
   * @brief Handles the write event from the backend.
   *
   * It handles HTTP and HTTPS responses. If there is not any error it is
   * going to send a read event to the client or read again from the backend
   * if needed. It modifies the response headers or content when needed calling
   * validateResponse() function.
   *
   * @param fd is the file descriptor from the backend connection used to get
   * the HttpStream.
   */
	inline void onResponseEvent(int fd);

	/**
   * @brief Handles the read event from the client.
   *
   * It handles HTTP and HTTPS requests. If there is not any error it is
   * going to send a write event to the backend or read again from the client
   * if needed. It modifies the request headers or content when needed calling
   * validateRequest() function.
   *
   * @param fd is the file descriptor from the client connection used to get
   * the HttpStream.
   */
	inline void onRequestEvent(int fd);

	/**
   * @brief Handles the connect timeout event.
   *
   * This means the backend connect operation has take too long. It replies a
   * 503 service unavailable error to the client and clearStream() on
   * the HttpStream. Furthermore, it updates the backend status to
   * BACKEND_STATUS::BACKEND_DOWN.
   *
   * @param fd is the file descriptor used to get the HttpStream.
   */
	inline void onConnectTimeoutEvent(int fd);

	/**
   * @brief Handles the response timeout event.
   *
   * This means the backend take too long sending the response. It clearStream()
   * on the HttpStream and replies a 504 Gateway Timeout error to the client.
   *
   * @param fd is the file descriptor used to get the HttpStream.
   */
	inline void onResponseTimeoutEvent(int fd);

	/**
   * @brief Handles the request timeout event.
   *
   * This means the client take too long sending the request. It clearStream()
   * on the HttpStream and do not send any error to the client.
   *
   * @param fd is the file descriptor used to get the HttpStream.
   */
	inline void onRequestTimeoutEvent(int fd);
	inline void onSignalEvent(int fd);
	inline void setStreamBackend(HttpStream *stream);
	/**
   * @brief Writes all the client buffer data to the backend.
   *
   * If there is any error it clearStream() on the HttpStream. If not, it enables
   * the backend read event by calling enableReadEvent().
   *
   * @param stream HttpStream to get the data and the both client and backend
   * connection information.
   */
	inline void onServerWriteEvent(HttpStream *stream);

	/**
   * @brief Writes all the backend buffer data to the client.
   *
   * If there is any error it clearStrea() on the HttpStream. If not, it enables
   * the client read event by calling enableReadEvent().
   *
   * @param stream HttpStream to get the data and the both client and backend
   * connection information.
   */
	inline void onClientWriteEvent(HttpStream *stream);

	/**
   * @brief Clears the HttpStream.
   *
   * It deletes all the timers and events. Finally, deletes the HttpStream.
   *
   * @param stream is the HttpStream to clear.
   */
	void clearStream(HttpStream *stream);

	inline void onServerDisconnect(HttpStream *stream);

	inline void onClientDisconnect(HttpStream *stream);

	/**
   * @brief This function handles the tasks received with the API format.
   *
   * It calls the needed functions depending on the @p task received. The task
   * must be a API formatted request.
   *
   * @param task to handle by the Listener.
   * @return json formatted string with the result of the operation.
   */
	std::string handleTask(ctl::CtlTask &task) override;

	/**
   * @brief Checks if the Listener should handle the @p task.
   *
   * @param task to check.
   * @return true if should handle the task, false if not.
   */
	bool isHandler(ctl::CtlTask &task) override;
	/**
   * @brief Stop gracefully the listener from accepting more connections.
   * @param stop immediately established connections.
   * @return true if should handle the task, false if not.
   */
	void stopListener(int listener_id, bool cut_connection = false);
#if USE_TIMER_FD_TIMEOUT == 0
	void onTimeOut(int fd, TIMEOUT_TYPE type) override;
#endif
	void onBackendConnectionError(HttpStream *stream);
#if WAF_ENABLED
	/**
   * @brief It responds to the client with an HTTP error or redirection depending on the
   * waf disruption
   * @param is the stream which was disrupted
   */
	void wafResponse(HttpStream *stream);
#endif
};
