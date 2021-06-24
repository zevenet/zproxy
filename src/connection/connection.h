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

#include "../../zcutils/zcutils.h"
#include "../../zcutils/zcu_network.h"
#include "../event/descriptor.h"
#include "../experimental/string_buffer.h"
#include "../http/http_request.h"
#include "../ssl/ssl_common.h"
#include "../util/utils.h"
#include "../util/common.h"
#include <atomic>
#include <fcntl.h>
#include <netdb.h>
#include <unistd.h>
#include <sys/un.h>
#include <sys/uio.h>

#ifndef MAX_DATA_SIZE
#define MAX_DATA_SIZE (1024 * 64)
#endif

#define FAKE_ZERO_COPY 0

#if ENABLE_ZERO_COPY

#define BUFSZ MAX_DATA_SIZE

struct SplicePipe {
	int pipe[2];
	int bytes{ 0 };
	SplicePipe()
	{
		if (pipe2(pipe, O_NONBLOCK) < 0) {
			perror("pipe");
		}
	}
	~SplicePipe()
	{
		close(pipe[0]);
		close(pipe[1]);
	}
};

#endif
using namespace events;
class Connection : public Descriptor {
    protected:
	IO::IO_RESULT writeTo(int target_fd, http_parser::HttpData &http_data);

    public:
	timeval time_start;
//  std::time_t date;
//  std::string str_buffer;
#if ENABLE_ZERO_COPY
	SplicePipe splice_pipe;
#if FAKE_ZERO_COPY
	char buffer_aux[MAX_DATA_SIZE];
#endif
#endif
	std::string address_str{ "" }; // the remote socket ip
	std::string local_address_str{ "" }; // the local socket ip
	int port{ -1 }; // the remote socket port
	int local_port{ -1 }; // the local socket port
	addrinfo *address;

	// StringBuffer string_buffer;
	char buffer[MAX_DATA_SIZE];
	size_t buffer_size{ 0 };
	size_t buffer_offset{ 0 }; // TODO::REMOVE
	std::string getPeerAddress();
	std::string getLocalAddress();
	int getPeerPort();
	int getLocalPort();
	void reset();
	void freeSsl();
#if ENABLE_ZERO_COPY
	IO::IO_RESULT zeroRead();
	IO::IO_RESULT zeroWrite(int dst_fd, http_parser::HttpData &http_data);
#endif
	static IO::IO_RESULT writeIOvec(int target_fd, iovec *iov,
					size_t iovec_size,
					size_t &iovec_written,
					size_t &nwritten);
	IO::IO_RESULT write(const char *data, size_t size, size_t &sent);
	IO::IO_RESULT writeTo(int fd, size_t &sent);
	IO::IO_RESULT writeTo(const Connection &target_connection,
			      http_parser::HttpData &http_data);

	IO::IO_RESULT read();

	void closeConnection();
	Connection();
	virtual ~Connection();

	bool listen(const std::string &address_str_, int port_);
	static int listen(const addrinfo &address_);
	bool listen(const std::string &af_unix_name);

	static int doAccept(int listener_fd);
	IO::IO_OP doConnect(addrinfo &address, int timeout, bool async = true,
			    int nf_mark = 0);
	IO::IO_OP doConnect(const std::string &af_unix_socket_path,
			    int timeout);
	bool isConnected();
	// SSL stuff
    public:
	ssl::SSL_STATUS ssl_conn_status{ ssl::SSL_STATUS::NONE };
	int handshake_retries{ 0 };
	SSL *ssl{ nullptr };
	// socket bio
	BIO *sbio{ nullptr };
	// buffer bio
	BIO *io{ nullptr };
	// ssl bio
	BIO *ssl_bio{ nullptr };
	const char *server_name{ nullptr };
	std::atomic<bool> ssl_connected;
};
