#if CACHE_ENABLED
#include "ICacheStorage.h"

#include <bits/stdc++.h>
#include <iostream>
#include <sys/stat.h>
#include <sys/types.h>

//Static variables
ICacheStorage * ICacheStorage::instance = 0;
bool ICacheStorage::initialized = false;
std::string ICacheStorage::mount_path;
size_t ICacheStorage::current_size;
size_t ICacheStorage::max_size;


/*
 *
 * RAMFS STORAGE
 *
 */
STORAGE_STATUS RamfsICacheStorage::initCacheStorage( size_t m_size, std::string m_point ) {
    STORAGE_STATUS ret = STORAGE_STATUS::SUCCESS;
    if ( initialized )
        return STORAGE_STATUS::ALREADY_INIT;

    //Ensure that the size is always set
    if (m_size <= 0)
        m_size = MAX_STORAGE_SIZE;

    mount_path = m_point;
    current_size = 0;
    max_size = m_size;

    //Create directory, if fails, and it's not because the folder is already created, just return an error
    if (mkdir(mount_path.data(),0777) == -1) {
        if (errno != EEXIST)
            return STORAGE_STATUS::MKDIR_ERROR;
    }
    //try to mount the RAMFS filesystem, return MOUNT_ERROR if failed
    if( mount(nullptr, mount_path.data(), "ramfs",0,"mode=rw,uid=0") )
    {
        printf( "Error trying to mount the RAMFS filesystem in the path %s", mount_path.data());
        return STORAGE_STATUS::MOUNT_ERROR;
    }
    initialized = true;

    return ret;
}
//Create the service folder
STORAGE_STATUS RamfsICacheStorage::initServiceStorage( std::string svc ) {
    if ( !initialized )
        return STORAGE_STATUS::NOT_INIT;
    //The mount point is mount_path/service
    if (mkdir((mount_path+string("/")+svc).data(),0777) == -1) {
        cerr << "Error :  " << strerror(errno) << endl;
        if (errno != EEXIST)
            return STORAGE_STATUS::MKDIR_ERROR;
    }
    return STORAGE_STATUS::SUCCESS;
}
STORAGE_TYPE RamfsICacheStorage::getStorageType(){ return STORAGE_TYPE::RAMFS; };
STORAGE_STATUS RamfsICacheStorage::getFromStorage( const std::string svc, const std::string url, std::string &out_buffer ){
    //get from path/svc/url
    size_t hashed_url = std::hash<std::string>()(url);

    // We have the file_path created as follows: /mount_point/svc1/hashed_url
    string file_path (mount_path + string("/") + svc + string("/") + to_string(hashed_url));


    std::ifstream in_stream( file_path.data());

    if ( !in_stream.is_open() )
        return  STORAGE_STATUS::OPEN_ERROR;

    std::stringstream buffer;
    buffer << in_stream.rdbuf();
    out_buffer = buffer.str();
    return STORAGE_STATUS::SUCCESS;
}
STORAGE_STATUS RamfsICacheStorage::putInStorage( const std::string svc, const std::string url, const std::string buffer){

    if( !initialized )
        return STORAGE_STATUS::NOT_INIT;
    if ( max_size <= current_size + buffer.size() )
        //Storage full, set flag??
        return STORAGE_STATUS::STORAGE_FULL;

    //Store in the path/svc/url
    size_t hashed_url = std::hash<std::string>()(url);
    // We have the file_path created as follows: /mount_point/svc1/hashed_url
    string file_path (mount_path + string("/") + svc + string("/") + to_string(hashed_url));
    //increment the current storage size
    current_size += buffer.size();

    std::ofstream out_stream(file_path.data());
    if( !out_stream.is_open() )
        return STORAGE_STATUS::OPEN_ERROR;
    out_stream << buffer;
    out_stream.close();

    if ( ! out_stream )
        return STORAGE_STATUS::FD_CLOSE_ERROR;

    return STORAGE_STATUS::SUCCESS;
}
STORAGE_STATUS RamfsICacheStorage::stopCacheStorage(){
    int err = umount(mount_path.data());
    if ( err )
        return STORAGE_STATUS::GENERIC_ERROR;

    return STORAGE_STATUS::SUCCESS;
}
/*
 *
 * STDMAP STORAGE
 *
 */
STORAGE_STATUS StdmapICacheStorage::initCacheStorage( size_t m_size, std::string m_point ) {
    STORAGE_STATUS ret = STORAGE_STATUS::SUCCESS;
    //Ensure that the size is always set
    if ( initialized )
        return STORAGE_STATUS::ALREADY_INIT;
    if (m_size <= 0)
        m_size = MAX_STORAGE_SIZE;

    mount_path = m_point;
    current_size = 0;
    max_size = m_size;

    initialized = true;

    return ret;
}
//Create the service folder
STORAGE_STATUS StdmapICacheStorage::initServiceStorage( std::string svc ) { return STORAGE_STATUS::SUCCESS; }
STORAGE_TYPE StdmapICacheStorage::getStorageType(){ return STORAGE_TYPE::STDMAP; };
STORAGE_STATUS StdmapICacheStorage::getFromStorage( const std::string svc, const std::string url, std::string &out_buffer ){
    //get from path/svc/url

    // We have the file_path created as follows: /mount_point/svc1/hashed_url
    std::string file_path (svc + string("/") + url);
    std::size_t hashed_index = std::hash<std::string>()(file_path);
    std::string buffer = cache_storage.at(hashed_index);
    if ( !buffer.length() )
        return STORAGE_STATUS::GENERIC_ERROR;
    out_buffer = buffer;
    return STORAGE_STATUS::SUCCESS;
}
STORAGE_STATUS StdmapICacheStorage::putInStorage( const std::string svc, const std::string url, const std::string buffer){

    if( !initialized )
        return STORAGE_STATUS::NOT_INIT;
    if ( max_size <= current_size + buffer.size() )
        //Storage full, set flag??
        return STORAGE_STATUS::STORAGE_FULL;

    //Store in the path/svc/url
    // We have the file_path created as follows: /mount_point/svc1/hashed_url
    string file_path (svc + string("/") + url);
    size_t hashed_index = std::hash<std::string>()(file_path);
    cache_storage[hashed_index] = buffer;

    //increment the current storage size
    current_size += buffer.size();

    return STORAGE_STATUS::SUCCESS;
}
STORAGE_STATUS StdmapICacheStorage::stopCacheStorage(){
    cache_storage.clear();
    return STORAGE_STATUS::SUCCESS;
}
#endif
