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

#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ev.h>
#include <assert.h>
#include <pthread.h>
#include <sys/syslog.h>

#include "config.h"
#include "zcu_log.h"
#include "zproxy.h"
#include "state.h"
#include "list.h"
#include "session.h"
#include "proxy.h"

struct zproxy_backend_state {
	struct list_head       list;
	char                   id[CONFIG_IDENT_MAX];
	struct zproxy_stats backend_stats;
};

struct zproxy_service_state {
	struct list_head       list;
	char                   name[CONFIG_IDENT_MAX];
	struct list_head       backends;
	struct zproxy_sessions *sessions;
};

static LIST_HEAD(state_list);
static pthread_mutex_t list_mutex = PTHREAD_RECURSIVE_MUTEX_INITIALIZER_NP;

static struct zproxy_backend_state *
zproxy_state_backend_lookup(const struct list_head *backend_list,
			    const char *backend_id)
{
	struct zproxy_backend_state *backend_state;

	list_for_each_entry(backend_state, backend_list, list) {
		if (strcmp(backend_state->id, backend_id) == 0)
			return backend_state;
	}

	return NULL;
}

static struct zproxy_service_state *
zproxy_state_service_lookup(const struct list_head *service_list,
			    const char *name)
{
	struct zproxy_service_state *service_state;

	list_for_each_entry(service_state, service_list, list) {
		if (strcmp(name, service_state->name) == 0)
			return service_state;
	}

	return NULL;
}

static struct zproxy_http_state *_zproxy_state_lookup(uint32_t proxy_id)
{
	struct zproxy_http_state *state;

	list_for_each_entry(state, &state_list, list) {
		if(state->proxy_id == proxy_id) {
			return state;
		}
	}

	return NULL;
}

struct zproxy_http_state *zproxy_state_lookup(uint32_t proxy_id)
{
	struct zproxy_http_state *state;

	pthread_mutex_lock(&list_mutex);
	state = _zproxy_state_lookup(proxy_id);
	state->refcnt++;
	pthread_mutex_unlock(&list_mutex);

	return state;
}

void zproxy_states_lock(void)
{
	pthread_mutex_lock(&list_mutex);
}

void zproxy_states_unlock(void)
{
	pthread_mutex_unlock(&list_mutex);
}

static void zproxy_state_maintenance_cb(struct ev_loop *loop, ev_timer *timer,
					int events)
{
	long counter = COUNTER_SESSIONS; // avoid CPU abuse of garbage recollector
	struct zproxy_http_state *state;
	struct zproxy_service_state *service_state;

	ev_timer_stop(loop, timer);

	pthread_mutex_lock(&list_mutex);
	state = container_of(timer, struct zproxy_http_state, timer);

	list_for_each_entry(service_state, &state->services, list) {
		counter -= service_state->sessions->size;
		zproxy_sessions_remove_expired(service_state->sessions);
		if (counter<=0)
			break;
	}
	pthread_mutex_unlock(&list_mutex);

	ev_timer_again(loop, timer);
}

struct zproxy_stats *
zproxy_stats_backend_get(const struct zproxy_http_state *http_state,
			 const struct zproxy_backend_cfg *backend_cfg)
{
	const struct zproxy_service_state *service_state =
		zproxy_state_service_lookup(&http_state->services, backend_cfg->service->name);
	if (!service_state)
		return NULL;
	struct zproxy_backend_state *backend_state =
		zproxy_state_backend_lookup(&service_state->backends, backend_cfg->runtime.id);
	if (!backend_state)
		return NULL;

	return &backend_state->backend_stats;
}

static int __zproxy_stats_backend_get_pending(const struct zproxy_http_state *http_state,
					      const struct zproxy_backend_cfg *backend_cfg)
{
	const struct zproxy_stats *backend_stats =
		zproxy_stats_backend_get(http_state, backend_cfg);
	if (!backend_stats)
		return -1;

	return backend_stats->conn_pending;
}

static int __zproxy_stats_backend_get_established(const struct zproxy_http_state *http_state,
						  const struct zproxy_backend_cfg *backend_cfg)
{
	const struct zproxy_stats *backend_stats =
		zproxy_stats_backend_get(http_state, backend_cfg);
	if (!backend_stats)
		return -1;

	return backend_stats->conn_established;
}

int zproxy_stats_backend_get_established(const struct zproxy_http_state *http_state,
					 const struct zproxy_backend_cfg *backend_cfg)
{
	return __zproxy_stats_backend_get_pending(http_state, backend_cfg) +
	       __zproxy_stats_backend_get_established(http_state, backend_cfg);
}

int zproxy_stats_backend_inc_code(const struct zproxy_http_state *http_state,
				  const struct zproxy_backend_cfg *backend_cfg,
				  const int code)
{
	struct zproxy_stats *backend_stats =
		zproxy_stats_backend_get(http_state, backend_cfg);
	if (!backend_stats)
		return -1;

	if(code >= 500)
		backend_stats->http_5xx_hits++;
	else if(code >= 400)
		backend_stats->http_4xx_hits++;
	else if(code >= 300)
		backend_stats->http_3xx_hits++;
	else if(code >= 200)
		backend_stats->http_2xx_hits++;
	else
		return -1;

	return 1;
}

void zproxy_stats_backend_inc_conn_established(const struct zproxy_http_state *http_state,
					       const struct zproxy_backend_cfg *backend_cfg)
{
	struct zproxy_stats *backend_stats =
		zproxy_stats_backend_get(http_state, backend_cfg);
	if (!backend_stats)
		return;

	backend_stats->conn_established++;
}

void zproxy_stats_backend_dec_conn_established(const struct zproxy_http_state *http_state,
					       const struct zproxy_backend_cfg *backend_cfg)
{
	struct zproxy_stats *backend_stats =
		zproxy_stats_backend_get(http_state, backend_cfg);
	if (!backend_stats)
		return;

	backend_stats->conn_established--;
}

int zproxy_stats_backend_inc_conn_pending(const struct zproxy_http_state *http_state,
					  const struct zproxy_backend_cfg *backend_cfg)
{
	struct zproxy_stats *backend_stats =
		zproxy_stats_backend_get(http_state, backend_cfg);
	if (!backend_stats)
		return -1;

	return ++backend_stats->conn_pending;
}

int zproxy_stats_backend_dec_conn_pending(const struct zproxy_http_state *http_state,
					  const struct zproxy_backend_cfg *backend_cfg)
{
	struct zproxy_stats *backend_stats =
		zproxy_stats_backend_get(http_state, backend_cfg);
	if (!backend_stats)
		return -1;

	return --backend_stats->conn_pending;
}

static int zproxy_state_backend_init(const struct zproxy_service_cfg *service_cfg,
				      struct list_head *backend_list)
{
	struct zproxy_backend_cfg *backend;
	struct zproxy_backend_state *backend_state;

	list_for_each_entry(backend, &service_cfg->backend_list, list) {
		backend_state = zproxy_state_backend_lookup(backend_list,
							    backend->runtime.id);
		if (backend_state)
			continue;

		backend_state = (struct zproxy_backend_state*)
			calloc(1, sizeof(struct zproxy_backend_state));
		if (!backend_state) {
			zcu_log_print(LOG_ERR,
				      "Couldn't create backend state (OOM)");
			return -1;
		}

		snprintf(backend_state->id, CONFIG_IDENT_MAX, "%s",
			 backend->runtime.id);
		list_add_tail(&backend_state->list, backend_list);
	}

	return 1;
}

int zproxy_state_backend_add(const struct zproxy_http_state *http_state,
			      const struct zproxy_backend_cfg *backend)
{
	struct zproxy_service_state *service_state;
	const char *service_name = backend->service->name;
	struct zproxy_backend_state *backend_state;

	pthread_mutex_lock(&list_mutex);
	service_state = zproxy_state_service_lookup(&http_state->services,
						    service_name);
	if (!service_state) {
		zcu_log_print(LOG_ERR, "Couldn't find service state %s.",
			      service_name);
		return -1;
	}

	backend_state = zproxy_state_backend_lookup(&service_state->backends,
						    backend->runtime.id);
	if (backend_state) {
		zcu_log_print(LOG_INFO, "Backend %s already exists.",
			      backend->runtime.id);
		pthread_mutex_unlock(&list_mutex);
		return 1;
	}

	backend_state = (struct zproxy_backend_state*)
		calloc(1, sizeof(struct zproxy_backend_state));
	if (!backend_state) {
		zcu_log_print(LOG_ERR, "Couldn't create backend (OOM).");
		return -1;
	}

	snprintf(backend_state->id, CONFIG_IDENT_MAX, "%s",
		 backend->runtime.id);
	list_add_tail(&backend_state->list, &service_state->backends);
	pthread_mutex_unlock(&list_mutex);

	return 1;
}

struct zproxy_http_state *
zproxy_state_init(const struct zproxy_proxy_cfg *proxy)
{
	struct zproxy_http_state *state = nullptr;
	struct zproxy_service_state *service_state;
	struct zproxy_service_cfg *service_cfg;

	pthread_mutex_lock(&list_mutex);
	state = _zproxy_state_lookup(proxy->id);
	if (state) {
		state->refcnt++;
	} else {
		state = (struct zproxy_http_state*)
			calloc(1, sizeof(struct zproxy_http_state));
		if (!state) {
			pthread_mutex_unlock(&list_mutex);
			return NULL;
		}

		state->proxy_id = proxy->id;
		INIT_LIST_HEAD(&state->services);

		// Garbage collector for expired sessions
		ev_init(&state->timer, zproxy_state_maintenance_cb);
		state->timer.repeat = TIMEOUT_SESSIONS;
		ev_timer_again(zproxy_main.loop, &state->timer);

		list_add_tail(&state->list, &state_list);
	}

	list_for_each_entry(service_cfg, &proxy->service_list, list) {
		service_state = zproxy_state_service_lookup(&state->services,
							    service_cfg->name);
		if (!service_state) {
			service_state = (struct zproxy_service_state*)
				calloc(1, sizeof(struct zproxy_service_state));
			if (!service_state) {
				pthread_mutex_unlock(&list_mutex);
				return NULL;
			}
			service_state->sessions =
				zproxy_sessions_alloc(service_cfg);
			snprintf(service_state->name, CONFIG_IDENT_MAX, "%s",
				 service_cfg->name);
			INIT_LIST_HEAD(&service_state->backends);
			list_add_tail(&service_state->list, &state->services);
		}

		if (zproxy_state_backend_init(service_cfg,
					      &service_state->backends) < 0) {
			return NULL;
		}
	}
	pthread_mutex_unlock(&list_mutex);

	return state;
}

static void zproxy_backend_state_purge(struct zproxy_backend_state *backend_state)
{
	list_del(&backend_state->list);
	free(backend_state);
}

static void zproxy_service_state_purge(struct zproxy_service_state *service_state)
{
	struct zproxy_backend_state *backend_state, *next;

	zproxy_sessions_free(service_state->sessions);
	list_for_each_entry_safe(backend_state, next, &service_state->backends, list)
		zproxy_backend_state_purge(backend_state);
	list_del(&service_state->list);
	free(service_state);
}

static void zproxy_proxy_state_purge(struct zproxy_http_state *state)
{
	struct zproxy_service_state *service_state, *next;

	if (--state->refcnt > 0)
		return;

	list_for_each_entry_safe(service_state, next, &state->services, list)
		zproxy_service_state_purge(service_state);

	ev_timer_stop(zproxy_main.loop, &state->timer);
	list_del(&state->list);
	free(state);
}

void zproxy_state_purge(uint32_t proxy_id)
{
	struct zproxy_http_state *state;

	pthread_mutex_lock(&list_mutex);
	state = _zproxy_state_lookup(proxy_id);
	if (state)
		zproxy_proxy_state_purge(state);
	pthread_mutex_unlock(&list_mutex);
}

void zproxy_state_free(struct zproxy_http_state **http_state)
{
	pthread_mutex_unlock(&list_mutex);
	zproxy_proxy_state_purge(*http_state);
	*http_state = NULL;
	pthread_mutex_unlock(&list_mutex);
}

static void zproxy_state_cfg_service_update(const struct zproxy_service_cfg *service,
					    struct zproxy_service_state *service_state)
{
	const struct zproxy_backend_cfg *backend;
	struct zproxy_backend_state *backend_state, *next;
	bool found;

	zproxy_session_delete_old_backends(service, service_state->sessions);

	list_for_each_entry_safe(backend_state, next, &service_state->backends,
				 list) {
		found = false;
		list_for_each_entry(backend, &service->backend_list, list) {
			if (strcmp(backend->runtime.id, backend_state->id) == 0) {
				found = true;
				break;
			}
		}

		if (!found)
			zproxy_backend_state_purge(backend_state);
	}
}

static void zproxy_state_cfg_proxy_update(const struct zproxy_proxy_cfg *proxy,
					  struct zproxy_http_state *http_state)
{
	const struct zproxy_service_cfg *service;
	struct zproxy_service_state *service_state, *next;
	bool found;

	list_for_each_entry_safe(service_state, next, &http_state->services,
				 list) {
		found = false;
		list_for_each_entry(service, &proxy->service_list, list) {
			if (strcmp(service->name, service_state->name) == 0) {
				found = true;
				break;
			}
		}

		if (!found)
			zproxy_service_state_purge(service_state);
		else
			zproxy_state_cfg_service_update(service, service_state);
	}
}

void zproxy_state_cfg_update(struct zproxy_cfg *cfg)
{
	const struct zproxy_proxy_cfg *proxy;
	struct zproxy_http_state *http_state, *next_state;
	int found;

	pthread_mutex_lock(&list_mutex);
	list_for_each_entry_safe(http_state, next_state, &state_list, list) {
		found = 0;
		list_for_each_entry(proxy, &cfg->proxy_list, list) {
			if (proxy->id == http_state->proxy_id) {
				found = 1;
				break;
			}
		}

		if (!found)
			zproxy_proxy_state_purge(http_state);
		else
			zproxy_state_cfg_proxy_update(proxy, http_state);
	}
	pthread_mutex_unlock(&list_mutex);
}

struct zproxy_sessions *
zproxy_state_get_service_sessions(const char *service_name,
				  const struct list_head *service_list)
{
	struct zproxy_service_state *service_state;
	list_for_each_entry(service_state, service_list, list) {
		if (strcmp(service_state->name, service_name) == 0)
			return service_state->sessions;
	}

	return NULL;
}
