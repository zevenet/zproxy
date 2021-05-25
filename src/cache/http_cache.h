/*
 *    Zevenet zproxy Load Balancer Software License
 *    This file is part of the Zevenet zproxy Load Balancer software package.
 *
 *    Copyright (C) 2019-today ZEVENET SL, Sevilla (Spain)
 *
 *    This program is free software: you can redistribute it and/or modify
 *    it under the terms of the GNU Affero General Public License as
 *    published by the Free Software Foundation, either version 3 of the
 *    License, or any later version.
 *
 *    This program is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *    GNU Affero General Public License for more details.
 *
 *    You should have received a copy of the GNU Affero General Public License
 *    along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 */
#pragma once

#include "../http/http.h"
#include "../http/http_request.h"
#include "../service/backend.h"
// Storage headers
#include "../ctl/ctl.h"
#include "../stats/counter.h"
#include "../util/common.h"
#include "cache_commons.h"
#include "disk_cache_storage.h"
#include "i_cache_storage.h"
#include "ram_cache_storage.h"
#include <pcreposix.h>
#include <string>
#include <unordered_map>

using namespace std;
namespace st = storage_commons;
#define DEFAULT_TIMEOUT 3600;
#define CACHE_EXPIRATION 10;
/**
 * @class HttpCacheManager HttpCacheManager.h "src/handlers/HttpCacheManager.h"
 * @brief The HttpCacheManager class controls all the cache operations and logic
 */
class HttpCache
{
      private:
	int cache_timeout = -1;
	  std::string service_name;
	RamICacheStorage *ram_storage;
	DiskICacheStorage *disk_storage;
	  unordered_map < size_t, cache_commons::CacheObject * >cache;	// Caching map
	regex_t *cache_pattern = nullptr;
	  std::string ramfs_mount_point = "/tmp/cache_ramfs";
	  std::string disk_mount_point = "/tmp/cache_disk";
	void addResponse(HttpResponse & response, HttpRequest request);
	void updateResponse(HttpResponse response, HttpRequest request);
	  st::STORAGE_TYPE getStorageType(HttpResponse response);
	  st::STORAGE_TYPE getStorageType();

      public:
	  std::time_t t_stamp;
	  cache_commons::cache_stats stats;
	size_t cache_max_size = 0;
	  virtual ~ HttpCache();
  /**
   * @brief cacheInit Initialize the cache manager configuring its pattern and
   * the timeout it also get the ram storage manager and disk storage manager,
   * @param pattern is the pointer to the regex_t configured in the service,
   * checks its re_pcre field to decide on enabling the cache or not
   * @param timeout is the timeout value read from the configuration file
   * @param svc is the service name
   * @param storage_size is the ram storage max size
   * @param storage_threshold is the threshold to determine if must be cached by
   * ram or by disk
   * @param f_name is the farm name, used to determine the mount point
   */
	void cacheInit(regex_t * pattern, const int timeout,
		       const std::string & svc, long storage_size,
		       int storage_threshold, const std::string & f_name,
		       const std::string & cache_ram_mpoint,
		       const std::string & cache_disk_mpoint);
  /**
   * @brief Provide access to the cache_timeout variable
   *
   * @return timeout is the timeout value set to the cache manager
   */
	int getCacheTimeout()
	{
		return this->cache_timeout;
	}
  /**
   * @brief canBeServedFromCache Checks if the request allows to serve cached
   * content and if the cached content is fresh
   *
   * @param request is the HttpRequest that will be checked if serveable or
   * not
   * @return if the content can be served it returns true or false in other case
   */
	cache_commons::CacheObject *
		canBeServedFromCache(HttpRequest & request);
  /**
   * @brief get the cached object from the cache, which contains the cached
   * response
   *
   * @param request is the HttpRequest used to determine which stored content to
   * use
   *
   * @return returns the cache_commons::CacheObject or nullptr if not found
   */
	cache_commons::CacheObject * getCacheObject(HttpRequest request);
  /**
   * @brief cache_commons::CacheObject
   * @param hashed_url a hashed string of an URL in order to retrieve its object
   * @return  the cache_commons::CacheObject which is associated to the url or
   * nullptr if not found
   */
	cache_commons::CacheObject * getCacheObject(size_t hashed_url);
  /**
   * @brief returns the pattern used by the cache manager
   *
   * @return returns the regex_t that is being used by the cache manager
   */
	regex_t *getCachePattern()
	{
		return cache_pattern;
	}
  /**
   * @brief append data to a already stored response, in the case of a response
   * in multiple packets
   *
   * @param msg is the pointer to the buffer to append
   * @param msg_size is the size of the buffer to append
   * @param url indicates the resource
   *
   */
	void addData(HttpResponse & response, std::string_view data,
		     const std::string & url);
  /**
   * @brief getResponseFromCache
   * @param request is the HttpRequest used to determine the cached response to
   * use
   * @param cached_response is the reference to a response, which will used to
   * store the created response
   * @return 0 if successful, != 0 in any other case.
   */
	int getResponseFromCache(HttpRequest request,
				 HttpResponse & cached_response,
				 std::string & buffer);
  /**
   * @brief handle the response of an http request, checks if cache_control
   * directives allows the response to be cached, if the response HTTP code is
   * 200, 301 or 308 and if the HTTP verb was GET or HEAD in order to cache the
   * response
   *
   * @param response is the HttpResponse generated for the HttpRequest
   * @param request is the HttpRequest used for caching purpose
   */
	void handleResponse(HttpResponse & response, HttpRequest request);
  /**
   * @brief handle the task from the API for example to delete some content
   *
   * @param task the CtlTask provided by the service handletask
   */
	std::string handleCacheTask(ctl::CtlTask & task);
  /**
   * @brief recoverCache
   * @param svc
   * @param st_type
   */
	void recoverCache(const std::string & svc, st::STORAGE_TYPE st_type);
  /**
   * @brief createResponseEntry Creates a cache_commons::CacheObject entry with
   * cache information of a HttpResponse
   * @param response the response which will be used to create the
   * cache_commons::CacheObject entry
   * @param pointer for cache_commons::CacheObject, it will be stored in it, if
   * nullptr, the function will create
   * @return cache_commons::CacheObject is the cache information representation
   * of the response
   */
	void createResponseEntry(HttpResponse response,
				 cache_commons::CacheObject * c_object);
  /**
   * @brief deleteEntry removes the cache entry of the param request
   * @param request the HttpRequest used to determine which entry to delete
   */
	int deleteEntry(HttpRequest request);
  /**
   * @brief deleteEntry removes the cache entry of the param request
   * @param hashed_url the size_t variable used to determine which entry will be
   * deleted
   */
	int deleteEntry(size_t hashed_url);
  /**
   * @brief doCacheMaintenance if the cache needs maintenance ( 1 per second or
   * more), check entries which must be deleted
   */
	void doCacheMaintenance();
  /**
   * @brief validateResponseEncoding checks if the stored response encoding
   * match with any of the accept encoding provided
   * @param request is the HttpRequest object containing the incoming
   * HttpRequest information
   * @param c_object is the CacheObject object containing the entry stored
   */
	bool validateResponseEncoding(HttpRequest request,
				      cache_commons::CacheObject * c_object);
  /**
   * @brief flushCache Flush the full cache content, emptying both storages too.
   */
	void flushCache();
};

namespace cache_stats__
{
#if DEBUG_ZCU_LOG
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
#endif
}				// namespace cache_stats__
