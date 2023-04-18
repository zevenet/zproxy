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

#ifndef _ZPROXY_SERVICE_H_
#define _ZPROXY_SERVICE_H_

#include "http_request.h"
#include "session.h"
#include "state.h"

class Service
{
public:
    static bool selectService(const HttpRequest &request,
			const struct zproxy_service_cfg *service_config);

    static bool checkBackendAvailable(const zproxy_service_cfg *service_config,
			zproxy_backend_cfg *bck, struct zproxy_http_state *http_state);

	/**
	 * Selects the corresponding Backend to which the connection will be routed
	 * according to the established balancing algorithm.
	 */
    static zproxy_backend_cfg *selectBackend(
			struct zproxy_service_cfg *service_config,
			HttpRequest &request,
			std::string &client_addr, struct zproxy_sessions *sessions,
			struct zproxy_http_state *http_state);

};

#endif
