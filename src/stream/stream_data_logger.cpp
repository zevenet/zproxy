#include "stream_data_logger.h"
#include "../../zcutils/zcutils.h"

std::string StreamDataLogger::logTag(HttpStream *stream, const char *tag)
{
	int total_b, size = MAXBUF;
	char ret[MAXBUF];
	char caddr[200];

	total_b =
		sprintf(ret, "[th:%lx][st:%d][f:%s]", pthread_self(),
			stream->stream_id,
			stream->service_manager->listener_config_->name.data());

	auto service = static_cast<Service *>(stream->request.getService());
	if (service == nullptr) {
		total_b += sprintf(ret + total_b, "[svc:-][bk:-]");
	} else {
		if (stream->backend_connection.getBackend() == nullptr)
			total_b += sprintf(ret + total_b, "[svc:%s][bk:-]",
					   service->name.c_str());
		else
			total_b += sprintf(
				ret + total_b, "[svc:%s][bk:%s:%d]",
				service->name.c_str(),
				stream->backend_connection.getBackend()
					->address.c_str(),
				stream->backend_connection.getBackend()->port);
	}

	if (stream->client_connection.getPeerAddress() == "") {
		total_b += sprintf(ret + total_b, "[cl:-]");
	} else
		total_b += sprintf(
			ret + total_b, "[cl:%s]",
			stream->client_connection.getPeerAddress().c_str());

	if (tag != nullptr)
		total_b += sprintf(ret + total_b, "(%s)", tag);

	ret[total_b++] = '\0';

	std::string ret_st(ret);
	return ret_st;
}

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

	static const std::string str_fmt = "%s host:%s - \"%.*s\" \"%s\" "
					   "%lu \"%s\" "
					   "\"%s\" %lf";
	auto tag = logTag(&stream, "completed");

	zcu_log_print(LOG_INFO, str_fmt.c_str(), tag.data(),
		      !host.empty() ? host.c_str() : "-",
		      /* -2 is to remove the CLRF characters */
		      stream.request.http_message_str.length() - 2,
		      stream.request.http_message_str.data(),
		      stream.response.http_message_str.data(),
		      stream.response.content_length, referer.c_str(),
		      agent.c_str(), latency);
}
