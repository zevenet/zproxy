#if CACHE_ENABLED

#pragma once
#include <sys/mount.h>
#include <sys/stat.h>
#ifndef _STRING_H
#include <string>
#endif
#ifndef _REGEX_H
#include <pcreposix.h>
#endif
#include <cstring>
#include <unordered_map>
#include <fstream>
#include <sys/stat.h>
#include <sys/types.h>
#include <filesystem>
#include "../debug/Debug.h"
#if MEMCACHED_ENABLED
#include <libmemcached/memcached.h>
#endif

using namespace std;

#define MAX_STORAGE_SIZE 268435456; //256MB

enum STORAGE_STATUS { SUCCESS, MKDIR_ERROR, MOUNT_ERROR, MEMORY_ERROR, ALREADY_INIT, NOT_INIT, FD_CLOSE_ERROR, GENERIC_ERROR, OPEN_ERROR, NOT_FOUND, STORAGE_FULL, APPEND_ERROR, MPOINT_ALREADY_EXISTS};
enum STORAGE_TYPE { RAMFS, STDMAP, TMPFS, DISK, MEMCACHED };

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
     * @return STORAGE_STATUS return the status of the storage
     */
    virtual STORAGE_STATUS initCacheStorage(const size_t max_size, const std::string mount_point) = 0;
    /**
     * @brief initServiceStorage Initialize the service directory once the system is mounted/ initialized
     * @param svc service name
     * @return STORAGE_STATUS return the status of the storage
     */
    virtual STORAGE_STATUS initServiceStorage( std::string svc ) = 0;
    /**
     * @brief getFromStorage get from the storage system the data from the rel_path path
     * @param rel_path is the path where to recover the stored data from
     * @param out_buffer is the buffer where the stored content will be recovered to
     * @return STORAGE_STATUS return the status of the storage
     */
    virtual STORAGE_STATUS getFromStorage( const std::string rel_path, std::string &out_buffer ) = 0;
    /**
     * @brief putInStorage store in the mount_point/rel_path path the buffer
     * @param rel_path is the path where to store the buffer content
     * @param buffer is the string with data to store
     * @param response_size its the size of the response for size operations
     * @return STORAGE_STATUS return the status of the storage
     */
    virtual STORAGE_STATUS putInStorage( const std::string rel_path, const std::string buffer, size_t response_size) = 0;
    /**
     * @brief getStorageType return the current storage type
     * @return STORAGE_STATUS return the status of the storage
     */
    virtual STORAGE_TYPE getStorageType() = 0;
    /**
     * @brief stopCacheStorage stop and clean cache storage paths
     * @return STORAGE_STATUS return the status of the storage
     */
    virtual STORAGE_STATUS stopCacheStorage() = 0;
    /**
     * @brief appendData append incomming data to an existing data
     * @param rel_path the path where to append data
     * @param buffer the buffer containing the data to store
     * @return STORAGE_STATUS return the status of the storage
     */
    virtual STORAGE_STATUS appendData(const std::string rel_path, const std::string buffer) = 0;
    /**
     * @brief deleteInStorage clean the content of an url
     * @param url used to determine the path to delete
     * @return STORAGE_STATUS return the status of the storage
     */
    virtual STORAGE_STATUS deleteInStorage(std::string url) = 0;
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
/**
 * @brief The DiskICacheStorage interface is the specification of a ICacheStorage for DISK
 */
class DiskICacheStorage: public ICacheStorage{
protected:
    static DiskICacheStorage * instance;
    bool initialized = false;
public:
    size_t max_size = 0;
    size_t current_size = 0;
    std::string mount_path;
    virtual ~DiskICacheStorage(){}
};
/**
 * @brief The RamICacheStorage interface is the specification of a ICacheStorage for RAM
 */
class RamICacheStorage: public ICacheStorage{
protected:
    static RamICacheStorage * instance;
    bool initialized = false;
public:
    size_t max_size = 0;
    size_t current_size = 0;
    std::string mount_path;
    double cache_thr = 0;
    virtual ~RamICacheStorage(){}
};


/**
 * @class RamfsCacheStorage HttpCacheManager.h "src/handlers/HttpCacheManager.h"
 *
 * @brief The RamfsCacheStorage implements the interface ICacheStorage in order to allow RAMFS cache storage
 */
class RamfsCacheStorage: public RamICacheStorage{
private:
    RamfsCacheStorage(){}
public:
    static RamICacheStorage * getInstance() {
        if (instance == nullptr)
        {
            instance = new RamfsCacheStorage();
        }
        return instance;
    }
    STORAGE_TYPE getStorageType() override;
    STORAGE_STATUS initCacheStorage( const size_t max_size,const std::string m_point ) override;
    STORAGE_STATUS initServiceStorage (std::string svc) override;
    STORAGE_STATUS getFromStorage( const std::string rel_path, std::string &out_buffer ) override;
    STORAGE_STATUS putInStorage( const std::string rel_path, const std::string buffer, size_t response_size) override;
    STORAGE_STATUS stopCacheStorage() override;
    STORAGE_STATUS appendData(const std::string rel_path, const std::string buffer) override;
    bool isInStorage(const std::string svc, const std::string url) override;
    STORAGE_STATUS deleteInStorage(std::string path) override;
    bool isInStorage( std::string path );
};

/**
 * @class MemcachedStorage HttpCacheManager.h "src/handlers/HttpCacheManager.h"
 *
 * @brief The MemcachedStorage implements the interface RamICacheStorage in order to allow memcached storage
 */
#if MEMCACHED_ENABLED
class MemcachedStorage : public RamICacheStorage {
private:
    memcached_return rc;
    memcached_st * memc = nullptr;
    MemcachedStorage(){}
public:
    static RamICacheStorage * getInstance() {
        if (instance == nullptr)
        {
            instance = new MemcachedStorage();
        }
        return instance;
    }
    STORAGE_TYPE getStorageType() override;
    STORAGE_STATUS initCacheStorage( const size_t max_size,const std::string m_point ) override;
    STORAGE_STATUS initServiceStorage (std::string svc) override;
    STORAGE_STATUS getFromStorage( const std::string svc, const std::string url, std::string & out_buffer) override;
    STORAGE_STATUS putInStorage( const std::string svc, const std::string url, const std::string buffer) override;
    STORAGE_STATUS stopCacheStorage() override;
    STORAGE_STATUS appendData(const std::string svc, const std::string url, const std::string buffer) override;

};
#endif
/**
 * @class DiskCacheStorage HttpCacheManager.h "src/handlers/HttpCacheManager.h"
 *
 * @brief The DiskCacheStorage implements the interface DiskICacheStorage in order to allow memcached storage
 */
class DiskCacheStorage: DiskICacheStorage {
private:
    unordered_map<size_t,string> cache_storage;
    DiskCacheStorage(){}
public:
    static DiskICacheStorage * getInstance() {
        if (instance == nullptr)
        {
            instance = new DiskCacheStorage();
        }
        return instance;
    }
    STORAGE_TYPE getStorageType() override;
    STORAGE_STATUS initCacheStorage( const size_t max_size,const std::string m_point ) override;
    STORAGE_STATUS initServiceStorage (std::string svc) override;
    STORAGE_STATUS getFromStorage( const std::string rel_path, std::string &out_buffer ) override;
    STORAGE_STATUS putInStorage( const std::string rel_path, const std::string buffer, size_t response_size) override;
    STORAGE_STATUS stopCacheStorage() override;
    STORAGE_STATUS appendData(const std::string rel_path, const std::string buffer) override;
    bool isInStorage(const std::string svc, const std::string url) override;
    STORAGE_STATUS deleteInStorage(std::string path) override;
    bool isInStorage(const std::string path);
};

class StdmapCacheStorage: public RamICacheStorage{
private:
    StdmapCacheStorage(){}
    std::string svc;
public:
    static RamICacheStorage * getInstance() {
        if (instance == nullptr)
        {
            instance = new StdmapCacheStorage();
        }
        return instance;
    }
    unordered_map <std::string, std::string> storage;
    STORAGE_TYPE getStorageType() override;
    STORAGE_STATUS initCacheStorage( const size_t max_size,const std::string m_point ) override;
    STORAGE_STATUS initServiceStorage (std::string svc) override;
    STORAGE_STATUS getFromStorage( const std::string rel_path, std::string &out_buffer ) override;
    STORAGE_STATUS putInStorage( const std::string rel_path, const std::string buffer, size_t response_size) override;
    STORAGE_STATUS stopCacheStorage() override;
    STORAGE_STATUS appendData(const std::string rel_path, const std::string buffer) override;
    bool isInStorage(const std::string svc, const std::string url) override;
    STORAGE_STATUS deleteInStorage(std::string path) override;
    bool isInStorage( std::string path );
};

#endif
