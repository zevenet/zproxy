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

#include "zproxy.h"
#include "ctl.h"
#include "zcu_http.h"
#include "zcu_log.h"
#include "json.h"

#define API_REGEX_SELECT_LISTENER           "^[/]+listener[/]+([0-9]+)[/]*$"
#define API_REGEX_SELECT_LISTENER_SERVICES  "^[/]+listener[/]+([0-9]+)[/]+services[/]*$"
#define API_REGEX_SELECT_SERVICE            "^[/]+listener[/]+([0-9]+)[/]+service[/]+([a-zA-Z0-9-_. ]+)[/]*$"
#define API_REGEX_SELECT_SERVICE_SESSIONS   "^[/]+listener[/]+([0-9]+)[/]+service[/]+([a-zA-Z0-9-_. ]+)[/]+sessions[/]*$"
#define API_REGEX_SELECT_SESSION            "^[/]+listener[/]+([0-9]+)[/]+service[/]+([a-zA-Z0-9-_. ]+)[/]+session[/]+(.+)[/]*$"
#define API_REGEX_SELECT_SERVICE_BACKENDS   "^[/]+listener[/]+([0-9]+)[/]+service[/]+([a-zA-Z0-9-_. ]+)[/]+backends[/]*$"
#define API_REGEX_SELECT_BACKEND            "^[/]+listener[/]+([0-9]+)[/]+service[/]+([a-zA-Z0-9-_. ]+)[/]+backend[/]+([0-9.]+-[0-9]+)[/]*$"
#define API_REGEX_SELECT_BACKEND_STATUS     "^[/]+listener[/]+([0-9]+)[/]+service[/]+([a-zA-Z0-9-_. ]+)[/]+backend[/]+([0-9.]+-[0-9]+)[/]+status$"
#define API_REGEX_SELECT_CONFIG             "^[/]+config[/]*$"

static int send_msg(const struct zproxy_ctl_conn *ctl,
		    const enum ws_responses resp_code,
		    const char *content_type,
		    const char *buf, const size_t buf_len)
{
	int ret = 1;
	char resp_hdr[SRV_MAX_HEADER];

	if (content_type && buf && buf_len > 0) {
		sprintf(resp_hdr, "%s%s%s%zu%s%s%s%s%s%s",
			ws_str_responses[resp_code],
			content_type,
			HTTP_HEADER_CONTENTLEN, buf_len, HTTP_LINE_END,
			HTTP_HEADER_EXPIRES,
			HTTP_HEADER_PRAGMA_NO_CACHE,
			HTTP_HEADER_SERVER,
			HTTP_HEADER_CACHE_CONTROL, HTTP_LINE_END);
	} else {
		sprintf(resp_hdr, "%s%s%s%s%s%s",
			ws_str_responses[resp_code],
			HTTP_HEADER_EXPIRES,
			HTTP_HEADER_PRAGMA_NO_CACHE,
			HTTP_HEADER_SERVER,
			HTTP_HEADER_CACHE_CONTROL, HTTP_LINE_END);
	}

	if (send(ctl->io.fd, resp_hdr, strlen(resp_hdr), 0) < 0) {
		zcu_log_print(LOG_WARNING,
			      "Failed to send CTL response header to client.");
		return -1;
	}

	if (buf && buf_len > 0 && send(ctl->io.fd, buf, strlen(buf), 0) < 0) {
		zcu_log_print(LOG_WARNING,
			      "Failed to send CTL response body to client.");
		return -1;
	}

	return ret;
}

int ctl_handler_cb(const struct zproxy_ctl_conn *ctl,
		const struct zproxy_cfg *cfg)
{
	size_t used_bytes;
	HttpRequest request;
	const http_parser::PARSE_RESULT parse_res =
		request.parse(ctl->buf, ctl->buf_len, &used_bytes);
	regmatch_t matches[CONFIG_MAX_PARAMS];
	int ret = 1;
	char *buf = NULL;
	char err_str[ERR_BUF_MAX_SIZE];

	if (parse_res != http_parser::PARSE_RESULT::SUCCESS) {
		switch (parse_res) {
		case http_parser::PARSE_RESULT::FAILED:
			snprintf(err_str, ERR_BUF_MAX_SIZE,
				 "Failed to parse CTL request.");
			break;
		case http_parser::PARSE_RESULT::INCOMPLETE:
			snprintf(err_str, ERR_BUF_MAX_SIZE,
				 "Couldn't parse CTL request: incomplete.");
			break;
		case http_parser::PARSE_RESULT::TOOLONG:
			snprintf(err_str, ERR_BUF_MAX_SIZE,
				 "CTL request too long.");
			break;
		default:
			break;
		}

		send_msg(ctl, WS_HTTP_400, HTTP_HEADER_CONTENT_PLAIN,
			 err_str, strlen(err_str));
		return -1;
	}

	// set size to maximum number of parameters
	switch (request.getRequestMethod()) {
	case http::REQUEST_METHOD::GET:
		if (zproxy_regex_exec(API_REGEX_SELECT_LISTENER,
				      request.path.c_str(), matches)) {
			const std::string param =
				request.path.substr(matches[1].rm_so,
						matches[1].rm_eo - matches[1].rm_so);
			const int listener_id = atoi(param.c_str());
			ret = zproxy_json_encode(cfg,
					listener_id, NULL, NULL,
					ENCODE_PROXY, &buf);
		} else if (zproxy_regex_exec(API_REGEX_SELECT_LISTENER_SERVICES,
					     request.path.c_str(), matches)) {
			const std::string param =
				request.path.substr(matches[1].rm_so,
						matches[1].rm_eo - matches[1].rm_so);
			const int listener_id = atoi(param.c_str());
			ret = zproxy_json_encode(cfg,
					listener_id, NULL, NULL,
					ENCODE_PROXY_SERVICES, &buf);
		} else if (zproxy_regex_exec(API_REGEX_SELECT_SERVICE,
					     request.path.c_str(), matches)) {
			const std::string param1 =
				request.path.substr(matches[1].rm_so,
						matches[1].rm_eo - matches[1].rm_so);
			const int listener_id = atoi(param1.c_str());
			const std::string service_id =
				request.path.substr(matches[2].rm_so,
						matches[2].rm_eo - matches[2].rm_so);
			ret = zproxy_json_encode(cfg,
					listener_id, service_id.c_str(), NULL,
					ENCODE_SERVICE, &buf);
		} else if (zproxy_regex_exec(API_REGEX_SELECT_SERVICE_BACKENDS,
					     request.path.c_str(), matches)) {
			const std::string param1 =
				request.path.substr(matches[1].rm_so,
						matches[1].rm_eo - matches[1].rm_so);
			const int listener_id = atoi(param1.c_str());
			const std::string service_id =
				request.path.substr(matches[2].rm_so,
						matches[2].rm_eo - matches[2].rm_so);
			ret = zproxy_json_encode(cfg,
					listener_id, service_id.c_str(), NULL,
					ENCODE_SERVICE_BACKENDS, &buf);
		} else if (zproxy_regex_exec(API_REGEX_SELECT_BACKEND,
					     request.path.c_str(), matches)) {
			const std::string param1 =
				request.path.substr(matches[1].rm_so,
						matches[1].rm_eo - matches[1].rm_so);
			const int listener_id = atoi(param1.c_str());
			const std::string service_id =
				request.path.substr(matches[2].rm_so,
						matches[2].rm_eo - matches[2].rm_so);
			const std::string backend_id =
				request.path.substr(matches[3].rm_so,
						matches[3].rm_eo - matches[3].rm_so);
			ret = zproxy_json_encode(cfg,
					listener_id, service_id.c_str(), backend_id.c_str(),
					ENCODE_BACKEND, &buf);
		} else {
			send_msg(ctl, WS_HTTP_400, NULL, NULL, 0);
			return -1;
		}

		if (ret > 0) {
			send_msg(ctl, WS_HTTP_200, HTTP_HEADER_CONTENT_JSON,
				 buf, strlen(buf));
		} else if (ret == -1) {
			send_msg(ctl, WS_HTTP_404, HTTP_HEADER_CONTENT_PLAIN,
				 buf, strlen(buf));
		} else {
			send_msg(ctl, WS_HTTP_500, HTTP_HEADER_CONTENT_PLAIN,
				 buf, strlen(buf));
		}
		free(buf);
		break;
	case http_parser::REQUEST_METHOD::PATCH:
		if (zproxy_regex_exec(API_REGEX_SELECT_BACKEND_STATUS,
				      request.path.c_str(), matches)) {
			const std::string param1 =
				request.path.substr(matches[1].rm_so,
						    matches[1].rm_eo - matches[1].rm_so);
			const int listener_id = atoi(param1.c_str());
			const std::string service_id =
				request.path.substr(matches[2].rm_so,
						    matches[2].rm_eo - matches[2].rm_so);
			const std::string backend_id =
				request.path.substr(matches[3].rm_so,
						    matches[3].rm_eo - matches[3].rm_so);
			ret = zproxy_json_exec(cfg, listener_id,
					       service_id.c_str(),
					       backend_id.c_str(),
					       JSON_CMD_BACKEND_STATUS,
					       request.message, &buf);
		} else if (zproxy_regex_exec(API_REGEX_SELECT_SESSION,
					     request.path.c_str(), matches)) {
			const std::string param1 =
				request.path.substr(matches[1].rm_so,
						    matches[1].rm_eo - matches[1].rm_so);
			const int listener_id = atoi(param1.c_str());
			const std::string service_id =
				request.path.substr(matches[2].rm_so,
						    matches[2].rm_eo - matches[2].rm_so);
			const std::string session_id =
				request.path.substr(matches[3].rm_so,
						    matches[3].rm_eo - matches[3].rm_so);
			ret = zproxy_json_exec(cfg, listener_id, service_id.c_str(),
					       session_id.c_str(),
					       JSON_CMD_MODIFY_SESSION,
					       request.message, &buf);
		} else if (zproxy_regex_exec(API_REGEX_SELECT_CONFIG,
					     request.path.c_str(), matches)) {
			ret = zproxy_json_exec(cfg, 0, NULL, NULL,
					       JSON_CMD_RELOAD_CONFIG,
					       NULL, &buf);
		} else {
			send_msg(ctl, WS_HTTP_400, NULL, NULL, 0);
			return -1;
		}

		if (ret > 0) {
			send_msg(ctl, WS_HTTP_200, HTTP_HEADER_CONTENT_JSON,
				 buf, strlen(buf));
		} else if (ret == -1) {
			send_msg(ctl, WS_HTTP_404, HTTP_HEADER_CONTENT_JSON,
				 buf, strlen(buf));
		} else {
			send_msg(ctl, WS_HTTP_500, HTTP_HEADER_CONTENT_JSON,
				 buf, strlen(buf));
		}
		free(buf);
		break;
	case http_parser::REQUEST_METHOD::DELETE:
		if (zproxy_regex_exec(API_REGEX_SELECT_SERVICE_SESSIONS,
				      request.path.c_str(), matches)) {
			const std::string param1 =
				request.path.substr(matches[1].rm_so,
						    matches[1].rm_eo - matches[1].rm_so);
			const int listener_id = atoi(param1.c_str());
			const std::string service_id =
				request.path.substr(matches[2].rm_so,
						    matches[2].rm_eo - matches[2].rm_so);
			ret = zproxy_json_exec(cfg, listener_id, service_id.c_str(),
					       NULL, JSON_CMD_FLUSH_SESSIONS,
					       request.message, &buf);
		} else {
			send_msg(ctl, WS_HTTP_400, NULL, NULL, 0);
			return -1;
		}

		if (ret > 0) {
			send_msg(ctl, WS_HTTP_204, HTTP_HEADER_CONTENT_JSON,
				 buf, strlen(buf));
		} else if (ret == -1) {
			send_msg(ctl, WS_HTTP_404, HTTP_HEADER_CONTENT_JSON,
				 buf, strlen(buf));
		} else {
			send_msg(ctl, WS_HTTP_400, HTTP_HEADER_CONTENT_JSON,
				 buf, strlen(buf));
		}
		free(buf);
		break;
	case http_parser::REQUEST_METHOD::PUT:
		if (zproxy_regex_exec(API_REGEX_SELECT_SERVICE_SESSIONS,
				      request.path.c_str(), matches)) {
			const std::string param1 =
				request.path.substr(matches[1].rm_so,
						    matches[1].rm_eo - matches[1].rm_so);
			const int listener_id = atoi(param1.c_str());
			const std::string service_id =
				request.path.substr(matches[2].rm_so,
						    matches[2].rm_eo - matches[2].rm_so);
			ret = zproxy_json_exec(cfg, listener_id, service_id.c_str(),
					       NULL, JSON_CMD_ADD_SESSION,
					       request.message, &buf);
		} else if (zproxy_regex_exec(API_REGEX_SELECT_SERVICE_BACKENDS,
					     request.path.c_str(), matches)) {
			const std::string param1 =
				request.path.substr(matches[1].rm_so,
						    matches[1].rm_eo - matches[1].rm_so);
			const int listener_id = atoi(param1.c_str());
			const std::string service_id =
				request.path.substr(matches[2].rm_so,
						    matches[2].rm_eo - matches[2].rm_so);
			ret = zproxy_json_exec(cfg, listener_id, service_id.c_str(),
					       NULL, JSON_CMD_ADD_BACKEND,
					       request.message, &buf);
		} else {
			send_msg(ctl, WS_HTTP_400, NULL, NULL, 0);
			return -1;
		}

		if (ret > 0) {
			send_msg(ctl, WS_HTTP_201, HTTP_HEADER_CONTENT_JSON,
				 buf, strlen(buf));
		} else if (ret == -1) {
			send_msg(ctl, WS_HTTP_404, HTTP_HEADER_CONTENT_JSON,
				 buf, strlen(buf));
		} else if (ret == -2) {
			send_msg(ctl, WS_HTTP_400, HTTP_HEADER_CONTENT_JSON,
				 buf, strlen(buf));
		} else {
			send_msg(ctl, WS_HTTP_409, HTTP_HEADER_CONTENT_JSON,
				 buf, strlen(buf));
		}
		free(buf);
		break;
	default:
		send_msg(ctl, WS_HTTP_405, NULL, NULL, 0);
		return -1;
		break;
	}

	return ret;
}
