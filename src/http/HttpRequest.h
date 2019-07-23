//
// Created by abdess on 4/20/18.
//
#pragma once

#include "../debug/Debug.h"
#include "http_parser.h"
#include <map>

class HttpRequest : public http_parser::HttpData {

  /** Service that request was generated for*/
  void *request_service; // fixme; hack to avoid cyclic dependency, //TODO::
                         // remove
public:
  bool add_destination_header;
  bool upgrade_header;
  bool connection_header_upgrade;
  bool accept_encoding_header;
  bool host_header_found{false};

  void setRequestMethod() {
    auto sv = std::string_view(method, method_len);
//    auto sv = std::string(method, method_len);
    auto it = http::http_info::http_verbs.find(sv);
    if (it != http::http_info::http_verbs.end())
      request_method = it->second;
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

  inline std::string_view getRequestLine() {
    return std::string_view(http_message,
                            http_message_length);
  }

  std::string getUrl() {
    return path != nullptr ? std::string(path, path_length) : std::string();
  }
  void setService(/*Service */ void *service);
  void *getService() const;
};

class HttpResponse : public http_parser::HttpData {
public:

  bool transfer_encoding_header;
};
