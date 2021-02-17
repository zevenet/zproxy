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

#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/signalfd.h>
#include <unistd.h>
#include "descriptor.h"
#include "../../zcutils/zcutils.h"

using namespace events;
class SignalFd:public Descriptor
{
      public:
	sigset_t mask
	{
	};
	SignalFd() {
	}
	bool init()
	{
		sigemptyset(&mask);
		sigaddset(&mask, SIGTERM);
		sigaddset(&mask, SIGINT);
		sigaddset(&mask, SIGQUIT);
		sigaddset(&mask, SIGHUP);
		sigaddset(&mask, SIGPIPE);
		/* Block signals so that they aren't handled
		   according to their default dispositions */
		if (sigprocmask(SIG_BLOCK, &mask, NULL) == -1) {
			zcutils_log_print(LOG_ERR, "sigprocmask () failed");
			return false;
		}
		fd_ = signalfd(-1, &mask, 0);
		if (fd_ < 0) {
			zcutils_log_print(LOG_ERR, "sigprocmask () failed");
			return false;
		}
		return true;
	}
	uint32_t getSignal()
	{
		ssize_t s;
		signalfd_siginfo fdsi
		{
		};
		s = read(fd_, &fdsi, sizeof(struct signalfd_siginfo));
		if (s != sizeof(struct signalfd_siginfo)) {
			zcutils_log_print(LOG_ERR, "sigprocmask () failed");
			return false;
		}
		return fdsi.ssi_signo;
	}
};
