//
// Created by abdess on 4/5/18.
//

#include "http_stream.h"
#include "../util/Network.h"
#include "../util/common.h"
#include "../service/Service.h"

using namespace ssl;

HttpStream::HttpStream(std::string f_name)
    : request(), response(), client_connection(), backend_connection(),
      timer_fd() {
#ifdef CACHE_ENABLED
    this->current_time = time_helper::gmtTimeNow();
    this->prev_time = std::chrono::steady_clock::now();
#endif
    this->l_name=f_name;
}

HttpStream::~HttpStream() {}

void HttpStream::logTransaction() {

    Service *service = static_cast<Service *>(this->request.getService());
    std::string agent("");
    std::string referer("");
    std::string host("");
    std::string auth("");
    this->request.getHeaderValue(http::HTTP_HEADER_NAME::REFERER, referer);
    this->request.getHeaderValue(http::HTTP_HEADER_NAME::USER_AGENT, agent);
    this->request.getHeaderValue(http::HTTP_HEADER_NAME::HOST, host);
    this->request.getHeaderValue(http::HTTP_HEADER_NAME::AUTHORIZATION, auth);

    // 192.168.100.241:8080 192.168.0.186 - - "GET / HTTP/1.1" 200 11383 "" "curl/7.64.0"
    Debug::logmsg(LOG_INFO, "%s %s - %s \"%s %s HTTP/%s\" response_code/%d response_size/%d \"%s\" \"%s\"",
                  !host.empty() ? host.c_str(): "-",
                  this->client_connection.getPeerAddress().c_str(),
                  !auth.empty() ? auth.c_str() : "-",
                  this->request.getMethod().c_str(),
                  this->request.getUrl().c_str(),
                  this->request.getVersion().c_str(),
                  this->response.http_status_code,
                  this->response.content_length,
                  !referer.empty() ? referer.c_str() : "",
                  !agent.empty() ? agent.c_str() : ""
                  );
}
