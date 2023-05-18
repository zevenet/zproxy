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

#include <cstdio>
#include <cstring>
#include <jansson.h>
#include <netdb.h>
#include <pthread.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <sys/syslog.h>
#include <sys/types.h>
#include "json.h"
#include "zcu_log.h"
#include "zcu_network.h"
#include "ctl.h"
#include "state.h"
#include "list.h"
#include "proxy.h"
#include "monitor.h"
#include "session.h"
#include "service.h"
#include "config.h"
#include "zproxy.h"

static json_t *serialize_backend(const struct zproxy_backend_cfg *backend_cfg,
				 const struct zproxy_http_state *state)
{
	struct zproxy_stats *stats = zproxy_stats_backend_get(state, backend_cfg);
	struct zproxy_monitor_backend_state backend_state = {};
	const struct timeval *avg_latency;
	double connect_time;

	zproxy_monitor_backend_state(&backend_cfg->runtime.addr,
				     backend_cfg->service->name, &backend_state);
	avg_latency = &backend_state.latency;
	connect_time = avg_latency->tv_sec + ((double)avg_latency->tv_usec) / 1000000.0;

	json_t *backend = json_object();
	json_object_set_new(backend, "2xx-code-hits",
			json_integer(stats->http_2xx_hits));
	json_object_set_new(backend, "3xx-code-hits",
			json_integer(stats->http_3xx_hits));
	json_object_set_new(backend, "4xx-code-hits",
			json_integer(stats->http_4xx_hits));
	json_object_set_new(backend, "5xx-code-hits",
			json_integer(stats->http_5xx_hits));
	json_object_set_new(backend, "address", json_string(backend_cfg->address));
	json_object_set_new(backend, "connect-time", json_real(connect_time));
	json_object_set_new(backend, "connections",
			json_integer(stats->conn_established));
	json_object_set_new(backend, "connections-limit",
			json_integer(backend_cfg->connection_limit));
	json_object_set_new(backend, "https",
			json_boolean(backend_cfg->runtime.ssl_enabled));
	json_object_set_new(backend, "id", json_string(backend_cfg->runtime.id));
	json_object_set_new(backend, "pending-connections",
			json_integer(stats->conn_pending));
	json_object_set_new(backend, "port", json_integer(backend_cfg->port));
	json_object_set_new(backend, "priority",
			json_integer(backend_cfg->priority));
	json_object_set_new(backend, "response-time", json_real(-1.0)); // stub
	if (backend_cfg->service->session.sess_type == SESS_TYPE::SESS_COOKIE_INSERT)
		json_object_set_new(backend, "cookie-key", json_string(backend_cfg->runtime.cookie_key));

	zproxy_monitor_backend_state(&backend_cfg->runtime.addr, backend_cfg->service->name, &backend_state);

	switch (backend_state.status) {
	case ZPROXY_MONITOR_UP:
		json_object_set_new(backend, "status", json_string("active"));
		break;
	case ZPROXY_MONITOR_DOWN:
		json_object_set_new(backend, "status", json_string("down"));
		break;
	case ZPROXY_MONITOR_DISABLED:
		json_object_set_new(backend, "status", json_string("disabled"));
		break;
	default:
		break;
	}
	json_object_set_new(backend, "type", json_integer(backend_cfg->type));
	json_object_set_new(backend, "nfmark", json_integer(backend_cfg->nf_mark));
	json_object_set_new(backend, "weight", json_integer(backend_cfg->weight));

	return backend;
}

static json_t *serialize_service_backends(const struct zproxy_service_cfg *service_cfg,
					  const struct zproxy_http_state *state)
{
	struct zproxy_backend_cfg *backend;
	json_t *backends = json_array();

	list_for_each_entry(backend, &service_cfg->backend_list, list) {
		json_array_append_new(backends,
				serialize_backend(backend, state));
	}

	return backends;
}

static json_t *serialize_session(const struct zproxy_session_node *session,
				 const struct zproxy_service_cfg *service_cfg)
{
	json_t *jsession = json_object();
	struct zproxy_backend_cfg *backend_cfg =
		zproxy_backend_cfg_lookup(service_cfg, &session->bck_addr);

	json_object_set_new(jsession, "id", json_string(session->key));
	json_object_set_new(jsession, "backend-id",
			    json_string(backend_cfg->runtime.id));
	json_object_set_new(jsession, "last-seen",
			    json_integer((json_int_t)session->timestamp));
	return jsession;
}

static json_t *serialize_service_sessions(const struct zproxy_service_cfg *service_cfg,
					  struct zproxy_sessions *sessions)
{
	json_t *jsessions = json_array();
	const zproxy_session_node *session;

	pthread_mutex_lock(&sessions->sessions_mutex);
	for (int i = 0; i < HASH_SESSION_SLOTS; i++) {
		list_for_each_entry(session, &sessions->session_hashtable[i], hlist) {
			if (session->defunct)
				continue;
			json_array_append_new(jsessions,
					      serialize_session(session, service_cfg));
		}
	}
	pthread_mutex_unlock(&sessions->sessions_mutex);

	return jsessions;
}

static json_t *serialize_service(const struct zproxy_service_cfg *service_cfg,
				 const struct zproxy_http_state *state)
{
	struct zproxy_monitor_service_state *service_state;
	json_t *service;

	service_state = zproxy_monitor_service_state_lookup(service_cfg->name);
	if (!service_state)
		return NULL;

	service = json_object();
	json_object_set_new(service, "backends",
			serialize_service_backends(service_cfg, state));

	json_object_set_new(service, "name", json_string(service_cfg->name));
	json_object_set_new(service, "priority", json_integer(service_state->priority));
	json_object_set_new(service, "sessions",
			    serialize_service_sessions(service_cfg, state->services.at(service_cfg->name)->sessions));

	return service;
}

static json_t *serialize_proxy_services(const struct zproxy_proxy_cfg *proxy_cfg,
					const struct zproxy_http_state *state)
{
	struct zproxy_service_cfg *service;
	json_t *services = json_array();

	list_for_each_entry(service, &proxy_cfg->service_list, list) {
		json_array_append_new(services,
				serialize_service(service, state));
	}

	return services;
}

static json_t *serialize_proxy(const struct zproxy_proxy_cfg *proxy_cfg,
			       const struct zproxy_http_state *state)
{
	json_t *proxy = json_object();

	json_object_set_new(proxy, "3xx-code-hits",
			json_integer(state->listener_stats.http_3xx_hits));
	json_object_set_new(proxy, "4xx-code-hits",
			json_integer(state->listener_stats.http_4xx_hits));
	json_object_set_new(proxy, "5xx-code-hits",
			json_integer(state->listener_stats.http_5xx_hits));
	json_object_set_new(proxy, "address", json_string(proxy_cfg->address));
	json_object_set_new(proxy, "connections",
			json_integer(state->listener_stats.conn_established));
	json_object_set_new(proxy, "https", json_boolean(proxy_cfg->runtime.ssl_enabled));
	json_object_set_new(proxy, "id", json_integer(proxy_cfg->id));
	json_object_set_new(proxy, "name", json_string(proxy_cfg->name));
	json_object_set_new(proxy, "pending-connections",
			json_integer(state->listener_stats.conn_established));
	json_object_set_new(proxy, "port", json_integer(proxy_cfg->port));

	json_object_set_new(proxy, "services",
			serialize_proxy_services(proxy_cfg, state));
	json_object_set_new(proxy, "waf-hits",
			json_integer(state->listener_stats.http_waf_hits));

	return proxy;
}

char *zproxy_json_encode_listeners(const struct zproxy_cfg *cfg)
{
	char *buf;
	const struct zproxy_proxy_cfg *proxy = NULL;
	struct zproxy_http_state *state = NULL;
	json_t *json_obj = json_array();

	if (!json_obj)
		return NULL;

	list_for_each_entry(proxy, &cfg->proxy_list, list) {
		state = zproxy_state_lookup(proxy->id);
		if (!state)
			continue;

		json_array_append_new(json_obj, serialize_proxy(proxy, state));

		zproxy_state_release(&state);
	}

	buf = json_dumps(json_obj, JSON_REAL_PRECISION(3) | JSON_INDENT(8));
	json_decref(json_obj);

	return buf;
}

char *zproxy_json_encode_listener(const struct zproxy_proxy_cfg *proxy)
{
	struct zproxy_http_state *state = NULL;
	json_t *json_obj;
	char *buf = NULL;

	state = zproxy_state_lookup(proxy->id);
	if (!state) {
		zcu_log_print(LOG_WARNING,
			      "Failed to find state for listener %d",
			      proxy->id);
		return NULL;
	}

	json_obj = serialize_proxy(proxy, state);
	buf = json_dumps(json_obj, JSON_REAL_PRECISION(3) | JSON_INDENT(8));
	json_decref(json_obj);

	zproxy_state_release(&state);

	return buf;
}

char *zproxy_json_encode_services(const struct zproxy_proxy_cfg *proxy)
{
	struct zproxy_http_state *state = NULL;
	json_t *json_obj;
	char *buf = NULL;

	state = zproxy_state_lookup(proxy->id);
	if (!state) {
		zcu_log_print(LOG_WARNING,
			      "Failed to find state for listener %d",
			      proxy->id);
		return NULL;
	}

	json_obj = serialize_proxy_services(proxy, state);
	buf = json_dumps(json_obj, JSON_REAL_PRECISION(3) | JSON_INDENT(8));
	json_decref(json_obj);

	zproxy_state_release(&state);

	return buf;
}

char *zproxy_json_encode_service(const struct zproxy_service_cfg *service)
{
	struct zproxy_http_state *state = NULL;
	json_t *json_obj;
	char *buf = NULL;

	state = zproxy_state_lookup(service->proxy->id);
	if (!state) {
		zcu_log_print(LOG_WARNING,
			      "Failed to find state for listener %d",
			      service->proxy->id);
		return NULL;
	}

	json_obj = serialize_service(service, state);
	buf = json_dumps(json_obj, JSON_REAL_PRECISION(3) | JSON_INDENT(8));
	json_decref(json_obj);

	zproxy_state_release(&state);

	return buf;
}

char *zproxy_json_encode_glob_sessions(const struct zproxy_cfg *cfg)
{
	char *buf;
	const struct zproxy_proxy_cfg *proxy = NULL;
	const struct zproxy_service_cfg *service = NULL;
	struct zproxy_http_state *state = NULL;
	json_t *json_obj = json_array();

	if (!json_obj)
		return NULL;

	list_for_each_entry(proxy, &cfg->proxy_list, list) {
		state = zproxy_state_lookup(proxy->id);
		if (!state)
			continue;

		json_t *proxy_obj = json_object();
		json_object_set_new(proxy_obj, "id", json_integer(proxy->id));

		json_t *serv_arr = json_array();
		list_for_each_entry(service, &proxy->service_list, list) {
			json_t *serv_obj = json_object();

			json_object_set_new(serv_obj, "name",
					    json_string(service->name));

			json_t *sess_arr =
				serialize_service_sessions(service,
							   state->services.at(service->name)->sessions);
			json_object_set_new(serv_obj, "sessions", sess_arr);
			json_array_append_new(serv_arr, serv_obj);
		}

		zproxy_state_release(&state);

		json_object_set_new(proxy_obj, "services", serv_arr);
		json_array_append_new(json_obj, proxy_obj);
	}

	buf = json_dumps(json_obj, JSON_REAL_PRECISION(3) | JSON_INDENT(8));
	json_decref(json_obj);

	return buf;
}

char *zproxy_json_encode_sessions(const zproxy_service_cfg *service,
				  zproxy_sessions *sessions)
{
	json_t *sess_arr;
	char *buf = NULL;

	sess_arr = serialize_service_sessions(service, sessions);
	if (!sess_arr)
		return NULL;

	buf = json_dumps(sess_arr, JSON_REAL_PRECISION(3) | JSON_INDENT(8));
	json_decref(sess_arr);

	return buf;
}

char *zproxy_json_encode_backends(const struct zproxy_service_cfg *service)
{
	struct zproxy_http_state *state = NULL;
	json_t *json_obj;
	char *buf = NULL;

	state = zproxy_state_lookup(service->proxy->id);
	if (!state) {
		zcu_log_print(LOG_WARNING,
			      "Failed to find state for listener %d",
			      service->proxy->id);
		return NULL;
	}

	json_obj = serialize_service_backends(service, state);
	buf = json_dumps(json_obj, JSON_REAL_PRECISION(3) | JSON_INDENT(8));
	json_decref(json_obj);

	zproxy_state_release(&state);

	return buf;
}

char *zproxy_json_encode_backend(const struct zproxy_backend_cfg *backend)
{
	struct zproxy_http_state *state = NULL;
	json_t *json_obj;
	char *buf = NULL;

	state = zproxy_state_lookup(backend->service->proxy->id);
	if (!state) {
		zcu_log_print(LOG_WARNING,
			      "Failed to find state for listener %d",
			      backend->service->proxy->id);
		return NULL;
	}

	json_obj = serialize_backend(backend, state);
	buf = json_dumps(json_obj, JSON_REAL_PRECISION(3) | JSON_INDENT(8));
	json_decref(json_obj);

	zproxy_state_release(&state);

	return buf;
}

int zproxy_json_decode_status(const char *buf, enum zproxy_status *status)
{
	json_error_t json_err;
	json_t *obj, *req_var;
	const char *req_value;
	*status = ZPROXY_MONITOR_UNDEFINED;

	if (!buf) {
		zcu_log_print(LOG_WARNING, "Empty JSON string buffer. Failed to decode.");
		return -1;
	}

	if (!(obj = json_loads(buf, 0, &json_err))) {
		zcu_log_print(LOG_WARNING, "Failed to decode JSON buffer.");
		return -1;
	}

	if (!(req_var = json_object_get(obj, "status"))) {
		zcu_log_print(LOG_WARNING, "No 'status' variable found.");
		return -1;
	}

	req_value = json_string_value(req_var);
	if (strcmp(req_value, "disabled") == 0) {
		*status = ZPROXY_MONITOR_DISABLED;
	} else if (strcmp(req_value, "active") == 0) {
		*status = ZPROXY_MONITOR_UP;
	} else {
		zcu_log_print(LOG_WARNING, "Invalid status '%s' given.",
			      req_value);
		return -1;
	}

	json_decref(obj);

	return 1;
}

int zproxy_json_decode_session(const char *buf, char *sess_id, size_t sess_id_len,
			       char *backend_id, size_t backend_id_len,
			       time_t *last_seen)
{
	json_error_t json_err;
	json_t *obj, *req_var;
	const char *bck_id;
	const char *id;

	if (!buf)
		return -1;

	if (!(obj = json_loads(buf, 0, &json_err))) {
		zcu_log_print(LOG_WARNING, "Failed to decode JSON buffer.");
		return -1;
	}

	if (sess_id) {
		if ((req_var = json_object_get(obj, "id"))) {
			id = json_string_value(req_var);
			snprintf(sess_id, sess_id_len, "%s", id);
		} else {
			sess_id[0] = '\0';
		}
	}

	if (backend_id) {
		if ((req_var = json_object_get(obj, "backend-id"))) {
			bck_id = json_string_value(req_var);
			snprintf(backend_id, backend_id_len, "%s", bck_id);
		} else {
			backend_id[0] = '\0';
		}
	}

	if (last_seen) {
		if ((req_var = json_object_get(obj, "last-seen"))) {
			*last_seen = (time_t)json_integer_value(req_var);
		} else {
			*last_seen = -1;
		}
	}

	json_decref(obj);

	return 1;
}

int zproxy_json_decode_glob_sessions(const char *buf,
				     std::vector<struct json_sess_listener> &listeners)
{
	json_error_t json_err;
	json_t *listener_arr, *listener_obj, *service_arr, *service_obj,
	       *session_arr, *session_obj, *req_var;
	size_t i, j, k;

	if (!buf)
		return -1;

	if (!(listener_arr = json_loads(buf, 0, &json_err))) {
		zcu_log_print(LOG_WARNING, "Failed to decode JSON buffer.");
		return -1;
	}

	json_array_foreach(listener_arr, i, listener_obj) {
		struct json_sess_listener listener;
		req_var = json_object_get(listener_obj, "id");
		listener.id = json_integer_value(req_var);

		service_arr = json_object_get(listener_obj, "services");
		json_array_foreach(service_arr, j, service_obj) {
			struct json_sess_service service;
			req_var = json_object_get(service_obj, "name");
			snprintf(service.name, CONFIG_IDENT_MAX,
				 json_string_value(req_var), "%s");

			session_arr = json_object_get(service_obj, "sessions");
			json_array_foreach(session_arr, k, session_obj) {
				struct json_session session;
				if ((req_var = json_object_get(session_obj, "id")))
					session.id = json_string_value(req_var);

				if ((req_var = json_object_get(session_obj, "backend-id")))
					session.backend_id = json_string_value(req_var);

				if ((req_var = json_object_get(session_obj, "last-seen")))
					session.last_seen = (time_t)json_integer_value(req_var);
				else
					session.last_seen = -1;

				service.sessions.push_back(session);
			}

			listener.services.push_back(service);
		}

		listeners.push_back(listener);
	}

	json_decref(listener_arr);

	return 1;
}

int zproxy_json_decode_sessions(const char *buf,
				std::vector<struct json_session> &sessions)
{
	json_error_t json_err;
	json_t *sess_array, *sess;
	size_t sess_i;

	if (!buf)
		return -1;

	if (!(sess_array = json_loads(buf, 0, &json_err))) {
		zcu_log_print(LOG_WARNING, "Failed to decode JSON buffer.");
		return -1;
	}

	if (!json_is_array(sess_array)) {
		zcu_log_print(LOG_WARNING, "Invalid JSON for sync");
		return -1;
	}

	json_array_foreach(sess_array, sess_i, sess) {
		sessions.push_back({
				   json_string_value(json_object_get(sess, "id")),
				   json_string_value(json_object_get(sess, "backend-id")),
				   json_integer_value(json_object_get(sess, "last-seen")),
				   });
	}

	json_decref(sess_array);
	return 1;
}

int zproxy_json_decode_backend(const char *buf, char *id, size_t id_len,
			       char *address, size_t address_len, int *port,
			       int *https, int *weight, int *priority,
			       int *connlimit)
{
	json_error_t json_err;
	json_t *obj, *req_var;
	const char *bck_id, *bck_addr;

	if (!buf)
		return -1;

	if (!(obj = json_loads(buf, 0, &json_err))) {
		zcu_log_print(LOG_WARNING, "Failed to decode JSON buffer.");
		return -1;
	}

	if (id) {
		if ((req_var = json_object_get(obj, "id"))) {
			bck_id = json_string_value(req_var);
			snprintf(id, id_len, "%s", bck_id);
		} else {
			id[0] = '\0';
		}
	}

	if (address) {
		if ((req_var = json_object_get(obj, "address"))) {
			bck_addr = json_string_value(req_var);
			snprintf(address, address_len, "%s", bck_addr);
		} else {
			address[0] = '\0';
		}
	}

	if (port) {
		if ((req_var = json_object_get(obj, "port")))
			*port = json_integer_value(req_var);
		else
			*port = -1;
	}

	if (https) {
		if ((req_var = json_object_get(obj, "https")))
			*https = json_boolean_value(req_var) ? 1 : 0;
		else
			*https = -1;
	}

	if (weight) {
		if ((req_var = json_object_get(obj, "weight")))
			*weight = json_integer_value(req_var);
		else
			*weight = -1;
	}

	if (priority) {
		if ((req_var = json_object_get(obj, "priority")))
			*priority = json_integer_value(req_var);
		else
			*priority = -1;
	}

	if (connlimit) {
		if ((req_var = json_object_get(obj, "connlimit")))
			*connlimit = json_integer_value(req_var);
		else
			*connlimit = -1;
	}

	json_decref(obj);

	return 1;
}
