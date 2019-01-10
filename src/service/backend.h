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
#include "../json/JsonDataValue.h"
#include "../json/JsonDataValueTypes.h"
#include "../json/jsonparser.h"

enum BACKEND_STATUS {
  NO_BACKEND = -1,  // this should be used for first assigned backends
  BACKEND_UP = 0,
  BACKEND_DOWN,
  BACKEND_DISABLED
};

enum BACKEND_TYPE {
  REMOTE,
  EMERGENCY_SERVER,
  REDIRECT,
  CACHE_SYSTEM,
};
using namespace Statistics;
using namespace json;

class Backend : public CtlObserver<ctl::CtlTask, std::string>, public BackendInfo{
public:
  Backend();
  ~Backend();
  BACKEND_STATUS status = NO_BACKEND;
  BACKEND_TYPE backend_type;
  BackendConfig backend_config;
  addrinfo *address_info{};
  int backend_id;
  std::string name;
  int weight;
  std::string address;
  int port;
  std::string bekey;
  int conn_timeout{};
  int response_timeout{};
  bool cut;
  //  bool disabled;

  void doMaintenance();
  std::string handleTask(ctl::CtlTask &task) override;
  bool isHandler(ctl::CtlTask &task) override;

  std::unique_ptr<JsonObject> getBackendJson();
};
