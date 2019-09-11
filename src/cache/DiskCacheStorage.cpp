#if CACHE_ENABLED
#include "DiskCacheStorage.h"

// Disk Static variables definition
DiskICacheStorage * DiskICacheStorage::instance = nullptr;

/*
 * DISKst::STORAGE
 */
st::STORAGE_STATUS  DiskCacheStorage::initCacheStorage( size_t m_size, double st_threshold, std::string svc, std::string m_point ) {
   st::STORAGE_STATUS ret =st::STORAGE_STATUS::SUCCESS;
    if ( initialized )
        return st::STORAGE_STATUS::ALREADY_INIT;
    //Create directory, if fails, and it's not because the folder is already created, just return an error
    if (mkdir(m_point.data(),0777) == -1) {
        if (errno == EEXIST)
        {
            initialized = true;
            mount_path = m_point;
            current_size = 0;
            //TODO: Recover
            return st::STORAGE_STATUS::MPOINT_ALREADY_EXISTS;
        }
        if (errno != EEXIST)
            return st::STORAGE_STATUS::MKDIR_ERROR;
    }
    //TODO: Set the maxsize
    mount_path = m_point;
    current_size = 0;
    m_size > 0 ? max_size = m_size : max_size = MAX_STORAGE_SIZE;
    initialized = true;

    return ret;
}
//Create the service folder
st::STORAGE_STATUS DiskCacheStorage::initServiceStorage( std::string svc ) {
    if ( !initialized )
        return st::STORAGE_STATUS::NOT_INIT;
    //The mount point is mount_path/service
    if (mkdir((mount_path+string("/")+svc).data(),0777) == -1) {
        if (errno == EEXIST)
            return st::STORAGE_STATUS::MPOINT_ALREADY_EXISTS;
        if (errno != EEXIST)
            return st::STORAGE_STATUS::MKDIR_ERROR;
    }
    return st::STORAGE_STATUS::SUCCESS;
}
st::STORAGE_TYPE DiskCacheStorage::getStorageType(){ return st::STORAGE_TYPE::DISK; };
st::STORAGE_STATUS DiskCacheStorage::getFromStorage( const std::string rel_path, std::string &out_buffer ){
    // We have the file_path created as follows: /mount_point/svc1/hashed_url
    string file_path (mount_path);
    file_path.append("/");
    file_path.append(rel_path);


    std::ifstream in_stream( file_path.data());

    if ( !in_stream.is_open() )
        return st::STORAGE_STATUS::OPEN_ERROR;

    std::stringstream buffer;
    buffer << in_stream.rdbuf();
    out_buffer = buffer.str();
    return st::STORAGE_STATUS::SUCCESS;
}
st::STORAGE_STATUS DiskCacheStorage::putInStorage( const std::string rel_path, const std::string buffer, size_t response_size){
    if( !initialized )
        return st::STORAGE_STATUS::NOT_INIT;
// FIXME: Is it needed to check size? probably yes -> ZBA
//    if ( max_size <= current_size + buffer.size() )
//        //Storage full, set flag??
//        return st::STORAGE_STATUS::STORAGE_FULL;

    // We have the file_path created as follows: /mount_point/svc1/hashed_url

    string file_path (mount_path);
    file_path.append("/");
    file_path.append(rel_path);
    //increment the current storage size
    current_size += buffer.size();

    std::ofstream out_stream(file_path.data(), std::ofstream::trunc );
    if( !out_stream.is_open() )
        return st::STORAGE_STATUS::OPEN_ERROR;
    out_stream.write(buffer.data(), buffer.size());
    out_stream.close();

    if ( ! out_stream )
        return st::STORAGE_STATUS::FD_CLOSE_ERROR;

    return st::STORAGE_STATUS::SUCCESS;
}
st::STORAGE_STATUS DiskCacheStorage::stopCacheStorage(){
    const std::filesystem::path path_m_point = std::filesystem::u8path (mount_path);
    if(!std::filesystem::remove_all(path_m_point))
        return st::STORAGE_STATUS::GENERIC_ERROR;
    return st::STORAGE_STATUS::SUCCESS;
}
st::STORAGE_STATUS DiskCacheStorage::appendData(const std::string rel_path, const std::string buffer)
{
    ofstream fout;  // Create Object of Ofstream
    //Create path
    auto path = mount_path;
    path.append ("/");
    path.append(rel_path);

    fout.open (path, std::ofstream::app); // Append mode
    if(fout.is_open())
        fout.write(buffer.data(), buffer.size());
    else
        return st::STORAGE_STATUS::APPEND_ERROR;
    fout.close(); // Closing the file
    current_size += buffer.size();
    return st::STORAGE_STATUS::SUCCESS;
}
bool DiskCacheStorage::isInStorage(const std::string svc, const std::string url)
{
    struct stat buffer;
    size_t hashed_url = std::hash<std::string>()(url);
    return (stat( std::string(mount_path+"/"+svc+"/"+to_string(hashed_url)).data(), &buffer) == 0);
}
bool DiskCacheStorage::isInStorage(const std::string path)
{
    struct stat buffer;
    return (stat( path.data(), &buffer) == 0);
}

st::STORAGE_STATUS DiskCacheStorage::deleteInStorage(string path)
{
    auto full_path = mount_path;
    full_path.append("/");
    full_path.append(path);
    if( isInStorage(full_path) ){
        if ( std::remove( full_path.data()) )
            return st::STORAGE_STATUS::GENERIC_ERROR;
    }
    else
        return st::STORAGE_STATUS::NOT_FOUND;
    return st::STORAGE_STATUS::SUCCESS;
}
#endif
