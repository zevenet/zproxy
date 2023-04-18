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
#include <stdbool.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <sys/eventfd.h>
#include <errno.h>
#include <syslog.h>
#include <sys/wait.h>
#include <getopt.h>
#include <libgen.h>

#include "zproxy.h"
#include "config.h"
#include "monitor.h"
#include "service.h"
#include "worker.h"
#include "ctl.h"
#include "zcu_environment.h"
#include "zcu_backtrace.h"

#ifndef PROJECT_VERSION
#define ZPROXY_VERSION		"0.1"
#else
#define ZPROXY_VERSION		PROJECT_VERSION
#endif
#define ZPROXY_COPYRIGHT	"Copyright (C) 2023 ZEVENET S.L."
#define ZPROXY_PROG_NAME	"zproxy"

static struct zproxy_args zproxy_args;

static void print_usage(const char *prog_name)
{
	fprintf(stdout,
		"%s, high-performance multithreaded and event-driven reverse proxy and load balancer\n"
		"Version %s %s\n"
		"Usage: %s\n"
		"  [ -h | --help ]				Show this help\n"
		"  [ -D | --disable-daemon ]			Disable the daemon mode\n"
		"  [ -C <FILE> | --control <FILE>]		Configure socket control\n"
		"  [ -f <FILE> | --file <FILE> ]		Launch with the given configuration file\n"
		"  [ -p <PIDFILE> | --pid <PIDFILE> ]		Set the PID file path\n"
		"  [ -c | --check ]				Check the configuration without launching it\n"
		"  [ -l <LEVEL> | --log <LEVEL> ]		Set the syslog level\n"
		"  [ -L <OUTPUT> | --log-output <OUTPUT> ]	Set the daemon logs output: 0 syslog (default), 1 stdout, 2 stderr\n"
		"  [ -V | --version ]				Print the proxy version\n",
		ZPROXY_PROG_NAME, ZPROXY_VERSION, ZPROXY_COPYRIGHT, prog_name);
}

static const struct option options[] = {
	{ .name = "help", .has_arg = 0, .val = 'h' },
	{ .name = "disable-daemon", .has_arg = 0, .val = 'D' },
	{ .name = "control", .has_arg = 1, .val = 'C' },
	{ .name = "file", .has_arg = 1, .val = 'f' },
	{ .name = "pid", .has_arg = 1, .val = 'p' },
	{ .name = "check", .has_arg = 0, .val = 'c' },
	{ .name = "log", .has_arg = 1, .val = 'l' },
	{ .name = "log-output", .has_arg = 1, .val = 'L' },
	{ .name = "version", .has_arg = 0, .val = 'V' },
	{ NULL },
};

struct zproxy_main zproxy_main;

static int zproxy_start(struct zproxy_cfg *cfg)
{
	struct zproxy_worker *workers[cfg->num_threads];
	struct zproxy_proxy_cfg *proxy_cfg;
	int i, j, ret;

	if (zproxy_workers_create(cfg, workers, cfg->num_threads) < 0)
		return -1;

	list_for_each_entry(proxy_cfg, &cfg->proxy_list, list) {
		for (i = 0; i < cfg->num_threads; i++) {
			ret = zproxy_worker_proxy_create(proxy_cfg, workers[i]);
			if (ret < 0)
				goto err_cleanup_worker;
		}
	}

	zproxy_workers_start(workers, cfg->num_threads);

	return 0;

err_cleanup_worker:
	list_for_each_entry_continue_reverse(proxy_cfg, &cfg->proxy_list, list) {
		for (j = i - 1; j >= 0; j++)
			zproxy_worker_proxy_destroy(workers[i]);

		i = cfg->num_threads;
	}

	zproxy_workers_destroy(workers, cfg->num_threads);

	return -1;
}

int zproxy_cfg_reload(struct zproxy_cfg *cfg)
{
	zproxy_service_state_refresh(cfg);
	zproxy_monitor_refresh(cfg);
	zproxy_ctl_refresh(cfg);
	zproxy_state_cfg_update(cfg);

	if (zproxy_start(cfg) < 0) {
		syslog(LOG_ERR, "Failed to restart after config reload");
		free(cfg);
		return -1;
	}

	zproxy_worker_notify_update();

	return 0;
}

int zproxy_cfg_file_reload(void)
{
	struct zproxy_cfg *cfg;

	cfg = (struct zproxy_cfg *)calloc(1, sizeof(*cfg));
	if (!cfg) {
		syslog(LOG_ERR, "OOM when allocating configuration");
		return -1;
	}
	zproxy_cfg_init(cfg);

	cfg->args = zproxy_args;

	if (zproxy_cfg_file(cfg) < 0) {
		syslog(LOG_ERR, "Error parsing the config file");
		free(cfg);
		return -1;
	}

	if (zproxy_cfg_reload(cfg) < 0) {
		free(cfg);
		return -1;
	}

	return 0;
}

static void zproxy_main_reload_event_cb(struct ev_loop *loop, struct ev_io *io, int events)
{
	uint64_t event;

	if (events & EV_ERROR)
		return;

	if (read(zproxy_main.ev_reload_io.fd, &event, sizeof(event)) < 0)
		return;

	if (!zproxy_main.active)
		return;

	zproxy_cfg_file_reload();
}

static void zproxy_main_shutdown_event_cb(struct ev_loop *loop, struct ev_io *io, int events)
{
	uint64_t event;

	if (events & EV_ERROR)
		return;

	if (read(zproxy_main.ev_shutdown_io.fd, &event, sizeof(event)) < 0)
		return;

	zproxy_worker_notify_shutdown();
	zproxy_main.active = false;
}

static int zproxy_main_loop_init(void)
{
	int evfd;

	zproxy_main.loop = ev_loop_new(EVFLAG_AUTO);
	if (!zproxy_main.loop)
		return -1;

	evfd = eventfd(0, EFD_NONBLOCK);
	if (evfd < 0) {
		ev_loop_destroy(zproxy_main.loop);
		return -1;
	}
	ev_io_init(&zproxy_main.ev_reload_io, zproxy_main_reload_event_cb, evfd, EV_READ);

	evfd = eventfd(0, EFD_NONBLOCK);
	if (evfd < 0) {
		close(zproxy_main.ev_reload_io.fd);
		ev_loop_destroy(zproxy_main.loop);
		return -1;
	}
	ev_io_init(&zproxy_main.ev_shutdown_io, zproxy_main_shutdown_event_cb, evfd, EV_READ);

	ev_io_start(zproxy_main.loop, &zproxy_main.ev_reload_io);
	ev_io_start(zproxy_main.loop, &zproxy_main.ev_shutdown_io);

	zproxy_main.active = true;

	return 0;
}

static void zproxy_main_loop_run(void)
{
	while (zproxy_main.active || zproxy_main.num_conn > 0) {
		ev_loop(zproxy_main.loop, EVRUN_ONCE);
		zproxy_workers_cleanup();
	}
}

static void zproxy_main_loop_destroy(void)
{
	ev_io_stop(zproxy_main.loop, &zproxy_main.ev_reload_io);
	ev_io_stop(zproxy_main.loop, &zproxy_main.ev_shutdown_io);
	ev_loop_destroy(zproxy_main.loop);
}

static void zproxy_main_notify_update(void)
{
	uint64_t event = 1;

	write(zproxy_main.ev_reload_io.fd, &event, sizeof(event));
}

static void zproxy_main_notify_shutdown(void)
{
	uint64_t event = 1;

	write(zproxy_main.ev_shutdown_io.fd, &event, sizeof(event));
}

static void zproxy_sigusr1(int signum)
{
	syslog(LOG_INFO, "SIGUSR1 has been received");
	zproxy_main_notify_update();
}

static void zproxy_sigterm(int signum)
{
	syslog(LOG_INFO, "SIGTERM has been received, shutting down");
	zproxy_main_notify_shutdown();
}

static void zproxy_sig_bt(int signum)
{
	syslog(LOG_INFO, "%s has been received", strsignal(signum));
	zcu_bt_print_symbols();
	exit(EXIT_FAILURE);
}

static void zproxy_args_init(struct zproxy_args *args)
{
	args->log_level = DEFAULT_LOG_LEVEL;
	args->log_output = DEFAULT_LOG_OUTPUT;
	args->daemon = DEFAULT_DAEMON;
	snprintf(args->ctrl_socket, CONFIG_IDENT_MAX, "%s", DEFAULT_CTRLSOCKET);
}

static bool zproxy_path_is_valid(const char *path)
{
	struct stat dir_stat;
	char *dir_path;

	dir_path = strdup(path);
	if (!dir_path)
		return false;

	dir_path = dirname(dir_path);

	if (stat(dir_path, &dir_stat) < 0) {
		fprintf(stderr, "ERROR: cannot access directory `%s': %s\n",
			dir_path, strerror(errno));
		free(dir_path);
		return false;
	}

	if (!S_ISDIR(dir_stat.st_mode)) {
		fprintf(stderr, "ERROR: path `%s' is not a directory\n", dir_path);
		free(dir_path);
		return false;
	}

	free(dir_path);

	return true;
}

int main(int argc, char *argv[])
{
	int check_only = DEFAULT_CHECKONLY;
	struct zproxy_cfg *cfg;
	int ret;
	int c;

	if (signal(SIGPIPE, SIG_IGN) == SIG_ERR)
		exit(EXIT_FAILURE);
	if (signal(SIGUSR1, zproxy_sigusr1) == SIG_ERR)
		exit(EXIT_FAILURE);
	if (signal(SIGTERM, zproxy_sigterm) == SIG_ERR)
		exit(EXIT_FAILURE);
	if (signal(SIGINT, zproxy_sigterm) == SIG_ERR)
		exit(EXIT_FAILURE);
	if (signal(SIGSEGV, zproxy_sig_bt) == SIG_ERR)
		exit(EXIT_FAILURE);
	if (signal(SIGABRT, zproxy_sig_bt) == SIG_ERR)
		exit(EXIT_FAILURE);

	zproxy_args_init(&zproxy_args);

	while ((c = getopt_long(argc, argv, "hDC:f:cl:L:Vp:", options, NULL)) != -1) {
		switch (c) {
		case 'h':
			print_usage(argv[0]);
			exit(EXIT_SUCCESS);
		case 'D':
			zproxy_args.daemon = false;
			break;
		case 'C':
			snprintf(zproxy_args.ctrl_socket, CONFIG_IDENT_MAX, "%s", optarg);
			if (!zproxy_path_is_valid(zproxy_args.ctrl_socket))
				exit(EXIT_FAILURE);
			break;
		case 'f':
			zproxy_args.conf_file_name = optarg;
			break;
		case 'p':
			zproxy_args.pid_file_name = optarg;
			break;
		case 'c':
			check_only = true;
			break;
		case 'l':
			zproxy_args.log_level = atoi(optarg);
			zcu_log_set_level(zproxy_args.log_level);
			break;
		case 'L':
			zproxy_args.log_output = atoi(optarg);
			zcu_log_set_output(zproxy_args.log_output);
			break;
		case 'V':
			fprintf(stdout,
				"zproxy version %s\n"
				"%s\n",
				ZPROXY_VERSION, ZPROXY_COPYRIGHT);
			exit(EXIT_SUCCESS);
		default:
			zcu_log_print(LOG_ERR, "bad flag -%c", optopt);
			exit(EXIT_FAILURE);
		}
	}

	if (optind < argc) {
		fprintf(stderr, "Unknown extra arguments (%s...)\n", argv[optind]);
		exit(EXIT_FAILURE);
	}

	if (!zproxy_args.conf_file_name) {
		fprintf(stderr, "You have to specify a config file via -f\n");
		exit(EXIT_FAILURE);
	}

	cfg = (struct zproxy_cfg *)calloc(1, sizeof(*cfg));
	if (!cfg) {
		syslog(LOG_ERR, "OOM when allocating configuration");
		exit(EXIT_FAILURE);
	}
	zproxy_cfg_init(cfg);

	cfg->args = zproxy_args;

	if (zproxy_cfg_file(cfg) < 0) {
		syslog(LOG_ERR, "Error parsing the config file");
		free(cfg);
		exit(EXIT_FAILURE);
	}

	if (check_only) {
		fprintf(stdout, "Config file %s is OK\n", cfg->args.conf_file_name);
		exit(EXIT_SUCCESS);
	}

	if (zproxy_args.daemon) {
		ret = fork();
		if (ret < 0) {
			fprintf(stderr, "Failed to fork() daemon\n");
			exit(EXIT_FAILURE);
		} else if (ret > 0) {
			exit(EXIT_SUCCESS);
		}

		close(STDIN_FILENO);
		close(STDOUT_FILENO);
		close(STDERR_FILENO);
		umask(0177);
	}
	if (cfg->args.pid_file_name)
		createPidFile(cfg->args.pid_file_name, getpid());

	if (zproxy_main_loop_init() < 0)
		exit(EXIT_FAILURE);

	if (zproxy_service_state_init(cfg) < 0)
		exit(EXIT_FAILURE);

	if (zproxy_monitor_create(cfg) < 0)
		exit(EXIT_FAILURE);

	if (zproxy_ctl_create(cfg) < 0) {
		syslog(LOG_ERR, "ERROR: cannot create control socket `%s': %s\n",
		       cfg->args.ctrl_socket, strerror(errno));
		exit(EXIT_FAILURE);
	}

	if (zproxy_start(cfg) < 0)
		exit(EXIT_FAILURE);

	zproxy_main_loop_run();

	zproxy_workers_wait();
	zproxy_monitor_destroy();
	zproxy_ctl_destroy();
	zproxy_service_state_fini();
	zproxy_main_loop_destroy();

	return EXIT_SUCCESS;
}
