//
// Created by abdess on 4/20/18.
//
#pragma once

#include "../debug/Debug.h"
#include "http_parser.h"

#ifdef CACHE_ENABLED
#include <map>
#include "../cache/CacheCommons.h"

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
  cache_commons::CACHE_SCOPE scope;
};
#endif
class HttpRequest : public http_parser::HttpData {

  /** Service that request was generated for*/
    void *request_service{nullptr}; // fixme; hack to avoid cyclic dependency, //TODO::
                         // remove
public:
  bool add_destination_header{false};
  bool upgrade_header{false};
  bool connection_header_upgrade{false};
  bool accept_encoding_header{false};
  bool host_header_found{false};
#ifdef CACHE_ENABLED
  struct CacheRequestOptions c_opt;
#endif
  void setRequestMethod();
  http::REQUEST_METHOD getRequestMethod();
  void printRequestMethod();
public:
  std::string getMethod();
  std::string getVersion();
  std::string_view getRequestLine();
  std::string getUrl();
  void setService(/*Service */ void *service);
  void *getService() const;
};

class HttpResponse : public http_parser::HttpData {
public:
#ifdef CACHE_ENABLED
    bool transfer_encoding_header;
    bool cached = false;
    struct CacheResponseOptions c_opt;
    cache_commons::CacheObject * c_object = nullptr;
    std::string etag;
    // Time specific headers
    long int date = -1;
    long int last_mod = -1;
    long int expires = -1;
    bool isCached();
    std::string str_buffer;
#endif
};
