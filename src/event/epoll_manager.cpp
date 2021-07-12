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

#include "epoll_manager.h"
#include "../../zcutils/zcu_network.h"
#include "../../zcutils/zcutils.h"
#include <climits>

namespace events
{
EpollManager::EpollManager() : accept_fd_set()
{
	if ((epoll_fd = epoll_create1(EPOLL_CLOEXEC)) < 0) {
		std::string error = "epoll_create(2) failed: ";
		error += std::strerror(errno);
		zcu_log_print(LOG_ERR, "%s():%d: %s", __FUNCTION__, __LINE__,
			      error.data());
		throw std::system_error(errno, std::system_category());
	}
}

/** Handles the connect events. */
void EpollManager::onConnectEvent(epoll_event &event)
{
#if DEBUG_ZCU_LOG
	zcu_log_print(LOG_DEBUG, "%s():%d: ~~ONConnectEvent fd: %d",
		      __FUNCTION__, __LINE__,
		      static_cast<int>(event.data.u64 >> CHAR_BIT));
#endif
	HandleEvent(static_cast<int>(event.data.u64 >> CHAR_BIT),
		    EVENT_TYPE::CONNECT,
		    static_cast<EVENT_GROUP>(event.data.u64 & 0xff));
}

/** Handles the write events. */
void EpollManager::onWriteEvent(epoll_event &event)
{
#if DEBUG_ZCU_LOG
	zcu_log_print(LOG_DEBUG, "%s():%d: ~~ONWriteEvent fd: %d", __FUNCTION__,
		      __LINE__, static_cast<int>(event.data.u64 >> CHAR_BIT));
#endif
	HandleEvent(static_cast<int>(event.data.u64 >> CHAR_BIT),
		    EVENT_TYPE::WRITE,
		    static_cast<EVENT_GROUP>(event.data.u64 & 0xff));
}

/** Handles the read events. */
void EpollManager::onReadEvent(epoll_event &event)
{
#if DEBUG_ZCU_LOG
	zcu_log_print(LOG_DEBUG, "%s():%d: ~~ONReadEvent fd: %d", __FUNCTION__,
		      __LINE__, static_cast<int>(event.data.u64 >> CHAR_BIT));
#endif
	HandleEvent(static_cast<int>(event.data.u64 >> CHAR_BIT),
		    EVENT_TYPE::READ,
		    static_cast<EVENT_GROUP>(event.data.u64 & 0xff));
}

bool EpollManager::deleteFd(int fd)
{
	if (epoll_ctl(epoll_fd, EPOLL_CTL_DEL, fd, NULL) < 0) {
		if (errno == ENOENT || errno == EBADF || errno == EPERM) {
			//      std::string error = "epoll_ctl(delete) unnecessary. ";
			//      error += std::strerror(errno);
			//        zcu_log_print(LOG_ERR, "%s():%d: %s", __FUNCTION__, __LINE__, error);
			return true;
		}
		std::string error = "epoll_ctl(delete) failed ";
		error += std::strerror(errno);
		zcu_log_print(LOG_ERR, "%s():%d: %s", __FUNCTION__, __LINE__,
			      error.data());
		return false;
	}
#if USE_TIMER_FD_TIMEOUT == 0
	deleteTimeOut(fd);
#endif
	return true;
}

int EpollManager::loopOnce(int time_out)
{
	int fd, i, ev_count = 0;
	ev_count = epoll_wait(epoll_fd, events, MAX_EPOLL_EVENT, time_out);
	Time::updateTime();
#if USE_TIMER_FD_TIMEOUT == 0
	for (auto it = timeouts.begin(); it != timeouts.end();) {
		if (it->second.timeout > 0) {
			if (Time::getTimeSec() - it->second.last_seent >
			    it->second.timeout) {
				it->second.timeout = 0;
				onTimeOut(it->first, it->second.type);
			}
			it++;
		} else {
			it = timeouts.erase(it);
		}
	}
#endif

	if (ev_count <= 0)
		return ev_count;
	for (i = 0; i < ev_count; ++i) {
		fd = static_cast<int>(events[i].data.u64 >> CHAR_BIT);
		auto event_group =
			static_cast<EVENT_GROUP>(events[i].data.u64 & 0xff);
		if ((events[i].events & EPOLLERR) != 0u) {
			HandleEvent(fd, EVENT_TYPE::DISCONNECT, event_group);
			continue;
		} else {
			if ((events[i].events & EPOLLIN) != 0u) {
				if (event_group == EVENT_GROUP::ACCEPTOR) {
					for (auto accept_fd : accept_fd_set) {
						if (fd == accept_fd) {
							onConnectEvent(
								events[i]);
							continue;
						}
					}
				} else {
					onReadEvent(events[i]);
				}
			}
			if ((events[i].events & (EPOLLRDHUP | EPOLLHUP)) !=
			    0u) {
				HandleEvent(fd, EVENT_TYPE::DISCONNECT,
					    event_group);
				continue;
			}
			if ((events[i].events & EPOLLOUT) != 0u) {
				onWriteEvent(events[i]);
			}
		}
	}

	return ev_count;
}

EpollManager::~EpollManager()
{
	::close(epoll_fd);
}

bool EpollManager::handleAccept(int listener_fd)
{
	zcu_log_print(LOG_DEBUG, "%s():%d: adding listener fd: %d",
		      __FUNCTION__, __LINE__, listener_fd);
	accept_fd_set.emplace_back(listener_fd);
	zcu_soc_set_socket_non_blocking(listener_fd);
	return addFd(listener_fd, EVENT_TYPE::ACCEPT, EVENT_GROUP::ACCEPTOR);
}

bool EpollManager::addFd(int fd, EVENT_TYPE event_type, EVENT_GROUP event_group,
			 int time_out)
{
	//  std::lock_guard<std::mutex> loc(epoll_mutex);
	struct epoll_event epevent = {};
	epevent.events = static_cast<uint32_t>(event_type);
	epevent.data.u64 = static_cast<uint64_t>(fd);
	epevent.data.u64 <<= CHAR_BIT;
	epevent.data.u64 |= static_cast<char>(event_group) & 0xff;
	if (epoll_ctl(epoll_fd, EPOLL_CTL_ADD, fd, &epevent) < 0) {
		if (errno == EEXIST) {
			return updateFd(fd, event_type, event_group);
		} else {
			std::string error = "epoll_ctl(add) failed ";
			error += std::strerror(errno);
			zcu_log_print(LOG_ERR, "%s():%d: %s", __FUNCTION__,
				      __LINE__, error.data());
			return false;
		}
	}
#if DEBUG_ZCU_LOG
	zcu_log_print(LOG_DEBUG, "%s():%d: Epoll::AddFD %d To EpollFD: %d",
		      __FUNCTION__, __LINE__, fd, epoll_fd);
#endif
	if (time_out != 0) {
		switch (event_type) {
		case EVENT_TYPE::READ:
		case EVENT_TYPE::READ_ONESHOT:
			setTimeOut(fd,
				   event_group == EVENT_GROUP::SERVER ?
						 TIMEOUT_TYPE::SERVER_READ_TIMEOUT :
						 TIMEOUT_TYPE::CLIENT_READ_TIMEOUT,
				   time_out);
			break;
		case EVENT_TYPE::WRITE:
			setTimeOut(fd,
				   event_group == EVENT_GROUP::SERVER ?
						 TIMEOUT_TYPE::SERVER_WRITE_TIMEOUT :
						 TIMEOUT_TYPE::CLIENT_WRITE_TIMEOUT,
				   time_out);
			break;
		default:
			setTimeOut(fd, TIMEOUT_TYPE::INACTIVE_TIMEOUT,
				   time_out);
		}
	}
	return true;
}

bool EpollManager::updateFd(int fd, EVENT_TYPE event_type,
			    EVENT_GROUP event_group, int time_out)
{
	//  std::lock_guard<std::mutex> loc(epoll_mutex);
#if DEBUG_ZCU_LOG
	zcu_log_print(LOG_DEBUG, "%s():%d: Epoll::UpdateFd %d", __FUNCTION__,
		      __LINE__, fd);
#endif
	struct epoll_event epevent = {};
	epevent.events = static_cast<uint32_t>(event_type);
	epevent.data.u64 = static_cast<uint64_t>(fd);
	epevent.data.u64 <<= CHAR_BIT;
	epevent.data.u64 |= static_cast<char>(event_group) & 0xff;
	if (epoll_ctl(epoll_fd, EPOLL_CTL_MOD, fd, &epevent) < 0) {
		if (errno == ENOENT) {
			std::string error =
				"epoll_ctl(update) failed, fd reopened, adding .. ";
			error += std::strerror(errno);
			zcu_log_print(LOG_ERR, "%s():%d: %s", __FUNCTION__,
				      __LINE__, error.data());
			return addFd(fd, event_type, event_group);
		} else {
			std::string error = "epoll_ctl(update) failed ";
			error += std::strerror(errno);
			zcu_log_print(LOG_ERR, "%s():%d: %s", __FUNCTION__,
				      __LINE__, error.data());
			return false;
		}
	}
	if (time_out != 0) {
		switch (event_type) {
		case EVENT_TYPE::READ:
		case EVENT_TYPE::READ_ONESHOT:
			setTimeOut(fd,
				   event_group == EVENT_GROUP::SERVER ?
						 TIMEOUT_TYPE::SERVER_READ_TIMEOUT :
						 TIMEOUT_TYPE::CLIENT_READ_TIMEOUT,
				   time_out);
			break;
		case EVENT_TYPE::WRITE:
			setTimeOut(fd,
				   event_group == EVENT_GROUP::SERVER ?
						 TIMEOUT_TYPE::SERVER_WRITE_TIMEOUT :
						 TIMEOUT_TYPE::CLIENT_WRITE_TIMEOUT,
				   time_out);
			break;
		default:
			setTimeOut(fd, TIMEOUT_TYPE::INACTIVE_TIMEOUT,
				   time_out);
		}
	}
	return true;
}
bool EpollManager::stopAccept(int listener_fd)
{
	this->deleteFd(listener_fd);
	for (auto it = accept_fd_set.begin(); it != accept_fd_set.end();) {
		if ((*it) == listener_fd) {
			it = accept_fd_set.erase(it);
		} else {
			it++;
		}
	}
	return true;
}

#if USE_TIMER_FD_TIMEOUT == 0
void EpollManager::setTimeOut(int fd, TIMEOUT_TYPE type, int timeout_sec)
{
	if (timeout_sec > 0) {
		auto it = timeouts.find(fd);
		if (it != timeouts.end()) {
			it->second.last_seent = Time::getTimeSec();
			it->second.timeout = timeout_sec;
			it->second.type = type;
		} else {
			TimeOut item;
			item.last_seent = Time::getTimeSec();
			item.timeout = timeout_sec;
			item.type = type;
			timeouts[fd] = item;
		}
	}
}
void EpollManager::stopTimeOut(int fd)
{
	auto it = timeouts.find(fd);
	if (it != timeouts.end()) {
		it->second.timeout = 0;
	}
}
void EpollManager::deleteTimeOut(int fd)
{
	auto it = timeouts.find(fd);
	if (it != timeouts.end()) {
		it->second.timeout = 0;
	}
}
#endif
}; // namespace events
