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

#ifndef _ZPROXY_SESSION_H_
#define _ZPROXY_SESSION_H_

#include <pthread.h>
#include <jansson.h>
#include "list.h"
#include "config.h"
#include "http_request.h"

#define MAX_SESSION_ID 255
#define HASH_SESSION_SLOTS 512

struct zproxy_sessions {
	struct list_head session_hashtable[HASH_SESSION_SLOTS];
	SESS_TYPE type;
	unsigned int ttl;
	char id[MAX_SESSION_ID];
	unsigned int size;
	pthread_mutex_t sessions_mutex = PTHREAD_MUTEX_INITIALIZER;
};

struct zproxy_session_node {
	struct list_head hlist;
	char key[MAX_SESSION_ID];
	struct sockaddr_in bck_addr;
	// last_seen is used to calculate if the session has expired.
	// If it has the value 0 means that the session does not expired, it is permanent
	unsigned int timestamp;
};


struct zproxy_sessions *zproxy_sessions_alloc(const struct zproxy_service_cfg *service_cfg);
void zproxy_sessions_flush(struct zproxy_sessions *sessions);
void zproxy_sessions_free(struct zproxy_sessions *sessions);
struct zproxy_session_node *zproxy_session_get(struct zproxy_sessions *sessions, const char *key);
struct zproxy_session_node *zproxy_session_add(struct zproxy_sessions *sessions, const char *key, const struct sockaddr_in *bck);
void zproxy_sessions_remove_expired(struct zproxy_sessions *sessions);
void zproxy_session_delete_backend(struct zproxy_sessions *sessions, const struct sockaddr_in *bck);
int zproxy_session_delete(struct zproxy_sessions *sessions, const char *key);
int zproxy_session_update(struct zproxy_sessions *sessions, const char *key, const struct sockaddr_in *bck, unsigned int timestamp);
void zproxy_session_delete_old_backends(const struct zproxy_service_cfg *service, struct zproxy_sessions *sessions);

#endif
