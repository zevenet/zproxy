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

#include "session.h"
#include "djb_hash.h"
#include "zcu_log.h"
#include <arpa/inet.h>
#include <netinet/in.h>
#include <time.h>
#include <sys/syslog.h>

void zproxy_sessions_dump(struct zproxy_sessions *sessions)
{
	struct zproxy_session_node *cur;

	pthread_mutex_lock(&sessions->sessions_mutex);
	for (int i = 0; i < HASH_SESSION_SLOTS; i++) {
		list_for_each_entry(cur, &sessions->session_hashtable[i], hlist) {
			zcu_log_print(LOG_DEBUG,
			       "** sessions[%d]: %s (bck=%s:%d;l-s=%d;d=%s)",
			       i, cur->key, inet_ntoa(cur->bck_addr.sin_addr),
			       ntohs(cur->bck_addr.sin_port), cur->timestamp,
			       cur->defunct ? "true" : "false");
		}
	}
	pthread_mutex_unlock(&sessions->sessions_mutex);
}

static int zproxy_session_is_static(struct zproxy_session_node *session)
{
	return !session->timestamp;
}

static void zproxy_session_update_timestamp(struct zproxy_session_node *session)
{
	session->timestamp = time(NULL);
}

static int zproxy_session_is_expired(struct zproxy_session_node *session, unsigned int ttl)
{
	if (zproxy_session_is_static(session))
		return 0;
	return time(NULL) - session->timestamp > ttl;
}

static int zproxy_session_free(struct zproxy_session_node *session)
{
	if (session->refcnt == 0) {
		list_del(&session->hlist);
		free(session);
		return 1;
	} else {
		session->defunct = true;
		return -1;
	}
}

struct zproxy_sessions *zproxy_sessions_alloc(const struct zproxy_service_cfg *service_cfg)
{
	struct zproxy_sessions *sessions;
	int i;

	sessions = (struct zproxy_sessions *)calloc(1, sizeof(*sessions));
	if (!sessions)
		return NULL;

	for (i = 0; i < HASH_SESSION_SLOTS; i++)
		INIT_LIST_HEAD(&sessions->session_hashtable[i]);

	sessions->type = service_cfg->session.sess_type;
	sessions->ttl = service_cfg->session.sess_ttl;
	sessions->size = 0;
	snprintf(sessions->id, sizeof(sessions->id), "%s", service_cfg->session.sess_id);

	return sessions;
}

void zproxy_sessions_flush(struct zproxy_sessions *sessions)
{
	struct zproxy_session_node *session, *next;
	int i;

	pthread_mutex_lock(&sessions->sessions_mutex);
	sessions->size = 0;
	for (i = 0; i < HASH_SESSION_SLOTS; i++) {
		list_for_each_entry_safe(session, next, &sessions->session_hashtable[i], hlist)
			zproxy_session_free(session);
	}
	pthread_mutex_unlock(&sessions->sessions_mutex);
}

void zproxy_sessions_free(struct zproxy_sessions *sessions)
{
	zproxy_sessions_flush(sessions);
	free(sessions);
}

static struct zproxy_session_node *_zproxy_session_get(struct zproxy_sessions *sessions, const char *key)
{
	struct zproxy_session_node *cur;
	int hash = djb_hash(key) % HASH_SESSION_SLOTS;

	list_for_each_entry(cur, &sessions->session_hashtable[hash], hlist) {
		if (!cur->defunct && strncmp(cur->key, key, strlen(cur->key)+1) == 0)
			return cur;
	}

	return NULL;
}

struct zproxy_session_node *zproxy_session_get(struct zproxy_sessions *sessions, const char *key)
{
	struct zproxy_session_node *session;

	pthread_mutex_lock(&sessions->sessions_mutex);
	session = _zproxy_session_get(sessions, key);
	if (session)
		session->refcnt++;
	pthread_mutex_unlock(&sessions->sessions_mutex);

	return session;
}

struct zproxy_session_node *zproxy_session_add(struct zproxy_sessions *sessions, const char *key, const struct sockaddr_in *bck)
{
	struct zproxy_session_node *session;
	uint32_t hash;

	pthread_mutex_lock(&sessions->sessions_mutex);
	session = _zproxy_session_get(sessions, key);
	if (session) {
		if (!zproxy_session_is_static(session))
			zproxy_session_update_timestamp(session);
		session->refcnt++;
		pthread_mutex_unlock(&sessions->sessions_mutex);
		return session;
	}

	session = (struct zproxy_session_node *)calloc(1, sizeof(*session));
	if (!session) {
		pthread_mutex_unlock(&sessions->sessions_mutex);
		return NULL;
	}

	snprintf(session->key, sizeof(session->key), "%s", key);
	memcpy(&session->bck_addr, bck, sizeof(struct sockaddr_in));
	session->timestamp = time(NULL);
	session->defunct = false;

	sessions->size++;

	hash = djb_hash(session->key) % HASH_SESSION_SLOTS;
	list_add_tail(&session->hlist, &sessions->session_hashtable[hash]);

	session->refcnt++;
	pthread_mutex_unlock(&sessions->sessions_mutex);

	return session;
}

void zproxy_session_release(struct zproxy_session_node **session)
{
	if (!*session)
		return;

	(*session)->refcnt--;
}

void zproxy_sessions_remove_expired(struct zproxy_sessions *sessions)
{
	struct zproxy_session_node *session, *next;
	int i;

	pthread_mutex_lock(&sessions->sessions_mutex);
	for (i = 0; i < HASH_SESSION_SLOTS; i++) {
		list_for_each_entry_safe(session, next, &sessions->session_hashtable[i], hlist) {
			if (zproxy_session_is_expired(session, sessions->ttl)) {
				if (zproxy_session_free(session) < 0)
					sessions->size--;
			}
		}
	}
	pthread_mutex_unlock(&sessions->sessions_mutex);
}

static int _zproxy_session_delete(struct zproxy_sessions *sessions, const char *key)
{
	struct zproxy_session_node *session;

	session = _zproxy_session_get(sessions, key);
	if (!session)
		return -1;

	if (zproxy_session_free(session) < 0)
		sessions->size--;

	return 0;
}

int zproxy_session_delete(struct zproxy_sessions *sessions, const char *key)
{
	int ret;

	pthread_mutex_lock(&sessions->sessions_mutex);
	ret = _zproxy_session_delete(sessions, key);
	pthread_mutex_unlock(&sessions->sessions_mutex);

	return ret;
}

int zproxy_session_update(struct zproxy_sessions *sessions, const char *key, const struct sockaddr_in *bck, unsigned int timestamp)
{
	struct zproxy_session_node *session;

	pthread_mutex_lock(&sessions->sessions_mutex);
	session = _zproxy_session_get(sessions, key);
	if (!session) {
		pthread_mutex_unlock(&sessions->sessions_mutex);
		return -1;
	}

	memcpy(&session->bck_addr, bck, sizeof(struct sockaddr_in));
	session->timestamp = timestamp;
	pthread_mutex_unlock(&sessions->sessions_mutex);

	return 0;
}

void zproxy_session_delete_backend(struct zproxy_sessions *sessions, const struct sockaddr_in *bck)
{
	struct zproxy_session_node *session, *next;
	int i;

	pthread_mutex_lock(&sessions->sessions_mutex);
	for (i = 0; i < HASH_SESSION_SLOTS; i++) {
		list_for_each_entry_safe(session, next, &sessions->session_hashtable[i], hlist) {
			if (memcmp(&session->bck_addr, bck, sizeof(struct sockaddr_in)) == 0) {
				if (zproxy_session_free(session) < 0)
					sessions->size--;
			}
		}
	}
	pthread_mutex_unlock(&sessions->sessions_mutex);
}

void zproxy_session_delete_old_backends(const struct zproxy_service_cfg *service, struct zproxy_sessions *sessions)
{
	struct zproxy_session_node *session, *next;
	int i;

	pthread_mutex_lock(&sessions->sessions_mutex);
	for (i = 0; i < HASH_SESSION_SLOTS; i++) {
		list_for_each_entry_safe(session, next, &sessions->session_hashtable[i], hlist) {
			if (!zproxy_backend_cfg_lookup(service, &session->bck_addr)) {
				if (zproxy_session_free(session) < 0)
					sessions->size--;
			}
		}
	}
	pthread_mutex_unlock(&sessions->sessions_mutex);
}
