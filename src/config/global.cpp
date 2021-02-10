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

#include "global.h"

global::run_options global::run_options::current{};
global::StartOptions global::StartOptions::current{};

global::run_options& global::run_options::getCurrent() { return current; }
global::run_options::run_options(bool overwrite_current) {}

global::StartOptions& global::StartOptions::getCurrent() { return current; }

void global::StartOptions::setCurrent(const global::StartOptions& options) {
  current.conf_file_name = options.conf_file_name;
  current.pid_file_name = options.pid_file_name;
  current.check_only = options.check_only;
  current.verbose_mode = options.verbose_mode;
  current.sync_is_enabled = options.sync_is_enabled;
}

static void print_usage(const char *prog_name)
{
	fprintf(stderr,
		"%s, high-performance multithreaded and event-driven reverse proxy and load balancer\n"
		"Version %s %s\n"
		"Usage: %s\n"
		"  [ -h | --help ]			Show this help\n"
		"  [ -s | --sync ]			Enable session synchronization\n"
		"  [ -f <FILE> | --file <FILE> ]		Launch with the given configuration file\n"
		"  [ -p <PIDFILE> | --pid <PIDFILE> ]	Set the PID file path\n"
		"  [ -c | --check ]			Check the configuration without launching it\n"
		"  [ -v | --verbose ]			Run in verbose mode\n"
		"  [ -V | --version ]			Print the proxy version\n"
		, prog_name, ZPROXY_VERSION, ZPROXY_COPYRIGHT, prog_name);
}

static const struct option options[] = {
	{ .name = "help",		.has_arg = 0,	.val = 'h' },
	{ .name = "sync",		.has_arg = 0,	.val = 's' },
	{ .name = "file",		.has_arg = 1,	.val = 'f' },
	{ .name = "pid",		.has_arg = 1,	.val = 'p' },
	{ .name = "check",		.has_arg = 0,	.val = 'c' },
	{ .name = "verbose",	.has_arg = 0,	.val = 'v' },
	{ .name = "version",	.has_arg = 0,	.val = 'V' },
	{ NULL },
};

std::unique_ptr<global::StartOptions> global::StartOptions::parsePoundOption(
	int argc, char** argv, bool write_to_current)
{
	auto res = std::make_unique<StartOptions>();
	int c;
	int opt_err = 0;

	while ((c = getopt_long(argc, argv, "hsf:cvVp:", options, NULL)) != -1) {
		switch (c) {
		case 'h':
			print_usage(argv[0]);
			exit(EXIT_SUCCESS);
		case 's':
			res->sync_is_enabled = true;
			break;
		case 'f':
			res->conf_file_name = optarg;
			break;
		case 'p':
			res->pid_file_name = optarg;
			break;
		case 'c':
			res->check_only = true;
			break;
		case 'v':
			res->verbose_mode = true;
			break;
		case 'V':
			Logger::logmsg(LOG_ALERT, "zproxy version %s", ZPROXY_VERSION);
			Logger::logmsg(LOG_ALERT, "Build: %s %s", ZPROXY_HOST_INFO,
						   ZPROXY_BUILD_INFO);
			Logger::logmsg(LOG_ALERT, "%s", ZPROXY_COPYRIGHT);
			exit(EXIT_FAILURE);
		default:
			Logger::logmsg(LOG_ERR, "bad flag -%c", optopt);
			return nullptr;
		}
	}

	if (optind < argc) {
		Logger::logmsg(LOG_ERR, "unknown extra arguments (%s...)", argv[optind]);
		exit(EXIT_FAILURE);
	}

	// we must write to the current configuration the first time we parse the
	// options
	if (write_to_current)
		current.setCurrent(*res);

	return std::move(res);
}
