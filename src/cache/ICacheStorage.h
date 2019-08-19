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
#include <string>
#include <cstring>
#include <pcreposix.h>
#include <unordered_map>
#include <iostream>
#include <fstream>
#if MEMCACHED_ENABLED
#include <libmemcached/memcached.h>
#endif

using namespace std;

#define MAX_STORAGE_SIZE 268435456; //256MB

enum STORAGE_STATUS { SUCCESS, MKDIR_ERROR, MOUNT_ERROR, MEMORY_ERROR, ALREADY_INIT, NOT_INIT, FD_CLOSE_ERROR, GENERIC_ERROR, OPEN_ERROR, STORAGE_FULL, APPEND_ERROR };
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
    virtual STORAGE_STATUS getFromStorage( const std::string svc, const std::string url, std::string & out_buffer ) = 0;
    virtual STORAGE_STATUS putInStorage( const std::string svc, const std::string url, const std::string buffer) = 0;
    virtual STORAGE_TYPE getStorageType() = 0;
    virtual STORAGE_STATUS stopCacheStorage() = 0;
    virtual STORAGE_STATUS appendData(const std::string svc, const std::string url, const std::string buffer) = 0;
    };

class DiskICacheStorage: public ICacheStorage{
protected:
    static DiskICacheStorage * instance;
    static bool initialized;
public:
    static size_t max_size;
    static size_t current_size;
    static std::string mount_path;
};

class RamICacheStorage: public ICacheStorage{
protected:
    static RamICacheStorage * instance;
    static bool initialized;
public:
    static size_t max_size;
    static size_t current_size;
    static std::string mount_path;
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
    STORAGE_STATUS getFromStorage( const std::string svc, const std::string url, std::string & out_buffer) override;
    STORAGE_STATUS putInStorage( const std::string svc, const std::string url, const std::string buffer) override;
    STORAGE_STATUS stopCacheStorage() override;
    STORAGE_STATUS appendData(const std::string svc, const std::string url, const std::string buffer) override;
};


/**
 * @class StdmapCacheStorage HttpCacheManager.h "src/handlers/HttpCacheManager.h"
 *
 * @brief The StdmapCacheStorage implements the interface ICacheStorage in order to allow STDMAP cache storage
 */
class StdmapCacheStorage: public RamICacheStorage{
private:
    unordered_map<size_t,string> cache_storage;
    StdmapCacheStorage(){}
public:
    static ICacheStorage * getInstance() {
        if (instance == nullptr)
        {
            instance = new StdmapCacheStorage();
        }
        return instance;
    }
    STORAGE_TYPE getStorageType() override;
    STORAGE_STATUS initCacheStorage( const size_t max_size,const std::string m_point ) override;
    STORAGE_STATUS initServiceStorage (std::string svc) override;
    STORAGE_STATUS getFromStorage( const std::string svc, const std::string url, std::string & out_buffer) override;
    STORAGE_STATUS putInStorage( const std::string svc, const std::string url, const std::string buffer) override;
    STORAGE_STATUS stopCacheStorage() override;
    STORAGE_STATUS appendData(const std::string svc, const std::string url, const std::string buffer) override{};
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
    static ICacheStorage * getInstance() {
        if (instance == nullptr)
        {
            instance = new DiskCacheStorage();
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
