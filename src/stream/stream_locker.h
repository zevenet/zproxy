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

#ifndef _STREAM_LOCKER_
#define _STREAM_LOCKER_

#include "../../zcutils/zcutils.h"
#include <atomic>

enum class LOCKER_STATUS : int {
	/** The ctl is waiting to apply some action */
	PENDING,
	/** The ctl is applying some action */
	ENABLED,
	/** No actions are pending to apply */
	DISABLED
};

extern std::atomic<LOCKER_STATUS> ctl_locker;
extern std::atomic<int> ctl_bussy_processes;

void stream_locker_enable();
void stream_locker_disable();
void stream_locker_increase();
void stream_locker_decrease();

#endif /* _STREAM_LOCKER_ */
