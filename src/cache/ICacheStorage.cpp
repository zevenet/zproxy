#if CACHE_ENABLED
#include "ICacheStorage.h"

#include <iostream>
#include <sys/stat.h>
#include <sys/types.h>
#include <filesystem>
#include "../debug/Debug.h"

// Ram Static variables definitions
RamICacheStorage * RamICacheStorage::instance = nullptr;
bool RamICacheStorage::initialized = false;
double RamICacheStorage::cache_thr;
size_t RamICacheStorage::current_size;
size_t RamICacheStorage::max_size;
std::string RamICacheStorage::mount_path;
// Disk Static variables definition
DiskICacheStorage * DiskICacheStorage::instance = nullptr;
bool DiskICacheStorage::initialized = false;
std::string DiskICacheStorage::mount_path;
size_t DiskICacheStorage::current_size;
size_t DiskICacheStorage::max_size = 0;

/*
 * RAMFS STORAGE
 */
STORAGE_STATUS RamfsCacheStorage::initCacheStorage( size_t m_size, std::string m_point ) {
    STORAGE_STATUS ret = STORAGE_STATUS::SUCCESS;
    if ( initialized )
        return STORAGE_STATUS::ALREADY_INIT;

    //Ensure that the size is always set
    if (m_size <= 0)
        m_size = MAX_STORAGE_SIZE;

    //Create directory, if fails, and it's not because the folder is already created, just return an error
    if (mkdir(m_point.data(),0777) == -1) {
        if (errno != EEXIST)
            return STORAGE_STATUS::MKDIR_ERROR;
    }
    mount_path = m_point;

    //try to mount the RAMFS filesystem, return MOUNT_ERROR if failed
    if( mount(nullptr, mount_path.data(), "ramfs",0,"mode=rw,uid=0") )
    {
        printf( "Error trying to mount the RAMFS filesystem in the path %s", mount_path.data());
        return STORAGE_STATUS::MOUNT_ERROR;
    }
    current_size = 0;
    max_size = m_size;


    initialized = true;

    return ret;
}
//Create the service folder
STORAGE_STATUS RamfsCacheStorage::initServiceStorage( std::string svc ) {
    if ( !initialized )
        return STORAGE_STATUS::NOT_INIT;
    //The mount point is mount_path/service
    if (mkdir((mount_path+string("/")+svc).data(),0777) == -1) {
        cerr << "Error :  " << std::strerror(errno) << endl;
        if (errno != EEXIST)
            return STORAGE_STATUS::MKDIR_ERROR;
    }
    return STORAGE_STATUS::SUCCESS;
}
STORAGE_TYPE RamfsCacheStorage::getStorageType(){ return STORAGE_TYPE::RAMFS; };
STORAGE_STATUS RamfsCacheStorage::getFromStorage( const std::string svc, const std::string url, std::string &out_buffer ){
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
STORAGE_STATUS RamfsCacheStorage::putInStorage( const std::string svc, const std::string url, const std::string buffer, size_t response_size){
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

    std::ofstream out_stream(file_path.data(), std::ofstream::trunc);
    if( !out_stream.is_open() )
        return STORAGE_STATUS::OPEN_ERROR;
    out_stream.write(buffer.data(), buffer.size());
    out_stream.close();

    if ( ! out_stream )
        return STORAGE_STATUS::FD_CLOSE_ERROR;

    return STORAGE_STATUS::SUCCESS;
}
STORAGE_STATUS RamfsCacheStorage::stopCacheStorage(){
    int err = umount(mount_path.data());
    if ( err )
        return STORAGE_STATUS::GENERIC_ERROR;

    return STORAGE_STATUS::SUCCESS;
}
STORAGE_STATUS RamfsCacheStorage::appendData(const std::string svc, const std::string url, const std::string buffer)
{
    ofstream fout;  // Create Object of Ofstream
    size_t hashed_url = std::hash<std::string>()(url);

    fout.open (std::string(mount_path + string("/") + svc + string("/") + to_string(hashed_url)).data(), std::ofstream::app); // Append mode
    if(fout.is_open())
        fout.write( buffer.data(),buffer.size());
    else
        return STORAGE_STATUS::APPEND_ERROR;
    fout.close(); // Closing the file
    current_size += buffer.size();
    return STORAGE_STATUS::SUCCESS;
}
bool RamfsCacheStorage::isStored(const std::string svc, const std::string url)
{
    struct stat buffer;
    size_t hashed_url = std::hash<std::string>()(url);
    return (stat( std::string(mount_path+"/"+svc+"/"+to_string(hashed_url)).data(), &buffer) == 0);
}
#if MEMCACHED_ENABLED
/*
 * MEMCACHED STORAGE
 */
STORAGE_TYPE MemcachedStorage::getStorageType(){ return STORAGE_TYPE::MEMCACHED;}
STORAGE_STATUS MemcachedStorage::initServiceStorage ( std::string svc ){
    return STORAGE_STATUS::SUCCESS;
}
STORAGE_STATUS MemcachedStorage::initCacheStorage( const size_t max_size,const std::string m_point ){
    memc = memcached_create(nullptr);
    memcached_server_add_unix_socket(memc,m_point.data());
//    memc = memcached (m_point.data(), m_point.size());
    if ( memc == nullptr )
        return STORAGE_STATUS::GENERIC_ERROR;
    return STORAGE_STATUS::SUCCESS;
}
STORAGE_STATUS MemcachedStorage::getFromStorage( const std::string svc, const std::string url, std::string & out_buffer){
    size_t hashed_key = std::hash<std::string>()(string(svc+"/"+url));

    size_t buff_length= 0;
    char * buff = memcached_get(memc, to_string(hashed_key).data(), to_string(hashed_key).size(), &buff_length, 0, &rc);
    if( rc != MEMCACHED_SUCCESS )
        return STORAGE_STATUS::GENERIC_ERROR;
    out_buffer = string(buff,buff_length);
    return STORAGE_STATUS::SUCCESS;
}
STORAGE_STATUS MemcachedStorage::putInStorage( const std::string svc, const std::string url, const std::string buffer){
    size_t hashed_key = std::hash<std::string>()(string(svc+"/"+url));

    if ( memcached_set(memc, to_string(hashed_key).data(), to_string(hashed_key).size(),  buffer.data(), buffer.size(), 0, 0) != MEMCACHED_SUCCESS )
        return STORAGE_STATUS::GENERIC_ERROR;
    return STORAGE_STATUS::SUCCESS;
}
STORAGE_STATUS MemcachedStorage::stopCacheStorage(){
    memcached_free(memc);
    return STORAGE_STATUS::SUCCESS;
}
STORAGE_STATUS MemcachedStorage::appendData(const std::string svc, const std::string url, const std::string buffer)
{
    //TODO: Fill the appendData
    return STORAGE_STATUS::SUCCESS;
}
#endif
/*
 * DISK STORAGE
 */
STORAGE_STATUS  DiskCacheStorage::initCacheStorage( size_t m_size, std::string m_point ) {
    STORAGE_STATUS ret = STORAGE_STATUS::SUCCESS;
    if ( initialized )
        return STORAGE_STATUS::ALREADY_INIT;
    //Create directory, if fails, and it's not because the folder is already created, just return an error
    if (mkdir(m_point.data(),0777) == -1) {
        if (errno != EEXIST)
            return STORAGE_STATUS::MKDIR_ERROR;
    }
    //Ensure that the size is always set
    if (m_size <= 0)
        m_size = MAX_STORAGE_SIZE;
    mount_path = m_point;
    current_size = 0;
    max_size = m_size;

    initialized = true;

    return ret;
}
//Create the service folder
STORAGE_STATUS DiskCacheStorage::initServiceStorage( std::string svc ) {
    if ( !initialized )
        return STORAGE_STATUS::NOT_INIT;
    //The mount point is mount_path/service
    if (mkdir((mount_path+string("/")+svc).data(),0777) == -1) {
        if (errno != EEXIST)
            return STORAGE_STATUS::MKDIR_ERROR;
    }
    return STORAGE_STATUS::SUCCESS;
}
STORAGE_TYPE DiskCacheStorage::getStorageType(){ return STORAGE_TYPE::DISK; };
STORAGE_STATUS DiskCacheStorage::getFromStorage( const std::string svc, const std::string url, std::string &out_buffer ){
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
STORAGE_STATUS DiskCacheStorage::putInStorage( const std::string svc, const std::string url, const std::string buffer, size_t response_size){
    if( !initialized )
        return STORAGE_STATUS::NOT_INIT;
// FIXME: Is it needed to check size? probably yes -> ZBA
//    if ( max_size <= current_size + buffer.size() )
//        //Storage full, set flag??
//        return STORAGE_STATUS::STORAGE_FULL;

    //Store in the path/svc/url
    size_t hashed_url = std::hash<std::string>()(url);
    // We have the file_path created as follows: /mount_point/svc1/hashed_url

    string file_path (mount_path + string("/") + svc + string("/") + to_string(hashed_url));
    //increment the current storage size
    current_size += buffer.size();

    std::ofstream out_stream(file_path.data(), std::ofstream::trunc );
    if( !out_stream.is_open() )
        return STORAGE_STATUS::OPEN_ERROR;
    out_stream.write(buffer.data(), buffer.size());
    out_stream.close();

    if ( ! out_stream )
        return STORAGE_STATUS::FD_CLOSE_ERROR;

    return STORAGE_STATUS::SUCCESS;
}
STORAGE_STATUS DiskCacheStorage::stopCacheStorage(){
    if ( remove( mount_path.data()))
        return STORAGE_STATUS::GENERIC_ERROR;
    return STORAGE_STATUS::SUCCESS;
}
STORAGE_STATUS DiskCacheStorage::appendData(const std::string svc, const std::string url, const std::string buffer)
{
    ofstream fout;  // Create Object of Ofstream
    size_t hashed_url = std::hash<std::string>()(url);

    fout.open (std::string(mount_path + string("/") + svc + string("/") + to_string(hashed_url)).data(), std::ofstream::app); // Append mode
    if(fout.is_open())
        fout.write(buffer.data(), buffer.size());
    else
        return STORAGE_STATUS::APPEND_ERROR;
    fout.close(); // Closing the file
    current_size += buffer.size();
    return STORAGE_STATUS::SUCCESS;
}
bool DiskCacheStorage::isStored(const std::string svc, const std::string url)
{
    struct stat buffer;
    size_t hashed_url = std::hash<std::string>()(url);
    return (stat( std::string(mount_path+"/"+svc+"/"+to_string(hashed_url)).data(), &buffer) == 0);
}

#endif
