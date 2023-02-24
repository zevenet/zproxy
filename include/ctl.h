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

#ifndef ZPROXY_CTL_H
#define ZPROXY_CTL_H

#include <stdint.h>
#include <ev.h>
#include "list.h"
#include "config.h"

/*
 * ERR_BUF_MAX_SIZE must fit a listener ID (uint32_t), a service name (of size
 * CONFIG_IDENT_MAX maximum) and a backend id (IP-port), plus the error message
 * itself.
 */
#define ERR_BUF_MAX_SIZE CONFIG_IDENT_MAX + 512

/* main control thread. */
#define ZPROXY_CTL_MAIN_PATH		"/tmp/zproxy_ctl.sock"

#ifndef UNIX_PATH_MAX
#define UNIX_PATH_MAX   108
#endif

struct zproxy_ctl_conn {
	struct list_head	list;
	struct ev_io		io;
	struct ev_timer		timer;
	char			buf[4096];
	uint32_t		buf_len;
	int32_t			content_len;
	const struct zproxy_cfg	*cfg;
	int			(*cb)(const struct zproxy_ctl_conn *ctl, const struct zproxy_cfg *cfg);
};

int zproxy_ctl_create(const struct zproxy_cfg *cfg);
void zproxy_ctl_destroy(void);
void zproxy_ctl_refresh(const struct zproxy_cfg *cfg);

struct zproxy_ctl_conn *zproxy_ctl_accept(struct ev_io *io,
		int (*cb)(const struct zproxy_ctl_conn *ctl, const struct zproxy_cfg *cfg));

int ctl_handler_cb(const struct zproxy_ctl_conn *ctl,
		const struct zproxy_cfg *cfg);

#endif
