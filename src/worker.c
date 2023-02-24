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

#include <stdlib.h>
#include <pthread.h>
#include <unistd.h>
#include <sys/eventfd.h>
#include <ev.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <assert.h>
#include "worker.h"
#include "proxy.h"
#include "socket.h"
#include "ctl.h"

static uint64_t worker_genid = 1;
static uint32_t worker_id;
static LIST_HEAD(worker_list);

static void *zproxy_thread_work(void *arg)
{
	struct zproxy_worker *worker = (struct zproxy_worker *)arg;

	while (worker->genid >= worker_genid || worker->num_conn > 0)
		ev_loop(worker->loop, EVRUN_ONCE);

	worker->dead = true;

	return NULL;
}

static void __zproxy_worker_destroy(struct zproxy_worker *worker)
{
	struct zproxy_proxy *proxy, *next;

	assert(worker->genid < worker_genid && worker->num_conn == 0);

	list_for_each_entry_safe(proxy, next, &worker->proxy_list, list)
		zproxy_proxy_destroy(proxy);

	ev_io_stop(worker->loop, &worker->ev_io);
	close(worker->ev_io.fd);
	zproxy_cfg_free(worker->config);
	ev_loop_destroy(worker->loop);
	free(worker);
}

static void zproxy_worker_destroy(struct zproxy_worker *worker)
{
	list_del(&worker->list);
	__zproxy_worker_destroy(worker);
}

void zproxy_worker_cb(struct ev_loop *loop, struct ev_io *io, int events)
{
	struct zproxy_worker *worker;
	uint64_t event;

	if (events & EV_ERROR)
		return;

	worker = container_of(io, struct zproxy_worker, ev_io);

	read(worker->ev_io.fd, &event, sizeof(event));

	/* just read event, do nothing else, generation id will do the rest. */
}

static struct zproxy_worker *__zproxy_worker_create(struct zproxy_cfg *cfg)
{
	struct zproxy_worker *worker;
	int evfd;

	worker = (struct zproxy_worker *)calloc(1, sizeof(*worker));
	if (!worker)
		return NULL;

	++worker_id;
	if (worker_id == 0)
		++worker_id;

	worker->id = worker_id;
	worker->config = zproxy_cfg_get(cfg);
	INIT_LIST_HEAD(&worker->proxy_list);
	INIT_LIST_HEAD(&worker->conn_list);
	INIT_LIST_HEAD(&worker->ctl_list);

	worker->loop = ev_loop_new(EVFLAG_AUTO);
	if (!worker->loop)
		goto err_loop;

	evfd = eventfd(0, EFD_NONBLOCK);
	if (evfd < 0)
		goto err_evfd;

	ev_io_init(&worker->ev_io, zproxy_worker_cb, evfd, EV_READ);

	return worker;
err_evfd:
	ev_loop_destroy(worker->loop);
err_loop:
	free(worker);

	return NULL;
}

int zproxy_workers_create(struct zproxy_cfg *config,
			  struct zproxy_worker **worker_array, int num_workers)
{
	struct zproxy_worker *worker;
	int i, j;

	for (i = 0; i < num_workers; i++) {
		worker = __zproxy_worker_create(config);
		if (!worker)
			goto err_worker;

		worker_array[i] = worker;
        }

	return 0;
err_worker:
	for (j = 0; j < i; j++)
		__zproxy_worker_destroy(worker_array[j]);

	return -1;
}

void zproxy_workers_destroy(struct zproxy_worker **worker_array, int num_workers)
{
	int i;

	for (i = 0; i < num_workers; i++)
		__zproxy_worker_destroy(worker_array[i]);
}

int zproxy_worker_proxy_create(const struct zproxy_proxy_cfg *cfg,
			       struct zproxy_worker *worker)
{
	struct zproxy_proxy *proxy;

	proxy = zproxy_proxy_create(cfg, worker, &http_proxy);
	if (!proxy)
		return -1;

	list_add_tail(&proxy->list, &worker->proxy_list);
	ev_io_start(worker->loop, &proxy->io);

	return 0;
}

void zproxy_worker_proxy_destroy(struct zproxy_worker *worker)
{
	struct zproxy_proxy *proxy, *next;

	list_for_each_entry_safe(proxy, next, &worker->proxy_list, list) {
		list_del(&proxy->list);
		ev_io_stop(worker->loop, &proxy->io);
		zproxy_proxy_destroy(proxy);
	}
}

int zproxy_workers_start(struct zproxy_worker **worker_array, int num_workers)
{
	struct zproxy_worker *worker;
	int i;

	worker_genid++;

	for (i = 0; i < num_workers; i++) {
		worker = worker_array[i];
		worker->genid = worker_genid;
		ev_io_start(worker->loop, &worker->ev_io);

		if (pthread_create(&worker->thread_id, NULL, zproxy_thread_work,
				   worker_array[i]) != 0)
			goto err_thread;

		list_add_tail(&worker->list, &worker_list);
	}
	return 0;

err_thread:
	while (i > 0)
		pthread_cancel(worker_array[i]->thread_id);

	return -1;
}

void zproxy_workers_wait(void)
{
	struct zproxy_worker *worker, *next;

	list_for_each_entry_safe(worker, next, &worker_list, list) {
		pthread_join(worker->thread_id, NULL);
		zproxy_worker_destroy(worker);
	}
}

void zproxy_workers_cleanup(void)
{
	struct zproxy_worker *worker, *next;

	list_for_each_entry_safe(worker, next, &worker_list, list) {
		if (!worker->dead)
			continue;

		pthread_join(worker->thread_id, NULL);
		zproxy_worker_destroy(worker);
	}
}

static void __zproxy_worker_notify(const struct zproxy_worker *worker)
{
	uint64_t event = 1;

	write(worker->ev_io.fd, &event, sizeof(event));
}

void zproxy_worker_notify_update(void)
{
	struct zproxy_worker *worker;

	list_for_each_entry(worker, &worker_list, list)
		__zproxy_worker_notify(worker);
}

void zproxy_worker_notify_shutdown(void)
{
	struct zproxy_worker *worker;

	/* workers know they have to go away */
	worker_genid++;

	list_for_each_entry(worker, &worker_list, list)
		__zproxy_worker_notify(worker);
}
