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

#include "stream_locker.h"

LOCKER_STATUS ctl_locker = LOCKER_STATUS::DISABLED;
int ctl_bussy_processes = 0;

void stream_locker_enable()
{
	ctl_locker = LOCKER_STATUS::PENDING;
	while (ctl_bussy_processes != 0) {
		// add sleep?
	}
	ctl_locker = LOCKER_STATUS::ENABLED;
}
void stream_locker_disable()
{
	if (ctl_locker == LOCKER_STATUS::ENABLED)
		ctl_locker = LOCKER_STATUS::DISABLED;
}
void stream_locker_increase()
{
	while (ctl_locker == LOCKER_STATUS::PENDING ||
	       ctl_locker == LOCKER_STATUS::ENABLED) {
	}
	ctl_bussy_processes++;
}
void stream_locker_decrease()
{
	ctl_bussy_processes--;
}
