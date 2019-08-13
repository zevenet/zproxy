#if CACHE_ENABLED
#pragma once

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
#include <pcreposix.h>
#include <unordered_map>
#include <iostream>
#include <fstream>
using namespace std;

#define MAX_STORAGE_SIZE 268435456; //256MB

enum STORAGE_STATUS { SUCCESS, MKDIR_ERROR, MOUNT_ERROR, MEMORY_ERROR, ALREADY_INIT, NOT_INIT, FD_CLOSE_ERROR, GENERIC_ERROR, OPEN_ERROR, STORAGE_FULL };
enum STORAGE_TYPE { RAMFS, STDMAP, TMPFS, DISK };

/**
 * @class ICacheStorage HttpCacheManager.h "src/handlers/HttpCacheManager.h"
 *
 * @brief Definition for the interface ICacheStorage
 *
 */
class ICacheStorage {
protected:
    ICacheStorage(){}
    static ICacheStorage * instance;
    static bool initialized;
public:
    static size_t max_size;
    static size_t current_size;
    static std::string mount_path;
    virtual STORAGE_STATUS initCacheStorage(const size_t max_size, const std::string mount_point) = 0;
    virtual STORAGE_STATUS initServiceStorage( std::string svc ) = 0;
    virtual STORAGE_STATUS getFromStorage( const std::string svc, const std::string url, std::string & out_buffer ) = 0;
    virtual STORAGE_STATUS putInStorage( const std::string svc, const std::string url, const std::string buffer) = 0;
    virtual STORAGE_TYPE getStorageType() = 0;
    virtual STORAGE_STATUS stopCacheStorage() = 0;
    };

/**
 * @class RamfsICacheStorage HttpCacheManager.h "src/handlers/HttpCacheManager.h"
 *
 * @brief The RamfsICacheStorage implements the interface ICacheStorage in order to allow RAMFS cache storage
 *
 */
class RamfsICacheStorage: public ICacheStorage{
private:
    RamfsICacheStorage(){}
public:
    static ICacheStorage * getInstance() {
        if (instance == nullptr)
        {
            instance = new RamfsICacheStorage();
        }
        return instance;
    }
    STORAGE_TYPE getStorageType() override;
    STORAGE_STATUS initCacheStorage( const size_t max_size,const std::string m_point ) override;
    STORAGE_STATUS initServiceStorage (std::string svc) override;
    STORAGE_STATUS getFromStorage( const std::string svc, const std::string url, std::string & out_buffer) override;
    STORAGE_STATUS putInStorage( const std::string svc, const std::string url, const std::string buffer) override;
    STORAGE_STATUS stopCacheStorage() override;
};


/**
 * @class StdmapICacheStorage HttpCacheManager.h "src/handlers/HttpCacheManager.h"
 *
 * @brief The StdmapICacheStorage implements the interface ICacheStorage in order to allow STDMAP cache storage
 *
 */
class StdmapICacheStorage: public ICacheStorage{
private:
    unordered_map<size_t,string> cache_storage;
    StdmapICacheStorage(){}
public:
    static ICacheStorage * getInstance() {
        if (instance == nullptr)
        {
            instance = new StdmapICacheStorage();
        }
        return instance;
    }
    STORAGE_TYPE getStorageType() override;
    STORAGE_STATUS initCacheStorage( const size_t max_size,const std::string m_point ) override;
    STORAGE_STATUS initServiceStorage (std::string svc) override;
    STORAGE_STATUS getFromStorage( const std::string svc, const std::string url, std::string & out_buffer) override;
    STORAGE_STATUS putInStorage( const std::string svc, const std::string url, const std::string buffer) override;
    STORAGE_STATUS stopCacheStorage() override;
};

#endif
