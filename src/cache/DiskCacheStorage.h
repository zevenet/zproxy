#pragma once
#include "CacheCommons.h"
#include "ICacheStorage.h"

/**
 * @brief The DiskICacheStorage interface is the specification of a ICacheStorage for DISK
 */
class DiskICacheStorage: public ICacheStorage{
protected:
    static DiskICacheStorage * instance;
    bool initialized = false;
public:
    static DiskICacheStorage * getInstance();
    size_t max_size = 0;
    size_t current_size = 0;
    std::string mount_path;
    virtual ~DiskICacheStorage(){}
};

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
    st::STORAGE_TYPE getStorageType() override;
    st::STORAGE_STATUS initCacheStorage( const size_t max_size,double st_threshold,const std::string &svc,const std::string &m_point ) override;
    st::STORAGE_STATUS initServiceStorage (const std::string &svc) override;
    st::STORAGE_STATUS getFromStorage( const std::string &rel_path, std::string &out_buffer ) override;
    st::STORAGE_STATUS putInStorage( const std::string &rel_path, std::string_view buffer, size_t response_size) override;
    st::STORAGE_STATUS stopCacheStorage() override;
    st::STORAGE_STATUS appendData(const std::string &rel_path, std::string_view buffer) override;
    bool isInStorage(const std::string &svc, const std::string &url) override;
    st::STORAGE_STATUS deleteInStorage(const std::string &path) override;
    bool isInStorage(const std::string &path);
};
