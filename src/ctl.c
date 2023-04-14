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

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <pcreposix.h>
#include <string>
#include <pthread.h>
#include <syslog.h>
#include <fcntl.h>
#include <sys/socket.h>
#include <sys/un.h>
#include "zcu_log.h"
#include "zproxy.h"
#include "socket.h"
#include "ctl.h"
#include "http_request.h"
#include "worker.h"
#include "config.h"

static struct {
	struct ev_io		io;
	struct list_head	conn_list;
	const struct zproxy_cfg	*cfg;
} zproxy_ctl;

static void zproxy_ctl_conn_free(struct ev_loop *loop,
				 struct zproxy_ctl_conn *ctl)
{
	close(ctl->io.fd);
	ev_io_stop(loop, &ctl->io);
	ev_timer_stop(loop, &ctl->timer);
	list_del(&ctl->list);
	zproxy_cfg_free(ctl->cfg);
	zproxy_main.num_conn--;
	free(ctl);
}

static void zproxy_ctl_timer_cb(struct ev_loop *loop, ev_timer *timer, int events)
{
	struct zproxy_ctl_conn *ctl;

	ctl = container_of(timer, struct zproxy_ctl_conn, timer);

	syslog(LOG_ERR, "timeout request to control socket, this should not ever happen!\n");

	zproxy_ctl_conn_free(loop, ctl);
}

void zproxy_ctl_cb(struct ev_loop *loop, struct ev_io *io, int events)
{
	struct zproxy_ctl_conn *ctl;
	int32_t body_len;
	const char *ptr;
	int ret;

	if (events & EV_ERROR)
		return;

	ctl = container_of(io, struct zproxy_ctl_conn, io);

	ret = recv(ctl->io.fd, &ctl->buf[ctl->buf_len],
		   sizeof(ctl->buf) - ctl->buf_len, 0);
	if (ret <= 0)
		goto err_out;

	ctl->buf_len += ret;

	if (ctl->content_len < 0) {
		ctl->buf[sizeof(ctl->buf) - 1] = '\0';

		ptr = strstr(ctl->buf, "Content-Length: ");
		if (ptr)
			sscanf(ptr, "Content-Length: %i[^\r\n]", &ctl->content_len);
	}

	ptr = strstr(ctl->buf, "\r\n\r\n");
	if (!ptr)
		return;

	body_len = ctl->buf_len - (ptr + 4 - ctl->buf);

	if (ctl->content_len >= 0 && ctl->content_len != body_len)
		return;

	zcu_log_print(LOG_INFO, "received control command");

	if (ctl->cb)
		ctl->cb(ctl, zproxy_ctl.cfg);
err_out:
	zproxy_ctl_conn_free(loop, ctl);
}

struct zproxy_ctl_conn *
zproxy_ctl_accept(struct ev_io *io,
		int (*cb)(const struct zproxy_ctl_conn *ctl, const struct zproxy_cfg *cfg))
{
	socklen_t addrlen = sizeof(struct sockaddr_un);
	struct zproxy_ctl_conn *ctl;
	struct sockaddr_un local;
	int fd, flags;

	fd = accept(io->fd, (struct sockaddr *)&local, &addrlen);
	if (fd < 0)
		return NULL;

	flags = fcntl(fd, F_GETFL);
	fcntl(fd, F_SETFL, flags | O_NONBLOCK);

	ctl = (struct zproxy_ctl_conn *)calloc(1, sizeof(*ctl));
	if (!ctl) {
		close(fd);
		return NULL;
	}

	ctl->cfg = zproxy_cfg_get(zproxy_ctl.cfg);
	ctl->content_len = -1;
	ctl->cb = cb;
	ev_init(&ctl->timer, zproxy_ctl_timer_cb);
	ctl->timer.repeat = 10.;
	ev_timer_again(zproxy_main.loop, &ctl->timer);

	ev_io_init(&ctl->io, zproxy_ctl_cb, fd, EV_READ);

	zproxy_main.num_conn++;
	ev_io_start(zproxy_main.loop, &ctl->io);

	return ctl;
}

void zproxy_ctl_server_cb(struct ev_loop *loop, struct ev_io *io, int events)
{
	struct zproxy_ctl_conn *conn;

	if (events & EV_ERROR)
		return;

	conn = zproxy_ctl_accept(&zproxy_ctl.io, ctl_handler_cb);
	if (!conn)
		return;

	list_add_tail(&conn->list, &zproxy_ctl.conn_list);
}

void zproxy_ctl_refresh(const struct zproxy_cfg *cfg)
{
	const struct zproxy_cfg *old_cfg = NULL;

	if (zproxy_ctl.cfg)
		old_cfg = zproxy_ctl.cfg;

	zproxy_ctl.cfg = zproxy_cfg_get(cfg);

	if (old_cfg)
		zproxy_cfg_free(old_cfg);
}

int zproxy_ctl_create(const struct zproxy_cfg *cfg)
{
	int sd;

	zproxy_ctl_refresh(cfg);
	INIT_LIST_HEAD(&zproxy_ctl.conn_list);

	sd = zproxy_server_unix_main_setup(cfg->args.ctrl_socket);
	if (sd < 0)
		return -1;

	ev_io_init(&zproxy_ctl.io, zproxy_ctl_server_cb, sd, EV_READ);
	ev_io_start(zproxy_main.loop, &zproxy_ctl.io);

	return 0;
}

void zproxy_ctl_destroy(void)
{
	ev_io_stop(zproxy_main.loop, &zproxy_ctl.io);
	zproxy_server_unix_main_stop(zproxy_ctl.io.fd,
				     zproxy_ctl.cfg->args.ctrl_socket);
	zproxy_cfg_free(zproxy_ctl.cfg);
}
