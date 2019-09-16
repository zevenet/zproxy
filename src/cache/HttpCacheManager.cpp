#if CACHE_ENABLED
#include "HttpCacheManager.h"
// Returns the cache content with all the information stored
cache_commons::CacheObject *HttpCacheManager::getCacheObject(HttpRequest request) {
  return getCacheObject(std::hash<std::string>()(request.getUrl()));
}
cache_commons::CacheObject *HttpCacheManager::getCacheObject(size_t hashed_url) {
  cache_commons::CacheObject *c_object = nullptr;
  auto iter = cache.find(hashed_url);
  if (iter != cache.end()){
    c_object = iter->second;
  }
  return c_object;
}

// Store in cache the response if it doesn't exists
void HttpCacheManager::handleResponse(HttpResponse &response,
                                      HttpRequest request) {
  auto c_opt = getCacheObject(request);
  if ( c_opt != nullptr && c_opt->dirty == true ){
        return;
  }

  if( c_opt != nullptr && c_opt->isFresh()){
      //If the stored response is fresh, we must not to store this response
      response.c_opt.cacheable = false;
  }
  // If the response/request is set as not cacheable, we can't cache it
  if (!response.c_opt.cacheable) {
    return;
  } else if (response.cache_control == false && response.pragma == true) {
    // Check the pragma only if no cache-control header in request nor in
    // response, if the pragma was present, disable cache
    return;
  }
  //  Check status code
  if (response.http_status_code != 200 && response.http_status_code != 301 &&
          response.http_status_code != 308){
      return;
  }
  if ( ((response.content_length + response.headers_length ) >= cache_max_size) && cache_max_size != 0 ){
    DEBUG_COUNTER_HIT(cache_stats__::cache_not_stored);
    Debug::logmsg(LOG_WARNING, "Not caching response with %d bytes size", response.content_length + response.headers_length);
    return;
  }

  // Check HTTP verb
  switch (http::http_info::http_verbs.at(
      std::string(request.method, request.method_len))) {
  case http::REQUEST_METHOD::GET:
    addResponse(response, request);
    break;
  case http::REQUEST_METHOD::HEAD:
    if (getCacheObject(request) != nullptr)
      updateResponse(response, request);
    break;
  default:
    return;
  }
  return;
}

void HttpCacheManager::updateResponse(HttpResponse response,
                                      HttpRequest request) {
  auto c_object = getCacheObject(request);
  if (response.content_length == 0){
    Debug::logmsg(LOG_WARNING, "Content-Length header with 0 value when trying "
                               "to update content in the cache");
  }
  if (response.content_length != c_object->content_length) {
    Debug::logmsg(
        LOG_WARNING,
        "Content-Length in response and Content-Length cached missmatch for %s",
        request.getUrl().data());
    return;
  }
  if (response.etag.compare(c_object->etag) != 0) {
    Debug::logmsg(LOG_WARNING,
                  "ETag in response and ETag cached missmatch for %s",
                  request.getUrl().data());
    return;
  }
  c_object->staled = false;
  c_object->date = timeHelper::gmtTimeNow();

  return;
}
// Decide on whether to use RAMFS or disk
st::STORAGE_TYPE HttpCacheManager::getStorageType( HttpResponse response )
{
    size_t ram_size_left = ram_storage->max_size - ram_storage->current_size;

    size_t response_size = response.http_message_length + response.content_length;
    //If chunked -> store in disk
    if ( (response.chunked_status != http::CHUNKED_STATUS::CHUNKED_DISABLED &&
          response.transfer_encoding_type == http::TRANSFER_ENCODING_TYPE::CHUNKED ) ||
         response_size > ram_storage->max_size * 0.05 || response_size >= ram_size_left ){
        return st::STORAGE_TYPE::DISK;
    }
#if CACHE_STORAGE_STDMAP
    else{
        return STORAGE_TYPE::STDMAP;
    }
#else
    else{
        return st::STORAGE_TYPE::RAMFS;
    }
#endif
}

bool HttpCacheManager::needCacheMaintenance()
{
    auto current_time = timeHelper::gmtTimeNow();
    return ( current_time - last_maintenance > 0 ) ? true : false;
}

HttpCacheManager::~HttpCacheManager() {
    // Free cache pattern
    if (cache_pattern != nullptr){
        regfree(cache_pattern);
        cache_pattern = nullptr;
        ram_storage->stopCacheStorage();
        disk_storage->stopCacheStorage();
        cache.clear();
    }
}

void HttpCacheManager::cacheInit(regex_t *pattern, const int timeout, const std::string svc, long storage_size, int storage_threshold, std::string f_name, std::string cache_ram_mpoint,std::string cache_disk_mpoint) {
    if (pattern != nullptr) {
        if (pattern->re_pcre != nullptr) {
            this->cache_pattern = pattern;
            this->cache_timeout = timeout;
            this->cache_enabled = true;
            this->service_name = svc;
        }
        else {
            return;
        }
        if ( cache_ram_mpoint.size() > 0 ){
            ramfs_mount_point = cache_ram_mpoint;
            if ( ramfs_mount_point.back() == '/'){
                ramfs_mount_point.erase(ramfs_mount_point.size()-1);
            }
        }
        if ( cache_disk_mpoint.size() > 0 ){
            disk_mount_point = cache_disk_mpoint;
            if ( disk_mount_point.back() == '/'){
                disk_mount_point.erase(disk_mount_point.size()-1);
            }
        }
        //Create directory, if fails, and it's not because the folder is already created, just return an error
        if (mkdir(ramfs_mount_point.data(),0777) == -1) {
            if (errno != EEXIST){
                Debug::logmsg(LOG_ERR, "Error creating the directory %s", ramfs_mount_point.data());
                exit( 1 );
            }
        }
        if (mkdir(disk_mount_point.data(),0777) == -1) {
            if (errno != EEXIST){
                Debug::logmsg(LOG_ERR, "Error creating the directory %s", disk_mount_point.data());
                exit( 1 );
            }
        }

        //Set mount point farm name dependant
        ramfs_mount_point.append ("/");
        ramfs_mount_point.append(f_name);
        disk_mount_point.append ("/");
        disk_mount_point.append(f_name);


        st::STORAGE_STATUS svc_status;
//RAM
        ram_storage = RamICacheStorage::getInstance();
        ram_storage->initCacheStorage(static_cast<unsigned long>(storage_size), static_cast<double>(storage_threshold) / 100, svc, ramfs_mount_point);
        svc_status = ram_storage->initServiceStorage(svc);
        //recover cache status
        if ( svc_status == st::STORAGE_STATUS::MPOINT_ALREADY_EXISTS ){
            recoverCache(svc,st::STORAGE_TYPE::RAMFS);
        }

//DISK
        disk_storage = DiskCacheStorage::getInstance();
        disk_storage->initCacheStorage(0, 0, svc, disk_mount_point);
        svc_status = disk_storage->initServiceStorage(svc);
        //recover cache status
        if ( svc_status == st::STORAGE_STATUS::MPOINT_ALREADY_EXISTS ){
            recoverCache(svc, st::STORAGE_TYPE::DISK);
        }

        last_maintenance = timeHelper::gmtTimeNow();
    }
}

void HttpCacheManager::addResponse(HttpResponse &response,
                                     HttpRequest request) {
  auto cache_entry = new cache_commons::CacheObject();
  std::unique_ptr<cache_commons::CacheObject> c_object ( cache_entry);
  auto hashed_url = hash<std::string> ()(request.getUrl());
  auto old_object = getCacheObject(request);
  cache[hashed_url] = c_object.get();

  addResponseEntry(response, c_object.get());
  // link response with c_object
  response.c_object = c_object.get();

  //Check what storage to use
  st::STORAGE_STATUS err;

  //Create the path string
  std::string rel_path = service_name;
  rel_path.append("/");
  rel_path.append(to_string(hashed_url));

  switch (c_object->storage){
  case st::STORAGE_TYPE::STDMAP:
  case st::STORAGE_TYPE::RAMFS:
      if( old_object != nullptr ){
        ram_storage->current_size -= (old_object->content_length + old_object->headers_size);
      }
      err = ram_storage->putInStorage(rel_path, std::string(response.buffer,response.buffer_size), (response.content_length + response.headers_length));
      if(err == st::STORAGE_STATUS::SUCCESS){
          DEBUG_COUNTER_HIT(cache_stats__::cache_RAM_entries);
      }
      break;
  case st::STORAGE_TYPE::DISK:
      if( old_object != nullptr){
        disk_storage->current_size -= (old_object->content_length + old_object->headers_size);
      }
      err = disk_storage->putInStorage(rel_path, std::string(response.buffer,response.buffer_size), (response.content_length + response.headers_length));
      if(err == st::STORAGE_STATUS::SUCCESS){
          DEBUG_COUNTER_HIT(cache_stats__::cache_DISK_entries);
      }
      break;
  default:
      return;
  }
  // If success, store in the unordered map
  if ( err != st::STORAGE_STATUS::SUCCESS){
    Debug::logmsg(LOG_ERR, "Error trying to store the response in storage");
    deleteEntry(request);
    return;
  }
  c_object->headers_size = response.headers_length;
  if ( response.chunked_status == http::CHUNKED_STATUS::CHUNKED_DISABLED ){
      if ( response.content_length == response.message_length ){
          c_object->dirty = false;
      }
  }
//TRY
  if( response.chunked_status == http::CHUNKED_STATUS::CHUNKED_LAST_CHUNK ){
      c_object->dirty = false;
      c_object->content_length = response.content_length;
  }

  c_object.release();
  return;
}

void HttpCacheManager::addResponseEntry( HttpResponse response,cache_commons::CacheObject * c_object ){
    if ( c_object == nullptr) {
        c_object = new cache_commons::CacheObject();
    }
    // Store the response date in the cache
    if ( response.date <= 0 ){
        response.date = timeHelper::gmtTimeNow();
    }
    if ( response.last_mod <= 0) {
        response.last_mod = timeHelper::gmtTimeNow();
    }

    c_object->date = response.date;
    /*
   *max-age, s-maxage, etc.
   */
    // If the max_age is not set nor the timeout exist, we have to calculate
    // heuristically
    if (response.c_opt.max_age >= 0 && this->cache_timeout != 0){
        // Set the most restrictive value
        response.c_opt.max_age > this->cache_timeout
                ? c_object->max_age = this->cache_timeout
                : c_object->max_age = response.c_opt.max_age;
    }
    else if (this->cache_timeout >= 0){
        // Store the config file timeout
        c_object->max_age = this->cache_timeout;
    }
    else if (response.c_opt.max_age >= 0){
        // Store the response cache max-age
        c_object->max_age = response.c_opt.max_age;
    }
    else if (response.last_mod >= 0) {
        // heuristic algorithm -> 10% of last-modified
        time_t now = timeHelper::gmtTimeNow();
        c_object->max_age = (now - response.last_mod) * 0.1;
    } else {
        // If not available value, use the defined default timeout
        c_object->max_age = DEFAULT_TIMEOUT;
    }
    /*
     *must-revalidate, proxy-revalidate
     */
    if (response.expires >= 0){
        c_object->expires = response.expires;
    }
    // If there is etag, then store it
    if (!response.etag.empty()){
        c_object->etag = response.etag;
    }

    c_object->revalidate = response.c_opt.revalidate;
    // Reset the stale flag, the cache has been created or updated
    c_object->staled = false;
    c_object->content_length = response.content_length;
    c_object->no_cache_response = response.c_opt.no_cache;

    c_object->encoding = response.transfer_encoding_type;

    switch ( getStorageType(response)){
    case st::STORAGE_TYPE::RAMFS:
        c_object->storage = st::STORAGE_TYPE::RAMFS;
        break;
    case st::STORAGE_TYPE::DISK:
        c_object->storage = st::STORAGE_TYPE::DISK;
        break;
    case st::STORAGE_TYPE::STDMAP:
        c_object->storage = st::STORAGE_TYPE::STDMAP;
        break;
    default:
        Debug::logmsg(LOG_ERR, "Not able to decide storage, exiting");
        exit(-1);
    }

    return;
}

// Append pending data to its cached content
void HttpCacheManager::addData( HttpResponse &response ,char *msg, size_t msg_size, std::string url) {
    auto c_object = getCacheObject(std::hash<std::string>()(url));
    if( c_object == nullptr ){
        Debug::logmsg(LOG_ERR, "Incoming data for a cache entry not stored yet");
        return;
    }
    if( response.c_object == nullptr )
        return;

    //create the path string
    size_t hashed_url = std::hash <std::string> () (url);
    std::string rel_path = service_name;
    rel_path.append("/");
    rel_path.append(to_string(hashed_url));

    storage_commons::STORAGE_STATUS err;
    //Check what storage to use
    switch (c_object->storage){
    case st::STORAGE_TYPE::STDMAP:
    case st::STORAGE_TYPE::RAMFS:
        err = ram_storage->appendData(rel_path, std::string(msg, msg_size));
        break;
    case st::STORAGE_TYPE::DISK:
        err = disk_storage->appendData(rel_path, std::string(msg, msg_size));
        break;
    default:
        return;
    }
    if ( err != storage_commons::STORAGE_STATUS::SUCCESS ){
        Debug::logmsg(LOG_WARNING, "There was an unexpected error result while appending data to the cache content %s", url.data());
    }
    //disable flag
    if ( response.chunked_status == http::CHUNKED_STATUS::CHUNKED_DISABLED && response.message_bytes_left == msg_size ){
        response.c_object->dirty = false;
    }
    else if ( response.chunked_status == http::CHUNKED_STATUS::CHUNKED_LAST_CHUNK ) {
        response.c_object->dirty = false;
        c_object->content_length = response.content_length;
    }
    return;
}

cache_commons::CacheObject * HttpCacheManager::canBeServedFromCache(HttpRequest &request) {
    cache_commons::CacheObject *c_object = getCacheObject(request);

    if( c_object == nullptr ){
        return nullptr;
    }
    if (c_object->dirty ){
        return nullptr;
    }
    if (request.c_opt.no_cache || (!request.cache_control && request.pragma)){
        return nullptr;
    }
    if (request.c_opt.only_if_cached){
        return c_object;
    }
    //TODO: isfresh applies to   Cobject, must be of Cobject
    bool serveable = c_object->isFresh();

    std::time_t now = timeHelper::gmtTimeNow();

    // if staled and must revalidate is included, we MUST revalidate the
    // response
    if (!serveable && c_object->revalidate){
        return nullptr;
    }
    // If max-age request directive is set, we must check if the response
    // complies
    if (request.c_opt.max_age >= 0) {
        if (!c_object->staled){
            if ((now - c_object->date) > request.c_opt.max_age){
                serveable = false;
            }
        }
    }
    // Check if complies with the request directive min-fresh
    if (request.c_opt.min_fresh >= 0) {
        if (!c_object->staled){
            if ((now - c_object->date) > request.c_opt.min_fresh){
                return nullptr;
            }
        }
    }
    // Check if complies with the request directive max-stale
    if (request.c_opt.max_stale >= 0) {
        if (c_object->staled && !c_object->revalidate){
            if ((now - c_object->date - c_object->max_age) < request.c_opt.max_stale){
                serveable = true;
            }
        }
    }

    return serveable ? c_object : nullptr;
}
int HttpCacheManager::getResponseFromCache(HttpRequest request,
                                          HttpResponse &cached_response, std::string &buffer ) {
  auto c_object = getCacheObject(request);
  c_object->updateFreshness();

  size_t parsed = 0;
  std::string rel_path = service_name ;
  rel_path.append("/");
  rel_path.append(to_string( std::hash<std::string>()(request.getUrl())));

  buffer = "";
  //Get the response from the right storage
  switch(c_object->storage){
  case st::STORAGE_TYPE::STDMAP:
  case st::STORAGE_TYPE::RAMFS:
      ram_storage->getFromStorage(rel_path, buffer);
      break;
  case st::STORAGE_TYPE::DISK:
      disk_storage->getFromStorage(rel_path, buffer );
      break;
  default:
      return -1;
  }


//  cached_response.buffer = static_cast<char *>(calloc(buff.size(),sizeof(char)));
//  memcpy(cached_response.buffer, buff.data(),buff.size());
  auto ret = cached_response.parseResponse(buffer, &parsed);
  cached_response.cached = true;

  for (size_t j = 0; j < cached_response.num_headers; j++) {
    if ( std::string(cached_response.headers[j].name).compare("date") == 0 )
    {
        cached_response.headers[j].header_off = true;
        cached_response.addHeader(http::HTTP_HEADER_NAME::DATE, timeHelper::strTime(c_object->date)->data() );
    }
    cached_response.headers[j].header_off = false;
  }

  if (ret == http_parser::PARSE_RESULT::FAILED) {
    Debug::logmsg(LOG_ERR, "The cached response failed to be parsed");
    return -1;
  } else if (ret == http_parser::PARSE_RESULT::SUCCESS) {
    // Add warning header
    std::vector<std::string> w_codes;
    std::vector<std::string> w_text;
    // Take the date for the warning
    std::string *w_date = timeHelper::strTimeNow();
    // Create warnings if needed
    if (c_object->staled) {
      w_codes.push_back(std::to_string(http::WARNING_CODE::RESPONSE_STALE));
      w_text.push_back(http::http_info::warning_code_values_strings.at(
          http::WARNING_CODE::RESPONSE_STALE));
    }
    // Defined by RFC7234
    if (c_object->heuristic && c_object->max_age >= 86400 && c_object->staled) {
      w_codes.push_back(
          std::to_string(http::WARNING_CODE::HEURISTIC_EXPIRATION));
      w_text.push_back(http::http_info::warning_code_values_strings.at(
          http::WARNING_CODE::HEURISTIC_EXPIRATION));
    }
    // Add warning headers if needed
    for (unsigned long i = 0; i < w_codes.size() && i < w_text.size(); i++) {
      cached_response.addHeader(http::HTTP_HEADER_NAME::WARNING,
                                w_codes.at(i) + " - " + "\"" + w_text.at(i) +
                                    "\" \"" + w_date->data() + "\"");
    }
    // Add Age header
    time_t now = timeHelper::getAge(c_object->date);
    cached_response.addHeader(
        http::HTTP_HEADER_NAME::AGE,
        std::to_string(
            now >= 0 ? now : 0)); // ensure that it is greater or equal than 0
  }

  return 0;
}

std::string HttpCacheManager::handleCacheTask(ctl::CtlTask &task)
{
    int err = 0;
    if (task.subject != ctl::CTL_SUBJECT::CACHE)
        return JSON_OP_RESULT::ERROR;
    switch (task.command)
    {
    case ctl::CTL_COMMAND::DELETE:{
        auto json_data = JsonParser::parse(task.data);
        if ( json_data == nullptr )
            return JSON_OP_RESULT::ERROR;
        //Error handling when trying to use the key
        try {
          json_data->at(JSON_KEYS::CACHE_CONTENT);
        }
        catch (const std::out_of_range& oor) {
          std::cerr << "Wrong key found, must be \"" << JSON_KEYS::CACHE_CONTENT << "\", caused by " << oor.what() << '\n';
          return JSON_OP_RESULT::ERROR;
        }
        auto url = dynamic_cast<JsonDataValue *>(json_data->at(JSON_KEYS::CACHE_CONTENT).get())->string_value;
        err = deleteEntry(std::hash<std::string>()(url));
        break;
    }
    default:
            Debug::logmsg(LOG_ERR, "Not a valid cache command");
            return JSON_OP_RESULT::ERROR;
    }
    if ( err != 0 ){
        return JSON_OP_RESULT::ERROR;
    }
    return JSON_OP_RESULT::OK;
}

void HttpCacheManager::recoverCache(string svc,st::STORAGE_TYPE st_type)
{
    //We have to read all headers and load it in memory
    std::string path;
    switch(st_type){
    case st::STORAGE_TYPE::RAMFS:
         path = ram_storage->mount_path;
         path.append("/");
         path.append(svc);
        break;
    case st::STORAGE_TYPE::DISK:
        path = disk_storage->mount_path;
        path.append("/");
        path.append(svc);
        break;
    default:
        break;
    }
    std::ifstream in_file;
    std::string in_line, file_name;
    std::string buffer;
    std::unique_ptr <cache_commons::CacheObject> c_object (new cache_commons::CacheObject);
    for(const auto & entry : std::filesystem::directory_iterator(path))
    {
        HttpResponse stored_response;
        //Iterate through all the files
        in_file.open(entry.path());
        file_name = std::filesystem::path(entry.path()).filename();
        while ( std::getline(in_file, in_line ))
        {
            buffer.append(in_line + "\n");
            //The \r line alone separate the HTTP header from body
            if ( in_line.compare("\r") == 0)
            {
                //finished reading, need to store the response obtained
                size_t bytes =0;

                stored_response.parseResponse(buffer,&bytes);
                validateCacheResponse(stored_response);
                addResponseEntry(stored_response, c_object.get());
                c_object->dirty = false;
                c_object->storage = st_type;
                //Increment the current size of the storage
                switch(st_type){
                    case st::STORAGE_TYPE::RAMFS:
                        ram_storage->current_size += c_object->content_length + stored_response.headers_length;
                        break;
                    case st::STORAGE_TYPE::DISK:
                        disk_storage->current_size += c_object->content_length + stored_response.headers_length;
                        break;
                    default:
                        Debug::logmsg(LOG_WARNING,"Wrong storage type");
                        break;
                }
                break;
            }
        }
        if (c_object != nullptr){
            c_object->dirty = false;
            cache[strtoul(file_name.data(),0,0)] = c_object.release();
        }
        in_file.close();
    }
}

void HttpCacheManager::validateCacheResponse(HttpResponse &response){

  for (auto i = 0; i != response.num_headers; i++) {
    // check header values length

    auto header = std::string_view(response.headers[i].name,
                                   response.headers[i].name_len);
    auto header_value = std::string_view(
        response.headers[i].value, response.headers[i].value_len);
    auto it = http::http_info::headers_names.find(header);
    if (it != http::http_info::headers_names.end()) {
      const auto header_name = it->second;
      switch (header_name) {
      case http::HTTP_HEADER_NAME::CONTENT_LENGTH: {
          response.content_length =
              static_cast<size_t>(std::atoi(response.headers[i].value));
          continue;
      }
      case http::HTTP_HEADER_NAME::CACHE_CONTROL: {
        std::vector<string> cache_directives;
        helper::splitString(std::string(header_value), cache_directives, ' ');
        response.cache_control = true;
        // Lets iterate over the directives array
        for (unsigned long l = 0; l < cache_directives.size(); l++) {
          // split using = to obtain the directive value, if supported
          string directive;
          string directive_value = "";

          std::vector<string> parsed_directive;
          helper::splitString(cache_directives[l], parsed_directive, '=');
          directive = parsed_directive[0];

          if (parsed_directive.size() == 2){
            directive_value = parsed_directive[1];
          }

          if (http::http_info::cache_control_values.count(directive) > 0) {
            switch (http::http_info::cache_control_values.at(directive)) {
            case http::CACHE_CONTROL::MAX_AGE:
              if (directive_value.size() != 0 && response.c_opt.max_age == -1)
                response.c_opt.max_age = stoi(directive_value);
              break;
            case http::CACHE_CONTROL::PUBLIC:
              response.c_opt.scope = cache_commons::CACHE_SCOPE::PUBLIC;
              break;
            case http::CACHE_CONTROL::PRIVATE:
              response.c_opt.scope = cache_commons::CACHE_SCOPE::PRIVATE;
              break;
            case http::CACHE_CONTROL::PROXY_REVALIDATE:
              response.c_opt.revalidate = true;
              break;
            case http::CACHE_CONTROL::S_MAXAGE:
              if (directive_value.size() != 0)
                response.c_opt.max_age = stoi(directive_value);
              break;
            case http::CACHE_CONTROL::NO_CACHE:
              response.c_opt.no_cache = true;
              response.c_opt.cacheable = false;
              break;
            case http::CACHE_CONTROL::NO_STORE:
              response.c_opt.cacheable = false;
              break;
            }
          }
        }
        break;
      }
      case http::HTTP_HEADER_NAME::PRAGMA: {
        if (header_value.compare("no-cache") == 0) {
          response.pragma = true;
        }
        break;
      }
      case http::HTTP_HEADER_NAME::ETAG:
        response.etag = std::string(header_value);
        break;
      case http::HTTP_HEADER_NAME::EXPIRES:
        response.expires = timeHelper::strToTime(std::string(header_value));
        break;
      case http::HTTP_HEADER_NAME::DATE:
        response.date = timeHelper::strToTime(std::string(header_value));
        break;
      case http::HTTP_HEADER_NAME::LAST_MODIFIED:
        response.last_mod = timeHelper::strToTime(std::string(header_value));
        break;
      default:continue;
      }

    }
  }
  return;
}
void HttpCacheManager::validateCacheRequest(HttpRequest &request){
    // Check for correct headers
    for (auto i = 0; i != request.num_headers; i++) {
        // check header values length
        auto header = std::string_view(request.headers[i].name,
                                       request.headers[i].name_len);
        auto header_value = std::string_view(
                    request.headers[i].value, request.headers[i].value_len);

        auto it = http::http_info::headers_names.find(header);
        if (it != http::http_info::headers_names.end()) {
            auto header_name = it->second;
            switch (header_name) {
            case http::HTTP_HEADER_NAME::TRANSFER_ENCODING:
                //TODO
                break;
            case http::HTTP_HEADER_NAME::CACHE_CONTROL: {
                std::vector<string> cache_directives;
                helper::splitString(std::string(header_value), cache_directives, ' ');
                request.cache_control = true;

                // Lets iterate over the directives array
                for (unsigned long l = 0; l < cache_directives.size(); l++) {
                    // split using = to obtain the directive value, if supported
                    if (cache_directives[l].back() == ',')
                        cache_directives[l] =
                                cache_directives[l].substr(0, cache_directives[l].length() - 1);
                    string directive;
                    string directive_value = "";

                    std::vector<string> parsed_directive;
                    helper::splitString(cache_directives[l], parsed_directive, '=');

                    directive = parsed_directive[0];

                    // If the size == 2 the directive is like directive=value
                    if (parsed_directive.size() == 2)
                        directive_value = parsed_directive[1];
                    // To separe directive from the token
                    if (http::http_info::cache_control_values.count(directive) > 0) {
                        switch (http::http_info::cache_control_values.at(directive)) {
                        case http::CACHE_CONTROL::MAX_AGE:
                            if (directive_value.size() != 0)
                                request.c_opt.max_age = stoi(directive_value);
                            break;
                        case http::CACHE_CONTROL::MAX_STALE:
                            if (directive_value.size() != 0)
                                request.c_opt.max_stale = stoi(directive_value);
                            break;
                        case http::CACHE_CONTROL::MIN_FRESH:
                            if (directive_value.size() != 0)
                                request.c_opt.min_fresh = stoi(directive_value);
                            break;
                        case http::CACHE_CONTROL::NO_CACHE:
                            request.c_opt.no_cache = true;
                            break;
                        case http::CACHE_CONTROL::NO_STORE:
                            request.c_opt.no_store = true;
                            break;
                        case http::CACHE_CONTROL::NO_TRANSFORM:
                            request.c_opt.transform = false;
                            break;
                        case http::CACHE_CONTROL::ONLY_IF_CACHED:
                            request.c_opt.only_if_cached = true;
                            break;
                        default:
                            Debug::logmsg(
                                        LOG_ERR,
                                        ("Malformed cache-control, found response directive " +
                                         directive + " in the request")
                                        .c_str());
                            break;
                        }
                    } else {
                        Debug::logmsg(LOG_ERR, ("Unrecognized directive " + directive +
                                                " in the request")
                                      .c_str());
                    }
                }
                break;
            }
            case http::HTTP_HEADER_NAME::AGE:
                break;
            case http::HTTP_HEADER_NAME::PRAGMA: {
                if (header_value.compare("no-cache") == 0) {
                    request.pragma = true;
                }
                break;
            }
            default: continue;
            }

        }
    }

    return;
}
int HttpCacheManager::deleteEntry(HttpRequest request){
    return deleteEntry(std::hash<std::string>()(request.getUrl()));
}

int HttpCacheManager::deleteEntry(size_t hashed_url){
    std::string path (service_name);
    path.append("/");
    path.append(to_string(hashed_url));
    auto c_object = getCacheObject(hashed_url);
    if(c_object == nullptr){
        Debug::logmsg(LOG_WARNING, "Trying to discard a non existing entry from the cache");
        return -1;
    }
    // Create the key and the file path

    storage_commons::STORAGE_STATUS err;

    switch(c_object->storage){
    case storage_commons::STORAGE_TYPE::STDMAP:
    case storage_commons::STORAGE_TYPE::RAMFS:
        err = ram_storage->deleteInStorage(path);
        break;
    case storage_commons::STORAGE_TYPE::DISK:
        err = disk_storage->deleteInStorage(path);
        break;
    default: return -1;
    }
    if ( err != storage_commons::STORAGE_STATUS::SUCCESS && err != storage_commons::STORAGE_STATUS::NOT_FOUND){
        Debug::logmsg(LOG_ERR, "Error trying to delete cache content from the storage");
        return -1;
    }
    if ( cache.erase(hashed_url) != 1 ){
       Debug::logmsg(LOG_WARNING, "Error deleting cache entry");
       return -1;
    }
    return 0;
}

void HttpCacheManager::doCacheMaintenance(){

//Iterate over all the content, check staled, check how long, discard if have to
    if ( !needCacheMaintenance() ){
        return;
    }
    last_maintenance = timeHelper::gmtTimeNow();
    for (auto iter = cache.begin(); iter != cache.end();){
        iter->second->updateFreshness();
        //If not staled continue with the loop
        if(!iter->second->staled){
            continue;
        }
        else
        {
            int expiration_to = CACHE_EXPIRATION;
            auto entry_age = timeHelper::gmtTimeNow() - iter->second->date;
            //Greater than 10 times the max age
            if ( entry_age > iter->second->max_age * expiration_to ){
                Debug::logmsg(LOG_REMOVE, "Removing old cache entry: %zu", iter->first);
                deleteEntry((iter++)->first);
                break;
            }
            else{
                iter++;
            }
        }
    }
}
#endif
