//
// Created by developer on 24/9/19.
//

#include "CacheManager.h"
#if CACHE_ENABLED
void CacheManager::handleResponse(HttpStream *stream, Service *service, ListenerConfig &listener_config_)
{
    if ( !stream->response.hasPendingData()){
        service->validateCacheResponse(stream->response);
        regex_t *pattern = service->getCachePattern();
        regmatch_t matches[2];
        if (pattern != nullptr) {
            if (regexec(pattern, stream->request.getUrl().data(), 1, matches, 0) == 0){
                if (stream->request.c_opt.no_store == false){
                    service->handleResponse(stream->response, stream->request);
                }
                else{
                    service->stats.cache_not_stored++;
                }
            }
        }
    }
    else{
        if (service->cache_enabled && service->getCacheObject(stream->request) != nullptr &&
            !stream->request.c_opt.no_store && stream->response.c_opt.cacheable) {
          service->addData(stream->response, std::string_view (stream->backend_connection.buffer,
                  stream->backend_connection.buffer_size), stream->request.getUrl());
        }
    }
}

int CacheManager::handleRequest(HttpStream * stream, Service *service, ListenerConfig &listener_config_ ) {
    std::chrono::steady_clock::time_point current_time = std::chrono::steady_clock::now();
    std::chrono::duration<long> time_span = std::chrono::duration_cast<std::chrono::duration<long>>(current_time - stream->prev_time);
    stream->prev_time = current_time;
    stream->current_time += time_span.count();
    service->t_stamp = stream->current_time;
    service->validateCacheRequest(stream->request);
    if (service->canBeServedFromCache(stream->request) != nullptr) {
        DEBUG_COUNTER_HIT(cache_stats__::cache_match);
        stream->response.reset_parser();
        if ( service->getResponseFromCache(stream->request, stream->response, stream->backend_connection.str_buffer) == 0){
            http_manager::validateResponse(*stream, listener_config_);

            if (http::http_info::http_verbs.at(std::string(
                    stream->request.method, stream->request.method_len)) ==
                http::REQUEST_METHOD::HEAD) {
                // If HTTP verb is HEAD, just send headers
                stream->response.buffer_size =
                        stream->response.buffer_size - stream->response.message_length;
                stream->response.message = nullptr;
                stream->response.message_length = 0;
                stream->response.message_bytes_left = 0;
            }
            stream->client_connection.buffer_size = 0;
            stream->request.setHeaderSent(false);
            stream->backend_connection.buffer_size = stream->response.buffer_size;
            stream->client_connection.enableWriteEvent();
            //Return 0, we are using cache
            return 0;
        }
    }
    if (stream->request.c_opt.only_if_cached ) {
        // If the directive only-if-cached is in the request and the content
        // is not cached, reply an error 504 as stated in the rfc7234
        return -1;
    }
    DEBUG_COUNTER_HIT(cache_stats__::cache_miss);
    service->stats.cache_miss++;
    stream->response.reset_parser();
    stream->response.cached = false;
    stream->response.setHeaderSent(false);
    stream->backend_connection.buffer_size = 0;
    //Return 1, we can't serve from cache
    return 1;
}
#endif