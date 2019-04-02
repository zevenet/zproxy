//
// Created by abdess on 4/20/18.
//
#pragma once

#include "../debug/Debug.h"
#include "http_parser.h"
#include <map>

class HttpRequest : public http_parser::HttpData {

public:

  bool add_destination_header;
  bool upgrade_header;
  bool connection_header_upgrade;
  bool accept_encoding_header;

  void setRequestMethod() {
    request_method = http::http_info::http_verbs.at(getMethod());
  }

  http::REQUEST_METHOD getRequestMethod() {
    setRequestMethod();
    return request_method;
  }

  void printRequestMethod() {
    Debug::logmsg(
        LOG_DEBUG, "Request method: %s",
        http::http_info::http_verb_strings.at(request_method).c_str());
  }

public:
  inline std::string getMethod() {
    return method != nullptr ? std::string(method, method_len) : std::string();
  }
  inline std::string getRequestLine() {
    std::string res(http_message, http_message_length);
    //    for (auto index = method_len + path_length; method[index] != '\r';
    //         index++) {
    //      res += method[index];
    //    }
    return std::move(res);
  }

  std::string getUrl() {
    return path != nullptr ? std::string(path, path_length) : std::string();
  }
};

class HttpResponse : public http_parser::HttpData {
  public:
  bool transfer_encoding_header;
};
