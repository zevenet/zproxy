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
#include "../connection/connection.h"
#include "../debug/logger.h"
#include "../event/epoll_manager.h"
#include "../http/http_request.h"
#include "../json/json.h"
#include "../json/json_data_value.h"
#include "../json/json_parser.h"
#include "ctl.h"
#include <getopt.h>
#include <set>

#define NO_VALUE -1
using namespace ctl;

static const struct option long_options[] = {
    {"control-socket", required_argument, nullptr, 'c'},
    {"control-address", required_argument, nullptr, 'a'},
    {"enable-listener", required_argument, nullptr, 'L'},
    {"disable-listener", required_argument, nullptr, 'l'},
    {"enable-service", required_argument, nullptr, 'S'},
    {"disable-service", required_argument, nullptr, 's'},
    {"enable-backend", required_argument, nullptr, 'B'},
    {"disable-backend", required_argument, nullptr, 'b'},
    {"flush-sessions", required_argument, nullptr, 'f'},
    {"add-session", required_argument, nullptr, 'N'},
    {"delete-session", required_argument, nullptr, 'n'},
    {"reload-listener-conf", required_argument, nullptr, 'R'},

    {"enable-XML-output", no_argument, nullptr, 'X'},
    {"resolve-host", no_argument, nullptr, 'H'},
    {"verbose", no_argument, nullptr, 'v'},
    {"help", no_argument, nullptr, 'h'},
    {nullptr, no_argument, nullptr, 0}};

enum class CTL_ACTION {
  RELOAD,
  NONE,
  ENABLE,
  DISABLE,
  ADD_SESSION,
  DELETE_SESSION,
  FLUSH_SESSIONS
};

struct OptionArgs {};

class PoundClient /*: public EpollManager*/ {
  const char *options_string = "a:vc:LlRSsBbNnfXH";
  std::string binary_name;    /*argv[0]*/
  std::string control_socket; /* -c option */
  std::string session_key;    /* -k option */
  std::string address;

  int listener_id = 0;
  int service_id = NO_VALUE;
  int backend_id = NO_VALUE;

  CTL_INTERFACE_MODE interface_mode = CTL_INTERFACE_MODE::CTL_NONE;
  CTL_ACTION ctl_command = CTL_ACTION::NONE;
  CTL_SUBJECT ctl_command_subject = CTL_SUBJECT::NONE;
  bool tcp_mode;
  bool xml_output;
  bool resolve_hosts;
  bool verbose;
  Connection connection;
  OptionArgs global_args;
  bool trySetTargetId(int &target_id, char *possible_value);
  void trySetAllTargetId(char *argv[], int &option_index);
  void showHelp(const std::string error = "", bool exit_on_error = true);
  bool doRequest(http::REQUEST_METHOD request_method, http::HTTP_VERSION http_version, std::string json_object,
                 std::string path, std::string &buffer);
  void verboseLog(const std::string &str);
  void outputStatus(json::JsonObject *json_response_listener);
  bool executeCommand();
  void showError(std::string error);

 public:
  bool init(int argc, char *argv[]);
};
