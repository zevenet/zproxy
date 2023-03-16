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

#include <cstdio>
#include <jansson.h>
#include <stdarg.h>
#include "config.h"
#include "state.h"
#include "monitor.h"
#include "proxy.h"
#include "ctl.h"

/* QUICK JSON RESPONSES */
inline char *zproxy_json_return_ok(void)
{
	char *buf;
	json_t *res = json_object();

	json_object_set_new(res, "result", json_string("ok"));
	buf = json_dumps(res, JSON_INDENT(0) | JSON_COMPACT);
	json_decref(res);

	return buf;
}
inline char *zproxy_json_return_err(const char *format, ...)
{
	char *buf, reason[ERR_BUF_MAX_SIZE];
	va_list args;
	json_t *res = json_object();

	va_start(args, format);
	vsnprintf(reason, ERR_BUF_MAX_SIZE, format, args);
	va_end(args);

	json_object_set_new(res, "result", json_string("error"));
	json_object_set_new(res, "reason", json_string(reason));
	buf = json_dumps(res, JSON_INDENT(0) | JSON_COMPACT);
	json_decref(res);

	return buf;
}

/* ENCODING */
char *zproxy_json_encode_listener(const struct zproxy_proxy_cfg *proxy);
char *zproxy_json_encode_services(const struct zproxy_proxy_cfg *proxy);
char *zproxy_json_encode_service(const struct zproxy_service_cfg *service);
char *zproxy_json_encode_backends(const struct zproxy_service_cfg *service);
char *zproxy_json_encode_backend(const struct zproxy_backend_cfg *backend);

/* DECODING */
int zproxy_json_decode_status(const char *buf, enum zproxy_status *status);
int zproxy_json_decode_session(const char *buf, char *sess_id, size_t sess_id_len,
			       char *backend_id, size_t backend_id_len,
			       time_t *last_seen);
int zproxy_json_decode_backend(const char *buf, char *id, size_t id_len,
			       char *address, size_t address_len, int *port,
			       int *https, int *weight, int *priority,
			       int *connlimit);

#endif //_ZPROXY_JSON_H_
