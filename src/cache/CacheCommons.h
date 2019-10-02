#pragma once
#include <string>
#include <atomic>
#include "../util/utils.h"
#include "../http/http.h"
namespace storage_commons {
enum STORAGE_STATUS { SUCCESS, MKDIR_ERROR, MOUNT_ERROR, MEMORY_ERROR, ALREADY_INIT, NOT_INIT, FD_CLOSE_ERROR, GENERIC_ERROR, OPEN_ERROR, NOT_FOUND, STORAGE_FULL, APPEND_ERROR, MPOINT_ALREADY_EXISTS};
enum STORAGE_TYPE { RAMFS, STDMAP, TMPFS, DISK, MEMCACHED };
}
namespace cache_commons {

enum CACHE_SCOPE {
    PUBLIC,
    PRIVATE,
};
struct CacheObject {
    CacheObject(){
        dirty = true;
        chunked = http::CHUNKED_STATUS::CHUNKED_DISABLED;
        encoding = http::TRANSFER_ENCODING_TYPE::NONE;
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
    cache_commons::CACHE_SCOPE scope;
    storage_commons::STORAGE_TYPE storage;
    http::TRANSFER_ENCODING_TYPE encoding;
    http::CHUNKED_STATUS chunked;
    /**
     * @brief Checks whether the cached content is fresh or not, staling it if not
     * fresh.
     *
     * @param request is the HttpRequest to check if the resource is fresh or
     * not.
     * @return if the content is fresh it returns true or false in other case
     */
    bool isFresh( time_t current_time) {
        updateFreshness(current_time);

        return !this->staled;
    }
    /**
     * @brief updateFreshness update the freshness for a single stored response
     * @param c_object, the cache_commons::CacheObject which we want to update
     */
    void updateFreshness(time_t current_time) {
        if (!this->staled) {
            time_t now = current_time;
            long int age_limit = 0;
            if (this->max_age >= 0 && !this->heuristic)
                age_limit = this->max_age;
            else if (this->expires >= 0)
                age_limit = this->expires;
            else if (this->max_age >= 0 && this->heuristic)
                age_limit = this->max_age;
            if ((now - this->date) > age_limit) {
                this->staled = true;
            }
        }
    }
};

struct cache_stats {
    long cache_RAM_inserted_entries = 0; /* Number of times  */
    std::string cache_RAM_mountpoint;
    long cache_RAM_used = 0;
    long cache_DISK_inserted_entries = 0;
    std::string cache_DISK_mountpoint;
    long cache_DISK_used = 0;
    double cache_match = 0;
    long cache_staled_entries = 0;
    double cache_miss = 0;
    double cache_not_stored = 0;
};

}
