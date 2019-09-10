#if CACHE_ENABLED

#pragma once
#include <sys/mount.h>
#include <sys/stat.h>
#include <string>
#include <pcreposix.h>
#include <cstring>
#include <unordered_map>
#include <fstream>
#include <sys/stat.h>
#include <sys/types.h>
#include <filesystem>
#include "../debug/Debug.h"
#include "CacheCommons.h"
#if MEMCACHED_ENABLED
#include <libmemcached/memcached.h>
#endif

using namespace std;
namespace st = storage_commons;

#define MAX_STORAGE_SIZE 268435456; //256MB


/**
 * @class ICacheStorage ICacheStorage.h "src/handlers/ICacheStorage.h"
 *
 * @brief Definition for the interface ICacheStorage for implementation
 */
class ICacheStorage {
protected:
    ICacheStorage(){}
public:
    /**
     * @brief initCacheStorage Initialize the storage, setting the mount point and max size
     * @param max_size The max size for the storage
     * @param mount_point the mount point where to put the cached content
     * @return st::STORAGE_STATUS return the status of the storage
     */
    virtual st::STORAGE_STATUS initCacheStorage(const size_t max_size, double st_threshold, std::string svc, const std::string mount_point) = 0;
    /**
     * @brief initServiceStorage Initialize the service directory once the system is mounted/ initialized
     * @param svc service name
     * @return STORAGE_STATUS return the status of the storage
     */
    virtual st::STORAGE_STATUS initServiceStorage( std::string svc ) = 0;
    /**
     * @brief getFromStorage get from the storage system the data from the rel_path path
     * @param rel_path is the path where to recover the stored data from
     * @param out_buffer is the buffer where the stored content will be recovered to
     * @return STORAGE_STATUS return the status of the storage
     */
    virtual st::STORAGE_STATUS getFromStorage( const std::string rel_path, std::string &out_buffer ) = 0;
    /**
     * @brief putInStorage store in the mount_point/rel_path path the buffer
     * @param rel_path is the path where to store the buffer content
     * @param buffer is the string with data to store
     * @param response_size its the size of the response for size operations
     * @return STORAGE_STATUS return the status of the storage
     */
    virtual st::STORAGE_STATUS putInStorage( const std::string rel_path, const std::string buffer, size_t response_size) = 0;
    /**
     * @brief getStorageType return the current storage type
     * @return STORAGE_STATUS return the status of the storage
     */
    virtual st::STORAGE_TYPE getStorageType() = 0;
    /**
     * @brief stopCacheStorage stop and clean cache storage paths
     * @return STORAGE_STATUS return the status of the storage
     */
    virtual st::STORAGE_STATUS stopCacheStorage() = 0;
    /**
     * @brief appendData append incomming data to an existing data
     * @param rel_path the path where to append data
     * @param buffer the buffer containing the data to store
     * @return STORAGE_STATUS return the status of the storage
     */
    virtual st::STORAGE_STATUS appendData(const std::string rel_path, const std::string buffer) = 0;
    /**
     * @brief deleteInStorage clean the content of an url
     * @param url used to determine the path to delete
     * @return STORAGE_STATUS return the status of the storage
     */
    virtual st::STORAGE_STATUS deleteInStorage(std::string url) = 0;
    /**
     * @brief isInStorage checks whether the data file determine by svc and url exists or not
     * @param svc the service name
     * @param url the response url
     * @return STORAGE_STATUS return the status of the storage
     */
    virtual bool isInStorage(const std::string svc, const std::string url) = 0;
    /**
     * @brief ~ICacheStorage
     */
    virtual ~ICacheStorage() {}
    };

#endif
