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
#pragma once

#include <openssl/ssl.h>
#include <cstring>
#include <list>
#include <mutex>

#define MAX_ENCODING_SIZE 4096
#define MAX_ID_SIZE 512
namespace ssl
{
typedef struct {
	unsigned int sess_id_size;
	unsigned char sess_id[MAX_ID_SIZE];
	size_t encoding_length;
	unsigned char encoding_data[MAX_ENCODING_SIZE];
} SslSessionData;

class SslSessionManager {
    public:
	std::list<SslSessionData *> sessions;
	static std::mutex singleton_mtx;
	static SslSessionManager *getInstance();
	int addSession(SSL *ssl, SSL_SESSION *session);
	SSL_SESSION *getSession(SSL *ssl, const unsigned char *id,
				int id_length, int *do_copy);
	void deleteSession(SSL_CTX *sctx, SSL_SESSION *session);
	static void attachCallbacks(SSL_CTX *sctx);
	static int addSessionCb(SSL *ssl, SSL_SESSION *session);
	static SSL_SESSION *getSessionCb(SSL *ssl, const unsigned char *id,
					 int id_length, int *do_copy);
	static void deleteSessionCb(SSL_CTX *sctx, SSL_SESSION *session);

    private:
	static SslSessionManager *ssl_session_manager;
	std::mutex data_mtx;

	SslSessionManager();
	virtual ~SslSessionManager();
	void removeSessionId(const unsigned char *id, int idLength);
};
} // namespace ssl
