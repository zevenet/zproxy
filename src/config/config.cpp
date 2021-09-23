/*
 * Pound - the reverse-proxy load-balancer
 * Copyright (C) 2002-2010 Apsis GmbH
 * Copyright (C) 2019-today ZEVENET SL, Sevilla (Spain)
 *
 * This file is part of Pound.
 *
 * Pound is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3 of the License, or
 * (at your option) any later version.
 *
 * Pound is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 * Contact information:
 * Apsis GmbH
 * P.O.Box
 * 8707 Uetikon am See
 * Switzerland
 * EMail: roseg@apsis.ch
 */
#undef _SYS_SYSLOG_H // TODO:: hack to avoid facilitynames redefinition, should
// be fixed
#define SYSLOG_NAMES
#define NULL 0
#include <syslog.h>
#undef NULL
#undef SYSLOG_NAMES
#include "config.h"
#include <iostream>
#include "regex_manager.h"
#include "../../zcutils/zcutils.h"
#include "../../zcutils/zcu_network.h"

#ifdef WAF_ENABLED
#include <modsecurity/rules.h>
#endif
Config::Config(bool _abort_on_error)
	: clnt_to(10), be_to(15), be_connto(15), dynscale(0), ignore_case(0),
	  EC_nid(0), // NID_X9_62_prime256v1;
	  listener_id_counter(0), abort_on_error(_abort_on_error), log_level(5),
	  def_facility(LOG_DAEMON), ctrl_mode(-1), log_facility(-1),
	  print_log(0)
{
}

Config::~Config()
{
}

void Config::parse_file()
{
	char lin[ZCU_DEF_BUFFER_SIZE];
	std::shared_ptr<ServiceConfig> svc{ nullptr };
	std::shared_ptr<ListenerConfig> lstn{ nullptr };
	int i;
	regmatch_t matches[5];

	while (conf_fgets(lin, ZCU_DEF_BUFFER_SIZE)) {
		if (strlen(lin) > 0 && lin[strlen(lin) - 1] == '\n')
			lin[strlen(lin) - 1] = '\0';
		if (!regexec(&regex_set::User, lin, 4, matches, 0)) {
			lin[matches[1].rm_eo] = '\0';
			user = std::string(
				lin + matches[1].rm_so,
				static_cast<size_t>(matches[1].rm_eo -
						    matches[1].rm_so));
		} else if (!regexec(&regex_set::Group, lin, 4, matches, 0)) {
			lin[matches[1].rm_eo] = '\0';
			group = std::string(
				lin + matches[1].rm_so,
				static_cast<size_t>(matches[1].rm_eo -
						    matches[1].rm_so));
		} else if (!regexec(&regex_set::Name, lin, 4, matches, 0)) {
			lin[matches[1].rm_eo] = '\0';
			name = std::string(
				lin + matches[1].rm_so,
				static_cast<size_t>(matches[1].rm_eo -
						    matches[1].rm_so));
			zcu_log_set_prefix(const_cast<char *>(name.data()));
		} else if (!regexec(&regex_set::RootJail, lin, 4, matches, 0)) {
			lin[matches[1].rm_eo] = '\0';
			root_jail = std::string(
				lin + matches[1].rm_so,
				static_cast<size_t>(matches[1].rm_eo -
						    matches[1].rm_so));
		} else if (!regexec(&regex_set::DHParams, lin, 4, matches, 0)) {
			lin[matches[1].rm_eo] = '\0';
			DH *dh = global::SslHelper::load_dh_params(
				lin + matches[1].rm_so);
			if (!dh)
				conf_err(
					"DHParams config: could not load file");
			DHCustom_params = dh;
		} else if (!regexec(&regex_set::Daemon, lin, 4, matches, 0)) {
			daemonize = atoi(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::Threads, lin, 4, matches, 0)) {
			numthreads = atoi(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::ThreadModel, lin, 4, matches,
				    0)) { // ignore
			// threadpool = ((lin[matches[1].rm_so] | 0x20) == 'p'); /* 'pool' */ //
		} else if (!regexec(&regex_set::LogFacility, lin, 4, matches,
				    0)) {
			lin[matches[1].rm_eo] = '\0';
			if (lin[matches[1].rm_so] == '-')
				def_facility = -1;
			else
				for (i = 0; facilitynames[i].c_name; i++)
					if (!strcmp(facilitynames[i].c_name,
						    lin + matches[1].rm_so)) {
						def_facility =
							facilitynames[i].c_val;
						break;
					}
		} else if (!regexec(&regex_set::Grace, lin, 4, matches, 0)) {
			grace = atoi(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::LogLevel, lin, 4, matches, 0)) {
			log_level = atoi(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::Client, lin, 4, matches, 0)) {
			clnt_to = atoi(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::Alive, lin, 4, matches, 0)) {
			alive_to = atoi(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::DynScale, lin, 4, matches, 0)) {
			dynscale = atoi(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::TimeOut, lin, 4, matches, 0)) {
			be_to = atoi(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::ConnTO, lin, 4, matches, 0)) {
			be_connto = atoi(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::Ignore100continue, lin, 4,
				    matches, 0)) {
			ignore_100 = atoi(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::IgnoreCase, lin, 4, matches,
				    0)) {
			ignore_case = atoi(lin + matches[1].rm_so);
#if OPENSSL_VERSION_NUMBER >= 0x0090800fL
#ifndef OPENSSL_NO_ECDH
		} else if (!regexec(&regex_set::ECDHCurve, lin, 4, matches,
				    0)) {
			lin[matches[1].rm_eo] = '\0';
			if ((EC_nid = OBJ_sn2nid(lin + matches[1].rm_so)) == 0)
				conf_err(
					"ECDHCurve config: invalid curve name");
#endif
#endif

		} else if (!regexec(&regex_set::SSLEngine, lin, 4, matches,
				    0)) {
			lin[matches[1].rm_eo] = '\0';
			ENGINE_load_builtin_engines();
			engine_id = std::string(
				lin + matches[1].rm_so,
				static_cast<size_t>(matches[1].rm_eo -
						    matches[1].rm_so));
		} else if (!regexec(&regex_set::Control, lin, 4, matches, 0)) {
			if (!ctrl_name.empty())
				conf_err("Control multiply defined - aborted");
			lin[matches[1].rm_eo] = '\0';
			ctrl_name = std::string(
				lin + matches[1].rm_so,
				static_cast<size_t>(matches[1].rm_eo -
						    matches[1].rm_so));
		} else if (!regexec(&regex_set::ControlIP, lin, 4, matches,
				    0)) {
			lin[matches[1].rm_eo] = '\0';
			ctrl_ip = std::string(
				lin + matches[1].rm_so,
				static_cast<size_t>(matches[1].rm_eo -
						    matches[1].rm_so));
		} else if (!regexec(&regex_set::ControlPort, lin, 4, matches,
				    0)) {
			lin[matches[1].rm_eo] = '\0';
			ctrl_port = atoi(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::ControlUser, lin, 4, matches,
				    0)) {
			lin[matches[1].rm_eo] = '\0';
			ctrl_user = std::string(
				lin + matches[1].rm_so,
				static_cast<size_t>(matches[1].rm_eo -
						    matches[1].rm_so));
		} else if (!regexec(&regex_set::ControlGroup, lin, 4, matches,
				    0)) {
			lin[matches[1].rm_eo] = '\0';
			ctrl_group = std::string(
				lin + matches[1].rm_so,
				static_cast<size_t>(matches[1].rm_eo -
						    matches[1].rm_so));
		} else if (!regexec(&regex_set::ControlMode, lin, 4, matches,
				    0)) {
			lin[matches[1].rm_eo] = '\0';
			ctrl_mode =
				std::strtol(lin + matches[1].rm_so, nullptr, 8);
			if (errno == ERANGE || errno == EINVAL) {
				fprintf(stderr,
					"line %d: ControlMode config: %s - aborted",
					*n_lin, strerror(errno));
				exit(1);
			}
		} else if (!regexec(&regex_set::ListenHTTP, lin, 4, matches,
				    0)) {
			if (listeners == nullptr)
				listeners = parse_HTTP();
			else {
				for (lstn = listeners; lstn->next;
				     lstn = lstn->next)
					;
				lstn->next = parse_HTTP();
			}
		} else if (!regexec(&regex_set::ListenHTTPS, lin, 4, matches,
				    0)) {
			if (listeners == nullptr)
				listeners = parse_HTTPS();
			else {
				for (lstn = listeners; lstn->next;
				     lstn = lstn->next)
					;
				lstn->next = parse_HTTPS();
			}
		} else if (!regexec(&regex_set::Service, lin, 4, matches, 0)) {
			if (services == nullptr)
				services = parseService(nullptr);
			else {
				for (svc = services; svc->next; svc = svc->next)
					;
				svc->next = parseService(nullptr);
			}
		} else if (!regexec(&regex_set::ServiceName, lin, 4, matches,
				    0)) {
			lin[matches[1].rm_eo] = '\0';
			if (services == nullptr)
				services = parseService(lin + matches[1].rm_so);
			else {
				for (svc = services; svc->next; svc = svc->next)
					;
				svc->next =
					parseService(lin + matches[1].rm_so);
			}
		} else if (!regexec(&regex_set::Anonymise, lin, 4, matches,
				    0)) {
			anonymise = 1;
#ifdef CACHE_ENABLED
		} else if (!regexec(&regex_set::CacheThreshold, lin, 2, matches,
				    0)) {
			int threshold = atoi(lin + matches[1].rm_so);
			if (threshold <= 0 || threshold > 99)
				conf_err(
					"Invalid value for cache threshold (CacheThreshold), must be "
					"between 1 and 99 (%)");
			this->cache_thr = threshold;
		} else if (!regexec(&regex_set::CacheRamSize, lin, 3, matches,
				    0)) {
			long size = atol(lin + matches[1].rm_so);
			if (matches[2].rm_so != matches[0].rm_eo - 1) {
				char *size_modifier = nullptr;
				size_modifier = strdup(lin + matches[2].rm_so);
				// Apply modifier
				if (*size_modifier == 'K' ||
				    *size_modifier == 'k')
					size = size * 1024;
				else if (*size_modifier == 'M' ||
					 *size_modifier == 'm')
					size = size * 1024 * 1024;
				else if (*size_modifier == 'G' ||
					 *size_modifier == 'g')
					size = size * 1024 * 1024 * 1024;
			}
			cache_s = size;
		} else if (!regexec(&regex_set::CacheRamPath, lin, 2, matches,
				    0)) {
			cache_ram_path = std::string(lin + matches[1].rm_so,
						     matches[1].rm_eo -
							     matches[1].rm_so);
		} else if (!regexec(&regex_set::CacheDiskPath, lin, 2, matches,
				    0)) {
			cache_disk_path = std::string(lin + matches[1].rm_so,
						      matches[1].rm_eo -
							      matches[1].rm_so);
#endif
		} else {
			conf_err("unknown directive - aborted");
		}
	}
	return;
}

bool Config::init(const global::StartOptions &start_options)
{
	conf_file_name = start_options.conf_file_name.empty() ?
				       F_CONF :
				       start_options.conf_file_name;
	pid_name = start_options.pid_file_name.empty() ?
				 F_PID :
				 start_options.pid_file_name;

	// init configuration file lists.
	f_name[0] = std::string(conf_file_name);
	if ((f_in[0] = fopen(conf_file_name.data(), "rt")) == nullptr) {
		fprintf(stderr, "can't open open %s", conf_file_name.data());
		return false;
	}
	n_lin[0] = 0;
	cur_fin = 0;

	DHCustom_params = nullptr;
	numthreads = 0;
	alive_to = 30;
	daemonize = 1;
	grace = 30;
	ignore_100 = 1;
	services = nullptr;
	listeners = nullptr;
	zcu_log_set_prefix("");
#ifdef CACHE_ENABLED
	cache_s = 0;
	cache_thr = 0;
#endif
	parse_file();

	if (start_options.check_only) {
		fprintf(stdout, "Config file %s is OK\n",
			conf_file_name.data());
		return true;
	}

	if (start_options.disable_daemon) {
		daemonize = 0;
	}

	if (listeners == nullptr) {
		fprintf(stderr, "no listeners defined - aborted");
		return false;
	}

	/* set the facility only here to ensure the syslog gets opened if necessary
	 */
	log_facility = def_facility;
	return !found_parse_error;
}

std::string Config::file2str(const char *fname)
{
	struct stat st {
	};
	if (stat(fname, &st))
		conf_err("can't stat Err file - aborted");
	std::ifstream t(fname);
	std::string res((std::istreambuf_iterator<char>(t)),
			std::istreambuf_iterator<char>());
	return res;
}

void Config::parseReplaceHeader(char *lin, regmatch_t *matches,
				ReplaceHeader **replace_header_request,
				ReplaceHeader **replace_header_response)
{
	lin[matches[1].rm_eo] = '\0';
	lin[matches[2].rm_eo] = '\0';
	lin[matches[3].rm_eo] = '\0';
	lin[matches[4].rm_eo] = '\0';
	auto type_ = std::string(lin + matches[1].rm_so);
	auto name_ = std::string(lin + matches[2].rm_so);
	auto match_ = std::string(lin + matches[3].rm_so);
	auto replace_ = std::string(lin + matches[4].rm_so);
	ReplaceHeader *current{ nullptr };

	if (!strcasecmp(type_.data(), "Request")) {
		if (*replace_header_request) {
			for (current = *replace_header_request; current->next;
			     current = current->next)
				;
			current->next = new ReplaceHeader();
			current = current->next;
		} else {
			*replace_header_request = new ReplaceHeader();
			current = *replace_header_request;
		}
	} else if (!strcasecmp(type_.data(), "Response")) {
		if (*replace_header_response) {
			for (current = *replace_header_response; current->next;
			     current = current->next)
				;
			current->next = new ReplaceHeader();
			current = current->next;
		} else {
			*replace_header_response = new ReplaceHeader();
			current = *replace_header_response;
		}
	} else {
		conf_err("ReplaceHeader type not specified");
	}

	if (::regcomp(&current->name, name_.data(),
		      REG_ICASE | REG_NEWLINE | REG_EXTENDED))
		conf_err("Error compiling Name regex ");
	if (::regcomp(&current->match, match_.data(),
		      REG_ICASE | REG_NEWLINE | REG_EXTENDED))
		conf_err("Error compiling Match regex ");
	current->replace = replace_;
}

std::shared_ptr<ListenerConfig> Config::parse_HTTP()
{
	char lin[ZCU_DEF_BUFFER_SIZE];
	auto res = std::make_shared<ListenerConfig>();
	std::shared_ptr<ServiceConfig> svc;
	MATCHER *m;
	int has_addr, has_port;
	regmatch_t matches[5];

	res->name = name;
	res->id = listener_id_counter++;
	res->to = clnt_to;
	res->rewr_loc = 1;
#if WAF_ENABLED
	res->errwaf = "The request was rejected by the server.";
#endif
	res->errreq = "Invalid request.";
	res->err414 = "Request URI is too long.";
	res->err500 =
		"An internal server error occurred. Please try again later.";
	res->err501 = "This method may not be used.";
	res->err503 = "The service is not available. Please try again later.";
	res->log_level = log_level;
	res->alive_to = alive_to;
	res->ignore100continue = ignore_100;

	res->ssl_forward_sni_server_name = false;
	if (regcomp(&res->verb, xhttp[0],
		    REG_ICASE | REG_NEWLINE | REG_EXTENDED))
		conf_err("xHTTP bad default pattern - aborted");
	has_addr = has_port = 0;
	while (conf_fgets(lin, ZCU_DEF_BUFFER_SIZE)) {
		if (strlen(lin) > 0 && lin[strlen(lin) - 1] == '\n')
			lin[strlen(lin) - 1] = '\0';
		if (!regexec(&regex_set::Address, lin, 4, matches, 0)) {
			lin[matches[1].rm_eo] = '\0';
			addrinfo addr{};
			if (zcu_net_get_host(lin + matches[1].rm_so, &addr,
					     PF_UNSPEC))
				conf_err("Unknown Listener address");
			if (addr.ai_family != AF_INET &&
			    addr.ai_family != AF_INET6)
				conf_err("Unknown Listener address family");
			free(addr.ai_addr);
			has_addr = 1;
			res->address = lin + matches[1].rm_so;
		} else if (!regexec(&regex_set::Name, lin, 4, matches, 0)) {
			lin[matches[1].rm_eo] = '\0';
			res->name = std::string(
				lin + matches[1].rm_so,
				static_cast<size_t>(matches[1].rm_eo -
						    matches[1].rm_so));
		} else if (!regexec(&regex_set::Port, lin, 4, matches, 0)) {
			has_port = 1;
			lin[matches[1].rm_eo] = '\0';
			res->port = std::atoi(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::Disabled, lin, 4, matches, 0)) {
			res->disabled = atoi(lin + matches[1].rm_so) == 1;
		} else if (!regexec(&regex_set::xHTTP, lin, 4, matches, 0)) {
			int n;

			n = atoi(lin + matches[1].rm_so);
			regfree(&res->verb);
			if (regcomp(&res->verb, xhttp[n],
				    REG_ICASE | REG_NEWLINE | REG_EXTENDED))
				conf_err("xHTTP bad pattern - aborted");
		} else if (!regexec(&regex_set::Client, lin, 4, matches, 0)) {
			res->to = atoi(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::CheckURL, lin, 4, matches, 0)) {
			if (res->has_pat)
				conf_err("CheckURL multiple pattern - aborted");
			lin[matches[1].rm_eo] = '\0';
			if (regcomp(&res->url_pat, lin + matches[1].rm_so,
				    REG_NEWLINE | REG_EXTENDED |
					    (ignore_case ? REG_ICASE : 0)))
				conf_err("CheckURL bad pattern - aborted");
			res->has_pat = 1;
#if WAF_ENABLED
		} else if (!regexec(&regex_set::ErrWAF, lin, 4, matches, 0)) {
			lin[matches[1].rm_eo] = '\0';
			res->errwaf = file2str(lin + matches[1].rm_so);
#endif
		} else if (!regexec(&regex_set::Err414, lin, 4, matches, 0)) {
			lin[matches[1].rm_eo] = '\0';
			res->err414 = file2str(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::Err500, lin, 4, matches, 0)) {
			lin[matches[1].rm_eo] = '\0';
			res->err500 = file2str(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::Err501, lin, 4, matches, 0)) {
			lin[matches[1].rm_eo] = '\0';
			res->err501 = file2str(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::Err503, lin, 4, matches, 0)) {
			lin[matches[1].rm_eo] = '\0';
			res->err503 = file2str(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::MaxRequest, lin, 4, matches,
				    0)) {
			res->max_req = atoll(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::RewriteLocation, lin, 4,
				    matches, 0)) {
			res->rewr_loc = std::atoi(lin + matches[1].rm_so);
			res->rewr_loc_path =
				(matches[1].rm_eo <= matches[2].rm_so) ? 1 : 0;
		} else if (!regexec(&regex_set::AddRequestHeader, lin, 4,
				    matches, 0)) {
			parseAddHeader(&res->add_head_req, lin, matches);
		} else if (!regexec(&regex_set::AddResponseHeader, lin, 4,
				    matches, 0)) {
			parseAddHeader(&res->add_head_resp, lin, matches);
		} else if (!regexec(&regex_set::RemoveRequestHeader, lin, 4,
				    matches, 0)) {
			parseRemoveHeader(&res->head_off_req, lin, matches);
		} else if (!regexec(&regex_set::RemoveResponseHeader, lin, 4,
				    matches, 0)) {
			parseRemoveHeader(&res->head_off_resp, lin, matches);
		} else if (!regexec(&regex_set::RewriteDestination, lin, 4,
				    matches, 0)) {
			res->rewr_dest = atoi(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::RewriteHost, lin, 4, matches,
				    0)) {
			res->rewr_host = atoi(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::LogLevel, lin, 4, matches, 0)) {
			res->log_level = atoi(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::SSLConfigFile, lin, 4, matches,
				    0)) {
			conf_err(
				"SSLConfigFile directive not allowed in HTTP listeners.");
		} else if (!regexec(&regex_set::SSLConfigSection, lin, 4,
				    matches, 0)) {
			conf_err(
				"SSLConfigSection directive not allowed in HTTP listeners.");
		} else if (!regexec(&regex_set::ForceHTTP10, lin, 4, matches,
				    0)) {
			m = new MATCHER();
			m->next = res->forcehttp10;
			res->forcehttp10 = m;
			lin[matches[1].rm_eo] = '\0';
			if (regcomp(&m->pat, lin + matches[1].rm_so,
				    REG_ICASE | REG_NEWLINE | REG_EXTENDED))
				conf_err("ForceHTTP10 bad pattern");
		} else if (!regexec(&regex_set::Service, lin, 4, matches, 0)) {
			if (res->services == nullptr) {
				res->services = parseService(nullptr);
				if (res->services->sts >= 0)
					conf_err(
						"StrictTransportSecurity not allowed in HTTP listener - "
						"aborted");
			} else {
				for (svc = res->services; svc->next;
				     svc = svc->next)
					;
				svc->next = parseService(nullptr);
				if (svc->next->sts >= 0)
					conf_err(
						"StrictTransportSecurity not allowed in HTTP listener - "
						"aborted");
			}
		} else if (!regexec(&regex_set::ServiceName, lin, 4, matches,
				    0)) {
			lin[matches[1].rm_eo] = '\0';
			if (res->services == nullptr)
				res->services =
					parseService(lin + matches[1].rm_so);
			else {
				for (svc = res->services; svc->next;
				     svc = svc->next)
					;
				svc->next =
					parseService(lin + matches[1].rm_so);
			}
		} else if (!regexec(&regex_set::ReplaceHeader, lin, 5, matches,
				    0)) {
			parseReplaceHeader(lin, matches,
					   &res->replace_header_request,
					   &res->replace_header_response);
		} else if (!regexec(&regex_set::End, lin, 4, matches, 0)) {
			if (!has_addr || !has_port)
				conf_err(
					"ListenHTTP missing Address or Port - aborted");
			return res;
#if WAF_ENABLED
		} else if (!regexec(&regex_set::WafRules, lin, 4, matches, 0)) {
			auto file = std::string(lin + matches[1].rm_so,
						matches[1].rm_eo -
							matches[1].rm_so);
			if (!res->rules) {
				res->rules =
					std::make_shared<modsecurity::Rules>();
			}
			auto err = res->rules->loadFromUri(file.data());
			if (err == -1) {
				fprintf(stderr,
					"error loading waf ruleset file %s: %s",
					file.data(),
					res->rules->getParserError().data());
				conf_err("Error loading waf ruleset");
				break;
			}
			if (!res->rules) {
				res->rules =
					std::make_shared<modsecurity::Rules>();
			}
			zcu_log_print(LOG_DEBUG, "Rules: ");
			for (int i = 0;
			     i <= modsecurity::Phases::NUMBER_OF_PHASES; i++) {
				auto rule = res->rules->getRulesForPhase(i);
				if (rule) {
					zcu_log_print(LOG_DEBUG,
						      "Phase: %d ( %d rules )",
						      i, rule->size());
					for (auto &x : *rule) {
						zcu_log_print(
							LOG_DEBUG,
							"\tRule Id: %d From %s at %d ",
							x->m_ruleId,
							x->m_fileName.data(),
							x->m_lineNumber);
					}
				}
			}
#endif
		} else {
			conf_err("unknown directive - aborted");
		}
	}

	conf_err("ListenHTTP premature EOF");
	return nullptr;
}

void Config::parseAddHeader(std::string *add_head, char *lin,
			    regmatch_t *matches)
{
	lin[matches[1].rm_eo] = '\0';
	if (add_head->empty()) {
		*add_head = std::string(lin + matches[1].rm_so,
					static_cast<size_t>(matches[1].rm_eo -
							    matches[1].rm_so));
	} else {
		*add_head += "\r\n";
		*add_head += std::string(lin + matches[1].rm_so,
					 static_cast<size_t>(matches[1].rm_eo -
							     matches[1].rm_so));
	}
}

void Config::parseRemoveHeader(MATCHER **head_off, char *lin,
			       regmatch_t *matches)
{
	MATCHER *m;

	if (*head_off) {
		for (m = *head_off; m->next; m = m->next)
			;
		if ((m->next = new MATCHER()) == nullptr)
			conf_err(
				"RemoveHeader config: out of memory - aborted");
		m = m->next;
	} else {
		if ((*head_off = new MATCHER()) == nullptr)
			conf_err(
				"RemoveHeader config: out of memory - aborted");
		m = *head_off;
	}
	memset(m, 0, sizeof(MATCHER));
	lin[matches[1].rm_eo] = '\0';
	if (regcomp(&m->pat, lin + matches[1].rm_so,
		    REG_ICASE | REG_NEWLINE | REG_EXTENDED))
		conf_err("RemoveHeader bad pattern - aborted");
}

std::shared_ptr<ListenerConfig> Config::parse_HTTPS()
{
	char lin[ZCU_DEF_BUFFER_SIZE];
	auto res = std::make_shared<ListenerConfig>();
	std::shared_ptr<ServiceConfig> svc;
	MATCHER *m;
	int has_addr, has_port, has_other;
	unsigned long ssl_op_enable, ssl_op_disable;
	std::shared_ptr<SNI_CERTS_CTX> pc;
	regmatch_t matches[5];
	bool openssl_file_exists = false;

	ssl_op_enable = SSL_OP_ALL;
#ifdef SSL_OP_NO_COMPRESSION
	ssl_op_enable |= SSL_OP_NO_COMPRESSION;
#endif
	ssl_op_disable = SSL_OP_ALLOW_UNSAFE_LEGACY_RENEGOTIATION |
			 SSL_OP_LEGACY_SERVER_CONNECT |
			 SSL_OP_DONT_INSERT_EMPTY_FRAGMENTS;

	res->to = clnt_to;
	res->rewr_loc = 1;
	res->name = name;
	res->id = listener_id_counter++;
#if WAF_ENABLED
	res->errwaf = "The request was rejected by the server.";
#endif
	res->errreq = "Invalid request.";
	res->err414 = "Request URI is too long.";
	res->err500 =
		"An internal server error occurred. Please try again later.";
	res->err501 = "This method may not be used.";
	res->err503 = "The service is not available. Please try again later.";
	res->errnossl = "Please use HTTPS.";
	res->codenossl = http::Code::BadRequest;
	res->nossl_url = "";
	res->nossl_redir = 0;
	res->allow_client_reneg = 0;
	res->log_level = log_level;
	res->alive_to = alive_to;
	res->engine_id = engine_id;
	res->ssl_forward_sni_server_name = true;
	if (regcomp(&res->verb, xhttp[0],
		    REG_ICASE | REG_NEWLINE | REG_EXTENDED))
		conf_err("xHTTP bad default pattern - aborted");
	has_addr = has_port = has_other = 0;
	while (conf_fgets(lin, ZCU_DEF_BUFFER_SIZE)) {
		if (strlen(lin) > 0 && lin[strlen(lin) - 1] == '\n')
			lin[strlen(lin) - 1] = '\0';
		if (!regexec(&regex_set::Address, lin, 4, matches, 0)) {
			lin[matches[1].rm_eo] = '\0';
			addrinfo addr{};
			if (zcu_net_get_host(lin + matches[1].rm_so, &addr,
					     PF_UNSPEC))
				conf_err("Unknown Listener address");
			if (addr.ai_family != AF_INET &&
			    addr.ai_family != AF_INET6)
				conf_err("Unknown Listener address family");
			free(addr.ai_addr);
			has_addr = 1;
			res->address = lin + matches[1].rm_so;
#if WAF_ENABLED
		} else if (!regexec(&regex_set::WafRules, lin, 4, matches, 0)) {
			auto file = std::string(lin + matches[1].rm_so,
						matches[1].rm_eo -
							matches[1].rm_so);
			if (!res->rules) {
				res->rules =
					std::make_shared<modsecurity::Rules>();
			}
			auto err = res->rules->loadFromUri(file.data());
			if (err == -1) {
				fprintf(stderr,
					"error loading waf ruleset file %s: %s",
					file.data(),
					res->rules->getParserError().data());
				conf_err("Error loading waf ruleset");
				break;
			}
			zcu_log_print(LOG_DEBUG, "Rules: ");
			for (int i = 0;
			     i <= modsecurity::Phases::NUMBER_OF_PHASES; i++) {
				auto rule = res->rules->getRulesForPhase(i);
				if (rule) {
					zcu_log_print(LOG_DEBUG,
						      "Phase: %d ( %d rules )",
						      i, rule->size());
					for (auto &x : *rule) {
						zcu_log_print(
							LOG_DEBUG,
							"\tRule Id: %d From %s at %d ",
							x->m_ruleId,
							x->m_fileName.data(),
							x->m_lineNumber);
					}
				}
			}
#endif
		} else if (!regexec(&regex_set::Name, lin, 4, matches, 0)) {
			lin[matches[1].rm_eo] = '\0';
			res->name = std::string(
				lin + matches[1].rm_so,
				static_cast<size_t>(matches[1].rm_eo -
						    matches[1].rm_so));
		} else if (!regexec(&regex_set::Port, lin, 4, matches, 0)) {
			lin[matches[1].rm_eo] = '\0';
			has_port = 1;
			res->port = atoi(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::xHTTP, lin, 4, matches, 0)) {
			int n;

			n = atoi(lin + matches[1].rm_so);
			regfree(&res->verb);
			if (regcomp(&res->verb, xhttp[n],
				    REG_ICASE | REG_NEWLINE | REG_EXTENDED))
				conf_err("xHTTP bad pattern - aborted");
		} else if (!regexec(&regex_set::Client, lin, 4, matches, 0)) {
			res->to = atoi(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::Disabled, lin, 4, matches, 0)) {
			res->disabled = atoi(lin + matches[1].rm_so) == 1;
		} else if (!regexec(&regex_set::CheckURL, lin, 4, matches, 0)) {
			if (res->has_pat)
				conf_err("CheckURL multiple pattern - aborted");
			lin[matches[1].rm_eo] = '\0';
			if (regcomp(&res->url_pat, lin + matches[1].rm_so,
				    REG_NEWLINE | REG_EXTENDED |
					    (ignore_case ? REG_ICASE : 0)))
				conf_err("CheckURL bad pattern - aborted");
			res->has_pat = 1;
		} else if (!regexec(&regex_set::Err414, lin, 4, matches, 0)) {
			lin[matches[1].rm_eo] = '\0';
			res->err414 = file2str(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::Err500, lin, 4, matches, 0)) {
			lin[matches[1].rm_eo] = '\0';
			res->err500 = file2str(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::Err501, lin, 4, matches, 0)) {
			lin[matches[1].rm_eo] = '\0';
			res->err501 = file2str(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::Err503, lin, 4, matches, 0)) {
			lin[matches[1].rm_eo] = '\0';
			res->err503 = file2str(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::ErrNoSsl, lin, 4, matches, 0)) {
			res->codenossl = http::Code::BadRequest;
			if (matches[1].rm_eo != matches[1].rm_so) {
				res->codenossl = static_cast<http::Code>(
					atoi(lin + matches[1].rm_so));
				if (!strcmp(http::reasonPhrase(res->codenossl),
					    "(UNKNOWN)"))
					conf_err(
						"The http code for ErrNoSsl is not valid - aborted");
			}
			lin[matches[2].rm_eo] = '\0';
			res->errnossl = file2str(lin + matches[2].rm_so);
#if WAF_ENABLED
		} else if (!regexec(&regex_set::ErrWAF, lin, 4, matches, 0)) {
			lin[matches[1].rm_eo] = '\0';
			res->errwaf = file2str(lin + matches[1].rm_so);
#endif
		} else if (!regexec(&regex_set::NoSslRedirect, lin, 4, matches,
				    0)) {
			res->nossl_redir = 302;
			if (matches[1].rm_eo != matches[1].rm_so)
				res->nossl_redir = atoi(lin + matches[1].rm_so);
			lin[matches[2].rm_eo] = '\0';
			res->nossl_url = std::string(
				lin + matches[2].rm_so,
				static_cast<size_t>(matches[2].rm_eo -
						    matches[2].rm_so));
			if (regexec(&regex_set::LOCATION, res->nossl_url.data(),
				    4, matches, 0))
				conf_err("Redirect bad URL - aborted");
			if ((matches[3].rm_eo - matches[3].rm_so) ==
			    1) /* the path is a single '/', so remove it */
				res->nossl_url.data()[matches[3].rm_so] = '\0';
			if (strstr(res->nossl_url.c_str(), MACRO::VHOST_STR))
				conf_err("The macro cannot be used here");
		} else if (!regexec(&regex_set::MaxRequest, lin, 4, matches,
				    0)) {
			res->max_req = atoll(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::ForwardSNI, lin, 4, matches,
				    0)) {
			res->ssl_forward_sni_server_name =
				std::atoi(lin + matches[1].rm_so) == 1;
		} else if (!regexec(&regex_set::RewriteLocation, lin, 4,
				    matches, 0)) {
			res->rewr_loc = std::atoi(lin + matches[1].rm_so);
			res->rewr_loc_path =
				(matches[1].rm_eo <= matches[2].rm_so) ? 1 : 0;
		} else if (!regexec(&regex_set::AddRequestHeader, lin, 4,
				    matches, 0)) {
			parseAddHeader(&res->add_head_req, lin, matches);
		} else if (!regexec(&regex_set::AddResponseHeader, lin, 4,
				    matches, 0)) {
			parseAddHeader(&res->add_head_resp, lin, matches);
		} else if (!regexec(&regex_set::RemoveRequestHeader, lin, 4,
				    matches, 0)) {
			parseRemoveHeader(&res->head_off_req, lin, matches);
		} else if (!regexec(&regex_set::RemoveResponseHeader, lin, 4,
				    matches, 0)) {
			parseRemoveHeader(&res->head_off_resp, lin, matches);
		} else if (!regexec(&regex_set::RewriteDestination, lin, 4,
				    matches, 0)) {
			res->rewr_dest = atoi(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::RewriteHost, lin, 4, matches,
				    0)) {
			res->rewr_host = atoi(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::LogLevel, lin, 4, matches, 0)) {
			res->log_level = atoi(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::Cert, lin, 4, matches, 0)) {
			lin[matches[1].rm_eo] = '\0';
			load_cert(has_other, res, lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::CertDir, lin, 4, matches, 0)) {
			lin[matches[1].rm_eo] = '\0';
			load_certdir(has_other, res, lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::ClientCert, lin, 4, matches,
				    0)) {
			has_other = 1;
			if (res->ctx == nullptr)
				conf_err(
					"ClientCert may only be used after Cert - aborted");
			switch (res->clnt_check =
					atoi(lin + matches[1].rm_so)) {
			case 0:
				/* don't ask */
				for (pc = res->ctx; pc; pc = pc->next)
					SSL_CTX_set_verify(pc->ctx.get(),
							   SSL_VERIFY_NONE,
							   nullptr);
				break;
			case 1:
				/* ask but OK if no client certificate */
				for (pc = res->ctx; pc; pc = pc->next) {
					SSL_CTX_set_verify(
						pc->ctx.get(),
						SSL_VERIFY_PEER |
							SSL_VERIFY_CLIENT_ONCE,
						nullptr);
					SSL_CTX_set_verify_depth(
						pc->ctx.get(),
						atoi(lin + matches[2].rm_so));
				}
				break;
			case 2:
				/* ask and fail if no client certificate */
				for (pc = res->ctx; pc; pc = pc->next) {
					SSL_CTX_set_verify(
						pc->ctx.get(),
						SSL_VERIFY_PEER |
							SSL_VERIFY_FAIL_IF_NO_PEER_CERT,
						nullptr);
					SSL_CTX_set_verify_depth(
						pc->ctx.get(),
						atoi(lin + matches[2].rm_so));
				}
				break;
			case 3:
				/* ask but do not verify client certificate */
				for (pc = res->ctx; pc; pc = pc->next) {
					SSL_CTX_set_verify(
						pc->ctx.get(),
						SSL_VERIFY_PEER |
							SSL_VERIFY_CLIENT_ONCE,
						global::SslHelper::
							verifyCertificate_OK);
					SSL_CTX_set_verify_depth(
						pc->ctx.get(),
						atoi(lin + matches[2].rm_so));
				}
				break;
			}
		} else if (!regexec(&regex_set::DisableProto, lin, 4, matches,
				    0)) {
			lin[matches[1].rm_eo] = '\0';
			if (strcasecmp(lin + matches[1].rm_so, "SSLv2") == 0)
				ssl_op_enable |= SSL_OP_NO_SSLv2;
			else if (strcasecmp(lin + matches[1].rm_so, "SSLv3") ==
				 0)
				ssl_op_enable |=
					SSL_OP_NO_SSLv2 | SSL_OP_NO_SSLv3;
#ifdef SSL_OP_NO_TLSv1
			else if (strcasecmp(lin + matches[1].rm_so, "TLSv1") ==
				 0)
				ssl_op_enable |= SSL_OP_NO_SSLv2 |
						 SSL_OP_NO_SSLv3 |
						 SSL_OP_NO_TLSv1;
#endif
#ifdef SSL_OP_NO_TLSv1_1
			else if (strcasecmp(lin + matches[1].rm_so,
					    "TLSv1_1") == 0)
				ssl_op_enable |=
					SSL_OP_NO_SSLv2 | SSL_OP_NO_SSLv3 |
					SSL_OP_NO_TLSv1 | SSL_OP_NO_TLSv1_1;
#endif
#ifdef SSL_OP_NO_TLSv1_2
			else if (strcasecmp(lin + matches[1].rm_so,
					    "TLSv1_2") == 0)
				ssl_op_enable |=
					SSL_OP_NO_SSLv2 | SSL_OP_NO_SSLv3 |
					SSL_OP_NO_TLSv1 | SSL_OP_NO_TLSv1_1 |
					SSL_OP_NO_TLSv1_2;
#endif
#ifdef SSL_OP_NO_TLSv1_3
			else if (strcasecmp(lin + matches[1].rm_so,
					    "TLSv1_3") == 0)
				ssl_op_enable |= SSL_OP_NO_TLSv1_3;
#endif
#ifndef OPENSSL_NO_ECDH
		} else if (!regexec(&regex_set::ECDHCurve, lin, 4, matches,
				    0)) {
			if (res->ctx == nullptr)
				conf_err(
					"BackEnd ECDHCurve can only be used after HTTPS - aborted");
			lin[matches[1].rm_eo] = '\0';
			if ((res->ecdh_curve_nid =
				     OBJ_sn2nid(lin + matches[1].rm_so)) == 0)
				conf_err(
					"ECDHCurve config: invalid curve name");
#endif
		} else if (!regexec(&regex_set::SSLAllowClientRenegotiation,
				    lin, 4, matches, 0)) {
			res->allow_client_reneg = atoi(lin + matches[1].rm_so);
			if (res->allow_client_reneg == 2) {
				ssl_op_enable |=
					SSL_OP_ALLOW_UNSAFE_LEGACY_RENEGOTIATION;
				ssl_op_disable &=
					~SSL_OP_ALLOW_UNSAFE_LEGACY_RENEGOTIATION;
			} else {
				ssl_op_disable |=
					SSL_OP_ALLOW_UNSAFE_LEGACY_RENEGOTIATION;
				ssl_op_enable &=
					~SSL_OP_ALLOW_UNSAFE_LEGACY_RENEGOTIATION;
			}
		} else if (!regexec(&regex_set::SSLHonorCipherOrder, lin, 4,
				    matches, 0)) {
			if (std::atoi(lin + matches[1].rm_so)) {
				ssl_op_enable |=
					SSL_OP_CIPHER_SERVER_PREFERENCE;
				ssl_op_disable &=
					~SSL_OP_CIPHER_SERVER_PREFERENCE;
			} else {
				ssl_op_disable |=
					SSL_OP_CIPHER_SERVER_PREFERENCE;
				ssl_op_enable &=
					~SSL_OP_CIPHER_SERVER_PREFERENCE;
			}
		} else if (!regexec(&regex_set::Ciphers, lin, 4, matches, 0)) {
			has_other = 1;
			if (res->ctx == nullptr)
				conf_err(
					"Ciphers may only be used after Cert - aborted");
			lin[matches[1].rm_eo] = '\0';
			for (pc = res->ctx; pc; pc = pc->next)
				SSL_CTX_set_cipher_list(pc->ctx.get(),
							lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::CAlist, lin, 4, matches, 0)) {
			STACK_OF(X509_NAME) * cert_names;

			has_other = 1;
			if (res->ctx == nullptr)
				conf_err(
					"CAList may only be used after Cert - aborted");
			lin[matches[1].rm_eo] = '\0';
			if ((cert_names = SSL_load_client_CA_file(
				     lin + matches[1].rm_so)) == nullptr)
				conf_err(
					"SSL_load_client_CA_file failed - aborted");
			for (pc = res->ctx; pc; pc = pc->next)
				SSL_CTX_set_client_CA_list(pc->ctx.get(),
							   cert_names);
		} else if (!regexec(&regex_set::VerifyList, lin, 4, matches,
				    0)) {
			has_other = 1;
			if (res->ctx == nullptr)
				conf_err(
					"VerifyList may only be used after Cert - aborted");
			lin[matches[1].rm_eo] = '\0';
			for (pc = res->ctx; pc; pc = pc->next)
				if (SSL_CTX_load_verify_locations(
					    pc->ctx.get(),
					    lin + matches[1].rm_so,
					    nullptr) != 1)
					conf_err(
						"SSL_CTX_load_verify_locations failed - aborted");
		} else if (!regexec(&regex_set::SSLConfigFile, lin, 4, matches,
				    0)) {
			lin[matches[1].rm_eo] = '\0';
			res->ssl_config_file =
				std::string(lin + matches[1].rm_so);
			openssl_file_exists = true;
		} else if (!regexec(&regex_set::SSLConfigSection, lin, 4,
				    matches, 0)) {
			lin[matches[1].rm_eo] = '\0';
			res->ssl_config_section = lin + matches[1].rm_so;
		} else if (!regexec(&regex_set::CRLlist, lin, 4, matches, 0)) {
			X509_STORE *store;
			X509_LOOKUP *lookup;

			has_other = 1;
			if (res->ctx == nullptr)
				conf_err(
					"CRLlist may only be used after Cert - aborted");
			lin[matches[1].rm_eo] = '\0';
			for (pc = res->ctx; pc; pc = pc->next) {
				store = SSL_CTX_get_cert_store(pc->ctx.get());
				if ((lookup = X509_STORE_add_lookup(
					     store, X509_LOOKUP_file())) ==
				    nullptr)
					conf_err(
						"X509_STORE_add_lookup failed - aborted");
				if (X509_load_crl_file(lookup,
						       lin + matches[1].rm_so,
						       X509_FILETYPE_PEM) != 1)
					conf_err(
						"X509_load_crl_file failed - aborted");
				X509_STORE_set_flags(
					store,
					X509_V_FLAG_CRL_CHECK |
						X509_V_FLAG_CRL_CHECK_ALL);
			}
			//#else
			//        conf_err("your version of OpenSSL does not support CRL
			//        checking");
			//#endif
		} else if (!regexec(&regex_set::NoHTTPS11, lin, 4, matches,
				    0)) {
			res->noHTTPS11 = std::atoi(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::ForceHTTP10, lin, 4, matches,
				    0)) {
			m = new MATCHER();
			m->next = res->forcehttp10;
			res->forcehttp10 = m;
			lin[matches[1].rm_eo] = '\0';
			if (regcomp(&m->pat, lin + matches[1].rm_so,
				    REG_ICASE | REG_NEWLINE | REG_EXTENDED))
				conf_err("bad pattern");
		} else if (!regexec(&regex_set::SSLUncleanShutdown, lin, 4,
				    matches, 0)) {
			if ((m = new MATCHER()) == nullptr)
				conf_err("out of memory");
			memset(m, 0, sizeof(MATCHER));
			m->next = res->ssl_uncln_shutdn;
			res->ssl_uncln_shutdn = m;
			lin[matches[1].rm_eo] = '\0';
			if (regcomp(&m->pat, lin + matches[1].rm_so,
				    REG_ICASE | REG_NEWLINE | REG_EXTENDED))
				conf_err("bad pattern");
		} else if (!regexec(&regex_set::Service, lin, 4, matches, 0)) {
			if (res->services == nullptr) {
				res->services = parseService(nullptr);
			} else {
				for (svc = res->services; svc->next;
				     svc = svc->next)
					;
				svc->next = parseService(nullptr);
			}
		} else if (!regexec(&regex_set::ServiceName, lin, 4, matches,
				    0)) {
			lin[matches[1].rm_eo] = '\0';
			if (res->services == nullptr)
				res->services =
					parseService(lin + matches[1].rm_so);
			else {
				for (svc = res->services; svc->next;
				     svc = svc->next)
					;
				svc->next =
					parseService(lin + matches[1].rm_so);
			}
		} else if (!regexec(&regex_set::ReplaceHeader, lin, 5, matches,
				    0)) {
			parseReplaceHeader(lin, matches,
					   &res->replace_header_request,
					   &res->replace_header_response);
		} else if (!regexec(&regex_set::End, lin, 4, matches, 0)) {
			if (openssl_file_exists) {
				res->ctx = std::make_shared<SNI_CERTS_CTX>();
				res->ctx->ctx = std::shared_ptr<SSL_CTX>(
					SSL_CTX_new(SSLv23_server_method()),
					&::__SSL_CTX_free);
			}
			if ((!has_addr || !has_port || res->ctx == nullptr) &&
			    !openssl_file_exists)
				conf_err(
					"ListenHTTPS missing Address, Port, SSL Config file or Certificate "
					"- aborted");
			if (!openssl_file_exists) {
				for (pc = res->ctx; pc; pc = pc->next) {
					SSL_CTX_set_app_data(pc->ctx.get(),
							     res.get());
					SSL_CTX_set_mode(
						pc->ctx.get(),
						SSL_MODE_RELEASE_BUFFERS);
					SSL_CTX_set_options(pc->ctx.get(),
							    ssl_op_enable);
					SSL_CTX_clear_options(pc->ctx.get(),
							      ssl_op_disable);
					sprintf(lin, "%d-zproxy-%ld", getpid(),
						random());
					SSL_CTX_set_session_id_context(
						pc->ctx.get(),
						reinterpret_cast<unsigned char *>(
							lin),
						static_cast<unsigned int>(
							strlen(lin)));
					SSL_CTX_set_tmp_rsa_callback(
						pc->ctx,
						global::SslHelper::
							RSA_tmp_callback);
					SSL_CTX_set_info_callback(
						pc->ctx.get(),
						global::SslHelper::
							SSLINFO_callback);
					if (nullptr == DHCustom_params)
						SSL_CTX_set_tmp_dh_callback(
							pc->ctx.get(),
							global::SslHelper::
								DH_tmp_callback);
					else
						SSL_CTX_set_tmp_dh(
							pc->ctx.get(),
							DHCustom_params);

#ifndef OPENSSL_NO_ECDH
					/* This generates a EC_KEY structure with no key, but a group defined
					 */

					if (res->ecdh_curve_nid != 0 ||
					    EC_nid != 0) {
						if (res->ecdh_curve_nid == 0)
							res->ecdh_curve_nid =
								EC_nid;
						EC_KEY *ecdh;
						if ((ecdh = EC_KEY_new_by_curve_name(
							     res->ecdh_curve_nid)) ==
						    nullptr)
							conf_err(
								"Unable to generate Listener temp ECDH key");
						SSL_CTX_set_tmp_ecdh(
							pc->ctx.get(), ecdh);
						SSL_CTX_set_options(
							pc->ctx.get(),
							SSL_OP_SINGLE_ECDH_USE);
						EC_KEY_free(ecdh);
					}
#if defined(SSL_CTX_set_ecdh_auto)
					else {
						SSL_CTX_set_ecdh_auto(res->ctx,
								      1);
					}
#endif
#endif
				}
			}
			return res;
		} else {
			conf_err("unknown directive");
		}
	}

	conf_err("ListenHTTPS premature EOF");
	return nullptr;
}

// return false on success
bool parseCertCN(regex_t *pattern, char *server_name)
{
	char server_[ZCU_DEF_BUFFER_SIZE];
	int len = 0, nlen = 0;

	server_[len++] = '^';
	do {
		// add: "[-a-z0-1]*"
		if (server_name[nlen] == '*') {
			server_[len++] = '[';
			server_[len++] = '-';
			server_[len++] = 'a';
			server_[len++] = '-';
			server_[len++] = 'z';
			server_[len++] = '0';
			server_[len++] = '-';
			server_[len++] = '9';
			server_[len++] = ']';
			server_[len++] = '*';
		} else if (server_name[nlen] == '.') {
			server_[len++] = '\\';
			server_[len++] = '.';
		} else
			server_[len++] = server_name[nlen];
		nlen++;

	} while (server_name[nlen] != '\0' && len < ZCU_DEF_BUFFER_SIZE);

	if (len >= ZCU_DEF_BUFFER_SIZE) {
		zcu_log_print(
			LOG_ERR,
			"Error parsing certificate server name, buffer full %s",
			server_name);
		return true;
	}

	server_[len++] = '$';
	server_[len++] = '\0';

	if (regcomp(pattern, server_, REG_NEWLINE))
		return true;

	return false;
}

regex_t **Config::get_subjectaltnames(X509 *x509, unsigned int *count_)
{
	size_t local_count;
	regex_t **result;
	STACK_OF(GENERAL_NAME) *san_stack =
		static_cast<STACK_OF(GENERAL_NAME) *>(X509_get_ext_d2i(
			x509, NID_subject_alt_name, nullptr, nullptr));
	unsigned char *temp[sk_GENERAL_NAME_num(san_stack)];
	GENERAL_NAME *name__;
	size_t i;

	local_count = 0;
	result = nullptr;
	name__ = nullptr;
	*count_ = 0;
	if (san_stack == nullptr)
		return nullptr;
	while (sk_GENERAL_NAME_num(san_stack) > 0) {
		name__ = sk_GENERAL_NAME_pop(san_stack);
		switch (name__->type) {
		case GEN_DNS:
			temp[local_count] = general_name_string(name__);
			if (temp[local_count] == nullptr)
				conf_err("out of memory");
			local_count++;
			break;
		default:
			zcu_log_print(
				LOG_WARNING,
				"unsupported subjectAltName type encountered: %i",
				name__->type);
		}
		GENERAL_NAME_free(name__);
	}

	if (local_count > 0) {
		result = static_cast<regex_t **>(
			std::malloc(sizeof(regex_t *) * local_count));
		if (result == nullptr)
			conf_err("out of memory");

		for (i = 0; i < local_count; i++) {
			result[i] = static_cast<regex_t *>(
				std::malloc(sizeof(regex_t)));
			if (result[i] == nullptr)
				conf_err("out of memory");
			if (parseCertCN(result[i],
					reinterpret_cast<char *>(temp[i])))
				conf_err("out of memory");
			free(temp[i]);
		}
	}
	*count_ = static_cast<unsigned int>(local_count);

	sk_GENERAL_NAME_pop_free(san_stack, GENERAL_NAME_free);

	return result;
}

void Config::load_cert(int has_other, std::weak_ptr<ListenerConfig> listener_,
		       char *filename)
{
	auto res = listener_.lock();
	std::shared_ptr<SNI_CERTS_CTX> pc;
#ifdef SSL_CTRL_SET_TLSEXT_SERVERNAME_CB
	/* we have support for SNI */
	char server_name[ZCU_DEF_BUFFER_SIZE] /*, *cp */;
	regmatch_t matches[5];
	if (has_other)
		conf_err(
			"Cert directives MUST precede other SSL-specific directives - "
			"aborted");
	if (res->ctx) {
		for (pc = res->ctx; pc->next; pc = pc->next)
			;
		pc->next = std::make_shared<SNI_CERTS_CTX>();
		pc = pc->next;
	} else {
		res->ctx = std::make_shared<SNI_CERTS_CTX>();
		pc = res->ctx;
	}
	pc->ctx = std::shared_ptr<SSL_CTX>(SSL_CTX_new(SSLv23_server_method()),
					   &::__SSL_CTX_free);
	pc->next = nullptr;
	if (SSL_CTX_use_certificate_chain_file(pc->ctx.get(), filename) != 1)
		conf_err("SSL_CTX_use_certificate_chain_file failed - aborted");
	if (SSL_CTX_use_PrivateKey_file(pc->ctx.get(), filename,
					SSL_FILETYPE_PEM) != 1)
		conf_err("SSL_CTX_use_PrivateKey_file failed - aborted");
	if (SSL_CTX_check_private_key(pc->ctx.get()) != 1)
		conf_err("SSL_CTX_check_private_key failed - aborted");
	std::unique_ptr<BIO, decltype(&::BIO_free)> bio_cert(
		BIO_new_file(filename, "r"), ::BIO_free);
	std::unique_ptr<X509, decltype(&::X509_free)> x509(
		::PEM_read_bio_X509(bio_cert.get(), nullptr, nullptr, nullptr),
		::X509_free);
	memset(server_name, '\0', ZCU_DEF_BUFFER_SIZE);
	X509_NAME_oneline(X509_get_subject_name(x509.get()), server_name,
			  ZCU_DEF_BUFFER_SIZE - 1);
	pc->subjectAltNameCount = 0;
	pc->subjectAltNames = nullptr;
	pc->subjectAltNames =
		get_subjectaltnames(x509.get(), &(pc->subjectAltNameCount));
	if (!regexec(&regex_set::CNName, server_name, 4, matches, 0)) {
		server_name[matches[1].rm_eo] = '\0';
		if (parseCertCN(&pc->server_name,
				server_name + matches[1].rm_so))
			conf_err(
				"ListenHTTPS: could not set certificate subject");
	} else
		zcu_log_print(LOG_WARNING,
			      "ListenHTTPS: could not get certificate CN");

// conf_err("ListenHTTPS: could not get certificate CN");
#else
	/* no SNI support */
	if (has_other)
		conf_err(
			"Cert directives MUST precede other SSL-specific directives - "
			"aborted");
	if (res->ctx)
		conf_err(
			"ListenHTTPS: multiple certificates not supported - aborted");
	if ((res->ctx = std::malloc(sizeof(SNI_CERTS_CTX))) == NULL)
		conf_err(
			"ListenHTTPS new SNI_CERTS_CTX: out of memory - aborted");
	res->ctx->server_name = NULL;
	res->ctx->next = NULL;
	if ((res->ctx->ctx = SSL_CTX_new(SSLv23_server_method())) == NULL)
		conf_err("SSL_CTX_new failed - aborted");
	if (SSL_CTX_use_certificate_chain_file(res->ctx->ctx, filename) != 1)
		conf_err("SSL_CTX_use_certificate_chain_file failed - aborted");
	if (SSL_CTX_use_PrivateKey_file(res->ctx->ctx, filename,
					SSL_FILETYPE_PEM) != 1)
		conf_err("SSL_CTX_use_PrivateKey_file failed - aborted");
	if (SSL_CTX_check_private_key(res->ctx->ctx) != 1)
		conf_err("SSL_CTX_check_private_key failed - aborted");
#endif
}

void Config::load_certdir(int has_other,
			  std::weak_ptr<ListenerConfig> listener_,
			  const std::string &dir_path)
{
	DIR *dp;
	struct dirent *de;

	char buf[512];
	char *files[200];
	char *pattern;
	int filecnt = 0;
	int idx, use;
	auto res = listener_.lock();

	zcu_log_print(LOG_DEBUG, "including Certs from Dir %s",
		      dir_path.data());

	pattern = const_cast<char *>(strrchr(dir_path.data(), '/'));
	if (pattern) {
		*pattern++ = 0;
		if (!*pattern)
			pattern = nullptr;
	}

	if ((dp = opendir(dir_path.data())) == nullptr) {
		conf_err("can't open IncludeDir directory");
		exit(1);
	}

	while ((de = readdir(dp)) != nullptr) {
		if (de->d_name[0] == '.')
			continue;
		if (!pattern || fnmatch(pattern, de->d_name, 0) == 0) {
			snprintf(buf, sizeof(buf), "%s%s%s", dir_path.data(),
				 (dir_path[dir_path.size() - 1] == '/') ? "" :
										"/",
				 de->d_name);
			buf[sizeof(buf) - 1] = 0;
			if (filecnt == sizeof(files) / sizeof(*files)) {
				conf_err(
					"Max certificate files per directory reached");
			}
			if ((files[filecnt++] = strdup(buf)) == nullptr) {
				conf_err("CertDir out of memory");
			}
			continue;
		}
	}
	/* We order the list, and load in ascending order */
	while (filecnt) {
		use = 0;
		for (idx = 1; idx < filecnt; idx++)
			if (strcmp(files[use], files[idx]) > 0)
				use = idx;

		zcu_log_print(LOG_DEBUG, " I Cert ==> %s", files[use]);

		load_cert(has_other, res, files[use]);
		files[use] = files[--filecnt];
	}

	closedir(dp);
}

void Config::parseRedirect(char *lin, regmatch_t *matches,
			   std::shared_ptr<BackendConfig> be,
			   MATCHER *url = nullptr)
{
	// 1 - Dynamic or not, 2 - Request Redirect #, 3 - Destination URL
	be->be_type = 302;
	be->redir_req = 0;
	if (matches[1].rm_eo != matches[1].rm_so) {
		if ((lin[matches[1].rm_so] & ~0x20) == 'D') {
			be->redir_req = 2;
			if (!url || url->next)
				conf_err(
					"Dynamic Redirect must be preceeded by a URL line");
		} else if ((lin[matches[1].rm_so] & ~0x20) == 'A')
			be->redir_req = 1;
	}
	if (matches[2].rm_eo != matches[2].rm_so)
		be->be_type = atoi(lin + matches[2].rm_so);
	pthread_mutex_init(&be->mut, nullptr);
	lin[matches[3].rm_eo] = '\0';
	be->url = std::string(lin + matches[3].rm_so);
	/* split the URL into its fields */
	if (regexec(&regex_set::LOCATION, be->url.data(), 4, matches, 0))
		conf_err("Redirect bad URL - aborted");
	if ((matches[3].rm_eo - matches[3].rm_so) ==
	    1) /* the path is a single '/', so remove it */
		be->url.pop_back();
	if (strstr(be->url.c_str(), MACRO::VHOST_STR))
		be->redir_macro = true;
}

std::shared_ptr<ServiceConfig> Config::parseService(const char *svc_name)
{
	char lin[ZCU_DEF_BUFFER_SIZE];
	char pat[ZCU_DEF_BUFFER_SIZE];
	char *ptr;
	auto res = std::make_shared<ServiceConfig>();
	std::shared_ptr<BackendConfig> be;
	MATCHER *m;
	int ign_case;
	regmatch_t matches[10];

	res->f_name = name;
	res->max_headers_allowed = 128;
	res->sess_type = SESS_TYPE::SESS_NONE;
	res->dynscale = dynscale;
	res->sts = -1;
	pthread_mutex_init(&res->mut, nullptr);
	if (svc_name)
		res->name = svc_name;
	ign_case = ignore_case;
	while (conf_fgets(lin, ZCU_DEF_BUFFER_SIZE)) {
		if (strlen(lin) > 0 && lin[strlen(lin) - 1] == '\n')
			lin[strlen(lin) - 1] = '\0';
		if (!regexec(&regex_set::URL, lin, 4, matches, 0)) {
			if (res->url) {
				for (m = res->url; m->next; m = m->next)
					;
				if ((m->next = new MATCHER()) == nullptr)
					conf_err(
						"URL config: out of memory - aborted");
				m = m->next;
			} else {
				if ((res->url = new MATCHER()) == nullptr)
					conf_err(
						"URL config: out of memory - aborted");
				m = res->url;
			}
			memset(m, 0, sizeof(MATCHER));
			lin[matches[1].rm_eo] = '\0';
			if (regcomp(&m->pat, lin + matches[1].rm_so,
				    REG_NEWLINE | REG_EXTENDED |
					    (ign_case ? REG_ICASE : 0)))
				conf_err("URL bad pattern - aborted");
		} else if (!regexec(&regex_set::ReplaceHeader, lin, 5, matches,
				    0)) {
			parseReplaceHeader(lin, matches,
					   &res->replace_header_request,
					   &res->replace_header_response);
		} else if (!regexec(&regex_set::OrURLs, lin, 4, matches, 0)) {
			if (res->url) {
				for (m = res->url; m->next; m = m->next)
					;
				if ((m->next = new MATCHER()) == nullptr)
					conf_err(
						"URL config: out of memory - aborted");
				m = m->next;
			} else {
				if ((res->url = new MATCHER()) == nullptr)
					conf_err(
						"URL config: out of memory - aborted");
				m = res->url;
			}
			memset(m, 0, sizeof(MATCHER));
			ptr = parse_orurls();
			if (regcomp(&m->pat, ptr,
				    REG_NEWLINE | REG_EXTENDED |
					    (ign_case ? REG_ICASE : 0)))
				conf_err("OrURLs bad pattern - aborted");
			free(ptr);
		} else if (!regexec(&regex_set::HeadRequire, lin, 4, matches,
				    0)) {
			if (res->req_head) {
				for (m = res->req_head; m->next; m = m->next)
					;
				if ((m->next = new MATCHER()) == nullptr)
					conf_err(
						"HeadRequire config: out of memory - aborted");
				m = m->next;
			} else {
				if ((res->req_head = new MATCHER()) == nullptr)
					conf_err(
						"HeadRequire config: out of memory - aborted");
				m = res->req_head;
			}
			memset(m, 0, sizeof(MATCHER));
			lin[matches[1].rm_eo] = '\0';
			if (regcomp(&m->pat, lin + matches[1].rm_so,
				    REG_ICASE | REG_NEWLINE | REG_EXTENDED))
				conf_err("HeadRequire bad pattern - aborted");
		} else if (!regexec(&regex_set::HeadDeny, lin, 4, matches, 0)) {
			if (res->deny_head) {
				for (m = res->deny_head; m->next; m = m->next)
					;
				if ((m->next = new MATCHER()) == nullptr)
					conf_err(
						"HeadDeny config: out of memory - aborted");
				m = m->next;
			} else {
				if ((res->deny_head = new MATCHER()) == nullptr)
					conf_err(
						"HeadDeny config: out of memory - aborted");
				m = res->deny_head;
			}
			memset(m, 0, sizeof(MATCHER));
			lin[matches[1].rm_eo] = '\0';
			if (regcomp(&m->pat, lin + matches[1].rm_so,
				    REG_ICASE | REG_NEWLINE | REG_EXTENDED))
				conf_err("HeadDeny bad pattern - aborted");
		} else if (!regexec(&regex_set::RewriteUrl, lin, 4, matches,
				    0)) {
			ReplaceHeader *current{ nullptr };
			lin[matches[1].rm_eo] = '\0';
			lin[matches[2].rm_eo] = '\0';
			lin[matches[3].rm_eo] = '\0';

			if (res->rewr_url) {
				for (current = res->rewr_url; current->next;
				     current = current->next)
					;
				current->next = new ReplaceHeader();
				current = current->next;
			} else {
				res->rewr_url = new ReplaceHeader();
				current = res->rewr_url;
			}

			auto match_ = std::string(lin + matches[1].rm_so);
			auto replace_ = std::string(lin + matches[2].rm_so);
			if (regcomp(&current->match, match_.data(),
				    REG_ICASE | REG_NEWLINE | REG_EXTENDED))
				conf_err("Error compiling Match regex ");
			current->replace = replace_;
			if (matches[2].rm_eo < matches[3].rm_so) {
				current->last = 1;
			}
		} else if (!regexec(&regex_set::RewriteLocation, lin, 4,
				    matches, 0)) {
			res->rewr_loc = atoi(lin + matches[1].rm_so);
			res->rewr_loc_path =
				(matches[1].rm_eo <= matches[2].rm_so) ? 1 : 0;
		} else if (!regexec(&regex_set::AddRequestHeader, lin, 4,
				    matches, 0)) {
			parseAddHeader(&res->add_head_req, lin, matches);
		} else if (!regexec(&regex_set::AddResponseHeader, lin, 4,
				    matches, 0)) {
			parseAddHeader(&res->add_head_resp, lin, matches);
		} else if (!regexec(&regex_set::RemoveRequestHeader, lin, 4,
				    matches, 0)) {
			parseRemoveHeader(&res->head_off_req, lin, matches);
		} else if (!regexec(&regex_set::RemoveResponseHeader, lin, 4,
				    matches, 0)) {
			parseRemoveHeader(&res->head_off_resp, lin, matches);
		} else if (!regexec(&regex_set::StrictTransportSecurity, lin, 4,
				    matches, 0)) {
			res->sts = atoi(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::TestServer, lin, 4, matches,
				    0)) {
			if (res->backends) {
				for (be = res->backends; be->next;
				     be = be->next)
					;
				be->next = std::make_shared<BackendConfig>();
				be = be->next;
			} else {
				res->backends =
					std::make_shared<BackendConfig>();
				be = res->backends;
			}
			be->be_type = 2;
			//maximum request number allowed per TCP connection
			be->max_request = atoi(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::Redirect, lin, 4, matches, 0)) {
			if (res->backends) {
				for (be = res->backends; be->next;
				     be = be->next)
					;
				be->next = std::make_shared<BackendConfig>();
				be = be->next;
			} else {
				res->backends =
					std::make_shared<BackendConfig>();
				be = res->backends;
			}
			parseRedirect(lin, matches, be, res->url);
		} else if (!regexec(&regex_set::BackEnd, lin, 4, matches, 0)) {
			if (res->backends) {
				for (be = res->backends; be->next;
				     be = be->next)
					;
				be->next = parseBackend(svc_name, 0);
			} else
				res->backends = parseBackend(svc_name, 0);
		} else if (!regexec(&regex_set::Emergency, lin, 4, matches,
				    0)) {
			res->emergency = parseBackend(svc_name, 1);
		} else if (!regexec(&regex_set::BackendCookie, lin, 5, matches,
				    0)) {
			lin[matches[1].rm_eo] = '\0';
			lin[matches[2].rm_eo] = '\0';
			lin[matches[3].rm_eo] = '\0';
			lin[matches[4].rm_eo] = '\0';
			snprintf(pat, ZCU_DEF_BUFFER_SIZE - 1,
				 "Cookie[^:]*:.*[; \t]%s=\"?([^\";]*)\"?",
				 lin + matches[1].rm_so);
			if (matches[1].rm_so == matches[1].rm_eo)
				conf_err("Backend cookie must have a name");
			if ((res->becookie = strdup(lin + matches[1].rm_so)) ==
			    nullptr)
				conf_err("out of memory");
			if (regcomp(&res->becookie_re, pat,
				    REG_ICASE | REG_NEWLINE | REG_EXTENDED))
				conf_err(
					"Backend Cookie pattern failed - aborted");
			if (matches[2].rm_so != matches[2].rm_eo &&
			    (res->becdomain = strdup(lin + matches[2].rm_so)) ==
				    nullptr)
				conf_err("out of memory");
			if (matches[3].rm_so != matches[3].rm_eo &&
			    (res->becpath = strdup(lin + matches[3].rm_so)) ==
				    nullptr)
				conf_err("out of memory");
			res->becage = atoi(lin + matches[4].rm_so);
			if ((lin[matches[4].rm_so] & ~0x20) == 'S')
				res->becage = -1;
			else
				res->becage = atoi(lin + matches[4].rm_so);
#ifdef CACHE_ENABLED
		} else if (!regexec(&Cache, lin, 4, matches, 0)) {
			parseCache(res);
#endif
		} else if (!regexec(&regex_set::Session, lin, 4, matches, 0)) {
			parseSession(res);
		} else if (!regexec(&regex_set::DynScale, lin, 4, matches, 0)) {
			res->dynscale = atoi(lin + matches[1].rm_so) == 1;
		} else if (!regexec(&regex_set::PinnedConnection, lin, 4,
				    matches, 0)) {
			res->pinned_connection =
				std::atoi(lin + matches[1].rm_so) == 1;
		} else if (!regexec(&regex_set::RoutingPolicy, lin, 4, matches,
				    0)) {
			lin[matches[1].rm_eo] = '\0';
			std::string cp = lin + matches[1].rm_so;
			if (cp == "ROUND_ROBIN")
				res->routing_policy = 0;
			else if (cp == "LEAST_CONNECTIONS")
				res->routing_policy = 1;
			else if (cp == "RESPONSE_TIME")
				res->routing_policy = 2;
			else if (cp == "PENDING_CONNECTIONS")
				res->routing_policy = 3;
			else
				conf_err("Unknown routing policy");
		} else if (!regexec(&regex_set::CompressionAlgorithm, lin, 4,
				    matches, 0)) {
			lin[matches[1].rm_eo] = '\0';
			std::string cp = lin + matches[1].rm_so;
			if (cp == "gzip" || cp == "deflate")
				res->compression_algorithm = cp;
			else
				conf_err("Unknown compression algorithm");
		} else if (!regexec(&regex_set::IgnoreCase, lin, 4, matches,
				    0)) {
			ign_case = atoi(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::Disabled, lin, 4, matches, 0)) {
			res->disabled = atoi(lin + matches[1].rm_so) == 1;
		} else if (!regexec(&regex_set::End, lin, 4, matches, 0)) {
			for (be = res->backends; be; be = be->next) {
				if (!be->disabled)
					res->tot_pri += be->weight;
				res->abs_pri += be->weight;
			}
			return res;
		} else {
			conf_err("unknown directive");
		}
	}

	conf_err("Service premature EOF");
	return nullptr;
}

char *Config::parse_orurls()
{
	char lin[ZCU_DEF_BUFFER_SIZE];
	char *pattern;
	regex_t comp;
	regmatch_t matches[5];

	pattern = nullptr;
	while (conf_fgets(lin, ZCU_DEF_BUFFER_SIZE)) {
		if (strlen(lin) > 0 && lin[strlen(lin) - 1] == '\n')
			lin[strlen(lin) - 1] = '\0';
		if (!regexec(&regex_set::URL, lin, 4, matches, 0)) {
			lin[matches[1].rm_eo] = '\0';
			/* Verify the pattern is valid */
			if (regcomp(&comp, lin + matches[1].rm_so,
				    REG_NEWLINE | REG_EXTENDED))
				conf_err("URL bad pattern - aborted");
			regfree(&comp);
			if (pattern == nullptr) {
				if ((pattern = static_cast<char *>(std::malloc(
					     strlen(lin + matches[1].rm_so) +
					     5))) == nullptr)
					conf_err(
						"OrURLs config: out of memory - aborted");
				*pattern = 0;
				strcat(pattern, "((");
				strcat(pattern, lin + matches[1].rm_so);
				strcat(pattern, "))");
			} else {
				if ((pattern = static_cast<char *>(realloc(
					     pattern,
					     strlen(pattern) +
						     strlen(lin +
							    matches[1].rm_so) +
						     4))) == nullptr)
					conf_err(
						"OrURLs config: out of memory - aborted");
				pattern[strlen(pattern) - 1] = 0;
				strcat(pattern, "|(");
				strcat(pattern, lin + matches[1].rm_so);
				strcat(pattern, "))");
			}
		} else if (!regexec(&regex_set::End, lin, 4, matches, 0)) {
			if (!pattern)
				conf_err(
					"No URL directives specified within OrURLs block");
			return pattern;
		} else {
			conf_err("unknown directive");
		}
	}

	conf_err("OrURLs premature EOF");
	return nullptr;
}

std::shared_ptr<BackendConfig> Config::parseBackend(const char *svc_name,
						    const int is_emergency)
{
	char lin[ZCU_DEF_BUFFER_SIZE];
	regmatch_t matches[5];
#ifdef CACHE_ENABLED
	char *cp;
#endif
	auto res = std::make_shared<BackendConfig>();
	int has_addr, has_port;

	res->f_name = name;
	res->srv_name = svc_name;
	res->be_type = 0;
	res->rw_timeout = is_emergency ? 120 : be_to;
	res->conn_to = is_emergency ? 120 : be_connto;
	res->alive = 1;
	res->priority = 1;
	res->weight = 1;
	res->connections = 0;
	res->connection_limit = 0;
	res->next = nullptr;
	res->ctx = nullptr;
	res->nf_mark = 0;
	has_addr = has_port = 0;
	addrinfo addr{};
	addrinfo ha_addr{};
	pthread_mutex_init(&res->mut, nullptr);
	while (conf_fgets(lin, ZCU_DEF_BUFFER_SIZE)) {
		if (strlen(lin) > 0 && lin[strlen(lin) - 1] == '\n')
			lin[strlen(lin) - 1] = '\0';
		if (!regexec(&regex_set::Address, lin, 4, matches, 0)) {
			lin[matches[1].rm_eo] = '\0';

			if (zcu_net_get_host(lin + matches[1].rm_so, &addr,
					     PF_UNSPEC)) {
				/* if we can't resolve it, maybe this is a UNIX domain socket */
				if (std::string_view(lin + matches[1].rm_so,
						     matches[1].rm_eo -
							     matches[1].rm_so)
					    .find('/') != std::string::npos) {
					if ((strlen(lin + matches[1].rm_so) +
					     1) > UNIX_PATH_MAX)
						conf_err(
							"UNIX path name too long");
				} else {
					// maybe the backend still not available, we set it as down;
					res->alive = 0;
					zcu_log_print(
						LOG_WARNING,
						"%s line %d: Could not resolve backend host \"%s\".",
						f_name[cur_fin].data(),
						n_lin[cur_fin],
						lin + matches[1].rm_so);
				}
			}
			res->address = lin + matches[1].rm_so;
			has_addr = 1;
		} else if (!regexec(&regex_set::Port, lin, 4, matches, 0)) {
			lin[matches[1].rm_eo] = '\0';
			res->port = std::atoi(lin + matches[1].rm_so);
			has_port = 1;
		} else if (!regexec(&regex_set::BackendKey, lin, 4, matches,
				    0)) {
			lin[matches[1].rm_eo] = '\0';
			res->bekey = std::string(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::SSLConfigFile, lin, 4, matches,
				    0)) {
			lin[matches[1].rm_eo] = '\0';
			res->ssl_config_file =
				std::string(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::SSLConfigSection, lin, 4,
				    matches, 0)) {
			if (res->ssl_config_file.empty())
				conf_err(
					"SSLConfigSection needed if SSLConfigFile directive is set - "
					"aborted");
			lin[matches[1].rm_eo] = '\0';
			res->ssl_config_section =
				std::string(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::Priority, lin, 4, matches, 0)) {
			if (is_emergency)
				conf_err(
					"Priority is not supported for Emergency back-ends");
			res->priority = std::atoi(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::Weight, lin, 4, matches, 0)) {
			if (is_emergency)
				conf_err(
					"Weight is not supported for Emergency back-ends");
			res->weight = std::atoi(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::TimeOut, lin, 4, matches, 0)) {
			res->rw_timeout = std::atoi(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::NfMark, lin, 4, matches, 0)) {
			res->nf_mark = std::atoi(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::ConnLimit, lin, 4, matches,
				    0)) {
			res->connection_limit =
				std::atoi(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::ConnTO, lin, 4, matches, 0)) {
			res->conn_to = std::atoi(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::HAport, lin, 4, matches, 0)) {
			if (is_emergency)
				conf_err(
					"HAport is not supported for Emergency back-ends");
			lin[matches[1].rm_eo] = '\0';
			res->ha_port = std::atoi(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::HAportAddr, lin, 4, matches,
				    0)) {
			if (is_emergency)
				conf_err(
					"HAportAddr is not supported for Emergency back-ends");
			lin[matches[1].rm_eo] = '\0';
			if (zcu_net_get_host(lin + matches[1].rm_so, &ha_addr,
					     PF_UNSPEC)) {
				/* if we can't resolve it assume this is a UNIX domain socket */
				if ((strlen(lin + matches[1].rm_so) + 1) >
				    UNIX_PATH_MAX)
					conf_err("UNIX path name too long");
			}
			res->ha_address = lin + matches[1].rm_so;
			std::free(ha_addr.ai_addr);
			if (matches[2].rm_so > 0) {
				lin[matches[2].rm_eo] = '\0';
				res->ha_port =
					std::atoi(lin + matches[1].rm_so);
			}
		} else if (!regexec(&regex_set::HTTPS, lin, 4, matches, 0)) {
			res->ctx = std::shared_ptr<SSL_CTX>(
				SSL_CTX_new(SSLv23_client_method()),
				&__SSL_CTX_free);
			SSL_CTX_set_app_data(res->ctx.get(), res.get());
			SSL_CTX_set_verify(res->ctx.get(), SSL_VERIFY_NONE,
					   nullptr);
			SSL_CTX_set_mode(res->ctx.get(),
					 SSL_MODE_RELEASE_BUFFERS);
#ifdef SSL_MODE_SEND_FALLBACK_SCSV
			SSL_CTX_set_mode(res->ctx.get(),
					 SSL_MODE_SEND_FALLBACK_SCSV);
#endif
			SSL_CTX_set_options(res->ctx.get(), SSL_OP_ALL);
#ifdef SSL_OP_NO_COMPRESSION
			SSL_CTX_set_options(res->ctx.get(),
					    SSL_OP_NO_COMPRESSION);
#endif
			SSL_CTX_clear_options(
				res->ctx.get(),
				SSL_OP_ALLOW_UNSAFE_LEGACY_RENEGOTIATION);
			SSL_CTX_clear_options(res->ctx.get(),
					      SSL_OP_LEGACY_SERVER_CONNECT);
			sprintf(lin, "%d-zproxy-%ld", getpid(), random());
			SSL_CTX_set_session_id_context(
				res->ctx.get(),
				reinterpret_cast<unsigned char *>(lin),
				static_cast<uint32_t>(strlen(lin)));
			SSL_CTX_set_tmp_rsa_callback(
				res->ctx, global::SslHelper::RSA_tmp_callback);
			if (nullptr == DHCustom_params)
				SSL_CTX_set_tmp_dh_callback(
					res->ctx.get(),
					global::SslHelper::DH_tmp_callback);
			else
				SSL_CTX_set_tmp_dh(res->ctx.get(),
						   DHCustom_params);
		} else if (!regexec(&regex_set::Cert, lin, 4, matches, 0)) {
			if (res->ctx == nullptr)
				conf_err(
					"BackEnd Cert can only be used after HTTPS - aborted");
			lin[matches[1].rm_eo] = '\0';
			if (SSL_CTX_use_certificate_chain_file(
				    res->ctx.get(), lin + matches[1].rm_so) !=
			    1)
				conf_err(
					"SSL_CTX_use_certificate_chain_file failed - aborted");
			if (SSL_CTX_use_PrivateKey_file(res->ctx.get(),
							lin + matches[1].rm_so,
							SSL_FILETYPE_PEM) != 1)
				conf_err(
					"SSL_CTX_use_PrivateKey_file failed - aborted");
			if (SSL_CTX_check_private_key(res->ctx.get()) != 1)
				conf_err(
					"SSL_CTX_check_private_key failed - aborted");
		} else if (!regexec(&regex_set::Ciphers, lin, 4, matches, 0)) {
			if (res->ctx == nullptr)
				conf_err(
					"BackEnd Ciphers can only be used after HTTPS - aborted");
			lin[matches[1].rm_eo] = '\0';
			SSL_CTX_set_cipher_list(res->ctx.get(),
						lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::DisableProto, lin, 4, matches,
				    0)) {
			if (res->ctx == nullptr)
				conf_err(
					"BackEnd Disable can only be used after HTTPS - aborted");
			lin[matches[1].rm_eo] = '\0';
			if (strcasecmp(lin + matches[1].rm_so, "SSLv2") == 0)
				SSL_CTX_set_options(res->ctx.get(),
						    SSL_OP_NO_SSLv2);
			else if (strcasecmp(lin + matches[1].rm_so, "SSLv3") ==
				 0)
				SSL_CTX_set_options(res->ctx.get(),
						    SSL_OP_NO_SSLv2 |
							    SSL_OP_NO_SSLv3);
#ifdef SSL_OP_NO_TLSv1
			else if (strcasecmp(lin + matches[1].rm_so, "TLSv1") ==
				 0)
				SSL_CTX_set_options(res->ctx.get(),
						    SSL_OP_NO_SSLv2 |
							    SSL_OP_NO_SSLv3 |
							    SSL_OP_NO_TLSv1);
#endif
#ifdef SSL_OP_NO_TLSv1_1
			else if (strcasecmp(lin + matches[1].rm_so,
					    "TLSv1_1") == 0)
				SSL_CTX_set_options(res->ctx.get(),
						    SSL_OP_NO_SSLv2 |
							    SSL_OP_NO_SSLv3 |
							    SSL_OP_NO_TLSv1 |
							    SSL_OP_NO_TLSv1_1);
#endif
#ifdef SSL_OP_NO_TLSv1_2
			else if (strcasecmp(lin + matches[1].rm_so,
					    "TLSv1_2") == 0)
				SSL_CTX_set_options(res->ctx.get(),
						    SSL_OP_NO_SSLv2 |
							    SSL_OP_NO_SSLv3 |
							    SSL_OP_NO_TLSv1 |
							    SSL_OP_NO_TLSv1_1 |
							    SSL_OP_NO_TLSv1_2);
#endif
#ifdef SSL_OP_NO_TLSv1_3
			else if (strcasecmp(lin + matches[1].rm_so,
					    "TLSv1_3") == 0)
				SSL_CTX_set_options(res->ctx.get(),
						    SSL_OP_NO_TLSv1_3);
#endif
#ifndef OPENSSL_NO_ECDH
		} else if (!regexec(&regex_set::ECDHCurve, lin, 4, matches,
				    0)) {
			if (res->ctx == nullptr)
				conf_err(
					"BackEnd ECDHCurve can only be used after HTTPS - aborted");
			lin[matches[1].rm_eo] = '\0';
			if ((res->ecdh_curve_nid =
				     OBJ_sn2nid(lin + matches[1].rm_so)) == 0)
				conf_err(
					"ECDHCurve config: invalid curve name");

			if (res->ecdh_curve_nid != 0) {
				/* This generates a EC_KEY structure with no key, but a group defined
				 */
				EC_KEY *ecdh;
				if ((ecdh = EC_KEY_new_by_curve_name(
					     res->ecdh_curve_nid)) == nullptr)
					conf_err(
						"Unable to generate temp ECDH key");
				SSL_CTX_set_tmp_ecdh(res->ctx.get(), ecdh);
				SSL_CTX_set_options(res->ctx.get(),
						    SSL_OP_SINGLE_ECDH_USE);
				EC_KEY_free(ecdh);
			}
#if defined(SSL_CTX_set_ecdh_auto)
			else {
				SSL_CTX_set_ecdh_auto(res->ctx.get(), 1);
			}
#endif
#endif
		} else if (!regexec(&regex_set::Disabled, lin, 4, matches, 0)) {
			res->disabled = std::atoi(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::End, lin, 4, matches, 0)) {
			if (!has_addr)
				conf_err("BackEnd missing Address - aborted");
			if ((addr.ai_family == AF_INET ||
			     addr.ai_family == AF_INET6) &&
			    !has_port)
				conf_err("BackEnd missing Port - aborted");
			std::free(addr.ai_addr);
			return res;
		} else {
			std::free(addr.ai_addr);
			conf_err("unknown directive");
		}
	}

	conf_err("BackEnd premature EOF");
	return nullptr;
}

#ifdef CACHE_ENABLED
void Config::parseCache(ServiceConfig *const svc)
{
	char lin[ZCU_DEF_BUFFER_SIZE], *cp;
	if (cache_s == 0 || cache_thr == 0)
		conf_err(
			"There is no CacheRamSize nor CacheThreshold configured, exiting");
	regmatch_t matches[5];
	svc->cache_size = cache_s;
	svc->cache_threshold = cache_thr;
	if (cache_ram_path.size() != 0) {
		svc->cache_ram_path = cache_ram_path;
	}
	if (cache_disk_path.size() != 0) {
		svc->cache_disk_path = cache_disk_path;
	}
	while (conf_fgets(lin, ZCU_DEF_BUFFER_SIZE)) {
		if (strlen(lin) > 0 && lin[strlen(lin) - 1] == '\n')
			lin[strlen(lin) - 1] = '\0';
		if (!regexec(&MaxSize, lin, 2, matches, 0))
			svc->cache_max_size =
				strtoul(lin + matches[1].rm_so, nullptr, 0);
		if (!regexec(&CacheContent, lin, 4, matches, 0)) {
			lin[matches[1].rm_eo] = '\0';
			cp = lin + matches[1].rm_so;
			if (regcomp(&svc->cache_content, cp,
				    REG_ICASE | REG_NEWLINE | REG_EXTENDED))
				conf_err(
					"Cache content pattern failed, aborting");
			// Set the service CacheContent option
		} else if (!regexec(&CacheTO, lin, 4, matches, 0)) {
			// Set the service CacheTO option
			cp = lin + matches[1].rm_so;
			svc->cache_timeout = std::atoi(cp);
		} else if (!regexec(&End, lin, 4, matches, 0)) {
			return;
		}
	}
}
#endif
void Config::parseSession(std::weak_ptr<ServiceConfig> svc_spt)
{
	char lin[ZCU_DEF_BUFFER_SIZE], *cp, *parm;
	regmatch_t matches[5];
	parm = nullptr;
	auto svc = svc_spt.lock();
	svc->f_name = name;
	while (conf_fgets(lin, ZCU_DEF_BUFFER_SIZE)) {
		if (strlen(lin) > 0 && lin[strlen(lin) - 1] == '\n')
			lin[strlen(lin) - 1] = '\0';
		if (!regexec(&regex_set::Type, lin, 4, matches, 0)) {
			if (svc->sess_type != SESS_TYPE::SESS_NONE)
				conf_err(
					"Multiple Session types in one Service - aborted");
			lin[matches[1].rm_eo] = '\0';
			cp = lin + matches[1].rm_so;
			if (!strcasecmp(cp, "IP"))
				svc->sess_type = SESS_TYPE::SESS_IP;
			else if (!strcasecmp(cp, "COOKIE"))
				svc->sess_type = SESS_TYPE::SESS_COOKIE;
			else if (!strcasecmp(cp, "URL"))
				svc->sess_type = SESS_TYPE::SESS_URL;
			else if (!strcasecmp(cp, "PARM"))
				svc->sess_type = SESS_TYPE::SESS_PARM;
			else if (!strcasecmp(cp, "BASIC"))
				svc->sess_type = SESS_TYPE::SESS_BASIC;
			else if (!strcasecmp(cp, "HEADER"))
				svc->sess_type = SESS_TYPE::SESS_HEADER;
			else
				conf_err("Unknown Session type");
		} else if (!regexec(&regex_set::TTL, lin, 4, matches, 0)) {
			svc->sess_ttl = std::atoi(lin + matches[1].rm_so);
		} else if (!regexec(&regex_set::ID, lin, 4, matches, 0)) {
			svc->sess_id = lin + matches[1].rm_so;
			svc->sess_id = svc->sess_id.substr(
				0, static_cast<size_t>(matches[1].rm_eo -
						       matches[1].rm_so));
			if (svc->sess_type != SESS_TYPE::SESS_COOKIE &&
			    svc->sess_type != SESS_TYPE::SESS_URL &&
			    svc->sess_type != SESS_TYPE::SESS_HEADER)
				conf_err(
					"no ID permitted unless COOKIE/URL/HEADER Session - aborted");
			lin[matches[1].rm_eo] = '\0';
			if ((parm = strdup(lin + matches[1].rm_so)) == nullptr)
				conf_err("ID config: out of memory - aborted");
		} else if (!regexec(&regex_set::End, lin, 4, matches, 0)) {
			if (svc->sess_type == SESS_TYPE::SESS_NONE)
				conf_err("Session type not defined - aborted");
			if (svc->sess_ttl == 0)
				conf_err("Session TTL not defined - aborted");
			if ((svc->sess_type == SESS_TYPE::SESS_COOKIE ||
			     svc->sess_type == SESS_TYPE::SESS_URL ||
			     svc->sess_type == SESS_TYPE::SESS_HEADER) &&
			    parm == nullptr)
				conf_err("Session ID not defined - aborted");
			if (svc->sess_type == SESS_TYPE::SESS_COOKIE) {
				snprintf(lin, ZCU_DEF_BUFFER_SIZE - 1,
					 "Cookie[^:]*:.*[; \t]%s=", parm);
				if (regcomp(&svc->sess_start, lin,
					    REG_ICASE | REG_NEWLINE |
						    REG_EXTENDED))
					conf_err(
						"COOKIE pattern failed - aborted");
				if (regcomp(&svc->sess_pat, "([^;]*)",
					    REG_ICASE | REG_NEWLINE |
						    REG_EXTENDED))
					conf_err(
						"COOKIE pattern failed - aborted");
			} else if (svc->sess_type == SESS_TYPE::SESS_URL) {
				snprintf(lin, ZCU_DEF_BUFFER_SIZE - 1,
					 "[?&]%s=", parm);
				if (regcomp(&svc->sess_start, lin,
					    REG_ICASE | REG_NEWLINE |
						    REG_EXTENDED))
					conf_err(
						"URL pattern failed - aborted");
				if (regcomp(&svc->sess_pat, "([^&;#]*)",
					    REG_ICASE | REG_NEWLINE |
						    REG_EXTENDED))
					conf_err(
						"URL pattern failed - aborted");
			} else if (svc->sess_type == SESS_TYPE::SESS_PARM) {
				if (regcomp(&svc->sess_start, ";",
					    REG_ICASE | REG_NEWLINE |
						    REG_EXTENDED))
					conf_err(
						"PARM pattern failed - aborted");
				if (regcomp(&svc->sess_pat, "([^?]*)",
					    REG_ICASE | REG_NEWLINE |
						    REG_EXTENDED))
					conf_err(
						"PARM pattern failed - aborted");
			} else if (svc->sess_type == SESS_TYPE::SESS_BASIC) {
				if (regcomp(&svc->sess_start,
					    "Authorization:[ \t]*Basic[ \t]*",
					    REG_ICASE | REG_NEWLINE |
						    REG_EXTENDED))
					conf_err(
						"BASIC pattern failed - aborted");
				if (regcomp(&svc->sess_pat, "([^ \t]*)",
					    REG_ICASE | REG_NEWLINE |
						    REG_EXTENDED))
					conf_err(
						"BASIC pattern failed - aborted");
			} else if (svc->sess_type == SESS_TYPE::SESS_HEADER) {
				snprintf(lin, ZCU_DEF_BUFFER_SIZE - 1,
					 "%s:[ \t]*", parm);
				if (regcomp(&svc->sess_start, lin,
					    REG_ICASE | REG_NEWLINE |
						    REG_EXTENDED))
					conf_err(
						"HEADER pattern failed - aborted");
				if (regcomp(&svc->sess_pat, "([^ \t]*)",
					    REG_ICASE | REG_NEWLINE |
						    REG_EXTENDED))
					conf_err(
						"HEADER pattern failed - aborted");
			}
			if (parm != nullptr)
				free(parm);
			return;
		} else {
			conf_err("unknown directive");
		}
	}

	conf_err("Session premature EOF");
}

void Config::conf_err(const char *msg)
{
	fprintf(stderr, "%s line %d: %s\n", f_name[cur_fin].data(),
		n_lin[cur_fin], msg);
	if (abort_on_error)
		exit(EXIT_FAILURE);
	this->found_parse_error = true;
}

char *Config::conf_fgets(char *buf, const int max)
{
	int i;
	regmatch_t matches[5];
	for (;;) {
		if (fgets(buf, max, f_in[cur_fin]) == nullptr) {
			fclose(f_in[cur_fin]);
			if (cur_fin > 0) {
				cur_fin--;
				continue;
			} else
				return nullptr;
		}
		n_lin[cur_fin]++;
		for (i = 0; i < max; i++)
			if (buf[i] == '\n' || buf[i] == '\r') {
				buf[i] = '\0';
				break;
			}
		if (!regexec(&regex_set::Empty, buf, 4, matches, 0) ||
		    !regexec(&regex_set::Comment, buf, 4, matches,
			     0)) /* comment or empty line */
			continue;
		if (!regexec(&regex_set::Include, buf, 4, matches, 0)) {
			buf[matches[1].rm_eo] = '\0';
			if (cur_fin == (MAX_FIN - 1))
				conf_err("Include nesting too deep");
			cur_fin++;
			f_name[cur_fin] = std::string(&buf[matches[1].rm_so]);
			if ((f_in[cur_fin] = fopen(&buf[matches[1].rm_so],
						   "rt")) == nullptr)
				conf_err("can't open included file");
			n_lin[cur_fin] = 0;
			continue;
		}
		if (!regexec(&regex_set::IncludeDir, buf, 4, matches, 0)) {
			buf[matches[1].rm_eo] = '\0';
			include_dir(buf + matches[1].rm_so);
			continue;
		}
		return buf;
	}
}

void Config::include_dir(const char *conf_path)
{
	DIR *dp;
	struct dirent *de;

	char buf[512];
	char *files[200];
	int filecnt = 0;
	int idx, use;

	zcu_log_print(LOG_DEBUG, "Including Dir %s", conf_path);

	if ((dp = opendir(conf_path)) == nullptr) {
		conf_err("can't open IncludeDir directory");
		exit(1);
	}

	while ((de = readdir(dp)) != nullptr) {
		if (de->d_name[0] == '.')
			continue;
		if ((strlen(de->d_name) >= 5 &&
		     !strncmp(de->d_name + strlen(de->d_name) - 4, ".cfg",
			      4)) ||
		    (strlen(de->d_name) >= 6 &&
		     !strncmp(de->d_name + strlen(de->d_name) - 5, ".conf",
			      5))) {
			snprintf(buf, sizeof(buf), "%s%s%s", conf_path,
				 (conf_path[strlen(conf_path) - 1] == '/') ?
					       "" :
					       "/",
				 de->d_name);
			buf[sizeof(buf) - 1] = 0;
			if (filecnt == sizeof(files) / sizeof(*files)) {
				conf_err(
					"Max config files per directory reached");
			}
			if ((files[filecnt++] = strdup(buf)) == nullptr) {
				conf_err("IncludeDir out of memory");
			}
			continue;
		}
	}
	/* We order the list, and include in reverse order, because include_file
	 * adds to the top of the list */
	while (filecnt) {
		use = 0;
		for (idx = 1; idx < filecnt; idx++)
			if (strcmp(files[use], files[idx]) < 0)
				use = idx;

		zcu_log_print(LOG_DEBUG, " I==> %s", files[use]);

		// Copied from Include logic
		if (cur_fin == (MAX_FIN - 1))
			conf_err("Include nesting too deep");
		cur_fin++;
		f_name[cur_fin] = files[use];
		if ((f_in[cur_fin] = fopen(files[use], "rt")) == nullptr) {
			fprintf(stderr,
				"%s line %d: Can't open included file %s",
				f_name[cur_fin].data(), n_lin[cur_fin],
				files[use]);
			exit(1);
		}
		n_lin[cur_fin] = 0;
		files[use] = files[--filecnt];
	}

	closedir(dp);
}

void Config::setAsCurrent()
{
	if (found_parse_error)
		return;
	global::run_options::getCurrent().num_threads = numthreads;
	global::run_options::getCurrent().log_level = log_level;
	global::run_options::getCurrent().log_facility = log_facility;
	global::run_options::getCurrent().user = user;
	global::run_options::getCurrent().group = group;
	global::run_options::getCurrent().pid_name = pid_name;
	global::run_options::getCurrent().ctrl_name = ctrl_name;
	global::run_options::getCurrent().ctrl_ip = ctrl_ip;
	global::run_options::getCurrent().ctrl_user = ctrl_user;
	global::run_options::getCurrent().ctrl_group = ctrl_group;
	global::run_options::getCurrent().ctrl_mode = ctrl_mode;
	global::run_options::getCurrent().daemonize = daemonize;
	global::run_options::getCurrent().backend_resurrect_timeout = alive_to;
	global::run_options::getCurrent().grace_time = grace;
	global::run_options::getCurrent().root_jail = root_jail;
	global::run_options::getCurrent().config_file_name = conf_file_name;
	global::StartOptions::getCurrent().conf_file_name = conf_file_name;
}

bool Config::init(const std::string &file_name)
{
	conf_file_name = file_name;

	// init configuration file lists.
	f_name[0] = std::string(conf_file_name);
	if ((f_in[0] = fopen(conf_file_name.data(), "rt")) == nullptr) {
		fprintf(stderr, "can't open open %s", conf_file_name.data());
		return false;
	}
	n_lin[0] = 0;
	cur_fin = 0;

	DHCustom_params = nullptr;
	numthreads = 0;
	alive_to = 30;
	daemonize = 1;
	grace = 30;
	ignore_100 = 1;
	services = nullptr;
	listeners = nullptr;
	zcu_log_set_prefix("");
#ifdef CACHE_ENABLED
	cache_s = 0;
	cache_thr = 0;
#endif
	parse_file();
	if (listeners == nullptr) {
		zcu_log_print(LOG_ERR, "no listeners defined - aborted",
			      __FUNCTION__, __LINE__);
		return false;
	}

	/* set the facility only here to ensure the syslog gets opened if necessary
	 */
	log_facility = def_facility;
	return !found_parse_error;
}

void __SSL_CTX_free(SSL_CTX *ssl_ctx)
{
	::SSL_CTX_free(ssl_ctx);
}
