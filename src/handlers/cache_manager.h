#pragma once
#include "../handlers/http_manager.h"
#include "../http/http_stream.h"
#include "../stream/stream_manager.h"

class CacheManager
{
      public:
    /**
     * @brief handleResponse handle all cache logic checks when a request is received before calling the HttpCache
     * @param stream representation pointer of the HttpStream
     * @param service the service for the request
     * @param listener_config_
     */
	static void handleResponse(HttpStream * stream, Service * service);
    /**
     * @brief handleRequest handle all cache logic checks when a response is received before calling the HttpCache
     * @param stream representation pointer of the HttpStream
     * @param service the service for the request
     * @param listener_config_
     */
	static int handleRequest(HttpStream * stream, Service * service,
				 ListenerConfig & listener_config_);
    /**
     * @brief validateCacheResponse It takes a HTTP response and validate Cache related headers to store their values
     * @param response it is the HttpResponse object reference with the parsed response to handle.
     */
	static void validateCacheResponse(HttpResponse & response);
    /**
   * @brief validateCacheRequest It takes a HTTP request and validate Cache related headers to store their values
   * @param request it is the HttpRequest object reference with the parsed request to handle.
   */
	static void validateCacheRequest(HttpRequest & request);
    /**
    * @brief validateCacheRequest It takes a HTTP request and validate Cache related headers to store their values
    * @param request it is the HttpRequest object reference with the parsed request to handle.
    */
	static void handleStreamClose(HttpStream * stream);
};
