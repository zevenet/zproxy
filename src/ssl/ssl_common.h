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

#include <openssl/err.h>
#include <openssl/ssl.h>
#include <string>
#include <memory>
#include "../../zcutils/zcutils.h"

namespace ssl
{
enum class SSL_STATUS {
	NONE,
	WANT_READ,
	WANT_WRITE,
	NEED_HANDSHAKE,
	HANDSHAKE_START,
	HANDSHAKE_DONE,
	HANDSHAKE_ERROR,
	SSL_ERROR
};

inline std::string getSslStatusString(SSL_STATUS status)
{
	switch (status) {
	case SSL_STATUS::NONE:
		return "NONE";
	case SSL_STATUS::WANT_READ:
		return "WANT_READ";
	case SSL_STATUS::WANT_WRITE:
		return "WANT_WRITE";
	case SSL_STATUS::NEED_HANDSHAKE:
		return "NEED_HANDSHAKE";
	case SSL_STATUS::HANDSHAKE_START:
		return "HANDSHAKE_START";
	case SSL_STATUS::HANDSHAKE_DONE:
		return "HANDSHAKE_DONE";
	case SSL_STATUS::HANDSHAKE_ERROR:
		return "HANDSHAKE_ERROR";
	case SSL_STATUS::SSL_ERROR:
		return "SSL_ERROR";
	}
}

typedef void (*SslInfoCallback)();

/*
 * Get a "line" from a BIO, strip the trailing newline, skip the input stream if buffer too small
 * The result buffer is NULL terminated
 * Return 0 on success
 */
static int get_line(BIO *const in, char *const buf, const int bufsize,
		    int *out_line_size)
{
	char tmp;
	int i, n_read;

	//    memset(buf, 0, bufsize);
	*out_line_size = 0;
	for (n_read = 0;;)
		switch (BIO_gets(in, buf + n_read, bufsize - n_read - 1)) {
		case -2:
			/* BIO_gets not implemented */
			return -1;
		case 0:
		case -1:
			return 1;
		default:
			for (i = n_read; i < bufsize && buf[i]; i++)
				if (buf[i] == '\n' || buf[i] == '\r') {
					buf[i] = '\0';
					*out_line_size = i;
					return 0;
				}
			if (i < bufsize) {
				n_read = i;
				continue;
			}
			zcu_log_print(LOG_NOTICE, "(%lx) line too long: %s",
				      pthread_self(), buf);
			/* skip rest of "line" */
			tmp = '\0';
			while (tmp != '\n')
				if (BIO_read(in, &tmp, 1) != 1)
					return 1;
			break;
		}
}

static std::unique_ptr<char> ossGetErrorStackString(void)
{
	BIO *bio = BIO_new(BIO_s_mem());
	ERR_print_errors(bio);
	char *buf = nullptr;
	size_t len = BIO_get_mem_data(bio, &buf);
	char *ret = (char *)calloc(1, 1 + len);
	if (ret)
		memcpy(ret, buf, len);
	BIO_free(bio);
	return std::unique_ptr<char>(ret);
}

static std::unique_ptr<char> ossGetSslSessionInfo(const SSL_SESSION *ses)
{
	if (ses == nullptr)
		return nullptr;
	BIO *bio = BIO_new(BIO_s_mem());
	char *buf = nullptr;
	if (SSL_SESSION_print(bio, ses) == 0)
		return nullptr;
	size_t len = BIO_get_mem_data(bio, &buf);
	char *ret = (char *)calloc(1, 1 + len);
	if (ret)
		memcpy(ret, buf, len);
	BIO_free(bio);
	return std::unique_ptr<char>(ret);
}

inline static void logSslErrorStack(void)
{
	unsigned long err;
	while ((err = ERR_get_error()) != 0) {
		char details[256];
		ERR_error_string_n(static_cast<uint32_t>(err), details,
				   sizeof(details));
		zcu_log_print(LOG_ERR, "%s", details);
	}
}

static const char *getErrorString(int error)
{
	switch (error) {
	case SSL_ERROR_NONE:
		return "SSL_ERROR_NONE";
	case SSL_ERROR_ZERO_RETURN:
		return "SSL_ERROR_ZERO_RETURN";
	case SSL_ERROR_WANT_READ:
		return "SSL_ERROR_WANT_READ";
	case SSL_ERROR_WANT_WRITE:
		return "SSL_ERROR_WANT_WRITE";
	case SSL_ERROR_WANT_CONNECT:
		return "SSL_ERROR_WANT_CONNECT";
	case SSL_ERROR_WANT_ACCEPT:
		return "SSL_ERROR_WANT_ACCEPT";
	case SSL_ERROR_WANT_X509_LOOKUP:
		return "SSL_ERROR_WANT_X509_LOOKUP";
	case SSL_ERROR_SYSCALL:
		return "SSL_ERROR_SYSCALL";
	case SSL_ERROR_SSL:
		return "SSL_ERROR_SSL";
	default:
		return "Unknown error";
	}
}
} // namespace ssl
