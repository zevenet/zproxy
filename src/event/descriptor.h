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

#include "../../zcutils/zcutils.h"
#include "epoll_manager.h"
#include <atomic>

namespace events
{
class Descriptor {
	events::EpollManager *event_manager_{ nullptr };
	std::atomic<events::EVENT_TYPE> current_event{
		events::EVENT_TYPE::NONE
	};
	std::atomic<events::EVENT_GROUP> event_group_{
		events::EVENT_GROUP::NONE
	};

    protected:
	int fd_;

    public:
	Descriptor() : event_manager_(nullptr), fd_(-1)
	{
	}
	virtual ~Descriptor()
	{
		if (event_manager_ != nullptr && fd_ > 0)
			event_manager_->deleteFd(fd_);
	}

	inline void setEventManager(events::EpollManager &event_manager)
	{
		event_manager_ = &event_manager;
	}
	inline bool disableEvents()
	{
		current_event = events::EVENT_TYPE::NONE;
		if (event_manager_ != nullptr && fd_ > 0)
			return event_manager_->deleteFd(fd_);
		return false;
	}

	inline bool enableEvents(events::EpollManager *epoll_manager,
				 events::EVENT_TYPE event_type,
				 events::EVENT_GROUP event_group)
	{
		if (epoll_manager != nullptr && fd_ > 0) {
			current_event = event_type;
			event_manager_ = epoll_manager;
			event_group_ = event_group;
			return event_manager_->addFd(fd_, event_type,
						     event_group_);
		}
		return false;
	}

	inline bool setEvents(events::EVENT_TYPE event_type,
			      events::EVENT_GROUP event_group)
	{
		if (event_manager_ != nullptr && fd_ > 0) {
			current_event = event_type;
			event_group_ = event_group;
			return event_manager_->updateFd(fd_, event_type,
							event_group_);
		}
		return false;
	}

	inline bool setEvent(events::EVENT_TYPE event_type)
	{
		if (event_manager_ != nullptr && fd_ > 0) {
			current_event = event_type;
			return event_manager_->updateFd(fd_, event_type,
							event_group_);
		}
		return false;
	}

	inline bool enableReadEvent(bool one_shot = false)
	{
		if (event_manager_ != nullptr &&
		    current_event != events::EVENT_TYPE::READ && fd_ > 0) {
			auto res =
				current_event == events::EVENT_TYPE::NONE ?
					event_manager_->addFd(
						fd_,
						!one_shot ?
							events::EVENT_TYPE::READ :
							      events::EVENT_TYPE::
								READ_ONESHOT,
						event_group_) :
					      event_manager_->updateFd(
						fd_,
						!one_shot ?
							events::EVENT_TYPE::READ :
							      events::EVENT_TYPE::
								READ_ONESHOT,
						event_group_);
			current_event =
				!one_shot ? events::EVENT_TYPE::READ :
						  events::EVENT_TYPE::READ_ONESHOT;
			return res;
		}
		zcu_log_print(LOG_DEBUG, "%s():%d: InReadModeAlready",
			      __FUNCTION__, __LINE__);
		return false;
	}

	inline bool enableWriteEvent()
	{
		if (event_manager_ != nullptr && fd_ > 0) {
			auto res = event_manager_->updateFd(
				fd_, events::EVENT_TYPE::WRITE, event_group_);
			current_event = events::EVENT_TYPE::WRITE;
			return res;
		}
		zcu_log_print(LOG_DEBUG, "%s():%d: InWriteModeAlready",
			      __FUNCTION__, __LINE__);
		return false;
	}

	inline int getFileDescriptor() const
	{
		return fd_;
	}

	inline void setFileDescriptor(int fd)
	{
		if (fd < 0) {
			zcu_log_print(LOG_DEBUG,
				      "%s():%d: file descriptor not valid",
				      __FUNCTION__, __LINE__);
			return;
		}

		fd_ = fd;
	}
};
} // namespace events
