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

#ifndef _ZPROXY_HTTP_MANAGER_H_
#define _ZPROXY_HTTP_MANAGER_H_

#include "http_protocol.h"
#include "http_stream.h"


struct Regex : public regex_t {
	explicit Regex(const char *reg_ex_expression) : regex_t()
	{
		if (::regcomp(this, reg_ex_expression,
				  REG_ICASE | REG_NEWLINE | REG_EXTENDED)) {
			zcu_log_print_th(LOG_ERR,
					  "%s():%d: error compiling regex: %s",
					  __FUNCTION__, __LINE__,
					  reg_ex_expression);
		}
	}
	bool doMatch(const char *str, size_t n_match, regmatch_t p_match[],
			 int e_flags = 0)
	{
		return ::regexec(this, str, n_match, p_match, e_flags) == 0;
	}
	~Regex()
	{
		::regfree(this);
	}
};
static const Regex URL_REGEX("^(http|https)://([^/]+)(.*)");


using namespace http;

class http_manager {
public:

	static void getHostAndPort(std::string vhost, std::string proto, std::string &host_addr,
		int &port);

	static void rewriteHeaderWithUrl(std::string &header_value,
		std::string &proto, std::string &vhost,
		std::string vhost_header, zproxy_proxy_cfg *listener_config,
		int rewr_loc_vhost, zproxy_backend_cfg *backend);

	static void setHeadersRewrBck(HttpStream *stream);

	static void rewriteUrl(HttpStream *stream);

	static validation::REQUEST_RESULT validateRequestLine(HttpStream *stream);

  /**
   * @brief Validates the request.
   *
   * It checks that all the headers are well formed and mark the headers off if
   * needed.
   *
   * @param request is the HttpRequest to modify.
   * @return if there is not any error it returns
   * validation::REQUEST_RESULT::OK. If errors happen, it returns the
   * corresponding element of validation::REQUEST_RESULT.
   */
    static http::validation::REQUEST_RESULT validateRequest(HttpStream *stream);

    static http::validation::REQUEST_RESULT validateResponse(HttpStream *stream);

	static char *replyError(HttpStream *stream, http::Code code,
				  const std::string &code_string,
				  const std::string &str);

	static char *replyRedirectBackend(HttpStream &stream,
				 zproxy_backend_redirect &redirect);

	static char *replyRedirect(int code, const std::string &url,
				 HttpStream &stream);
};

std::string zproxy_service_get_session_key(struct zproxy_sessions *sessions, char *client_addr, HttpRequest &request);
std::string getCookieValue(std::string_view cookie_header_value, std::string_view sess_id);

#endif
