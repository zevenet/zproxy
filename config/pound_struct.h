#pragma once

#include <netdb.h>
#include <openssl/ssl.h>

//#ifndef _REGEX_H
#include <pcreposix.h>
//#endif
#include <sys/socket.h>
#include <string>
typedef enum {
  RENEG_INIT = 0,
  RENEG_REJECT,
  RENEG_ALLOW,
  RENEG_ABORT
} RENEG_STATE;

/* maximal session key size */
#define KEY_SIZE 127

/* matcher chain */
typedef struct _matcher {
  regex_t pat; /* pattern to match the request/header against */
  struct _matcher *next;
} MATCHER;

/* back-end types */
typedef enum {
  SESS_NONE,
  SESS_IP,
  SESS_COOKIE,
  SESS_URL,
  SESS_PARM,
  SESS_HEADER,
  SESS_BASIC
} SESS_TYPE;

/* back-end definition */
class BackendConfig {
 public:
  std::string address;
  int port;
  int be_type; /* 0 if real back-end, otherwise code (301, 302/default, 307) */
  struct addrinfo addr;    /* IPv4/6 address */
  int priority;            /* priority */
  int to;                  /* read/write time-out */
  int conn_to;             /* connection time-out */
  struct addrinfo ha_addr; /* HA address/port */
  char *url;               /* for redirectors */
  int redir_req; /* 0 - redirect is absolute, 1 - the redirect should include
                    the request path, or 2 if it should use perl dynamic
                    replacement */
  char *bekey;   /* Backend Key for Cookie */
  SSL_CTX *ctx;  /* CTX for SSL connections */
  pthread_mutex_t mut; /* mutex for this back-end */
  int n_requests;      /* number of requests seen */
  double t_requests;   /* time to answer these requests */
  double t_average;    /* average time to answer requests */
  int alive;           /* false if the back-end is dead */
  int resurrect;       /* this back-end is to be resurrected */
  int disabled;        /* true if the back-end is disabled */
  int connections;
  BackendConfig *next = nullptr;
  int key_id;
};

typedef struct _tn {
  int listener;
  int service;
  char *key;
  void *content;
  time_t last_acc;
} TABNODE;

class ServiceConfig {
 public:
  int key_id;
  int listener_key_id;
  char name[KEY_SIZE + 1]; /* symbolic name */
  MATCHER *url,            /* request matcher */
      *req_head,           /* required headers */
      *deny_head;          /* forbidden headers */
  BackendConfig *backends;
  BackendConfig *emergency;
  int abs_pri;         /* abs total priority for all back-ends */
  int tot_pri;         /* total priority for current back-ends */
  pthread_mutex_t mut; /* mutex for this service */
  SESS_TYPE sess_type;
  int sess_ttl;       /* session time-to-live */
  regex_t sess_start; /* pattern to identify the session data */
  regex_t sess_pat;   /* pattern to match the session data */

#if OPENSSL_VERSION_NUMBER >= 0x10000000L
  LHASH_OF(TABNODE) *sessions; /* currently active sessions */
#else
  LHASH *sessions; /* currently active sessions */
#endif
  regex_t becookie_re; /* Regexs to find backend cookies */
  char *becookie,      /* Backend Cookie Name */
      *becdomain,      /* Backend Cookie domain */
      *becpath;        /* Backend cookie path */
  int becage;          /* Backend cookie age */
  int dynscale; /* true if the back-ends should be dynamically rescaled */
  int disabled; /* true if the service is disabled */
  int sts;      /* strict transport security */
  ServiceConfig *next;
};

typedef struct _pound_ctx {
  SSL_CTX *ctx;
  char *server_name;
  unsigned char **subjectAltNames;
  unsigned int subjectAltNameCount;
  struct _pound_ctx *next;
} POUND_CTX;

/* Listener definition */
struct ListenerConfig {
  int key_id;
  struct addrinfo addr; /* IPv4/6 address */
  int sock;             /* listening socket */
  POUND_CTX *ctx;       /* CTX for SSL connections */
  int clnt_check;       /* client verification mode */
  int noHTTPS11;        /* HTTP 1.1 mode for SSL */
  MATCHER *forcehttp10; /* User Agent Patterns to force HTTP 1.0 mode */
  MATCHER *
      ssl_uncln_shutdn; /* User Agent Patterns to enable ssl unclean shutdown */
  char *add_head;       /* extra SSL header */
  regex_t verb;         /* pattern to match the request verb against */
  int to;               /* client time-out */
  int has_pat;          /* was a URL pattern defined? */
  regex_t url_pat;      /* pattern to match the request URL against */
  char *err414,         /* error messages */
      *err500, *err501, *err503, *errnossl;
  char *nossl_url; /* If a user goes to a https port with a http: url, redirect
                      them to this url */
  int nossl_redir; /* Code to use for redirect (301 302 307)*/
  long max_req;    /* max. request size */
  MATCHER *head_off;      /* headers to remove */
  int rewr_loc;           /* rewrite location response */
  int rewr_dest;          /* rewrite destination header */
  int disabled;           /* true if the listener is disabled */
  int log_level;          /* log level for this listener */
  int allow_client_reneg; /* Allow Client SSL Renegotiation */
  int disable_ssl_v2;     /* Disable SSL version 2 */
  ServiceConfig *services;
  ListenerConfig *next;
};
