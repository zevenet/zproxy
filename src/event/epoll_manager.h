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

#include <sys/epoll.h>
#include <unistd.h>
#include <mutex>
#include <unordered_map>
#include <vector>
#include "../util/time.h"
#include "../stats/counter.h"

namespace events
{
#define MAX_EPOLL_EVENT 500
#define EPOLL_WAIT_TIMEOUT 250
/** The enum EVENT_GROUP defines the different group types. */
enum class EVENT_GROUP : char {
	/** This group accept connections. */
	ACCEPTOR = 0x1,
	/** This group handles the events of the server. */
	SERVER,
	/** This group handles the events of the client. */
	CLIENT,
	/** This group handles the connection timeout events. */
	CONNECT_TIMEOUT,
	/** This group handles the request timeout events. */
	REQUEST_TIMEOUT,
	/** This group handles the response timeout events. */
	RESPONSE_TIMEOUT,
	/** This group hanfles the signals events from the Operative System. */
	SIGNAL,
	/** This groups handles the maintenance events. */
	MAINTENANCE,
	/** This groups handles the CTL events. */
	CTL_INTERFACE,
	NONE,
};

inline std::string getEventGroup(EVENT_GROUP event)
{
	switch (event) {
	case EVENT_GROUP::ACCEPTOR:
		return "ACCEPTOR";
	case EVENT_GROUP::SERVER:
		return "SERVER";
	case EVENT_GROUP::CLIENT:
		return "CLIENT";
	case EVENT_GROUP::CONNECT_TIMEOUT:
		return "CONNECT_TIMEOUT";
	case EVENT_GROUP::REQUEST_TIMEOUT:
		return "REQUEST_TIMEOUT";
	case EVENT_GROUP::RESPONSE_TIMEOUT:
		return "RESPONSE_TIMEOUT";
	case EVENT_GROUP::SIGNAL:
		return "SIGNAL";
	case EVENT_GROUP::MAINTENANCE:
		return "MAINTENANCE";
	case EVENT_GROUP::CTL_INTERFACE:
		return "CTL_INTERFACE";
	case EVENT_GROUP::NONE:
		return "NONE";
	}
	return "UNDEFINED";
};

/** The enum EVENT_TYPE defines the different event types. */
enum class EVENT_TYPE : uint32_t {
	/** Timeout reached. */
	TIMEOUT = EPOLLIN,
#if SM_HANDLE_ACCEPT
#ifdef EPOLLEXCLUSIVE
	ACCEPT = (EPOLLIN | EPOLLEXCLUSIVE),
#else
	/** Accept the connection. */
	ACCEPT = (EPOLLIN | EPOLLET),
#endif
#else
	/** Accept the connection. */
	ACCEPT = (EPOLLIN | EPOLLET),
#endif
	/** Read from the connection. */
	READ = ((EPOLLIN | EPOLLRDHUP | EPOLLHUP) & ~EPOLLOUT),
	/** Read from the connection. */
	READ_ONESHOT =
		((EPOLLIN | EPOLLET | EPOLLONESHOT | EPOLLRDHUP | EPOLLHUP) &
		 ~EPOLLOUT),
	/** Write to the connection, is always one shot */
	WRITE = (EPOLLOUT | EPOLLONESHOT | EPOLLRDHUP | EPOLLHUP) & ~EPOLLIN,
	/** Read or write event */
	ANY = (EPOLLONESHOT | EPOLLIN | EPOLLET | EPOLLRDHUP | EPOLLHUP |
	       EPOLLOUT),
	/** Connect event */
	CONNECT,
	/** Disconnect event */
	DISCONNECT,
	NONE
};

inline std::string getEventType(EVENT_TYPE event)
{
	switch (event) {
	case EVENT_TYPE::ACCEPT:
		return "ACCEPT";
	case EVENT_TYPE::TIMEOUT:
		return "TIMEOUT";
	case EVENT_TYPE::READ:
		return "READ";
	case EVENT_TYPE::READ_ONESHOT:
		return "READ_ONESHOT";
	case EVENT_TYPE::WRITE:
		return "WRITE";
	case EVENT_TYPE::ANY:
		return "ANY";
	case EVENT_TYPE::CONNECT:
		return "CONNECT";
	case EVENT_TYPE::DISCONNECT:
		return "DISCONNECT";
	case EVENT_TYPE::NONE:
		return "NONE";
	}
	return "UNDEFINED";
};

#if USE_TIMER_FD_TIMEOUT == 0
enum class TIMEOUT_TYPE : uint8_t {
	INACTIVE_TIMEOUT,
	CLIENT_READ_TIMEOUT,
	SERVER_READ_TIMEOUT,
	CLIENT_WRITE_TIMEOUT,
	SERVER_WRITE_TIMEOUT,
};
struct TimeOut : public Counter<TimeOut> {
	TIMEOUT_TYPE type;
	time_t last_seent{ 0 };
	int timeout{ 0 };
};
#endif
// TODO:: Make it static polimorphosm, template<typename Handler>
/**
 * @class EpollManager epoll_manager.h "src/event/epoll_manager.h"
 * @brief The EpollManager is a wrapper class over the EPOLL system. It handles
 * all
 * the operations needed.
 */
class EpollManager {
	int epoll_fd;
#if USE_TIMER_FD_TIMEOUT == 0
	std::unordered_map<int /*fd */, TimeOut> timeouts;
#endif
	std::vector<int> accept_fd_set;
	/** Array of epoll_event. This array contains all the events. */
	epoll_event events[MAX_EPOLL_EVENT];

    protected:
	virtual void HandleEvent(int fd, EVENT_TYPE event_type,
				 EVENT_GROUP event_group) = 0;
	inline void onDisconnectEvent(epoll_event &event);
	inline void onReadEvent(epoll_event &event);
	inline void onWriteEvent(epoll_event &event);
	inline void onConnectEvent(epoll_event &event);

    public:
	EpollManager();

	virtual ~EpollManager();

	/**
   * @brief This function is the core function of the system. It waits for new
   * events
   * and handles them.
   * @param time_out used to wait for events.
   * @return the current number of events.
   */
	int loopOnce(int time_out = -1);

	/**
   * @brief Sets the Listener as a non blocking socket and starts to accept
   * connections.
   * @param listener_fd is the Listener file descriptor
   * @return @c true if everything is ok, @c false if not.
   */

	bool handleAccept(int listener_fd);
	bool stopAccept(int listener_fd);
	/**
   * @brief Adds a new event to the event manager with an unused @p fd.
   *
   * If the @p fd already exists in the event manager, it updates the event with
   * the new @p event_type and @event_group specified.
   *
   * @param fd to add.
   * @param event_type of the new event.
   * @param event_group of the new event.
   * @return @c true if everything is ok, @c false if not.
   */
	bool addFd(int fd, EVENT_TYPE event_type, EVENT_GROUP event_group,
		   int time_out = 0);

	/**
   * @brief Deletes an event to the event manager with the @p fd.
   *
   * If the @p fd already exists in the event manager, it deletes the event. If
   * the @p is not in the event manager, do nothing.
   *
   * @param fd to delete.
   * @return @c true if everything is ok, @c false if not.
   */
	bool deleteFd(int fd);

	/**
   * @brief Deletes an event to the event manager with the @p fd.
   *
   * If the @p fd doesn't exist in the event manager, it adds the event.
   *
   * @param fd to update.
   * @param event_type to update the event.
   * @param event_group to update the event.
   * @return @c true if everything is ok, @c false if not.
   */
	bool updateFd(int fd, EVENT_TYPE event_type, EVENT_GROUP event_group,
		      int time_out = 0);

#if USE_TIMER_FD_TIMEOUT == 0
	void setTimeOut(int fd, TIMEOUT_TYPE type, int timeout_sec);
	void stopTimeOut(int fd);
	void deleteTimeOut(int fd);
	virtual void onTimeOut(int fd, TIMEOUT_TYPE type){};
#endif
};
} // namespace events
