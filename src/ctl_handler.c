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

#include "config.h"
#include "monitor.h"
#include "session.h"
#include "state.h"
#include "zcu_network.h"
#include "zcu_log.h"
#include "zproxy.h"
#include "ctl.h"
#include "zcu_http.h"
#include "zcu_log.h"
#include "json.h"

#include <netdb.h>
#include <stdio.h>
#include <sys/syslog.h>
#include <vector>

#define CTL_PATH_MAX_PARAMS  4

#define API_REGEX_SELECT_LISTENERS          "^[/]+listeners[/]*$"
#define API_REGEX_SELECT_LISTENER           "^[/]+listener[/]+([0-9]+)[/]*$"
#define API_REGEX_SELECT_LISTENER_SERVICES  "^[/]+listener[/]+([0-9]+)[/]+services[/]*$"
#define API_REGEX_SELECT_SERVICE            "^[/]+listener[/]+([0-9]+)[/]+service[/]+([a-zA-Z0-9-_. ]+)[/]*$"
#define API_REGEX_SELECT_SERVICE_SESSIONS   "^[/]+listener[/]+([0-9]+)[/]+service[/]+([a-zA-Z0-9-_. ]+)[/]+sessions[/]*$"
#define API_REGEX_SELECT_SESSION            "^[/]+listener[/]+([0-9]+)[/]+service[/]+([a-zA-Z0-9-_. ]+)[/]+session[/]+(.+)[/]*$"
#define API_REGEX_SELECT_SERVICE_BACKENDS   "^[/]+listener[/]+([0-9]+)[/]+service[/]+([a-zA-Z0-9-_. ]+)[/]+backends[/]*$"
#define API_REGEX_SELECT_BACKEND            "^[/]+listener[/]+([0-9]+)[/]+service[/]+([a-zA-Z0-9-_. ]+)[/]+backend[/]+([0-9.]+-[0-9]+)[/]*$"
#define API_REGEX_SELECT_BACKEND_STATUS     "^[/]+listener[/]+([0-9]+)[/]+service[/]+([a-zA-Z0-9-_. ]+)[/]+backend[/]+([0-9.]+-[0-9]+)[/]+status$"
#define API_REGEX_SELECT_CONFIG             "^[/]+config[/]*$"
#define API_REGEX_SELECT_SESSIONS           "^[/]+sessions[/]*$"

#define GET_MATCH_1PARAM(str, p1)                                              \
	const std::string p1 =                                                 \
		str.substr(matches[1].rm_so, matches[1].rm_eo - matches[1].rm_so)

#define GET_MATCH_2PARAM(str, p1, p2)                                          \
	GET_MATCH_1PARAM(str, p1);                                             \
	const std::string p2 =                                                 \
		str.substr(matches[2].rm_so, matches[2].rm_eo - matches[2].rm_so)

#define GET_MATCH_3PARAM(str, p1, p2, p3)                                      \
	GET_MATCH_2PARAM(str, p1, p2);                                         \
	const std::string p3 =                                                 \
		str.substr(matches[3].rm_so, matches[3].rm_eo - matches[3].rm_so)

static int send_msg(const struct zproxy_ctl_conn *ctl,
		    const enum ws_responses resp_code,
		    const char *content_type,
		    const char *buf, const size_t buf_len)
{
	char resp_hdr[SRV_MAX_HEADER];

	if (buf_len > 0 && !content_type) {
		zcu_log_print(LOG_WARNING, "No content type given for buffer!");
		return -1;
	}

	if (buf_len > 0) {
		sprintf(resp_hdr, "%s%s%s%zu%s%s%s%s%s%s",
			ws_str_responses[resp_code],
			content_type,
			HTTP_HEADER_CONTENTLEN, buf_len, HTTP_LINE_END,
			HTTP_HEADER_EXPIRES,
			HTTP_HEADER_PRAGMA_NO_CACHE,
			HTTP_HEADER_SERVER,
			HTTP_HEADER_CACHE_CONTROL, HTTP_LINE_END);
	} else {
		sprintf(resp_hdr, "%s%s%s%s%s%s",
			ws_str_responses[resp_code],
			HTTP_HEADER_EXPIRES,
			HTTP_HEADER_PRAGMA_NO_CACHE,
			HTTP_HEADER_SERVER,
			HTTP_HEADER_CACHE_CONTROL, HTTP_LINE_END);
	}

	if (send(ctl->io.fd, resp_hdr, strlen(resp_hdr), 0) < 0) {
		zcu_log_print(LOG_WARNING,
			      "Failed to send CTL response header to client.");
		return -1;
	}

	if (buf_len > 0 && send(ctl->io.fd, buf, strlen(buf), 0) < 0) {
		zcu_log_print(LOG_WARNING,
			      "Failed to send CTL response body to client.");
		return -1;
	}

	return 1;
}

static struct zproxy_proxy_cfg *
find_listener(const struct zproxy_cfg *cfg, uint32_t listener_id)
{
	struct zproxy_proxy_cfg *proxy;

	list_for_each_entry(proxy, &cfg->proxy_list, list) {
		if (proxy->id == listener_id)
			return proxy;
	}

	return NULL;
}

static struct zproxy_service_cfg *
find_service(const struct zproxy_cfg *cfg, uint32_t listener_id,
	     const char *service_id)
{
	const struct zproxy_proxy_cfg *proxy_cfg;
	struct zproxy_service_cfg *service_cfg;

	proxy_cfg = find_listener(cfg, listener_id);
	if (!proxy_cfg)
		return NULL;

	list_for_each_entry(service_cfg, &proxy_cfg->service_list, list) {
		if (strcmp(service_id, service_cfg->name) == 0)
			return service_cfg;
	}

	return NULL;
}

static struct zproxy_backend_cfg *
find_backend(const struct zproxy_cfg *cfg, uint32_t listener_id,
	     const char *service_id, const char *backend_id)
{
	const struct zproxy_service_cfg *service_cfg;
	struct zproxy_backend_cfg *backend_cfg;

	service_cfg = find_service(cfg, listener_id, service_id);
	if (!service_cfg)
		return NULL;

	list_for_each_entry(backend_cfg, &service_cfg->backend_list, list) {
		if (strcmp(backend_id, backend_cfg->runtime.id) == 0)
			return backend_cfg;
	}

	return NULL;
}

static enum ws_responses handle_get(const std::string &req_path,
				    const struct zproxy_cfg *cfg,
				    char **resp_buf)
{
	regmatch_t matches[CTL_PATH_MAX_PARAMS];
	*resp_buf = NULL;

	if (zproxy_regex_exec(API_REGEX_SELECT_LISTENERS, req_path.c_str(),
			      matches)) {
		if (!(*resp_buf = zproxy_json_encode_listeners(cfg))) {
			*resp_buf = zproxy_json_return_err("Failed to serialize listeners.");
			return WS_HTTP_500;
		}
	} else if (zproxy_regex_exec(API_REGEX_SELECT_LISTENER, req_path.c_str(),
				     matches)) {
		GET_MATCH_1PARAM(req_path, param);
		const int listener_id = atoi(param.c_str());
		const struct zproxy_proxy_cfg *proxy =
			find_listener(cfg, listener_id);
		if (!proxy) {
			*resp_buf = zproxy_json_return_err("Listener %d not found.",
							   listener_id);
			return WS_HTTP_404;
		}
		if (!(*resp_buf = zproxy_json_encode_listener(proxy))) {
			*resp_buf = zproxy_json_return_err("Failed to serialize listener %d.",
							   listener_id);
			return WS_HTTP_500;
		}
	} else if (zproxy_regex_exec(API_REGEX_SELECT_LISTENER_SERVICES,
				     req_path.c_str(), matches)) {
		GET_MATCH_1PARAM(req_path, param);
		const int listener_id = atoi(param.c_str());
		const struct zproxy_proxy_cfg *proxy =
			find_listener(cfg, listener_id);
		if (!proxy) {
			*resp_buf = zproxy_json_return_err("Listener %d not found.",
							   listener_id);
			return WS_HTTP_404;
		}
		if (!(*resp_buf = zproxy_json_encode_services(proxy))) {
			*resp_buf = zproxy_json_return_err("Failed to serialize services of listener %d.",
							   listener_id);
			return WS_HTTP_500;
		}
	} else if (zproxy_regex_exec(API_REGEX_SELECT_SERVICE,
				     req_path.c_str(), matches)) {
		GET_MATCH_2PARAM(req_path, param1, service_id);
		const int listener_id = atoi(param1.c_str());
		const struct zproxy_service_cfg *service =
			find_service(cfg, listener_id, service_id.c_str());
		if (!service) {
			*resp_buf = zproxy_json_return_err("Service %s in listener %d not found.",
							   service_id.c_str(),
							   listener_id);
			return WS_HTTP_404;
		}
		if (!(*resp_buf = zproxy_json_encode_service(service))) {
			*resp_buf = zproxy_json_return_err("Failed to serialize service %s.",
							   service_id.c_str());
			return WS_HTTP_500;
		}
	} else if (zproxy_regex_exec(API_REGEX_SELECT_SERVICE_BACKENDS,
				     req_path.c_str(), matches)) {
		GET_MATCH_2PARAM(req_path, param1, service_id);
		const int listener_id = atoi(param1.c_str());
		const struct zproxy_service_cfg *service =
			find_service(cfg, listener_id, service_id.c_str());
		if (!service) {
			*resp_buf = zproxy_json_return_err("Service %s in listener %d not found.",
							   service_id.c_str(),
							   listener_id);
			return WS_HTTP_404;
		}
		if (!(*resp_buf = zproxy_json_encode_backends(service))) {
			*resp_buf = zproxy_json_return_err("Failed to serialize backends of service %s.",
							   service_id.c_str());
			return WS_HTTP_500;
		}
	} else if (zproxy_regex_exec(API_REGEX_SELECT_SERVICE_SESSIONS,
				     req_path.c_str(), matches)) {
		GET_MATCH_2PARAM(req_path, param1, service_id);
		const int listener_id = atoi(param1.c_str());
		const struct zproxy_service_cfg *service =
			find_service(cfg, listener_id, service_id.c_str());
		struct zproxy_http_state *state =
			zproxy_state_lookup(listener_id);
		zproxy_sessions *sessions =
			zproxy_state_get_session(service_id, &state->services);
		if (!(*resp_buf = zproxy_json_encode_sessions(service, sessions))) {
			*resp_buf = zproxy_json_return_err("Failed to serialize sesssions of service %s.",
							   service_id.c_str());
			return WS_HTTP_500;
		}
		zproxy_state_release(&state);
	} else if (zproxy_regex_exec(API_REGEX_SELECT_BACKEND,
				     req_path.c_str(), matches)) {
		GET_MATCH_3PARAM(req_path, param1, service_id, backend_id);
		const int listener_id = atoi(param1.c_str());
		const struct zproxy_backend_cfg *backend =
			find_backend(cfg, listener_id, service_id.c_str(),
				     backend_id.c_str());
		if (!backend) {
			*resp_buf = zproxy_json_return_err("Backend %s in service %s in listener %d not found.",
							   backend_id.c_str(),
							   service_id.c_str(),
							   listener_id);
			return WS_HTTP_404;
		}
		if (!(*resp_buf = zproxy_json_encode_backend(backend))) {
			*resp_buf = zproxy_json_return_err("Failed to serialize backend %s.",
							   backend_id.c_str());
			return WS_HTTP_500;
		}
	} else if (zproxy_regex_exec(API_REGEX_SELECT_SESSIONS,
				     req_path.c_str(), matches)) {
		if (!(*resp_buf = zproxy_json_encode_glob_sessions(cfg))) {
			*resp_buf = zproxy_json_return_err("Failed to encode sessions.");
			return WS_HTTP_500;
		}
	} else {
		return WS_HTTP_400;
	}

	return WS_HTTP_200;
}

static enum ws_responses handle_patch(const std::string &req_path,
				    const char *req_msg,
				    const struct zproxy_cfg *cfg,
				    char **resp_buf)
{
	regmatch_t matches[CTL_PATH_MAX_PARAMS];
	*resp_buf = NULL;

	if (zproxy_regex_exec(API_REGEX_SELECT_SERVICE_SESSIONS,
			      req_path.c_str(), matches)) {
		GET_MATCH_2PARAM(req_path, param1, service_id);
		const int listener_id = atoi(param1.c_str());
		std::vector<struct json_session> new_sessions;
		if (zproxy_json_decode_sessions(req_msg, new_sessions) < 0) {
			*resp_buf = zproxy_json_return_err("Failed to decode JSON.");
			return WS_HTTP_400;
		}

		struct zproxy_http_state *state =
			zproxy_state_lookup(listener_id);
		if (!state) {
			*resp_buf = zproxy_json_return_err("Listener %d not found.",
							   listener_id);
			return WS_HTTP_404;
		}
		zproxy_sessions *sessions =
			zproxy_state_get_session(service_id, &state->services);
		if (!sessions) {
			zproxy_state_release(&state);
			*resp_buf = zproxy_json_return_err("Service %s not found.",
							   service_id.c_str());
			return WS_HTTP_404;
		}

		zproxy_sessions_flush(sessions);
		for (struct json_session &i : new_sessions) {
			struct zproxy_backend_cfg *backend =
				find_backend(cfg, listener_id, service_id.c_str(),
					     i.backend_id.c_str());
			if (!backend) {
				*resp_buf = zproxy_json_return_err("Backend %s doesn't exist.",
								   i.backend_id.c_str());
				return WS_HTTP_500;
			}
			zproxy_session_node *sess =
				zproxy_session_add(sessions, i.id.data(), &backend->runtime.addr);
			if (!sess) {
				*resp_buf = zproxy_json_return_err("Failed to create session");
				return WS_HTTP_500;
			}
			sess->timestamp = i.last_seen;
			zproxy_session_release(&sess);
		}

		zproxy_state_release(&state);
	} else if (zproxy_regex_exec(API_REGEX_SELECT_BACKEND_STATUS,
			      req_path.c_str(), matches)) {
		GET_MATCH_3PARAM(req_path, param1, service_id, backend_id);
		const int listener_id = atoi(param1.c_str());
		struct zproxy_backend_cfg *backend =
			find_backend(cfg, listener_id, service_id.c_str(),
				     backend_id.c_str());
		if (!backend) {
			*resp_buf = zproxy_json_return_err("Backend %s in service %s in listener %d not found.",
							   backend_id.c_str(),
							   service_id.c_str(),
							   listener_id);
			return WS_HTTP_404;
		}

		enum zproxy_status new_status;
		if (zproxy_json_decode_status(req_msg, &new_status) < 0) {
			*resp_buf = zproxy_json_return_err("Invalid JSON format.");
			return WS_HTTP_400;
		}

		if (zproxy_monitor_backend_set_enabled(&backend->runtime.addr,
						       service_id.c_str(),
						       new_status == ZPROXY_MONITOR_UP) < 0) {
			*resp_buf = zproxy_json_return_err("Failed to set backend status");
			return WS_HTTP_500;
		}
	} else if (zproxy_regex_exec(API_REGEX_SELECT_SESSION,
				     req_path.c_str(), matches)) {
		GET_MATCH_3PARAM(req_path, param1, service_id, session_id);
		const int listener_id = atoi(param1.c_str());

		char backend_id[CONFIG_IDENT_MAX] = { 0 };
		time_t last_seen;
		if (zproxy_json_decode_session(req_msg, NULL, 0,
					       backend_id, CONFIG_IDENT_MAX,
					       &last_seen) < 0) {
			*resp_buf = zproxy_json_return_err("Invalid JSON format.");
			return WS_HTTP_400;
		}
		struct zproxy_backend_cfg *backend =
			find_backend(cfg, listener_id, service_id.c_str(),
				     backend_id);
		if (!backend) {
			*resp_buf = zproxy_json_return_err("Backend %s in service %s in listener %d not found.",
							   backend_id,
							   service_id.c_str(),
							   listener_id);
			return WS_HTTP_404;
		}

		struct zproxy_http_state *state =
			zproxy_state_lookup(listener_id);
		if (!state) {
			*resp_buf = zproxy_json_return_err("Listener %d not found.",
							   listener_id);
			return WS_HTTP_404;
		}
		zproxy_sessions *sessions =
			zproxy_state_get_session(service_id, &state->services);
		if (!sessions) {
			zproxy_state_release(&state);
			*resp_buf = zproxy_json_return_err("Service %s not found.",
							   service_id.c_str());
			return WS_HTTP_404;
		}
		if (zproxy_session_update(
				sessions, session_id.data(), &backend->runtime.addr, last_seen) < 0) {
			zproxy_state_release(&state);
			*resp_buf = zproxy_json_return_err("Could not find session with ID %s.",
							   session_id.c_str());
			return WS_HTTP_404;
		}
		zproxy_state_release(&state);
	} else if (zproxy_regex_exec(API_REGEX_SELECT_CONFIG,
				     req_path.c_str(), matches)) {
		if (zproxy_cfg_file_reload() < 0) {
			*resp_buf = zproxy_json_return_err("Failed to reload configuration.");
			return WS_HTTP_500;
		}
	} else if (zproxy_regex_exec(API_REGEX_SELECT_SESSIONS,
				     req_path.c_str(), matches)) {
		struct zproxy_http_state *state;
		std::vector<struct json_sess_listener> sess_listeners;
		if (zproxy_json_decode_glob_sessions(req_msg, sess_listeners) < 0) {
			*resp_buf = zproxy_json_return_err("Failed to decode JSON.");
			return WS_HTTP_500;
		}

		for (auto &i : sess_listeners) {
			state = zproxy_state_lookup(i.id);
			if (!state) {
				*resp_buf = zproxy_json_return_err("Listener %d doesn't exist.",
								   i.id);
				return WS_HTTP_500;
			}
			for (auto &j : i.services) {
				struct zproxy_sessions *sessions;
				sessions = zproxy_state_get_session(j.name, &state->services);
				if (!sessions) {
					*resp_buf = zproxy_json_return_err("Service %s doesn't exist.",
									   j.name);
					return WS_HTTP_500;
				}
				zproxy_sessions_flush(sessions);
				for (auto &k : j.sessions) {
					struct zproxy_backend_cfg *backend =
						find_backend(cfg, i.id, j.name,
							     k.backend_id.c_str());
					if (!backend) {
						*resp_buf = zproxy_json_return_err("Backend %s doesn't exist.",
										   k.backend_id.c_str());
						return WS_HTTP_500;
					}
					zproxy_session_node *sess =
						zproxy_session_add(sessions,
								   k.id.data(),
								   &backend->runtime.addr);
					if (!sess) {
						*resp_buf = zproxy_json_return_err("Failed to create session");
						return WS_HTTP_500;
					}
					sess->timestamp = k.last_seen;
					zproxy_session_release(&sess);
				}
			}
			zproxy_state_release(&state);
		}
	} else {
		return WS_HTTP_400;
	}

	*resp_buf = zproxy_json_return_ok();

	return WS_HTTP_200;
}

static enum ws_responses handle_delete(const std::string &req_path,
				       const char *req_msg,
				       const struct zproxy_cfg *cfg,
				       char **resp_buf)
{
	regmatch_t matches[CTL_PATH_MAX_PARAMS];
	*resp_buf = NULL;

	if (zproxy_regex_exec(API_REGEX_SELECT_SERVICE_SESSIONS,
			      req_path.c_str(), matches)) {
		GET_MATCH_2PARAM(req_path, param1, service_id);
		const int listener_id = atoi(param1.c_str());
		struct zproxy_http_state *state =
			zproxy_state_lookup(listener_id);
		if (!state) {
			*resp_buf = zproxy_json_return_err("Listener %d not found.",
							   listener_id);
			return WS_HTTP_404;
		}
		zproxy_sessions *sessions =
			zproxy_state_get_session(service_id, &state->services);
		if (!sessions) {
			zproxy_state_release(&state);
			*resp_buf = zproxy_json_return_err("Service %s not found.",
							   service_id.c_str());
			return WS_HTTP_404;
		}

		if (strlen(req_msg) <= 0) {
			zcu_log_print(LOG_DEBUG, "Manually flushing sessions.");
			zproxy_sessions_flush(sessions);
		} else {
			char backend_id[CONFIG_IDENT_MAX] = { 0 };
			char sess_id[CONFIG_IDENT_MAX] = { 0 };

			if (zproxy_json_decode_session(req_msg, sess_id, CONFIG_IDENT_MAX,
						       backend_id, CONFIG_IDENT_MAX,
						       NULL) < 0) {
				zproxy_state_release(&state);
				*resp_buf = zproxy_json_return_err("Invalid JSON format.");
				return WS_HTTP_400;
			}
			if (backend_id[0]) {
				zcu_log_print(LOG_DEBUG, "Manually flushing sessions with backend ID %s",
					      backend_id);
				struct zproxy_backend_cfg *backend =
					find_backend(cfg, listener_id,
						     service_id.c_str(),
						     backend_id);
				if (!backend) {
					zproxy_state_release(&state);
					*resp_buf = zproxy_json_return_err("Backend %s in service %s in listener %d not found.",
									   backend_id, service_id.c_str(), listener_id);
					return WS_HTTP_404;
				}
				zproxy_session_delete_backend(sessions, &backend->runtime.addr);
			} else if (sess_id[0]) {
				zcu_log_print(LOG_DEBUG,
					      "Manually flushing sessions with ID %s",
					      sess_id);
				if (zproxy_session_delete(sessions, sess_id) < 0) {
					zproxy_state_release(&state);
					*resp_buf = zproxy_json_return_err("Could not find session with ID %s",
									   sess_id);
					return WS_HTTP_404;
				}
			} else {
				zproxy_state_release(&state);
				zproxy_json_return_err("Invalid flush command.");
				return WS_HTTP_400;
			}
		}
		zproxy_state_release(&state);
	} else {
		return WS_HTTP_400;
	}

	*resp_buf = zproxy_json_return_ok();

	return WS_HTTP_204;
}

static enum ws_responses handle_put(const std::string &req_path,
				    const char *req_msg,
				    const struct zproxy_cfg *cfg,
				    char **resp_buf)
{
	regmatch_t matches[CTL_PATH_MAX_PARAMS];
	*resp_buf = NULL;

	if (zproxy_regex_exec(API_REGEX_SELECT_SERVICE_SESSIONS,
			      req_path.c_str(), matches)) {
		GET_MATCH_2PARAM(req_path, param1, service_id);
		const int listener_id = atoi(param1.c_str());
		char sess_id[CONFIG_IDENT_MAX] = { 0 };
		char backend_id[CONFIG_IDENT_MAX] = { 0 };
		time_t last_seen;

		if (zproxy_json_decode_session(req_msg, sess_id, CONFIG_IDENT_MAX,
					       backend_id, CONFIG_IDENT_MAX,
					       &last_seen) < 0) {
			*resp_buf = zproxy_json_return_err("Invalid JSON format.");
			return WS_HTTP_400;
		}

		if (!backend_id[0]) {
			*resp_buf = zproxy_json_return_err("Invalid JSON format. Expected 'backend-id' variable.");
			return WS_HTTP_400;
		}
		struct zproxy_backend_cfg *backend =
			find_backend(cfg, listener_id, service_id.c_str(),
				     backend_id);
		if (!backend) {
			*resp_buf = zproxy_json_return_err("Backend %s in service %s in listener %d not found.",
							   backend_id, service_id.c_str(), listener_id);
			return WS_HTTP_404;
		}

		if (!sess_id[0]) {
			*resp_buf = zproxy_json_return_err("Invalid JSON format. Expected 'id' variable.");
			return WS_HTTP_400;
		}

		struct zproxy_http_state *state =
			zproxy_state_lookup(listener_id);
		if (!state) {
			*resp_buf = zproxy_json_return_err("Listener %d not found.",
							   listener_id);
			return WS_HTTP_404;
		}
		zproxy_sessions *sessions =
			zproxy_state_get_session(service_id, &state->services);
		if (!sessions) {
			zproxy_state_release(&state);
			*resp_buf = zproxy_json_return_err("Service %s not found.",
							   service_id.c_str());
			return WS_HTTP_404;
		}

		zproxy_session_node *session =
			zproxy_session_add(sessions, sess_id, &backend->runtime.addr);
		if (!session) {
			zproxy_state_release(&state);
			*resp_buf = zproxy_json_return_err("Unable to create session. Perhaps it already exists.");
			return WS_HTTP_409;
		}
		if (last_seen >= 0)
			session->timestamp = last_seen;
		zproxy_session_release(&session);
		zproxy_state_release(&state);
	} else if (zproxy_regex_exec(API_REGEX_SELECT_SERVICE_BACKENDS,
				     req_path.c_str(), matches)) {
		GET_MATCH_2PARAM(req_path, param1, service_id);
		const int listener_id = atoi(param1.c_str());
		struct zproxy_backend_cfg *new_backend;
		struct zproxy_cfg *new_cfg;
		struct zproxy_service_cfg *service;

		char bck_addr[CONFIG_MAX_FIN] = { 0 };
		char bck_id[CONFIG_IDENT_MAX] = { 0 };
		int bck_port, bck_weight, bck_https, bck_prio, bck_connlimit;
		if (zproxy_json_decode_backend(req_msg, bck_id, CONFIG_IDENT_MAX,
					       bck_addr, CONFIG_MAX_FIN, &bck_port,
					       &bck_https, &bck_weight, &bck_prio,
					       &bck_connlimit) < 0) {
			*resp_buf = zproxy_json_return_err("Invalid JSON format.");
			return WS_HTTP_400;
		}

		if (!bck_addr[0]) {
			*resp_buf = zproxy_json_return_err("Invalid JSON format. Expected 'address' variable.");
			return WS_HTTP_400;
		}
		struct addrinfo addr;
		if (zcu_net_get_host(bck_addr, &addr, PF_UNSPEC, 0)) {
			// if we can't resolve it, maybe this is a UNIX domain socket
			if (strstr(bck_addr, "/")) {
				if ((strlen(bck_addr) + 1) > CONFIG_UNIX_PATH_MAX) {
					*resp_buf = zproxy_json_return_err("Invalid JSON format. Expected 'backend-id' variable.");
					return WS_HTTP_400;
				}
			} else { // maybe the new_backend still not available, we set it as down
				zcu_log_print(LOG_WARNING, "Could not resolve new backend.");
			}
		}
		free(addr.ai_addr);

		if (bck_port < 0) {
			*resp_buf = zproxy_json_return_err("Invalid JSON format. Expected 'port' variable.");
			return WS_HTTP_400;
		}

		if (!(new_backend = zproxy_backend_cfg_alloc())) {
			*resp_buf = zproxy_json_return_err("Could not create a new backend. (Maybe Out of Memory)");
			return WS_HTTP_500;
		}
		if (!(new_cfg = zproxy_cfg_clone(cfg))) {
			free(new_backend);
			*resp_buf = zproxy_json_return_err("Could not clone new configuration. (Maybe Out of Memory)");
			return WS_HTTP_500;
		}

		service = find_service(new_cfg, listener_id, service_id.c_str());
		if (!service) {
			free(new_backend);
			zproxy_cfg_free(new_cfg);
			*resp_buf = zproxy_json_return_err("Service %s in listener %d not found.",
							   service_id.c_str(), listener_id);
			return WS_HTTP_404;
		}

		zproxy_backend_cfg_init(cfg, service, new_backend);

		if (bck_id[0]) {
			snprintf(new_backend->runtime.id, CONFIG_IDENT_MAX,
				 "%s", bck_id);
		} else {
			snprintf(new_backend->runtime.id, CONFIG_IDENT_MAX,
				 "%s-%d", bck_addr, bck_port);
		}
		snprintf(new_backend->address, CONFIG_MAX_FIN, "%s", bck_addr);
		new_backend->runtime.addr.sin_addr.s_addr =
			inet_addr(new_backend->address);
		new_backend->runtime.addr.sin_family = AF_INET;
		new_backend->port = bck_port;
		new_backend->runtime.addr.sin_port = htons(new_backend->port);
		if (bck_weight >= 0)
			new_backend->weight = bck_weight;
		if (bck_https >= 0)
			new_backend->runtime.ssl_enabled = bck_https;
		if (bck_prio >= 0)
			new_backend->priority = bck_prio;
		if (bck_connlimit >= 0)
			new_backend->connection_limit = bck_connlimit;

		if (new_backend->runtime.ssl_enabled)
			zproxy_backend_ctx_start(new_backend);

		list_add_tail(&new_backend->list, &service->backend_list);
		service->backend_list_size++;
		if (service->session.sess_type == SESS_TYPE::SESS_COOKIE_INSERT) {
			zproxy_set_backend_cookie_insertion(service, new_backend,
					       new_backend->cookie_set_header);
		}

		if (zproxy_cfg_reload(new_cfg) < 0) {
			free(new_backend);
			zproxy_cfg_free(new_cfg);
			*resp_buf = zproxy_json_return_err("Failed to load new configuration.");
			return WS_HTTP_500;
		}
		struct zproxy_http_state *state =
			zproxy_state_lookup(listener_id);
		zproxy_state_backend_add(state, new_backend);
		zproxy_state_release(&state);
	} else {
		return WS_HTTP_400;
	}

	*resp_buf = zproxy_json_return_ok();

	return WS_HTTP_201;
}

int ctl_handler_cb(const struct zproxy_ctl_conn *ctl,
		const struct zproxy_cfg *cfg)
{
	size_t used_bytes;
	HttpRequest request;
	const http_parser::PARSE_RESULT parse_res =
		request.parse(ctl->buf, ctl->buf_len, &used_bytes);
	int ret;
	enum ws_responses resp_code;
	const char *content_type;
	char *buf = NULL;
	size_t buf_len;

	if (parse_res != http_parser::PARSE_RESULT::SUCCESS) {
		switch (parse_res) {
		case http_parser::PARSE_RESULT::FAILED:
			buf = zproxy_json_return_err("Failed to parse CTL request.");
			break;
		case http_parser::PARSE_RESULT::INCOMPLETE:
			buf = zproxy_json_return_err("Failed to parse CTL request: incomplete.");
			break;
		case http_parser::PARSE_RESULT::TOOLONG:
			buf = zproxy_json_return_err("CTL request too long.");
			break;
		default:
			break;
		}

		zcu_log_print(LOG_WARNING, "CTL request parsing error.");

		resp_code = WS_HTTP_400;
		goto err_handler;
	}

	switch (request.getRequestMethod()) {
	case http::REQUEST_METHOD::GET: {
		zcu_log_print(LOG_DEBUG, "CTL GET %s", request.path.c_str());
		resp_code = handle_get(request.path, cfg, &buf);
		if (resp_code == WS_HTTP_200)
			zcu_log_print(LOG_INFO, "JSON object encoding successful");
		else
			zcu_log_print(LOG_INFO, "Failed to encode object");
		break;
	}
	case http_parser::REQUEST_METHOD::PATCH: {
		zcu_log_print(LOG_DEBUG, "CTL PATCH %s", request.path.c_str());
		resp_code = handle_patch(request.path, request.message, cfg, &buf);
		if (resp_code == WS_HTTP_200)
			zcu_log_print(LOG_INFO, "Object patching successful");
		else
			zcu_log_print(LOG_INFO, "Failed to patch object");
		break;
	}
	case http_parser::REQUEST_METHOD::DELETE: {
		zcu_log_print(LOG_DEBUG, "CTL DELETE %s", request.path.c_str());
		resp_code = handle_delete(request.path, request.message, cfg, &buf);
		if (resp_code == WS_HTTP_204)
			zcu_log_print(LOG_INFO, "Object deletion successful");
		else
			zcu_log_print(LOG_INFO, "Failed to delete object");
		break;
	}
	case http_parser::REQUEST_METHOD::PUT: {
		zcu_log_print(LOG_DEBUG, "CTL PUT %s", request.path.c_str());
		resp_code = handle_put(request.path, request.message, cfg, &buf);
		if (resp_code == WS_HTTP_204)
			zcu_log_print(LOG_INFO, "Object creation successful");
		else
			zcu_log_print(LOG_INFO, "Failed to create object");
		break;
	}
	default: {
		zcu_log_print(LOG_WARNING, "Received unknown or unsupported request method");
		return send_msg(ctl, WS_HTTP_405, NULL, NULL, 0);
	}
	}

err_handler:
	content_type = buf != NULL ? HTTP_HEADER_CONTENT_JSON : NULL;
	buf_len = buf != NULL ? strlen(buf) : 0;
	ret = send_msg(ctl, resp_code, content_type, buf, buf_len);
	free(buf);

	return ret;
}
