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

#include "list.h"
#include "config.h"
#include "service.h"
#include "services.h"
#include "session.h"
#include "http_request.h"
#include "monitor.h"
#include "http_manager.h"

bool Service::selectService(const HttpRequest &request,
		const struct zproxy_service_cfg *service_config)
{
	int i, found;
	struct matcher *m, *next;

	/* check for request */
	regmatch_t eol{ 0, static_cast<regoff_t>(request.path.length()) };
	list_for_each_entry_safe(m, next, &service_config->runtime.req_url, list) {
		if (regexec(&m->pat, request.path.data(), 1, &eol,
				REG_STARTEND) != 0)
			return false;
	}

	/* check for required headers */
	list_for_each_entry_safe(m, next, &service_config->runtime.req_head, list) {
		for (found = i = 0;
			 i < (int)(request.num_headers) && !found; i++) {

			eol.rm_so = 0;
			eol.rm_eo = request.headers[i].line_size - 2;
			if (regexec(&m->pat, request.headers[i].name, 1, &eol,
					REG_STARTEND) == 0)
				found = 1;
		}
		if (!found)
			return false;
	}

	/* check for forbidden headers */
	list_for_each_entry_safe(m, next, &service_config->runtime.deny_head, list) {
		for (i = 0; i < static_cast<int>(request.num_headers);
			 i++) {
			eol.rm_so = 0;
			eol.rm_eo = request.headers[i].line_size - 2;
			if (regexec(&m->pat, request.headers[i].name, 1, &eol,
					REG_STARTEND) == 0)
				return false;
		}
	}
	return true;
}

struct zproxy_backend_cfg *Service::selectBackend(
		struct zproxy_service_cfg *service_config,
		HttpRequest &request,
        std::string &client_addr, struct zproxy_sessions *sessions,
		struct zproxy_http_state *http_state)
{
	struct zproxy_backend_cfg *selected_backend = nullptr;
	struct zproxy_session_node *session;
	std::string session_key;

	if (list_empty(&service_config->backend_list))
		return nullptr;

	// check sessions table
	if (service_config->session.sess_type != SESS_TYPE::SESS_NONE) {
		session_key = zproxy_service_get_session_key(sessions, client_addr.data(), request);
		session = zproxy_session_get(sessions, session_key.data());
		if (session) {
			selected_backend = zproxy_service_backend_session(service_config, &session->bck_addr, http_state);
			if (selected_backend)
				return selected_backend;
		}
	}

	selected_backend = (struct zproxy_backend_cfg *)zproxy_service_schedule(service_config, http_state);

	if (selected_backend && !session_key.empty() &&
		service_config->session.sess_type != SESS_TYPE::SESS_NONE)
		zproxy_session_add(sessions, session_key.data(), &selected_backend->runtime.addr);

	return selected_backend;
}
