//
// Created by abdess on 4/5/18.
//

#include "http_stream.h"
#include "../util/Network.h"
#include "../util/common.h"
#include "../service/Service.h"

using namespace ssl;

HttpStream::HttpStream()
    : request(), response(), client_connection(), backend_connection(),
      timer_fd() {
#ifdef CACHE_ENABLED
    this->current_time = time_helper::gmtTimeNow();
    this->prev_time = std::chrono::steady_clock::now();
#endif
}

HttpStream::~HttpStream() {}

void HttpStream::logTransaction() {

    Service *service = static_cast<Service *>(this->request.getService());
    char ofs[32];
    std::string agent("");
    std::string referer("");
    std::string host("");
    std::string auth("");
    this->request.getHeaderValue(http::HTTP_HEADER_NAME::REFERER, referer);
    this->request.getHeaderValue(http::HTTP_HEADER_NAME::USER_AGENT, agent);
    this->request.getHeaderValue(http::HTTP_HEADER_NAME::HOST, host);
    this->request.getHeaderValue(http::HTTP_HEADER_NAME::AUTHORIZATION, auth);

    // std::chrono::steady_clock::time_point
    std::chrono::steady_clock::time_point time_now = std::chrono::steady_clock::now();
    std::chrono::duration<double> time_span = std::chrono::duration_cast<std::chrono::duration<double>>(time_now.time_since_epoch() - this->client_connection.time_start.time_since_epoch());
    struct tm *tim = std::localtime (&this->client_connection.date);
    std::strftime (ofs, sizeof (ofs), "%z", tim);

    //poundlogs, 192.168.100.241:8080 192.168.0.186 - - [30/Sep/2019:14:24:51 +0000] "GET / HTTP/1.1" 200 11383 "" "curl/7.64.0" (assur -> 192.168.100.253:80) 0.002 sec
    Debug::logmsg(LOG_INFO, "%s %s - %s [%d/%d/%d:%d:%d:%d %s] \"%s %s HTTP/%s\" %d %d \"%s\" \"%s\" (%s -> %s:%d) %.3f sec",
                  !host.empty() ? host.c_str(): "-",
                  this->client_connection.getPeerAddress().c_str(),
                  !auth.empty() ? auth.c_str() : "-",
                  tim->tm_mday,
                  tim->tm_mon+1,
                  tim->tm_year+1900,
                  tim->tm_hour,
                  tim->tm_min,
                  tim->tm_sec,
                  ofs,
                  this->request.getMethod().c_str(),
                  this->request.getUrl().c_str(),
                  this->request.getVersion().c_str(),
                  this->response.http_status_code,
                  this->response.content_length,
                  !referer.empty() ? referer.c_str() : "",
                  !agent.empty() ? agent.c_str() : "",
                  service->name.c_str() ? service->name.c_str() : "-",
                  this->backend_connection.getPeerAddress().c_str(),
                  this->backend_connection.getPeerPort(),
                  time_span.count() / 1.0);
}
