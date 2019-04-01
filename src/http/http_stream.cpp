//
// Created by abdess on 4/5/18.
//

#include "http_stream.h"
#include "../util/Network.h"
#include "../util/common.h"

HttpStream::HttpStream()
    : request(), response(), client_connection(), backend_connection(),
      timer_fd(), chunked_status(http::CHUNKED_STATUS::CHUNKED_DISABLED) {}
void HttpStream::replyError(HttpStatus::Code code, const char *code_string,
                            const char *string) {
  char caddr[50];
  if (UNLIKELY(Network::getPeerAddress(client_connection.getFileDescriptor(), caddr, 50) == nullptr)) {
    Debug::LogInfo("Error getting peer address", LOG_DEBUG);
  } else {
    Debug::logmsg(LOG_WARNING, "(%lx) e%d %s %s from %s",
                  std::this_thread::get_id(),
                  static_cast<int>(HttpStatus::Code::NotImplemented),
                  code_string,
                  client_connection.buffer, caddr);
  }
  auto response_ = HttpStatus::getHttpResponse(code, code_string, string);
  client_connection.write(response_.c_str(), response_.length());
}

HttpStream::~HttpStream() {}

void HttpStream::replyRedirect(BackendConfig &backend_config) {
  std::string new_url = backend_config.url;
  new_url += this->request.getUrl();
  auto response_ = HttpStatus::getRedirectResponse(
      (HttpStatus::Code)backend_config.be_type, new_url);
  client_connection.write(response_.c_str(), response_.length());
}
void HttpStream::replyRedirect(int code, const char *url) {
  auto response_ = HttpStatus::getRedirectResponse(
      (HttpStatus::Code)code, url);
  client_connection.write(response_.c_str(), response_.length());
}
