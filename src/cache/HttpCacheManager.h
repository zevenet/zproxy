#pragma once
#if CACHE_ENABLED
#include "../debug/Debug.h"
#include "../http/HttpRequest.h"
#include "../http/http.h"
#include "../service/backend.h"
#include "ICacheStorage.h"
#include "../util/common.h"
#include "../stats/counter.h"
#include "../ctl/ctl.h"
#include <string>
#include <pcreposix.h>
#include <unordered_map>
#include "CacheCommons.h"
using namespace std;
namespace st = storage_commons;
#define DEFAULT_TIMEOUT 3600;

/**
 * @class HttpCacheManager HttpCacheManager.h "src/handlers/HttpCacheManager.h"
 * @brief The HttpCacheManager class controls all the cache operations and logic
 */
class HttpCacheManager {
private:
  int cache_timeout = -1;
  std::string service_name;
  RamICacheStorage * ram_storage;
  DiskICacheStorage * disk_storage;
  unordered_map<size_t, cache_commons::CacheObject *> cache; // Caching map
  regex_t *cache_pattern = nullptr;
  std::string ramfs_mount_point = "/tmp/cache_ramfs";
  std::string disk_mount_point = "/tmp/cache_disk";

  /**
   * @brief updateFreshness update the freshness for a single stored response
   * @param c_object, the cache_commons::CacheObject which we want to update
   */
  void updateFreshness(cache_commons::CacheObject *c_object);
  /**
   * @brief hashStr
   * @param str
   * @return
   */
  size_t hashStr(std::string str);
  void storeResponse(HttpResponse response, HttpRequest request);
  void updateResponse(HttpResponse response, HttpRequest request);
  st::STORAGE_TYPE getStorageType( HttpResponse response );
public:
  size_t cache_max_size = 0;
  bool cache_enabled = false;
  virtual ~HttpCacheManager();
  /**
   * @brief cacheInit Initialize the cache manager configuring its pattern and the
   * timeout it also get the ram storage manager and disk storage manager,
   * @param pattern is the pointer to the regex_t configured in the service,
   * checks its re_pcre field to decide on enabling the cache or not
   * @param timeout is the timeout value read from the configuration file
   * @param svc is the service name
   * @param storage_size is the ram storage max size
   * @param storage_threshold is the threshold to determine if must be cached by ram or by disk
   * @param f_name is the farm name, used to determine the mount point
   */
  void cacheInit(regex_t *pattern, const int timeout, const std::string svc, long storage_size, int storage_threshold, std::string f_name);
  /**
   * @brief Provide access to the cache_timeout variable
   *
   * @return timeout is the timeout value set to the cache manager
   */
  int getCacheTimeout() {  return this->cache_timeout; }
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
   * @brief canBeServedFromCache Checks if the request allows to serve cached content and if the
   * cached content is fresh
   *
   * @param request is the HttpRequest that will be checked if serveable or
   * not
   * @return if the content can be served it returns true or false in other case
   */
  cache_commons::CacheObject * canBeServedFromCache(HttpRequest &request);
  /**
   * @brief get the cached object from the cache, which contains the cached
   * response
   *
   * @param request is the HttpRequest used to determine which stored content to
   * use
   *
   * @return returns the cache_commons::CacheObject or nullptr if not found
   */
  cache_commons::CacheObject *getCacheObject(HttpRequest request);
  /**
   * @brief getcache_commons::CacheObject
   * @param url an string object containing an URL in order to retrieve its object
   * @return  the cache_commons::CacheObject which is associated to the url or nullptr if not found
   */
  cache_commons::CacheObject *getCacheObject(std::string url);
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
   */
  void appendData(char *msg, size_t msg_size, std::string url);
  /**
   * @brief getResponseFromCache
   * @param request is the HttpRequest used to determine the cached response to
   * use
   * @param cached_response is the reference to a response, which will used to store the created response
   * @return 0 if successful, != 0 in any other case.
   */
  int getResponseFromCache(HttpRequest request,
                          HttpResponse &cached_response, std::string &buffer );
  /**
   * @brief handle the response of an http request, checks if cache_control
   * directives allows the response to be cached, if the response HTTP code is
   * 200, 301 or 308 and if the HTTP verb was GET or HEAD in order to cache the
   * response
   *
   * @param response is the HttpResponse generated for the HttpRequest
   * @param request is the HttpRequest used for caching purpose
   */
  void handleResponse(HttpResponse response, HttpRequest request);
  /**
   * @brief handle the task from the API for example to delete some content
   *
   * @param task the CtlTask provided by the service handletask
   */
  std::string handleCacheTask(ctl::CtlTask &task);
  /**
   * @brief recoverCache
   * @param svc
   * @param st_type
   */
  void recoverCache( std::string svc, st::STORAGE_TYPE st_type );
  /**
   * @brief parseCacheBuffer It takes a buffer of an stored HTTP response and create an HttpResponse object
   * @param buffer it is the buffer containing an HTTP response with HTTP header first.
   * @return HttpResponse as the filled clase after parsing the buffer
   */
  HttpResponse parseCacheBuffer(std::string buffer);
  /**
   * @brief createcache_commons::CacheObjectEntry Creates a cache_commons::CacheObject entry with cache information of a HttpResponse
   * @param response the response which will be used to create the cache_commons::CacheObject entry
   * @return cache_commons::CacheObject is the cache information representation of the response
   */
  cache_commons::CacheObject * createCacheObjectEntry( HttpResponse response );
};

namespace cache_stats__ {
#define DEBUG_COUNTER_HIT(x) std::unique_ptr<x> UNIQUE_NAME(counter_hit) (new x)
    DEFINE_OBJECT_COUNTER(cache_RAM_entries)
    DEFINE_OBJECT_COUNTER(cache_DISK_entries)
    DEFINE_OBJECT_COUNTER(cache_RAM_mountpoint)
    DEFINE_OBJECT_COUNTER(cache_DISK_mountpoint)
    DEFINE_OBJECT_COUNTER(cache_match)
    DEFINE_OBJECT_COUNTER(cache_staled_entries)
    DEFINE_OBJECT_COUNTER(cache_miss)
    DEFINE_OBJECT_COUNTER(cache_ram_used)
    DEFINE_OBJECT_COUNTER(cache_disk_used)
    DEFINE_OBJECT_COUNTER(cache_not_stored)
}

#endif
