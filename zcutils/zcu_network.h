/*
 *   This file is part of zcutils, ZEVENET Core Utils.
 *
 *   Copyright (C) ZEVENET SL.
 *   Author: Laura Garcia <laura.garcia@zevenet.com>
 *
 *   This program is free software: you can redistribute it and/or modify
 *   it under the terms of the GNU Affero General Public License as
 *   published by the Free Software Foundation, either version 3 of the
 *   License, or any later version.
 *
 *   This program is distributed in the hope that it will be useful,
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *   GNU Affero General Public License for more details.
 *
 *   You should have received a copy of the GNU Affero General Public License
 *   along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 */

#ifndef _ZCU_NETWORK_H_
#define _ZCU_NETWORK_H_

#include "zcutils.h"
#include <arpa/inet.h>
#include <fcntl.h>
#include <netdb.h>
#include <netinet/tcp.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <sys/un.h>
#include <cstring>
#include <string>
#include <memory>

/****  SOCKET  ****/

int zcu_soc_get_local_port(int socket_fd);

bool zcu_soc_equal_sockaddr(sockaddr *addr1, sockaddr *addr2,
			    bool compare_port = true);

char *zcu_soc_get_peer_address(int socket_fd, char *buf, size_t bufsiz,
			       bool include_port = false);
int zcu_soc_get_peer_port(int socket_fd);

char *zcu_soc_get_local_address(int socket_fd, char *buf, size_t bufsiz,
				bool include_port = false);

bool zcu_soc_set_socket_non_blocking(int fd, bool blocking = false);

bool zcu_soc_set_timeout(int sock_fd, unsigned int seconds);

bool zcu_soc_set_soreuseaddroption(int sock_fd);

bool zcu_soc_set_tcpreuseportoption(int sock_fd);

bool zcu_soc_set_tcpnodelayoption(int sock_fd);

bool zcu_soc_set_tcpdeferacceptoption(int sock_fd);

bool zcu_soc_set_sokeepaliveoption(int sock_fd);

bool zcu_soc_set_solingeroption(int sock_fd, bool enable = false);

bool zcu_soc_set_tcplinger2option(int sock_fd);

/*useful for use with send file, wait 200 ms to to fill TCP packet */
bool zcu_soc_set_tcpcorkoption(int sock_fd);

#ifdef SO_ZEROCOPY
/*useful for use with send file, wait 200 ms to to fill TCP packet */
bool zcu_soc_set_sozerocopy(int sock_fd);

#endif
// set netfilter mark, need root privileges
bool zcu_soc_set_somarkoption(int sock_fd, int nf_mark);

bool zcu_soc_isconnected(int sock_fd);

/*return -1 in case of erro and set errno */
int zcu_soc_get_socketsendbuffersize(int socket_fd);

/*return -1 in case of erro and set errno */
int zcu_soc_get_socketreceivebuffersize(int socket_fd);

int zcu_soc_set_socketsendbuffersize(int socket_fd, unsigned int new_size);

int zcu_soc_set_socketreceivebuffersize(int socket_fd, unsigned int new_size);

/****  NET  ****/

/*
	 * Search for a host name_, return the addrinfo for it
	 */
int zcu_net_get_host(const char *name, addrinfo *res, int ai_family = AF_UNSPEC,
		     int port = 0);

std::unique_ptr<addrinfo, decltype(&::freeaddrinfo)>
zcu_net_get_address(const std::string &address, int port = 0);

int zcu_net_get_peer_port(struct addrinfo *addr);

/*
	 * Translate inet/inet6 address/port into a string
	 */
void zcu_net_addr2str(char *const res, size_t res_len,
		      const struct addrinfo *addr, bool include_port = false);

bool zcu_net_equal_sockaddr(addrinfo *x, addrinfo *y, bool compare_port = true);

#endif /* _ZCU_NETWORK_H_ */
