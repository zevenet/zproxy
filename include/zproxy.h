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

#ifndef _ZPROXY_H_
#define _ZPROXY_H_

#include <stdint.h>
#include <ev.h>

struct zproxy_main {
	struct ev_loop *loop;
	struct ev_io ev_reload_io;
	struct ev_io ev_shutdown_io;
	uint32_t num_conn;
	bool active;
};

extern struct zproxy_main zproxy_main;

int zproxy_cfg_file_reload(void);
int zproxy_cfg_reload(struct zproxy_cfg *cfg);

#endif
