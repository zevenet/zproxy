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

#ifndef _ZPROXY_MONITOR_H
#define _ZPROXY_MONITOR_H

#include <sys/time.h>

enum zproxy_status {
	ZPROXY_MONITOR_DOWN	= 0,
	ZPROXY_MONITOR_UP,
	ZPROXY_MONITOR_DISABLED,
};

int zproxy_monitor_create(const struct zproxy_cfg *cfg);
int zproxy_monitor_refresh(const struct zproxy_cfg *cfg);
void zproxy_monitor_destroy(void);

struct zproxy_monitor_backend_state {
	enum zproxy_status	status;
	struct timeval		latency;
};

bool zproxy_monitor_backend_state(const struct sockaddr_in *addr,
				  const char *service_name,
				  struct zproxy_monitor_backend_state *state);

int zproxy_monitor_backend_set_enabled(const struct sockaddr_in *addr,
				       const char *service_name, bool enabled);

struct zproxy_monitor_service_state {
	int priority;
};

struct zproxy_monitor_service_state *zproxy_monitor_service_state_lookup(const char *name);

#endif
