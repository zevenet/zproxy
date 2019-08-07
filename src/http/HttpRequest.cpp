//
// Created by abdess on 4/6/19.
//
#include "HttpRequest.h"

void HttpRequest::setService(void *service) {
  this->request_service = service;
}

void *HttpRequest::getService() const {
  return request_service;
}
#if CACHE_ENABLED
bool HttpResponse::isCached() { return this->cached; }
#endif
