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
#pragma once

#include <netdb.h>
#include <openssl/ssl.h>
#include <pcreposix.h>
#include <sys/socket.h>
#include <memory>
#include <string>
#include "../stats/counter.h"
#include "../stats/backend_stats.h"

#if WAF_ENABLED
#include <modsecurity/modsecurity.h>
#endif

enum class RENEG_STATE {
	RENEG_INIT = 0,
	RENEG_REJECT,
	RENEG_ALLOW,
	RENEG_ABORT
};

/* matcher chain */
struct MATCHER {
	regex_t pat; /* pattern to match the request/header against */
	MATCHER *next{ nullptr };
	~MATCHER()
	{
		if (next != nullptr)
			delete next;
		::regfree(&pat);
	}
};

struct ReplaceHeader {
	regex_t name, /* header name to replace */
		match; /* header value match, if don't */
	std::string replace; /* replace formated pattern from patch */
	int last{ 0 }; /* flag to disrupt the replace checks if this matches*/
	ReplaceHeader *next{ nullptr };
	~ReplaceHeader()
	{
		::regfree(&name);
		::regfree(&match);
		delete next;
	}
};
/* back-end types */
enum class SESS_TYPE {
	SESS_NONE,
	SESS_IP,
	SESS_COOKIE,
	SESS_URL,
	SESS_PARM,
	SESS_HEADER,
	SESS_BASIC
};

/* back-end definition */
class BackendConfig : Counter<BackendConfig> {
    public:
	std::string f_name;
	std::string srv_name;
	std::string address; /* IPv4/6 address */
	int port{ 0 };
	int be_type; /* 0 if real back-end, otherwise code (301, 302/default, 307) */
	int weight; /* weight */
	int priority; /* priority */
	int rw_timeout; /* read/write time-out */
	int conn_to; /* connection time-out */
	std::string ha_address; /* HA address/port */
	int ha_port{ 0 };
	std::string url; /* for redirectors */
	int redir_req; /* 0 - redirect is absolute, 1 - the redirect should include
				   the request path, or 2 if it should use perl dynamic
				   replacement */
	bool redir_macro{
		false
	}; /* If it is 1 the redirect requires an expand of the vhost macro */
	std::string bekey; /* Backend Key for Cookie */
	std::shared_ptr<SSL_CTX> ctx = nullptr; /* CTX for SSL connections */
	std::string ssl_config_file; /* ssl config file path */
	std::string ssl_config_section; /* ssl config file path */
	pthread_mutex_t mut; /* mutex for this back-end */
	int n_requests; /* number of requests seen */
	double t_requests; /* time to answer these requests */
	double t_average; /* average time to answer requests */
	int alive; /* false if the back-end is dead */
	int resurrect; /* this back-end is to be resurrected */
	int disabled; /* true if the back-end is disabled */
	int connections;
	int connection_limit; /* It is the limit of established connection that can manage simultanoausly*/
	Statistics::HttpResponseHits response_stats;
	int ecdh_curve_nid{ 0 };
	std::shared_ptr<BackendConfig> next = nullptr;
	int key_id;
	int nf_mark;
	int max_request{ 0 }; /*Maximum request number allowed per connection */
	~BackendConfig()
	{
	}
};

/** The enum Service::LOAD_POLICY defines the different types of load
* balancing available. All the methods are weighted except the Round Robin
* one.
*/
enum class ROUTING_POLICY {
	/** Selects the next backend following the Round Robin algorithm. */
	ROUND_ROBIN,
	/** Selects the backend with less stablished connections. */
	W_LEAST_CONNECTIONS,
	/** Selects the backend with less response time. */
	RESPONSE_TIME,
	/** Selects the backend with less pending connections. */
	PENDING_CONNECTIONS,
};

class ServiceConfig : Counter<ServiceConfig> {
    public:
	int key_id;
	int listener_key_id;
	std::string name; /* symbolic name */
	std::string f_name; /* farm name */
	MATCHER *url, /* request matcher */
		*req_head, /* required headers */
		*deny_head; /* forbidden headers */
	std::string add_head_req; /* extra request headers */
	std::string add_head_resp; /* extra response headers */
	MATCHER *head_off_req{
		nullptr
	}; /* headers to remove from the client request*/
	MATCHER *head_off_resp{
		nullptr
	}; /* headers to remove  from backned response */
	ReplaceHeader *replace_header_request{ nullptr };
	ReplaceHeader *replace_header_response{ nullptr };
	std::shared_ptr<BackendConfig> backends;
	std::shared_ptr<BackendConfig> emergency;
	int abs_pri; /* abs total priority for all back-ends */
	int tot_pri; /* total priority for current back-ends */
	pthread_mutex_t mut; /* mutex for this service */
	SESS_TYPE sess_type;
	int sess_ttl; /* session time-to-live */
	std::string sess_id; /* id used to track the session */
	regex_t sess_start; /* pattern to identify the session data */
	regex_t sess_pat; /* pattern to match the session data */
	ReplaceHeader *rewr_url{ nullptr }; /* List of regexp to apply */
#ifdef CACHE_ENABLED
	int cache_timeout = -1; /* cached content timeout in seconds */
	std::string cache_disk_path, cache_ram_path;
	regex_t cache_content; /* pattern to decide if must be cached or not */
	long cache_size;
	size_t cache_max_size;
	int cache_threshold;
#endif
	regex_t becookie_re; /* Regexs to find backend cookies */
	char *becookie, /* Backend Cookie Name */
		*becdomain, /* Backend Cookie domain */
		*becpath; /* Backend cookie path */
	int becage; /* Backend cookie age */
	int rewr_loc_path{
		-1
	}; /* overwrite the RewriteLocation (Path) parameter in the service, -1 is that was not defind in the service */
	int rewr_loc{
		-1
	}; /* overwrite the RewriteLocation parameter in the service, -1 is that was not defind in the service */
	bool dynscale; /* true if the back-ends should be dynamically rescaled */
	bool disabled; /* true if the service is disabled */
	int sts; /* strict transport security */
	int max_headers_allowed;
	ROUTING_POLICY
		routing_policy; /* load policy (from 0 to 3) defined in the LOAD_POLICY enum */
	int pinned_connection; /* Pin the connection by default */
	std::string compression_algorithm; /* Compression algorithm */
	std::shared_ptr<ServiceConfig> next;

	~ServiceConfig()
	{
		delete becookie;
		delete becdomain;
		delete becpath;
		delete url;
		delete req_head;
		delete deny_head;
		delete replace_header_request;
		delete replace_header_response;
		::regfree(&sess_start);
		::regfree(&sess_pat);
	}
};

struct SNI_CERTS_CTX {
	std::shared_ptr<SSL_CTX> ctx;
	regex_t server_name{ nullptr };
	regex_t **subjectAltNames{ nullptr };
	unsigned int subjectAltNameCount{ 0 };
	std::shared_ptr<SNI_CERTS_CTX> next;
	~SNI_CERTS_CTX()
	{
		::regfree(&server_name);
		if (subjectAltNames != nullptr) {
			for (unsigned int i = 0; i < subjectAltNameCount; i++) {
				::regfree(*(subjectAltNames + i));
				free(*(subjectAltNames + i));
			}
			free(subjectAltNames);
		}
	}
};

/* Listener definition */
struct ListenerConfig : Counter<ListenerConfig> {
	std::string name;
	int id{ 0 };
	std::string address;
	addrinfo *addr_info; /* IPv4/6 address */
	int port;
	std::shared_ptr<SNI_CERTS_CTX> ctx{
		nullptr
	}; /* CTX for SSL connections */
	int clnt_check; /* client verification mode */
	int noHTTPS11; /* HTTP 1.1 mode for SSL */
	MATCHER *forcehttp10{
		nullptr
	}; /* User Agent Patterns to force HTTP 1.0 mode */
	MATCHER *ssl_uncln_shutdn; /* User Agent Patterns to enable ssl unclean shutdown */
	regex_t verb; /* pattern to match the request verb against */
	int to; /* client time-out */
	int has_pat; /* was a URL pattern defined? */
	regex_t url_pat; /* pattern to match the request URL against */
	std::string err414, /* error messages */
		err500, err501, err503, errnossl, errreq;
	http::Code codenossl;
#if WAF_ENABLED
	std::string errwaf;
#endif
	std::string nossl_url; /* If a user goes to a https port with a http: url,
				   redirect them to this url */
	int nossl_redir; /* Code to use for redirect (301 302 307) */
	long max_req; /* max. request size */
	std::string add_head_req; /* extra request headers */
	std::string add_head_resp; /* extra response headers */
	MATCHER *head_off_req{
		nullptr
	}; /* headers to remove from the client request*/
	MATCHER *head_off_resp{
		nullptr
	}; /* headers to remove  from backned response */
	std::string ssl_config_file; /* OpenSSL config file path */
	int rewr_loc_path{
		0
	}; /* rewrite the path in the location response header */
	int rewr_loc{ 0 }; /* rewrite location response */
	int rewr_dest{ 0 }; /* rewrite destination header */
	int rewr_host{ 0 }; /* rewrite host header */
	std::string ssl_config_section; /* OpenSSL config section */
	int disabled{ 0 }; /* true if the listener is disabled */
	int log_level; /* log level for this listener */
	int allow_client_reneg; /* Allow Client SSL Renegotiation */
	int disable_ssl_v2; /* Disable SSL version 2 */
	int alive_to;
	int ignore100continue; /* Ignore Expect: 100-continue headers in requests. */
	std::string engine_id; /* Engine id loaded by openssl */
	bool ssl_forward_sni_server_name{
		false
	}; /* enable SNI hostname forwarding to
				   https backends, param ForwardSNI */
	Statistics::HttpResponseHits response_stats;
#if WAF_ENABLED
	std::shared_ptr<modsecurity::Rules> rules{
		nullptr
	}; /* Rules of modsecurity */
#endif
	int ecdh_curve_nid{ 0 };
	ReplaceHeader *replace_header_request{ nullptr };
	ReplaceHeader *replace_header_response{ nullptr };
	std::shared_ptr<ServiceConfig> services{ nullptr };
	std::shared_ptr<ListenerConfig> next{ nullptr };
	~ListenerConfig()
	{
		delete replace_header_request;
		delete replace_header_response;
		delete forcehttp10;
		delete ssl_uncln_shutdn;
		::regfree(&verb);
		::regfree(&url_pat);
		delete head_off_req;
		delete head_off_resp;
		::freeaddrinfo(addr_info);
	}
};
