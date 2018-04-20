//
// Created by abdess on 4/9/18.
//
#pragma once

#include <string>
struct Backend {
  addrinfo *address_info;
  int backen_id;
  std::string address;
  int port;
  int timeout;
};