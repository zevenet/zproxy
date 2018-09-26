//
// Created by abdess on 4/9/18.
//
#pragma once

#include <string>
#include <netdb.h>
#include "pound_struct.h"
enum BACKEND_STATUS {
  NO_BACKEND = -1, // this should be used for first assigned backends
  BACKEND_CONNECTED = 0,
  BACKEND_DISCONECTED,
};

enum BACKEND_TYPE {
  REMOTE,
  EMERGENCY_SERVER,
  REDIRECT,
  CACHE_SYSTEM,
};

class Backend {
 public:
  Backend() = default;
  BACKEND_TYPE backend_type;
  BackendConfig backend_config;
  addrinfo *address_info{};
  int backen_id{};
  std::string address;
  int port{};
  int conn_timeout{};
  int response_timeout{};
  bool disabled{};
};
