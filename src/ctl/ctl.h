//
// Created by abdess on 10/2/18.
//

#pragma once
#include <string>
#include "../http/HttpRequest.h"

namespace ctl {

enum CTL_COMMAND {
  CTL_CMD_NONE,
  CTL_CMD_ADD,
  CTL_CMD_DELETE,
  CTL_CMD_ENABLE,
  CTL_CMD_DISABLE,
  CTL_CMD_UPDATE,
  CTL_CMD_GET,
  CTL_CMD_SUSCRIBE,
  CTL_CMD_UNSUSCRIBE
};

enum CTL_HANDLER_TYPE {
  CTL_NONE,
  CTL_LISTENER,
  CTL_BACKEND,
  CTL_SERVICE,
  CTL_SERVICE_MANAGER,
  CTL_GLOBAL_CONF,
  CTL_STREAM_MANAGER,
  CTL_ENVIORONMENT
};

enum CTL_SUBJECT {
  CTL_SB_NONE,
  CTL_SB_SESSION,
  CTL_SB_BACKEND,
  CTL_SB_SERVICE,
  CTL_SB_LISTENER,
  CTL_SB_CONFIG,
  CTL_SB_STATUS,
};

struct CtlTask {
  HttpRequest* request;
  CTL_COMMAND command = CTL_CMD_NONE;
  CTL_HANDLER_TYPE target = CTL_NONE;
  CTL_SUBJECT subject = CTL_SB_NONE;

  int listener_id = -1;
  int service_id = -1;
  int backend_id = -1;

  std::string target_subject_id = "";

  std::string service_name;
  std::string backend_name;
  std::string data;
};

enum CTL_INTERFACE_MODE {
  CTL_UNIX,
  CTL_AF_INET,
};

}  // namespace ctl
