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

#include <ev.h>
#include <assert.h>
#include <pthread.h>

#include "zproxy.h"
#include "state.h"
#include "list.h"
#include "zcu_time.h"
#include "session.h"
#include "proxy.h"

static LIST_HEAD(state_list);
static pthread_mutex_t list_mutex = PTHREAD_RECURSIVE_MUTEX_INITIALIZER_NP;

static void zproxy_state_maintenance_cb(struct ev_loop *loop, ev_timer *timer, int events)
{
	unsigned long counter = COUNTER_SESSIONS; // avoid CPU abuse of garbage recollector
	struct zproxy_http_state *state;

	Time::updateTime();
	ev_timer_stop(loop, timer);

	pthread_mutex_lock(&list_mutex);
	state = container_of(timer, struct zproxy_http_state, timer);

	for (auto & service : state->services) {
		counter -= service.second->sessions.sessions_set.size();
		service.second->sessions.removeExpiredSessions();
		if (counter<=0)
			break;
	}
	pthread_mutex_unlock(&list_mutex);

	ev_timer_again(loop, timer);
}

struct zproxy_stats *zproxy_stats_backend_get(
		const struct zproxy_http_state *http_state,
		const struct zproxy_backend_cfg *backend_cfg)
{
	return &http_state->services.at(backend_cfg->service->name)
		->backends.at(backend_cfg->runtime.id)
		->backend_stats;
}

int zproxy_stats_backend_get_established(
		const struct zproxy_http_state *http_state,
		const struct zproxy_backend_cfg *backend_cfg)
{
	return http_state->services.at(backend_cfg->service->name)
		->backends.at(backend_cfg->runtime.id)
		->backend_stats.conn_established;
}

int zproxy_stats_backend_inc_code(struct zproxy_http_state *http_state,
		const struct zproxy_backend_cfg *backend_cfg,
		int code)
{
	struct zproxy_stats *backend_stats =
		&http_state->services.at(backend_cfg->service->name)
		->backends.at(backend_cfg->runtime.id)
		->backend_stats;
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

void zproxy_stats_backend_inc_conn_established(
		struct zproxy_http_state *http_state,
		const struct zproxy_backend_cfg *backend_cfg)
{
	http_state->services.at(backend_cfg->service->name)
		->backends.at(backend_cfg->runtime.id)
		->backend_stats.conn_established++;
}

void zproxy_stats_backend_dec_conn_established(
		struct zproxy_http_state *http_state,
		const struct zproxy_backend_cfg *backend_cfg)
{
	http_state->services.at(backend_cfg->service->name)
		->backends.at(backend_cfg->runtime.id)
		->backend_stats.conn_established--;
}

int zproxy_stats_backend_inc_conn_pending(
		struct zproxy_http_state *http_state,
		const struct zproxy_backend_cfg *backend_cfg)
{
	return ++http_state->services.at(backend_cfg->service->name)
		->backends.at(backend_cfg->runtime.id)
		->backend_stats.conn_pending;
}

int zproxy_stats_backend_dec_conn_pending(
		struct zproxy_http_state *http_state,
		const struct zproxy_backend_cfg *backend_cfg)
{
	return --http_state->services.at(backend_cfg->service->name)
		->backends.at(backend_cfg->runtime.id)
		->backend_stats.conn_pending;
}

struct zproxy_backend_state *zproxy_state_get_backend(
		const std::unordered_map<std::string, std::shared_ptr<struct zproxy_backend_state>> *backend_state_map,
		const struct zproxy_backend_cfg *backend)
{
	const std::string id = std::string(backend->runtime.id);

	auto backend_pair = backend_state_map->find(id);
	if (backend_pair == backend_state_map->end())
		return nullptr;

	return backend_pair->second.get();
}

void zproxy_state_backend_init(const struct zproxy_service_cfg *service_cfg,
		std::unordered_map<std::string, std::shared_ptr<zproxy_backend_state>> *backend_state_list)
{
	struct zproxy_backend_cfg *backend;

	list_for_each_entry(backend, &service_cfg->backend_list, list) {
		auto backend_state = zproxy_state_get_backend(backend_state_list, backend);
		if (backend_state != nullptr) {
			backend_state->refcnt++;
			continue;
		}

		const std::string backend_id = std::string(backend->runtime.id);

		auto new_backend_state = std::make_shared<zproxy_backend_state>();
		auto it = make_pair(backend_id, std::move(new_backend_state));
		backend_state_list->emplace(std::move(it));
	}
}

void zproxy_state_backend_add(struct zproxy_http_state *http_state,
			      const struct zproxy_backend_cfg *backend)
{
	struct zproxy_service_state *service_state;
	const char *service_name = backend->service->name;
	struct zproxy_backend_state *backend_state;

	pthread_mutex_lock(&list_mutex);
	service_state = http_state->services.at(service_name).get();

	backend_state = zproxy_state_get_backend(&service_state->backends, backend);
	if (backend_state != nullptr) {
		backend_state->refcnt++;
		pthread_mutex_unlock(&list_mutex);
		return;
	}

	const std::string backend_id = std::string(backend->runtime.id);

	auto new_backend_state = std::make_shared<zproxy_backend_state>();
	auto it = make_pair(backend_id, std::move(new_backend_state));
	service_state->backends.emplace(std::move(it));
	pthread_mutex_unlock(&list_mutex);
}

struct zproxy_http_state *zproxy_state_init(const struct zproxy_proxy_cfg *proxy)
{
	struct zproxy_http_state *state = nullptr;
	struct zproxy_http_state *state_ptr;
	struct std::shared_ptr<zproxy_service_state> service_state;
	struct zproxy_service_cfg *service_cfg;

	pthread_mutex_lock(&list_mutex);
	list_for_each_entry(state_ptr, &state_list, list) {
		if (proxy->id == state_ptr->proxy_id) {
			state_ptr->refcnt++;
			state = state_ptr;
			break;
		}
	}

	if (!state) {
		state = new zproxy_http_state;
		if (!state) {
			pthread_mutex_unlock(&list_mutex);
			return NULL;
		}

		state->proxy_id = proxy->id;

		// Garbage recolector for expired sessions
		ev_init(&state->timer, zproxy_state_maintenance_cb);
		state->timer.repeat = TIMEOUT_SESSIONS;
		ev_timer_again(zproxy_main.loop, &state->timer);

		list_add_tail(&state->list, &state_list);
	}

	list_for_each_entry(service_cfg, &proxy->service_list, list) {

		auto service_state_pair = state->services.find(service_cfg->name);
		if (service_state_pair == state->services.end()) {
			service_state = std::make_shared<zproxy_service_state>(service_cfg->session.sess_type,
					service_cfg->session.sess_id, service_cfg->session.sess_ttl);
			state->services.emplace(make_pair(service_cfg->name, service_state));
		} else {
			service_state = service_state_pair->second;
			service_state->refcnt++;
		}
		zproxy_state_backend_init(service_cfg, &service_state->backends);
	}
	pthread_mutex_unlock(&list_mutex);

	return state;
}

static void zproxy_state_cfg_service_update(const struct zproxy_service_cfg *service,
					    struct zproxy_service_state *service_state)
{
	const struct zproxy_backend_cfg *backend;
	auto backend_state = service_state->backends.begin();
	int found;

	for (auto &session : service_state->sessions.sessions_set) {
		if (!zproxy_backend_cfg_lookup(service, &session.second->bck_addr)) {
			service_state->sessions.deleteSessionByKey(session.first);
		}
	}

	while (backend_state != service_state->backends.end()) {
		found = 0;
		list_for_each_entry(backend, &service->backend_list, list) {
			if (strcmp(backend->runtime.id, backend_state->first.c_str())) {
				found = 1;
				break;
			}
		}

		if (!found) {
			auto iter = backend_state;
			backend_state++;
			service_state->backends.erase(iter);
			continue;
		}

		backend_state++;
	}
}

static void zproxy_state_cfg_proxy_update(const struct zproxy_proxy_cfg *proxy,
					  struct zproxy_http_state *http_state)
{
	const struct zproxy_service_cfg *service;
	auto service_state = http_state->services.begin();
	int found;

	while (service_state != http_state->services.end()) {
		found = 0;
		list_for_each_entry(service, &proxy->service_list, list) {
			if (strcmp(service->name, service_state->first.c_str()) == 0) {
				found = 1;
				break;
			}
		}

		if (!found) {
			auto iter = service_state;
			service_state++;
			http_state->services.erase(iter);
			continue;
		}

		zproxy_state_cfg_service_update(service,
						service_state->second.get());
		service_state++;
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

		if (!found) {
			list_del(&http_state->list);
			if (--http_state->refcnt == 0)
				delete http_state;
			continue;
		}

		zproxy_state_cfg_proxy_update(proxy, http_state);
	}
	pthread_mutex_unlock(&list_mutex);
}

void zproxy_backend_state_purge(struct std::shared_ptr<zproxy_service_state> services)
{
	for (auto & backend_pair : services->backends) {
		if (--backend_pair.second->refcnt == 0)
			services->backends.erase(backend_pair.first);
	}
}

void zproxy_state_purge(struct zproxy_proxy_cfg *proxy)
{
	struct zproxy_http_state *state_ptr, *next;

	pthread_mutex_lock(&list_mutex);
	list_for_each_entry_safe(state_ptr, next, &state_list, list) {
		if (proxy->id != state_ptr->proxy_id)
			continue;

		if (--state_ptr->refcnt == 0) {
			ev_timer_stop(zproxy_main.loop, &state_ptr->timer);
			list_del(&state_ptr->list);
			delete state_ptr;
			continue;
		}
	}
	pthread_mutex_unlock(&list_mutex);
}

struct zproxy_http_state *zproxy_state_lookup(uint32_t proxy_id)
{
	struct zproxy_http_state *state;

	pthread_mutex_lock(&list_mutex);
	list_for_each_entry(state, &state_list, list) {
		if(state->proxy_id == proxy_id) {
			state->refcnt++;
			return state;
		}
	}
	pthread_mutex_unlock(&list_mutex);

	return NULL;
}

void zproxy_state_release(struct zproxy_http_state **http_state)
{
	(*http_state)->refcnt--;
	*http_state = NULL;
	pthread_mutex_unlock(&list_mutex);
}

sessions::Set *zproxy_state_get_session(const std::string &service,
	std::unordered_map<std::string, std::shared_ptr<zproxy_service_state>> *service_list)
{
	auto session_pair = service_list->find(service);

	if (session_pair == service_list->end())
		return NULL;

	return &session_pair->second->sessions;
}
