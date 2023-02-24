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

#ifndef _ZPROXY_JSON_H_
#define _ZPROXY_JSON_H_

#include <jansson.h>
#include "config.h"
#include "state.h"
#include "proxy.h"

enum json_obj_type {
	ENCODE_PROXY,
	ENCODE_PROXY_SERVICES,
	ENCODE_SERVICE,
	ENCODE_SERVICE_BACKENDS,
	ENCODE_BACKEND,
};

enum zproxy_json_cmd {
	JSON_CMD_BACKEND_STATUS,
	JSON_CMD_FLUSH_SESSIONS,
	JSON_CMD_MODIFY_SESSION,
	JSON_CMD_ADD_SESSION,
	JSON_CMD_RELOAD_CONFIG,
	JSON_CMD_ADD_BACKEND,
};

int zproxy_json_encode(
		const struct zproxy_cfg *cfg,
		const uint32_t listener_id,
		const char *service_name,
		const char *backend_id,
		enum json_obj_type type,
		char **buf);

/**
 * Execute command from CTL.
 */
int zproxy_json_exec(const struct zproxy_cfg *cfg, const uint32_t listener_id,
		     const char *service_name, const char *lvl_3_id,
		     enum zproxy_json_cmd cmd, const char *buf, char **res);

#endif //_ZPROXY_JSON_H_
