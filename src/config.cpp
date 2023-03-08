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

#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <dirent.h>
#include <iostream>
#include <fstream>
#include <fnmatch.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <openssl/engine.h>

#include "macro.h"
#include "config.h"
#include "list.h"
#include "zcu_common.h"
#include "zcu_network.h"
#include "ssl.h"
#include "state.h"
#if ENABLE_WAF
#include "waf.h"
#else
#include "waf_dummy.h"
#endif

#define CONFIG_REGEX_Empty			"^[ \t]*$"
#define CONFIG_REGEX_Comment			"^[ \t]*#.*$"
#define CONFIG_REGEX_User			"^[ \t]*User[ \t]+\"(.+)\"[ \t]*$"
#define CONFIG_REGEX_Group			"^[ \t]*Group[ \t]+\"(.+)\"[ \t]*$"
#define CONFIG_REGEX_Name			"^[ \t]*Name[ \t]+\"?([a-zA-Z0-9_-]+)\"?[ \t]*$"
#define CONFIG_REGEX_HTTPTracerDir		"^[ \t]*HTTPTracerDir[ \t]+\"(.+)\"[ \t]*$"
#define CONFIG_REGEX_RootJail			"^[ \t]*RootJail[ \t]+\"(.+)\"[ \t]*$"
#define CONFIG_REGEX_Daemon			"^[ \t]*Daemon[ \t]+([01])[ \t]*$"
#define CONFIG_REGEX_Threads			"^[ \t]*Threads[ \t]+([1-9][0-9]*)[ \t]*$"
#define CONFIG_REGEX_ThreadModel		"^[ \t]*ThreadModel[ \t]+(pool|dynamic)[ \t]*$"
#define CONFIG_REGEX_LogFacility		"^[ \t]*LogFacility[ \t]+([a-z0-9-]+)[ \t]*$"
#define CONFIG_REGEX_LogLevel			"^[ \t]*LogLevel[ \t]+([0-9])[ \t]*$"
#define CONFIG_REGEX_Grace			"^[ \t]*Grace[ \t]+([0-9]+)[ \t]*$"
#define CONFIG_REGEX_Alive			"^[ \t]*Alive[ \t]+([1-9][0-9]*)[ \t]*$"
#define CONFIG_REGEX_SSLEngine			"^[ \t]*SSLEngine[ \t]+\"(.+)\"[ \t]*$"
#define CONFIG_REGEX_Control			"^[ \t]*Control[ \t]+\"(.+)\"[ \t]*$"
#define CONFIG_REGEX_ControlIP			"^[ \t]*ControlIP[ \t]+([^ \t]+)[ \t]*$"
#define CONFIG_REGEX_ControlPort		"^[ \t]*ControlPort[ \t]+([1-9][0-9]*)[ \t]*$"
#define CONFIG_REGEX_ControlUser		"^[ \t]*ControlUser[ \t]+\"(.+)\"[ \t]*$"
#define CONFIG_REGEX_ControlGroup		"^[ \t]*ControlGroup[ \t]+\"(.+)\"[ \t]*$"
#define CONFIG_REGEX_ControlMode		"^[ \t]*ControlMode[ \t]+([0-7]+)[ \t]*$"
#define CONFIG_REGEX_ListenHTTP			"^[ \t]*ListenHTTP[ \t]*$"
#define CONFIG_REGEX_ListenHTTPS		"^[ \t]*ListenHTTPS[ \t]*$"
#define CONFIG_REGEX_End			"^[ \t]*End[ \t]*$"
#define CONFIG_REGEX_BackendKey			"^[ \t]*Key[ \t]+\"(.+)\"[ \t]*$"
#define CONFIG_REGEX_Address			"^[ \t]*Address[ \t]+([^ \t]+)[ \t]*$"
#define CONFIG_REGEX_Port			"^[ \t]*Port[ \t]+([1-9][0-9]*)[ \t]*$"
#define CONFIG_REGEX_Cert			"^[ \t]*Cert[ \t]+\"(.+)\"[ \t]*$"
#define CONFIG_REGEX_CertDir			"^[ \t]*CertDir[ \t]+\"(.+)\"[ \t]*$"
#define CONFIG_REGEX_xHTTP			"^[ \t]*xHTTP[ \t]+([012345])[ \t]*$"
#define CONFIG_REGEX_Client			"^[ \t]*Client[ \t]+([1-9][0-9]*)[ \t]*$"
#define CONFIG_REGEX_CheckURL			"^[ \t]*CheckURL[ \t]+\"(.+)\"[ \t]*$"
#define CONFIG_REGEX_SSLConfigFile		"^[ \t]*SSLConfigFile[ \t]+\"(.+)\"[ \t]*$"
#define CONFIG_REGEX_ErrNoSsl			"^[ \t]*ErrNoSsl[ \t]+([45][0-9][0-9][ \t]+)?\"(.+)\"[ \t]*$"
#define CONFIG_REGEX_Err414			"^[ \t]*Err414[ \t]+\"(.+)\"[ \t]*$"
#define CONFIG_REGEX_Err500			"^[ \t]*Err500[ \t]+\"(.+)\"[ \t]*$"
#define CONFIG_REGEX_Err501			"^[ \t]*Err501[ \t]+\"(.+)\"[ \t]*$"
#define CONFIG_REGEX_Err503			"^[ \t]*Err503[ \t]+\"(.+)\"[ \t]*$"
#define CONFIG_REGEX_NoSslRedirect		"^[ \t]*NoSslRedirect[ \t]+(30[127][ \t]+)?\"(.+)\"[ \t]*$"
#define CONFIG_REGEX_SSLConfigSection		"^[ \t]*SSLConfigSection[ \t]+([^ \t]+)[ \t]*$"
#define CONFIG_REGEX_MaxRequest			"^[ \t]*MaxRequest[ \t]+([1-9][0-9]*)[ \t]*$"
#define CONFIG_REGEX_AddRequestHeader		"^[ \t]*(?:AddHeader|AddRequestHeader)[ \t]+\"(.+)\"[ \t]*$"
#define CONFIG_REGEX_RemoveRequestHeader	"^[ \t]*(?:HeadRemove|RemoveRequestHeader)[ \t]+\"(.+)\"[ \t]*$"
#define CONFIG_REGEX_AddResponseHeader		"^[ \t]*AddResponseHead(?:er)?[ \t]+\"(.+)\"[ \t]*$"
#define CONFIG_REGEX_RemoveResponseHeader	"^[ \t]*RemoveResponseHead(?:er)?[ \t]+\"(.+)\"[ \t]*$"
#define CONFIG_REGEX_RewriteLocation		"^[ \t]*RewriteLocation[ \t]+([012])([ \t]+[01])?[ \t]*$"
#define CONFIG_REGEX_RewriteDestination		"^[ \t]*RewriteDestination[ \t]+([01])[ \t]*$"
#define CONFIG_REGEX_RewriteHost		"^[ \t]*RewriteHost[ \t]+([01])[ \t]*$"
#define CONFIG_REGEX_RewriteUrl			"^[ \t]*RewriteUrl[ \t]+\"(.+)\"[ \t]+\"(.*)\"([ \t]+last)?[ \t]*$"
#define CONFIG_REGEX_ServiceName		"^[ \t]*Service[ \t]+\"(.+)\"[ \t]*$"
#define CONFIG_REGEX_URL			"^[ \t]*URL[ \t]+\"(.+)\"[ \t]*$"
#define CONFIG_REGEX_OrURLs			"^[ \t]*OrURLS[ \t]*$"
#define CONFIG_REGEX_HeadRequire		"^[ \t]*HeadRequire[ \t]+\"(.+)\"[ \t]*$"
#define CONFIG_REGEX_HeadDeny			"^[ \t]*HeadDeny[ \t]+\"(.+)\"[ \t]*$"
#define CONFIG_REGEX_StrictTransportSecurity	"^[ \t]*StrictTransportSecurity[ \t]+([0-9]+)[ \t]*$"
#define CONFIG_REGEX_BackEnd			"^[ \t]*BackEnd[ \t]*$"
#define CONFIG_REGEX_Priority			"^[ \t]*Priority[ \t]+([1-9])[ \t]*$"
#define CONFIG_REGEX_Weight			"^[ \t]*Weight[ \t]+([1-9]*)[ \t]*$"
#define CONFIG_REGEX_TimeOut			"^[ \t]*TimeOut[ \t]+([1-9][0-9]*)[ \t]*$"
#define CONFIG_REGEX_Redirect			"^[ \t]*Redirect(Append|Dynamic|)[ \t]+(30[127][ \t]+|)\"(.+)\"[ \t]*$"
#define CONFIG_REGEX_Session			"^[ \t]*Session[ \t]*$"
#define CONFIG_REGEX_Type			"^[ \t]*Type[ \t]+([^ \t]+)[ \t]*$"
#define CONFIG_REGEX_TTL			"^[ \t]*TTL[ \t]+([1-9][0-9]*)[ \t]*$"
#define CONFIG_REGEX_ID				"^[ \t]*ID[ \t]+\"(.+)\"[ \t]*$"
#define CONFIG_REGEX_SessPath			"^[ \t]*Path[ \t]+\"(.+)\"[ \t]*$"
#define CONFIG_REGEX_SessDomain			"^[ \t]*Domain[ \t]+\"(.+)\"[ \t]*$"
#define CONFIG_REGEX_DynScale			"^[ \t]*DynScale[ \t]+([01])[ \t]*$"
#define CONFIG_REGEX_CompressionAlgorithm	"^[ \t]*CompressionAlgorithm[ \t]+([^ \t]+)[ \t]*$"
#define CONFIG_REGEX_RoutingPolicy		"^[ \t]*RoutingPolicy[ \t]+([^ \t]+)[ \t]*$"
#define CONFIG_REGEX_SSLAllowClientRenegotiation "^[ \t]*SSLAllowClientRenegotiation[ \t]+([012])[ \t]*$"
#define CONFIG_REGEX_DisableProto		"^[ \t]*Disable[ \t]+(SSLv2|SSLv3|TLSv1|TLSv1_1|TLSv1_2|TLSv1_3)[ \t]*$"
#define CONFIG_REGEX_SSLHonorCipherOrder	"^[ \t]*SSLHonorCipherOrder[ \t]+([01])[ \t]*$"
#define CONFIG_REGEX_Ciphers			"^[ \t]*Ciphers[ \t]+\"(.+)\"[ \t]*$"
#define CONFIG_REGEX_CAlist			"^[ \t]*CAlist[ \t]+\"(.+)\"[ \t]*$"
#define CONFIG_REGEX_VerifyList			"^[ \t]*VerifyList[ \t]+\"(.+)\"[ \t]*$"
#define CONFIG_REGEX_CRLlist			"^[ \t]*CRLlist[ \t]+\"(.+)\"[ \t]*$"
#define CONFIG_REGEX_SSLUncleanShutdown		"^[ \t]*SSLUncleanShutdown[ \t]+\"(.+)\"[ \t]*$"
#define CONFIG_REGEX_Include			"^[ \t]*Include[ \t]+\"(.+)\"[ \t]*$"
#define CONFIG_REGEX_IncludeDir			"^[ \t]*IncludeDir[ \t]+\"(.+)\"[ \t]*$"
#define CONFIG_REGEX_ConnLimit			"^[ \t]*ConnLimit[ \t]+([0-9][0-9]*)[ \t]*$"
#define CONFIG_REGEX_ConnTO			"^[ \t]*ConnTO[ \t]+([1-9][0-9]*)[ \t]*$"
#define CONFIG_REGEX_IgnoreCase			"^[ \t]*IgnoreCase[ \t]+([01])[ \t]*$"
#define CONFIG_REGEX_Ignore100continue		"^[ \t]*Ignore100continue[ \t]+([01])[ \t]*$"
#define CONFIG_REGEX_HTTPS			"^[ \t]*HTTPS[ \t]*$"
#define CONFIG_REGEX_DHParams			"^[ \t]*DHParams[ \t]+\"(.+)\"[ \t]*$"
#define CONFIG_REGEX_Anonymise			"^[ \t]*Anonymise[ \t]*$"
#define CONFIG_REGEX_ECDHCurve			"^[ \t]*ECDHCurve[ \t]+\"(.+)\"[ \t]*$"
#define CONFIG_REGEX_ForwardSNI			"^[ \t]*ForwardSNI[ \t]+([01])[ \t]*$"
#define CONFIG_REGEX_LOCATION			"^(http|https)://([^/]+)(.*)"
#define CONFIG_REGEX_NfMark			"^[ \t]*NfMark[ \t]+([1-9][0-9]*)[ \t]*$"
#define CONFIG_REGEX_NfMark_Hex			"^[ \t]*NfMark[ \t]+(0x[0-9a-f]+)[ \t]*$"
#define CONFIG_REGEX_ReplaceHeader		"^[ \t]*ReplaceHeader[ \t]+(Request|Response)[ \t]+\"(.+)\"[ \t]+\"(.+)\"[ \t]+\"(.*)\"[ \t]*$"

/* WAF */
#define CONFIG_REGEX_ErrWAF			"^[ \t]*ErrWAF[ \t]+\"(.+)\"[ \t]*$"
#define CONFIG_REGEX_WafRules			"^[ \t]*WafRules[ \t]+\"(.+)\"[ \t]*$"

static int n_lin = 0;
static int listener_counter = 0;

#define parse_error(str){ \
	fprintf(stderr, "config_error(line %d): ", n_lin); \
	fprintf(stderr, str": %s\n", lin); \
	goto err; \
}

#define require_ssl(x) \
	if (!x) \
		parse_error("directive for HTTPS listener")

static const char *xhttp[6] = {
	"^(GET|POST|HEAD) ([^ ]+) HTTP/1.[01].*$",
	"^(GET|POST|HEAD|PUT|PATCH|DELETE) ([^ ]+) HTTP/1.[01].*$",
	"^(GET|POST|HEAD|PUT|PATCH|DELETE|LOCK|UNLOCK|PROPFIND|PROPPATCH|SEARCH|"
	"MKCOL|MKCALENDAR|MOVE|COPY|OPTIONS|TRACE|MKACTIVITY|CHECKOUT|MERGE|"
	"REPORT) ([^ ]+) HTTP/1.[01].*$",
	"^(GET|POST|HEAD|PUT|PATCH|DELETE|LOCK|UNLOCK|PROPFIND|PROPPATCH|SEARCH|"
	"MKCOL|MKCALENDAR|MOVE|COPY|OPTIONS|TRACE|MKACTIVITY|CHECKOUT|MERGE|"
	"REPORT|SUBSCRIBE|UNSUBSCRIBE|BPROPPATCH|POLL|BMOVE|BCOPY|BDELETE|"
	"BPROPFIND|NOTIFY|CONNECT) ([^ ]+) HTTP/1.[01].*$",
	"^(GET|POST|HEAD|PUT|PATCH|DELETE|LOCK|UNLOCK|PROPFIND|PROPPATCH|SEARCH|"
	"MKCOL|MKCALENDAR|MOVE|COPY|OPTIONS|TRACE|MKACTIVITY|CHECKOUT|MERGE|"
	"REPORT|SUBSCRIBE|UNSUBSCRIBE|BPROPPATCH|POLL|BMOVE|BCOPY|BDELETE|"
	"BPROPFIND|NOTIFY|CONNECT|RPC_IN_DATA|RPC_OUT_DATA|VERSION-CONTROL) ([^ "
	"]+) HTTP/1.[01].*$",
	"^(GET|POST|HEAD|PUT|PATCH|DELETE|OPTIONS) ([^ ]+) HTTP/1.[01].*$"
};

#define DEFAULT_NUM_THREADS		8
#define DEFAULT_MAINTENANCE_TO		10
#define DEFAULT_BE_CONNTO           	6
#define DEFAULT_FILE_CONFIG		"/usr/local/etc/zproxy.cfg"
#define DEFAULT_PIDFILE			"/var/run/zproxy.pid"
#define DEFAULT_SSL_CONFIG		false
#define DEFAULT_RW_URL_REV		1
#define DEFAULT_RW_LOCATION		0
#define DEFAULT_URLPATTERN_OPTION	false
#define DEFAULT_MAX_HEADERS_ALLOWED	128
#define DEFAULT_BACKEND_PRIORITY	1
#define DEFAULT_BACKEND_WEIGHT		1
#define DEFAULT_BACKEND_CONN_LIMIT	0
#define DEFAULT_BACKEND_NFMARK		0
#define DEFAULT_SSL_CIPHERS		"DES-EDE3-CBC"
#define DEFAULT_BACKEND_PRIORITY	1
#define DEFAULT_BACKEND_WEIGHT		1
#define DEFAULT_BACKEND_CONN_LIMIT	0
#define DEFAULT_BACKEND_NFMARK		0

void zproxy_cfg_init(struct zproxy_cfg *cfg)
{
	cfg->num_threads = DEFAULT_NUM_THREADS;
	cfg->timer.maintenance = DEFAULT_MAINTENANCE_TO;
	cfg->timer.connect = DEFAULT_BE_CONNTO;
	listener_counter = 0;
}

static struct zproxy_proxy_cfg *zproxy_proxy_cfg_alloc(const struct zproxy_cfg *cfg)
{
	struct zproxy_proxy_cfg *proxy_cfg;

	proxy_cfg = (struct zproxy_proxy_cfg *)calloc(1, sizeof(struct zproxy_proxy_cfg));
	if (!proxy_cfg)
		return NULL;

	INIT_LIST_HEAD(&proxy_cfg->service_list);
	proxy_cfg->cfg = cfg;

	return proxy_cfg;
}

static void zproxy_proxy_ssl_cfg_init(struct zproxy_cfg *cfg,
				      struct zproxy_proxy_cfg *proxy,
				      bool ssl_enabled)
{
	proxy->runtime.ssl_enabled = ssl_enabled;
	proxy->ssl.ssl_op_disable = SSL_OP_ALLOW_UNSAFE_LEGACY_RENEGOTIATION |
				    SSL_OP_LEGACY_SERVER_CONNECT |
				    SSL_OP_DONT_INSERT_EMPTY_FRAGMENTS;
	snprintf(proxy->ssl.ciphers, CONFIG_IDENT_MAX, DEFAULT_SSL_CIPHERS);
	INIT_LIST_HEAD(&proxy->runtime.ssl_certs);
	INIT_LIST_HEAD(&proxy->ssl.cert_paths);
}

static void zproxy_proxy_cfg_init(struct zproxy_cfg *cfg,
				  struct zproxy_proxy_cfg *proxy,
				  bool ssl_enabled)
{
	zproxy_proxy_ssl_cfg_init(cfg, proxy, ssl_enabled);

	proxy->timer.client = cfg->timer.client;
	proxy->header.rw_url_rev = DEFAULT_RW_URL_REV;
	proxy->header.rw_location = DEFAULT_RW_LOCATION;
	proxy->header.rw_destination = DEFAULT_RW_LOCATION;
	proxy->header.rw_host = DEFAULT_RW_LOCATION;
	proxy->id = listener_counter++;

	proxy->log_level = cfg->args.log_level;

	INIT_LIST_HEAD(&proxy->runtime.replace_header_req);
	INIT_LIST_HEAD(&proxy->runtime.replace_header_res);
	INIT_LIST_HEAD(&proxy->runtime.del_header_req);
	INIT_LIST_HEAD(&proxy->runtime.del_header_res);
}

static void zproxy_proxy_ssl_cfg_free(struct zproxy_proxy_cfg *proxy)
{
	struct sni_cert_ctx *cert, *next;
	struct cert_path *path, *next_path;
	unsigned int i;

	list_for_each_entry_safe(cert, next, &proxy->runtime.ssl_certs, list) {
		zproxy_ssl_ctx_free(cert->ctx);
		regfree(&cert->server_name);

		for (i = 0; i < cert->subjectAltNameCount; i++)
			free(*(cert->subjectAltNames + i));
		free(cert->subjectAltNames);
		list_del(&cert->list);
		free(cert);
	}

	list_for_each_entry_safe(path, next_path, &proxy->ssl.cert_paths, list) {
		list_del(&path->list);
		free(path);
	}
}

static struct zproxy_service_cfg *zproxy_service_cfg_check(struct zproxy_proxy_cfg *proxy, std::string svc_name)
{
	struct zproxy_service_cfg *cfg, *next;

	list_for_each_entry_safe(cfg, next, &proxy->service_list, list)
		if (strncmp(cfg->name, svc_name.c_str(), CONFIG_IDENT_MAX) == 0)
			return cfg;

	return NULL;
}

static struct zproxy_service_cfg *zproxy_service_cfg_alloc(void)
{
	struct zproxy_service_cfg *cfg;

	cfg = (struct zproxy_service_cfg *)calloc(1, sizeof(struct zproxy_service_cfg));
	if (!cfg)
		return NULL;

	INIT_LIST_HEAD(&cfg->backend_list);

	return cfg;
}

static void zproxy_backend_cfg_free(struct zproxy_backend_cfg *backend)
{
	zproxy_ssl_ctx_free(backend->runtime.ssl_ctx);
	list_del(&backend->list);
	free(backend);
}

static void zproxy_service_cfg_init(struct zproxy_proxy_cfg *proxy, struct zproxy_service_cfg *service)
{
	if (proxy->name[0])
		snprintf(service->name, CONFIG_IDENT_MAX, "%s", proxy->name);
	service->proxy = proxy;
	service->session.sess_type = SESS_TYPE::SESS_NONE;
	service->header.rw_url_rev = proxy->header.rw_url_rev;
	service->header.rw_location = proxy->header.rw_location;
	service->header.sts = -1;
	service->ignore_case = proxy->ignore_case;
	INIT_LIST_HEAD(&service->runtime.del_header_req);
	INIT_LIST_HEAD(&service->runtime.del_header_res);
	INIT_LIST_HEAD(&service->runtime.req_head);
	INIT_LIST_HEAD(&service->runtime.deny_head);
	INIT_LIST_HEAD(&service->runtime.replace_header_req);
	INIT_LIST_HEAD(&service->runtime.replace_header_res);
	INIT_LIST_HEAD(&service->runtime.req_rw_url);
	INIT_LIST_HEAD(&service->runtime.req_url);
}

static void zproxy_replace_header_list_cfg_free(struct list_head *head)
{
	struct replace_header *header, *hnext;

	list_for_each_entry_safe(header, hnext, head, list) {
		regfree(&header->name);
		regfree(&header->match);
		list_del(&header->list);
		free(header);
	}
}

static void zproxy_matcher_list_cfg_free(struct list_head *head)
{
	struct matcher *match, *mnext;

	list_for_each_entry_safe(match, mnext, head, list) {
		regfree(&match->pat);
		list_del(&match->list);
		free(match);
	}
}

static void zproxy_service_cfg_free(struct zproxy_service_cfg *service)
{
	zproxy_backend_cfg *backend, *next;

	list_for_each_entry_safe(backend, next, &service->backend_list, list)
		zproxy_backend_cfg_free(backend);

	zproxy_matcher_list_cfg_free(&service->runtime.del_header_req);
	zproxy_matcher_list_cfg_free(&service->runtime.del_header_res);
	zproxy_matcher_list_cfg_free(&service->runtime.req_head);
	zproxy_matcher_list_cfg_free(&service->runtime.deny_head);
	zproxy_replace_header_list_cfg_free(&service->runtime.replace_header_req);
	zproxy_replace_header_list_cfg_free(&service->runtime.replace_header_res);
	zproxy_replace_header_list_cfg_free(&service->runtime.req_rw_url);
	zproxy_matcher_list_cfg_free(&service->runtime.req_url);

	list_del(&service->list);
	free(service);
}

void zproxy_backend_cfg_init(const struct zproxy_cfg *cfg,
			     struct zproxy_service_cfg *service,
			     struct zproxy_backend_cfg *backend)
{
	backend->runtime.ssl_enabled = DEFAULT_SSL_CONFIG;
	backend->service = service;
	backend->type = service->redirect.be_type;
	backend->timer.backend = cfg->timer.backend;
	backend->timer.connect = cfg->timer.connect;
	backend->priority = DEFAULT_BACKEND_PRIORITY;
	backend->weight = DEFAULT_BACKEND_WEIGHT;
	backend->connection_limit = DEFAULT_BACKEND_CONN_LIMIT;
	backend->nf_mark = DEFAULT_BACKEND_NFMARK;
}

struct zproxy_backend_cfg *
zproxy_backend_cfg_lookup(const struct zproxy_service_cfg *service,
			  const struct sockaddr_in *addr)
{
	struct zproxy_backend_cfg *backend;
	const struct sockaddr_in *backend_addr;

	list_for_each_entry(backend, &service->backend_list, list) {
		backend_addr = &backend->runtime.addr;
		if (backend_addr->sin_addr.s_addr == addr->sin_addr.s_addr &&
		    backend_addr->sin_port == addr->sin_port) {
			return backend;
		}
	}

	return nullptr;
}

struct zproxy_backend_cfg *zproxy_backend_cfg_alloc(void)
{
	return (struct zproxy_backend_cfg *)calloc(1, sizeof(struct zproxy_backend_cfg));
}

int zproxy_regex_exec(const char *expr, const char *buf, regmatch_t *matches)
{
	regex_t regex;
	int found = 0;

	if (regcomp(&regex, expr, REG_ICASE | REG_EXTENDED))
		return found;

	if (!regexec(&regex, buf, CONFIG_MAX_PARAMS, matches, 0))
		found = 1;

	regfree(&regex);

	return found;
}

static const char *zproxy_cfg_file_gets(struct zproxy_cfg *cfg,
					char *buf, const int max, FILE *fd)
{
	regmatch_t matches[CONFIG_MAX_PARAMS] = {};
	int i;

	for (;;) {
		if (!fgets(buf, max, fd))
			return NULL;

		n_lin++;
		for (i = 0; i < max; i++)
			if (buf[i] == '\n' || buf[i] == '\r') {
				buf[i] = '\0';
				break;
			}

		if (zproxy_regex_exec(CONFIG_REGEX_Empty, buf, matches) ||
			zproxy_regex_exec(CONFIG_REGEX_Comment, buf, matches) ||
			zproxy_regex_exec(CONFIG_REGEX_Include, buf, matches) ||
			zproxy_regex_exec(CONFIG_REGEX_IncludeDir, buf, matches))
			continue;

		return buf;
	}
}

static std::string file2str(const char *fname, int *err)
{
	struct stat st { };
	*err = 0;

	if (stat(fname, &st)) {
		*err = 1;
		return "";
	}

	std::ifstream t(fname, std::ios_base::in);
	std::string res((std::istreambuf_iterator<char>(t)), std::istreambuf_iterator<char>());

	return res;
}

static int parseReplaceHeader(struct zproxy_cfg *cfg,
				char *lin, regmatch_t *matches,
				struct list_head *replace_header_req,
				struct list_head *replace_header_res)
{
	for (int i = 1; i <= CONFIG_MAX_PARAMS; i++)
		lin[matches[i].rm_eo] = '\0';
	auto type_ = std::string(lin + matches[1].rm_so);
	auto name_ = std::string(lin + matches[2].rm_so);
	auto match_ = std::string(lin + matches[3].rm_so);
	auto replace_ = std::string(lin + matches[4].rm_so);
	struct replace_header *current;
	struct list_head *lcurrent;

	if (!strcasecmp(type_.data(), "Request")) {
		lcurrent = replace_header_req;
	} else if (!strcasecmp(type_.data(), "Response")) {
		lcurrent = replace_header_res;
	} else {
		parse_error("ReplaceHeader type not specified");
	}

	current = (struct replace_header *) calloc(1, sizeof(struct replace_header));
	if (!current)
		parse_error("ReplaceHeader config: out of memory");

	snprintf(current->name_str, CONFIG_IDENT_MAX, "%s", name_.data());
	snprintf(current->match_str, CONFIG_IDENT_MAX, "%s", match_.data());
	snprintf(current->replace, CONFIG_IDENT_MAX, "%s", replace_.data());

	list_add_tail(&current->list, lcurrent);
	return 0;
err:
	return -1;
}

static void parseAddHeader(struct zproxy_cfg *cfg, char *add_head, char *lin, regmatch_t *matches)
{
	lin[matches[1].rm_eo] = '\0';
	if (strlen(add_head) == 0) {
		snprintf(add_head, CONFIG_MAXBUF, "%s", lin + matches[1].rm_so);
	} else {
		strncat(add_head, "\r\n", CONFIG_MAXBUF - strlen(add_head));
		strncat(add_head, lin + matches[1].rm_so,
			CONFIG_MAXBUF - strlen(add_head));
	}
}

static int parseRemoveHeader(struct zproxy_cfg *cfg, struct list_head *head_off, char *lin, regmatch_t *matches)
{
	struct matcher *m = (struct matcher *) calloc(1, sizeof(struct matcher));
	if (!m)
		parse_error("RemoveHeader config: out of memory");

	lin[matches[1].rm_eo] = '\0';
	snprintf(m->pat_str, CONFIG_IDENT_MAX, "%s", lin + matches[1].rm_so);

	list_add_tail(&m->list, head_off);
	return 0;
err:
	return -1;
}

static char *conf_fgets(struct zproxy_cfg *cfg, char *buf, const int max, FILE *fd)
{
	regmatch_t matches[CONFIG_MAX_PARAMS] = {};
	int i;

	for (;;) {
		if (!fgets(buf, max, fd))
			return NULL;

		n_lin++;
		for (i = 0; i < max; i++)
			if (buf[i] == '\n' || buf[i] == '\r') {
				buf[i] = '\0';
				break;
			}

		if (zproxy_regex_exec(CONFIG_REGEX_Empty, buf, matches) ||
		    zproxy_regex_exec(CONFIG_REGEX_Comment, buf, matches) ||
		    zproxy_regex_exec(CONFIG_REGEX_Include, buf, matches) ||
		    zproxy_regex_exec(CONFIG_REGEX_IncludeDir, buf, matches))
			continue;

		return buf;
	}
}

static int parseRedirect(struct zproxy_backend_redirect * be, char *lin,
			 regmatch_t *matches, bool empty_req_url)
{
	be->enabled = true;
	be->be_type = 302;
	be->redir_type = 0;

	if (matches[1].rm_eo != matches[1].rm_so &&
	    (lin[matches[1].rm_so] & ~0x20) == 'A') {
		be->redir_type = 2;
	} else {
		const size_t lin_size = strlen(lin);
		for (size_t i = 0; lin[i] != '\0'; ++i) {
			if (lin[i] == '$' &&
			    i+1 < lin_size && // to avoid a segfault in the next condition
			    IN_RANGE(lin[i+1], '1', '9')) {
				if (empty_req_url)
					parse_error("Regex replace redirect requires prior definition of URL line");
				be->redir_type = 1;
			}
		}
	}

	if (matches[2].rm_eo != matches[2].rm_so)
		be->be_type = atoi(lin + matches[2].rm_so);

	lin[matches[3].rm_eo] = '\0';
	snprintf(be->url, CONFIG_MAXBUF, "%s", lin + matches[3].rm_so);

	/* split the URL into its fields */
	if (zproxy_regex_exec(CONFIG_REGEX_LOCATION, lin, matches))
		parse_error("Redirect bad URL");

	if ((matches[3].rm_eo - matches[3].rm_so) == 1) {
		/* the path is a single '/', so remove it */
		be->url[0] = '\0';
	}

	if (strstr(be->url, MACRO::VHOST_STR))
		be->redir_macro = true;

	return 0;
err:
	return -1;

}

static int parseSession(struct zproxy_cfg *cfg,
			struct zproxy_service_cfg *service, FILE *fd)
{
	regmatch_t matches[CONFIG_MAX_PARAMS] = {};
	char lin[ZCU_DEF_BUFFER_SIZE], *cp, *parm;
	parm = nullptr;

	while (conf_fgets(cfg, lin, ZCU_DEF_BUFFER_SIZE, fd)) {
		if (strlen(lin) > 0 && lin[strlen(lin) - 1] == '\n')
			lin[strlen(lin) - 1] = '\0';
		if (zproxy_regex_exec(CONFIG_REGEX_Type, lin, matches)) {
			if (service->session.sess_type != SESS_TYPE::SESS_NONE)
				parse_error("Multiple Session types in one Service - aborted");
			lin[matches[1].rm_eo] = '\0';
			cp = lin + matches[1].rm_so;
			if (!strcasecmp(cp, "IP"))
				service->session.sess_type = SESS_TYPE::SESS_IP;
			else if (!strcasecmp(cp, "COOKIE"))
				service->session.sess_type = SESS_TYPE::SESS_COOKIE;
			else if (!strcasecmp(cp, "BACKENDCOOKIE"))
				service->session.sess_type = SESS_TYPE::SESS_BCK_COOKIE;
			else if (!strcasecmp(cp, "URL"))
				service->session.sess_type = SESS_TYPE::SESS_URL;
			else if (!strcasecmp(cp, "PARM"))
				service->session.sess_type = SESS_TYPE::SESS_PARM;
			else if (!strcasecmp(cp, "BASIC"))
				service->session.sess_type = SESS_TYPE::SESS_BASIC;
			else if (!strcasecmp(cp, "HEADER"))
				service->session.sess_type = SESS_TYPE::SESS_HEADER;
			else
				parse_error("Unknown Session type");
		} else if (zproxy_regex_exec(CONFIG_REGEX_TTL, lin, matches)) {
			service->session.sess_ttl = std::atoi(lin + matches[1].rm_so);

		} else if (zproxy_regex_exec(CONFIG_REGEX_ID, lin, matches)) {
			lin[matches[1].rm_eo] = '\0';
			snprintf(service->session.sess_id, CONFIG_IDENT_MAX, "%s", lin + matches[1].rm_so);

			if (service->session.sess_type != SESS_TYPE::SESS_COOKIE &&
				service->session.sess_type != SESS_TYPE::SESS_BCK_COOKIE &&
				service->session.sess_type != SESS_TYPE::SESS_URL &&
				service->session.sess_type != SESS_TYPE::SESS_HEADER)
				parse_error("no ID permitted unless COOKIE/URL/HEADER Session");

			if ((parm = strdup(lin + matches[1].rm_so)) == nullptr)
				parse_error("ID config: out of memory");
		} else if (zproxy_regex_exec(CONFIG_REGEX_SessDomain, lin, matches)) {
			lin[matches[1].rm_eo] = '\0';
			if (matches[1].rm_so == matches[1].rm_eo)
				parse_error("Domain cannot be empty");
			snprintf(service->session.sess_domain, CONFIG_IDENT_MAX, "%s", lin + matches[1].rm_so);
		} else if (zproxy_regex_exec(CONFIG_REGEX_SessPath, lin, matches)) {
			lin[matches[1].rm_eo] = '\0';
			if (matches[1].rm_so == matches[1].rm_eo)
				parse_error("Path cannot be empty");
			snprintf(service->session.sess_path, CONFIG_IDENT_MAX, "%s", lin + matches[1].rm_so);
		} else if (zproxy_regex_exec(CONFIG_REGEX_End, lin, matches)) {
			if (service->session.sess_type == SESS_TYPE::SESS_NONE)
				parse_error("Session type not defined");
			if (service->session.sess_ttl == 0)
				parse_error("Session TTL not defined");
			if (service->session.sess_domain[0] && service->session.sess_type != SESS_TYPE::SESS_BCK_COOKIE)
				parse_error("Session Domain is valid only for BackendCookie sessions");
			if (service->session.sess_path[0] && service->session.sess_type != SESS_TYPE::SESS_BCK_COOKIE)
				parse_error("Session Paths is valid only for BackendCookie sessions");
			if ((service->session.sess_type == SESS_TYPE::SESS_COOKIE ||
				 service->session.sess_type == SESS_TYPE::SESS_URL ||
				 service->session.sess_type == SESS_TYPE::SESS_HEADER) &&
				parm == nullptr)
				parse_error("Session ID not defined");
			if (parm != nullptr)
				free(parm);

			return 0;
		} else
			parse_error("unknown directive");
	}

	parse_error("Session premature EOF");
	return 0;
err:
	return -1;
}

int zproxy_backend_ctx_start(struct zproxy_backend_cfg *bck)
{
	return zproxy_ssl_backend_ctx_alloc(bck);
}

void setBackendCookieHeader(zproxy_service_cfg *service,
				    zproxy_backend_cfg *backend,
				    char *set_cookie_header)
{
	size_t cookie_hdr_len = 0;

	if (strlen(backend->runtime.cookie_key) == 0) {
		snprintf(backend->runtime.cookie_key, CONFIG_IDENT_MAX - 1,
			 "4-%08x-%x", htonl(backend->runtime.addr.sin_addr.s_addr),
			 htonl(backend->runtime.addr.sin_port));
	}

	cookie_hdr_len = strlen(set_cookie_header);

	snprintf(set_cookie_header + cookie_hdr_len,
		 CONFIG_IDENT_MAX - cookie_hdr_len,
		 "%s=%s", service->session.sess_id, backend->runtime.cookie_key);

	if (service->session.sess_domain[0]) {
		cookie_hdr_len = strlen(set_cookie_header);
		snprintf(set_cookie_header + cookie_hdr_len,
			 CONFIG_IDENT_MAX - cookie_hdr_len,
			 "; Domain=%s", service->session.sess_domain);
	}
	if (service->session.sess_path[0]) {
		cookie_hdr_len = strlen(set_cookie_header);
		snprintf(set_cookie_header + cookie_hdr_len,
			 CONFIG_IDENT_MAX - cookie_hdr_len,
			 "; Path=%s", service->session.sess_path);
	}

	if (service->session.sess_ttl > 0) {
		cookie_hdr_len = strlen(set_cookie_header);
		snprintf(set_cookie_header + cookie_hdr_len,
			 CONFIG_IDENT_MAX - cookie_hdr_len,
			 "; Max-Age=%d", service->session.sess_ttl * 1000);
	}
}

static bool zproxy_backend_id_exists(const struct zproxy_backend_cfg *new_backend,
				     const struct zproxy_service_cfg *service)
{
	struct zproxy_backend_cfg *backend;

	list_for_each_entry(backend, &service->backend_list, list) {
		if (!strcmp(backend->runtime.id, new_backend->runtime.id)) {
			return true;
		}
	}

	return false;
}

static bool zproxy_backend_id_collision(const struct zproxy_backend_cfg *new_backend)
{
	const struct zproxy_cfg *cfg = new_backend->service->proxy->cfg;
	const struct zproxy_service_cfg *service;
	const struct zproxy_proxy_cfg *proxy;

	/* search for an existing backend with this ID in the service configuration. */
	list_for_each_entry(proxy, &cfg->proxy_list, list) {
		list_for_each_entry(service, &proxy->service_list, list) {
			if (strncmp(service->name, new_backend->service->name, CONFIG_IDENT_MAX))
				continue;
			if (zproxy_backend_id_exists(new_backend, service))
				return true;
		}
	}

	/* search for an existing backend with this ID in this new proxy service with same name. */
	service = new_backend->service;
	if (zproxy_backend_id_exists(new_backend, service))
		return true;

	if (zproxy_backend_id_exists(new_backend, new_backend->service))
		return true;

	return false;
}

static int zproxy_backend_cfg_file(zproxy_cfg *cfg, zproxy_service_cfg *service,
				   FILE *fd)
{
	regmatch_t matches[CONFIG_MAX_PARAMS] = {};
	char lin[ZCU_DEF_BUFFER_SIZE];
	zproxy_backend_cfg *backend;
	int has_addr = 0, has_port = 0;
	addrinfo addr{};

	backend = zproxy_backend_cfg_alloc();
	if (!backend)
		return -1;

	zproxy_backend_cfg_init(cfg, service, backend);

	while (conf_fgets(cfg, lin, ZCU_DEF_BUFFER_SIZE, fd)) {
		if (strlen(lin) > 0 && lin[strlen(lin) - 1] == '\n')
			lin[strlen(lin) - 1] = '\0';

		if (zproxy_regex_exec(CONFIG_REGEX_Address, lin, matches)) {
			lin[matches[1].rm_eo] = '\0';
			addrinfo addr{};
			if (zcu_net_get_host(lin + matches[1].rm_so, &addr, PF_UNSPEC, 0)) {
				/* if we can't resolve it, maybe this is a UNIX domain socket */
				if (std::string_view(lin + matches[1].rm_so,
							 matches[1].rm_eo -
								 matches[1].rm_so)
						.find('/') != std::string::npos) {
					if ((strlen(lin + matches[1].rm_so) + 1) > CONFIG_UNIX_PATH_MAX)
						parse_error("UNIX path name too long");
				} else {
					// maybe the backend still not available, we set it as down;
					zcu_log_print(
						LOG_WARNING,
						"line %d: Could not resolve backend host \"%s\".",
						n_lin,
						lin + matches[1].rm_so);
				}
			}
			free(addr.ai_addr);
			snprintf(backend->address, CONFIG_MAX_FIN, "%s", lin + matches[1].rm_so);
			backend->runtime.addr.sin_addr.s_addr = inet_addr(backend->address);
			backend->runtime.addr.sin_family = AF_INET;
			has_addr = 1;
		} else if (zproxy_regex_exec(CONFIG_REGEX_Port, lin, matches)) {
			lin[matches[1].rm_eo] = '\0';
			backend->port = std::atoi(lin + matches[1].rm_so);
			backend->runtime.addr.sin_port = htons(backend->port);
			has_port = 1;
		} else if (zproxy_regex_exec(CONFIG_REGEX_BackendKey, lin, matches)) { // NOT USED
		} else if (zproxy_regex_exec(CONFIG_REGEX_SSLConfigFile, lin, matches)) { // NOT USED
		} else if (zproxy_regex_exec(CONFIG_REGEX_SSLConfigSection, lin, matches)) { // NOT USED
		} else if (zproxy_regex_exec(CONFIG_REGEX_Priority, lin, matches)) {
			backend->priority = std::atoi(lin + matches[1].rm_so);
		} else if (zproxy_regex_exec(CONFIG_REGEX_Weight, lin, matches)) {
			backend->weight = std::atoi(lin + matches[1].rm_so);
		} else if (zproxy_regex_exec(CONFIG_REGEX_TimeOut, lin, matches)) {
			backend->timer.backend = std::atoi(lin + matches[1].rm_so);
		} else if (zproxy_regex_exec(CONFIG_REGEX_NfMark, lin, matches)) {
			backend->nf_mark = std::atoi(lin + matches[1].rm_so);
		} else if (zproxy_regex_exec(CONFIG_REGEX_NfMark_Hex, lin, matches)) {
			backend->nf_mark = strtoul(lin + matches[1].rm_so, NULL, 0);
		} else if (zproxy_regex_exec(CONFIG_REGEX_ConnLimit, lin, matches)) {
			backend->connection_limit =
				std::atoi(lin + matches[1].rm_so);
		} else if (zproxy_regex_exec(CONFIG_REGEX_ConnTO, lin, matches)) {
			backend->timer.connect = std::atoi(lin + matches[1].rm_so);
			if (backend->timer.connect >= service->proxy->cfg->timer.maintenance)
				parse_error("Alive must be greater than ConnTo");
		} else if (zproxy_regex_exec(CONFIG_REGEX_HTTPS, lin, matches)) {
			backend->runtime.ssl_enabled = true;
		} else if (zproxy_regex_exec(CONFIG_REGEX_Cert, lin, matches)) { // NOT USED
		} else if (zproxy_regex_exec(CONFIG_REGEX_Ciphers, lin, matches)) { // NOT USED
		} else if (zproxy_regex_exec(CONFIG_REGEX_DisableProto, lin, matches)) { // NOT USED
		} else if (zproxy_regex_exec(CONFIG_REGEX_ECDHCurve, lin, matches)) { // NOT USED
		} else if (zproxy_regex_exec(CONFIG_REGEX_End, lin, matches)) {
			if (!has_addr)
				parse_error("BackEnd missing Address");
			if ((addr.ai_family == AF_INET ||
				 addr.ai_family == AF_INET6) &&
				!has_port)
				parse_error("BackEnd missing Port");
			free(addr.ai_addr);

			snprintf(backend->runtime.id, CONFIG_IDENT_MAX, "%s-%d",
				 backend->address, backend->port);

			if (zproxy_backend_id_collision(backend))
				parse_error("Cannot have two backends with the same address and port.");

			list_add_tail(&backend->list, &service->backend_list);
			service->backend_list_size++;
			if (service->session.sess_type == SESS_TYPE::SESS_BCK_COOKIE)
				setBackendCookieHeader(service, backend, backend->cookie_set_header);

			return 0;
		} else {
			free(addr.ai_addr);
			parse_error("unknown directive in backend context");
		}
	}

	parse_error("BackEnd premature EOF");
err:
	return -1;
}

static int zproxy_backend_cfg_prepare(struct zproxy_backend_cfg *backend)
{
	if (backend->runtime.ssl_enabled)
		zproxy_backend_ctx_start(backend);
	return 0;
}

static int zproxy_service_cfg_prepare(struct zproxy_service_cfg *service)
{
	struct replace_header *tmp_replace_header;
	struct matcher *tmp_matcher;
	struct zproxy_backend_cfg *tmp_backend;

	list_for_each_entry(tmp_matcher, &service->runtime.del_header_req, list) {
		if (regcomp(&tmp_matcher->pat, tmp_matcher->pat_str,
			    REG_ICASE | REG_NEWLINE | REG_EXTENDED)) {
			zcu_log_print(LOG_ERR, "Failed to compile regular expression '%s'",
				      tmp_matcher->pat_str);
			return -1;
		}
	}
	list_for_each_entry(tmp_matcher, &service->runtime.del_header_res, list) {
		if (regcomp(&tmp_matcher->pat, tmp_matcher->pat_str,
			    REG_ICASE | REG_NEWLINE | REG_EXTENDED)) {
			zcu_log_print(LOG_ERR, "Failed to compile regular expression '%s'",
				      tmp_matcher->pat_str);
			return -1;
		}
	}

	list_for_each_entry(tmp_matcher, &service->runtime.req_head, list) {
		if (regcomp(&tmp_matcher->pat, tmp_matcher->pat_str,
			    REG_ICASE | REG_NEWLINE | REG_EXTENDED)) {
			zcu_log_print(LOG_ERR, "Failed to compile regular expression '%s'",
				      tmp_matcher->pat_str);
			return -1;
		}
	}
	list_for_each_entry(tmp_matcher, &service->runtime.deny_head, list) {
		if (regcomp(&tmp_matcher->pat, tmp_matcher->pat_str,
			    REG_ICASE | REG_NEWLINE | REG_EXTENDED)) {
			zcu_log_print(LOG_ERR, "Failed to compile regular expression '%s'",
				      tmp_matcher->pat_str);
			return -1;
		}
	}

	list_for_each_entry(tmp_replace_header, &service->runtime.replace_header_req,
			    list) {
		if (regcomp(&tmp_replace_header->name, tmp_replace_header->name_str,
			    REG_ICASE | REG_NEWLINE | REG_EXTENDED)) {
			zcu_log_print(LOG_ERR, "Failed to compile regular expression.");
			return -1;
		}
		if (regcomp(&tmp_replace_header->match, tmp_replace_header->match_str,
			    REG_ICASE | REG_NEWLINE | REG_EXTENDED)) {
			zcu_log_print(LOG_ERR, "Failed to compile regular expression.");
			regfree(&tmp_replace_header->name);
			return -1;
		}
	}
	list_for_each_entry(tmp_replace_header, &service->runtime.replace_header_res,
			    list) {
		if (regcomp(&tmp_replace_header->name, tmp_replace_header->name_str,
			    REG_ICASE | REG_NEWLINE | REG_EXTENDED)) {
			zcu_log_print(LOG_ERR, "Failed to compile regular expression '%s'",
				      tmp_replace_header->name_str);
			return -1;
		}
		if (regcomp(&tmp_replace_header->match, tmp_replace_header->match_str,
			    REG_ICASE | REG_NEWLINE | REG_EXTENDED)) {
			zcu_log_print(LOG_ERR, "Failed to compile regular expression '%s'",
				      tmp_replace_header->match_str);
			regfree(&tmp_replace_header->name);
			return -1;
		}
	}

	list_for_each_entry(tmp_replace_header, &service->runtime.req_rw_url, list) {
		if (regcomp(&tmp_replace_header->match, tmp_replace_header->match_str,
			    REG_ICASE | REG_NEWLINE | REG_EXTENDED)) {
			zcu_log_print(LOG_ERR, "Failed to compile regular expression '%s'",
				      tmp_replace_header->match_str);
			regfree(&tmp_replace_header->name);
			return -1;
		}
	}

	list_for_each_entry(tmp_matcher, &service->runtime.req_url, list) {
		if (regcomp(&tmp_matcher->pat, tmp_matcher->pat_str,
			    REG_ICASE | REG_NEWLINE | REG_EXTENDED)) {
			zcu_log_print(LOG_ERR, "Failed to compile regular expression '%s'",
				      tmp_matcher->pat_str);
			return -1;
		}
	}

	list_for_each_entry(tmp_backend, &service->backend_list, list) {
		if (zproxy_backend_cfg_prepare(tmp_backend) < 0)
			return -1;
	}

	return 0;
}

static int zproxy_service_cfg_file(struct zproxy_cfg *cfg,
				   struct zproxy_proxy_cfg *proxy,
				   std::string svc_name, FILE *fd)
{
	regmatch_t matches[CONFIG_MAX_PARAMS] = {};
	char lin[ZCU_DEF_BUFFER_SIZE] = {0};
	zproxy_service_cfg *service;

	service = zproxy_service_cfg_check(proxy, svc_name);
	if (service) {
		fprintf(stderr, "Service name already exists: %s\n", svc_name.c_str());
		return -1;
	}

	service = zproxy_service_cfg_alloc();
	if (!service)
		return -1;

	zproxy_service_cfg_init(proxy, service);
	if (!svc_name.empty())
		snprintf(service->name, CONFIG_IDENT_MAX, "%s", svc_name.c_str());

	while (conf_fgets(cfg, lin, ZCU_DEF_BUFFER_SIZE, fd)) {
		if (strlen(lin) > 0 && lin[strlen(lin) - 1] == '\n')
			lin[strlen(lin) - 1] = '\0';
		if (zproxy_regex_exec(CONFIG_REGEX_URL, lin, matches)) {
			struct matcher *m = (struct matcher *) calloc(1, sizeof(struct matcher));
			if (!m)
				parse_error("URL out of memory error");
			lin[matches[1].rm_eo] = '\0';
			snprintf(m->pat_str, CONFIG_IDENT_MAX, "%s", lin + matches[1].rm_so);
			list_add_tail(&m->list, &service->runtime.req_url);
		} else if (zproxy_regex_exec(CONFIG_REGEX_ReplaceHeader, lin, matches)) {
			if (parseReplaceHeader(cfg, lin, matches,
					   &service->runtime.replace_header_req,
					   &service->runtime.replace_header_res) < 0)
				return -1;
		} else if (zproxy_regex_exec(CONFIG_REGEX_OrURLs, lin, matches)) { // NOT USED
		} else if (zproxy_regex_exec(CONFIG_REGEX_HeadRequire, lin, matches)) {
			struct matcher *m = (struct matcher *) calloc(1, sizeof(struct matcher));
			if (!m)
				parse_error("HeadRequire out of memory error");
			lin[matches[1].rm_eo] = '\0';
			snprintf(m->pat_str, CONFIG_IDENT_MAX, "%s", lin + matches[1].rm_so);
			list_add_tail(&m->list, &service->runtime.req_head);
		} else if (zproxy_regex_exec(CONFIG_REGEX_HeadDeny, lin, matches)) {
			struct matcher *m = (struct matcher *) calloc(1, sizeof(struct matcher));
			if (!m)
				parse_error("HeadDeny out of memory error");
			lin[matches[1].rm_eo] = '\0';
			snprintf(m->pat_str, CONFIG_IDENT_MAX, "%s", lin + matches[1].rm_so);
			list_add_tail(&m->list, &service->runtime.deny_head);
		} else if (zproxy_regex_exec(CONFIG_REGEX_RewriteUrl, lin, matches)) {
			lin[matches[1].rm_eo] = '\0';
			lin[matches[2].rm_eo] = '\0';
			if (matches[3].rm_eo > 0)
				lin[matches[3].rm_eo] = '\0';
			auto match_ = std::string(lin + matches[1].rm_so);
			auto replace_ = std::string(lin + matches[2].rm_so);
			struct replace_header *current = (struct replace_header *) calloc(1, sizeof(struct replace_header));
			if (!current)
				parse_error("RewriteUrl out of memory error");
			snprintf(current->match_str, CONFIG_IDENT_MAX, "%s", match_.data());
			snprintf(current->replace, CONFIG_IDENT_MAX, "%s", replace_.data());
			list_add_tail(&current->list, &service->runtime.req_rw_url);
		} else if (zproxy_regex_exec(CONFIG_REGEX_RewriteLocation, lin, matches)) {
			if (matches[1].rm_so == -1)
				parse_error("RewriteLocation requires at least one argument");
			service->header.rw_location = atoi(lin + matches[1].rm_so) ? 1 : 0;
			if (matches[2].rm_so != -1)
				service->header.rw_url_rev =
					atoi(lin + matches[2].rm_so) ? 1 : 0;
		} else if (zproxy_regex_exec(CONFIG_REGEX_AddRequestHeader, lin, matches)) {
			parseAddHeader(cfg, service->header.add_header_req, lin, matches);
		} else if (zproxy_regex_exec(CONFIG_REGEX_AddResponseHeader, lin, matches)) {
			parseAddHeader(cfg, service->header.add_header_res, lin, matches);
		} else if (zproxy_regex_exec(CONFIG_REGEX_RemoveRequestHeader, lin, matches)) {
			if (parseRemoveHeader(cfg, &service->runtime.del_header_req, lin, matches) < 0)
				return -1;
		} else if (zproxy_regex_exec(CONFIG_REGEX_RemoveResponseHeader, lin, matches)) {
			if (parseRemoveHeader(cfg, &service->runtime.del_header_res, lin, matches) < 0)
				return -1;
		} else if (zproxy_regex_exec(CONFIG_REGEX_StrictTransportSecurity, lin, matches)) {
			service->header.sts = atoi(lin + matches[1].rm_so);
		} else if (zproxy_regex_exec(CONFIG_REGEX_Redirect, lin, matches)) {
			if (parseRedirect(&service->redirect, lin, matches,
					  (bool)list_empty(&service->runtime.req_url)) == -1)
				return -1;
		} else if (zproxy_regex_exec(CONFIG_REGEX_BackEnd, lin, matches)) {
			if (zproxy_backend_cfg_file(cfg, service, fd) == -1)
				return -1;
		} else if (zproxy_regex_exec(CONFIG_REGEX_Session, lin, matches)) {
			if (parseSession(cfg, service, fd) < 0)
				return -1;
		} else if (zproxy_regex_exec(CONFIG_REGEX_DynScale, lin, matches)) {	// NOT USED
		} else if (zproxy_regex_exec(CONFIG_REGEX_RoutingPolicy, lin, matches)) {
			lin[matches[1].rm_eo] = '\0';
			std::string cp = lin + matches[1].rm_so;
			if (cp == "ROUND_ROBIN")
				service->routing_policy = ROUTING_POLICY::ROUND_ROBIN;
			else if (cp == "LEAST_CONNECTIONS")
				service->routing_policy = ROUTING_POLICY::W_LEAST_CONNECTIONS;
			else if (cp == "RESPONSE_TIME")
				service->routing_policy = ROUTING_POLICY::RESPONSE_TIME;
			else if (cp == "PENDING_CONNECTIONS")
				service->routing_policy = ROUTING_POLICY::W_LEAST_CONNECTIONS;
			else
				parse_error("Unknown routing policy");
		} else if (zproxy_regex_exec(CONFIG_REGEX_CompressionAlgorithm, lin, matches)) { // NOT USED
		} else if (zproxy_regex_exec(CONFIG_REGEX_IgnoreCase, lin, matches)) {
			service->ignore_case = atoi(lin + matches[1].rm_so);
		} else if (zproxy_regex_exec(CONFIG_REGEX_End, lin, matches)) {
			list_add_tail(&service->list, &proxy->service_list);
			return 0;
		} else
			parse_error("unknown directive in service context");
	}

	parse_error("Service premature EOF");
err:
	return -1;
}

static int generate_key(RSA **ret_rsa, unsigned long bits)
{
	int rc = 0;
	RSA *rsa;

	rsa = RSA_new();
	if (rsa) {
		BIGNUM *bne = BN_new();
		if (BN_set_word(bne, RSA_F4))
			rc = RSA_generate_key_ex(rsa, bits, bne, nullptr);
		BN_free(bne);
		if (rc)
			*ret_rsa = rsa;
		else
			RSA_free(rsa);
	}
	return rc;
}

static int zproxy_proxy_ctx_start(struct zproxy_proxy_cfg *proxy)
{
	return zproxy_ssl_ctx_configure(proxy);
}

static void zproxy_proxy_cfg_free(struct zproxy_cfg *cfg,
				  struct zproxy_proxy_cfg *proxy)
{
	zproxy_service_cfg *service, *next;

	list_for_each_entry_safe(service, next, &proxy->service_list, list)
		zproxy_service_cfg_free(service);

	if (proxy->runtime.waf_rules != nullptr && cfg->runtime.waf_refs > 0) {
		zcu_log_print(LOG_DEBUG, "Destroying WAF rules.");
		Waf::destroy_rules(proxy->runtime.waf_rules);
		cfg->runtime.waf_refs--;
	}

	if (proxy->runtime.ssl_enabled)
		zproxy_proxy_ssl_cfg_free(proxy);

	zproxy_replace_header_list_cfg_free(&proxy->runtime.replace_header_req);
	zproxy_replace_header_list_cfg_free(&proxy->runtime.replace_header_res);
	zproxy_matcher_list_cfg_free(&proxy->runtime.del_header_req);
	zproxy_matcher_list_cfg_free(&proxy->runtime.del_header_res);
	regfree(&proxy->runtime.req_url_pat_reg);
	regfree(&proxy->runtime.req_verb_reg);
	list_del(&proxy->list);
	free(proxy);
}

static int zproxy_cfg_errmsg_file(const char *path, char *errmsg)
{
	size_t len;
	FILE *fp;

	if (!path[0])
		return 0;

	fp = fopen(path, "r");
	if (!fp) {
		syslog(LOG_ERR, "Can't open error file %s", path);
		return -1;
	}

	len = fread(errmsg, sizeof(char), CONFIG_MAXBUF, fp);
	if (ferror(fp) != 0) {
		syslog(LOG_ERR, "Error when reading file %s", path);
		fclose(fp);
		return -1;
	}

	if (len >= CONFIG_MAXBUF) {
		syslog(LOG_ERR, "File %s contains too large error, max is %u",
		       path, CONFIG_MAXBUF);
		return -1;
	}

	fclose(fp);

	return 0;
}

static int zproxy_proxy_cfg_prepare(struct zproxy_proxy_cfg *proxy)
{
	int err;
	struct replace_header *tmp_replace_header;
	struct zproxy_service_cfg *service;
	struct matcher *tmp_matcher;
	struct cert_path *path;

	if (zproxy_cfg_errmsg_file(proxy->error.err414_path,
				   proxy->runtime.err414_msg) < 0)
		return -1;

	if (zproxy_cfg_errmsg_file(proxy->error.err500_path,
				   proxy->runtime.err500_msg) < 0)
		return -1;

	if (zproxy_cfg_errmsg_file(proxy->error.err501_path,
				   proxy->runtime.err501_msg) < 0)
		return -1;

	if (zproxy_cfg_errmsg_file(proxy->error.err503_path,
				   proxy->runtime.err503_msg) < 0)
		return -1;

	if (proxy->error.errnossl_path[0] == '\0') {
		snprintf(proxy->runtime.errnossl_msg, CONFIG_MAXBUF, "%s",
			 CONFIG_DEFAULT_ErrNoSsl);
	} else {
		if (zproxy_cfg_errmsg_file(proxy->error.errnossl_path,
					   proxy->runtime.errnossl_msg) < 0)
			return -1;
	}

	if (zproxy_cfg_errmsg_file(proxy->error.nossl_url_path,
				   proxy->runtime.nossl_url_msg) < 0)
		return -1;

	if (zproxy_cfg_errmsg_file(proxy->error.errwaf_path,
				   proxy->runtime.errwaf_msg) < 0)
		return -1;

	list_for_each_entry(tmp_replace_header, &proxy->runtime.replace_header_req,
			    list) {
		if (regcomp(&tmp_replace_header->name, tmp_replace_header->name_str,
			    REG_ICASE | REG_NEWLINE | REG_EXTENDED)) {
			zcu_log_print(LOG_ERR, "Failed to compile regular expression.");
			return -1;
		}
		if (regcomp(&tmp_replace_header->match, tmp_replace_header->match_str,
			    REG_ICASE | REG_NEWLINE | REG_EXTENDED)) {
			zcu_log_print(LOG_ERR, "Failed to compile regular expression.");
			regfree(&tmp_replace_header->name);
			return -1;
		}
	}
	list_for_each_entry(tmp_replace_header, &proxy->runtime.replace_header_res,
			    list) {
		if (regcomp(&tmp_replace_header->name, tmp_replace_header->name_str,
			    REG_ICASE | REG_NEWLINE | REG_EXTENDED)) {
			zcu_log_print(LOG_ERR, "Failed to compile regular expression '%s'",
				      tmp_replace_header->name_str);
			return -1;
		}
		if (regcomp(&tmp_replace_header->match, tmp_replace_header->match_str,
			    REG_ICASE | REG_NEWLINE | REG_EXTENDED)) {
			zcu_log_print(LOG_ERR, "Failed to compile regular expression '%s'",
				      tmp_replace_header->match_str);
			regfree(&tmp_replace_header->name);
			return -1;
		}
	}

	list_for_each_entry(tmp_matcher, &proxy->runtime.del_header_req, list) {
		if (regcomp(&tmp_matcher->pat, tmp_matcher->pat_str,
			    REG_ICASE | REG_NEWLINE | REG_EXTENDED)) {
			zcu_log_print(LOG_ERR, "Failed to compile regular expression '%s'",
				      tmp_matcher->pat_str);
			return -1;
		}
	}
	list_for_each_entry(tmp_matcher, &proxy->runtime.del_header_res, list) {
		if (regcomp(&tmp_matcher->pat, tmp_matcher->pat_str,
			    REG_ICASE | REG_NEWLINE | REG_EXTENDED)) {
			zcu_log_print(LOG_ERR, "Failed to compile regular expression '%s'",
				      tmp_matcher->pat_str);
			return -1;
		}
	}

	if (proxy->waf_rules_path[0]) {
		struct zproxy_cfg *cfg = (struct zproxy_cfg*)proxy->cfg;
		// initialize WAF if we haven't already
		if (cfg->runtime.waf_refs == 0) {
			cfg->runtime.waf_api = Waf::init_api();
		}
		cfg->runtime.waf_refs++;

		if (Waf::parse_conf(proxy->waf_rules_path,
				    &proxy->runtime.waf_rules) < 0) {
			zcu_log_print(LOG_ERR, "Failed to load WAF Rules");
			return -1;
		}
	}

	if (regcomp(&proxy->runtime.req_url_pat_reg, proxy->request.url_pat_str,
		    REG_NEWLINE | REG_EXTENDED | (proxy->ignore_case ? REG_ICASE : 0))) {
		zcu_log_print(LOG_ERR, "Failed to compile regular expression '%s'",
			      proxy->request.url_pat_str);
		return -1;
	}

	if (regcomp(&proxy->runtime.req_verb_reg, xhttp[proxy->request.verb],
		    REG_ICASE | REG_NEWLINE | REG_EXTENDED)) {
		regfree(&proxy->runtime.req_url_pat_reg);
		return -1;
	}

	list_for_each_entry(service, &proxy->service_list, list) {
		if (zproxy_service_cfg_prepare(service) < 0) {
			regfree(&proxy->runtime.req_url_pat_reg);
			regfree(&proxy->runtime.req_verb_reg);
			return -1;
		}
	}

	list_for_each_entry(path, &proxy->ssl.cert_paths, list) {
		if (zproxy_ssl_ctx_alloc(proxy, path->path, &err) < 0) {
			switch (err) {
			case SSL_CERTFILE_ERR:
				zcu_log_print(LOG_ERR, "SSL unknown cert file error");
				return -1;
				break;
			case SSL_INIT_ERR:
				zcu_log_print(LOG_ERR, "SSL init error");
				return -1;
				break;
			case SSL_SERVERNAME_ERR:
				zcu_log_print(LOG_ERR, "SSL server name error");
				return -1;
				break;
			case SSL_LOADCB_ERR:
				zcu_log_print(LOG_ERR, "SSL loading callback error");
				return -1;
				break;
			default:
				zcu_log_print(LOG_ERR, "SSL unknown error");
				return -1;
				break;
			}
		}
	}

	return 0;
}

static int zproxy_proxy_cfg_file(struct zproxy_cfg *cfg, struct zproxy_proxy_cfg *proxy,
				 bool ssl_enabled, FILE *fd)
{
	regmatch_t matches[CONFIG_MAX_PARAMS] = {};
	char lin[ZCU_DEF_BUFFER_SIZE];
	int has_addr, has_port;

	proxy = zproxy_proxy_cfg_alloc(cfg);
	if (!proxy)
		return -1;

	zproxy_proxy_cfg_init(cfg, proxy, ssl_enabled);

	has_addr = has_port = 0;
	while (conf_fgets(cfg, lin, ZCU_DEF_BUFFER_SIZE, fd)) {
		if (strlen(lin) > 0 && lin[strlen(lin) - 1] == '\n')
			lin[strlen(lin) - 1] = '\0';
		if (zproxy_regex_exec(CONFIG_REGEX_Address, lin, matches)) {
			lin[matches[1].rm_eo] = '\0';
			snprintf(proxy->address, CONFIG_MAX_FIN, "%s", lin + matches[1].rm_so);
			proxy->runtime.addr.sin_addr.s_addr = inet_addr(proxy->address);
			proxy->runtime.addr.sin_family = AF_INET;
			has_addr = 1;
		} else if (zproxy_regex_exec(CONFIG_REGEX_WafRules, lin, matches)) {
			auto file = std::string(lin + matches[1].rm_so,
						matches[1].rm_eo -
							matches[1].rm_so);
			snprintf(proxy->waf_rules_path, CONFIG_IDENT_MAX,
				 "%s", file.data());
		} else if (zproxy_regex_exec(CONFIG_REGEX_ErrWAF, lin, matches)) {
			lin[matches[1].rm_eo] = '\0';
			snprintf(proxy->error.errwaf_path, PATH_MAX, "%s", lin + matches[1].rm_so);
		} else if (zproxy_regex_exec(CONFIG_REGEX_Name, lin, matches)) {
			lin[matches[1].rm_eo] = '\0';
			snprintf(proxy->name, CONFIG_IDENT_MAX, "%s", lin + matches[1].rm_so);
		} else if (zproxy_regex_exec(CONFIG_REGEX_Port, lin, matches)) {
			lin[matches[1].rm_eo] = '\0';
			proxy->port = atoi(lin + matches[1].rm_so);
			proxy->runtime.addr.sin_port = htons(proxy->port);
			has_port = 1;
		} else if (zproxy_regex_exec(CONFIG_REGEX_xHTTP, lin, matches)) {
			proxy->request.verb = atoi(lin + matches[1].rm_so);
		} else if (zproxy_regex_exec(CONFIG_REGEX_Client, lin, matches)) {
			proxy->timer.client = atoi(lin + matches[1].rm_so);
		} else if (zproxy_regex_exec(CONFIG_REGEX_CheckURL, lin, matches)) {
			if (proxy->request.url_pat_str[0])
				parse_error("CheckURL multiple pattern");
			lin[matches[1].rm_eo] = '\0';
			snprintf(proxy->request.url_pat_str, CONFIG_IDENT_MAX, "%s", lin + matches[1].rm_so);
		} else if (zproxy_regex_exec(CONFIG_REGEX_Err414, lin, matches)) {
			lin[matches[1].rm_eo] = '\0';
			snprintf(proxy->error.err414_path, PATH_MAX, "%s", lin + matches[1].rm_so);
		} else if (zproxy_regex_exec(CONFIG_REGEX_Err500, lin, matches)) {
			lin[matches[1].rm_eo] = '\0';
			snprintf(proxy->error.err500_path, PATH_MAX, "%s", lin + matches[1].rm_so);
		} else if (zproxy_regex_exec(CONFIG_REGEX_Err501, lin, matches)) {
			lin[matches[1].rm_eo] = '\0';
			snprintf(proxy->error.err501_path, PATH_MAX, "%s", lin + matches[1].rm_so);
		} else if (zproxy_regex_exec(CONFIG_REGEX_Err503, lin, matches)) {
			lin[matches[1].rm_eo] = '\0';
			snprintf(proxy->error.err503_path, PATH_MAX, "%s", lin + matches[1].rm_so);
		} else if (zproxy_regex_exec(CONFIG_REGEX_ErrNoSsl, lin, matches)) {
			if (matches[1].rm_eo != matches[1].rm_so) {
				lin[matches[1].rm_eo] = '\0';
				proxy->runtime.errnossl_code = atoi(lin + matches[1].rm_so);
			} else {
				proxy->runtime.errnossl_code = CONFIG_DEFAULT_ErrNoSsl_Code;
			}
			lin[matches[2].rm_eo] = '\0';
			snprintf(proxy->error.errnossl_path, PATH_MAX, "%s",
				 lin + matches[2].rm_so);
		} else if (zproxy_regex_exec(CONFIG_REGEX_NoSslRedirect, lin, matches)) {  // NOT USED
		} else if (zproxy_regex_exec(CONFIG_REGEX_ForwardSNI, lin, matches)) { // NOT USED
		} else if (zproxy_regex_exec(CONFIG_REGEX_MaxRequest, lin, matches)) {
			proxy->max_req = atoll(lin + matches[1].rm_so);
		} else if (zproxy_regex_exec(CONFIG_REGEX_RewriteLocation, lin, matches)) {

			if (matches[1].rm_so == -1)
				parse_error("RewriteLocation requires at least one argument");
			proxy->header.rw_location = atoi(lin + matches[1].rm_so) ? 1 : 0;
			if (matches[2].rm_so != -1)
				proxy->header.rw_url_rev =
					atoi(lin + matches[2].rm_so) ? 1 : 0;

		} else if (zproxy_regex_exec(CONFIG_REGEX_AddRequestHeader, lin, matches)) {
			parseAddHeader(cfg, proxy->header.add_header_req, lin, matches);
		} else if (zproxy_regex_exec(CONFIG_REGEX_AddResponseHeader, lin, matches)) {
			parseAddHeader(cfg, proxy->header.add_header_res, lin, matches);
		} else if (zproxy_regex_exec(CONFIG_REGEX_RemoveRequestHeader, lin, matches)) {
			if (parseRemoveHeader(cfg, &proxy->runtime.del_header_req, lin, matches) < 0)
				return -1;
		} else if (zproxy_regex_exec(CONFIG_REGEX_RemoveResponseHeader, lin, matches)) {
			if (parseRemoveHeader(cfg, &proxy->runtime.del_header_res, lin, matches) < 0)
				return -1;
		} else if (zproxy_regex_exec(CONFIG_REGEX_RewriteDestination, lin, matches)) {
			proxy->header.rw_destination = atoi(lin + matches[1].rm_so);
		} else if (zproxy_regex_exec(CONFIG_REGEX_RewriteHost, lin, matches)) {
			proxy->header.rw_host = atoi(lin + matches[1].rm_so);
		} else if (zproxy_regex_exec(CONFIG_REGEX_LogLevel, lin, matches)) {
			proxy->log_level = atoi(lin + matches[1].rm_so);
		} else if (zproxy_regex_exec(CONFIG_REGEX_Cert, lin, matches)) {
			struct cert_path *c_path;
			require_ssl(proxy->runtime.ssl_enabled);
			lin[matches[1].rm_eo] = '\0';
			c_path = (struct cert_path*)calloc(1, sizeof(struct cert_path));
			snprintf(c_path->path, PATH_MAX, "%s", lin + matches[1].rm_so);
			list_add_tail(&c_path->list, &proxy->ssl.cert_paths);

			if (!c_path->path[0])
				parse_error("SSL unknown cert file error");

			proxy->runtime.ssl_certs_cnt++;
		} else if (zproxy_regex_exec(CONFIG_REGEX_CertDir, lin, matches)) { // NOT USED
		} else if (zproxy_regex_exec(CONFIG_REGEX_DisableProto, lin, matches)) {
			require_ssl(proxy->runtime.ssl_enabled);
			lin[matches[1].rm_eo] = '\0';
			if (strcasecmp(lin + matches[1].rm_so, "SSLv2") == 0)
				proxy->ssl.ssl_op_enable |= SSL_OP_NO_SSLv2;
			else if (strcasecmp(lin + matches[1].rm_so, "SSLv3") == 0)
				proxy->ssl.ssl_op_enable |=
					SSL_OP_NO_SSLv2 | SSL_OP_NO_SSLv3;
#ifdef SSL_OP_NO_TLSv1
			else if (strcasecmp(lin + matches[1].rm_so, "TLSv1") == 0)
				proxy->ssl.ssl_op_enable |= SSL_OP_NO_SSLv2 |
						 SSL_OP_NO_SSLv3 |
						 SSL_OP_NO_TLSv1;
#endif
#ifdef SSL_OP_NO_TLSv1_1
			else if (strcasecmp(lin + matches[1].rm_so, "TLSv1_1") == 0)
				proxy->ssl.ssl_op_enable |=
					SSL_OP_NO_SSLv2 | SSL_OP_NO_SSLv3 |
					SSL_OP_NO_TLSv1 | SSL_OP_NO_TLSv1_1;
#endif
#ifdef SSL_OP_NO_TLSv1_2
			else if (strcasecmp(lin + matches[1].rm_so, "TLSv1_2") == 0)
				proxy->ssl.ssl_op_enable |=
					SSL_OP_NO_SSLv2 | SSL_OP_NO_SSLv3 |
					SSL_OP_NO_TLSv1 | SSL_OP_NO_TLSv1_1 |
					SSL_OP_NO_TLSv1_2;
#endif
#ifdef SSL_OP_NO_TLSv1_3
			else if (strcasecmp(lin + matches[1].rm_so, "TLSv1_3") == 0)
				proxy->ssl.ssl_op_enable |= SSL_OP_NO_TLSv1_3;
#endif
		} else if (zproxy_regex_exec(CONFIG_REGEX_ECDHCurve, lin, matches)) { // NOT USED
		} else if (zproxy_regex_exec(CONFIG_REGEX_SSLAllowClientRenegotiation, lin, matches)) {
			require_ssl(proxy->runtime.ssl_enabled);
			proxy->ssl.allow_client_reneg = atoi(lin + matches[1].rm_so);
			if (proxy->ssl.allow_client_reneg == 2) {
				proxy->ssl.ssl_op_enable |=	SSL_OP_ALLOW_UNSAFE_LEGACY_RENEGOTIATION;
				proxy->ssl.ssl_op_disable &= ~SSL_OP_ALLOW_UNSAFE_LEGACY_RENEGOTIATION;
			} else {
				proxy->ssl.ssl_op_disable |= SSL_OP_ALLOW_UNSAFE_LEGACY_RENEGOTIATION;
				proxy->ssl.ssl_op_enable &= ~SSL_OP_ALLOW_UNSAFE_LEGACY_RENEGOTIATION;
			}
		} else if (zproxy_regex_exec(CONFIG_REGEX_SSLHonorCipherOrder, lin, matches)) {
			require_ssl(proxy->runtime.ssl_enabled);
			if (std::atoi(lin + matches[1].rm_so)) {
				proxy->ssl.ssl_op_enable |=	SSL_OP_CIPHER_SERVER_PREFERENCE;
				proxy->ssl.ssl_op_disable &= ~SSL_OP_CIPHER_SERVER_PREFERENCE;
			} else {
				proxy->ssl.ssl_op_disable |= SSL_OP_CIPHER_SERVER_PREFERENCE;
				proxy->ssl.ssl_op_enable &= ~SSL_OP_CIPHER_SERVER_PREFERENCE;
			}
		} else if (zproxy_regex_exec(CONFIG_REGEX_Ciphers, lin, matches)) {
			require_ssl(proxy->runtime.ssl_enabled);
			lin[matches[1].rm_eo] = '\0';
			snprintf(proxy->ssl.ciphers, CONFIG_IDENT_MAX, "%s", lin + matches[1].rm_so);
		} else if (zproxy_regex_exec(CONFIG_REGEX_CAlist, lin, matches)) { // NOT USED
		} else if (zproxy_regex_exec(CONFIG_REGEX_VerifyList, lin, matches)) { // NOT USED
		} else if (zproxy_regex_exec(CONFIG_REGEX_SSLConfigFile, lin, matches)) { // NOT USED
		} else if (zproxy_regex_exec(CONFIG_REGEX_SSLConfigSection, lin, matches)) { // NOT USED
		} else if (zproxy_regex_exec(CONFIG_REGEX_CRLlist, lin, matches)) { // NOT USED
		} else if (zproxy_regex_exec(CONFIG_REGEX_SSLUncleanShutdown, lin, matches)) { // NOT USED
		} else if (zproxy_regex_exec(CONFIG_REGEX_ServiceName, lin, matches)) {
			lin[matches[1].rm_eo] = '\0';
			if (zproxy_service_cfg_file(cfg, proxy, lin + matches[1].rm_so, fd) == -1)
				return -1;
		} else if (zproxy_regex_exec(CONFIG_REGEX_ReplaceHeader, lin, matches)) {
			if (parseReplaceHeader(cfg, lin, matches,
					   &proxy->runtime.replace_header_req,
					   &proxy->runtime.replace_header_res) < 0)
				return -1;
		} else if (zproxy_regex_exec(CONFIG_REGEX_End, lin, matches)) {
			if (!has_addr || !has_port)
				parse_error("ListenHTTP missing Address or Port");
			if (ssl_enabled) {
				if (proxy->runtime.ssl_certs_cnt == 0)
					parse_error("ListenHTTPS missing SSL certificate");
				if (zproxy_proxy_ctx_start(proxy) == -1)
					parse_error("Error creating SSL context");
			}
			Waf::dump_rules(proxy->runtime.waf_rules);
			list_add_tail(&proxy->list, &cfg->proxy_list);
			return 0;
		} else
			parse_error("unknown directive in listener context");
	}

	parse_error("Listener premature EOF");

err:
	return -1;
}

const struct zproxy_cfg *zproxy_cfg_get(const struct zproxy_cfg *cfg)
{
	struct zproxy_cfg *_cfg = (struct zproxy_cfg *)cfg;

	_cfg->refcnt++;

	return cfg;
}

static struct zproxy_backend_cfg *
zproxy_backend_cfg_clone(const struct zproxy_backend_cfg *backend_cfg,
		         struct zproxy_service_cfg *service_cfg)
{
	struct zproxy_backend_cfg *new_backend;

	zcu_log_print(LOG_DEBUG, "Clone Backend: %s", backend_cfg->runtime.id);

	new_backend = zproxy_backend_cfg_alloc();
	if (!new_backend)
		return NULL;

	*new_backend = *backend_cfg;
	new_backend->service = service_cfg;
	new_backend->runtime.ssl_ctx = NULL;

	return new_backend;
}

static struct zproxy_service_cfg *
zproxy_service_cfg_clone(const struct zproxy_service_cfg *service_cfg,
			 struct zproxy_proxy_cfg *proxy_cfg)
{
	struct zproxy_service_cfg *new_service;

	zcu_log_print(LOG_DEBUG, "Clone Service: %s", service_cfg->name);

	new_service = zproxy_service_cfg_alloc();
	if (!new_service)
		return NULL;

	*new_service = *service_cfg;
	new_service->proxy = proxy_cfg;
	INIT_LIST_HEAD(&new_service->backend_list);
	INIT_LIST_HEAD(&new_service->runtime.del_header_req);
	INIT_LIST_HEAD(&new_service->runtime.del_header_res);
	INIT_LIST_HEAD(&new_service->runtime.req_head);
	INIT_LIST_HEAD(&new_service->runtime.deny_head);
	INIT_LIST_HEAD(&new_service->runtime.replace_header_req);
	INIT_LIST_HEAD(&new_service->runtime.replace_header_res);
	INIT_LIST_HEAD(&new_service->runtime.req_rw_url);
	INIT_LIST_HEAD(&new_service->runtime.req_url);

	return new_service;
}

static struct zproxy_proxy_cfg *
zproxy_proxy_cfg_clone(const struct zproxy_proxy_cfg *proxy_cfg,
		       struct zproxy_cfg *cfg)
{
	struct zproxy_proxy_cfg *new_proxy;
	struct cert_path *cert_path;

	zcu_log_print(LOG_DEBUG, "Clone Listener: %s", proxy_cfg->name);

	new_proxy = zproxy_proxy_cfg_alloc(cfg);
	if (!new_proxy)
		return NULL;

	*new_proxy = *proxy_cfg;
	new_proxy->cfg = cfg;
	INIT_LIST_HEAD(&new_proxy->service_list);
	INIT_LIST_HEAD(&new_proxy->ssl.cert_paths); // TODO: Fill this!
	INIT_LIST_HEAD(&new_proxy->runtime.ssl_certs);
	INIT_LIST_HEAD(&new_proxy->runtime.del_header_req);
	INIT_LIST_HEAD(&new_proxy->runtime.del_header_res);
	INIT_LIST_HEAD(&new_proxy->runtime.replace_header_req);
	INIT_LIST_HEAD(&new_proxy->runtime.replace_header_res);

	list_for_each_entry(cert_path, &proxy_cfg->ssl.cert_paths, list) {
		struct cert_path *cert_path_clone;

		cert_path_clone = (struct cert_path *)calloc(1, sizeof(*cert_path));
		if (!cert_path_clone)
			goto err_cert_path;

		*cert_path_clone = *cert_path;

		list_add_tail(&cert_path_clone->list, &new_proxy->ssl.cert_paths);
	}

	return new_proxy;

err_cert_path:
	zproxy_proxy_cfg_free(cfg, new_proxy);

	return NULL;
}

struct zproxy_cfg *zproxy_cfg_clone(const struct zproxy_cfg *cfg)
{
	struct zproxy_backend_cfg *backend, *new_backend;
	struct zproxy_service_cfg *service, *new_service;
	struct zproxy_proxy_cfg *proxy, *new_proxy;
	struct zproxy_cfg *new_cfg;

	new_cfg = (struct zproxy_cfg *)calloc(1, sizeof(*new_cfg));
	if (!new_cfg)
		return NULL;

	/* XXX: broken, clone pointers. */
	*new_cfg = *cfg;
	new_cfg->refcnt = 0;
	INIT_LIST_HEAD(&new_cfg->proxy_list);

	list_for_each_entry(proxy, &cfg->proxy_list, list) {
		new_proxy = zproxy_proxy_cfg_clone(proxy, new_cfg);
		if (!new_proxy)
			goto err;

		list_for_each_entry(service, &proxy->service_list, list) {
			new_service = zproxy_service_cfg_clone(service, new_proxy);
			if (!new_service)
				goto err;

			list_for_each_entry(backend, &service->backend_list, list) {
				new_backend = zproxy_backend_cfg_clone(backend,
								       new_service);
				if (!new_backend)
					goto err;

				list_add_tail(&new_backend->list, &new_service->backend_list);
			}

			list_add_tail(&new_service->list, &new_proxy->service_list);
		}

		list_add_tail(&new_proxy->list, &new_cfg->proxy_list);
	}

	zproxy_cfg_prepare(new_cfg);

	return new_cfg;
err:
	zproxy_cfg_free(new_cfg);

	return NULL;
}

void zproxy_cfg_free(const struct zproxy_cfg *cfg)
{
	struct zproxy_cfg *_cfg = (struct zproxy_cfg *)cfg;
	struct zproxy_proxy_cfg *proxy, *next;

	if (--_cfg->refcnt == 0) {
		list_for_each_entry_safe(proxy, next, &cfg->proxy_list, list)
			zproxy_proxy_cfg_free(_cfg, proxy);

		DH_free(cfg->runtime.ssl_dh_params);
		if (_cfg->runtime.waf_api != nullptr && _cfg->runtime.waf_refs == 0) {
			zcu_log_print(LOG_DEBUG, "Destroying WAF API");
			Waf::destroy_api(cfg->runtime.waf_api);
		}

		free(_cfg);
	}
}

int zproxy_cfg_prepare(struct zproxy_cfg *cfg)
{
	DH *dh;
	struct zproxy_proxy_cfg *tmp_proxy;

	if (cfg->ssl.dh_file[0]) {
		dh = load_dh_params(cfg->ssl.dh_file);
		if (!dh) {
			syslog(LOG_ERR, "DHParams config: could not load file %s",
			       cfg->ssl.dh_file);
			return -1;
		}
		cfg->runtime.ssl_dh_params = dh;
	}

	if (cfg->ssl.ecdh_curve[0]) {
		if ((cfg->runtime.ssl_ecdh_curve_nid = OBJ_sn2nid(cfg->ssl.ecdh_curve)) == 0) {
			syslog(LOG_ERR, "ECDHCurve config: invalid curve name %s",
			       cfg->ssl.ecdh_curve);
			return -1;
		}
	}

	list_for_each_entry(tmp_proxy, &cfg->proxy_list, list) {
		if (zproxy_proxy_cfg_prepare(tmp_proxy) < 0) {
			return -1;
		}
	}

	return 0;
}

int zproxy_cfg_file(struct zproxy_cfg *cfg)
{
	regmatch_t matches[CONFIG_MAX_PARAMS] = {};
	int alive_defined = 0, connto_defined = 0;
	struct zproxy_proxy_cfg *proxy = NULL;
	char lin[ZCU_DEF_BUFFER_SIZE];
	FILE *fd;

	fd = fopen(cfg->args.conf_file_name, "r");
	if (!fd) {
		fprintf(stderr, "can't open open the file %s\n", cfg->args.conf_file_name);
		return -1;
	}
	n_lin = 0;

	INIT_LIST_HEAD(&cfg->proxy_list);

	while (zproxy_cfg_file_gets(cfg, lin, ZCU_DEF_BUFFER_SIZE, fd)) {
		if (strlen(lin) > 0 && lin[strlen(lin) - 1] == '\n')
			lin[strlen(lin) - 1] = '\0';
		if (zproxy_regex_exec(CONFIG_REGEX_User, lin, matches)) { // NOT USED
		} else if (zproxy_regex_exec(CONFIG_REGEX_Group, lin, matches)) { // NOT USED
		} else if (zproxy_regex_exec(CONFIG_REGEX_Name, lin, matches)) { // NOT USED
		} else if (zproxy_regex_exec(CONFIG_REGEX_HTTPTracerDir, lin, matches)) { // NOT USED
		} else if (zproxy_regex_exec(CONFIG_REGEX_RootJail, lin, matches)) { // NOT USED
		} else if (zproxy_regex_exec(CONFIG_REGEX_DHParams, lin, matches)) {
			lin[matches[1].rm_eo] = '\0';
			snprintf(cfg->ssl.dh_file, PATH_MAX, "%s", lin + matches[1].rm_so);
		} else if (zproxy_regex_exec(CONFIG_REGEX_Daemon, lin, matches)) {
			cfg->args.daemon = atoi(lin + matches[1].rm_so);
		} else if (zproxy_regex_exec(CONFIG_REGEX_Threads, lin, matches)) {
			cfg->num_threads = atoi(lin + matches[1].rm_so);
		} else if (zproxy_regex_exec(CONFIG_REGEX_ThreadModel, lin, matches)) { // NOT USED
		} else if (zproxy_regex_exec(CONFIG_REGEX_LogFacility, lin, matches)) { // NOT USED
		} else if (zproxy_regex_exec(CONFIG_REGEX_Grace, lin, matches)) { // NOT USED
		} else if (zproxy_regex_exec(CONFIG_REGEX_LogLevel, lin, matches)) {
			cfg->args.log_level = atoi(lin + matches[1].rm_so);
			zcu_log_set_level(cfg->args.log_level);
		} else if (zproxy_regex_exec(CONFIG_REGEX_Client, lin, matches)) {
			cfg->timer.client = atoi(lin + matches[1].rm_so);
		} else if (zproxy_regex_exec(CONFIG_REGEX_Alive, lin, matches)) {
			cfg->timer.maintenance = atoi(lin + matches[1].rm_so);
			alive_defined = 1;

			if (alive_defined && connto_defined &&
			    cfg->timer.connect >= cfg->timer.maintenance)
				parse_error("Alive must be greater than ConnTo");
		} else if (zproxy_regex_exec(CONFIG_REGEX_DynScale, lin, matches)) { // NOT USED
		} else if (zproxy_regex_exec(CONFIG_REGEX_TimeOut, lin, matches)) {
			cfg->timer.backend = atoi(lin + matches[1].rm_so);
		} else if (zproxy_regex_exec(CONFIG_REGEX_ConnTO, lin, matches)) {
			cfg->timer.connect = atoi(lin + matches[1].rm_so);
			connto_defined = 1;

			if (alive_defined && connto_defined &&
			    cfg->timer.connect >= cfg->timer.maintenance)
				parse_error("Alive must be greater than ConnTo");
		} else if (zproxy_regex_exec(CONFIG_REGEX_Ignore100continue, lin, matches)) { // NOT USED
		} else if (zproxy_regex_exec(CONFIG_REGEX_IgnoreCase, lin, matches)) { // NOT USED
		} else if (zproxy_regex_exec(CONFIG_REGEX_ECDHCurve, lin, matches)) {
			lin[matches[1].rm_eo] = '\0';
			snprintf(cfg->ssl.ecdh_curve, CONFIG_IDENT_MAX, "%s", lin + matches[1].rm_so);
		} else if (zproxy_regex_exec(CONFIG_REGEX_SSLEngine, lin, matches)) { // NOT USED
		} else if (zproxy_regex_exec(CONFIG_REGEX_Control, lin, matches)) { // NOT USED
		} else if (zproxy_regex_exec(CONFIG_REGEX_ControlIP, lin, matches)) { // NOT USED
		} else if (zproxy_regex_exec(CONFIG_REGEX_ControlPort, lin, matches)) { // NOT USED
		} else if (zproxy_regex_exec(CONFIG_REGEX_ControlUser, lin, matches)) { // NOT USED
		} else if (zproxy_regex_exec(CONFIG_REGEX_ControlGroup, lin, matches)) { // NOT USED
		} else if (zproxy_regex_exec(CONFIG_REGEX_ControlMode, lin, matches)) { // NOT USED
		} else if (zproxy_regex_exec(CONFIG_REGEX_ListenHTTP, lin, matches)) {
			if (zproxy_proxy_cfg_file(cfg, proxy, false, fd) == -1)
				return -1;
		} else if (zproxy_regex_exec(CONFIG_REGEX_ListenHTTPS, lin, matches)) {
			if (zproxy_proxy_cfg_file(cfg, proxy, true, fd) == -1)
				return -1;
		} else if (zproxy_regex_exec(CONFIG_REGEX_ServiceName, lin, matches)) {
			lin[matches[1].rm_eo] = '\0';
			if (zproxy_service_cfg_file(cfg, proxy, lin + matches[1].rm_so, fd) == -1)
				return -1;
		} else if (zproxy_regex_exec(CONFIG_REGEX_Anonymise, lin, matches)) { // NOT USED
		} else
			parse_error("unknown directive in file context");
	}

	if (zproxy_cfg_prepare(cfg) < 0)
		goto err;

	fclose(fd);

	return 0;
err:
	fclose(fd);
	return -1;
}
