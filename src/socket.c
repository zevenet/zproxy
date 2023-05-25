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

#include <stdlib.h>
#include <stdint.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <arpa/inet.h>
#include <fcntl.h>
#include <syslog.h>
#include <ev.h>
#include <errno.h>
#include <assert.h>
#include <stdio.h>
#include "socket.h"
#include "ctl.h"
#include "zcu_network.h"
#include "zcu_log.h"

#define ZPROXY_LISTENER 250

int zproxy_socket_server_setup(const struct sockaddr_in *addr)
{
	struct sockaddr_in local;
	int sd, ret, on = 1;

	sd = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
	if (sd < 0) {
		zcu_log_print(LOG_ERR, "cannot create main socket\n");
		return -1;
	}

	ret = setsockopt(sd, SOL_SOCKET, SO_REUSEPORT, &on, sizeof(on));
	if (ret < 0) {
		zcu_log_print(LOG_ERR, "cannot set on SO_REUSEPORT\n");
		return -1;
	}

	on = 1;
	ret = setsockopt(sd, IPPROTO_TCP, TCP_NODELAY, &on, sizeof(on));
	if (ret < 0) {
		zcu_log_print(LOG_ERR, "cannot set on TCP_NODELAY\n");
		return -1;
	}

	on = 1;
	ret = setsockopt(sd, SOL_SOCKET, SO_KEEPALIVE, &on, sizeof(on));
	if (ret < 0) {
		zcu_log_print(LOG_ERR, "cannot set on SO_KEEPALIVE\n");
		return -1;
	}

	memcpy(&local, addr, sizeof(*addr));

	if (bind(sd, (struct sockaddr *) &local, sizeof(local)) < 0) {
		close(sd);
		zcu_log_print(LOG_ERR, "cannot bind socket\n");
		return -1;
	}

	listen(sd, ZPROXY_LISTENER);

	return sd;
}

int zproxy_client_connect(const struct sockaddr_in *backend_addr, int *sd, int nf_mark)
{
	int remote_fd, flags, len, ret, on = 1;

	*sd = -1;
	remote_fd = socket(AF_INET, SOCK_STREAM, 0);
	if (remote_fd < 0)
		return -1;

	flags = fcntl(remote_fd, F_GETFL);
	flags |= O_NONBLOCK;
	ret = fcntl(remote_fd, F_SETFL, flags);
	if (ret < 0)
		return ret;

	ret = setsockopt(remote_fd, IPPROTO_TCP, TCP_NODELAY, &on, sizeof(on));
	if (ret < 0)
		return ret;

	on = 1;
	ret = setsockopt(remote_fd, SOL_SOCKET, SO_KEEPALIVE, &on, sizeof(on));
	if (ret < 0)
		return ret;

	if (nf_mark > 0)
		setsockopt(remote_fd, SOL_SOCKET, SO_MARK, &nf_mark, sizeof(nf_mark));

	len = sizeof(*backend_addr);
	*sd = remote_fd;

	return connect(remote_fd, (struct sockaddr *)backend_addr, len);
}

#define ZPROXY_CTL_LISTEN	10

static int zproxy_server_unix_setup(const char *path)
{
	struct sockaddr_un local = {
		.sun_family	= AF_UNIX,
	};
	int sd, reuseaddr = 1, len, err;

	sd = socket(AF_UNIX, SOCK_STREAM, 0);
	if (sd < 0)
		return -1;

	err = setsockopt(sd, SOL_SOCKET, SO_REUSEADDR, &reuseaddr,
			sizeof(reuseaddr));
	if (err < 0)
		goto err_out;

	snprintf(local.sun_path, sizeof(local.sun_path), "%s", path);
	len = strlen(local.sun_path) + sizeof(local.sun_family);
	unlink(local.sun_path);

	err = bind(sd, (struct sockaddr *)&local, len);
	if (err < 0)
		goto err_out;

	listen(sd, ZPROXY_CTL_LISTEN);

	return sd;

err_out:
	close(sd);

	return -1;
}

int zproxy_server_unix_main_setup(const char *main_path)
{
	return zproxy_server_unix_setup(main_path);
}

void zproxy_server_unix_main_stop(int sd, const char *main_path)
{
	unlink(main_path);
	close(sd);
}
