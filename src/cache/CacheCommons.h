#pragma once
#include <string>
#include <atomic>

namespace storage_commons {
enum STORAGE_STATUS { SUCCESS, MKDIR_ERROR, MOUNT_ERROR, MEMORY_ERROR, ALREADY_INIT, NOT_INIT, FD_CLOSE_ERROR, GENERIC_ERROR, OPEN_ERROR, NOT_FOUND, STORAGE_FULL, APPEND_ERROR, MPOINT_ALREADY_EXISTS};
enum STORAGE_TYPE { RAMFS, STDMAP, TMPFS, DISK, MEMCACHED };
}
namespace cache_commons {

enum class CACHE_SCOPE {
  PUBLIC,
  PRIVATE,
};
struct CacheObject {
    CacheObject(){
        dirty = true;
    }
    std::string etag;
    size_t content_length;
    bool no_cache_response =
            false;
    bool cacheable = true;
    bool transform = true;
    bool staled = false;
    bool revalidate = false;
    bool heuristic = false;
    std::atomic <bool> dirty = true;
    long int date = -1;
    long int last_mod = -1;
    long int expires = -1;
    long int max_age = -1;
    size_t headers_size = 0;
    CACHE_SCOPE scope;
    storage_commons::STORAGE_TYPE storage;
};
}

