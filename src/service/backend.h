//
// Created by abdess on 4/9/18.
//
#pragma once

#include <netdb.h>
#include <atomic>
#include "../config/pound_struct.h"
#include "../ctl/ControlManager.h"
#include "../ctl/ctl.h"
#include "../ctl/observer.h"
#include "../debug/Debug.h"
#include "../util/utils.h"
#include "../stats/backend_stats.h"

enum BACKEND_STATUS {
  NO_BACKEND = -1,  // this should be used for first assigned backends
  BACKEND_CONNECTED = 0,
  BACKEND_DISCONECTED,
};

enum BACKEND_TYPE {
  REMOTE,
  EMERGENCY_SERVER,
  REDIRECT,
  CACHE_SYSTEM,
};
using namespace Statistics;

class Backend : public CtlObserver<ctl::CtlTask, std::string>, public BackendInfo{
 public:
  Backend();
  ~Backend();
  BACKEND_TYPE backend_type;
  BackendConfig backend_config;
  addrinfo *address_info{};
  int backen_id{};
  std::string address;
  int port{};
  int conn_timeout{};
  int response_timeout{};
  bool disabled{};

  std::string handleTask(ctl::CtlTask &task) override;
  bool isHandler(ctl::CtlTask &task) override;
};
