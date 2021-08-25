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

#pragma once

#include <dirent.h>
#include <fcntl.h>
#include <fnmatch.h>
#include <getopt.h>
#include <malloc.h>
#include <netdb.h>
#include <openssl/engine.h>
#include <openssl/lhash.h>
#include <openssl/ssl.h>
#include <openssl/x509v3.h>
#include <sys/stat.h>
#include <sys/un.h>
#include <unistd.h>
#include <cstdio>
#include <cstring>
#include <mutex>
#include <string>
#include <fstream>
#include "macro.h"
#include "../stats/counter.h"
#include "../version.h"
#include "config_data.h"
#include "global.h"

#ifndef F_CONF
constexpr auto F_CONF = "/usr/local/etc/zproxy.cfg";
#endif
#ifndef F_PID
constexpr auto F_PID = "/var/run/zproxy.pid";
#endif
constexpr int MAX_FIN = 100;
constexpr int UNIX_PATH_MAX = 108;

void __SSL_CTX_free(SSL_CTX *ssl_ctx);
class Config : public Counter<Config> {
	const char *xhttp[6] = {
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

	int clnt_to;
	int be_to;
	int be_connto;
	bool dynscale;
	int ignore_case;
	std::array<std::string, MAX_FIN> f_name;
	FILE *f_in[MAX_FIN];
	int n_lin[MAX_FIN];
	size_t cur_fin;
	DH *DHCustom_params;
	int EC_nid;
	int listener_id_counter;
	bool abort_on_error;

    public:
	int log_level;
	int def_facility;
	/*
	 * Global variables needed by everybody
	 */

	std::string user, /* user to run as */
		group, /* group to run as */
		name, /* farm name to run as */
		root_jail, /* directory to chroot to */
		pid_name, /* file to record pid in */
		ctrl_name, /* control socket name */
		ctrl_ip, /* control socket ip */
		ctrl_user, /* control socket username */
		ctrl_group, /* control socket group name */
		engine_id, /* openssl engine id */
		conf_file_name; /* Configuration file path name */

	long ctrl_mode; /* octal mode of the control socket */

	int numthreads, /* number of worker threads */
		anonymise, /* anonymise client address */
		alive_to, /* check interval for resurrection */
		daemonize, /* run as daemon */
		log_facility, /* log facility to use */
		print_log, /* print log messages to stdout/stderr */
		grace, /* grace period before shutdown */
		ignore_100, /* ignore header "Expect: 100-continue" */
		/* 1 Ignore header (Default) */
		/* 0 Manages header */
		ctrl_port = 0, sync_is_enabled; /*session sync enabled */
#ifdef CACHE_ENABLED
	long cache_s;
	int cache_thr;
	std::string cache_ram_path;
	std::string cache_disk_path;
#endif

    public:
	void conf_err(const char *msg);
	char *conf_fgets(char *buf, const int max);
	void include_dir(const char *conf_path);

	/*
	 * return the file contents as a string
	 */
	std::string file2str(const char *fname);

	/*
	 * it parses the replace_header directive
	 */
	void parseReplaceHeader(char *lin, regmatch_t *matches,
				ReplaceHeader **replace_header_request,
				ReplaceHeader **replace_header_response);

	/*
	 * parse the AddRequestHeader and AddResponseHeader directives
	 */
	void parseAddHeader(std::string *add_head, char *lin,
			    regmatch_t *matches);

	/*
	 * parse the RemoveRequestHeader and RemoveResponseHeader directives
	 */
	void parseRemoveHeader(MATCHER **head_off, char *lin,
			       regmatch_t *matches);

	/*
	 * parse an HTTP listener
	 */
	std::shared_ptr<ListenerConfig> parse_HTTP();

	/*
	 * parse an HTTPS listener
	 */
	std::shared_ptr<ListenerConfig> parse_HTTPS();

	regex_t **get_subjectaltnames(X509 *x509, unsigned int *count);

	void load_cert(int has_other, std::weak_ptr<ListenerConfig> listener_,
		       char *filename);

	void load_certdir(int has_other,
			  std::weak_ptr<ListenerConfig> listener_,
			  const std::string &dir_path);

	/*
	 * parse a service
	 */
	std::shared_ptr<ServiceConfig> parseService(const char *svc_name);

	/*
	 * parse an OrURLs block
	 *
	 * Forms a composite pattern of all URLs within
	 * of the form ((url1)|(url2)|(url3)) (and so on)
	 */
	char *parse_orurls();

	/*
	 * parse a back-end
	 */
	std::shared_ptr<BackendConfig> parseBackend(const char *svc_name,
						    const int is_emergency);
	/*
	 * Parse the cache configuration
	 */
#ifdef CACHE_ENABLED
	void parseCache(ServiceConfig *const svc);
#endif
	/*
	 * parse a session
	 */
	void parseSession(std::weak_ptr<ServiceConfig> svc_spt);
	/*
	 * parse the config file
	 */
	void parse_file();

    public:
	std::shared_ptr<ServiceConfig> services;
	/* global services (if any) */ // Not used
	std::shared_ptr<ListenerConfig> listeners; /* all available listeners */

    public:
	Config(bool _abort_on_error = false);
	~Config();

	/*
	 * prepare to parse the config file provided.
	 */
	bool init(const global::StartOptions &start_options);
	bool init(const std::string &file_name);
	bool found_parse_error{ false };
	void setAsCurrent();
};
