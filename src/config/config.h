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
#include "../debug/debug.h"
#include "config_data.h"

#ifndef F_CONF
constexpr auto F_CONF = "/usr/local/etc/zproxy.cfg";
#endif
#ifndef F_PID
constexpr auto F_PID = "/var/run/zproxy.pid";
#endif
constexpr int MAX_FIN = 100;
constexpr int UNIX_PATH_MAX = 108;
/*
 * RSA ephemeral keys: how many and how often
 */
constexpr int N_RSA_KEYS = 11;
#ifndef T_RSA_KEYS /* Timeout for RSA ephemeral keys generation */
constexpr int T_RSA_KEYS = 7200;
#endif
static std::mutex RSA_mut;            /*Mutex for RSA keygen*/
static RSA *RSA512_keys[N_RSA_KEYS];  /* ephemeral RSA keys */
static RSA *RSA1024_keys[N_RSA_KEYS]; /* ephemeral RSA keys */

#if OPENSSL_VERSION_NUMBER >= 0x10100000L
#define general_name_string(n)                                                                                   \
  reinterpret_cast<unsigned char *>(strndup(reinterpret_cast<const char *>(ASN1_STRING_get0_data(n->d.dNSName)), \
                                            ASN1_STRING_length(n->d.dNSName) + 1))
#else
#define general_name_string(n) \
  (unsigned char *)strndup((char *)ASN1_STRING_data(n->d.dNSName), ASN1_STRING_length(n->d.dNSName) + 1)
#endif

class Config {
  const char *xhttp[5] = {
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
      "BPROPFIND|NOTIFY|CONNECT|RPC_IN_DATA|RPC_OUT_DATA) ([^ ]+) HTTP/1.[01].*$",
  };

  int log_level;
  int def_facility;
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

 public:
  /*
   * Global variables needed by everybody
   */

  std::string user, /* user to run as */
      group,        /* group to run as */
      name,         /* farm name to run as */
      root_jail,    /* directory to chroot to */
      pid_name,     /* file to record pid in */
      ctrl_name,    /* control socket name */
      ctrl_ip,      /* control socket ip */
      ctrl_user,    /* control socket username */
      ctrl_group,   /* control socket group name */
      engine_id;    /* openssl engine id*/

  long ctrl_mode; /* octal mode of the control socket */

  static int numthreads;              /* number of worker threads */
  int anonymise,                      /* anonymise client address */
      alive_to,                       /* check interval for resurrection */
      daemonize,                      /* run as daemon */
      log_facility,                   /* log facility to use */
      print_log,                      /* print log messages to stdout/stderr */
      grace,                          /* grace period before shutdown */
      ignore_100,                     /* ignore header "Expect: 100-continue"*/
                                      /* 1 Ignore header (Default)*/
                                      /* 0 Manages header */
      ctrl_port = 0, sync_is_enabled; /*session sync enabled*/
#ifdef CACHE_ENABLED
  long cache_s;
  int cache_thr;
  std::string cache_ram_path;
  std::string cache_disk_path;
#endif
  int conf_init(const std::string &name);

 private:
  regex_t Empty, Comment, User, Group, Name, RootJail, Daemon, LogFacility, LogLevel, Alive, SSLEngine, Control,
      ControlIP, ControlPort;
  regex_t ListenHTTP, ListenHTTPS, End, Address, Port, Cert, CertDir, xHTTP, Client, CheckURL;
  regex_t Err414, Err500, Err501, Err503, SSLConfigFile, SSLConfigSection, ErrNoSsl, NoSslRedirect, MaxRequest,
      HeadRemove, RewriteLocation, RewriteDestination, RewriteHost;
  regex_t Service, ServiceName, URL, OrURLs, HeadRequire, HeadDeny, BackEnd, Emergency, Priority, HAport, HAportAddr,
      StrictTransportSecurity;
  regex_t Redirect, TimeOut, Session, Type, TTL, ID, DynScale, PinnedConnection, RoutingPolicy, NfMark,
      CompressionAlgorithm;
  regex_t ClientCert, AddHeader, DisableProto, SSLAllowClientRenegotiation, SSLHonorCipherOrder, Ciphers;
  regex_t CAlist, VerifyList, CRLlist, NoHTTPS11, Grace, Include, ConnTO, IgnoreCase, Ignore100continue, HTTPS;
  regex_t Disabled, Threads, CNName, Anonymise, DHParams, ECDHCurve;
  regex_t ControlGroup, ControlUser, ControlMode;
  regex_t ThreadModel;
  regex_t IncludeDir;
  regex_t ForceHTTP10, SSLUncleanShutdown;
  regex_t BackendKey, BackendCookie;
#ifdef CACHE_ENABLED
  regex_t Cache, CacheContent, CacheTO, CacheThreshold, CacheRamSize, MaxSize, CacheDiskPath,
      CacheRamPath; /* Cache configuration regex */
#endif
 public:
  static regex_t HEADER, /* Allowed header */
      CHUNK_HEAD,        /* chunk header line */
      RESP_SKIP,         /* responses for which we skip response */
      RESP_IGN,          /* responses for which we ignore content */
      LOCATION,          /* the host we are redirected to */
      AUTHORIZATION;     /* the Authorisation header */

  bool compile_regex();
  void clean_regex();

  void conf_err(const char *msg);
  char *conf_fgets(char *buf, const int max);
  void include_dir(const char *conf_path);

  /*
   * return the file contents as a string
   */
  std::string file2str(const char *fname);

  /*
   * parse an HTTP listener
   */
  ListenerConfig *parse_HTTP(void);

  /*
   * parse an HTTPS listener
   */
  ListenerConfig *parse_HTTPS(void);

  unsigned char **get_subjectaltnames(X509 *x509, unsigned int *count);

  void load_cert(int has_other, ListenerConfig *res, char *filename);

  void load_certdir(int has_other, ListenerConfig *res, const std::string &dir_path);

  /*
   * parse a service
   */
  ServiceConfig *parseService(const char *svc_name);
  /*
   * Dummy certificate verification - always OK
   */
  static int verify_OK(int pre_ok, X509_STORE_CTX *ctx);

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
  BackendConfig *parseBackend(const char *svc_name, const int is_emergency);
  /*
   * Parse the cache configuration
   */
#ifdef CACHE_ENABLED
  void parseCache(ServiceConfig *const svc);
#endif
  /*
   * parse a session
   */
  void parseSession(ServiceConfig *const svc);
  /*
   * parse the config file
   */
  void parse_file(void);

 public:
  ServiceConfig *services;   /* global services (if any) */
  ListenerConfig *listeners; /* all available listeners */

 public:
  Config();
  ~Config();

  /*
   * prepare to parse the arguments/config file
   */
  void parseConfig(const int argc, char **const argv);
  bool exportConfigToJsonFile(std::string save_path);

 private:
  /*
   * return a pre-generated RSA key
   */
  RSA *RSA_tmp_callback(/* not used */ SSL *ssl,
                        /* not used */ int is_export, int keylength);

#if OPENSSL_VERSION_NUMBER < 0x10100000
  static inline int DH_set0_pqg(DH *dh, BIGNUM *p, BIGNUM *q, BIGNUM *g);
#endif

  //#include "dh512.h"//TODO::

#if DH_LEN == 1024
#include "dh1024.h"
  static DH *DH512_params, *DH1024_params;

  DH *DH_tmp_callback(/* not used */ SSL *s, /* not used */ int is_export, int keylength) {
    return keylength == 512 ? DH512_params : DH1024_params;
  }
#else
  //#include "dh2048.h" //TODO
  static DH *DH512_params, *DH2048_params;

  static DH *DH_tmp_callback(/* not used */ SSL *s,
                      /* not used */ int is_export, int keylength);
#endif

  static DH *load_dh_params(char *file);

  /*
   * Search for a host name, return the addrinfo for it
   */
  int get_host(char *const name, struct addrinfo *res, int ai_family);

  static void SSLINFO_callback(const SSL *ssl, int where, int rc);
};
