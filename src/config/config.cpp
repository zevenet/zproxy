#include "config.h"
#define SYSLOG_NAMES
#include "../debug/Debug.h"
#undef SYSLOG_NAMES
#include "../version.h"

int Config::numthreads = 0;
Config::Config() {
  log_level = 1;
  def_facility = LOG_DAEMON;
  clnt_to = 10;
  be_to = 15;
  be_connto = 15;
  dynscale = 0;
  ignore_case = 0;
  EC_nid = NID_X9_62_prime256v1;
  ctrl_user = ctrl_group = nullptr;
  print_log = 0;
  ctrl_user = ctrl_group = NULL;
  ctrl_mode = -1;
  log_facility = -1;
}

Config::~Config() {}
regex_t Config::HEADER,    /* Allowed header */
    Config::CHUNK_HEAD,    /* chunk header line */
    Config::RESP_SKIP,     /* responses for which we skip response */
    Config::RESP_IGN,      /* responses for which we ignore content */
    Config::LOCATION,      /* the host we are redirected to */
    Config::AUTHORIZATION; /* the Authorisation header */
void Config::parse_file() {
  char lin[MAXBUF];
  ServiceConfig *svc;
  ListenerConfig *lstn;
  int i;
  regmatch_t matches[5];

  while (conf_fgets(lin, MAXBUF)) {
    if (strlen(lin) > 0 && lin[strlen(lin) - 1] == '\n')
      lin[strlen(lin) - 1] = '\0';
    if (!regexec(&User, lin, 4, matches, 0)) {
      lin[matches[1].rm_eo] = '\0';
      if ((user = strdup(lin + matches[1].rm_so)) == NULL)
        conf_err("User config: out of memory - aborted");
    } else if (!regexec(&Group, lin, 4, matches, 0)) {
      lin[matches[1].rm_eo] = '\0';
      if ((group = strdup(lin + matches[1].rm_so)) == NULL)
        conf_err("Group config: out of memory - aborted");
    } else if (!regexec(&Name, lin, 4, matches, 0)) {
      lin[matches[1].rm_eo] = '\0';
//      if ((name = strdup(lin + matches[1].rm_so)) == NULL)
//        conf_err("Farm name config: out of memory - aborted");
      name = std::string(lin + matches[1].rm_so, matches[1].rm_eo - matches[1].rm_so);
    } else if (!regexec(&RootJail, lin, 4, matches, 0)) {
      lin[matches[1].rm_eo] = '\0';
      if ((root_jail = strdup(lin + matches[1].rm_so)) == NULL)
        conf_err("RootJail config: out of memory - aborted");
    } else if (!regexec(&DHParams, lin, 4, matches, 0)) {
      lin[matches[1].rm_eo] = '\0';
      DH *dh = load_dh_params(lin + matches[1].rm_so);
      if (!dh) conf_err("DHParams config: could not load file");
      DHCustom_params = dh;
    } else if (!regexec(&Daemon, lin, 4, matches, 0)) {
      daemonize = atoi(lin + matches[1].rm_so);
    } else if (!regexec(&Threads, lin, 4, matches, 0)) {
      numthreads = atoi(lin + matches[1].rm_so);
    } else if (!regexec(&ThreadModel, lin, 4, matches, 0)) {
      threadpool = ((lin[matches[1].rm_so] | 0x20) == 'p'); /* 'pool' */
    } else if (!regexec(&LogFacility, lin, 4, matches, 0)) {
      lin[matches[1].rm_eo] = '\0';
      if (lin[matches[1].rm_so] == '-')
        def_facility = -1;
      else
        for (i = 0; facilitynames[i].c_name; i++)
          if (!strcmp(facilitynames[i].c_name, lin + matches[1].rm_so)) {
            def_facility = facilitynames[i].c_val;
            break;
          }
    } else if (!regexec(&Grace, lin, 4, matches, 0)) {
      grace = atoi(lin + matches[1].rm_so);
    } else if (!regexec(&LogLevel, lin, 4, matches, 0)) {
      log_level = atoi(lin + matches[1].rm_so);
    } else if (!regexec(&Client, lin, 4, matches, 0)) {
      clnt_to = atoi(lin + matches[1].rm_so);
    } else if (!regexec(&Alive, lin, 4, matches, 0)) {
      alive_to = atoi(lin + matches[1].rm_so);
    } else if (!regexec(&DynScale, lin, 4, matches, 0)) {
      dynscale = atoi(lin + matches[1].rm_so);
    } else if (!regexec(&TimeOut, lin, 4, matches, 0)) {
      be_to = atoi(lin + matches[1].rm_so);
    } else if (!regexec(&ConnTO, lin, 4, matches, 0)) {
      be_connto = atoi(lin + matches[1].rm_so);
    } else if (!regexec(&Ignore100continue, lin, 4, matches, 0)) {
      ignore_100 = atoi(lin + matches[1].rm_so);
    } else if (!regexec(&IgnoreCase, lin, 4, matches, 0)) {
      ignore_case = atoi(lin + matches[1].rm_so);
#if OPENSSL_VERSION_NUMBER >= 0x0090800fL
#ifndef OPENSSL_NO_ECDH
    } else if (!regexec(&ECDHCurve, lin, 4, matches, 0)) {
      lin[matches[1].rm_eo] = '\0';
      if ((EC_nid = OBJ_sn2nid(lin + matches[1].rm_so)) == 0)
        conf_err("ECDHCurve config: invalid curve name");
#endif
#endif
#if HAVE_OPENSSL_ENGINE_H
    } else if (!regexec(&SSLEngine, lin, 4, matches, 0)) {
      lin[matches[1].rm_eo] = '\0';
#if OPENSSL_VERSION_NUMBER >= 0x00907000L
      ENGINE_load_builtin_engines();
#endif
    if ((engine_id = strdup(lin + matches[1].rm_so)) == NULL) {
      Debug::logmsg(LOG_ERR,
                    "line %d: ControlUser config: out of memory - aborted",
                    n_lin);
      exit(1);
    }
#endif
    } else if (!regexec(&Control, lin, 4, matches, 0)) {
      if (ctrl_name != NULL) conf_err("Control multiply defined - aborted");
      lin[matches[1].rm_eo] = '\0';
      ctrl_name = strdup(lin + matches[1].rm_so);
    } else if (!regexec(&ControlIP, lin, 4, matches, 0)) {
        lin[matches[1].rm_eo] = '\0';
        ctrl_ip = strdup(lin + matches[1].rm_so);
    } else if (!regexec(&ControlPort, lin, 4, matches, 0)) {
        lin[matches[1].rm_eo] = '\0';
        ctrl_port = atoi(lin + matches[1].rm_so);
    } else if (!regexec(&ControlUser, lin, 4, matches, 0)) {
      lin[matches[1].rm_eo] = '\0';
      if ((ctrl_user = strdup(lin + matches[1].rm_so)) == NULL) {
        Debug::logmsg(LOG_ERR,
                      "line %d: ControlUser config: out of memory - aborted",
                      n_lin);
        exit(1);
      }
    } else if (!regexec(&ControlGroup, lin, 4, matches, 0)) {
      lin[matches[1].rm_eo] = '\0';
      if ((ctrl_group = strdup(lin + matches[1].rm_so)) == NULL) {
        Debug::logmsg(LOG_ERR,
                      "line %d: ControlGroup config: out of memory - aborted",
                      n_lin);
        exit(1);
      }
    } else if (!regexec(&ControlMode, lin, 4, matches, 0)) {
      lin[matches[1].rm_eo] = '\0';
      ctrl_mode = strtol(lin + matches[1].rm_so, NULL, 8);
      if (errno == ERANGE || errno == EINVAL) {
        Debug::logmsg(LOG_ERR, "line %d: ControlMode config: %s - aborted",
                      n_lin, strerror(errno));
        exit(1);
      }
    } else if (!regexec(&ListenHTTP, lin, 4, matches, 0)) {
      if (listeners == NULL)
        listeners = parse_HTTP();
      else {
        for (lstn = listeners; lstn->next; lstn = lstn->next);
        lstn->next = parse_HTTP();
      }
    } else if (!regexec(&ListenHTTPS, lin, 4, matches, 0)) {
      if (listeners == NULL)
        listeners = parse_HTTPS();
      else {
        for (lstn = listeners; lstn->next; lstn = lstn->next);
        lstn->next = parse_HTTPS();
      }
    } else if (!regexec(&Service, lin, 4, matches, 0)) {
      if (services == NULL)
        services = parseService(NULL);
      else {
        for (svc = services; svc->next; svc = svc->next);
        svc->next = parseService(NULL);
      }
    } else if (!regexec(&ServiceName, lin, 4, matches, 0)) {
      lin[matches[1].rm_eo] = '\0';
      if (services == NULL)
        services = parseService(lin + matches[1].rm_so);
      else {
        for (svc = services; svc->next; svc = svc->next);
        svc->next = parseService(lin + matches[1].rm_so);
      }
    } else if (!regexec(&Anonymise, lin, 4, matches, 0)) {
      anonymise = 1;
#if CACHE_ENABLED
    } else if (!regexec(&CacheThreshold, lin, 2, matches, 0)){
        int threshold = atoi(lin + matches[1].rm_so);
        if ( threshold <= 0 || threshold > 99 )
           conf_err("Invalid value for cache threshold (CacheThreshold), must be between 1 and 99 (%)");
        this->cache_thr = threshold;
    } else if (!regexec(&CacheRamSize, lin, 3, matches, 0)){
        long size = atol(lin + matches[1].rm_so);
        if (matches[2].rm_so != matches[0].rm_eo - 1){
            char * size_modifier = nullptr;
            size_modifier = strdup(lin + matches[2].rm_so);
            //Apply modifier
            if(*size_modifier == 'K' || *size_modifier == 'k' )
                size = size*1024;
            else if(*size_modifier == 'M' || *size_modifier == 'm' )
                size = size*1024*1024;
            else if(*size_modifier == 'G' || *size_modifier == 'g' )
                size = size*1024*1024*1024;
        }
        cache_s = size;
    } else if(!regexec(&CacheRamPath, lin, 2, matches, 0)){
        cache_ram_path = std::string(lin + matches[1].rm_so, matches[1].rm_eo - matches[1].rm_so);
    } else if(!regexec(&CacheDiskPath, lin, 2, matches, 0)){
        cache_disk_path = std::string(lin + matches[1].rm_so, matches[1].rm_eo - matches[1].rm_so);
#endif
    } else {
      conf_err("unknown directive - aborted");
    }
  }
  return;
}

void Config::parseConfig(const int argc, char **const argv) {
  char *conf_name;
  FILE *f_conf;
  int c_opt, check_only;

  if (!compile_regex()) {
    Debug::logmsg(LOG_ERR, "bad config Regex - aborted");
    exit(1);
  }

  opterr = 0;
  check_only = 0;
  conf_name = F_CONF;
  pid_name = F_PID;

  while ((c_opt = getopt(argc, argv, "sf:cvVp:")) > 0)
    switch (c_opt) {
      case 's':sync_is_enabled = 1;
        break;
      case 'f':conf_name = optarg;
        break;
      case 'p':pid_name = optarg;
        break;
      case 'c':check_only = 1;
        break;
      case 'v':print_log = 1;
        break;
      case 'V':print_log = 1;
      {
        Debug::logmsg(LOG_ALERT, "Zhttp version %s", ZHTTP_VERSION);
        Debug::logmsg(LOG_ALERT, "Build: %s %s", ZHTTP_HOST_INFO,ZHTTP_BUILD_INFO);
        Debug::logmsg(LOG_ALERT, "%s",ZHTTP_COPYRIGHT);
        exit(EXIT_SUCCESS);
      }

#ifdef C_SUPER
      if (strcmp(C_SUPER, "0"))
        Debug::logmsg(LOG_DEBUG, "    --disable-super");
#endif
#ifdef C_CERT1L
      if (strcmp(C_CERT1L, "1"))
        Debug::logmsg(LOG_DEBUG, "    --enable-cert1l");
#endif
#ifdef C_SSL
      if (strcmp(C_SSL, ""))
        Debug::logmsg(LOG_DEBUG, "    --with-ssl=%s", C_SSL);
#endif
#ifdef C_T_RSA
      if (strcmp(C_T_RSA, "0"))
        Debug::logmsg(LOG_DEBUG, "    --with-t_rsa=%s", C_T_RSA);
#endif
#ifdef C_MAXBUF
      if (strcmp(C_MAXBUF, "0"))
        Debug::logmsg(LOG_DEBUG, "    --with-maxbuf=%s", C_MAXBUF);
#endif
#ifdef C_OWNER
      if (strcmp(C_OWNER, ""))
        Debug::logmsg(LOG_DEBUG, "    --with-owner=%s", C_OWNER);
#endif
#ifdef C_GROUP
      if (strcmp(C_GROUP, ""))
        Debug::logmsg(LOG_DEBUG, "    --with-group=%s", C_GROUP);
#endif
#ifdef C_DH_LEN
      if (strcmp(C_DH_LEN, "0"))
        Debug::logmsg(LOG_DEBUG, "    --with-dh=%s", C_DH_LEN);
#endif
        Debug::logmsg(LOG_DEBUG, "Exiting...");
        exit(0);
        break;
      default:Debug::logmsg(LOG_ERR, "bad flag -%c", optopt);
        exit(1);
        break;
    }
  if (optind < argc) {
    Debug::logmsg(LOG_ERR, "unknown extra arguments (%s...)", argv[optind]);
    exit(1);
  }

  conf_init(conf_name);

  user = NULL;
  group = NULL;
//  name = NULL;
  root_jail = NULL;
  ctrl_name = NULL;
  DHCustom_params = NULL;

  numthreads = 0;
  threadpool = 1;
  alive_to = 30;
  daemonize = 1;
  grace = 30;
  ignore_100 = 1;
  services = NULL;
  listeners = NULL;
#if CACHE_ENABLED
  cache_s = 0;
  cache_thr = 0;
#endif
  parse_file();

  if (check_only) {
    Debug::logmsg(LOG_INFO, "Config file %s is OK", conf_name);
    exit(0);
  }

  if (listeners == NULL) {
    Debug::logmsg(LOG_ERR, "no listeners defined - aborted");
    exit(1);
  }

  // free compiled regex
  clean_regex();

  /* set the facility only here to ensure the syslog gets opened if necessary
   */
  log_facility = def_facility;

  return;
}

char *Config::file2str(const char *fname) {
  char *res;
  struct stat st;
  int fin;

  if (stat(fname, &st)) conf_err("can't stat Err file - aborted");
  if ((fin = open(fname, O_RDONLY)) < 0)
    conf_err("can't open Err file - aborted");
  if ((res = malloc(st.st_size + 1)) == NULL)
    conf_err("can't alloc Err file (out of memory) - aborted");
  if (read(fin, res, st.st_size) != st.st_size)
    conf_err("can't read Err file - aborted");
  res[st.st_size] = '\0';
  close(fin);
  return res;
}

ListenerConfig *Config::parse_HTTP() {
  char lin[MAXBUF];
  ListenerConfig *res;
  ServiceConfig *svc;
  MATCHER *m;
  int has_addr, has_port;
  struct sockaddr_in in;
  struct sockaddr_in6 in6;
  regmatch_t matches[5];

  if ((res = new ListenerConfig()) ==
      nullptr) /*(Listener_t *)malloc(sizeof(Listener_t))) == NULL)*/
    conf_err("ListenHTTP config: out of memory - aborted");
  memset(res, 0, sizeof(ListenerConfig));
  res->to = clnt_to;
  res->rewr_loc = 1;
  res->err414 = "Request URI is too long";
  res->err500 = "An internal server error occurred. Please try again later.";
  res->err501 = "This method may not be used.";
  res->err503 = "The service is not available. Please try again later.";
  res->errnossl = "Please use HTTPS.";
  res->nossl_url = NULL;
  res->nossl_redir = 0;
  res->log_level = log_level;
  res->alive_to = alive_to;
  res->ignore100continue = ignore_100;
  if (regcomp(&res->verb, xhttp[0], REG_ICASE | REG_NEWLINE | REG_EXTENDED))
    conf_err("xHTTP bad default pattern - aborted");
  has_addr = has_port = 0;
  while (conf_fgets(lin, MAXBUF)) {
    if (strlen(lin) > 0 && lin[strlen(lin) - 1] == '\n')
      lin[strlen(lin) - 1] = '\0';
    if (!regexec(&Address, lin, 4, matches, 0)) {
      lin[matches[1].rm_eo] = '\0';
      if (get_host(lin + matches[1].rm_so, &res->addr, PF_UNSPEC))
        conf_err("Unknown Listener address");
      if (res->addr.ai_family != AF_INET && res->addr.ai_family != AF_INET6)
        conf_err("Unknown Listener address family");
      has_addr = 1;
      res->address = lin + matches[1].rm_so;
    } else if (!regexec(&Port, lin, 4, matches, 0)) {
      switch (res->addr.ai_family) {
        case AF_INET:memcpy(&in, res->addr.ai_addr, sizeof(in));
          in.sin_port = (in_port_t) htons(atoi(lin + matches[1].rm_so));
          memcpy(res->addr.ai_addr, &in, sizeof(in));
          break;
        case AF_INET6:memcpy(&in6, res->addr.ai_addr, sizeof(in6));
          in6.sin6_port = htons(atoi(lin + matches[1].rm_so));
          memcpy(res->addr.ai_addr, &in6, sizeof(in6));
          break;
        default:conf_err("Unknown Listener address family");
      }
      has_port = 1;
      res->port = std::atoi(lin + matches[1].rm_so);
    } else if (!regexec(&xHTTP, lin, 4, matches, 0)) {
      int n;

      n = atoi(lin + matches[1].rm_so);
      regfree(&res->verb);
      if (regcomp(&res->verb, xhttp[n], REG_ICASE | REG_NEWLINE | REG_EXTENDED))
        conf_err("xHTTP bad pattern - aborted");
    } else if (!regexec(&Client, lin, 4, matches, 0)) {
      res->to = atoi(lin + matches[1].rm_so);
    } else if (!regexec(&CheckURL, lin, 4, matches, 0)) {
      if (res->has_pat) conf_err("CheckURL multiple pattern - aborted");
      lin[matches[1].rm_eo] = '\0';
      if (regcomp(&res->url_pat, lin + matches[1].rm_so,
                  REG_NEWLINE | REG_EXTENDED | (ignore_case ? REG_ICASE : 0)))
        conf_err("CheckURL bad pattern - aborted");
      res->has_pat = 1;
    } else if (!regexec(&Err414, lin, 4, matches, 0)) {
      lin[matches[1].rm_eo] = '\0';
      res->err414 = file2str(lin + matches[1].rm_so);
    } else if (!regexec(&Err500, lin, 4, matches, 0)) {
      lin[matches[1].rm_eo] = '\0';
      res->err500 = file2str(lin + matches[1].rm_so);
    } else if (!regexec(&Err501, lin, 4, matches, 0)) {
      lin[matches[1].rm_eo] = '\0';
      res->err501 = file2str(lin + matches[1].rm_so);
    } else if (!regexec(&Err503, lin, 4, matches, 0)) {
      lin[matches[1].rm_eo] = '\0';
      res->err503 = file2str(lin + matches[1].rm_so);
    } else if (!regexec(&MaxRequest, lin, 4, matches, 0)) {
      res->max_req = atoll(lin + matches[1].rm_so);
    } else if (!regexec(&HeadRemove, lin, 4, matches, 0)) {
      if (res->head_off) {
        for (m = res->head_off; m->next; m = m->next);
        if ((m->next = (MATCHER *) malloc(sizeof(MATCHER))) == NULL)
          conf_err("HeadRemove config: out of memory - aborted");
        m = m->next;
      } else {
        if ((res->head_off = (MATCHER *) malloc(sizeof(MATCHER))) == NULL)
          conf_err("HeadRemove config: out of memory - aborted");
        m = res->head_off;
      }
      memset(m, 0, sizeof(MATCHER));
      lin[matches[1].rm_eo] = '\0';
      if (regcomp(&m->pat, lin + matches[1].rm_so,
                  REG_ICASE | REG_NEWLINE | REG_EXTENDED))
        conf_err("HeadRemove bad pattern - aborted");
    } else if (!regexec(&AddHeader, lin, 4, matches, 0)) {
      lin[matches[1].rm_eo] = '\0';
      if (res->add_head == NULL) {
        if ((res->add_head = strdup(lin + matches[1].rm_so)) == NULL)
          conf_err("AddHeader config: out of memory - aborted");
      } else {
        if ((res->add_head = realloc(
            res->add_head,
            strlen(res->add_head) + strlen(lin + matches[1].rm_so) + 3)) ==
            NULL)
          conf_err("AddHeader config: out of memory - aborted");
        strcat(res->add_head, "\r\n");
        strcat(res->add_head, lin + matches[1].rm_so);
      }
    } else if (!regexec(&RewriteLocation, lin, 4, matches, 0)) {
      res->rewr_loc = atoi(lin + matches[1].rm_so);
    } else if (!regexec(&RewriteDestination, lin, 4, matches, 0)) {
      res->rewr_dest = atoi(lin + matches[1].rm_so);
    } else if (!regexec(&RewriteHost, lin, 4, matches, 0)) {
      res->rewr_host = atoi(lin + matches[1].rm_so);
    }else if (!regexec(&LogLevel, lin, 4, matches, 0)) {
      res->log_level = atoi(lin + matches[1].rm_so);
    } else if (!regexec(&SSLConfigFile, lin, 4, matches, 0)) {
      conf_err("SSLConfigFile directive not allowed in HTTP listeners.");
    } else if (!regexec(&SSLConfigSection, lin, 4, matches, 0)) {
      conf_err("SSLConfigSection directive not allowed in HTTP listeners.");
    } else if (!regexec(&ForceHTTP10, lin, 4, matches, 0)) {
      if ((m = (MATCHER *) malloc(sizeof(MATCHER))) == NULL)
        conf_err("out of memory");
      memset(m, 0, sizeof(MATCHER));
      m->next = res->forcehttp10;
      res->forcehttp10 = m;
      lin[matches[1].rm_eo] = '\0';
      if (regcomp(&m->pat, lin + matches[1].rm_so,
                  REG_ICASE | REG_NEWLINE | REG_EXTENDED))
        conf_err("ForceHTTP10 bad pattern");
    } else if (!regexec(&Service, lin, 4, matches, 0)) {
      if (res->services == NULL) {
        res->services = parseService(NULL);
        if (res->services->sts >= 0)
          conf_err(
              "StrictTransportSecurity not allowed in HTTP listener - "
              "aborted");
      } else {
        for (svc = res->services; svc->next; svc = svc->next);
        svc->next = parseService(NULL);
        if (svc->next->sts >= 0)
          conf_err(
              "StrictTransportSecurity not allowed in HTTP listener - "
              "aborted");
      }
    } else if (!regexec(&ServiceName, lin, 4, matches, 0)) {
      lin[matches[1].rm_eo] = '\0';
      if (res->services == NULL)
        res->services = parseService(lin + matches[1].rm_so);
      else {
        for (svc = res->services; svc->next; svc = svc->next);
        svc->next = parseService(lin + matches[1].rm_so);
      }
    } else if (!regexec(&End, lin, 4, matches, 0)) {
      if (!has_addr || !has_port)
        conf_err("ListenHTTP missing Address or Port - aborted");
      return res;
    } else {
      conf_err("unknown directive - aborted");
    }
  }

  conf_err("ListenHTTP premature EOF");
  return NULL;
}

ListenerConfig *Config::parse_HTTPS() {
  char lin[MAXBUF];
  ListenerConfig *res;
  ServiceConfig *svc;
  MATCHER *m;
  int has_addr, has_port, has_other;
  long ssl_op_enable, ssl_op_disable;
  struct hostent *host;
  struct sockaddr_in in;
  struct sockaddr_in6 in6;
  POUND_CTX *pc;
  regmatch_t matches[5];
  bool openssl_file_exists = false;

  ssl_op_enable = SSL_OP_ALL;
#ifdef SSL_OP_NO_COMPRESSION
  ssl_op_enable |= SSL_OP_NO_COMPRESSION;
#endif
  ssl_op_disable = SSL_OP_ALLOW_UNSAFE_LEGACY_RENEGOTIATION |
      SSL_OP_LEGACY_SERVER_CONNECT |
      SSL_OP_DONT_INSERT_EMPTY_FRAGMENTS;

  //  if ((res = (Listener_t *)malloc(sizeof(Listener_t))) == NULL)
  if ((res = new ListenerConfig()) == nullptr)
    conf_err("ListenHTTPS config: out of memory - aborted");
  memset(res, 0, sizeof(ListenerConfig));

  res->to = clnt_to;
  res->rewr_loc = 1;
  res->err414 = "Request URI is too long";
  res->err500 = "An internal server error occurred. Please try again later.";
  res->err501 = "This method may not be used.";
  res->err503 = "The service is not available. Please try again later.";
  res->allow_client_reneg = 0;
  res->errnossl = "Please use HTTPS.";
  res->nossl_url = NULL;
  res->nossl_redir = 0;
  res->log_level = log_level;
  res->alive_to = alive_to;
  res->engine_id = engine_id;

  if (regcomp(&res->verb, xhttp[0], REG_ICASE | REG_NEWLINE | REG_EXTENDED))
    conf_err("xHTTP bad default pattern - aborted");
  has_addr = has_port = has_other = 0;
  while (conf_fgets(lin, MAXBUF)) {
    if (strlen(lin) > 0 && lin[strlen(lin) - 1] == '\n')
      lin[strlen(lin) - 1] = '\0';
    if (!regexec(&Address, lin, 4, matches, 0)) {
      lin[matches[1].rm_eo] = '\0';
      if (get_host(lin + matches[1].rm_so, &res->addr, PF_UNSPEC))
        conf_err("Unknown Listener address");
      if (res->addr.ai_family != AF_INET && res->addr.ai_family != AF_INET6)
        conf_err("Unknown Listener address family");
      has_addr = 1;
      res->address = lin + matches[1].rm_so;
    } else if (!regexec(&Port, lin, 4, matches, 0)) {
      if (res->addr.ai_family == AF_INET) {
        memcpy(&in, res->addr.ai_addr, sizeof(in));
        in.sin_port = (in_port_t) htons(atoi(lin + matches[1].rm_so));
        memcpy(res->addr.ai_addr, &in, sizeof(in));
      } else {
        memcpy(&in6, res->addr.ai_addr, sizeof(in6));
        in6.sin6_port = htons(atoi(lin + matches[1].rm_so));
        memcpy(res->addr.ai_addr, &in6, sizeof(in6));
      }
      has_port = 1;
      res->port = atoi(lin + matches[1].rm_so);
    } else if (!regexec(&xHTTP, lin, 4, matches, 0)) {
      int n;

      n = atoi(lin + matches[1].rm_so);
      regfree(&res->verb);
      if (regcomp(&res->verb, xhttp[n], REG_ICASE | REG_NEWLINE | REG_EXTENDED))
        conf_err("xHTTP bad pattern - aborted");
    } else if (!regexec(&Client, lin, 4, matches, 0)) {
      res->to = atoi(lin + matches[1].rm_so);
    } else if (!regexec(&CheckURL, lin, 4, matches, 0)) {
      if (res->has_pat) conf_err("CheckURL multiple pattern - aborted");
      lin[matches[1].rm_eo] = '\0';
      if (regcomp(&res->url_pat, lin + matches[1].rm_so,
                  REG_NEWLINE | REG_EXTENDED | (ignore_case ? REG_ICASE : 0)))
        conf_err("CheckURL bad pattern - aborted");
      res->has_pat = 1;
    } else if (!regexec(&Err414, lin, 4, matches, 0)) {
      lin[matches[1].rm_eo] = '\0';
      res->err414 = file2str(lin + matches[1].rm_so);
    } else if (!regexec(&Err500, lin, 4, matches, 0)) {
      lin[matches[1].rm_eo] = '\0';
      res->err500 = file2str(lin + matches[1].rm_so);
    } else if (!regexec(&Err501, lin, 4, matches, 0)) {
      lin[matches[1].rm_eo] = '\0';
      res->err501 = file2str(lin + matches[1].rm_so);
    } else if (!regexec(&Err503, lin, 4, matches, 0)) {
      lin[matches[1].rm_eo] = '\0';
      res->err503 = file2str(lin + matches[1].rm_so);
    } else if (!regexec(&ErrNoSsl, lin, 4, matches, 0)) {
      lin[matches[1].rm_eo] = '\0';
      res->errnossl = file2str(lin + matches[1].rm_so);
    } else if (!regexec(&NoSslRedirect, lin, 4, matches, 0)) {
      res->nossl_redir = 302;
      if (matches[1].rm_eo != matches[1].rm_so)
        res->nossl_redir = atoi(lin + matches[1].rm_so);
      lin[matches[2].rm_eo] = '\0';
      if ((res->nossl_url = strdup(lin + matches[2].rm_so)) == NULL)
        conf_err("NoSslRedirect out of memory");
      if (regexec(&LOCATION, res->nossl_url, 4, matches, 0))
        conf_err("Redirect bad URL - aborted");
      if ((matches[3].rm_eo - matches[3].rm_so) == 1)
        /* the path is a single '/', so remove it */
        res->nossl_url[matches[3].rm_so] = '\0';
    } else if (!regexec(&MaxRequest, lin, 4, matches, 0)) {
      res->max_req = atoll(lin + matches[1].rm_so);
    } else if (!regexec(&HeadRemove, lin, 4, matches, 0)) {
      if (res->head_off) {
        for (m = res->head_off; m->next; m = m->next);
        if ((m->next = (MATCHER *) malloc(sizeof(MATCHER))) == NULL)
          conf_err("HeadRemove config: out of memory - aborted");
        m = m->next;
      } else {
        if ((res->head_off = (MATCHER *) malloc(sizeof(MATCHER))) == NULL)
          conf_err("HeadRemove config: out of memory - aborted");
        m = res->head_off;
      }
      memset(m, 0, sizeof(MATCHER));
      lin[matches[1].rm_eo] = '\0';
      if (regcomp(&m->pat, lin + matches[1].rm_so,
                  REG_ICASE | REG_NEWLINE | REG_EXTENDED))
        conf_err("HeadRemove bad pattern - aborted");
    } else if (!regexec(&RewriteLocation, lin, 4, matches, 0)) {
      res->rewr_loc = atoi(lin + matches[1].rm_so);
    } else if (!regexec(&RewriteDestination, lin, 4, matches, 0)) {
      res->rewr_dest = atoi(lin + matches[1].rm_so);
    }else if (!regexec(&RewriteHost, lin, 4, matches, 0)) {
      res->rewr_host = atoi(lin + matches[1].rm_so);
    } else if (!regexec(&LogLevel, lin, 4, matches, 0)) {
      res->log_level = atoi(lin + matches[1].rm_so);
    } else if (!regexec(&Cert, lin, 4, matches, 0)) {
      lin[matches[1].rm_eo] = '\0';
      load_cert(has_other, res, lin + matches[1].rm_so);
    } else if (!regexec(&CertDir, lin, 4, matches, 0)) {
      lin[matches[1].rm_eo] = '\0';
      load_certdir(has_other, res, lin + matches[1].rm_so);
    } else if (!regexec(&ClientCert, lin, 4, matches, 0)) {
      has_other = 1;
      if (res->ctx == NULL)
        conf_err("ClientCert may only be used after Cert - aborted");
      switch (res->clnt_check = atoi(lin + matches[1].rm_so)) {
        case 0:
          /* don't ask */
          for (pc = res->ctx; pc; pc = pc->next)
            SSL_CTX_set_verify(pc->ctx, SSL_VERIFY_NONE, NULL);
          break;
        case 1:
          /* ask but OK if no client certificate */
          for (pc = res->ctx; pc; pc = pc->next) {
            SSL_CTX_set_verify(pc->ctx,
                               SSL_VERIFY_PEER | SSL_VERIFY_CLIENT_ONCE, NULL);
            SSL_CTX_set_verify_depth(pc->ctx, atoi(lin + matches[2].rm_so));
          }
          break;
        case 2:
          /* ask and fail if no client certificate */
          for (pc = res->ctx; pc; pc = pc->next) {
            SSL_CTX_set_verify(
                pc->ctx, SSL_VERIFY_PEER | SSL_VERIFY_FAIL_IF_NO_PEER_CERT,
                NULL);
            SSL_CTX_set_verify_depth(pc->ctx, atoi(lin + matches[2].rm_so));
          }
          break;
        case 3:
          /* ask but do not verify client certificate */
          for (pc = res->ctx; pc; pc = pc->next) {
            SSL_CTX_set_verify(
                pc->ctx, SSL_VERIFY_PEER | SSL_VERIFY_CLIENT_ONCE, verify_OK);
            SSL_CTX_set_verify_depth(pc->ctx, atoi(lin + matches[2].rm_so));
          }
          break;
      }
    } else if (!regexec(&AddHeader, lin, 4, matches, 0)) {
      lin[matches[1].rm_eo] = '\0';
      if (res->add_head == NULL) {
        if ((res->add_head = strdup(lin + matches[1].rm_so)) == NULL)
          conf_err("AddHeader config: out of memory - aborted");
      } else {
        if ((res->add_head = realloc(
            res->add_head,
            strlen(res->add_head) + strlen(lin + matches[1].rm_so) + 3)) ==
            NULL)
          conf_err("AddHeader config: out of memory - aborted");
        strcat(res->add_head, "\r\n");
        strcat(res->add_head, lin + matches[1].rm_so);
      }
    } else if (!regexec(&DisableProto, lin, 4, matches, 0)) {
      lin[matches[1].rm_eo] = '\0';
      if (strcasecmp(lin + matches[1].rm_so, "SSLv2") == 0)
        ssl_op_enable |= SSL_OP_NO_SSLv2;
      else if (strcasecmp(lin + matches[1].rm_so, "SSLv3") == 0)
        ssl_op_enable |= SSL_OP_NO_SSLv2 | SSL_OP_NO_SSLv3;
#ifdef SSL_OP_NO_TLSv1
      else if (strcasecmp(lin + matches[1].rm_so, "TLSv1") == 0)
        ssl_op_enable |= SSL_OP_NO_SSLv2 | SSL_OP_NO_SSLv3 | SSL_OP_NO_TLSv1;
#endif
#ifdef SSL_OP_NO_TLSv1_1
      else if (strcasecmp(lin + matches[1].rm_so, "TLSv1_1") == 0)
        ssl_op_enable |= SSL_OP_NO_SSLv2 | SSL_OP_NO_SSLv3 | SSL_OP_NO_TLSv1 |
            SSL_OP_NO_TLSv1_1;
#endif
#ifdef SSL_OP_NO_TLSv1_2
      else if (strcasecmp(lin + matches[1].rm_so, "TLSv1_2") == 0)
        ssl_op_enable |= SSL_OP_NO_SSLv2 | SSL_OP_NO_SSLv3 | SSL_OP_NO_TLSv1 |
            SSL_OP_NO_TLSv1_1 | SSL_OP_NO_TLSv1_2;
#endif
#ifdef SSL_OP_NO_TLSv1_3
            else if(strcasecmp(lin + matches[1].rm_so, "TLSv1_3") == 0)
                ssl_op_enable |= SSL_OP_NO_SSLv2 | SSL_OP_NO_SSLv3 | SSL_OP_NO_TLSv1 | SSL_OP_NO_TLSv1_1 | SSL_OP_NO_TLSv1_2 | SSL_OP_NO_TLSv1_3;
#endif
    } else if (!regexec(&SSLAllowClientRenegotiation, lin, 4, matches, 0)) {
      res->allow_client_reneg = atoi(lin + matches[1].rm_so);
      if (res->allow_client_reneg == 2) {
        ssl_op_enable |= SSL_OP_ALLOW_UNSAFE_LEGACY_RENEGOTIATION;
        ssl_op_disable &= ~SSL_OP_ALLOW_UNSAFE_LEGACY_RENEGOTIATION;
      } else {
        ssl_op_disable |= SSL_OP_ALLOW_UNSAFE_LEGACY_RENEGOTIATION;
        ssl_op_enable &= ~SSL_OP_ALLOW_UNSAFE_LEGACY_RENEGOTIATION;
      }
    } else if (!regexec(&SSLHonorCipherOrder, lin, 4, matches, 0)) {
      if (atoi(lin + matches[1].rm_so)) {
        ssl_op_enable |= SSL_OP_CIPHER_SERVER_PREFERENCE;
        ssl_op_disable &= ~SSL_OP_CIPHER_SERVER_PREFERENCE;
      } else {
        ssl_op_disable |= SSL_OP_CIPHER_SERVER_PREFERENCE;
        ssl_op_enable &= ~SSL_OP_CIPHER_SERVER_PREFERENCE;
      }
    } else if (!regexec(&Ciphers, lin, 4, matches, 0)) {
      has_other = 1;
      if (res->ctx == NULL)
        conf_err("Ciphers may only be used after Cert - aborted");
      lin[matches[1].rm_eo] = '\0';
      for (pc = res->ctx; pc; pc = pc->next)
        SSL_CTX_set_cipher_list(pc->ctx, lin + matches[1].rm_so);
    } else if (!regexec(&CAlist, lin, 4, matches, 0)) {
      STACK_OF(X509_NAME) *cert_names;

      has_other = 1;
      if (res->ctx == NULL)
        conf_err("CAList may only be used after Cert - aborted");
      lin[matches[1].rm_eo] = '\0';
      if ((cert_names = SSL_load_client_CA_file(lin + matches[1].rm_so)) ==
          NULL)
        conf_err("SSL_load_client_CA_file failed - aborted");
      for (pc = res->ctx; pc; pc = pc->next)
        SSL_CTX_set_client_CA_list(pc->ctx, cert_names);
    } else if (!regexec(&VerifyList, lin, 4, matches, 0)) {
      has_other = 1;
      if (res->ctx == NULL)
        conf_err("VerifyList may only be used after Cert - aborted");
      lin[matches[1].rm_eo] = '\0';
      for (pc = res->ctx; pc; pc = pc->next)
        if (SSL_CTX_load_verify_locations(pc->ctx, lin + matches[1].rm_so,
                                          NULL) != 1)
          conf_err("SSL_CTX_load_verify_locations failed - aborted");
    } else if (!regexec(&SSLConfigFile, lin, 4, matches, 0)) {
      lin[matches[1].rm_eo] = '\0';
      res->ssl_config_file = std::string(lin + matches[1].rm_so);
      openssl_file_exists = true;
    } else if (!regexec(&SSLConfigSection, lin, 4, matches, 0)) {
      lin[matches[1].rm_eo] = '\0';
      std::string section = lin + matches[1].rm_so;
      res->ssl_config_section = section.c_str();
    } else if (!regexec(&CRLlist, lin, 4, matches, 0)) {
      //#if HAVE_X509_STORE_SET_FLAGS
      X509_STORE *store;
      X509_LOOKUP *lookup;

      has_other = 1;
      if (res->ctx == NULL)
        conf_err("CRLlist may only be used after Cert - aborted");
      lin[matches[1].rm_eo] = '\0';
      for (pc = res->ctx; pc; pc = pc->next) {
        store = SSL_CTX_get_cert_store(pc->ctx);
        if ((lookup = X509_STORE_add_lookup(store, X509_LOOKUP_file())) == NULL)
          conf_err("X509_STORE_add_lookup failed - aborted");
        if (X509_load_crl_file(lookup, lin + matches[1].rm_so,
                               X509_FILETYPE_PEM) != 1)
          conf_err("X509_load_crl_file failed - aborted");
        X509_STORE_set_flags(store,
                             X509_V_FLAG_CRL_CHECK | X509_V_FLAG_CRL_CHECK_ALL);
      }
      //#else
      //        conf_err("your version of OpenSSL does not support CRL
      //        checking");
      //#endif
    } else if (!regexec(&NoHTTPS11, lin, 4, matches, 0)) {
      res->noHTTPS11 = atoi(lin + matches[1].rm_so);
    } else if (!regexec(&ForceHTTP10, lin, 4, matches, 0)) {
      if ((m = (MATCHER *) malloc(sizeof(MATCHER))) == NULL)
        conf_err("out of memory");
      memset(m, 0, sizeof(MATCHER));
      m->next = res->forcehttp10;
      res->forcehttp10 = m;
      lin[matches[1].rm_eo] = '\0';
      if (regcomp(&m->pat, lin + matches[1].rm_so,
                  REG_ICASE | REG_NEWLINE | REG_EXTENDED))
        conf_err("bad pattern");
    } else if (!regexec(&SSLUncleanShutdown, lin, 4, matches, 0)) {
      if ((m = (MATCHER *) malloc(sizeof(MATCHER))) == NULL)
        conf_err("out of memory");
      memset(m, 0, sizeof(MATCHER));
      m->next = res->ssl_uncln_shutdn;
      res->ssl_uncln_shutdn = m;
      lin[matches[1].rm_eo] = '\0';
      if (regcomp(&m->pat, lin + matches[1].rm_so,
                  REG_ICASE | REG_NEWLINE | REG_EXTENDED))
        conf_err("bad pattern");
    } else if (!regexec(&Service, lin, 4, matches, 0)) {
      if (res->services == NULL)
        res->services = parseService(NULL);
      else {
        for (svc = res->services; svc->next; svc = svc->next);
        svc->next = parseService(NULL);
      }
    } else if (!regexec(&ServiceName, lin, 4, matches, 0)) {
      lin[matches[1].rm_eo] = '\0';
      if (res->services == NULL)
        res->services = parseService(lin + matches[1].rm_so);
      else {
        for (svc = res->services; svc->next; svc = svc->next);
        svc->next = parseService(lin + matches[1].rm_so);
      }
    } else if (!regexec(&End, lin, 4, matches, 0)) {
      X509_STORE *store;

      if (openssl_file_exists) {
      if ((res->ctx = malloc(sizeof(POUND_CTX))) == NULL)
        conf_err("ListenHTTPS new POUND_CTX: out of memory - aborted");
      if ((res->ctx->ctx = SSL_CTX_new(SSLv23_server_method())) == NULL)
        conf_err("SSL_CTX_new failed - aborted");
      }
      if ((!has_addr || !has_port || res->ctx == NULL) && !openssl_file_exists)
        conf_err("ListenHTTPS missing Address, Port, SSL Config file or Certificate - aborted");
      if (!openssl_file_exists) {

      for (pc = res->ctx; pc; pc = pc->next) {
        SSL_CTX_set_app_data(pc->ctx, res);
        SSL_CTX_set_mode(pc->ctx, SSL_MODE_RELEASE_BUFFERS);
        SSL_CTX_set_options(pc->ctx, ssl_op_enable);
        SSL_CTX_clear_options(pc->ctx, ssl_op_disable);
        sprintf(lin, "%d-Zhttp-%ld", getpid(), random());
        SSL_CTX_set_session_id_context(pc->ctx, (unsigned char *) lin,
                                       strlen(lin));
        SSL_CTX_set_tmp_rsa_callback(pc->ctx, RSA_tmp_callback);
        SSL_CTX_set_info_callback(pc->ctx, SSLINFO_callback);
        if (NULL == DHCustom_params)
          SSL_CTX_set_tmp_dh_callback(pc->ctx, DH_tmp_callback);
        else
          SSL_CTX_set_tmp_dh(pc->ctx, DHCustom_params);

#if OPENSSL_VERSION_NUMBER >= 0x0090800fL
#ifndef OPENSSL_NO_ECDH
        /* This generates a EC_KEY structure with no key, but a group defined
         */
        EC_KEY *ecdh;
        if ((ecdh = EC_KEY_new_by_curve_name(EC_nid)) == NULL)
          conf_err("Unable to generate temp ECDH key");
        SSL_CTX_set_tmp_ecdh(pc->ctx, ecdh);
        SSL_CTX_set_options(pc->ctx, SSL_OP_SINGLE_ECDH_USE);
        EC_KEY_free(ecdh);
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
  return NULL;
}

unsigned char **Config::get_subjectaltnames(X509 *x509, unsigned int *count) {
  unsigned int local_count;
  unsigned char **result;
  STACK_OF(GENERAL_NAME) *san_stack =
      (STACK_OF(GENERAL_NAME) *) X509_get_ext_d2i(x509, NID_subject_alt_name,
                                                  NULL, NULL);
  unsigned char *temp[sk_GENERAL_NAME_num(san_stack)];
  GENERAL_NAME *name;
  int i;

  local_count = 0;
  result = NULL;
  name = NULL;
  *count = 0;
  if (san_stack == NULL) return NULL;
  while (sk_GENERAL_NAME_num(san_stack) > 0) {
    name = sk_GENERAL_NAME_pop(san_stack);
    switch (name->type) {
      case GEN_DNS:
        temp[local_count] = general_name_string(name);
        if (temp[local_count] == NULL) conf_err("out of memory");
        local_count++;
        break;
      default:
        Debug::logmsg(LOG_INFO,
                      "unsupported subjectAltName type encountered: %i",
                      name->type);
    }
    GENERAL_NAME_free(name);
  }

  result = (unsigned char **) malloc(sizeof(unsigned char *) * local_count);
  if (result == NULL) conf_err("out of memory");
  for (i = 0; i < local_count; i++) {
    result[i] = strndup(temp[i], strlen(temp[i]) + 1);
    if (result[i] == NULL) conf_err("out of memory");
    free(temp[i]);
  }
  *count = local_count;

  sk_GENERAL_NAME_pop_free(san_stack, GENERAL_NAME_free);

  return result;
}

void Config::load_cert(int has_other, ListenerConfig *res, char *filename) {
  POUND_CTX *pc;
#ifdef SSL_CTRL_SET_TLSEXT_SERVERNAME_CB
  /* we have support for SNI */
  FILE *fcert;
  char server_name[MAXBUF], *cp;
  X509 *x509;
  regmatch_t matches[5];

  if (has_other)
    conf_err(
        "Cert directives MUST precede other SSL-specific directives - "
        "aborted");
  if (res->ctx) {
    for (pc = res->ctx; pc->next; pc = pc->next);
    if ((pc->next = malloc(sizeof(POUND_CTX))) == NULL)
      conf_err("ListenHTTPS new POUND_CTX: out of memory - aborted");
    pc = pc->next;
  } else {
    if ((res->ctx = malloc(sizeof(POUND_CTX))) == NULL)
      conf_err("ListenHTTPS new POUND_CTX: out of memory - aborted");
    pc = res->ctx;
  }
  if ((pc->ctx = SSL_CTX_new(SSLv23_server_method())) == NULL)
    conf_err("SSL_CTX_new failed - aborted");
  pc->server_name = NULL;
  pc->next = NULL;
  if (SSL_CTX_use_certificate_chain_file(pc->ctx, filename) != 1)
    conf_err("SSL_CTX_use_certificate_chain_file failed - aborted");
  if (SSL_CTX_use_PrivateKey_file(pc->ctx, filename, SSL_FILETYPE_PEM) != 1)
    conf_err("SSL_CTX_use_PrivateKey_file failed - aborted");
  if (SSL_CTX_check_private_key(pc->ctx) != 1)
    conf_err("SSL_CTX_check_private_key failed - aborted");
  if ((fcert = fopen(filename, "r")) == NULL)
    conf_err("ListenHTTPS: could not open certificate file");
  if ((x509 = PEM_read_X509(fcert, NULL, NULL, NULL)) == NULL)
    conf_err("ListenHTTPS: could not get certificate subject");
  fclose(fcert);
  memset(server_name, '\0', MAXBUF);
  X509_NAME_oneline(X509_get_subject_name(x509), server_name, MAXBUF - 1);
  pc->subjectAltNameCount = 0;
  pc->subjectAltNames = NULL;
  pc->subjectAltNames = get_subjectaltnames(x509, &(pc->subjectAltNameCount));
  X509_free(x509);
  if (!regexec(&CNName, server_name, 4, matches, 0)) {
    server_name[matches[1].rm_eo] = '\0';
    if ((pc->server_name = strdup(server_name + matches[1].rm_so)) == NULL)
      conf_err("ListenHTTPS: could not set certificate subject");
  } else
    Debug::logmsg(LOG_ERR, "ListenHTTPS: could not get certificate CN");
// ZLB Patch - Disable exit error when CN is not present
// conf_err("ListenHTTPS: could not get certificate CN");
#else
  /* no SNI support */
  if (has_other)
    conf_err(
        "Cert directives MUST precede other SSL-specific directives - "
        "aborted");
  if (res->ctx)
    conf_err("ListenHTTPS: multiple certificates not supported - aborted");
  if ((res->ctx = malloc(sizeof(POUND_CTX))) == NULL)
    conf_err("ListenHTTPS new POUND_CTX: out of memory - aborted");
  res->ctx->server_name = NULL;
  res->ctx->next = NULL;
  if ((res->ctx->ctx = SSL_CTX_new(SSLv23_server_method())) == NULL)
    conf_err("SSL_CTX_new failed - aborted");
  if (SSL_CTX_use_certificate_chain_file(res->ctx->ctx, filename) != 1)
    conf_err("SSL_CTX_use_certificate_chain_file failed - aborted");
  if (SSL_CTX_use_PrivateKey_file(res->ctx->ctx, filename, SSL_FILETYPE_PEM) !=
      1)
    conf_err("SSL_CTX_use_PrivateKey_file failed - aborted");
  if (SSL_CTX_check_private_key(res->ctx->ctx) != 1)
    conf_err("SSL_CTX_check_private_key failed - aborted");
#endif
}

void Config::load_certdir(int has_other, ListenerConfig *res,
                          const char *dir_path) {
  DIR *dp;
  struct dirent *de;

  char buf[512];
  char *files[200], *cp;
  char *pattern;
  int filecnt = 0;
  int idx, use;

  Debug::logmsg(LOG_DEBUG, "Including Certs from Dir %s", dir_path);

  pattern = strrchr(dir_path, '/');
  if (pattern) {
    *pattern++ = 0;
    if (!*pattern) pattern = NULL;
  }

  if ((dp = opendir(dir_path)) == NULL) {
    conf_err("can't open IncludeDir directory");
    exit(1);
  }

  while ((de = readdir(dp)) != NULL) {
    if (de->d_name[0] == '.') continue;
    if (!pattern || fnmatch(pattern, de->d_name, 0) == 0) {
      snprintf(buf, sizeof(buf), "%s%s%s", dir_path,
               (dir_path[strlen(dir_path) - 1] == '/') ? "" : "/", de->d_name);
      buf[sizeof(buf) - 1] = 0;
      if (filecnt == sizeof(files) / sizeof(*files)) {
        conf_err("Max certificate files per directory reached");
      }
      if ((files[filecnt++] = strdup(buf)) == NULL) {
        conf_err("CertDir out of memory");
      }
      continue;
    }
  }
  /* We order the list, and load in ascending order */
  while (filecnt) {
    use = 0;
    for (idx = 1; idx < filecnt; idx++)
      if (strcmp(files[use], files[idx]) > 0) use = idx;

    Debug::logmsg(LOG_DEBUG, " I Cert ==> %s", files[use]);

    load_cert(has_other, res, files[use]);
    files[use] = files[--filecnt];
  }

  closedir(dp);
}

ServiceConfig *Config::parseService(const char *svc_name) {
  char lin[MAXBUF];
  char pat[MAXBUF];
  char *ptr;
  ServiceConfig *res;
  BackendConfig *be;
  MATCHER *m;
  int ign_case;
  regmatch_t matches[5];

  if ((res = new ServiceConfig()) == nullptr) {
    conf_err("Service config: out of memory - aborted");
  }
  memset(res, 0, sizeof(ServiceConfig));
  res->max_headers_allowed = 128;
  res->sess_type = SESS_NONE;
  res->dynscale = dynscale;
  res->sts = -1;
  pthread_mutex_init(&res->mut, NULL);
  if (svc_name) strncpy(res->name, svc_name, KEY_SIZE);
#if OPENSSL_VERSION_NUMBER >= 0x10100000L
    if((res->sessions = lh_TABNODE_new(t_hash, t_cmp)) == NULL)
#elif OPENSSL_VERSION_NUMBER >= 0x10000000L
    if((res->sessions = LHM_lh_new(TABNODE, t)) == NULL)
#else
    if((res->sessions = lh_new(LHASH_HASH_FN(t_hash), LHASH_COMP_FN(t_cmp))) == NULL)
#endif
    conf_err("lh_new failed - aborted");
  if (res->sessions == NULL) conf_err("lh_new failed - aborted");
  ign_case = ignore_case;
  while (conf_fgets(lin, MAXBUF)) {
    if (strlen(lin) > 0 && lin[strlen(lin) - 1] == '\n')
      lin[strlen(lin) - 1] = '\0';
    if (!regexec(&URL, lin, 4, matches, 0)) {
      if (res->url) {
        for (m = res->url; m->next; m = m->next);
        if ((m->next = (MATCHER *) malloc(sizeof(MATCHER))) == NULL)
          conf_err("URL config: out of memory - aborted");
        m = m->next;
      } else {
        if ((res->url = (MATCHER *) malloc(sizeof(MATCHER))) == NULL)
          conf_err("URL config: out of memory - aborted");
        m = res->url;
      }
      memset(m, 0, sizeof(MATCHER));
      lin[matches[1].rm_eo] = '\0';
      if (regcomp(&m->pat, lin + matches[1].rm_so,
                  REG_NEWLINE | REG_EXTENDED | (ign_case ? REG_ICASE : 0)))
        conf_err("URL bad pattern - aborted");
    } else if (!regexec(&OrURLs, lin, 4, matches, 0)) {
      if (res->url) {
        for (m = res->url; m->next; m = m->next);
        if ((m->next = (MATCHER *) malloc(sizeof(MATCHER))) == NULL)
          conf_err("URL config: out of memory - aborted");
        m = m->next;
      } else {
        if ((res->url = (MATCHER *) malloc(sizeof(MATCHER))) == NULL)
          conf_err("URL config: out of memory - aborted");
        m = res->url;
      }
      memset(m, 0, sizeof(MATCHER));
      ptr = parse_orurls();
      if (regcomp(&m->pat, ptr,
                  REG_NEWLINE | REG_EXTENDED | (ign_case ? REG_ICASE : 0)))
        conf_err("OrURLs bad pattern - aborted");
      free(ptr);
    } else if (!regexec(&HeadRequire, lin, 4, matches, 0)) {
      if (res->req_head) {
        for (m = res->req_head; m->next; m = m->next);
        if ((m->next = (MATCHER *) malloc(sizeof(MATCHER))) == NULL)
          conf_err("HeadRequire config: out of memory - aborted");
        m = m->next;
      } else {
        if ((res->req_head = (MATCHER *) malloc(sizeof(MATCHER))) == NULL)
          conf_err("HeadRequire config: out of memory - aborted");
        m = res->req_head;
      }
      memset(m, 0, sizeof(MATCHER));
      lin[matches[1].rm_eo] = '\0';
      if (regcomp(&m->pat, lin + matches[1].rm_so,
                  REG_ICASE | REG_NEWLINE | REG_EXTENDED))
        conf_err("HeadRequire bad pattern - aborted");
    } else if (!regexec(&HeadDeny, lin, 4, matches, 0)) {
      if (res->deny_head) {
        for (m = res->deny_head; m->next; m = m->next);
        if ((m->next = (MATCHER *) malloc(sizeof(MATCHER))) == NULL)
          conf_err("HeadDeny config: out of memory - aborted");
        m = m->next;
      } else {
        if ((res->deny_head = (MATCHER *) malloc(sizeof(MATCHER))) == NULL)
          conf_err("HeadDeny config: out of memory - aborted");
        m = res->deny_head;
      }
      memset(m, 0, sizeof(MATCHER));
      lin[matches[1].rm_eo] = '\0';
      if (regcomp(&m->pat, lin + matches[1].rm_so,
                  REG_ICASE | REG_NEWLINE | REG_EXTENDED))
        conf_err("HeadDeny bad pattern - aborted");
    } else if (!regexec(&StrictTransportSecurity, lin, 4, matches, 0)) {
      res->sts = atoi(lin + matches[1].rm_so);
    } else if (!regexec(&Redirect, lin, 4, matches, 0)) {
      if (res->backends) {
        for (be = res->backends; be->next; be = be->next);
        if ((be->next = (BackendConfig *) malloc(sizeof(BackendConfig))) == NULL)
          conf_err("Redirect config: out of memory - aborted");
        be = be->next;
      } else {
        if ((res->backends = (BackendConfig *) malloc(sizeof(BackendConfig))) ==
            NULL)
          conf_err("Redirect config: out of memory - aborted");
        be = res->backends;
      }
      // 1 - Dynamic or not, 2 - Request Redirect #, 3 - Destination URL
      memset(be, 0, sizeof(BackendConfig));
      be->be_type = 302;
      be->redir_req = 0;
      if (matches[1].rm_eo != matches[1].rm_so) {
        if ((lin[matches[1].rm_so] & ~0x20) == 'D') {
          be->redir_req = 2;
          if (!res->url || res->url->next)
            conf_err("Dynamic Redirect must be preceeded by a URL line");
        } else if ((lin[matches[1].rm_so] & ~0x20) == 'A')
          be->redir_req = 1;
      }
      if (matches[2].rm_eo != matches[2].rm_so)
        be->be_type = atoi(lin + matches[2].rm_so);
      be->priority = 1;
      be->alive = 1;
      pthread_mutex_init(&be->mut, NULL);
      lin[matches[3].rm_eo] = '\0';
      if ((be->url = strdup(lin + matches[3].rm_so)) == NULL)
        conf_err("Redirector config: out of memory - aborted");
      /* split the URL into its fields */
      if (regexec(&LOCATION, be->url, 4, matches, 0))
        conf_err("Redirect bad URL - aborted");
      if ((matches[3].rm_eo - matches[3].rm_so) == 1)
        /* the path is a single '/', so remove it */
        be->url[matches[3].rm_so] = '\0';
    } else if (!regexec(&BackEnd, lin, 4, matches, 0)) {
      if (res->backends) {
        for (be = res->backends; be->next; be = be->next);
        be->next = parseBackend(0);
      } else
        res->backends = parseBackend(0);
    } else if (!regexec(&Emergency, lin, 4, matches, 0)) {
      res->emergency = parseBackend(1);
    } else if (!regexec(&BackendCookie, lin, 5, matches, 0)) {
      lin[matches[1].rm_eo] = '\0';
      lin[matches[2].rm_eo] = '\0';
      lin[matches[3].rm_eo] = '\0';
      lin[matches[4].rm_eo] = '\0';
      snprintf(pat, MAXBUF - 1, "Cookie[^:]*:.*[; \t]%s=\"?([^\";]*)\"?",
               lin + matches[1].rm_so);
      if (matches[1].rm_so == matches[1].rm_eo)
        conf_err("Backend cookie must have a name");
      if ((res->becookie = strdup(lin + matches[1].rm_so)) == NULL)
        conf_err("out of memory");
      if (regcomp(&res->becookie_re, pat,
                  REG_ICASE | REG_NEWLINE | REG_EXTENDED))
        conf_err("Backend Cookie pattern failed - aborted");
      if (matches[2].rm_so != matches[2].rm_eo &&
          (res->becdomain = strdup(lin + matches[2].rm_so)) == NULL)
        conf_err("out of memory");
      if (matches[3].rm_so != matches[3].rm_eo &&
          (res->becpath = strdup(lin + matches[3].rm_so)) == NULL)
        conf_err("out of memory");
      res->becage = atoi(lin + matches[4].rm_so);
      if ((lin[matches[4].rm_so] & ~0x20) == 'S')
        res->becage = -1;
      else
        res->becage = atoi(lin + matches[4].rm_so);
#if CACHE_ENABLED
    } else if (!regexec(&Cache, lin, 4, matches, 0)) {
      parseCache(res);
#endif
    } else if (!regexec(&Session, lin, 4, matches, 0)) {
      parseSession(res);
    } else if (!regexec(&DynScale, lin, 4, matches, 0)) {
      res->dynscale = atoi(lin + matches[1].rm_so) == 1;
    } else if (!regexec(&PinnedConnection, lin, 4, matches, 0)) {
      res->pinned_connection = atoi(lin + matches[1].rm_so) == 1;
    } else if (!regexec(&RoutingPolicy, lin, 4, matches, 0)) {
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
    } else if (!regexec(&CompressionAlgorithm, lin, 4, matches, 0)) {
      lin[matches[1].rm_eo] = '\0';
      std::string cp = lin + matches[1].rm_so;
      if (cp == "gzip")
        res->compression_algorithm = cp;
      else if (cp == "deflate")
        res->compression_algorithm = cp;
      else
        conf_err("Unknown compression algorithm");
    } else if (!regexec(&IgnoreCase, lin, 4, matches, 0)) {
      ign_case = atoi(lin + matches[1].rm_so);
    } else if (!regexec(&Disabled, lin, 4, matches, 0)) {
      res->disabled = atoi(lin + matches[1].rm_so) == 1;
    } else if (!regexec(&End, lin, 4, matches, 0)) {
      for (be = res->backends; be; be = be->next) {
        if (!be->disabled) res->tot_pri += be->priority;
        res->abs_pri += be->priority;
      }
      return res;
    } else {
      conf_err("unknown directive");
    }
  }

  conf_err("Service premature EOF");
  return NULL;
}

int Config::verify_OK(int pre_ok, X509_STORE_CTX *ctx) { return 1; }

char *Config::parse_orurls() {
  char lin[MAXBUF];
  char *pattern;
  regex_t comp;
  regmatch_t matches[5];

  pattern = NULL;
  while (conf_fgets(lin, MAXBUF)) {
    if (strlen(lin) > 0 && lin[strlen(lin) - 1] == '\n')
      lin[strlen(lin) - 1] = '\0';
    if (!regexec(&URL, lin, 4, matches, 0)) {
      lin[matches[1].rm_eo] = '\0';
      /* Verify the pattern is valid */
      if (regcomp(&comp, lin + matches[1].rm_so, REG_NEWLINE | REG_EXTENDED))
        conf_err("URL bad pattern - aborted");
      regfree(&comp);
      if (pattern == NULL) {
        if ((pattern = (char *) malloc(strlen(lin + matches[1].rm_so) + 5)) ==
            NULL)
          conf_err("OrURLs config: out of memory - aborted");
        *pattern = 0;
        strcat(pattern, "((");
        strcat(pattern, lin + matches[1].rm_so);
        strcat(pattern, "))");
      } else {
        if ((pattern = (char *) realloc(
            pattern,
            strlen(pattern) + strlen(lin + matches[1].rm_so) + 4)) == NULL)
          conf_err("OrURLs config: out of memory - aborted");
        pattern[strlen(pattern) - 1] = 0;
        strcat(pattern, "|(");
        strcat(pattern, lin + matches[1].rm_so);
        strcat(pattern, "))");
      }
    } else if (!regexec(&End, lin, 4, matches, 0)) {
      if (!pattern) conf_err("No URL directives specified within OrURLs block");
      return pattern;
    } else {
      conf_err("unknown directive");
    }
  }

  conf_err("OrURLs premature EOF");
  return NULL;
}

BackendConfig *Config::parseBackend(const int is_emergency) {
  char lin[MAXBUF];
  regmatch_t matches[5];
  char *cp;
  BackendConfig *res;
  int has_addr, has_port;
  struct hostent *host;
  struct sockaddr_in in;
  struct sockaddr_in6 in6;

  if ((res = (BackendConfig *) malloc(sizeof(BackendConfig))) == NULL)
    conf_err("BackEnd config: out of memory - aborted");
  memset(res, 0, sizeof(BackendConfig));
  res->be_type = 0;
  res->addr.ai_socktype = SOCK_STREAM;
  res->rw_timeout = is_emergency ? 120 : be_to;
  res->conn_to = is_emergency ? 120 : be_connto;
  res->alive = 1;
  memset(&res->addr, 0, sizeof(res->addr));
  res->priority = 5;
  memset(&res->ha_addr, 0, sizeof(res->ha_addr));
  res->url = NULL;
  res->bekey = NULL;
  res->connections;
  res->next = NULL;
  res->ctx = nullptr;
  res->nf_mark = 0;
  has_addr = has_port = 0;
  pthread_mutex_init(&res->mut, NULL);
  while (conf_fgets(lin, MAXBUF)) {
    if (strlen(lin) > 0 && lin[strlen(lin) - 1] == '\n')
      lin[strlen(lin) - 1] = '\0';
    if (!regexec(&Address, lin, 4, matches, 0)) {
      lin[matches[1].rm_eo] = '\0';
      if (get_host(lin + matches[1].rm_so, &res->addr, PF_UNSPEC)) {
        /* if we can't resolve it assume this is a UNIX domain socket */
        res->addr.ai_socktype = SOCK_STREAM;
        res->addr.ai_family = AF_UNIX;
        res->addr.ai_protocol = 0;
        if ((res->addr.ai_addr =
                 (struct sockaddr *) malloc(sizeof(struct sockaddr_un))) == NULL)
          conf_err("out of memory");
        if ((strlen(lin + matches[1].rm_so) + 1) > UNIX_PATH_MAX)
          conf_err("UNIX path name too long");
        res->addr.ai_addrlen = ::strlen(lin + matches[1].rm_so) + 1;
        res->addr.ai_addr->sa_family = AF_UNIX;
        strcpy(res->addr.ai_addr->sa_data, lin + matches[1].rm_so);
        res->addr.ai_addrlen = sizeof(struct sockaddr_un);
      }
      res->address = lin + matches[1].rm_so;
      has_addr = 1;
    } else if (!regexec(&Port, lin, 4, matches, 0)) {
      switch (res->addr.ai_family) {
        case AF_INET:memcpy(&in, res->addr.ai_addr, sizeof(in));
          res->port = atoi(lin + matches[1].rm_so);
          in.sin_port = (in_port_t) htons(atoi(lin + matches[1].rm_so));
          memcpy(res->addr.ai_addr, &in, sizeof(in));
          break;
        case AF_INET6:memcpy(&in6, res->addr.ai_addr, sizeof(in6));
          res->port = atoi(lin + matches[1].rm_so);
          in6.sin6_port = (in_port_t) htons(atoi(lin + matches[1].rm_so));
          memcpy(res->addr.ai_addr, &in6, sizeof(in6));
          break;
        default:conf_err("Port is supported only for INET/INET6 back-ends");
      }
      has_port = 1;
    } else if (!regexec(&BackendKey, lin, 4, matches, 0)) {
      lin[matches[1].rm_eo] = '\0';
      if ((res->bekey = strdup(lin + matches[1].rm_so)) == NULL)
        conf_err("out of memory");
    } else if (!regexec(&SSLConfigFile, lin, 4, matches, 0)) {
      lin[matches[1].rm_eo] = '\0';
      res->ssl_config_file = std::string(lin + matches[1].rm_so);
    } else if (!regexec(&SSLConfigSection, lin, 4, matches, 0)) {
        if (res->ssl_config_file.empty())
          conf_err("SSLConfigSection needed if SSLConfigFile directive is set - aborted");
        lin[matches[1].rm_eo] = '\0';
        res->ssl_config_section = std::string(lin + matches[1].rm_so);
    } else if (!regexec(&Priority, lin, 4, matches, 0)) {
      if (is_emergency)
        conf_err("Priority is not supported for Emergency back-ends");
      res->priority = atoi(lin + matches[1].rm_so);
    } else if (!regexec(&TimeOut, lin, 4, matches, 0)) {
      res->rw_timeout = atoi(lin + matches[1].rm_so);
    }else if (!regexec(&NfMark, lin, 4, matches, 0)) {
      res->nf_mark = atoi(lin + matches[1].rm_so);
    } else if (!regexec(&ConnTO, lin, 4, matches, 0)) {
      res->conn_to = atoi(lin + matches[1].rm_so);
    } else if (!regexec(&HAport, lin, 4, matches, 0)) {
      if (is_emergency)
        conf_err("HAport is not supported for Emergency back-ends");
      res->ha_addr = res->addr;
      if ((res->ha_addr.ai_addr =
               (struct sockaddr *) malloc(res->addr.ai_addrlen)) == NULL)
        conf_err("out of memory");
      memcpy(res->ha_addr.ai_addr, res->addr.ai_addr, res->addr.ai_addrlen);
      switch (res->addr.ai_family) {
        case AF_INET:memcpy(&in, res->ha_addr.ai_addr, sizeof(in));
          in.sin_port = (in_port_t) htons(atoi(lin + matches[1].rm_so));
          memcpy(res->ha_addr.ai_addr, &in, sizeof(in));
          break;
        case AF_INET6:memcpy(&in6, res->addr.ai_addr, sizeof(in6));
          in6.sin6_port = (in_port_t) htons(atoi(lin + matches[1].rm_so));
          memcpy(res->addr.ai_addr, &in6, sizeof(in6));
          break;
        default:conf_err("HAport is supported only for INET/INET6 back-ends");
      }
    } else if (!regexec(&HAportAddr, lin, 4, matches, 0)) {
      if (is_emergency)
        conf_err("HAportAddr is not supported for Emergency back-ends");
      lin[matches[1].rm_eo] = '\0';
      if (get_host(lin + matches[1].rm_so, &res->ha_addr, PF_UNSPEC)) {
        /* if we can't resolve it assume this is a UNIX domain socket */
        res->addr.ai_socktype = SOCK_STREAM;
        res->ha_addr.ai_family = AF_UNIX;
        res->ha_addr.ai_protocol = 0;
        if ((res->ha_addr.ai_addr =
                 (struct sockaddr *) strdup(lin + matches[1].rm_so)) == NULL)
          conf_err("out of memory");
        res->addr.ai_addrlen = strlen(lin + matches[1].rm_so) + 1;
      } else
        switch (res->ha_addr.ai_family) {
          case AF_INET:memcpy(&in, res->ha_addr.ai_addr, sizeof(in));
            in.sin_port = (in_port_t) htons(atoi(lin + matches[2].rm_so));
            memcpy(res->ha_addr.ai_addr, &in, sizeof(in));
            break;
          case AF_INET6:memcpy(&in6, res->ha_addr.ai_addr, sizeof(in6));
            in6.sin6_port = (in_port_t) htons(atoi(lin + matches[2].rm_so));
            memcpy(res->ha_addr.ai_addr, &in6, sizeof(in6));
            break;
          default:conf_err("Unknown HA address type");
        }
    } else if (!regexec(&HTTPS, lin, 4, matches, 0)) {
      if ((res->ctx = SSL_CTX_new(SSLv23_client_method())) == NULL)
        conf_err("SSL_CTX_new failed - aborted");
      SSL_CTX_set_app_data(res->ctx, res);
      SSL_CTX_set_verify(res->ctx, SSL_VERIFY_NONE, NULL);
      SSL_CTX_set_mode(res->ctx, SSL_MODE_RELEASE_BUFFERS);
#ifdef SSL_MODE_SEND_FALLBACK_SCSV
      SSL_CTX_set_mode(res->ctx, SSL_MODE_SEND_FALLBACK_SCSV);
#endif
      SSL_CTX_set_options(res->ctx, SSL_OP_ALL);
#ifdef SSL_OP_NO_COMPRESSION
      SSL_CTX_set_options(res->ctx, SSL_OP_NO_COMPRESSION);
#endif
      SSL_CTX_clear_options(res->ctx, SSL_OP_ALLOW_UNSAFE_LEGACY_RENEGOTIATION);
      SSL_CTX_clear_options(res->ctx, SSL_OP_LEGACY_SERVER_CONNECT);
      sprintf(lin, "%d-Zhttp-%ld", getpid(), random());
      SSL_CTX_set_session_id_context(res->ctx, (unsigned char *) lin,
                                     strlen(lin));
      SSL_CTX_set_tmp_rsa_callback(res->ctx, RSA_tmp_callback);
      if (NULL == DHCustom_params)
        SSL_CTX_set_tmp_dh_callback(res->ctx, DH_tmp_callback);
      else
        SSL_CTX_set_tmp_dh(res->ctx, DHCustom_params);

#if OPENSSL_VERSION_NUMBER >= 0x0090800fL
#ifndef OPENSSL_NO_ECDH
      /* This generates a EC_KEY structure with no key, but a group defined */
      EC_KEY *ecdh;
      if ((ecdh = EC_KEY_new_by_curve_name(EC_nid)) == NULL)
        conf_err("Unable to generate temp ECDH key");
      SSL_CTX_set_tmp_ecdh(res->ctx, ecdh);
      SSL_CTX_set_options(res->ctx, SSL_OP_SINGLE_ECDH_USE);
      EC_KEY_free(ecdh);
#endif
#endif
    } else if (!regexec(&Cert, lin, 4, matches, 0)) {
      if (res->ctx == NULL)
        conf_err("BackEnd Cert can only be used after HTTPS - aborted");
      lin[matches[1].rm_eo] = '\0';
      if (SSL_CTX_use_certificate_chain_file(res->ctx,
                                             lin + matches[1].rm_so) != 1)
        conf_err("SSL_CTX_use_certificate_chain_file failed - aborted");
      if (SSL_CTX_use_PrivateKey_file(res->ctx, lin + matches[1].rm_so,
                                      SSL_FILETYPE_PEM) != 1)
        conf_err("SSL_CTX_use_PrivateKey_file failed - aborted");
      if (SSL_CTX_check_private_key(res->ctx) != 1)
        conf_err("SSL_CTX_check_private_key failed - aborted");
    } else if (!regexec(&Ciphers, lin, 4, matches, 0)) {
      if (res->ctx == NULL)
        conf_err("BackEnd Ciphers can only be used after HTTPS - aborted");
      lin[matches[1].rm_eo] = '\0';
      SSL_CTX_set_cipher_list(res->ctx, lin + matches[1].rm_so);
    } else if (!regexec(&DisableProto, lin, 4, matches, 0)) {
      if (res->ctx == NULL)
        conf_err("BackEnd Disable can only be used after HTTPS - aborted");
      lin[matches[1].rm_eo] = '\0';
      if (strcasecmp(lin + matches[1].rm_so, "SSLv2") == 0)
        SSL_CTX_set_options(res->ctx, SSL_OP_NO_SSLv2);
      else if (strcasecmp(lin + matches[1].rm_so, "SSLv3") == 0)
        SSL_CTX_set_options(res->ctx, SSL_OP_NO_SSLv2 | SSL_OP_NO_SSLv3);
#ifdef SSL_OP_NO_TLSv1
      else if (strcasecmp(lin + matches[1].rm_so, "TLSv1") == 0)
        SSL_CTX_set_options(
            res->ctx, SSL_OP_NO_SSLv2 | SSL_OP_NO_SSLv3 | SSL_OP_NO_TLSv1);
#endif
#ifdef SSL_OP_NO_TLSv1_1
      else if (strcasecmp(lin + matches[1].rm_so, "TLSv1_1") == 0)
        SSL_CTX_set_options(res->ctx, SSL_OP_NO_SSLv2 | SSL_OP_NO_SSLv3 |
            SSL_OP_NO_TLSv1 | SSL_OP_NO_TLSv1_1);
#endif
#ifdef SSL_OP_NO_TLSv1_2
      else if (strcasecmp(lin + matches[1].rm_so, "TLSv1_2") == 0)
        SSL_CTX_set_options(res->ctx, SSL_OP_NO_SSLv2 | SSL_OP_NO_SSLv3 |
            SSL_OP_NO_TLSv1 | SSL_OP_NO_TLSv1_1 |
            SSL_OP_NO_TLSv1_2);
#endif
    } else if (!regexec(&Disabled, lin, 4, matches, 0)) {
      res->disabled = atoi(lin + matches[1].rm_so);
    } else if (!regexec(&End, lin, 4, matches, 0)) {
      if (!has_addr) conf_err("BackEnd missing Address - aborted");
      if ((res->addr.ai_family == AF_INET || res->addr.ai_family == AF_INET6) &&
          !has_port)
        conf_err("BackEnd missing Port - aborted");
      if (!res->bekey) {
        if (res->addr.ai_family == AF_INET)
          snprintf(
              lin, MAXBUF - 1, "4-%08x-%x",
              htonl(
                  ((struct sockaddr_in *) (res->addr.ai_addr))->sin_addr.s_addr),
              htons(((struct sockaddr_in *) (res->addr.ai_addr))->sin_port));
        else if (res->addr.ai_family == AF_INET6) {
          cp = (char *) &(
              ((struct sockaddr_in6 *) (res->addr.ai_addr))->sin6_addr);
          snprintf(
              lin, MAXBUF - 1,
              "6-%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x%"
              "02x%02x-%x",
              cp[0], cp[1], cp[2], cp[3], cp[4], cp[5], cp[6], cp[7], cp[8],
              cp[9], cp[10], cp[11], cp[12], cp[13], cp[14], cp[15],
              htons(((struct sockaddr_in6 *) (res->addr.ai_addr))->sin6_port));
        } else
          conf_err("cannot autogenerate backendkey, please specify one");

        if ((res->bekey = strdup(lin)) == NULL)
          conf_err("out of memory autogenerating backendkey");
      }
      return res;
    } else {
      conf_err("unknown directive");
    }
  }

  conf_err("BackEnd premature EOF");
  return NULL;
}

#if CACHE_ENABLED
void Config::parseCache(ServiceConfig *const svc) {
  char lin[MAXBUF], *cp;
  if( cache_s == 0 || cache_thr == 0)
    conf_err("There is no CacheRamSize nor CacheThreshold configured, exiting");
  regmatch_t matches[5];
  svc->cache_size = cache_s;
  svc->cache_threshold = cache_thr;
  svc->f_name = name;
  if ( cache_ram_path.size() != 0 ){
    svc->cache_ram_path = cache_ram_path;
  }
  if ( cache_disk_path.size() != 0 ){
    svc->cache_disk_path = cache_disk_path;
  }
  while (conf_fgets(lin, MAXBUF)) {
    if (strlen(lin) > 0 && lin[strlen(lin) - 1] == '\n')
      lin[strlen(lin) - 1] = '\0';
    if (!regexec(&MaxSize,lin,2,matches,0))
      svc->cache_max_size = strtoul(lin + matches[1].rm_so, nullptr, 0);
    if (!regexec(&CacheContent, lin, 4, matches, 0)) {
      lin[matches[1].rm_eo] = '\0';
      cp = lin + matches[1].rm_so;
      if (regcomp(&svc->cache_content, cp,
                  REG_ICASE | REG_NEWLINE | REG_EXTENDED))
        conf_err("Cache content pattern failed, aborting");
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
void Config::parseSession(ServiceConfig *const svc) {
  char lin[MAXBUF], *cp, *parm;
  regmatch_t matches[5];
  parm = NULL;
  while (conf_fgets(lin, MAXBUF)) {
    if (strlen(lin) > 0 && lin[strlen(lin) - 1] == '\n')
      lin[strlen(lin) - 1] = '\0';
    if (!regexec(&Type, lin, 4, matches, 0)) {
      if (svc->sess_type != SESS_NONE)
        conf_err("Multiple Session types in one Service - aborted");
      lin[matches[1].rm_eo] = '\0';
      cp = lin + matches[1].rm_so;
      if (!strcasecmp(cp, "IP"))
        svc->sess_type = SESS_IP;
      else if (!strcasecmp(cp, "COOKIE"))
        svc->sess_type = SESS_COOKIE;
      else if (!strcasecmp(cp, "URL"))
        svc->sess_type = SESS_URL;
      else if (!strcasecmp(cp, "PARM"))
        svc->sess_type = SESS_PARM;
      else if (!strcasecmp(cp, "BASIC"))
        svc->sess_type = SESS_BASIC;
      else if (!strcasecmp(cp, "HEADER"))
        svc->sess_type = SESS_HEADER;
      else
        conf_err("Unknown Session type");
    } else if (!regexec(&TTL, lin, 4, matches, 0)) {
      svc->sess_ttl = atoi(lin + matches[1].rm_so);
    } else if (!regexec(&ID, lin, 4, matches, 0)) {
      svc->sess_id = lin + matches[1].rm_so;
      svc->sess_id = svc->sess_id.substr(0 , static_cast<size_t>(matches[1].rm_eo - matches[1].rm_so));
      if (svc->sess_type != SESS_COOKIE && svc->sess_type != SESS_URL &&
          svc->sess_type != SESS_HEADER)
        conf_err("no ID permitted unless COOKIE/URL/HEADER Session - aborted");
      lin[matches[1].rm_eo] = '\0';
      if ((parm = strdup(lin + matches[1].rm_so)) == NULL)
        conf_err("ID config: out of memory - aborted");
    } else if (!regexec(&End, lin, 4, matches, 0)) {
      if (svc->sess_type == SESS_NONE)
        conf_err("Session type not defined - aborted");
      if (svc->sess_ttl == 0) conf_err("Session TTL not defined - aborted");
      if ((svc->sess_type == SESS_COOKIE || svc->sess_type == SESS_URL ||
          svc->sess_type == SESS_HEADER) &&
          parm == NULL)
        conf_err("Session ID not defined - aborted");
      if (svc->sess_type == SESS_COOKIE) {
        snprintf(lin, MAXBUF - 1, "Cookie[^:]*:.*[; \t]%s=", parm);
        if (regcomp(&svc->sess_start, lin,
                    REG_ICASE | REG_NEWLINE | REG_EXTENDED))
          conf_err("COOKIE pattern failed - aborted");
        if (regcomp(&svc->sess_pat, "([^;]*)",
                    REG_ICASE | REG_NEWLINE | REG_EXTENDED))
          conf_err("COOKIE pattern failed - aborted");
      } else if (svc->sess_type == SESS_URL) {
        snprintf(lin, MAXBUF - 1, "[?&]%s=", parm);
        if (regcomp(&svc->sess_start, lin,
                    REG_ICASE | REG_NEWLINE | REG_EXTENDED))
          conf_err("URL pattern failed - aborted");
        if (regcomp(&svc->sess_pat, "([^&;#]*)",
                    REG_ICASE | REG_NEWLINE | REG_EXTENDED))
          conf_err("URL pattern failed - aborted");
      } else if (svc->sess_type == SESS_PARM) {
        if (regcomp(&svc->sess_start, ";",
                    REG_ICASE | REG_NEWLINE | REG_EXTENDED))
          conf_err("PARM pattern failed - aborted");
        if (regcomp(&svc->sess_pat, "([^?]*)",
                    REG_ICASE | REG_NEWLINE | REG_EXTENDED))
          conf_err("PARM pattern failed - aborted");
      } else if (svc->sess_type == SESS_BASIC) {
        if (regcomp(&svc->sess_start, "Authorization:[ \t]*Basic[ \t]*",
                    REG_ICASE | REG_NEWLINE | REG_EXTENDED))
          conf_err("BASIC pattern failed - aborted");
        if (regcomp(&svc->sess_pat, "([^ \t]*)",
                    REG_ICASE | REG_NEWLINE | REG_EXTENDED))
          conf_err("BASIC pattern failed - aborted");
      } else if (svc->sess_type == SESS_HEADER) {
        snprintf(lin, MAXBUF - 1, "%s:[ \t]*", parm);
        if (regcomp(&svc->sess_start, lin,
                    REG_ICASE | REG_NEWLINE | REG_EXTENDED))
          conf_err("HEADER pattern failed - aborted");
        if (regcomp(&svc->sess_pat, "([^ \t]*)",
                    REG_ICASE | REG_NEWLINE | REG_EXTENDED))
          conf_err("HEADER pattern failed - aborted");
      }
      if (parm != NULL) free(parm);
      return;
    } else {
      conf_err("unknown directive");
    }
  }

  conf_err("Session premature EOF");
  return;
}

bool Config::compile_regex() {
  if (regcomp(&Empty, "^[ \t]*$", REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&Comment, "^[ \t]*#.*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&User, "^[ \t]*User[ \t]+\"(.+)\"[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&Group, "^[ \t]*Group[ \t]+\"(.+)\"[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&Name, "^[ \t]*Name[ \t]+(.+)[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&RootJail, "^[ \t]*RootJail[ \t]+\"(.+)\"[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&Daemon, "^[ \t]*Daemon[ \t]+([01])[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&Threads, "^[ \t]*Threads[ \t]+([1-9][0-9]*)[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&ThreadModel, "^[ \t]*ThreadModel[ \t]+(pool|dynamic)[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&LogFacility, "^[ \t]*LogFacility[ \t]+([a-z0-9-]+)[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&LogLevel, "^[ \t]*LogLevel[ \t]+([0-9])[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&Grace, "^[ \t]*Grace[ \t]+([0-9]+)[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&Alive, "^[ \t]*Alive[ \t]+([1-9][0-9]*)[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&SSLEngine, "^[ \t]*SSLEngine[ \t]+\"(.+)\"[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&Control, "^[ \t]*Control[ \t]+\"(.+)\"[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&ControlIP, "^[ \t]*ControlIP[ \t]+([^ \t]+)[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&ControlPort, "^[ \t]*ControlPort[ \t]+([1-9][0-9]*)[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&ControlUser, "^[ \t]*ControlUser[ \t]+\"(.+)\"[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&ControlGroup, "^[ \t]*ControlGroup[ \t]+\"(.+)\"[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&ControlMode, "^[ \t]*ControlMode[ \t]+([0-7]+)[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&ListenHTTP, "^[ \t]*ListenHTTP[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&ListenHTTPS, "^[ \t]*ListenHTTPS[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&End, "^[ \t]*End[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&BackendKey, "^[ \t]*Key[ \t]+\"(.+)\"[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&Address, "^[ \t]*Address[ \t]+([^ \t]+)[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&Port, "^[ \t]*Port[ \t]+([1-9][0-9]*)[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&Cert, "^[ \t]*Cert[ \t]+\"(.+)\"[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&CertDir, "^[ \t]*CertDir[ \t]+\"(.+)\"[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&xHTTP, "^[ \t]*xHTTP[ \t]+([01234])[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&Client, "^[ \t]*Client[ \t]+([1-9][0-9]*)[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&CheckURL, "^[ \t]*CheckURL[ \t]+\"(.+)\"[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&Err414, "^[ \t]*Err414[ \t]+\"(.+)\"[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&Err500, "^[ \t]*Err500[ \t]+\"(.+)\"[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&Err501, "^[ \t]*Err501[ \t]+\"(.+)\"[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&Err503, "^[ \t]*Err503[ \t]+\"(.+)\"[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&SSLConfigFile, "^[ \t]*SSLConfigFile[ \t]+\"(.+)\"[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&SSLConfigSection, "^[ \t]*SSLConfigSection[ \t]+([^ \t]+)[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&ErrNoSsl, "^[ \t]*ErrNoSsl[ \t]+\"(.+)\"[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&NoSslRedirect,
              "^[ \t]*NoSslRedirect[ \t]+(30[127][ \t]+)?\"(.+)\"[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&MaxRequest, "^[ \t]*MaxRequest[ \t]+([1-9][0-9]*)[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&HeadRemove, "^[ \t]*HeadRemove[ \t]+\"(.+)\"[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&RewriteLocation, "^[ \t]*RewriteLocation[ \t]+([012])[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&RewriteDestination,
              "^[ \t]*RewriteDestination[ \t]+([01])[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&RewriteHost,
              "^[ \t]*RewriteHost[ \t]+([01])[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&Service, "^[ \t]*Service[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&ServiceName, "^[ \t]*Service[ \t]+\"(.+)\"[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&URL, "^[ \t]*URL[ \t]+\"(.+)\"[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&OrURLs, "^[ \t]*OrURLS[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&BackendCookie,
              "^[ \t]*BackendCookie[ \t]+\"(.+)\"[ \t]+\"(.*)\"[ "
              "\t]+\"(.*)\"[ \t]+([0-9]+|Session)[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&HeadRequire, "^[ \t]*HeadRequire[ \t]+\"(.+)\"[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&HeadDeny, "^[ \t]*HeadDeny[ \t]+\"(.+)\"[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&StrictTransportSecurity,
              "^[ \t]*StrictTransportSecurity[ \t]+([0-9]+)[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&BackEnd, "^[ \t]*BackEnd[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&Emergency, "^[ \t]*Emergency[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&Priority, "^[ \t]*Priority[ \t]+([1-9])[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&TimeOut, "^[ \t]*TimeOut[ \t]+([1-9][0-9]*)[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&HAport, "^[ \t]*HAport[ \t]+([1-9][0-9]*)[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&HAportAddr,
              "^[ \t]*HAport[ \t]+([^ \t]+)[ \t]+([1-9][0-9]*)[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&Redirect,
              "^[ \t]*Redirect(Append|Dynamic|)[ \t]+(30[127][ "
              "\t]+|)\"(.+)\"[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&Session, "^[ \t]*Session[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&Type, "^[ \t]*Type[ \t]+([^ \t]+)[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&TTL, "^[ \t]*TTL[ \t]+([1-9-][0-9]*)[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&ID, "^[ \t]*ID[ \t]+\"(.+)\"[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&DynScale, "^[ \t]*DynScale[ \t]+([01])[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&CompressionAlgorithm, "^[ \t]*CompressionAlgorithm[ \t]+([^ \t]+)[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&PinnedConnection, "^[ \t]*PinnedConnection[ \t]+([01])[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&RoutingPolicy, "^[ \t]*RoutingPolicy[ \t]+([^ \t]+)[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&ClientCert, "^[ \t]*ClientCert[ \t]+([0-3])[ \t]+([1-9])[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&AddHeader, "^[ \t]*AddHeader[ \t]+\"(.+)\"[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&SSLAllowClientRenegotiation,
              "^[ \t]*SSLAllowClientRenegotiation[ \t]+([012])[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&DisableProto,
              "^[ \t]*Disable[ \t]+(SSLv2|SSLv3|TLSv1|TLSv1_1|TLSv1_2)[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&SSLHonorCipherOrder,
              "^[ \t]*SSLHonorCipherOrder[ \t]+([01])[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&Ciphers, "^[ \t]*Ciphers[ \t]+\"(.+)\"[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&CAlist, "^[ \t]*CAlist[ \t]+\"(.+)\"[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&VerifyList, "^[ \t]*VerifyList[ \t]+\"(.+)\"[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&CRLlist, "^[ \t]*CRLlist[ \t]+\"(.+)\"[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&NoHTTPS11, "^[ \t]*NoHTTPS11[ \t]+([0-2])[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&ForceHTTP10, "^[ \t]*ForceHTTP10[ \t]+\"(.+)\"[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&SSLUncleanShutdown,
              "^[ \t]*SSLUncleanShutdown[ \t]+\"(.+)\"[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&Include, "^[ \t]*Include[ \t]+\"(.+)\"[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&IncludeDir, "^[ \t]*IncludeDir[ \t]+\"(.+)\"[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&ConnTO, "^[ \t]*ConnTO[ \t]+([1-9][0-9]*)[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&IgnoreCase, "^[ \t]*IgnoreCase[ \t]+([01])[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
      regcomp(&Ignore100continue, "^[ \t]*Ignore100continue[ \t]+([01])[ \t]*$",
              REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
          regcomp(&HTTPS, "^[ \t]*HTTPS[ \t]*$",
                  REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
          regcomp(&Disabled, "^[ \t]*Disabled[ \t]+([01])[ \t]*$",
                  REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
          regcomp(&DHParams, "^[ \t]*DHParams[ \t]+\"(.+)\"[ \t]*$",
                  REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
          regcomp(&CNName, ".*[Cc][Nn]=([-*.A-Za-z0-9]+).*$",
                  REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
          regcomp(&Anonymise, "^[ \t]*Anonymise[ \t]*$",
                  REG_ICASE | REG_NEWLINE | REG_EXTENDED)
        #if CACHE_ENABLED
          ||    regcomp(&Cache, "^[ \t]*Cache[ \t]*$",
                        REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
          regcomp(&CacheContent, "^[ \t]*Content[ \t]+\"(.+)\"[ \t]*$",
                  REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
          regcomp(&CacheTO, "^[ \t]*CacheTO[ \t]+([1-9][0-9]*)[ \t]*$",
                  REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
          regcomp(&CacheRamSize, "^[ \t]*CacheRamSize[ \t]+([1-9][0-9]*)([gmkbGMKB]*)[ \t]*$",
                  REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
          regcomp(&CacheThreshold, "^[ \t]*CacheThreshold[ \t]+([1-9][0-9]*)[ \t]*$",
                  REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
          regcomp(&MaxSize, "^[ \t]*MaxSize[ \t]+([1-9][0-9]*)[ \t]*$",
                  REG_ICASE | REG_NEWLINE | REG_EXTENDED) ||
          regcomp(&CacheRamPath, "^[ \t]*CacheRamPath[ \t]+\"([a-zA-Z\\/\\._]*)\"[ \t]*$",
                  REG_ICASE | REG_NEWLINE | REG_EXTENDED)   ||
          regcomp(&CacheDiskPath, "^[ \t]*CacheDiskPath[ \t]+\"([a-zA-Z\\/\\._]*)\"[ \t]*$",
                  REG_ICASE | REG_NEWLINE | REG_EXTENDED)

        #endif
#if OPENSSL_VERSION_NUMBER >= 0x0090800fL
#ifndef OPENSSL_NO_ECDH
      || regcomp(&ECDHCurve, "^[ \t]*ECDHCurve[ \t]+\"(.+)\"[ \t]*$",
                 REG_ICASE | REG_NEWLINE | REG_EXTENDED)
#endif
#endif

      ) {
    return false;
  }

  /* prepare regular expressions */
     if(regcomp(&HEADER, "^([a-z0-9!#$%&'*+.^_`|~-]+):[ \t]*(.*)[ \t]*$", REG_ICASE | REG_NEWLINE | REG_EXTENDED)
     //|| regcomp(&CONN_UPGRD, "(^|[ \t,])upgrade([ \t,]|$)", REG_ICASE | REG_NEWLINE | REG_EXTENDED)
     || regcomp(&CHUNK_HEAD, "^([0-9a-f]+).*$", REG_ICASE | REG_NEWLINE | REG_EXTENDED)
     || regcomp(&RESP_SKIP, "^HTTP/1.1 100.*$", REG_ICASE | REG_NEWLINE | REG_EXTENDED)
     || regcomp(&RESP_IGN, "^HTTP/1.[01] (10[1-9]|1[1-9][0-9]|204|30[456]).*$", REG_ICASE | REG_NEWLINE | REG_EXTENDED)
     || regcomp(&LOCATION, "(http|https)://([^/]+)(.*)", REG_ICASE | REG_NEWLINE | REG_EXTENDED)
     || regcomp(&AUTHORIZATION, "Authorization:[ \t]*Basic[ \t]*\"?([^ \t]*)\"?[ \t]*", REG_ICASE | REG_NEWLINE | REG_EXTENDED)
     || regcomp(&NfMark, "^[ \t]*NfMark[ \t]+([1-9][0-9]*)[ \t]*$",REG_ICASE | REG_NEWLINE | REG_EXTENDED)
         ) {
         logmsg(LOG_ERR, "bad essential Regex - aborted");
         return false;
     }
  return true;
}

void Config::clean_regex() {
  regfree(&Empty);
  regfree(&Comment);
  regfree(&User);
  regfree(&Group);
  regfree(&Name);
  regfree(&RootJail);
  regfree(&Daemon);
  regfree(&Threads);
  regfree(&ThreadModel);
  regfree(&LogFacility);
  regfree(&LogLevel);
  regfree(&Grace);
  regfree(&Alive);
  regfree(&SSLEngine);
  regfree(&Control);
  regfree(&ControlIP);
  regfree(&ControlPort);
  regfree(&ControlUser);
  regfree(&ControlGroup);
  regfree(&ControlMode);
  regfree(&ListenHTTP);
  regfree(&ListenHTTPS);
  regfree(&End);
  regfree(&BackendKey);
  regfree(&Address);
  regfree(&Port);
  regfree(&Cert);
  regfree(&CertDir);
  regfree(&xHTTP);
  regfree(&Client);
  regfree(&CheckURL);
  regfree(&Err414);
  regfree(&Err500);
  regfree(&Err501);
  regfree(&Err503);
  regfree(&SSLConfigFile);
  regfree(&SSLConfigSection);
  regfree(&ErrNoSsl);
  regfree(&NoSslRedirect);
  regfree(&MaxRequest);
  regfree(&HeadRemove);
  regfree(&RewriteLocation);
  regfree(&RewriteDestination);
  regfree(&RewriteHost);
  regfree(&Service);
  regfree(&ServiceName);
  regfree(&URL);
  regfree(&OrURLs);
  regfree(&BackendCookie);
  regfree(&HeadRequire);
  regfree(&HeadDeny);
  regfree(&StrictTransportSecurity);
  regfree(&BackEnd);
  regfree(&Emergency);
  regfree(&Priority);
  regfree(&TimeOut);
  regfree(&HAport);
  regfree(&HAportAddr);
  regfree(&Redirect);
  regfree(&Session);
  regfree(&Type);
  regfree(&TTL);
  regfree(&ID);
  regfree(&DynScale);
  regfree(&PinnedConnection);
  regfree(&RoutingPolicy);
  regfree(&CompressionAlgorithm);
  regfree(&ClientCert);
  regfree(&AddHeader);
  regfree(&SSLAllowClientRenegotiation);
  regfree(&DisableProto);
  regfree(&SSLHonorCipherOrder);
  regfree(&Ciphers);
  regfree(&CAlist);
  regfree(&VerifyList);
  regfree(&CRLlist);
  regfree(&NoHTTPS11);
  regfree(&ForceHTTP10);
  regfree(&SSLUncleanShutdown);
  regfree(&Include);
  regfree(&IncludeDir);
  regfree(&ConnTO);
  regfree(&IgnoreCase);
  regfree(&Ignore100continue);
  regfree(&HTTPS);
  regfree(&Disabled);
  regfree(&CNName);
  regfree(&Anonymise);
#if CACHE_ENABLED
  regfree(&Cache);
  regfree(&CacheContent);
  regfree(&CacheTO);
  regfree(&CacheRamSize);
  regfree(&CacheThreshold);
  regfree(&MaxSize);
  regfree(&CacheDiskPath);
  regfree(&CacheRamPath);
#endif
#if OPENSSL_VERSION_NUMBER >= 0x0090800fL
#ifndef OPENSSL_NO_ECDH
  regfree(&ECDHCurve);
#endif
#endif
  regfree(&DHParams);
  regfree(&NfMark);
  if (DHCustom_params) DH_free(DHCustom_params);
}

int Config::conf_init(const char *name) {
  if ((f_name[0] = strdup(name)) == NULL) {
    Debug::logmsg(LOG_ERR, "open %s: out of memory", name);
    exit(1);
  }
  if ((f_in[0] = fopen(name, "rt")) == NULL) {
    Debug::logmsg(LOG_ERR, "can't open open %s", name);
    exit(1);
  }
  n_lin[0] = 0;
  cur_fin = 0;
  return 0;
}

void Config::conf_err(const char *msg) {
  Debug::logmsg(LOG_ERR, "%s line %d: %s", f_name[cur_fin], n_lin[cur_fin],
                msg);
  exit(1);
}

char *Config::conf_fgets(char *buf, const int max) {
  int i;
  regmatch_t matches[5];
  for (;;) {
    if (fgets(buf, max, f_in[cur_fin]) == NULL) {
      fclose(f_in[cur_fin]);
      free(f_name[cur_fin]);
      if (cur_fin > 0) {
        cur_fin--;
        continue;
      } else
        return NULL;
    }
    n_lin[cur_fin]++;
    for (i = 0; i < max; i++)
      if (buf[i] == '\n' || buf[i] == '\r') {
        buf[i] = '\0';
        break;
      }
    if (!regexec(&Empty, buf, 4, matches, 0) ||
        !regexec(&Comment, buf, 4, matches, 0))
      /* comment or empty line */
      continue;
    if (!regexec(&Include, buf, 4, matches, 0)) {
      buf[matches[1].rm_eo] = '\0';
      if (cur_fin == (MAX_FIN - 1)) conf_err("Include nesting too deep");
      cur_fin++;
      if ((f_name[cur_fin] = strdup(&buf[matches[1].rm_so])) == NULL)
        conf_err("Include out of memory");
      if ((f_in[cur_fin] = fopen(&buf[matches[1].rm_so], "rt")) == NULL)
        conf_err("can't open included file");
      n_lin[cur_fin] = 0;
      continue;
    }
    if (!regexec(&IncludeDir, buf, 4, matches, 0)) {
      buf[matches[1].rm_eo] = '\0';
      include_dir(buf + matches[1].rm_so);
      continue;
    }
    return buf;
  }
}

void Config::include_dir(const char *conf_path) {
  DIR *dp;
  struct dirent *de;

  char buf[512];
  char *files[200], *cp;
  int filecnt = 0;
  int idx, use;

  Debug::logmsg(LOG_DEBUG, "Including Dir %s", conf_path);

  if ((dp = opendir(conf_path)) == NULL) {
    conf_err("can't open IncludeDir directory");
    exit(1);
  }

  while ((de = readdir(dp)) != NULL) {
    if (de->d_name[0] == '.') continue;
    if ((strlen(de->d_name) >= 5 &&
        !strncmp(de->d_name + strlen(de->d_name) - 4, ".cfg", 4)) ||
        (strlen(de->d_name) >= 6 &&
            !strncmp(de->d_name + strlen(de->d_name) - 5, ".conf", 5))) {
      snprintf(buf, sizeof(buf), "%s%s%s", conf_path,
               (conf_path[strlen(conf_path) - 1] == '/') ? "" : "/",
               de->d_name);
      buf[sizeof(buf) - 1] = 0;
      if (filecnt == sizeof(files) / sizeof(*files)) {
        conf_err("Max config files per directory reached");
      }
      if ((files[filecnt++] = strdup(buf)) == NULL) {
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
      if (strcmp(files[use], files[idx]) < 0) use = idx;

    Debug::logmsg(LOG_DEBUG, " I==> %s", files[use]);

    // Copied from Include logic
    if (cur_fin == (MAX_FIN - 1)) conf_err("Include nesting too deep");
    cur_fin++;
    f_name[cur_fin] = files[use];
    if ((f_in[cur_fin] = fopen(files[use], "rt")) == NULL) {
      Debug::logmsg(LOG_ERR, "%s line %d: Can't open included file %s",
                    f_name[cur_fin], n_lin[cur_fin], files[use]);
      exit(1);
    }
    n_lin[cur_fin] = 0;
    files[use] = files[--filecnt];
  }

  closedir(dp);
}
bool Config::exportConfigToJsonFile(std::string save_path) {

  return false;
}

