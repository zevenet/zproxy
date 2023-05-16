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

#ifndef _ZPROXY_CONFIG_H
#define _ZPROXY_CONFIG_H

#include "list.h"
#include "http_protocol.h"
#include "zcu_http.h"
#include <stdbool.h>
#include <pcreposix.h>
#include <string>
#include <memory>
#include <openssl/ssl.h>
#include <arpa/inet.h>

#define DEFAULT_LOG_LEVEL		5
#define DEFAULT_LOG_OUTPUT		0
#define DEFAULT_DAEMON			true
#define DEFAULT_CTRLSOCKET		"/tmp/zproxy.socket"
#define DEFAULT_CHECKONLY		false

#define CONFIG_MAX_FIN			100
#define CONFIG_UNIX_PATH_MAX		108
#define CONFIG_IDENT_MAX		255
#define CONFIG_MAXBUF			4096
#define CONFIG_MAX_PARAMS		5

#define CONFIG_REGEX_CNName		".*[Cc][Nn]=([-*.A-Za-z0-9]+).*$"

#define CONFIG_DEFAULT_ErrNoSsl         "Please use HTTPS."
#define CONFIG_DEFAULT_ErrNoSsl_Code    WS_HTTP_400

/* pattern to match the request/header against */
struct matcher {
	struct list_head		list;
	char				pat_str[CONFIG_IDENT_MAX];
	regex_t 			pat;
};

/**
 * Replace header field
 *
 * @param name		header field name
 * @param match		header field value to match, if don't
 * @param replace	replace formated pattern from patch
 */
struct replace_header {
	struct list_head		list;
	char				name_str[CONFIG_IDENT_MAX];
	char				match_str[CONFIG_IDENT_MAX];
	regex_t				name;
	regex_t				match;
	char				replace[CONFIG_IDENT_MAX];
};

struct path_item {
	struct list_head        list;
	char                    path[PATH_MAX];
};

struct err_resp_item {
	struct list_head    list;
	int                 code;  ///< If 0 it is the default response
	char                path[PATH_MAX];
	char                data[CONFIG_MAXBUF];
};

inline char *zproxy_cfg_get_errmsg(struct list_head *list, int code) {
	char *ret = NULL;
	struct err_resp_item *err_item;

	list_for_each_entry(err_item, list, list) {
		if (err_item->code == code) {
			ret = err_item->data;
			return ret;
		} else if (err_item->code == 0 && !ret) {
			ret = err_item->data;
		}
	}
	return ret;
}

enum class SESS_TYPE {
	SESS_NONE,
	SESS_IP,
	SESS_COOKIE,
	SESS_COOKIE_INSERT,
	SESS_URL,
	SESS_PARM,
	SESS_HEADER,
	SESS_BASIC
};

/* The enum Service::LOAD_POLICY defines the different types of load
 * balancing available. All the methods are weighted except the Round Robin
 * one.
 */
enum class ROUTING_POLICY {
	/* Selects the next backend following the Round Robin algorithm (default). */
	ROUND_ROBIN,
	/* Selects the backend with less stablished connections. */
	W_LEAST_CONNECTIONS,
	/* Selects the backend with less response time. */
	RESPONSE_TIME,
};

/** The enum Backend::BACKEND_STATUS defines the status of the Backend. */
enum class BACKEND_STATUS {
	/** There is no Backend, used for first assigned backends. */
	NO_BACKEND = -1,
	/** The Backend is up. */
	UP = 0,
	/** The Backend is down. */
	DOWN,
	/** The Backend is disabled. */
	DISABLED
};

struct sni_cert_ctx {
	struct list_head		list;
	SSL_CTX				*ctx;
	regex_t				server_name;
	regex_t				**subjectAltNames;
	unsigned int			subjectAltNameCount;
};

/**
 * Backend configuration.
 *
 * @param list		node in service list
 * @param service	pointer to service that owns this backend
 * @param id		ID used for backend identification
 * @param addr		backend IP address
 * @param port		backend port
 * @param address	IP address in string format (for logging)
 * @param priority	priority
 * @param weight	weight
 * @param type		0 if real back-end, otherwise code (301, 302/default, 307)
 * @param connection_limit It is the limit of simultaneous established connection
 * @param nf_mark	Mark to track backend connections
 * @param timer.backend read/write backend time-out
 * @param timer.connect	timeout to connect to backend
 * @param cookie_key	Backend Key for Cookie
 * @param cookie_set_header set-cookie header to set this backend for persistence
 * @param ssl_enabled	ssl is enabled
 * @param SSL_CTX	pointer to ssl context object (certificates)
 */
struct zproxy_backend_cfg {
	struct list_head		list;
	struct zproxy_service_cfg	*service;
	int				port;
	char				address[CONFIG_MAX_FIN];
	int				priority;
	int				weight;
	int				type;
	int				connection_limit;
	uint32_t			nf_mark;

	struct {
		int			backend;
		int			connect;
	} timer;

	char				cookie_set_header[CONFIG_MAXBUF];

	struct {
		char			id[CONFIG_IDENT_MAX];
		struct sockaddr_in	addr;
		char			cookie_key[CONFIG_IDENT_MAX];
		bool			ssl_enabled;
		SSL_CTX			*ssl_ctx;
	} runtime;

};

struct zproxy_backend_redirect {
	bool enabled;
	char url[CONFIG_MAXBUF];
	bool redir_macro;
	int be_type;
	int redir_type = 0; // 0: static; 1: dynamic; 2: append
};

/**
 * Service configuration.
 *
 * @param list				node in listener list
 * @param proxy				pointer to listener that owns this service
 * @param backend_list			list of backends that are owned by this service
 * @param name				service name
 * @param backend_list_size		number of backends in the list (?)
 * @param ignore_case			ignore casing (?)
 * @param header.rw_url_rev		overwrite the RewriteLocation (Path) parameter in the service, -1 means undefined
 * @param header.rw_location		overwrite the RewriteLocation parameter in the service, -1 means undefined
 * @param header.sts			string transport security (?)
 * @param algorithm.routing_policy	load policy (from 0 to 3) defined in the LOAD_POLICY enum
 * @param session.sess_type		session type
 * @param session.sess_ttl		session time-to-live. Age cookie for backend_cookie sessions
 * @param session.sess_id		id used to track the session
 * @param session.sess_domain		Backend Cookie domain. Only for backend_cookie sessions
 * @param session.sess_path		Backend cookie path. Only for backend_cookie sessions
 * @param zproxy_backend_redirect	?
 * @param runtime.del_header_req	headers to remove from the client request
 * @param runtime.del_header_res	headers to remove from backend response
 * @param runtime.req_head		required headers
 * @param runtime.deny_head		forbidden headers
 * @param runtime.add_header_req	extra request headers
 * @param runtime.add_header_res	extra response headers
 * @param runtime.replace_header_req	Regular expression to replace request header
 * @param runtime.replace_header_res	Regular expression to replace response header
 * @param runtime.req_rw_url		List of regexp to apply
 * @param runtime.req_url		request matcher
 */
struct zproxy_service_cfg {
	struct list_head		list;

	struct zproxy_proxy_cfg		*proxy;
	char				name[CONFIG_IDENT_MAX];
	struct list_head		backend_list;
	int				backend_list_size;
	int				ignore_case;
		ROUTING_POLICY		routing_policy;

	struct {
		int			rw_url_rev;
		int			rw_location;
		char			add_header_req[CONFIG_MAXBUF];
		char			add_header_res[CONFIG_MAXBUF];
		int			sts;
	} header;

	struct {
		SESS_TYPE		sess_type;
		int			sess_ttl;
		char                    sess_id[CONFIG_IDENT_MAX];
		char                    sess_domain[CONFIG_IDENT_MAX];
		char                    sess_path[CONFIG_IDENT_MAX];
	} session;

	struct {
		struct list_head	del_header_req,
					del_header_res,
					req_head,
					deny_head;
		struct list_head	replace_header_req;
		struct list_head	replace_header_res;
		struct list_head	req_rw_url;
		struct list_head	req_url;
	} runtime;

	struct zproxy_backend_redirect 	redirect;
};

struct cert_path {
	struct list_head      list;
	char                  path[PATH_MAX];
};

/**
 * Listener configuration.
 *
 * @param list				node in configuration object list
 * @param zproxy_cfg			pointer to configuration object that owns this listener
 * @param service_list			list services that are contained by this listener
 * @param name				name of this listener
 * @param id				ID for this listener (?)
 * @param address			IP address in string format (for logging)
 * @param port				port
 * @param log_level			log_level (?)
 * @param ignore_case			?
 * @param timer.client			?
 * @param timer.maintainance		?
 * @param ssl_enabled			ssl is enabled
 * @param ssl.cert_path			path to certificate file
 * @param ssl.allow_client_reneg	Allow Client SSL Renegotiation (?)
 * @param ssl.ssl_op_enable		?
 * @param ssl.ssl_op_disable		?
 * @param ssl.openssl engine id		openssl engine id
 * @param ssl.ciphers			ciphers
 * @param max_req			max. request size
 * @param header.rw_url_rev		overwrite the RewriteLocation (Path) parameter in the service, -1 means undefined
 * @param header.rw_location		rewrite location response
 * @param header.rw_destination		rewrite destination header
 * @param header.rw_host		rewrite host header
 * @param error.parse_req_msg		?
 * @param error.err414			?
 * @param error.err500			?
 * @param error.err501			?
 * @param error.err503			?
 * @param error.errnossl		?
 * @param error.nossl_url		?
 * @param error.errwaf			?
 * @param runtime.waf_rules		?
 * @param runtime.ssl_dh_params		?
 * @param runtime.ssl_ecdh_curve_nid	?
 * @param runtime.req_verb_reg		pattern to match the request verb against
 * @param runtime.req_url_pat_reg	pattern to match the request URL against
 * @param runtime.addr			IP address
 * @param runtime.ssl_certs		CTX for SSL connections (?)
 * @param runtime.ssl_certs_cnt		?
 * @param runtime.del_header_req	headers to remove from the client request
 * @param runtime.del_header_res	headers to remove  from backend response
 * @param runtime.add_header_req	extra request headers
 * @param runtime.add_header_res	extra response headers
 * @param runtime.replace_header_req	Reg exp to replace request headers
 * @param runtime.replace_header_res	Reg exp to replace response headers
 */
struct zproxy_proxy_cfg {
	struct list_head		list;
	const struct zproxy_cfg		*cfg;
	struct list_head		service_list;

	char				name[CONFIG_IDENT_MAX];
	uint32_t			id;
	char				address[CONFIG_MAX_FIN];
	int				port;
	int				log_level;
	int				ignore_case;

	struct {
		char			url_pat_str[CONFIG_IDENT_MAX];
		int			verb;
	} request;

	struct {
		int			client;
		int			maintenance;
	} timer;

	struct {
		struct list_head        cert_paths;
		int			allow_client_reneg;
		unsigned long		ssl_op_enable, ssl_op_disable;
		char			ciphers[CONFIG_IDENT_MAX];
	} ssl;

	long				max_req;
	struct {
		int			rw_location;
		int			rw_url_rev;
		int			rw_destination;
		int			rw_host;
		char			add_header_req[CONFIG_MAXBUF];
		char			add_header_res[CONFIG_MAXBUF];
	} header;

	struct {
		char			parse_req_msg[CONFIG_MAXBUF];
		char			err414_path[PATH_MAX];
		char			err500_path[PATH_MAX];
		char			err501_path[PATH_MAX];
		char			err503_path[PATH_MAX];
		char			errnossl_path[PATH_MAX];
		struct list_head        errwaf_msgs;
		char			nosslredirect_url[PATH_MAX];
		enum ws_responses       nosslredirect_code;
		enum ws_responses       errnossl_code;
	} error;

	struct list_head                waf_rule_paths;

	struct {
		char			err414_msg[CONFIG_MAXBUF];
		char			err500_msg[CONFIG_MAXBUF];
		char			err501_msg[CONFIG_MAXBUF];
		char			err503_msg[CONFIG_MAXBUF];
		char			errnossl_msg[CONFIG_MAXBUF];
		void                    *waf_rules;
		regex_t			req_url_pat_reg;
		regex_t			req_verb_reg;
		struct sockaddr_in	addr;
		int			ssl_enabled;
		struct list_head	ssl_certs;
		int			ssl_certs_cnt;
		struct list_head	del_header_req;
		struct list_head	del_header_res;
		struct list_head	replace_header_req;
		struct list_head	replace_header_res;
	} runtime;
};

struct zproxy_args {
        bool            daemon;
        const char      *conf_file_name;
        const char      *pid_file_name;
        int             log_level;
        int             log_output;
        char		ctrl_socket[CONFIG_IDENT_MAX];
};

struct zproxy_cfg {
	struct list_head		proxy_list;
	uint32_t			refcnt;
	struct zproxy_args		args;
	int				num_threads;

	struct {
		int			maintenance;
		int			client;
		int			backend;
		int			connect;
	} timer;

	struct {
		char			dh_file[PATH_MAX];
		char			ecdh_curve[CONFIG_IDENT_MAX];
	} ssl;

	struct {
		DH			*ssl_dh_params;
		int			ssl_ecdh_curve_nid;
		void			*waf_api; ///< API connector with Modsecurity
		int			waf_refs; ///< API reference counter
	} runtime;
};

void zproxy_cfg_init(struct zproxy_cfg *cfg);
void zproxy_cfg_destroy(struct zproxy_cfg *cfg);
int zproxy_cfg_file(struct zproxy_cfg *cfg);
int zproxy_cfg_prepare(struct zproxy_cfg *cfg);
struct zproxy_cfg *zproxy_cfg_clone(const struct zproxy_cfg *cfg);
const struct zproxy_cfg *zproxy_cfg_get(const struct zproxy_cfg *cfg);
void zproxy_cfg_free(const struct zproxy_cfg *cfg);

void zproxy_set_backend_cookie_insertion(struct zproxy_service_cfg *service,
			    struct zproxy_backend_cfg *backend,
			    char *set_cookie_header);
struct zproxy_backend_cfg *zproxy_backend_cfg_alloc(void);
void zproxy_backend_cfg_init(const struct zproxy_cfg *cfg,
			     struct zproxy_service_cfg *service,
			     struct zproxy_backend_cfg *backend);
int zproxy_backend_ctx_start(struct zproxy_backend_cfg *bck);

struct zproxy_backend_cfg *
zproxy_backend_cfg_lookup(const struct zproxy_service_cfg *service,
			  const struct sockaddr_in *addr);

int zproxy_regex_exec(const char *expr, const char *buf,
		      regmatch_t *matches);

#endif
