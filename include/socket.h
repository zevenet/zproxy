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

#ifndef _ZPROXY_SOCKET_H
#define _ZPROXY_SOCKET_H

/**
 * Setup the socket listener for the proxy.
 *
 * @param addr Socket address to listen on.
 * @return On success it returns the socket file descriptor (>0); on failure it
 * returns -1.
 */
int zproxy_socket_server_setup(const struct sockaddr_in *local_addr);

/**
 * Connects a client to a provided backend and returns the socket in the sd
 * parameter.
 *
 * @param backend_addr Socket address of the backend.
 * @param sd The new remote socket file descriptor.
 * @return On success 0; on failture -1.
 */
int zproxy_client_connect(const struct sockaddr_in *backend_addr, int *sd, int nf_mark);

int zproxy_server_unix_main_setup(const char *main_path);
void zproxy_server_unix_main_stop(int sd, const char *main_path);

#endif
