#pragma once
#include "../http/http_stream.h"
#include "../handlers/http_manager.h"
#include "../stream/StreamManager.h"
class CacheManager {
public:
    static void handleResponse(HttpStream * stream, Service *service, ListenerConfig &listener_config_);
    static int handleRequest(HttpStream * stream, Service *service, ListenerConfig &listener_config_);
};
