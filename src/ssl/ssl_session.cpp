/*
 *    Zevenet zproxy Load Balancer Software License
 *    This file is part of the Zevenet zproxy Load Balancer software package.
 *
 *    Copyright (C) 2019-today ZEVENET SL, Sevilla (Spain)
 *
 *    This program is free software: you can redistribute it and/or modify
 *    it under the terms of the GNU Affero General Public License as
 *    published by the Free Software Foundation, either version 3 of the
 *    License, or any later version.
 *
 *    This program is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *    GNU Affero General Public License for more details.
 *
 *    You should have received a copy of the GNU Affero General Public License
 *    along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 */
#include "ssl_session.h"
#include "../../zcutils/zcutils.h"

using namespace ssl;

SslSessionManager *SslSessionManager::ssl_session_manager = nullptr;
std::mutex SslSessionManager::singleton_mtx{};

SslSessionManager *SslSessionManager::getInstance()
{
	std::lock_guard<std::mutex> instance_lock(singleton_mtx);
	if (ssl_session_manager == nullptr)
		ssl_session_manager = new SslSessionManager();
	return ssl_session_manager;
}

void SslSessionManager::removeSessionId(const unsigned char *id, int idLength)
{
	zcu_log_print(LOG_ERR, "SESSION DELETE id: %s", id);
	std::lock_guard<std::mutex> lock(data_mtx);
	auto i = sessions.begin();
	while (i != sessions.end()) {
		if (std::memcmp((*i)->sess_id, id, idLength) == 0) {
			delete (*i);
			sessions.erase(i++);
		} else
			++i;
	}
}

int SslSessionManager::addSession(SSL *ssl, SSL_SESSION *session)
{
	auto encoded_length = i2d_SSL_SESSION(session, NULL);

	unsigned char *buff;
	unsigned int id_length;
	const unsigned char *id = SSL_SESSION_get_id(session, &id_length);
	zcu_log_print(LOG_ERR, "SESSION ADD id: %s", id);
	removeSessionId(id, id_length);
	std::lock_guard<std::mutex> lock(data_mtx);

	auto *data = new SslSessionData();

	buff = data->encoding_data;

	i2d_SSL_SESSION(session, &buff);

	memcpy(data->sess_id, id, id_length);
	data->encoding_length = encoded_length;
	data->sess_id_size = id_length;

	sessions.push_back(data);
	return 1;
}

SSL_SESSION *SslSessionManager::getSession(SSL *ssl, const unsigned char *id,
					   int id_length, int *do_copy)
{
	unsigned char *buff;
	std::lock_guard<std::mutex> lock(data_mtx);
	zcu_log_print(LOG_DEBUG, "%s():%d: session get id %x", __FUNCTION__,
		      __LINE__, id);
	*do_copy = 0;

	for (auto data : sessions) {
		if (std::memcmp(data->sess_id, id, id_length) == 0) {
			buff = (unsigned char *)malloc(data->encoding_length);
			memcpy(buff, data->encoding_data,
			       data->encoding_length);
			return d2i_SSL_SESSION(NULL,
					       (const unsigned char **)&buff,
					       data->encoding_length);
		}
	}

	return NULL;
}

void SslSessionManager::deleteSession(SSL_CTX *sctx, SSL_SESSION *session)
{
	unsigned int id_length;
	const unsigned char *id = SSL_SESSION_get_id(session, &id_length);
	removeSessionId(id, id_length);
}

SslSessionManager::SslSessionManager()
{
}

SslSessionManager::~SslSessionManager()
{
	for (auto data : sessions) {
		delete data;
	}
}

void SslSessionManager::attachCallbacks(SSL_CTX *sctx)
{
	SSL_CTX_set_session_cache_mode(sctx, SSL_SESS_CACHE_NO_INTERNAL |
						     SSL_SESS_CACHE_SERVER);
	SSL_CTX_sess_set_new_cb(sctx, addSessionCb);
	SSL_CTX_sess_set_get_cb(sctx, getSessionCb);
	SSL_CTX_sess_set_remove_cb(sctx, deleteSessionCb);
}

int SslSessionManager::addSessionCb(SSL *ssl, SSL_SESSION *session)
{
	return getInstance()->addSession(ssl, session);
}

SSL_SESSION *SslSessionManager::getSessionCb(SSL *ssl, const unsigned char *id,
					     int id_length, int *do_copy)
{
	return getInstance()->getSession(ssl, id, id_length, do_copy);
}

void SslSessionManager::deleteSessionCb(SSL_CTX *sctx, SSL_SESSION *session)
{
	return getInstance()->deleteSession(sctx, session);
}
