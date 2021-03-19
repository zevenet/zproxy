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

#include "../version.h"
#include "ssl_helper.h"
#include "../../zcutils/zcutils.h"
#include <memory>
#include <getopt.h>
#include <string>

namespace global
{
	struct run_options
	{
		explicit run_options(bool write_to_current = false);
		static run_options & getCurrent();
		int num_threads
		{
		0};		/*number of StreamManagers to use (workers) */
		int log_level
		{
		5};		/*default log leves */
		int log_facility
		{
		LOG_DAEMON};	/*syslog log facility to use */
		  std::string user;	/* user to run as */
		  std::string group;	/* group to run as */
		  std::string pid_name;	/* file to record pid in */
		  std::string ctrl_name;	/* API control unix socket name */
		  std::string ctrl_ip;	/* API control socket ip */
		  std::string ctrl_user;	/* API control socket username */
		  std::string ctrl_group;	/* API control socket group name */
		long ctrl_mode
		{
		-1};		/* octal mode of the control socket */
		bool daemonize
		{
		true};		/* run as daemon */
		int backend_resurrect_timeout
		{
		10};		/* time in seconds for backend resurrection check */
		// TODO::To implement
		int grace_time
		{
		30};		/* Grace time before forcing shutdown */
		  std::string root_jail;	/* directory to chroot to */
		  std::string config_file_name;
	      private:
		static struct run_options current;
	};

	struct StartOptions
	{
		std::string conf_file_name;
		std::string pid_file_name;
		bool show_version
		{
		false};
		bool disable_daemon
		{
		false};
		bool check_only
		{
		false};
		bool sync_is_enabled
		{
		false};
		bool verbose_mode
		{
		false};
		int loglevel = zcu_log_level;
		int logoutput = zcu_log_output;

		/*Set current start options as global, this must be called at least once */
		void setCurrent(const StartOptions & options);
		static std::unique_ptr < StartOptions >
			parsePoundOption(int argc, char **argv,
					 bool write_to_current = false);

		static StartOptions & getCurrent();
	      private:
		static struct StartOptions current;
	};
};				// namespace global
