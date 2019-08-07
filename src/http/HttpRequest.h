//
// Created by abdess on 4/20/18.
//
#pragma once

#include "../debug/Debug.h"
#include "http_parser.h"
#include <map>
#if CACHE_ENABLED
enum class CACHE_SCOPE {
  PUBLIC,
  PRIVATE,
};

struct CacheRequestOptions {
  bool no_store = false;
  bool no_cache = false;
  bool only_if_cached = false;
  bool transform = true;
  int max_age = -1;
  int max_stale = -1;
  int min_fresh = -1;
};

struct CacheResponseOptions {
  bool no_cache = false;
  bool transform = true;
  bool cacheable = true; // Set by the request with no-store
  bool revalidate = false;
  int max_age = -1;
  CACHE_SCOPE scope;
};
#endif
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
#if CACHE_ENABLED
  struct CacheRequestOptions c_opt;
#endif
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
#if CACHE_ENABLED
    bool transfer_encoding_header;
    bool cached = false;
    struct CacheResponseOptions c_opt;
    std::string etag;
    // Time specific headers
    long int date = -1;
    long int last_mod = -1;
    long int expires = -1;
    bool isCached();
#endif
};
