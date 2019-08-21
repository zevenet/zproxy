#pragma once
#if CACHE_ENABLED
#include "../debug/Debug.h"
#include "../http/HttpRequest.h"
#include "../http/http.h"
#include "../service/backend.h"
#include "ICacheStorage.h"

#ifndef _STRING_H
#include <string>
#endif
#ifndef _REGEX_H
#include <pcreposix.h>
#endif
#include <unordered_map>
using namespace std;

#define DEFAULT_TIMEOUT 3600;

struct CacheObject {
  std::string buffer;
  std::string etag;
  size_t content_length;
  bool no_cache_response =
      false; // TODO: if no_cache in response,  revalidate using head
  bool cacheable = true;
  bool transform = true;
  bool staled = false;
  bool revalidate = false;
  bool heuristic = false;
  long int date = -1;
  long int last_mod = -1;
  long int expires = -1;
  long int max_age = -1;
  CACHE_SCOPE scope;
  STORAGE_TYPE storage;
};
/**
 * @class HttpCacheManager HttpCacheManager.h "src/handlers/HttpCacheManager.h"
 *
 * @brief The HttpCacheManager class controls all the cache operations and logic
 *
 */
class HttpCacheManager {
private:
  int cache_timeout = -1;
  std::string service_name;
  RamICacheStorage * ram_storage;
  DiskICacheStorage * disk_storage;
  unordered_map<size_t, CacheObject *> cache; // Caching map
  regex_t *cache_pattern = nullptr;
  std::string ramfs_mount_point = "/mnt/cache_ramfs";
  std::string disk_mount_point = "/mnt/cache_disk";


  void updateContentStale(CacheObject *c_object);
  size_t hashStr(std::string str);
  void storeResponse(HttpResponse response, HttpRequest request);
  void updateResponse(HttpResponse response, HttpRequest request);
  STORAGE_TYPE getStorageType( HttpResponse response );
public:
  bool cache_enabled = false;
  ~HttpCacheManager() {
    // Free cache pattern
    if (cache_pattern != nullptr)
      regfree(cache_pattern);
    ram_storage->stopCacheStorage();
  }
  /**
  * @brief Initialize the cache manager, configuring its pattern and the
  * timeout
  *
  * @param pattern is the pointer to the regex_t configured in the service,
  * checks its re_pcre field to decide on enabling the cache or not
  * @param timeout is the timeout value read from the configuration file
  */
  void cacheInit(regex_t *pattern, const int timeout, const std::string svc, long storage_size, int storage_threshold) {
    if (pattern != nullptr) {
      if (pattern->re_pcre != nullptr) {
        this->cache_pattern = pattern;
        this->cache_timeout = timeout;
        this->cache_enabled = true;
        this->service_name = svc;
      }
    //Cache initialization
    ram_storage = RamfsCacheStorage::getInstance();
    ram_storage->initCacheStorage(static_cast<unsigned long>(storage_size), ramfs_mount_point);
    ram_storage->initServiceStorage(svc);
    ram_storage->cache_thr = static_cast<double>(storage_threshold) / 100;
    disk_storage = DiskCacheStorage::getInstance();
    //Max size not useful yet
    disk_storage->initCacheStorage(0, disk_mount_point);
    disk_storage->initServiceStorage(svc);
    }
  }
  /**
  * @brief Provide access to the cache_timeout variable
  *
  * @return timeout is the timeout value set to the cache manager
  */
  int getCacheTimeout() {  return this->cache_timeout; }
  /**
  * @brief Checks whether the request is cached or not.
  *
  * @param http_request is the HttpRequest to check if the resource is cached or
  * not.
  * @return if the content is cached it returns true or false in other case
  */
  bool isCached(HttpRequest &request);
  /**
  * @brief Checks whether the cached content is fresh or not, staling it if not
  * fresh.
  *
  * @param request is the HttpRequest to check if the resource is fresh or
  * not.
  * @return if the content is fresh it returns true or false in other case
  */
  bool isFresh(HttpRequest &request);
  /**
  * @brief Checks if the request allows to serve cached content and if the
  * cached content is fresh
  *
  * @param request is the HttpRequest that will be checked if serveable or
  * not
  * @return if the content can be served it returns true or false in other case
  */
  bool canBeServed(HttpRequest &request);
  /**
  * @brief get the cached object from the cache, which contains the cached
  * response
  *
  * @param request is the HttpRequest used to determine which stored content to
  * use
  *
  * @return returns the CacheObject or nullptr if not found
  */
  CacheObject *getCachedObject(HttpRequest request);
  CacheObject * getCachedObject(std::string url);
  /**
  * @brief returns the pattern used by the cache manager
  *
  * @return returns the regex_t that is being used by the cache manager
  */
  regex_t *getCachePattern() { return cache_pattern; }
  /**
  * @brief append data to a already stored response, in the case of a response
  * in multiple packets
  *
  * @param msg is the pointer to the buffer to append
  * @param msg_size is the size of the buffer to append
  * @param url indicates the resource
  *
  * TODO: Add error control?
  */
  void appendData(char *msg, size_t msg_size, std::string url);
  /**
  * @brief Creates an HttpResponse directly from the cached response
  *
  * @param request is the HttpRequest used to determine the cached response to
  * use
  *
  * @return returns a pointer to the HttpResponse created from cached data or
  * nullptr if not able
  */
  int createCacheResponse(HttpRequest request,
                          HttpResponse &cached_response);
  /**
  * @brief handle the response of an http request, checks if cache_control
  * directives allows the response to be cached, if the response HTTP code is
  * 200, 301 or 308 and if the HTTP ver was GET or HEAD in order to cache the
  * response
  *
  * @param response is the HttpResponse generated for the HttpRequest
  * @param request is the HttpRequest used for caching purpose
  */
  void handleResponse(HttpResponse response, HttpRequest request);

};


#endif
