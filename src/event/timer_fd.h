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

#include "../event/descriptor.h"
#include <sys/timerfd.h>
#include <unistd.h>
#include <cstring>

using namespace events;
class TimerFd : public Descriptor {
	int timeout_ms_;
	bool one_shot_;

    public:
	virtual ~TimerFd();
	explicit TimerFd(int timeout_ms = -1, bool one_shot = true);
	bool set(int timeout_ms = -1, bool one_shot = true);
	bool unset();
	bool isOneShot() const;
	bool isTriggered();
	bool is_set;
	void close();
};
