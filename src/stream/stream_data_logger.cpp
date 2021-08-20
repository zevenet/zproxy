#include "stream_data_logger.h"
#include "../../zcutils/zcutils.h"

void StreamDataLogger::logTransaction(HttpStream &stream)
{
	if (zcu_log_level < LOG_INFO)
		return;
	std::string agent;
	std::string referer;
	std::string host;
	auto service = static_cast<Service *>(stream.request.getService());
	stream.request.getHeaderValue(http::HTTP_HEADER_NAME::REFERER, referer);
	stream.request.getHeaderValue(http::HTTP_HEADER_NAME::USER_AGENT,
				      agent);
	stream.request.getHeaderValue(http::HTTP_HEADER_NAME::HOST, host);
	auto latency = Time::getElapsed(stream.backend_connection.time_start);
	// 192.168.100.241:8080 192.168.0.186 - - "GET / HTTP/1.1" 200 11383 ""
	// "curl/7.64.0"
	static const std::string str_fmt =
		"[completed][%lx][%lu][%s][%s][%s:%d] host:%s client:%s - \"%.*s\" \"%s\" "
		"%d \"%s\" "
		"\"%s\" %lf";
	zcu_log_print(LOG_INFO, str_fmt.c_str(), pthread_self(),
		      stream.stream_id,
		      stream.service_manager->listener_config_->name.data(),
		      service->name.c_str(),
		      stream.backend_connection.getBackend()->address.c_str(),
		      stream.backend_connection.getBackend()->port,
		      !host.empty() ? host.c_str() : "-",
		      stream.client_connection.getPeerAddress().c_str(),
		      stream.request.http_message_str.length() - 2,
		      stream.request.http_message_str.data(),
		      stream.response.http_message_str.data(),
		      /* -2 is to remove the CLRF characters */
		      stream.response.content_length, referer.c_str(),
		      agent.c_str(), latency);
}
