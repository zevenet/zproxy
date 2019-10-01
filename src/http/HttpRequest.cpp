//
// Created by abdess on 4/6/19.
//
#include "HttpRequest.h"

void HttpRequest::setRequestMethod() {
    auto sv = std::string_view(method, method_len);
    //    auto sv = std::string(method, method_len);
    auto it = http::http_info::http_verbs.find(sv);
    if (it != http::http_info::http_verbs.end())
        request_method = it->second;
}

http::REQUEST_METHOD HttpRequest::getRequestMethod() {
    setRequestMethod();
    return request_method;
}

void HttpRequest::printRequestMethod() {
    Debug::logmsg(
                LOG_DEBUG, "Request method: %s",
                http::http_info::http_verb_strings.at(request_method).c_str());
}

std::string HttpRequest::getMethod() {
    return method != nullptr ? std::string(method, method_len) : std::string();
}

std::string_view HttpRequest::getRequestLine() {
    return std::string_view(http_message,
                            http_message_length);
}

std::string HttpRequest::getUrl() {
    return path != nullptr ? std::string(path, path_length) : std::string();
}

std::string HttpRequest::getVersion() {
    switch (http_version) {
    case http::HTTP_VERSION::HTTP_1_0:
        return std::string("1.0");

    case http::HTTP_VERSION::HTTP_1_1:
        return std::string("1.1");

    case http::HTTP_VERSION::HTTP_2_0:
        return std::string("2.0");

    }
    return std::string("");
}

void HttpRequest::setService(void *service) {
    this->request_service = service;
}

void *HttpRequest::getService() const {
    return request_service;
}
#ifdef CACHE_ENABLED
bool HttpResponse::isCached() { return this->cached; }
#endif
