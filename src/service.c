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

#include <arpa/inet.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <netinet/in.h>
#include <pthread.h>
#include "http_handler.h"
#include "pico_http_parser.h"
#include "http_tools.h"
#include "service.h"
#include "djb_hash.h"
#include "session.h"
#include "state.h"
#include "monitor.h"
#include "config.h"
#include "list.h"
#include "zcu_common.h"

#define HASH_SERVICE_SLOTS	64
static pthread_mutex_t service_state_mutex = PTHREAD_MUTEX_INITIALIZER;
static struct list_head service_state_hashtable[HASH_SERVICE_SLOTS];

struct zproxy_service_backend {
	struct list_head		list;
	struct sockaddr_in		addr;
	union {
		struct {
			int		weight;
		} rr;
	};
};

struct zproxy_service {
	struct list_head		hlist;
	char				name[CONFIG_IDENT_MAX];
	struct list_head		backend_list;
	struct zproxy_sessions	*sessions;

	union {
		struct {
			struct zproxy_service_backend	*backend;
			int            			used;
		} rr;
	};
};

static int zproxy_service_backend_alloc(const struct zproxy_backend_cfg *backend_cfg,
					struct zproxy_service *service)
{
	struct zproxy_service_backend *backend_state;

	backend_state = (struct zproxy_service_backend *)calloc(1, sizeof(*backend_state));
	if (!backend_state)
		return -1;

	backend_state->addr = backend_cfg->runtime.addr;
	backend_state->rr.weight = backend_cfg->weight;
	list_add_tail(&backend_state->list, &service->backend_list);

	return 0;
}

static int zproxy_service_alloc(const struct zproxy_service_cfg *service_cfg)
{
	struct zproxy_backend_cfg *backend_cfg;
	struct zproxy_service *service_state;
	uint32_t hash;

	service_state = (struct zproxy_service *)calloc(1, sizeof(*service_state));
	if (!service_state)
		return -1;

	snprintf(service_state->name, sizeof(service_state->name), "%s", service_cfg->name);
	INIT_LIST_HEAD(&service_state->backend_list);

	hash = djb_hash(service_cfg->name) % HASH_SERVICE_SLOTS;
	list_add_tail(&service_state->hlist, &service_state_hashtable[hash]);

	list_for_each_entry(backend_cfg, &service_cfg->backend_list, list) {
		if (zproxy_service_backend_alloc(backend_cfg, service_state) < 0)
			return -1;
	}

	if (service_cfg->session.sess_type != SESS_TYPE::SESS_NONE)
		service_state->sessions = zproxy_sessions_alloc(service_cfg);

	return 0;
}

int zproxy_service_state_init(struct zproxy_cfg *cfg)
{
	struct zproxy_service_cfg *service;
	struct zproxy_proxy_cfg *proxy;
	int i;

	for (i = 0; i < HASH_SERVICE_SLOTS; i++)
		INIT_LIST_HEAD(&service_state_hashtable[i]);

	list_for_each_entry(proxy, &cfg->proxy_list, list) {
		list_for_each_entry(service, &proxy->service_list, list) {
			if (zproxy_service_alloc(service) < 0)
				goto err;
		}
	}

	return 0;
err:
	zproxy_service_state_fini();

	return -1;
}

static struct zproxy_service *zproxy_service_lookup(const char *name)
{
	struct zproxy_service *service;
	uint32_t hash;

	hash = djb_hash(name) % HASH_SERVICE_SLOTS;
	list_for_each_entry(service, &service_state_hashtable[hash], hlist) {
		if (!strcmp(service->name, name))
			return service;
	}

	return NULL;
}

static void zproxy_service_backend_purge(struct zproxy_service *service_state)
{
	struct zproxy_service_backend *backend, *next;

	list_for_each_entry_safe(backend, next, &service_state->backend_list, list) {
		list_del(&backend->list);
		free(backend);
	}
}

static void zproxy_service_purge(struct zproxy_service *service_state)
{
	service_state->rr.backend = NULL;
	service_state->rr.used = 0;
}

static int zproxy_service_refresh(struct zproxy_service_cfg *service_cfg,
				  struct zproxy_service *service_state)
{
	struct zproxy_backend_cfg *backend_cfg;

	/* state information is lost for us on configuration reload. */
	zproxy_service_purge(service_state);

	zproxy_service_backend_purge(service_state);

	list_for_each_entry(backend_cfg, &service_cfg->backend_list, list) {
		if (zproxy_service_backend_alloc(backend_cfg, service_state) < 0)
			return -1;
	}

	return 0;
}

int zproxy_service_state_refresh(struct zproxy_cfg *cfg)
{
	struct zproxy_service *service_state;
	struct zproxy_service_cfg *service;
	struct zproxy_proxy_cfg *proxy;

	pthread_mutex_lock(&service_state_mutex);
	list_for_each_entry(proxy, &cfg->proxy_list, list) {
		list_for_each_entry(service, &proxy->service_list, list) {
			service_state = zproxy_service_lookup(service->name);
			if (service_state) {
				zproxy_service_refresh(service, service_state);
				continue;
			}

			if (zproxy_service_alloc(service) < 0) {
				pthread_mutex_unlock(&service_state_mutex);
				return -1;
			}
		}
	}
	pthread_mutex_unlock(&service_state_mutex);

	return 0;
}

void zproxy_service_state_fini(void)
{
	struct zproxy_service_backend *backend, *bnext;
	struct zproxy_service *service, *next;
	int i;

	for (i = 0; i < HASH_SERVICE_SLOTS; i++) {
		list_for_each_entry_safe(service, next, &service_state_hashtable[i], hlist) {
			list_for_each_entry_safe(backend, bnext, &service->backend_list, list) {
				list_del(&backend->list);
				free(backend);
			}
			if (service->sessions)
				zproxy_sessions_free(service->sessions);
			list_del(&service->hlist);
			free(service);
		}
	}
}

static bool zproxy_backend_is_available(const struct zproxy_service_cfg *service_config,
					const struct zproxy_backend_cfg *bck,
					struct zproxy_http_state *http_state)
{
	struct zproxy_monitor_backend_state monitor_backend = {};
	struct zproxy_monitor_service_state *monitor_service;
	bool over_connlimit;
	int bck_conns;

	bck_conns = zproxy_stats_backend_get_established(http_state, bck);

	/* if connection_limit > 0, because at 0 there is no limit */
	over_connlimit = bck->connection_limit > 0 && bck->connection_limit < bck_conns;
	if (over_connlimit) {
		zcu_log_print_th(LOG_DEBUG,
				 "Connection limit %d hit in backend %s:%d",
				 bck->connection_limit, bck->address,
				 bck->runtime.addr.sin_port);
		return false;
	}

	monitor_service = zproxy_monitor_service_state_lookup(service_config->name);
	if (!monitor_service) {
		zcu_log_print_th(LOG_ERR, "not found service name %s", service_config->name);
		return false;
	}

	if (!zproxy_monitor_backend_state(&bck->runtime.addr,
					  service_config->name, &monitor_backend))
		return false;

	if (monitor_backend.status != ZPROXY_MONITOR_UP ||
	    bck->priority > monitor_service->priority)
		return false;

	return true;
}

static const struct zproxy_backend_cfg *
zproxy_service_round_robin(const struct zproxy_service_cfg *service_cfg,
			   struct zproxy_http_state *http_state)
{
	const struct zproxy_backend_cfg *backend_cfg;
	struct zproxy_service_backend *first = NULL;
	struct zproxy_service_backend *backend;
	struct zproxy_service *service_state;
	int round = 0;

	service_state = zproxy_service_lookup(service_cfg->name);
	if (!service_state)
		goto err;

	while (1) {
		if (!service_state->rr.backend) {
			backend = list_first_entry(&service_state->backend_list,
						   struct zproxy_service_backend, list);
		} else {
			backend = service_state->rr.backend;
		}

		/* already iterated over the list without finding candidate? */
		if (!first)
			first = backend;
		else if (first == backend && ++round >= 2)
			break;

		backend_cfg = zproxy_backend_cfg_lookup(service_cfg, &backend->addr);
		if (!backend_cfg)
			goto skip_stale;

		if (zproxy_backend_is_available(service_cfg, backend_cfg, http_state) &&
		    ++service_state->rr.used <= backend->rr.weight)
			return backend_cfg;

skip_stale:
		service_state->rr.used = 0;
		if (list_is_last(&backend->list, &service_state->backend_list)) {
			service_state->rr.backend = NULL;
		} else {
			service_state->rr.backend = list_next_entry(backend, list);
		}
	}
err:

	return NULL;
}

static const struct zproxy_backend_cfg *
zproxy_service_least_conn(const struct zproxy_service_cfg *service_config,
			  struct zproxy_http_state *http_state)
{
	struct zproxy_backend_cfg *selected_backend = NULL;
	struct zproxy_backend_cfg *backend_cfg;
	int selected_conns = 0;
	int conns;

	list_for_each_entry(backend_cfg, &service_config->backend_list, list) {
		if (!zproxy_backend_is_available(service_config, backend_cfg, http_state))
			continue;

		conns = zproxy_stats_backend_get_established(http_state, backend_cfg);
		if (!selected_backend ||
		    conns * selected_backend->weight < selected_conns * backend_cfg->weight) {
			selected_backend = backend_cfg;
			selected_conns = conns;
			continue;
		}
	}

	return selected_backend;
}


static const struct zproxy_backend_cfg *
zproxy_service_response_time(const struct zproxy_service_cfg *service_config,
			     struct zproxy_http_state *http_state)
{
	struct timeval weighted_latency, selected_weighted_latency;
	struct zproxy_monitor_backend_state monitor_backend = {};
	struct zproxy_backend_cfg *selected_backend = NULL;
	const struct timeval *selected_avg_latency = NULL;
	struct zproxy_backend_cfg *backend_cfg;
	const struct timeval *avg_latency;

	list_for_each_entry(backend_cfg, &service_config->backend_list, list) {
		if (!zproxy_backend_is_available(service_config, backend_cfg, http_state))
			continue;

		avg_latency = &monitor_backend.latency;

		if (!selected_backend || !selected_avg_latency) {
			selected_backend = backend_cfg;
			selected_avg_latency = avg_latency;
			continue;
		}
		weighted_latency.tv_sec = avg_latency->tv_sec * selected_backend->weight;
		weighted_latency.tv_usec = avg_latency->tv_usec * selected_backend->weight;

		selected_weighted_latency.tv_sec = selected_avg_latency->tv_sec * backend_cfg->weight;
		selected_weighted_latency.tv_usec = selected_avg_latency->tv_usec * backend_cfg->weight;

		if (timercmp(&weighted_latency, &selected_weighted_latency, <)) {
			selected_backend = backend_cfg;
			selected_avg_latency = avg_latency;
			continue;
		}
	}

	return selected_backend;
}

static struct zproxy_backend_cfg *
zproxy_service_singleton_backend(const struct zproxy_service_cfg *service_config,
				 struct zproxy_http_state *http_state)
{
	struct zproxy_backend_cfg *selected_backend;

	if (service_config->backend_list_size != 1)
		return NULL;

	selected_backend = list_first_entry(&service_config->backend_list, struct zproxy_backend_cfg, list);
	if (zproxy_backend_is_available(service_config, selected_backend, http_state))
		return selected_backend;

	return NULL;
}

const struct zproxy_backend_cfg *
zproxy_service_schedule(const struct zproxy_service_cfg *service_config,
			struct zproxy_http_state *http_state)
{
	const struct zproxy_backend_cfg *selected_backend;

	selected_backend = zproxy_service_singleton_backend(service_config, http_state);
	if (selected_backend)
		return selected_backend;

	pthread_mutex_lock(&service_state_mutex);

	switch (service_config->routing_policy) {
	default:
	case ROUTING_POLICY::ROUND_ROBIN:
		selected_backend = zproxy_service_round_robin(service_config, http_state);
		break;
	case ROUTING_POLICY::W_LEAST_CONNECTIONS:
		selected_backend = zproxy_service_least_conn(service_config, http_state);
		break;
	case ROUTING_POLICY::RESPONSE_TIME:
		selected_backend = zproxy_service_response_time(service_config, http_state);
		break;
	}

	pthread_mutex_unlock(&service_state_mutex);

	return selected_backend;
}

struct zproxy_backend_cfg *
zproxy_service_backend_session(struct zproxy_service_cfg *service_config,
			       const struct sockaddr_in *bck_addr,
			       struct zproxy_http_state *http_state)
{
	struct zproxy_monitor_backend_state monitor_backend = {};
	struct zproxy_backend_cfg *selected_backend;

	selected_backend = zproxy_backend_cfg_lookup(service_config, bck_addr);
	if (!selected_backend) {
		zcu_log_print(LOG_DEBUG, "Failed to find session backend. Choosing a new one.");
		return NULL;
	}

	if (!zproxy_monitor_backend_state(bck_addr, service_config->name, &monitor_backend) ||
	    monitor_backend.status != ZPROXY_MONITOR_UP) {
		zcu_log_print(LOG_DEBUG, "Session backend is not up. Choosing a new one.");
		return NULL;
	}

	return selected_backend;
}

int _zproxy_service_select(struct zproxy_http_ctx *ctx, struct zproxy_service_cfg *service)
{
	int i, found;
	struct matcher *m, *next;
	struct zproxy_http_parser *parser = ctx->parser;
	regmatch_t eol;

	/* check for request */
	eol.rm_so = 0;
	eol.rm_eo = (regoff_t)(parser->req.path_len);
	list_for_each_entry_safe(m, next, &service->runtime.req_url, list) {
		if (regexec(&m->pat, parser->req.path, 1, &eol, REG_STARTEND) != 0)
			return 0;
	}

	/* check for required headers */
	list_for_each_entry_safe(m, next, &service->runtime.req_head, list) {
		for (found = i = 0;
			 i < (int)(parser->req.num_headers) && !found; i++) {

			eol.rm_so = 0;
			eol.rm_eo = parser->req.headers[i].line_size;
			if (regexec(&m->pat, parser->req.headers[i].name, 1, &eol,
					REG_STARTEND) == 0)
				found = 1;
		}
		if (!found)
			return 0;
	}

	/* check for forbidden headers */
	list_for_each_entry_safe(m, next, &service->runtime.deny_head, list) {
		for (i = 0; i < static_cast<int>(parser->req.num_headers);
			 i++) {
			eol.rm_so = 0;
			eol.rm_eo = parser->req.headers[i].line_size;
			if (regexec(&m->pat, parser->req.headers[i].name, 1, &eol,
					REG_STARTEND) == 0)
				return 0;
		}
	}
	return 1;
}

int zproxy_service_select(struct zproxy_http_ctx *ctx)
{
	struct zproxy_service_cfg *service;

	list_for_each_entry(service, &ctx->cfg->service_list, list) {
		if (_zproxy_service_select(ctx, service)) {
			ctx->parser->service_cfg = service;
			return 0;
		}
	}

	return 1;
}

static int zproxy_service_get_session_key(struct zproxy_sessions *sessions,
					  struct zproxy_http_ctx *ctx,
					  char *key, size_t key_len)
{
	int res = 0;

	switch (sessions->type) {
	case SESS_TYPE::SESS_IP: {
		snprintf(key, key_len, "%s", inet_ntoa(ctx->addr->sin_addr));
		res = 1;
		break;
	}
	case SESS_TYPE::SESS_COOKIE_INSERT:
	case SESS_TYPE::SESS_COOKIE: {
		for (size_t i = 0; i < ctx->parser->req.num_headers; ++i) {
			phr_header *header = &ctx->parser->req.headers[i];
			if (strncmp(header->name, http_headers_str[COOKIE],
				    header->name_len) == 0) {
				snprintf(key, MIN(header->value_len, key_len),
					 "%s", header->value);
				res = 1;
				break;
			}
		}
		break;
	}
	case SESS_TYPE::SESS_URL: {
		const char *path = ctx->parser->req.path;
		const size_t path_len = ctx->parser->req.path_len;
		int start, end;
		if (str_find_str(&start, &end, path, path_len, sessions->id,
				 strlen(sessions->id))) {
			for (; path[start] != '=' && (size_t)start < path_len;
			     ++start);
			if ((size_t)start != path_len) {
				for (end = start;
				     (path[end] != ';' && path[end] != '&') ||
				     (size_t)end < path_len;
				     ++end);
				snprintf(key, MIN(key_len, (size_t)end - start),
					 "%s", path + start);
				res = 1;
			}
		}
		break;
	}
	case SESS_TYPE::SESS_PARM: {
		const char *path = ctx->parser->req.path;
		const size_t path_len = ctx->parser->req.path_len;
		size_t start;
		for (start = 0; start < path_len && path[start] != ';'; ++start);
		snprintf(key, path_len - start, "%s", path + start);
		res = 1;
		break;
	}
	case SESS_TYPE::SESS_HEADER: {
		for (size_t i = 0; i < ctx->parser->req.num_headers; ++i) {
			phr_header *header = &ctx->parser->req.headers[i];
			if (strncmp(header->name, sessions->id,
				    header->name_len) == 0) {
				snprintf(key, MIN(header->value_len, key_len),
					 "%s", header->value);
				res = 1;
				break;
			}
		}
		break;
	}
	case SESS_TYPE::SESS_BASIC: {
		for (size_t i = 0; i < ctx->parser->req.num_headers; ++i) {
			phr_header *header = &ctx->parser->req.headers[i];
			if (strncmp(header->name,
				    http_headers_str[AUTHORIZATION],
				    header->name_len) == 0) {
				int start, end;
				if (str_find_str(&start, &end, header->value,
						 header->value_len, "Basic",
						 sizeof("Basic"))) {
					end++; // skip space
					snprintf(key,
						 MIN(header->value_len - end, key_len),
						 "%s", header->value + end);
					res = 1;
				}
				break;
			}
		}
		break;
	}
	case SESS_TYPE::SESS_NONE:
	default:
		break;
	}

	return res;
}

struct zproxy_backend_cfg *zproxy_service_select_backend(struct zproxy_http_ctx *ctx)
{
	struct zproxy_backend_cfg *selected_backend = NULL;
	struct zproxy_http_state *http_state = ctx->parser->http_state;
	struct zproxy_service_cfg *service;
	struct zproxy_sessions *sessions;
	struct zproxy_session_node *session;
	char session_key[MAX_SESSION_ID] = { 0 };
	size_t session_len = 0;

	service = ctx->parser->service_cfg;
	if (list_empty(&service->backend_list))
		return NULL;

	// check sessions table
	if (service->session.sess_type != SESS_TYPE::SESS_NONE) {
		sessions = zproxy_state_get_service_sessions(service->name,
							     &http_state->services);
		zproxy_service_get_session_key(sessions, ctx, session_key,
					       MAX_SESSION_ID);
		session_len = strlen(session_key);
		if (!session_len)
			goto select_backend;

		session = zproxy_session_get(sessions, session_key);
		if (session) {
			selected_backend = zproxy_service_backend_session(service, &session->bck_addr, http_state);
			if (selected_backend)
				return selected_backend;
		}
	}

select_backend:
	selected_backend = (struct zproxy_backend_cfg *)zproxy_service_schedule(service, (struct zproxy_http_state *)ctx->state);

	if (selected_backend && session_len &&
		service->session.sess_type != SESS_TYPE::SESS_NONE)
		zproxy_session_add(sessions, session_key, &selected_backend->runtime.addr);

	return selected_backend;
}
