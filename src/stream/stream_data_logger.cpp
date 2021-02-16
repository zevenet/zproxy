#include "stream_data_logger.h"
#include "../../zcutils/zcutils.h"

//~ void StreamDataLogger::setLogData(HttpStream* stream, ListenerConfig& listener_config) {
  //~ Logger::log_info[std::this_thread::get_id()].farm_name = std::string_view(listener_config.name);
  //~ if (stream != nullptr) {
    //~ auto service = stream->request.getService();
    //~ if (service != nullptr) {
      //~ Logger::log_info[std::this_thread::get_id()].service_name =
          //~ std::string_view(static_cast<Service*>(service)->name);
      //~ auto bck = stream->backend_connection.getBackend();
      //~ if (bck != nullptr)
        //~ Logger::log_info[std::this_thread::get_id()].backend_id = stream->backend_connection.getBackend()->backend_id;
    //~ }
  //~ } else {
    //~ Logger::log_info[std::this_thread::get_id()].service_name = std::string_view();
    //~ Logger::log_info[std::this_thread::get_id()].backend_id = -1;
  //~ }
//~ }

void StreamDataLogger::logTransaction(HttpStream& stream) {
  if (zcutils_log_level != LOG_INFO) return;
  std::string agent;
  std::string referer;
  std::string host;
  stream.request.getHeaderValue(http::HTTP_HEADER_NAME::REFERER, referer);
  stream.request.getHeaderValue(http::HTTP_HEADER_NAME::USER_AGENT, agent);
  stream.request.getHeaderValue(http::HTTP_HEADER_NAME::HOST, host);
  auto latency = Time::getElapsed(stream.backend_connection.time_start);
  // 192.168.100.241:8080 192.168.0.186 - - "GET / HTTP/1.1" 200 11383 ""
  // "curl/7.64.0"
  static const std::string str_fmt =
      "%s %s - \"%s \" \"%s\" "
      "%d \"%s\" "
      "\"%s\" %lf";
  zcutils_log_print(LOG_INFO, str_fmt.c_str(), !host.empty() ? host.c_str() : "-",
                 stream.client_connection.getPeerAddress().c_str(),
                 stream.request.http_message_str.data(),
                 stream.response.http_message_str.data(),
                 stream.response.content_length, referer.c_str(),
                 agent.c_str(),latency);
}

//~ void StreamDataLogger::resetLogData() {
  //~ Logger::log_info[std::this_thread::get_id()].farm_name = std::string_view();
  //~ Logger::log_info[std::this_thread::get_id()].service_name = std::string_view();
  //~ Logger::log_info[std::this_thread::get_id()].backend_id = -1;
//~ }

//~ StreamDataLogger::~StreamDataLogger() { resetLogData(); }
