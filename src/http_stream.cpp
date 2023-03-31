/*
 * Copyright (C) 2023  Zevenet S.L. <support@zevenet.com>
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as
 * published by the Free Software Foundation, either version 3 of the
 * License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#include "http_stream.h"
#include "state.h"

static int id = 0;

HttpStream::HttpStream(zproxy_proxy_cfg *listener, const sockaddr_in *cl,
		struct zproxy_http_state *http_state):
	stats_state(STREAM_STATE::UNDEF),
	request(), response(), http_state(http_state),
	waf(listener->cfg->runtime.waf_api, listener->runtime.waf_rules)
{
	stream_id = ++id;
	state = HTTP_STATE::REQ_HEADER_RCV;
	listener_config = listener;
	client_addr = inet_ntoa((in_addr)cl->sin_addr);
	client_port = ntohs(cl->sin_port);
}

HttpStream::~HttpStream()
{
	clearStats();
}

bool HttpStream::expectNewRequest()
{
	if (request.connection_close_pending || response.connection_close_pending)
		return false;

	if ((request.http_version == http::HTTP_VERSION::HTTP_1_0 || request.http_version == http::HTTP_VERSION::HTTP_1_1) && !request.connection_keep_alive)
		return false;

	if ((request.http_version == http::HTTP_VERSION::HTTP_1_0 || request.http_version == http::HTTP_VERSION::HTTP_1_1) && !response.connection_keep_alive)
		return false;

	return true;
}

std::string HttpStream::logTag(const int loglevel, const char *tag) const
{
	if(loglevel > zcu_log_get_level())
		return std::string("");
	int total_b;
	char ret[MAXBUF];

	total_b = sprintf(ret, "[st:%d]", this->stream_id);

	if (service_config == nullptr) {
		total_b += sprintf(ret + total_b, "[svc:-][bk:-]");
	} else {
		if (backend_config == nullptr)
			total_b += sprintf(ret + total_b, "[svc:%s][bk:-]",
					   service_config->name);
		else
			total_b += sprintf(
				ret + total_b, "[svc:%s][bk:%s:%hu]",
				service_config->name,
				backend_config->address,
				htons(backend_config->runtime.addr.sin_port));
	}

	if (tag == nullptr || strcmp(tag, "waf")) {
		if (client_addr == "") {
			total_b += sprintf(ret + total_b, "[cl:-]");
		} else
			total_b +=
				sprintf(ret + total_b, "[cl:%s]",
					client_addr.c_str());
		if (tag != nullptr)
			total_b += sprintf(ret + total_b, "(%s)", tag);
	}

	ret[total_b++] = '\0';

	std::string ret_st(ret);
	return ret_st;
}

void HttpStream::setState(HTTP_STATE new_state)
{
	zcu_log_print_th(LOG_DEBUG,
			  "Stream %d changing status: %s -> %s",
			  stream_id, getStateString(state),
			  getStateString(new_state));
	state = new_state;
	state_tracer.push_back(state);
};

void HttpStream::clearStats()
{
	switch(stats_state)
	{
		case NEW_CONN:
			zproxy_stats_listener_dec_conn_established(http_state);
			zproxy_stats_listener_dec_conn_pending(http_state);
			break;
		case BCK_CONN:
			zproxy_stats_listener_dec_conn_established(http_state);
			zproxy_stats_backend_dec_conn_pending(http_state, backend_config);
			break;
		case ESTABLISHED:
			zproxy_stats_listener_dec_conn_established(http_state);
			zproxy_stats_backend_dec_conn_established(http_state, backend_config);
			break;
		case UNDEF:
			streamLogDebug(this, "The stream stats are not defined");
			break;
		default:
			streamLogMessage(this, "The stream stats are not defined: %d", stats_state);
	}
	stats_state = UNDEF;
}

int HttpStream::setStats(const STREAM_STATE new_state)
{
	int ret = 1;

	switch (new_state)
	{
		case NEW_CONN:
			zproxy_stats_listener_inc_conn_established(http_state);
			zproxy_stats_listener_inc_conn_pending(http_state);
			break;
		case BCK_CONN:
			zproxy_stats_listener_inc_conn_established(http_state);
			zproxy_stats_backend_inc_conn_pending(http_state, backend_config);
			break;
		case ESTABLISHED:
			zproxy_stats_listener_inc_conn_established(http_state);
			zproxy_stats_backend_inc_conn_established(http_state, backend_config);
			break;
		default:
			ret = -1;
	}

	if (ret > 0)
	{
		stats_state = new_state;
	}
	return ret;

}

int HttpStream::updateStats(const STREAM_STATE new_state)
{
	int ret = 1;
	streamLogDebug(this, "Changing stats: %d -> %d", stats_state, new_state);

	if (new_state == stats_state)
		return ret;

	clearStats();

	ret = setStats(new_state);
	if(ret < 0)
	{
		streamLogMessage(this, "Error setting stats for state: %d -> %d",
				stats_state, new_state);
	}

	return ret;
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

	auto tag = logTag(LOG_INFO, "established");
	zcu_log_print_th(LOG_INFO,
			  "%s host:%s - \"%.*s\" \"%s\" %lu \"%s\" \"%s\"",
			  tag.data(), !host.empty() ? host.c_str() : "-",
			  // -2 is to remove the CLRF characters
			  this->request.http_message_str.length() - 2,
			  this->request.http_message_str.data(),
			  this->response.http_message_str.data(),
			  this->response.content_length, referer.c_str(),
			  agent.c_str());
}
