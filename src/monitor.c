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

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <ev.h>
#include <netinet/in.h>
#include <errno.h>
#include <sys/time.h>
#include <sys/syslog.h>
#include "zproxy.h"
#include "monitor.h"
#include "socket.h"
#include "list.h"
#include "jhash.h"
#include "config.h"
#include "djb_hash.h"

struct zproxy_monitor_service {
	struct list_head	hlist;
	char                    name[CONFIG_IDENT_MAX];
	uint32_t		use;
	struct list_head	backend_list;

	struct zproxy_monitor_service_state data;
};

/**
 * Backend status monitoring structure.
 */
struct zproxy_monitor_backend {
	struct list_head	hlist;
	struct list_head	list;
	struct ev_io		io;
	struct zproxy_monitor_service *service;
	int                     priority;
	int                     nf_mark;
	bool			stale;
	struct sockaddr_in	addr; ///< Backend's address
	enum zproxy_status	status; ///< Current status of the backend
	struct timeval start_conn_time; ///< Time the connection began.
	struct timeval avg_latency; ///< Average response time in seconds
	struct ev_timer		timer;
	int			conn_timeout; ///< Connection timeout
};

#define HASH_MONITOR_SLOTS	64

static struct {
	struct ev_timer		timer;
	struct list_head	service_hash[HASH_MONITOR_SLOTS];
	struct list_head	backend_hash[HASH_MONITOR_SLOTS];
} zproxy_monitor;

static void zproxy_update_service_prio(struct zproxy_monitor_service *service)
{
	struct zproxy_monitor_backend *backend;
	int new_priority = 1;

	list_for_each_entry(backend, &service->backend_list, list) {
		if (backend->priority > new_priority)
			break;
		if (backend->status != ZPROXY_MONITOR_UP)
			new_priority++;
	}

	service->data.priority = new_priority;
}

static void monitor_backend_update_latency(struct zproxy_monitor_backend *backend)
{
	struct timeval stop, diff, *avg_latency;

	gettimeofday(&stop, NULL);
	timersub(&stop, &backend->start_conn_time, &diff);
	avg_latency = &backend->avg_latency;

	if (!timerisset(avg_latency)) {
		*avg_latency = diff;
	} else {
		timeradd(&diff, avg_latency, avg_latency);
		avg_latency->tv_sec /= 2;
		avg_latency->tv_usec /= 2;
	}
}

static void zproxy_monitor_backend_down(struct zproxy_monitor_backend *backend)
{
	if (backend->status == ZPROXY_MONITOR_UP) {
		syslog(LOG_WARNING, "[svc:%s][bk:%s:%hu] The backend dead (killed)\n",
		       backend->service->name,
		       inet_ntoa(backend->addr.sin_addr),
		       htons(backend->addr.sin_port));
		backend->status = ZPROXY_MONITOR_DOWN;
		zproxy_update_service_prio(backend->service);
	}
}

static void zproxy_monitor_backend_up(struct zproxy_monitor_backend *backend)
{
	monitor_backend_update_latency(backend);
	if (backend->status == ZPROXY_MONITOR_DOWN) {
		syslog(LOG_WARNING, "[bk:%s:%hu] The backend resurrected",
		       inet_ntoa(backend->addr.sin_addr),
		       htons(backend->addr.sin_port));
		backend->status = ZPROXY_MONITOR_UP;
		zproxy_update_service_prio(backend->service);
	}
}

static void zproxy_monitor_backend_cb(struct ev_loop *loop, struct ev_io *io, int events)
{
	struct zproxy_monitor_backend *backend;
	int len, ret;

	backend = container_of(io, struct zproxy_monitor_backend, io);

	if (events & EV_ERROR)
		return;

	len = sizeof(backend->addr);

	ret = connect(backend->io.fd, (struct sockaddr *)&backend->addr, len);
	if (ret < 0 && errno != EISCONN)
		zproxy_monitor_backend_down(backend);
	else
		zproxy_monitor_backend_up(backend);

	ev_timer_stop(zproxy_main.loop, &backend->timer);
	ev_io_stop(loop, &backend->io);
	close(backend->io.fd);
	backend->io.fd = -1;
}

static void zproxy_monitor_backend_timer_cb(struct ev_loop *loop, ev_timer *timer, int events)
{
	struct zproxy_monitor_backend *backend;

	backend = container_of(timer, struct zproxy_monitor_backend, timer);

	syslog(LOG_ERR, "timeout connect to backend %s:%hu\n",
	       inet_ntoa(backend->addr.sin_addr),
	       ntohs(backend->addr.sin_port));

	zproxy_monitor_backend_down(backend);
}

static void zproxy_monitor_check(struct zproxy_monitor_backend *backend)
{
	int sd, ret;

	gettimeofday(&backend->start_conn_time, NULL);
	ev_timer_init(&backend->timer, zproxy_monitor_backend_timer_cb, backend->conn_timeout, 0.);
	ev_timer_start(zproxy_main.loop, &backend->timer);

	ret = zproxy_client_connect(&backend->addr, &sd, backend->nf_mark);
	if (ret < 0 && errno != EINPROGRESS) {
		if (sd >= 0)
			close(sd);

		ev_timer_stop(zproxy_main.loop, &backend->timer);

		zproxy_monitor_backend_down(backend);
		return;
	}

	ev_io_init(&backend->io, zproxy_monitor_backend_cb, sd, EV_WRITE);
	ev_io_start(zproxy_main.loop, &backend->io);
}

static void zproxy_monitor_check_backend(struct zproxy_monitor_backend *backend)
{

	/* pending health chech already in progress. */
	if (ev_is_active(&backend->io))
		return;

	zproxy_monitor_check(backend);
}

static struct zproxy_monitor_service *
__zproxy_monitor_service_lookup(const char *name)
{
	struct zproxy_monitor_service *service;
	uint32_t hash;

	hash = djb_hash(name) % HASH_MONITOR_SLOTS;
	list_for_each_entry(service, &zproxy_monitor.service_hash[hash], hlist) {
		if (!strcmp(service->name, name))
			return service;
	}

	return NULL;
}

struct zproxy_monitor_service_state *
zproxy_monitor_service_state_lookup(const char *name)
{
	struct zproxy_monitor_service *service;

	service = __zproxy_monitor_service_lookup(name);
	if (!service)
		return NULL;

	return &service->data;
}

static struct zproxy_monitor_service *
zproxy_monitor_service(const struct zproxy_service_cfg *service_cfg)
{
	struct zproxy_monitor_service *service;
	uint32_t hash;

	service = (struct zproxy_monitor_service *)calloc(1, sizeof(*service));
	if (!service)
		return NULL;

	strncpy(service->name, service_cfg->name, CONFIG_IDENT_MAX);
	service->data.priority = 1;
	INIT_LIST_HEAD(&service->backend_list);

	hash = djb_hash(service->name) % HASH_MONITOR_SLOTS;
	list_add_tail(&service->hlist, &zproxy_monitor.service_hash[hash]);

	return service;
}

static void zproxy_monitor_service_destroy(struct zproxy_monitor_service *service)
{
	list_del(&service->hlist);
	free(service);
}

static void zproxy_monitor_backend_destroy(struct zproxy_monitor_backend *backend)
{
	list_del(&backend->hlist);
	list_del(&backend->list);
	ev_io_stop(zproxy_main.loop, &backend->io);
	if (backend->io.fd >= 0)
		close(backend->io.fd);

	if (--backend->service->use == 0)
		zproxy_monitor_service_destroy(backend->service);

	ev_timer_stop(zproxy_main.loop, &backend->timer);
	free(backend);
}

static void zproxy_monitor_timer_cb(struct ev_loop *loop, ev_timer *timer, int events)
{
	struct zproxy_monitor_backend *backend, *next;
	int i;

	for (i = 0; i < HASH_MONITOR_SLOTS; i++) {
		list_for_each_entry_safe(backend, next, &zproxy_monitor.backend_hash[i], hlist) {
			if (backend->stale) {
				syslog(LOG_INFO, "backend %s:%d not used anymore after reload",
				       inet_ntoa(backend->addr.sin_addr),
				       htons(backend->addr.sin_port));
				zproxy_monitor_backend_destroy(backend);
				continue;
			}
			if (backend->status == ZPROXY_MONITOR_DISABLED)
				continue;
			zproxy_monitor_check_backend(backend);
		}
	}
}

/* zproxy_update_service_prio() needs backends to be ordered by priority. */
static void zproxy_monitor_service_add_backend(struct zproxy_monitor_backend *new_backend,
					       struct zproxy_monitor_service *service)
{
	struct zproxy_monitor_backend *backend;

	list_for_each_entry(backend, &service->backend_list, list) {
		if (new_backend->priority < backend->priority) {
			list_add_tail(&new_backend->list, &backend->list);
			return;
		}
	}

	list_add_tail(&new_backend->list, &service->backend_list);
}

static void zproxy_monitor_backend_update(const struct zproxy_backend_cfg *backend_cfg,
					  struct zproxy_monitor_backend *backend)
{
	backend->priority = backend_cfg->priority;
	backend->nf_mark = backend_cfg->nf_mark;
	backend->stale = false;
}

static int zproxy_monitor_backend(const struct zproxy_backend_cfg *backend_cfg,
				  struct zproxy_monitor_service *service)
{
	struct zproxy_monitor_backend *backend;
	uint32_t hash;

	backend = (struct zproxy_monitor_backend *)
			calloc(1, sizeof(struct zproxy_monitor_backend));
	if (!backend)
		return -1;

	service->use++;
	backend->service = service;
	backend->addr = backend_cfg->runtime.addr;
	backend->priority = backend_cfg->priority;
	backend->nf_mark = backend_cfg->nf_mark;
	backend->status = ZPROXY_MONITOR_UP;
	backend->stale = false;
	backend->conn_timeout = backend_cfg->timer.connect;

	zproxy_monitor_service_add_backend(backend, service);

	hash = jhash_2words(backend->addr.sin_addr.s_addr,
			    backend->addr.sin_port, 0) % HASH_MONITOR_SLOTS;
	list_add_tail(&backend->hlist, &zproxy_monitor.backend_hash[hash]);

	zproxy_monitor_check(backend);

	return 0;
}

static struct zproxy_monitor_backend *
__zproxy_monitor_backend_lookup(const struct sockaddr_in *addr,
				const char *service_name)
{
	struct zproxy_monitor_backend *backend;
	uint32_t hash;

	hash = jhash_2words(addr->sin_addr.s_addr, addr->sin_port, 0) % HASH_MONITOR_SLOTS;
	list_for_each_entry(backend, &zproxy_monitor.backend_hash[hash], hlist) {
		if (backend->addr.sin_addr.s_addr == addr->sin_addr.s_addr &&
		    backend->addr.sin_port == addr->sin_port &&
		    !strcmp(backend->service->name, service_name))
			return backend;
	}

	return NULL;
}

bool zproxy_monitor_backend_state(const struct sockaddr_in *addr,
				  const char *service_name,
				  struct zproxy_monitor_backend_state *state)
{
	struct zproxy_monitor_backend *backend;

	backend = __zproxy_monitor_backend_lookup(addr, service_name);
	if (!backend)
		return false;

	state->status = backend->status;
	state->latency = backend->avg_latency;

	return true;
}

int zproxy_monitor_backend_set_enabled(const struct sockaddr_in *addr,
				       const char *service_name,
				       bool enabled)
{
	struct zproxy_monitor_backend *backend;

	backend = __zproxy_monitor_backend_lookup(addr, service_name);
	if (!backend)
		return -1;

	if (!enabled && backend->status != ZPROXY_MONITOR_DISABLED) {
		backend->status = ZPROXY_MONITOR_DISABLED;
		timerclear(&backend->avg_latency);
		zproxy_update_service_prio(backend->service);
	} else if (enabled && backend->status == ZPROXY_MONITOR_DISABLED) {
		backend->status = ZPROXY_MONITOR_DOWN;
		zproxy_monitor_check_backend(backend);
	}

	return 1;
}

static int zproxy_monitor_backend_init(const struct zproxy_cfg *cfg)
{
	struct zproxy_monitor_service *service;
	struct zproxy_service_cfg *service_cfg;
	struct zproxy_backend_cfg *backend_cfg;
	struct zproxy_monitor_backend *backend;
	struct zproxy_proxy_cfg *proxy_cfg;

	list_for_each_entry(proxy_cfg, &cfg->proxy_list, list) {
		list_for_each_entry(service_cfg, &proxy_cfg->service_list, list) {
			service = __zproxy_monitor_service_lookup(service_cfg->name);
			if (!service) {
				service = zproxy_monitor_service(service_cfg);
				if (!service)
					return -1;
			}

			list_for_each_entry(backend_cfg, &service_cfg->backend_list, list) {
				backend = __zproxy_monitor_backend_lookup(&backend_cfg->runtime.addr,
									  service_cfg->name);
				if (!backend) {
					zproxy_monitor_backend(backend_cfg, service);
					continue;
				}

				zproxy_monitor_backend_update(backend_cfg, backend);
			}
		}
	}

	return 0;
}

int zproxy_monitor_create(const struct zproxy_cfg *cfg)
{
	int i;

	ev_init(&zproxy_monitor.timer, zproxy_monitor_timer_cb);
	zproxy_monitor.timer.repeat = cfg->timer.maintenance;
	ev_timer_again(zproxy_main.loop, &zproxy_monitor.timer);

	for (i = 0; i < HASH_MONITOR_SLOTS; i++) {
		INIT_LIST_HEAD(&zproxy_monitor.service_hash[i]);
		INIT_LIST_HEAD(&zproxy_monitor.backend_hash[i]);
	}

	if (zproxy_monitor_backend_init(cfg) < 0)
		return -1;

	return 0;
}

static void zproxy_monitor_backend_stale(void)
{
	struct zproxy_monitor_backend *backend;
	int i;

	for (i = 0; i < HASH_MONITOR_SLOTS; i++) {
		list_for_each_entry(backend, &zproxy_monitor.backend_hash[i], hlist)
			backend->stale = true;
	}
}

int zproxy_monitor_refresh(const struct zproxy_cfg *cfg)
{
	zproxy_monitor_backend_stale();

	if (zproxy_monitor_backend_init(cfg) < 0)
		return -1;

	return 0;
}

void zproxy_monitor_destroy(void)
{
	struct zproxy_monitor_backend *backend, *next;
	struct zproxy_monitor_service *service, *s_next;
	int i;

	for (i = 0; i < HASH_MONITOR_SLOTS; i++) {
		list_for_each_entry_safe(backend, next, &zproxy_monitor.backend_hash[i], hlist)
			zproxy_monitor_backend_destroy(backend);
	}

	for (i = 0; i < HASH_MONITOR_SLOTS; i++) {
		list_for_each_entry_safe(service, s_next, &zproxy_monitor.service_hash[i], hlist)
			zproxy_monitor_service_destroy(service);
	}

	ev_timer_stop(zproxy_main.loop, &zproxy_monitor.timer);
}
