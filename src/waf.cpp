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

#include <modsecurity/modsecurity.h>
#include <modsecurity/rules.h>
#include <modsecurity/transaction.h>
#include <unistd.h>

#include "waf.h"
#include "http_log.h"
#include "http_request.h"
#include "http_response.h"
#include "http_manager.h"
#include "state.h"

void Waf::logModsec(void *data, const void *message)
{
	if (data != nullptr)
		zcu_log_print_th(LOG_WARNING, "%s", static_cast<char *>(data));
	if (message != nullptr)
		zcu_log_print_th(LOG_WARNING, "[WAF] %s",
				  static_cast<char *>(const_cast<void *>(message)));
}

void *Waf::init_api(void)
{
	auto modsec_api = new modsecurity::ModSecurity();
	char pidstr[6];

	sprintf(pidstr, "%d", getpid());
	modsec_api->setConnectorInformation("zproxy_" + std::string(pidstr) + "_connector");
	modsec_api->setServerLogCb(logModsec);
	return (void *) modsec_api;
}

void Waf::destroy_api(void *modsec)
{
	if (modsec != nullptr)
		delete static_cast<modsecurity::ModSecurity*>(modsec);
}

void Waf::dump_rules(void *rules_ptr)
{
	if (rules_ptr == nullptr)
		return;

	auto rules = static_cast<modsecurity::Rules*>(rules_ptr);

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

void Waf::destroy_rules(void *rules)
{
	if(rules == nullptr)
		return;
	delete static_cast<modsecurity::Rules*>(rules);
}

int Waf::parse_conf(const std::string &file, void **rules)
{
	if (*rules == nullptr)
		*rules = new modsecurity::Rules();

	auto waf_rules = static_cast<modsecurity::Rules*>(*rules);

	auto err = waf_rules->loadFromUri(file.data());
	if (err == -1) {
		fprintf(stderr,
			"error loading waf ruleset file %s: %s",
			file.data(),
			waf_rules->getParserError().data());
		return -1;
	}
	return 0;
}

Waf::Stream::Stream(void *api, void *rules)
{
	waf_rules = static_cast<modsecurity::Rules*>(rules);
	if (waf_rules != nullptr)
		waf_enable = true;
	waf_api =  reinterpret_cast<modsecurity::ModSecurity *>(api);

}

Waf::Stream::~Stream()
{
	if(modsec_transaction != nullptr)
		delete modsec_transaction;
}

void Waf::Stream::resetTransaction()
{
	if(modsec_transaction != nullptr)
		delete modsec_transaction;
	initTransaction();
}

void Waf::Stream::initTransaction()
{
	if (waf_enable)
		modsec_transaction = new modsecurity::Transaction(waf_api, waf_rules, (void*)logModsec);
}

char *Waf::Stream::response(HttpStream *stream)
{
	char *resp = nullptr;

	streamLogWaf(stream, "WAF in request disrupted the HTTP transaction");

	zproxy_stats_listener_inc_waf(stream->http_state);
	if (modsec_transaction->m_it.url != nullptr) {
		resp = http_manager::replyRedirect(modsec_transaction->m_it.status,
			modsec_transaction->m_it.url, *stream);
	} else {
		auto code = static_cast<http::Code>(modsec_transaction->m_it.status);
		resp = http_manager::replyError(
			stream,
			code,
			http_info::http_status_code_strings.at(code),
			stream->listener_config->runtime.errwaf_msg);
	}

	return resp;
}

bool Waf::Stream::checkRequestHeaders(HttpStream *stream)
{
	if (!waf_enable)
		return WAF_PASS;

	std::string httpVersion = stream->request.getHttpVersion();
	std::string httpMethod(stream->request.method, stream->request.method_len);

	resetTransaction();
	modsecurity::intervention::reset(&modsec_transaction->m_it);

	modsec_transaction->processConnection(stream->client_addr.data(), stream->client_port,
			stream->listener_config->address, stream->listener_config->port);
	modsec_transaction->processURI(stream->request.path.data(), httpMethod.data(), httpVersion.data());

	for (int i = 0; i < static_cast<int>(stream->request.num_headers); i++) {
		auto name = reinterpret_cast<unsigned char *>(
			const_cast<char *>(stream->request.headers[i].name));
		auto value = reinterpret_cast<unsigned char *>(
			const_cast<char *>(stream->request.headers[i].value));
		modsec_transaction->addRequestHeader(
			name, stream->request.headers[i].name_len, value,
			stream->request.headers[i].value_len);
	}
	modsec_transaction->processRequestHeaders();

	if (modsec_transaction->m_it.log != nullptr) {
		streamLogWaf(stream, "%s", modsec_transaction->m_it.log);
	}

	return (modsec_transaction->m_it.disruptive);
}

bool Waf::Stream::checkRequestBody(HttpStream *stream)
{
	if (!waf_enable)
		return WAF_PASS;

	modsecurity::intervention::reset(&modsec_transaction->m_it);

	if (stream->request.message_length > 0) {
		modsec_transaction->appendRequestBody(
			(unsigned char *)stream->request.message,
			stream->request.message_length);
	}

	if (stream->response.expectBody() == false)
		modsec_transaction->processRequestBody();

	if (modsec_transaction->m_it.log != nullptr)
		streamLogWaf(stream, "%s", modsec_transaction->m_it.log);

	return (modsec_transaction->m_it.disruptive);
}

bool Waf::Stream::checkResponseHeaders(HttpStream *stream)
{
	if (!waf_enable)
		return WAF_PASS;

	modsecurity::intervention::reset(&modsec_transaction->m_it);
	for (int i = 0; i < static_cast<int>(stream->response.num_headers);
	     i++) {
		if (stream->response.headers[i].header_off)
			continue;
		auto name = reinterpret_cast<unsigned char *>(
			const_cast<char *>(stream->response.headers[i].name));
		auto value = reinterpret_cast<unsigned char *>(
			const_cast<char *>(stream->response.headers[i].value));
		modsec_transaction->addResponseHeader(
			name, stream->response.headers[i].name_len, value,
			stream->response.headers[i].value_len);
	}

	modsec_transaction->processResponseHeaders(
		stream->response.http_status_code, stream->response.getHttpVersion());

	if (modsec_transaction->m_it.log != nullptr)
		streamLogWaf(stream, "%s", modsec_transaction->m_it.log);

	return (modsec_transaction->m_it.disruptive);
}

bool Waf::Stream::checkResponseBody(HttpStream *stream)
{
	if (!waf_enable)
		return WAF_PASS;

	if (stream->response.message_length > 0) {
		modsec_transaction->appendResponseBody(
			reinterpret_cast<unsigned char *>(stream->response.message),
			stream->response.message_length);
	}

	if (stream->response.expectBody() == false)
		modsec_transaction->processResponseBody();

	if (modsec_transaction->m_it.log != nullptr)
		streamLogWaf(stream, "%s", modsec_transaction->m_it.log);

	return (modsec_transaction->m_it.disruptive);
}
