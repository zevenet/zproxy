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

#include <regex>

#include "zcu_network.h"
#include "zcu_common.h"
#include "config.h"
#include "http_log.h"
#include "http_protocol.h"
#include "http_manager.h"
#include "http_stream.h"
#include "macro.h"
#include "session.h"

/*
 * It replaces a chain in the original string.
 *    Returns :  n, offset where the replacement finished
 *               0,  if it didn't do anything
*/
static int str_replace_regexp(char *buf, const char *ori_str, int ori_len,
			   regex_t *match, char *replace_str)
{
	//memset(buf.get(), 0, ZCU_DEF_BUFFER_SIZE);
	regmatch_t umtch[10];
	char *chptr, *enptr, *srcptr;
	int offset = -1;
	umtch[0].rm_so = 0;
	umtch[0].rm_eo = ori_len;
	if (regexec(match, ori_str, 10, umtch, REG_STARTEND))
		return -1;

	zcu_log_print_th(LOG_DEBUG, "String matches %.*s", ori_len, ori_str);

	memcpy(buf, ori_str, umtch[0].rm_so);

	chptr = buf + umtch[0].rm_so;
	enptr = buf + ZCU_DEF_BUFFER_SIZE - 1;
	*enptr = '\0';
	srcptr = replace_str;
	for (; *srcptr && chptr < enptr - 1;) {
		if (srcptr[0] == '$' && srcptr[1] == '$') {
			*chptr++ = *srcptr++;
			srcptr++;
		}
		if (srcptr[0] == '$' && isdigit(srcptr[1])) {
			if (chptr + umtch[srcptr[1] - 0x30].rm_eo -
				    umtch[srcptr[1] - 0x30].rm_so >
			    enptr - 1)
				break;
			memcpy(chptr, ori_str + umtch[srcptr[1] - 0x30].rm_so,
			       umtch[srcptr[1] - 0x30].rm_eo -
				       umtch[srcptr[1] - 0x30].rm_so);
			chptr += umtch[srcptr[1] - 0x30].rm_eo -
				 umtch[srcptr[1] - 0x30].rm_so;
			srcptr += 2;
			continue;
		}
		*chptr++ = *srcptr++;
	}

	offset = chptr - buf;

	//copy the last part of the string
	if (umtch[0].rm_eo != umtch[0].rm_so) {
		memcpy(chptr, ori_str + umtch[0].rm_eo,
		       ori_len - umtch[0].rm_eo);
		chptr += ori_len - umtch[0].rm_eo;
	}

	*chptr = '\0';

	return offset;
}

void _replaceHeaderHttp(http_parser::HttpData *http,
					 phr_header *header,
					 struct list_head *replace_header,
					 regmatch_t *eol)
{
	char buf[ZCU_DEF_BUFFER_SIZE];
	struct replace_header *current, *next;

	if (header->header_off)
		return;

	list_for_each_entry_safe(current, next, replace_header, list) {
		eol->rm_eo = header->line_size;
		if (regexec(&current->name, header->name, 1, eol, REG_STARTEND) ==
			0) {
			if (str_replace_regexp(
					buf, header->value, header->value_len,
					&current->match,
					current->replace) != -1) {
				auto new_header_value = std::string(
					header->name, header->name_len);
				new_header_value += ": ";
				new_header_value += buf;
				http->addHeader(new_header_value);
				header->header_off = true;
				// Maybe modify for doing several sustitutions over the header
				break;
			}
		}
	}
}

void _removeHeaderHttp(phr_header *header, struct list_head *m, regmatch_t *eol)
{
	struct matcher *current, *next;

	list_for_each_entry_safe(current, next, m, list) {
		if (regexec(&current->pat, header->name, 1,
				  eol, REG_STARTEND) == 0) {
			header->header_off = true;
			break;
		}
	}
}

std::string getCookieValue(std::string_view cookie_header_value,
								  std::string_view sess_id)
{
	auto it_start = cookie_header_value.find(sess_id);
	if (it_start == std::string::npos)
		return std::string();
	it_start = cookie_header_value.find('=', it_start);
	auto it_end = cookie_header_value.find(';', it_start++);
	it_end = it_end != std::string::npos ? it_end : cookie_header_value.size();
	std::string res(cookie_header_value.data() + it_start,
					it_end - it_start);
	return res;
}

static std::string getQueryParameter(const std::string &url,
                                     const std::string &sess_id)
{
	auto it_start = url.find(sess_id);
	if (it_start == std::string::npos)
		return std::string();
	it_start = url.find('=', it_start);
	auto it_end = url.find(';', it_start++);
	it_end = it_end != std::string::npos ? it_end : url.find('&', it_start);
	;
	it_end = it_end != std::string::npos ? it_end : url.size();
	std::string res(url.data() + it_start, it_end - it_start);
	return res;
}

static std::string getUrlParameter(const std::string &url)
{
	std::string expr_ = "[;][^?]*";
	std::smatch match;
	std::regex rgx(expr_);

	if (std::regex_search(url, match, rgx)) {
		std::string result = match[0];
		return result.substr(1);
	} else {
		return std::string();
	}
}

std::string zproxy_service_get_session_key(struct zproxy_sessions *sessions, char *client_addr, HttpRequest &request)
{
	std::string key;

	switch (sessions->type) {
	case SESS_TYPE::SESS_NONE:
		break;
	case SESS_TYPE::SESS_IP:
		key = client_addr;
		break;
	case SESS_TYPE::SESS_BCK_COOKIE:
		/* fallthrough */
	case SESS_TYPE::SESS_COOKIE:
		if (!request.getHeaderValue(http::HTTP_HEADER_NAME::COOKIE, key))
			key = "";
		else
			key = getCookieValue(key, sessions->id);
		break;
	case SESS_TYPE::SESS_URL: {
		std::string url = request.getUrl();
		key = getQueryParameter(url, sessions->id);
		break;
	} case SESS_TYPE::SESS_PARM: {
		std::string url = request.getUrl();
		key = getUrlParameter(url);
		break;
	} case SESS_TYPE::SESS_HEADER:
		if (!request.getHeaderValue(sessions->id, key))
			key = "";
		break;
	case SESS_TYPE::SESS_BASIC:
		if (!request.getHeaderValue(
				http::HTTP_HEADER_NAME::AUTHORIZATION,
				key)) {
			key = "";
		} else {
			std::stringstream string_to_iterate(key);
			std::istream_iterator<std::string> begin(
				string_to_iterate);
			std::istream_iterator<std::string> end;
			std::vector<std::string> header_value_parts(begin, end);
			if (header_value_parts[0] != "Basic") {
				key = "";
			} else {
				key = header_value_parts
					[1]; // Currently it stores username:password
			}
		}
		break;
	default:
		break;
	}

	return key;
}

void http_manager::rewriteUrl(HttpStream *stream)
{
	char buf[ZCU_DEF_BUFFER_SIZE];
	HttpRequest &request = stream->request;
	int offset = 0, ori_size = ZCU_DEF_BUFFER_SIZE;
	bool modif = false;
	struct replace_header *current, *next;

	if (list_empty(&stream->service_config->runtime.req_rw_url))
		return;

	std::string path_orig = request.path;

	list_for_each_entry_safe(current, next, &stream->service_config->runtime.req_rw_url, list) {
		offset = str_replace_regexp(
			buf, request.path.data(), request.path.length(),
			&current->match, current->replace);
		if (offset != -1) {
			modif = true;
			request.path_mod = 1;
			request.path = buf;
			zcu_log_print_th(LOG_DEBUG,
					  "URL rewritten \"%s\" -> \"%s\"",
					  path_orig.data(), request.path.data());

			if (ori_size >
				static_cast<int>(request.path.length()) - offset) {
				ori_size = static_cast<int>(
						   request.path.length()) -
					   offset;
			}
		}
	}

	if (modif) {
		request.path_mod = true;
		request.path_repl = std::string(
			request.path.data(), request.path.length() - ori_size);
		request.path_ori = std::string(
			path_orig.data(), path_orig.length() - ori_size);
		zcu_log_print_th(LOG_DEBUG, "URL for reverse Location \"%s\"",
				  request.path.data());
	}

	request.http_message_str =
		std::string_view(request.method, request.method_len);
	request.http_message_str +=
		" " + request.path + " HTTP/" + request.getHttpVersion();
}

static void getHostAndPort(const std::string &vhost, const std::string &proto,
			   std::string &host_addr, int &port)
{
	host_addr = vhost;
	port = 0;
	auto port_it = vhost.find(':');

	if (port_it != std::string::npos) {
		port = std::stoul(
			vhost.substr(port_it + 1, vhost.length()));
		host_addr = vhost.substr(0, port_it);
	} else {
		port = proto == "https" ? 443 : 80;
	}
}


void parseUrl(std::string header_value, regmatch_t *matches, std::string &proto, std::string &host,
		std::string &path, std::string &addr, int &port)
{
	matches[0].rm_so = 0;
	matches[0].rm_eo = header_value.length();

	if (!regexec(&URL_REGEX, header_value.data(),
			4, matches, REG_STARTEND)) {
		proto = std::string(
			header_value.data() + matches[1].rm_so,
			static_cast<size_t>(matches[1].rm_eo - matches[1].rm_so));
		host = std::string(
			header_value.data() + matches[2].rm_so,
			static_cast<size_t>(matches[2].rm_eo - matches[2].rm_so));
		path = std::string(
			header_value.data() + matches[3].rm_so,
			static_cast<size_t>(matches[3].rm_eo - matches[3].rm_so));

		getHostAndPort(host, proto, addr, port);
	} else {
		path = header_value;
	}

	return;
}

bool isHost(std::string vaddr, int vport, std::string addr, int port) {
	std::string new_header_value;
	bool ret = false;

	auto in_addr = zcu_net_get_address(vaddr.c_str(), vport);

	if (in_addr != nullptr) {
		auto in_addr_2 = zcu_net_get_address(addr.c_str(), port);

		if (zcu_soc_equal_sockaddr(in_addr->ai_addr, in_addr_2->ai_addr, 1))
			ret = true;

		freeaddrinfo(in_addr);
		freeaddrinfo(in_addr_2);
	}

	return ret;
}

void rewriteHeaderDestination(HttpRequest &request, zproxy_proxy_cfg *listener, zproxy_backend_cfg *backend)
{
	regmatch_t matches[4];
	std::string proto;
	std::string host;
	std::string path;
	std::string host_addr;
	int port;
	std::string newh = http::http_info::headers_names_strings.at(http::HTTP_HEADER_NAME::DESTINATION) + ": ";

	parseUrl(request.destination_header, matches, proto, host, path, host_addr, port);

	if (host.empty() || !isHost(host_addr, port, listener->address, listener->port)) {
		newh += request.destination_header;
	} else {
		if (backend->runtime.ssl_enabled)
			newh += "https://";
		else
			newh += "http://";
		newh += std::string(backend->address) + ":" + std::to_string(backend->port) + path;
	}

	newh += http::CRLF;
	request.volatile_headers.push_back(std::move(newh));
}

void http_manager::setHeadersRewrBck(HttpStream *stream) {
	stream->request.volatile_headers.clear();

	if (stream->request.add_host_header)
		stream->request.setHeaderHost(stream->backend_config);

	if (stream->request.add_destination_header)
		rewriteHeaderDestination(stream->request, stream->listener_config, stream->backend_config);
}

static std::string _rewriteHeaderLocation(const std::string &header_value,
					  const std::string &proto,
					  const std::string &vhost,
					  const std::string &vhost_header,
					  const struct zproxy_proxy_cfg *listener_config,
					  int rewr_loc_vhost,
					  const struct zproxy_backend_cfg *backend)
{
	std::string new_header_value = "";
	std::string host_addr;
	int port;

	getHostAndPort(vhost, proto, host_addr, port);
	struct addrinfo *in_addr = zcu_net_get_address(host_addr.c_str(), port);

	if (in_addr) {
		struct addrinfo *backend_addr =
			zcu_net_get_address(backend->address, backend->port);
		struct addrinfo *listener_addr =
			zcu_net_get_address(listener_config->address, listener_config->port);

		// rewrite location if it points to the backend
		if (zcu_soc_equal_sockaddr(in_addr->ai_addr, backend_addr->ai_addr, 1)) {
			new_header_value = proto;
		// or the listener address with different port
		} else if (rewr_loc_vhost == 1 &&
			   (listener_config->port != port ||
			    ((listener_config->runtime.ssl_enabled == false) ? "http" : "https") != proto) &&
			   (zcu_soc_equal_sockaddr(in_addr->ai_addr, listener_addr->ai_addr, 0) || vhost == vhost_header)) {
			new_header_value = (proto == "https") ? "http" : "https";
		}

		if (!new_header_value.empty()) {
			new_header_value += "://";
			new_header_value += vhost_header;

			if ((listener_config->runtime.ssl_enabled == false && listener_config->port != 443) ||
			    (listener_config->port != 80)) {
				if (header_value.find(':') == std::string::npos) {
					new_header_value += ":";
					new_header_value += std::to_string(listener_config->port);
				}
			}
		}

		freeaddrinfo(backend_addr);
		freeaddrinfo(listener_addr);
		freeaddrinfo(in_addr);
	}

	if (new_header_value.empty() && !proto.empty() && !vhost.empty())
		new_header_value = proto + "://" + vhost;

	return new_header_value;
}

int rewriteHeaderLocation(HttpStream *stream, http::HTTP_HEADER_NAME header_name, phr_header *header)
{
	std::string header_value;
	header_value = std::string_view(header->value, header->value_len);

	int rw_location = stream->service_config->header.rw_location;
	int rw_url_rev = stream->service_config->header.rw_url_rev;

	if (!stream->request.path_mod)
		rw_url_rev = 0;

	if (rw_location == 0 && rw_url_rev == 0)
		return 0;

	// Rewrite location
	regmatch_t matches[4];
	std::string proto;
	std::string host;
	std::string path;
	std::string host_addr;
	int port;
	std::string new_header_value = "";

	parseUrl(header_value, matches, proto, host, path, host_addr, port);

	if (stream->backend_config && rw_location != 0) {
		new_header_value = _rewriteHeaderLocation(header_value,
			proto, host, stream->request.virtual_host, stream->listener_config,
			rw_location, stream->backend_config);
	}

	if (new_header_value.empty() && !proto.empty() && !host.empty())
		new_header_value = proto + "://" + host;

	if (stream->request.path_mod && rw_url_rev) {
		// the string to remove must be at the begining
		if (path.find(stream->request.path_repl.data()) == 0) {
			path.replace(0, stream->request.path_repl.length(),
					 stream->request.path_ori);
			syslog(LOG_DEBUG,"location-rewritten: %s", path.data());
		}
	}
	new_header_value += path;

	header->header_off = 1;
	stream->response.addHeader(header_name, new_header_value);

	return 1;
}

validation::REQUEST_RESULT http_manager::validateRequestLine(HttpStream *stream) {
	regmatch_t eol{ 0, static_cast<regoff_t>(
				   stream->request.http_message_str.length()) };

	auto res = ::regexec(&stream->listener_config->runtime.req_verb_reg,
				 stream->request.http_message_str.data(),
				 1, // include validation data package
				 &eol, REG_STARTEND);

	if (res != 0) {
		return validation::REQUEST_RESULT::METHOD_NOT_ALLOWED;
	} else {
		stream->request.setRequestMethod();
	}

	// URL
	if (stream->request.path.find("%00") != std::string::npos) {
		return validation::REQUEST_RESULT::URL_CONTAIN_NULL;
	}
	eol.rm_so = 0;
	eol.rm_eo = stream->request.path.length();
	if (stream->listener_config->request.url_pat_str[0] &&
		regexec(&stream->listener_config->runtime.req_url_pat_reg, stream->request.path.data(), 1, &eol,
			REG_STARTEND)) {
		return validation::REQUEST_RESULT::BAD_URL;
	}

	return validation::REQUEST_RESULT::OK;
}

validation::REQUEST_RESULT http_manager::validateRequest(HttpStream *stream)
{
	auto &listener = stream->listener_config;
	auto &service = stream->service_config;
	HttpRequest &request = stream->request;
	struct list_head *remove_match = (!list_empty(&service->runtime.del_header_req)) ?
		&service->runtime.del_header_req:
		&listener->runtime.del_header_req;
	struct list_head *repl_ptr = (!list_empty(&service->runtime.replace_header_req)) ?
		&service->runtime.replace_header_req:
		&listener->runtime.replace_header_req;
	std::string addHeaders = strlen(service->header.add_header_req) != 0 ?
		std::string(service->header.add_header_req) :
		std::string(listener->header.add_header_req);

	// Check request size .
	if (UNLIKELY(listener->max_req > 0 &&
		     request.headers_length >
				 static_cast<size_t>(listener->max_req) &&
		     request.request_method !=
			     http::REQUEST_METHOD::RPC_IN_DATA &&
		     request.request_method !=
			     http::REQUEST_METHOD::RPC_OUT_DATA)) {
		return validation::REQUEST_RESULT::REQUEST_TOO_LARGE;
	}

	// Check for correct headers
	for (size_t i = 0; i != request.num_headers; i++) {
		regmatch_t eol{ 0, static_cast<regoff_t>(request.headers[i].line_size) };
		eol.rm_so = 0;
		eol.rm_eo = request.headers[i].line_size;

		/* maybe header to be removed */
		_removeHeaderHttp(&request.headers[i], remove_match, &eol);

		_replaceHeaderHttp(&request, &request.headers[i], repl_ptr, &eol);

		stream->request.manageHeaders(*stream->listener_config, &request.headers[i]);
	}

	// Add the headers configured (addXheader directives). Service context has more
	// priority. These headers are not removed for removeheader directive
	if(!addHeaders.empty())
		stream->request.addHeader(addHeaders, true);

	request.setHeaderXForwardedFor(stream->client_addr);

	if (request.message_length > 0 && !request.expectBody()) {
		streamLogMessage(stream, "Request body is not expected, ignore %lu extra bytes: %.*s",
			request.message_length, request.message_length,
			request.message);
		request.message_length = 0;
	}

	return validation::REQUEST_RESULT::OK;
}

static void zproxy_http_manage_set_cookie(HttpStream *stream, std::string session_key)
{
	if (!stream->backend_config)
		return;

	if (session_key.empty()) {
		if (stream->service_config->session.sess_type != SESS_TYPE::SESS_BCK_COOKIE)
			return;

		stream->response.addHeader(http::HTTP_HEADER_NAME::SET_COOKIE,
								stream->backend_config->cookie_set_header);
		session_key = getCookieValue(stream->backend_config->cookie_set_header,
								stream->session->id);
	}

	zproxy_session_add(stream->session,
						session_key.data(),
						&stream->backend_config->runtime.addr);
}

validation::REQUEST_RESULT http_manager::validateResponse(HttpStream *stream)
{
	auto &listener = stream->listener_config;
	HttpResponse &response = stream->response;
	struct list_head *remove_match = (stream->service_config && !list_empty(&stream->service_config->runtime.del_header_res)) ?
		&stream->service_config->runtime.del_header_res:
		&listener->runtime.del_header_res;
	struct list_head *repl_ptr = (stream->service_config && !list_empty(&stream->service_config->runtime.replace_header_res)) ?
		&stream->service_config->runtime.replace_header_res:
		&listener->runtime.replace_header_res;
	std::string addHeaders = (stream->service_config && strlen(stream->service_config->header.add_header_res) != 0) ?
		std::string(stream->service_config->header.add_header_res) :
		std::string(listener->header.add_header_res);
	std::string session_key = "";

	/* If the response is 100 continue we need to enable chunked transfer. */
	if (response.http_status_code == 100) {
		return validation::REQUEST_RESULT::OK;
	}

	for (size_t i = 0; i != response.num_headers; i++) {
		regmatch_t eol{ 0, static_cast<regoff_t>(response.headers[i].line_size) };
		eol.rm_so = 0;
		eol.rm_eo = response.headers[i].line_size;

		/* maybe header to be removed from response */
		_removeHeaderHttp(&response.headers[i], remove_match, &eol);

		// check for header to be replaced in response
		_replaceHeaderHttp(
			&response, &response.headers[i],
			repl_ptr, &eol);

		if (response.headers[i].header_off)
			continue;

		stream->response.manageHeaders(&response.headers[i], stream->service_config, session_key);
	}

	// backend cookie insert
	zproxy_http_manage_set_cookie(stream, session_key);

	// Add custom headers
	if (!addHeaders.empty())
		response.addHeader(addHeaders, true);

	if (stream->response.location != nullptr)
		rewriteHeaderLocation(stream, http::HTTP_HEADER_NAME::LOCATION, stream->response.location);

	if (stream->response.content_location != nullptr)
		rewriteHeaderLocation(stream, http::HTTP_HEADER_NAME::CONTENT_LOCATION, stream->response.content_location);

	if (stream->request.connection_header_upgrade
			&& stream->request.upgrade_header
			&& stream->response.connection_header_upgrade
			&& stream->response.upgrade_header ) {
		stream->websocket = true;
		streamLogDebug(stream, "Websocket enabled");
	}

	if (stream->service_config && stream->service_config->header.sts > 0)
		stream->response.setHeaderStrictTransportSecurity(stream->service_config->header.sts);

	if (stream->response.message_length > 0 && !stream->response.expectBody()) {
		streamLogMessage(stream, "Response body is not defined, but %lu extra bytes was received: %.*s",
			stream->response.message_length, stream->response.message_length,
			stream->response.message);
		response.connection_close_pending = 1;
		response.message_undefined = true;
		std::string header_value = "close";
		response.addHeader(http::HTTP_HEADER_NAME::CONNECTION, header_value);
	}

	return validation::REQUEST_RESULT::OK;
}

char * http_manager::replyError(HttpStream *stream, http::Code code,
				  const std::string &code_string,
				  const std::string &str)
{
	streamLogError(stream, code, code_string);

	// apply stats based on code
	zproxy_stats_listener_inc_code(stream->http_state,
			static_cast<int>(code));

	char * resp = nullptr;
	auto resp_str = http::getHttpResponse(code, code_string, str);
	size_t used_bytes;

	stream->response.parse(resp_str.c_str(), resp_str.size(), &used_bytes);
	if (validateResponse(stream) != validation::REQUEST_RESULT::OK) {
		streamLogMessage(stream,
				"Failed to validating proxy %d error response.", code);
		return nullptr;
	}

	size_t size = stream->response.prepareToSend(&resp);
	if (size == 0) {
		streamLogMessage(stream, "Failed to prepare %d error response.", code);
		return nullptr;
	}

	return resp;
}

char *http_manager::replyRedirect(int code, const std::string &url,
				 HttpStream &stream)
{
	char * resp = nullptr;
	streamLogRedirect(&stream, url.c_str());

	// apply stats based on code
	zproxy_stats_listener_inc_code(stream.http_state,
			static_cast<int>(code));

	auto resp_str = http::getRedirectResponse(static_cast<http::Code>(code), url);
	size_t used_bytes;

	stream.response.parse(resp_str.c_str(), resp_str.size(), &used_bytes);
	if (validateResponse(&stream) != validation::REQUEST_RESULT::OK) {
		streamLogMessage(&stream,
				"Failed to validating proxy %d error response.", code);
		return nullptr;
	}

	size_t size = stream.response.prepareToSend(&resp);
	if (size == 0) {
		streamLogMessage(&stream, "Failed to prepare %d error response.", code);
		return nullptr;
	}

	return resp;
}

/**
   * @brief It looks for a substring inside of a string.
   *
   * @param It is the start offset where the substrng was found
   * @param It is the end offset of the substring
   * @param It is the string where look for
   * @param It is the string lenght
   * @param It is the sub string that is going to be looked for
   * @param It is the sub string lenght
   *
   * @return 1 if the string was found of 0 if it didn't
   */
static int str_find_str(int *off_start, int *off_end, const char *ori_str,
		     int ori_len, const char *match_str, int match_len)
{
	int i, flag = 0;
	*off_start = -1;
	*off_end = -1;

	for (i = 0; i < ori_len && flag < match_len; i++) {
		if (ori_str[i] == match_str[flag]) {
			if (flag == 0)
				*off_start = i;
			flag++;
		} else
			flag = 0;
	}
	if (flag == 0)
		return 0;

	*off_end = *off_start + match_len;
	return 1;
}

/**
   * @brief It replaces a substring for another inside of a string
   *
   * @param It is the buffer where the string modified will be returned
   * @param It is the original string where looks for
   * @param It is the lenght of the original string
   * @param It is the sub string that is going to be removed
   * @param It is the sub string lenght
   * @param It is the string that will be insert
   * @param It is the length of the string to insert
   *
   * @return 1 if the string was modified or 0 if it doesn't
   */
int str_replace_str(char *buf, const char *ori_str, int ori_len,
			const char *match_str, int match_len, char *replace_str,
			int replace_len)
{
	int offst = -1, offend = -1, offcopy = 0,
	    buf_len = ori_len - match_len + replace_len;

	if (!str_find_str(&offst, &offend, ori_str, ori_len, match_str,
				  match_len))
		return 0;

	zcu_log_print_th(LOG_DEBUG, "String matches %.*s", ori_len, ori_str);

	if (buf_len > ZCU_DEF_BUFFER_SIZE) {
		zcu_log_print_th(
			LOG_ERR,
			"String could not be replaced, the buffer size is not enought - %.*s",
			ori_len, ori_str);
		return 0;
	}

	if (offst != 0) {
		memcpy(buf, ori_str, offst);
	}

	offcopy += offst;
	memcpy(buf + offcopy, replace_str, replace_len);

	if (offend != ori_len) {
		offcopy += replace_len;
		memcpy(buf + offcopy, ori_str + offend, ori_len - offend);
	}
	buf[buf_len] = '\0';

	return 1;
}

char *http_manager::replyRedirectBackend(HttpStream &stream,
				 zproxy_backend_redirect &redirect)
{
	std::string new_url(redirect.url);
	char buf[ZCU_DEF_BUFFER_SIZE];
	struct matcher *current, *next;

	if (redirect.redir_macro) {
		str_replace_str(
			buf, redirect.url, strlen(redirect.url),
			MACRO::VHOST_STR, MACRO::VHOST_LEN,
			const_cast<char *>(stream.request.virtual_host.data()),
			stream.request.virtual_host.length());
		new_url = buf;
	}

	switch (redirect.redir_type) {
	case 1: // dynamic
		list_for_each_entry_safe(current, next, &stream.service_config->runtime.req_url, list) {
			if (str_replace_regexp(buf, stream.request.path.data(),
					       stream.request.path.length(),
					       &current->pat, new_url.data()) != -1) {
				new_url = buf;
			}
		}
		break;
	case 2: // append
		new_url += stream.request.path;
		break;
	default:
		break;
	}

	int redirect_code = redirect.be_type;

	return replyRedirect(redirect_code, new_url, stream);
}
