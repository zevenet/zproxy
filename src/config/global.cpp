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



global::StartOptions& global::StartOptions::getCurrent() {
  return current; }

void global::StartOptions::setCurrent(const global::StartOptions& options) {
  current.conf_file_name = options.conf_file_name;
  current.pid_file_name = options.pid_file_name;
  current.check_only = options.check_only;
  current.verbose_mode = options.verbose_mode;
  current.sync_is_enabled = options.sync_is_enabled;
}

std::unique_ptr<global::StartOptions> global::StartOptions::parsePoundOption(
    int argc, char** argv, bool write_to_current) {
  auto res = std::make_unique<StartOptions>();
  int c_opt;
  int opt_err = 0;
  while ((c_opt = ::getopt(argc, argv, "sf:cvVp:")) > 0) switch (c_opt) {
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
      case 'V': {
        Logger::logmsg(LOG_ALERT, "zproxy version %s", ZPROXY_VERSION);
        Logger::logmsg(LOG_ALERT, "Build: %s %s", ZPROXY_HOST_INFO,
                       ZPROXY_BUILD_INFO);
        Logger::logmsg(LOG_ALERT, "%s", ZPROXY_COPYRIGHT);
        return nullptr;
      }
      default: {
        Logger::logmsg(LOG_ERR, "bad flag -%c", optopt);
        return nullptr;
      }
    }
  if (optind < argc) {
    Logger::logmsg(LOG_ERR, "unknown extra arguments (%s...)", argv[optind]);
    exit(EXIT_FAILURE);
  }
  //we must write to the current configuration the first time we parse the options
  if(write_to_current){
    current.setCurrent(*res);
  }
  return std::move(res);
}
