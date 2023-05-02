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

#include "waf.h"
#include "state.h"
#include "zcu_log.h"
#include <string>
#include <sys/syslog.h>
#include <unistd.h>

static void zproxy_waf_logmodsec(void *data, const void *message)
{
	if (data != nullptr)
		zcu_log_print(LOG_WARNING, "%s", (char*)data);
	if (message != nullptr)
		zcu_log_print(LOG_WARNING, "[WAF] %s", (char*)message);
}

void *zproxy_waf_init_api(void)
{
	char conn_str[32];
	zcu_log_print(LOG_INFO, "Initializing ModSecurity API");
	modsecurity::ModSecurity *modsec_api = modsecurity::msc_init();

	sprintf(conn_str, "zproxy_%d_connector", getpid());
	msc_set_connector_info(modsec_api, conn_str);
	msc_set_log_cb(modsec_api, zproxy_waf_logmodsec);

	return (void *) modsec_api;
}

void zproxy_waf_destroy_api(void *modsec)
{
	if (modsec) {
		zcu_log_print(LOG_INFO, "Cleaning up ModSecurity API");
		msc_cleanup((modsecurity::ModSecurity*)modsec);
	}
}

void zproxy_waf_dump_rules(void *rules_ptr)
{
	if (!rules_ptr)
		return;

	modsecurity::Rules *rules = (modsecurity::Rules*)rules_ptr;

	zcu_log_print(LOG_DEBUG, "Rules: ");
	for (int i = 0; i <= modsecurity::Phases::NUMBER_OF_PHASES; i++) {
		auto rule = rules->getRulesForPhase(i);
		if (rule) {
			for (auto &x : *rule) {
				zcu_log_print(LOG_DEBUG,
						  "\tRule Id: %d From %s at %d ",
						  x->m_ruleId, x->m_fileName.data(),
						  x->m_lineNumber);
			}
		}
	}
}

void zproxy_waf_destroy_rules(void *rules)
{
	if (rules) {
		zcu_log_print(LOG_DEBUG, "Cleaning up WAF Rules");
		msc_rules_cleanup((modsecurity::Rules*)rules);
	}
}

int zproxy_waf_parse_conf(const char *file, void **rules)
{
	int err;
	const char *err_str;
	if (!*rules) {
		zcu_log_print(LOG_INFO, "Loading WAF Rules from %s", file);
		*rules = modsecurity::msc_create_rules_set();
	}

	modsecurity::Rules *waf_rules = (modsecurity::Rules*)*rules;

	err = msc_rules_add_file(waf_rules, file, &err_str);
	if (err == -1) {
		fprintf(stderr, "error loading waf ruleset file %s: %s",
			file, err_str);
		return -1;
	}
	return 0;
}

static enum WAF_ACTION waf_resolution(struct zproxy_waf_stream *waf_stream,
				      const HttpStream *stream)
{
	modsecurity::Transaction *t = waf_stream->modsec_transaction;
	modsecurity::ModSecurityIntervention *it = &waf_stream->last_it;
	it->status = 200;
	it->url = NULL;
	it->log = NULL;
	it->disruptive = 0;
	enum WAF_ACTION waf_action = WAF_PASS;

	if (msc_intervention(t, it)) {
		// log if any error was found
		if (!msc_process_logging(t)) {
			streamLogWaf(stream, "WAF, error processing the log");
		}
		if (it->url) {
			waf_action = WAF_REDIRECTION;
			if (it->status == 200)
				it->status = 302;
		} else if (it->disruptive) {
			waf_action = WAF_BLOCK;
			if (it->status == 200)
				it->status = 403;
		}
	}

	if (it->log)
		streamLogWaf(stream, "%s", it->log);

	return waf_action;
}

struct zproxy_waf_stream *zproxy_waf_stream_init(void *api, void *rules)
{
	struct zproxy_waf_stream *waf_stream =
		(struct zproxy_waf_stream*)calloc(1, sizeof(struct zproxy_waf_stream));
	if (!waf_stream)
		return NULL;

	waf_stream->waf_rules = (modsecurity::Rules*)rules;
	waf_stream->waf_api = (modsecurity::ModSecurity*)api;
	waf_stream->modsec_transaction = NULL;
	waf_stream->waf_enable = waf_stream->waf_rules ? true : false;

	return waf_stream;
}

void zproxy_waf_stream_destroy(struct zproxy_waf_stream *waf_stream)
{
	if (waf_stream->modsec_transaction)
		msc_transaction_cleanup(waf_stream->modsec_transaction);
	free(waf_stream);
}

static void zproxy_waf_stream_inittransaction(struct zproxy_waf_stream *waf_stream)
{
	if (waf_stream->waf_enable) {
		waf_stream->modsec_transaction =
			msc_new_transaction(waf_stream->waf_api, waf_stream->waf_rules,
					    (void*)zproxy_waf_logmodsec);
	}
}

static void zproxy_waf_stream_resettransaction(struct zproxy_waf_stream *waf_stream)
{
	if (waf_stream->modsec_transaction)
		msc_transaction_cleanup(waf_stream->modsec_transaction);
	zproxy_waf_stream_inittransaction(waf_stream);
}

char *zproxy_waf_stream_response(struct zproxy_waf_stream *waf_stream,
				 HttpStream *stream)
{
	char *resp = nullptr;
	modsecurity::ModSecurityIntervention *it = &waf_stream->last_it;

	streamLogWaf(stream, "WAF in request disrupted the HTTP transaction");

	zproxy_stats_listener_inc_waf(stream->http_state);
	if (it->url) {
		resp = http_manager::replyRedirect(it->status, it->url, *stream);
		free(it->url);
	} else {
		http::Code code = (http::Code)it->status;
		const char *html_msg =
			zproxy_cfg_get_errmsg(&stream->listener_config->error.errwaf_msgs,
					      it->status);
		// default to empty string so replyError() will format a default
		// response
		if (!html_msg)
			html_msg = "";
		resp = http_manager::replyError(stream, code,
						http_info::http_status_code_strings.at(code),
						html_msg);
	}

	if (it->log)
		free(it->log);

	return resp;
}

bool zproxy_waf_stream_checkrequestheaders(struct zproxy_waf_stream *waf_stream,
					   HttpStream *stream)
{
	enum WAF_ACTION waf_action;

	if (!waf_stream->waf_enable)
		return WAF_PASS;

	const std::string httpVersion = stream->request.getHttpVersion();
	const std::string httpMethod(stream->request.method,
				     stream->request.method_len);

	zproxy_waf_stream_resettransaction(waf_stream);

	msc_process_connection(waf_stream->modsec_transaction,
			       stream->client_addr.data(),
			       stream->client_port,
			       stream->listener_config->address,
			       stream->listener_config->port);
	msc_process_uri(waf_stream->modsec_transaction,
			stream->request.path.data(),
			httpMethod.data(), httpVersion.data());

	for (int i = 0; i < (int)stream->request.num_headers; i++) {
		unsigned char *name =
			(unsigned char*)stream->request.headers[i].name;
		size_t name_len = stream->request.headers[i].name_len;
		unsigned char *value =
			(unsigned char*)stream->request.headers[i].value;
		size_t value_len = stream->request.headers[i].value_len;
		msc_add_n_request_header(waf_stream->modsec_transaction, name,
					 name_len, value, value_len);
	}
	msc_process_request_headers(waf_stream->modsec_transaction);

	waf_action = waf_resolution(waf_stream, stream);

	return waf_action != WAF_PASS;
}

bool zproxy_waf_stream_checkrequestbody(struct zproxy_waf_stream *waf_stream,
					HttpStream *stream)
{
	enum WAF_ACTION waf_action;

	if (!waf_stream->waf_enable)
		return WAF_PASS;

	if (stream->request.message_length > 0) {
		msc_append_request_body(waf_stream->modsec_transaction,
					(unsigned char*)stream->request.message,
					stream->request.message_length);
	}

	if (!stream->response.expectBody())
		msc_process_request_body(waf_stream->modsec_transaction);

	waf_action = waf_resolution(waf_stream, stream);

	return waf_action != WAF_PASS;
}

bool zproxy_waf_stream_checkresponseheaders(struct zproxy_waf_stream *waf_stream,
					    HttpStream *stream)
{
	enum WAF_ACTION waf_action;

	if (!waf_stream->waf_enable)
		return WAF_PASS;

	for (int i = 0; i < (int)stream->response.num_headers; i++) {
		if (stream->response.headers[i].header_off)
			continue;
		unsigned char *name = (unsigned char*)stream->response.headers[i].name;
		size_t name_len = stream->response.headers[i].name_len;
		unsigned char *value = (unsigned char*)stream->response.headers[i].value;
		size_t value_len = stream->response.headers[i].value_len;
		msc_add_n_response_header(waf_stream->modsec_transaction, name,
					  name_len, value, value_len);
	}

	msc_process_response_headers(waf_stream->modsec_transaction,
				     stream->response.http_status_code,
				     stream->response.getHttpVersion().data());

	waf_action = waf_resolution(waf_stream, stream);

	return waf_action != WAF_PASS;
}

bool zproxy_waf_stream_checkresponsebody(struct zproxy_waf_stream *waf_stream,
					 HttpStream *stream)
{
	enum WAF_ACTION waf_action;

	if (!waf_stream->waf_enable)
		return WAF_PASS;

	if (stream->response.message_length > 0) {
		msc_append_response_body(waf_stream->modsec_transaction,
					 (unsigned char*)stream->response.message,
					 stream->response.message_length);
	}

	if (!stream->response.expectBody())
		msc_process_response_body(waf_stream->modsec_transaction);

	waf_action = waf_resolution(waf_stream, stream);

	return waf_action != WAF_PASS;
}
