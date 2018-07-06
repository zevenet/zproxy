//
// Created by abdess on 4/5/18.
//

#include "http_stream.h"

Connection *HttpStream::getConnection(int fd) {
  return fd == client_connection.getFileDescriptor() ? &client_connection
                                                     : &backend_connection;
}
HttpStream::HttpStream()
    : request(), response(),
      client_connection(),
      backend_connection() {

}
void HttpStream::replyError(HttpStatus::Code code, const char *code_string, const char *string) {
  auto response_ = HttpStatus::getErrorResponse(code, code_string, string);
  client_connection.write(response_.c_str(), response_.length());
}

HttpStream::~HttpStream() {
#if PRINT_READ_STADISTICS
  printReadStadistics(backend_stadistics, "Backend");
  printReadStadistics(client_stadistics, "Client");
#endif
}

void HttpStream::printReadStadistics(ConnectionStadistic_t &stadistic, std::string tag) {
  Debug::logmsg(LOG_DEBUG,
                "%s\nThread Stats   Avg      Min     Max   +/- Stdev\n"
                "    Latency    %d s     %d s      %d s         --%\n", tag.c_str(),
                stadistic.avr_read_time / CLOCKS_PER_SEC,
                stadistic.min_read_time / CLOCKS_PER_SEC,
                stadistic.max_read_time / CLOCKS_PER_SEC);
}
void HttpStream::replyRedirect(BackendConfig &backend_config) {
  auto response_ = HttpStatus::getRedirectResponse((HttpStatus::Code) backend_config.be_type, backend_config.url);
  client_connection.write(response_.c_str(), response_.length());
}
