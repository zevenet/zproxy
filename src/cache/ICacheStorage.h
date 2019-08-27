#if CACHE_ENABLED

//template <typename StorageType>
//class ICacheStorage {
//public:
//    static StorageType * instance;

//    static std::string path;
//    StorageType * getInstance(){
//        if(instance == nullptr)
//            instance = new StorageType();
//        return instance;
//    }

//    virtual int initCacheStorage();
//};
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

enum STORAGE_STATUS { SUCCESS, MKDIR_ERROR, MOUNT_ERROR, MEMORY_ERROR, ALREADY_INIT, NOT_INIT, FD_CLOSE_ERROR, GENERIC_ERROR, OPEN_ERROR, NOT_FOUND, STORAGE_FULL, APPEND_ERROR };
enum STORAGE_TYPE { RAMFS, STDMAP, TMPFS, DISK, MEMCACHED };

/**
 * @class ICacheStorage HttpCacheManager.h "src/handlers/HttpCacheManager.h"
 *
 * @brief Definition for the interface ICacheStorage
 */
class ICacheStorage {
protected:
    ICacheStorage(){}
public:
    virtual STORAGE_STATUS initCacheStorage(const size_t max_size, const std::string mount_point) = 0;
    virtual STORAGE_STATUS initServiceStorage( std::string svc ) = 0;
    virtual STORAGE_STATUS getFromStorage( const std::string rel_path, std::string &out_buffer ) = 0;
    virtual STORAGE_STATUS putInStorage( const std::string rel_path, const std::string buffer, size_t response_size) = 0;
    virtual STORAGE_TYPE getStorageType() = 0;
    virtual STORAGE_STATUS stopCacheStorage() = 0;
    virtual STORAGE_STATUS appendData(const std::string rel_path, const std::string buffer) = 0;
    virtual STORAGE_STATUS deleteInStorage(std::string url) = 0;
    virtual bool isStored(const std::string svc, const std::string url) = 0;
    virtual ~ICacheStorage() {}
    };

class DiskICacheStorage: public ICacheStorage{
protected:
    static DiskICacheStorage * instance;
    bool initialized = false;
public:
    size_t max_size = 0;
    size_t current_size = 0;
    std::string mount_path;
};

class RamICacheStorage: public ICacheStorage{
protected:
    static RamICacheStorage * instance;
    bool initialized = false;
public:
    size_t max_size = 0;
    size_t current_size = 0;
    std::string mount_path;
    double cache_thr = 0;
    virtual ~RamICacheStorage(){};
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
    bool isStored(const std::string svc, const std::string url) override;
    STORAGE_STATUS deleteInStorage(std::string path) override;
    bool isStored( std::string path );
};

/**
 * @class MemcachedStorage HttpCacheManager.h "src/handlers/HttpCacheManager.h"
 *
 * @brief The MemcachedStorage implements the interface RamICacheStorage in order to allow memcached storage
 */
#if MEMCACHED_ENABLED
//TODO: inherite from RamICacheStorage
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
    bool isStored(const std::string svc, const std::string url) override;
    STORAGE_STATUS deleteInStorage(std::string path) override;
    bool isStored(const std::string path);
};

#endif
