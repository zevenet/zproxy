#if CACHE_ENABLED
#pragma once
#include "CacheCommons.h"
#include "ICacheStorage.h"

/**
 * @brief The RamICacheStorage interface is the specification of a ICacheStorage for RAM
 */
class RamICacheStorage: public ICacheStorage{
protected:
    static RamICacheStorage * instance;
    bool initialized = false;
public:
    static RamICacheStorage * getInstance();
    size_t max_size = 0;
    size_t current_size = 0;
    std::string mount_path;
    double cache_thr = 0;
    virtual ~RamICacheStorage(){}
};
/**
 * @class RamfsCacheStorage RamCacheStorage.h "src/cache/RamCacheStorage.h"
 *
 * @brief The RamfsCacheStorage implements the interface RamICacheStorage in order to use RAMFS cache storage
 */
class RamfsCacheStorage: public RamICacheStorage{
public:
    st::STORAGE_TYPE getStorageType() override;
    st::STORAGE_STATUS initCacheStorage( const size_t max_size, double st_threshold, const std::string &svc, const std::string &m_point ) override;
    st::STORAGE_STATUS initServiceStorage (const std::string &svc) override;
    st::STORAGE_STATUS getFromStorage( const std::string &rel_path, std::string &out_buffer ) override;
    st::STORAGE_STATUS putInStorage( const std::string &rel_path, std::string_view buffer, size_t response_size) override;
    st::STORAGE_STATUS stopCacheStorage() override;
    st::STORAGE_STATUS appendData(const std::string &rel_path, std::string_view buffer) override;
    bool isInStorage(const std::string &svc, const std::string &url) override;
    st::STORAGE_STATUS deleteInStorage(const std::string &path) override;
    bool isInStorage( const std::string &path );
};
/**
 * @class StdmapCacheStorage RamCacheStorage.h "src/handlers/RamCacheStorage.h"
 *
 * @brief The StdmapCacheStorage implements the interface RamICacheStorage in order to use STDMAP cache storage
 */
class StdmapCacheStorage: public RamICacheStorage{
private:
    std::string svc;
public:
    StdmapCacheStorage(){}
    unordered_map <std::string, std::string> storage;
    st::STORAGE_TYPE getStorageType() override;
    st::STORAGE_STATUS initCacheStorage( const size_t max_size,double st_threshold, const std::string &svc, const std::string &m_point ) override;
    st::STORAGE_STATUS initServiceStorage (const std::string &svc) override;
    st::STORAGE_STATUS getFromStorage( const std::string &rel_path, std::string &out_buffer ) override;
    st::STORAGE_STATUS putInStorage( const std::string &rel_path, std::string_view buffer, size_t response_size) override;
    st::STORAGE_STATUS stopCacheStorage() override;
    st::STORAGE_STATUS appendData(const std::string &rel_path, std::string_view buffer) override;
    bool isInStorage(const std::string &svc, const std::string &url) override;
    st::STORAGE_STATUS deleteInStorage(const std::string &path) override;
    bool isInStorage( const std::string &path );
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
public:
    MemcachedStorage(){}
    st::STORAGE_TYPE getStorageType() override;
    st::STORAGE_STATUS initCacheStorage( const size_t max_size,const std::string m_point ) override;
    st::STORAGE_STATUS initServiceStorage (std::string svc) override;
    st::STORAGE_STATUS getFromStorage( const std::string svc, const std::string url, std::string & out_buffer) override;
    st::STORAGE_STATUS putInStorage( const std::string svc, const std::string url, const std::string buffer) override;
    st::STORAGE_STATUS stopCacheStorage() override;
    st::STORAGE_STATUS appendData(const std::string svc, const std::string url, const std::string buffer) override;

};
#endif
#endif
