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

#include <unistd.h>
#include <string>

#include "waf.h"
#include "http_log.h"
#include "http_request.h"
#include "http_response.h"
#include "http_manager.h"
#include "state.h"

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
	modsecurity::ModSecurity *modsec_api = modsecurity::msc_init();

	sprintf(conn_str, "zproxy_%d_connector", getpid());
	msc_set_connector_info(modsec_api, conn_str);
	msc_set_log_cb(modsec_api, zproxy_waf_logmodsec);

	return (void *) modsec_api;
}

void zproxy_waf_destroy_api(void *modsec)
{
	if (modsec)
		msc_cleanup((modsecurity::ModSecurity*)modsec);
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
	if (rules)
		msc_rules_cleanup((modsecurity::Rules*)rules);
}

int zproxy_waf_parse_conf(const std::string &file, void **rules)
{
	int err;
	const char *err_str;
	if (!*rules)
		*rules = modsecurity::msc_create_rules_set();

	modsecurity::Rules *waf_rules = (modsecurity::Rules*)*rules;

	err = msc_rules_add_file(waf_rules, file.data(), &err_str);
	if (err == -1) {
		fprintf(stderr,
			"error loading waf ruleset file %s: %s",
			file.data(), err_str);
		return -1;
	}
	return 0;
}

static void waf_reset_intervention(modsecurity::ModSecurityIntervention *it)
{
	// equivalent to modsecurity::intervention::reset(&modsec_transaction->m_it);
	it->status = 200;
	it->url = (char*)NULL;
	it->log = (char*)NULL;
	it->disruptive = 0;
}

struct zproxy_waf_stream *zproxy_waf_stream_init(void *api, void *rules)
{
	struct zproxy_waf_stream *waf_stream =
		(struct zproxy_waf_stream*)calloc(1, sizeof(struct zproxy_waf_stream));

	waf_stream->waf_rules = (modsecurity::Rules*)rules;
	waf_stream->waf_enable = waf_stream->waf_rules ? true : false;

	waf_stream->waf_api = (modsecurity::ModSecurity*)api;

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
	modsecurity::ModSecurityIntervention it;

	streamLogWaf(stream, "WAF in request disrupted the HTTP transaction");

	zproxy_stats_listener_inc_waf(stream->http_state);

	waf_reset_intervention(&it);
	msc_intervention(waf_stream->modsec_transaction, &it);
	if (it.url != nullptr) {
		resp = http_manager::replyRedirect(it.status, it.url, *stream);
		free(it.url);
	} else {
		http::Code code = (http::Code)it.status;
		resp = http_manager::replyError(stream, code,
						http_info::http_status_code_strings.at(code),
						stream->listener_config->runtime.errwaf_msg);
	}

	if (it.log != nullptr)
		free(it.log);
	if (it.url != nullptr)
		free(it.url);

	return resp;
}

bool zproxy_waf_stream_checkrequestheaders(struct zproxy_waf_stream *waf_stream,
					   HttpStream *stream)
{
	modsecurity::ModSecurityIntervention it;

	if (!waf_stream->waf_enable)
		return WAF_PASS;

	std::string httpVersion = stream->request.getHttpVersion();
	std::string httpMethod(stream->request.method, stream->request.method_len);

	zproxy_waf_stream_resettransaction(waf_stream);

	waf_reset_intervention(&it);
	msc_intervention(waf_stream->modsec_transaction, &it);

	msc_process_connection(waf_stream->modsec_transaction,
			       stream->client_addr.data(),
			       stream->client_port,
			       stream->listener_config->address,
			       stream->listener_config->port);
	msc_process_uri(waf_stream->modsec_transaction, stream->request.path.data(),
			httpMethod.data(), httpVersion.data());

	for (int i = 0; i < (int)stream->request.num_headers; i++) {
		unsigned char *name = (unsigned char*)stream->request.headers[i].name;
		size_t name_len = stream->request.headers[i].name_len;
		unsigned char *value = (unsigned char*)stream->request.headers[i].value;
		size_t value_len = stream->request.headers[i].value_len;
		msc_add_n_request_header(waf_stream->modsec_transaction, name,
					 name_len, value, value_len);
	}
	msc_process_request_headers(waf_stream->modsec_transaction);

	if (it.log != nullptr)
		free(it.log);
	if (it.url != nullptr)
		free(it.url);

	waf_reset_intervention(&it);
	msc_intervention(waf_stream->modsec_transaction, &it);
	if (it.log != nullptr) {
		streamLogWaf(stream, "%s", it.log);
		free(it.log);
	}
	if (it.url != nullptr)
		free(it.url);

	return (it.disruptive);
}

bool zproxy_waf_stream_checkrequestbody(struct zproxy_waf_stream *waf_stream,
					HttpStream *stream)
{
	modsecurity::ModSecurityIntervention it;

	if (!waf_stream->waf_enable)
		return WAF_PASS;

	waf_reset_intervention(&it);
	msc_intervention(waf_stream->modsec_transaction, &it);

	if (stream->request.message_length > 0) {
		msc_append_request_body(waf_stream->modsec_transaction,
					(unsigned char*)stream->request.message,
					stream->request.message_length);
	}

	if (stream->response.expectBody() == false)
		msc_process_request_body(waf_stream->modsec_transaction);

	waf_reset_intervention(&it);
	msc_intervention(waf_stream->modsec_transaction, &it);
	if (it.log != nullptr) {
		streamLogWaf(stream, "%s", it.log);
		free(it.log);
	}
	if (it.url != nullptr)
		free(it.url);

	return (it.disruptive);
}

bool zproxy_waf_stream_checkresponseheaders(struct zproxy_waf_stream *waf_stream,
					    HttpStream *stream)
{
	modsecurity::ModSecurityIntervention it;

	if (!waf_stream->waf_enable)
		return WAF_PASS;

	waf_reset_intervention(&it);
	msc_intervention(waf_stream->modsec_transaction, &it);

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

	waf_reset_intervention(&it);
	msc_intervention(waf_stream->modsec_transaction, &it);
	if (it.log != nullptr) {
		streamLogWaf(stream, "%s", it.log);
		free(it.log);
	}
	if (it.url != nullptr)
		free(it.url);

	return (it.disruptive);
}

bool zproxy_waf_stream_responsebody(struct zproxy_waf_stream *waf_stream,
				    HttpStream *stream)
{
	modsecurity::ModSecurityIntervention it;

	if (!waf_stream->waf_enable)
		return WAF_PASS;

	if (stream->response.message_length > 0) {
		msc_append_response_body(waf_stream->modsec_transaction,
					 (unsigned char*)stream->response.message,
					 stream->response.message_length);
	}

	if (stream->response.expectBody() == false)
		msc_process_response_body(waf_stream->modsec_transaction);

	waf_reset_intervention(&it);
	msc_intervention(waf_stream->modsec_transaction, &it);
	if (it.log != nullptr) {
		streamLogWaf(stream, "%s", it.log);
		free(it.log);
	}
	if (it.url != nullptr)
		free(it.url);

	return (it.disruptive);
}
