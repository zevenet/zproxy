//
// Created by abdess on 4/9/18.
//
#pragma once

#include <string>
#include <netdb.h>
enum BACKEND_STATUS {
  NO_BACKEND = -1,
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
  BACKEND_TYPE backend_type;
  int std_dvt;
  addrinfo *address_info;
  int backen_id;
  std::string address;
  int port;
  int timeout;
};
