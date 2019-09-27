//
// Created by abdess on 4/5/18.
//

#include "http_stream.h"
#include "../util/Network.h"
#include "../util/common.h"

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


