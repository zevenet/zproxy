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

#include "../config/config.h"
#include "../connection/connection.h"
#include "../event/epoll_manager.h"
#include "../http/http_request.h"
#include "../json/json.h"
#include "../util/environment.h"
#include "ctl.h"
#include "observer.h"
#include <atomic>

namespace ctl {
using namespace events;
using namespace json;
class ControlManager : public EpollManager, public CtlNotify<CtlTask, std::string> {
  static std::shared_ptr<ControlManager> instance;
  std::thread control_thread;
  Connection control_listener;
  std::atomic<bool> is_running;
  CTL_INTERFACE_MODE ctl_listener_mode;
  std::string control_path_name;
  void HandleEvent(int fd, EVENT_TYPE event_type, EVENT_GROUP event_group) override;
  void doWork();

 public:
  static std::shared_ptr<ControlManager> getInstance();
  explicit ControlManager(CTL_INTERFACE_MODE listener_mode = CTL_INTERFACE_MODE::CTL_UNIX);
  ControlManager(ControlManager &) = delete;
  ~ControlManager() final;
  bool init(Config &configuration, CTL_INTERFACE_MODE listener_mode = CTL_INTERFACE_MODE::CTL_UNIX);
  void start();
  void stop();
  void sendCtlCommand(CTL_COMMAND command, CTL_HANDLER_TYPE handler,
                      CTL_SUBJECT subject, std::string data = "");

 private:
  std::string handleCommand(HttpRequest &request);
  /*get request component target which will provide the response*/
  bool setTaskTarget(HttpRequest &request, CtlTask &task);
  bool setListenerTarget(CtlTask &task, std::istringstream &ss);
  bool setServiceTarget(CtlTask &task, std::istringstream &ss);
  bool setBackendTarget(CtlTask &task, std::istringstream &ss);
};

}  // namespace ctl
