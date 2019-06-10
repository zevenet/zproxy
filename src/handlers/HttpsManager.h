#pragma once

#include "../http/http_stream.h"
#include "../ssl/ssl_common.h"
#include "../ssl/SSLConnectionManager.h"
#include "../service/Service.h"

void httpsHeaders(HttpStream *stream, ssl::SSLConnectionManager *ssl_manager,
                  ListenerConfig listener_config_);

void setStrictTransportSecurity(Service *service, HttpStream *stream);