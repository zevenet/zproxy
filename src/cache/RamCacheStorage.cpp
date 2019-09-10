#if CACHE_ENABLED
#include "RamCacheStorage.h"

// Ram Static variables definitions
RamICacheStorage * RamICacheStorage::instance = nullptr;

RamICacheStorage *RamICacheStorage::getInstance()
{
    if(instance == nullptr )
    {
#if CACHE_STORAGE_STDMAP
        instance = new StdmapCacheStorage();
#elif MEMCACHED_ENABLED
        instance = new MemcachedStorage();
#else
        instance = new RamfsCacheStorage();
#endif
    }
    return instance;
}

st::STORAGE_STATUS RamfsCacheStorage::initCacheStorage( size_t m_size, double st_threshold, std::string svc, std::string m_point ) {
    st::STORAGE_STATUS ret = st::STORAGE_STATUS::SUCCESS;
    if ( initialized )
        return st::STORAGE_STATUS::ALREADY_INIT;

    //Ensure that the size is always set
    if (m_size <= 0)
        m_size = MAX_STORAGE_SIZE;

    //Create directory, if fails, and it's not because the folder is already created, just return an error
    if (mkdir(m_point.data(),0777) == -1) {
        if (errno == EEXIST)
        {
            initialized = true;
            max_size = m_size;
            mount_path = m_point.data();
            cache_thr = st_threshold;
            //TODO: Recover from here
            return st::STORAGE_STATUS::MPOINT_ALREADY_EXISTS;
        }
        else
            return st::STORAGE_STATUS::MKDIR_ERROR;
    }
    mount_path = m_point.data();

    //try to mount the RAMFS filesystem, return MOUNT_ERROR if failed
    if( mount(nullptr, mount_path.data(), "ramfs",0,"mode=rw,uid=0") )
    {
        printf( "Error trying to mount the RAMFS filesystem in the path %s", mount_path.data());
        return st::STORAGE_STATUS::MOUNT_ERROR;
    }
    current_size = 0;
    max_size = m_size;


    initialized = true;

    return ret;
}
//Create the service folder
st::STORAGE_STATUS RamfsCacheStorage::initServiceStorage( std::string svc ) {
    if ( !initialized )
        return st::STORAGE_STATUS::NOT_INIT;
    if (mkdir((mount_path+string("/")+svc).data(),0777) == -1) {
        if (errno == EEXIST)
            return st::STORAGE_STATUS::MPOINT_ALREADY_EXISTS;
        else{
            Debug::logmsg(LOG_ERR, "Error :  %s", std::strerror(errno));
            return st::STORAGE_STATUS::MKDIR_ERROR;
        }
    }
    return st::STORAGE_STATUS::SUCCESS;
}
st::STORAGE_TYPE RamfsCacheStorage::getStorageType(){ return st::STORAGE_TYPE::RAMFS; };
st::STORAGE_STATUS RamfsCacheStorage::getFromStorage( const std::string rel_path, std::string &out_buffer ){

    // We have the file_path created as follows: /mount_point/svc1/hashed_url
    string file_path (mount_path);
    file_path.append(string("/"));
    file_path.append(rel_path);

    std::ifstream in_stream( file_path.data());

    if ( !in_stream.is_open() )
        return st::STORAGE_STATUS::OPEN_ERROR;

    std::stringstream buffer;
    buffer << in_stream.rdbuf();
    out_buffer = buffer.str();
    return st::STORAGE_STATUS::SUCCESS;
}
st::STORAGE_STATUS RamfsCacheStorage::putInStorage( const std::string rel_path, const std::string buffer, size_t response_size){
    if( !initialized )
        return st::STORAGE_STATUS::NOT_INIT;
    if ( max_size <= current_size + response_size )
        //Storage full, set flag??
        return st::STORAGE_STATUS::STORAGE_FULL;

    // We have the file_path created as follows: /mount_point/svc1/hashed_url
    string file_path (mount_path);
    file_path.append("/");
    file_path.append(rel_path);

    //increment the current storage size
    current_size += buffer.size();

    std::ofstream out_stream(file_path.data(), std::ofstream::trunc);
    if( !out_stream.is_open() )
        return st::STORAGE_STATUS::OPEN_ERROR;
    out_stream.write(buffer.data(), buffer.size());
    out_stream.close();

    if ( ! out_stream )
        return st::STORAGE_STATUS::FD_CLOSE_ERROR;

    return st::STORAGE_STATUS::SUCCESS;
}
st::STORAGE_STATUS RamfsCacheStorage::stopCacheStorage(){
    int err = umount(mount_path.data());
    if ( err )
    {
        Debug::logmsg(LOG_REMOVE,"Error umounting the cache path %s ", mount_path.data() );
        return st::STORAGE_STATUS::GENERIC_ERROR;
    }
    std::filesystem::remove(mount_path.data());

    return st::STORAGE_STATUS::SUCCESS;
}
st::STORAGE_STATUS RamfsCacheStorage::appendData(const std::string rel_path, const std::string buffer)
{
    ofstream fout;  // Create Object of Ofstream
    auto path (mount_path);
    path.append("/");
    path.append(rel_path);

    fout.open (path, std::ofstream::app); // Append mode
    if(fout.is_open())
        fout.write( buffer.data(),buffer.size());
    else
        return st::STORAGE_STATUS::APPEND_ERROR;
    fout.close(); // Closing the file
    current_size += buffer.size();
    return st::STORAGE_STATUS::SUCCESS;
}
bool RamfsCacheStorage::isInStorage(const std::string svc, const std::string url)
{
    size_t hashed_url = std::hash<std::string>()(url);
    return isInStorage(std::string(mount_path+"/"+svc+"/"+to_string(hashed_url)).data());
}
bool RamfsCacheStorage::isInStorage( std::string path )
{
    struct stat buffer;
    return (stat(path.data(),&buffer) == 0);
}

st::STORAGE_STATUS RamfsCacheStorage::deleteInStorage(std::string path)
{
    //Create the path string
    auto full_path = mount_path;
    full_path.append("/");
    full_path.append(path);

    if( isInStorage(full_path) ){
        Debug::logmsg(LOG_NOTICE, "DELETING STORED CONTENT");
        if ( std::remove( full_path.data()) )
            return st::STORAGE_STATUS::GENERIC_ERROR;
    }
    else
        return st::STORAGE_STATUS::NOT_FOUND;
    return st::STORAGE_STATUS::SUCCESS;
}

st::STORAGE_TYPE StdmapCacheStorage::getStorageType(){
    return st::STORAGE_TYPE::STDMAP;
}
st::STORAGE_STATUS StdmapCacheStorage::initCacheStorage( const size_t max_size,double st_threshold, std::string svc, const std::string m_point ){
    this->mount_path = m_point;
    this->max_size = max_size;
    this->cache_thr =  st_threshold;

    return initServiceStorage(svc);
}
st::STORAGE_STATUS StdmapCacheStorage::initServiceStorage (std::string svc){
    this->svc = svc;
    return st::STORAGE_STATUS::SUCCESS;
}
st::STORAGE_STATUS StdmapCacheStorage::getFromStorage( const std::string rel_path, std::string &out_buffer ){
    std::string path = mount_path;
    path += "/";
    path += rel_path;
    out_buffer = storage.at(path);
    return st::STORAGE_STATUS::SUCCESS;
}
st::STORAGE_STATUS StdmapCacheStorage::putInStorage( const std::string rel_path, const std::string buffer, size_t response_size){
    current_size += buffer.size();
    std::string path = mount_path;
    path.append("/");
    path.append(rel_path);
    storage[path] = std::string(buffer);
    return st::STORAGE_STATUS::SUCCESS;
}
st::STORAGE_STATUS StdmapCacheStorage::stopCacheStorage(){

    return st::STORAGE_STATUS::SUCCESS;
}
st::STORAGE_STATUS StdmapCacheStorage::appendData(const std::string rel_path, const std::string buffer){
    std::string path = mount_path;
    path.append("/");
    path.append(rel_path);
    std::string out_buffer = storage.at(path);
    out_buffer.append(buffer);
    storage[path] = out_buffer;
    return st::STORAGE_STATUS::SUCCESS;
}
bool StdmapCacheStorage::isInStorage(const std::string svc, const std::string url){
    std::string path = mount_path;
    path.append( "/");
    path.append(svc);
    path.append("/");

    size_t hashed_url = hash<std::string>()(url);
    path += to_string(hashed_url);
    return  isInStorage(path);
}
st::STORAGE_STATUS StdmapCacheStorage::deleteInStorage(std::string path){
    if (storage.erase(path) != 1)
        return st::STORAGE_STATUS::GENERIC_ERROR;
    return st::STORAGE_STATUS::SUCCESS;
}
bool StdmapCacheStorage::isInStorage( std::string path ){
    if (storage.find(path) == storage.end())
      return false;
    else
      return true;
}
#if MEMCACHED_ENABLED
/*
 * MEMCACHEDst::STORAGE
 */
st::STORAGE_TYPE MemcachedStorage::getStorageType(){ return st::STORAGE_TYPE::MEMCACHED;}
st::STORAGE_STATUS MemcachedStorage::initServiceStorage ( std::string svc ){
    return st::STORAGE_STATUS::SUCCESS;
}
st::STORAGE_STATUS MemcachedStorage::initCacheStorage( const size_t max_size,const std::string m_point ){
    memc = memcached_create(nullptr);
    memcached_server_add_unix_socket(memc,m_point.data());
//    memc = memcached (m_point.data(), m_point.size());
    if ( memc == nullptr )
        return st::STORAGE_STATUS::GENERIC_ERROR;
    return st::STORAGE_STATUS::SUCCESS;
}
st::STORAGE_STATUS MemcachedStorage::getFromStorage( const std::string svc, const std::string url, std::string & out_buffer){
    size_t hashed_key = std::hash<std::string>()(string(svc+"/"+url));

    size_t buff_length= 0;
    char * buff = memcached_get(memc, to_string(hashed_key).data(), to_string(hashed_key).size(), &buff_length, 0, &rc);
    if( rc != MEMCACHED_SUCCESS )
        return st::STORAGE_STATUS::GENERIC_ERROR;
    out_buffer = string(buff,buff_length);
    return st::STORAGE_STATUS::SUCCESS;
}
st::STORAGE_STATUS MemcachedStorage::putInStorage( const std::string svc, const std::string url, const std::string buffer){
    size_t hashed_key = std::hash<std::string>()(string(svc+"/"+url));

    if ( memcached_set(memc, to_string(hashed_key).data(), to_string(hashed_key).size(),  buffer.data(), buffer.size(), 0, 0) != MEMCACHED_SUCCESS )
        return st::STORAGE_STATUS::GENERIC_ERROR;
    return st::STORAGE_STATUS::SUCCESS;
}
st::STORAGE_STATUS MemcachedStorage::stopCacheStorage(){
    memcached_free(memc);
    return st::STORAGE_STATUS::SUCCESS;
}
st::STORAGE_STATUS MemcachedStorage::appendData(const std::string svc, const std::string url, const std::string buffer)
{
    //TODO: Fill the appendData
    return st::STORAGE_STATUS::SUCCESS;
}
#endif
#endif
