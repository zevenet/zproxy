//
// Created by abdess on 4/20/18.
//
#pragma  once

#include "http_parser.h"
#include "../debug/Debug.h"

namespace validation {
enum VALIDATION_RESULT {
  OK,
  METHOD_NOT_ALLOWED,
  BAD_REQUEST,
  BAD_URL,
  URL_CONTAIN_NULL,
  REQUEST_TOO_LARGE,
};

const std::unordered_map<VALIDATION_RESULT, char *> validation_reason = {
    {OK, "valid request"},
    {METHOD_NOT_ALLOWED, "Method not allowed"},
    {BAD_REQUEST, "Bad request"}, {BAD_URL, "Bad URL"},
    {URL_CONTAIN_NULL, "URL contains null"},
    {REQUEST_TOO_LARGE, "Request too large"}
};

}

class HttpRequest : public http_parser::HttpParser {

 public:

  void setRequestMethod() {
    request_method = http::http_verbs[getMethod()];
  }
  void printRequestMethod() {
    Debug::logmsg(LOG_DEBUG, "Request method: %s", http::http_verb_strings.at(request_method));
  }
 public:

  std::string getMethod() {
    return method != nullptr ? std::move(std::string(method, method_len)) : std::string();
  }
  std::string getRequestLine() {
    std::string res(method, method_len + path_length);
    for (auto index = method_len + path_length; method[index] != '\r'; index++) {
      res += method[index];
    }
    return std::move(res);
  }

  std::string getUrl() {
    return path != nullptr ? std::move(std::string(path, path_length)) : std::string();
  }

};

class HttpResponse : public http_parser::HttpParser {

};