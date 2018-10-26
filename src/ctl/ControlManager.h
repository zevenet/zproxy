//
// Created by abdess on 9/28/18.
//

#pragma once

#include <atomic>
#include "../config/config.h"
#include "../connection/connection.h"
#include "../event/epoll_manager.h"
#include "../http/HttpRequest.h"
#include "../http/HttpStatus.h"
#include "../json/json.h"
#include "../util/environment.h"
#include "ctl.h"
#include "observer.h"

namespace ctl {
using namespace events;
using namespace json;
class ControlManager : public EpollManager,
                       public CtlNotify<CtlTask, std::string> {
  static std::unique_ptr<ControlManager> instance;
  std::thread control_thread;
  Connection control_listener;
  std::atomic<bool> is_running;
  CTL_INTERFACE_MODE ctl_listener_mode;

  void HandleEvent(int fd, EVENT_TYPE event_type,
                   EVENT_GROUP event_group) override;
  void doWork();

 public:
  static ControlManager *getInstance();
  explicit ControlManager(
      CTL_INTERFACE_MODE listener_mode = CTL_INTERFACE_MODE::CTL_UNIX);
  ControlManager(ControlManager &) = delete;
  ~ControlManager();
  bool init(Config &configuration,
            CTL_INTERFACE_MODE listener_mode = CTL_INTERFACE_MODE::CTL_UNIX);
  void start();
  void stop();

 private:
  std::string handleCommand(HttpRequest &request);
  /*get request component target which will provide the response*/
  bool setTaskTarget(HttpRequest &request, CtlTask &task);
  bool setListenerTarget(CtlTask &task, std::istringstream &ss);
  bool setServiceTarget(CtlTask &task, std::istringstream &ss);
  bool setBackendTarget(CtlTask &task, std::istringstream &ss);
};

}  // namespace ctl
