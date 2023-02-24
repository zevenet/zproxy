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

#ifndef ZPROXY_WORKER_H
#define ZPROXY_WORKER_H

#include <pthread.h>
#include "proxy.h"
#include "list.h"
#include "config.h"

struct zproxy_worker {
	struct list_head	list;
	uint32_t		id;
	pthread_t		thread_id;
	struct ev_loop		*loop;
	struct ev_io		ev_io;
	uint32_t		num_conn;
	uint64_t		genid;
	bool			dead;
	const struct zproxy_cfg	*config;
	struct list_head	proxy_list;
	struct list_head	conn_list;
	struct list_head	ctl_list;
};

int zproxy_workers_create(struct zproxy_cfg *config,
			  struct zproxy_worker **worker_array, int num_workers);
void zproxy_workers_destroy(struct zproxy_worker **worker_array, int num_workers);

int zproxy_worker_proxy_create(const struct zproxy_proxy_cfg *cfg,
                               struct zproxy_worker *worker);
void zproxy_worker_proxy_destroy(struct zproxy_worker *worker);

void zproxy_worker_notify_update(void);
void zproxy_worker_notify_shutdown(void);

int zproxy_workers_start(struct zproxy_worker **worker_array, int num_workers);
void zproxy_workers_wait(void);
void zproxy_workers_cleanup(void);

#endif
