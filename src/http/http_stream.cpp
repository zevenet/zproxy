/*
 *    Zevenet zproxy Load Balancer Software License
 *    This file is part of the Zevenet zproxy Load Balancer software package.
 *
 *    Copyright (C) 2019-today ZEVENET SL, Sevilla (Spain)
 *
 *    This program is free software: you can redistribute it and/or modify
 *    it under the terms of the GNU Affero General Public License as
 *    published by the Free Software Foundation, either version 3 of the
 *    License, or any later version.
 *
 *    This program is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *    GNU Affero General Public License for more details.
 *
 *    You should have received a copy of the GNU Affero General Public License
 *    along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 */

#include "http_stream.h"
#include "../service/service.h"
#include "../util/common.h"

HttpStream::HttpStream()
	: client_connection(), backend_connection(),
#if USE_TIMER_FD_TIMEOUT
	  timer_fd(),
#endif
	  request(), response(), status(0x0), options(0x0)
{
	static std::atomic<uint32_t> stream_id_counter;
	this->stream_id = stream_id_counter++;
#ifdef CACHE_ENABLED
	this->current_time = time_helper::gmtTimeNow();
	this->prev_time = std::chrono::steady_clock::now();
#endif
}

HttpStream::~HttpStream()
{
#if WAF_ENABLED
	if (modsec_transaction != nullptr) {
		// process the logging phase if there is something pending
		modsec_transaction->processLogging();
		modsecurity::intervention::free(&modsec_transaction->m_it);
	}
	delete this->modsec_transaction;
#endif
	if (tracer_fh != nullptr)
		fclose(tracer_fh);
}

void HttpStream::debugBufferData(const std::string &function, int line,
				 HttpStream *stream, const char *debug_str,
				 const char *data)
{
#if DEBUG_ZCU_LOG == 0
	return;
#endif

	if (stream == nullptr)
		return;
	zcu_log_print(
		LOG_DEBUG,
		"%s():%d: [%lu][%s][%.*s] cl_ip:%s cl_buff:%lu cl_off:%lu CL:%lu R:%d "
		"HS:%s CHR:%d CH:%s TP:%s RP:%s "
		"| bck_buff:%lu bck_off:%lu CL:%lu R:%d "
		"HS:%s CHR:%d CH:%s TP:%s RP:%s - %s",
		function.c_str(), line, stream->stream_id, debug_str,
		stream->request.path.length(), stream->request.path.data(),
		stream->client_connection.getPeerAddress().c_str(),
		stream->client_connection.buffer_size,
		stream->client_connection.buffer_offset,
		stream->request.content_length,
		stream->request.message_bytes_left,
		stream->request.getHeaderSent() ? "T" : "F",
		stream->request.chunk_size_left,
		stream->request.chunked_status !=
				http::CHUNKED_STATUS::CHUNKED_DISABLED ?
			"T" :
			      "F",
		stream->hasStatus(STREAM_STATUS::REQUEST_PENDING) ? "T" : "F",
		stream->hasStatus(STREAM_STATUS::CL_READ_PENDING) ? "T" : "F",
		stream->backend_connection.buffer_size,
		stream->backend_connection.buffer_offset,
		stream->response.content_length,
		stream->response.message_bytes_left,
		stream->response.getHeaderSent() ? "T" : "F",
		stream->response.chunk_size_left,
		stream->response.chunked_status !=
				http::CHUNKED_STATUS::CHUNKED_DISABLED ?
			"T" :
			      "F",
		stream->hasStatus(STREAM_STATUS::RESPONSE_PENDING) ? "T" : "F",
		stream->hasStatus(STREAM_STATUS::BCK_READ_PENDING) ? "T" : "F",
		data);
}

std::string HttpStream::logTag(const char *tag)
{
	int total_b;
	char ret[MAXBUF];

	total_b = sprintf(ret, "[st:%d]", this->stream_id);

	auto service = static_cast<Service *>(this->request.getService());
	if (service == nullptr) {
		total_b += sprintf(ret + total_b, "[svc:-][bk:-]");
	} else {
		if (this->backend_connection.getBackend() == nullptr)
			total_b += sprintf(ret + total_b, "[svc:%s][bk:-]",
					   service->name.c_str());
		else
			total_b += sprintf(
				ret + total_b, "[svc:%s][bk:%s:%d]",
				service->name.c_str(),
				this->backend_connection.getBackend()
					->address.c_str(),
				this->backend_connection.getBackend()->port);
	}

	if (tag == nullptr || strcmp(tag, "waf")) {
		if (this->client_connection.getPeerAddress() == "") {
			total_b += sprintf(ret + total_b, "[cl:-]");
		} else
			total_b +=
				sprintf(ret + total_b, "[cl:%s]",
					this->client_connection.getPeerAddress()
						.c_str());
		if (tag != nullptr)
			total_b += sprintf(ret + total_b, "(%s)", tag);
	}

	ret[total_b++] = '\0';

	std::string ret_st(ret);
	return ret_st;
}

void HttpStream::logSuccess()
{
	if (zcu_log_level < LOG_INFO)
		return;
	std::string agent;
	std::string referer;
	std::string host;
	this->request.getHeaderValue(http::HTTP_HEADER_NAME::REFERER, referer);
	this->request.getHeaderValue(http::HTTP_HEADER_NAME::USER_AGENT, agent);
	this->request.getHeaderValue(http::HTTP_HEADER_NAME::HOST, host);
	auto latency = Time::getElapsed(this->backend_connection.time_start);
	// 192.168.100.241:8080 192.168.0.186 - - "GET / HTTP/1.1" 200 11383 ""
	// "curl/7.64.0"

	auto tag = logTag("established");

	zcu_log_print(LOG_INFO,
		      "%s host:%s - \"%.*s\" \"%s\" %lu \"%s\" \"%s\" %lf",
		      tag.data(), !host.empty() ? host.c_str() : "-",
		      /* -2 is to remove the CLRF characters */
		      this->request.http_message_str.length() - 2,
		      this->request.http_message_str.data(),
		      this->response.http_message_str.data(),
		      this->response.content_length, referer.c_str(),
		      agent.c_str(), latency);
}

void HttpStream::initTracer(std::string dir, int id, std::string client_addr)
{
	std::string path = dir;
	path.append("/st_");
	path.append(std::to_string(id));
	path.append("-");
	path.append(client_addr);

	tracer_fh = fopen(path.data(), "w");
	if (tracer_fh == nullptr)
		zcu_log_print(LOG_WARNING,
			      "Tracer for %d stream could not be opened", id);
}

bool HttpStream::setStats(STREAM_STATS new_state)
{
	int err = 0;

	switch (new_state) {
	case NEW_CONN:
		service_manager->conns_stats.increaseEstablishedConn();
		service_manager->conns_stats.increasePendingConn();
		break;
	case BCK_CONN:
		service_manager->conns_stats.increaseEstablishedConn();
		backend_connection.getBackend()->increaseConnTimeoutAlive();
		break;
	case ESTABLISHED:
		service_manager->conns_stats.increaseEstablishedConn();
		backend_connection.getBackend()->increaseEstablishedConn();
		break;
	default:
		err = 1;
	}

	if (!err) {
		stats_state = new_state;
	}
	return err;
}

void HttpStream::clearStats()
{
	streamLogDebug(this, "Cleaning stats: %d", stats_state);
	switch (stats_state) {
	case NEW_CONN:
		service_manager->conns_stats.decreaseEstablishedConn();
		service_manager->conns_stats.decreasePendingConn();
		break;
	case BCK_CONN:
		service_manager->conns_stats.decreaseEstablishedConn();
		backend_connection.getBackend()->decreaseConnTimeoutAlive();
		break;
	case ESTABLISHED:
		service_manager->conns_stats.decreaseEstablishedConn();
		backend_connection.getBackend()->decreaseEstablishedConn();
		break;
	case UNDEF:
		streamLogDebug(this, "The stream stats are not defined");
		break;
	default:
		streamLogMessage(this, "The stream stats are not defined: %d",
				 stats_state);
	}
	stats_state = UNDEF;
}

bool HttpStream::updateStats(STREAM_STATS new_state)
{
	int err = 0;
	streamLogDebug(this, "Changing stats: %d -> %d", stats_state,
		       new_state);

	if (new_state == stats_state)
		return err;

	clearStats();

	err = setStats(new_state);
	if (err)
		streamLogMessage(this,
				 "Error setting stats for state: %d -> %d",
				 stats_state, new_state);

	return err;
}
