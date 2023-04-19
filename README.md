# ZPROXY

ZEVENET Zproxy is a high-performance multithreaded and event-driven L7 reverse
proxy and load balancer inspired by Pound reverse proxy simplicity.

Zproxy main features:

* HTTP, HTTPS handling
* Pound load balancer configuration file compatibility.
* Managed by REST API requests in JSON format.
* Load balancing algorithms: Round Robin, Least Connections, Response Time,
  Pending Connections
* Connection pinning.
* Backend output traffic marking.

## Table of Contents

* [Getting Started](#getting-started)
  * [Build Prerequisites](#build-prerequisites)
  * [Building The Project](#building-the-project)
  * [Project Structure](#project-structure)
  * [Quick Start Guide](#quick-start-guide)
* [Launch Time Options](#launch-time-options)
* [Configuration File](#configuration-file)
  * [Global Directives](#global-directives)
  * [HTTP Listener](#http-listener-listenhttp)
  * [HTTPS Listener](#https-listener-listenhttps)
  * [Service](#service)
  * [Backend](#backend)
  * [Session](#session)
* [API Description](#api-description)
* [Contributing](#contributing)
* [License](#license)
* [Authors](#authors)

## Getting Started

These instructions will get you a copy of the project up and running on your
local machine for development and testing purposes.

### Build prerequisites

* A modern C/C++ compiler (>= C++17)
* CMake >= 3.6
* Openssl >= 1.1
* ModSecurity 3 (_needed for WAF_)
* PCRE 3
* libev
* Jansson

### Building The Project

First, check out the git repo:

```
$ git clone https://github.com/zevenet/zproxy.git zproxy
$ cd zproxy
$ mkdir build
$ cd build && cmake ..
$ make [&& make install]
```

By default the code is compiled with WAF support (requiring ModSecurity). To
compile without WAF support, use the `-DENABLE_WAF=OFF` option with the CMake
command as follows:

```
$ cd build/
$ cmake -DENABLE_WAF=OFF ..
$ make [&& make install]
```

### Project Structure

* `src/`, `include/` — C++ source files that compile into a library (libproxy.a)
  and the main Zproxy binary.
* `zcutils/` — Zproxy library utilities.
* `tests/functional/` — Functionality tests for the Zproxy binary.
* `doc/` — Code documentation and man pages.

### Quick start guide

Following this guide you will have a Zproxy instance deployed and running.

1. Download and build Zproxy.

2. Take one of the example configuration files at `tests/functional/tests/<test_name>/zproxy.cfg`.

3. Run `$ zproxy -f /path/to/config_file.cfg`

4. And there you go! You can now check the global proxy status by using the
   control API.

## Launch Time Options

```
Usage: ./zproxy-ng
  [ -h | --help ]                               Show this help
  [ -D | --disable-daemon ]                     Disable the daemon mode
  [ -C <FILE> | --control <FILE>]               Configure socket control
  [ -f <FILE> | --file <FILE> ]                 Launch with the given configuration file
  [ -p <PIDFILE> | --pid <PIDFILE> ]            Set the PID file path
  [ -c | --check ]                              Check the configuration without launching it
  [ -l <LEVEL> | --log <LEVEL> ]                Set the syslog level: 0-2 no logs, 3 break points, 4 alerts, 5 errors, 6 info, 7 debug.
  [ -L <OUTPUT> | --log-output <OUTPUT> ]       Set the daemon logs output: 0 syslog (default), 1 stdout, 2 stderr
  [ -V | --version ]                            Print the proxy version
```

## Configuration File

In general Zproxy needs three types of objects defined in order to function:
listeners, services and back-ends.

#### Listeners

A listener is a definition of how Zproxy receives requests from the clients
(browsers). Two types of listeners may be defined: regular HTTP listeners and
HTTPS (HTTP over SSL/TLS) listeners. At the very least a listener must define
the address and port to listen on, with additional requirements for HTTPS
listeners.

#### Services

A service is the definition of how the requests are answered. The services may
be defined within a listener or at the top level (global). When a request is
received Zproxy attempts to match them to each service in turn, starting with
the services defined in the listener itself and, if needed, continuing with the
services defined at the global level. The services may define their own
conditions as to which requests they can answer: typically this involves certain
URLs (images only, or a certain  path) or specific headers (such as the Host
header). A service may also define a session mechanism: if defined future
requests from a given client will always be answered by the same back-end.

#### Back-ends

The back-ends are the actual servers for the content requested. By itself,
Zproxy supplies no responses - all contents must be received from a "real" web
server. The back-end defines how the server should be contacted.

Two types of back-ends may be defined: a "regular" back-end which receives
requests and returns responses, a "redirect" back-end in which case Zproxy will
respond  with  a redirect response, without accessing any back-end at all.

Multiple back-ends may be defined within a service, in which case Zproxy will
load-balance between the available back-ends.

If a back-end fails to respond it will be considered "dead", in which case,
Zproxy will stop sending requests to it. Dead back-ends are periodically checked
for availability, and once they respond again they are "resurected" and requests
are sent again their way. If no back-ends are available (none were defined, or
all are "dead") then Zproxy will reply with "503 Service Unavailable", without
checking additional services.

The connection between Zproxy and the back-ends is always via HTTP(S),
regardless of the actual protocol used between Zproxy and the client.

### Global Directives

Global directives may appear anywhere within the configuration file, though it
is customary for them to be at the start. They may appear in any order.

* **Threads** nnn

  How many Thread workers Zproxy should use, (default:
  automatic). Default to system concurrency level see nproc command.

* **DHParams** "path/to/dhparams.pem"

  Use the supplied dhparams pem file for DH key exchange for
  non-export-controlled negotiations.  Generate such a file with openssl
  dhparam.  This can be  used  to  do  2048bit DHE.

* **IgnoreCase** 0|1

  Ignore case when matching URLs (default: 0). This value can be overridden for
  specific services.

* **CompressionAlgorithm** gzip|deflate (TBI)

  Specify the compression algorithm to use. If the client supports it and the
  response from the backend is not already compressed, Zproxy applies the
  compression.

* **Alive** value

  Specify how often Zproxy monitor checks for back-end hosts (default: 10
  seconds). In general, it is a good idea to set this as low as possible - it
  will  find resurrected or down hosts faster. However, if you set it too low it
  will consume more resources - so beware.

* **Client** value

  Specify for how long Zproxy will wait for a client request (default: 10
  seconds). After this long has passed without the client sending any data
  Zproxy will close the connection. Set it higher if your clients time-out on a
  slow network or over-loaded server, lower if you start getting DOS attacks or
  run into problems with IE clients.  This value can be overridden for specific
  listeners.

* **TimeOut** value

  How long should Zproxy wait for a response from the back-end (in seconds).
  Default: 15 seconds.  This value can be overridden for specific back-ends.

* **ConnTO** value

  How long should Zproxy wait for a connection to the back-end (in seconds).
  Default: the TimeOut value. This value can be overridden for specific
  back-ends.

* **ECDHCurve** "name"

  Use for listeners the named curve for elliptical curve encryption (default:
  automatic).

* **ListenHTTP** or **ListenHTTPS**

  An HTTP listener defines an address and port that Zproxy will listen on for
  HTTP requests. All configuration directives enclosed between ListenHTTP and
  End are specific to a single HTTP listener. At the very least you must specify
  and address and a port for each listener. The following directives are
  available:

### HTTP Listener (ListenHTTP)

* **Address** address

  The address that Zproxy will listen on. This can be a numeric IP address, or a
  symbolic host name that must be resolvable at run-time. This is a mandatory
  parameter. The address 0.0.0.0 may be used as an alias for 'all available
  addresses on this machine', but this practice is strongly discouraged, as it
  will interfere with the rewriting mechanisms (see below).

* **Port** port

  The port number that Zproxy will listen on.  This is a mandatory parameter.

* **Name** name

  Listener identifier. It is used mostly to maintain the listener status after a
  reload.

* **xHTTP** value

  Defines which HTTP verbs are accepted. The possible values are:

  * **0** (default) accept only standard HTTP requests (GET, POST, HEAD).

  * **1** additionally allow extended HTTP requests (PUT, PATCH, DELETE).

  * **2** additionally allow standard WebDAV verbs (LOCK, UNLOCK, PROPFIND,
    PROPPATCH, SEARCH, MKCOL, MOVE, COPY, OPTIONS, TRACE, MKACTIVITY, CHECKOUT,
    MERGE, REPORT).

  * **3** additionally allow MS extensions WebDAV verbs (SUBSCRIBE, UNSUBSCRIBE,
    NOTIFY, BPROPFIND, BPROPPATCH, POLL, BMOVE, BCOPY, BDELETE, CONNECT).

  * **4** additionally allow MS RPC extensions verbs (RPC_IN_DATA, RPC_OUT_DATA).

  * **5** API REST standard: GET, POST, HEAD, PUT, PATCH, DELETE and OPTIONS

* **Client** value

  Override the global Client time-out value.

* **CheckURL** "pattern to match"

  Define  a  pattern  that  must be matched by each request sent to this
  listener. A request that does not match is considered to be illegal.  By
  default Zproxy accepts all requests (i.e. the pattern is ".\*"), but you are
  free to limit it to something more reasonable. Please note that this applies
  only to the request path - Zproxy will still check that the request is
  syntactically correct.

* **ErrWAF** "filename"

  A file with the text to be displayed if the WAF reject a request.  Default:
  "The request was rejected by the server.". Maximum file size: 4KB.

* **Err414** "filename"

  A file with the text to be displayed if an Error 414 occurs.  Default:
  "Request URI is too long.". Maximum file size: 4KB.

* **Err500** "filename"

  A file with the text to be displayed if an Error 500 occurs.  Default: "An
  internal server error occurred. Please try again later.". Maximum file size:
  4KB.

* **Err501** "filename"

  A file with the text to be displayed if an Error 501 occurs.  Default: "This
  method may not be used.". Maximum file size: 4KB.

* **Err503** "filename"

  A file with the text to be displayed if an Error 503 occurs.  Default: "The
  service is not available. Please try again later.". Maximum file size: 4KB.

* **ErrNoSsl** [code] "filename"

  A file with the text to be displayed if a user connects to a HTTPS listener
  with HTTP. If NoSslRedirect is defined, it takes precedence over this
  directive. Default: "Please use HTTPS.".

  The optional parameter "code" is the HTTP response code, it expects an 4xx or
  5xx value. Default: "400". Maximum file size: 4KB.

  Only valid for HTTPS listeners.

* **NoSslRedirect** [code] "url"

  A url that the user will be redirected to if the user connects to a HTTPS
  listener with HTTP. The code here is just like the code in Redirect blocks. It
  defaults to 302, but could be 301 or 307. Only valid for HTTPS listeners. If
  ErrNoSsl is defined also it will be ignored. Maximum file size: 4KB.

  Example:

  ```
  NoSslRedirect "https://thishost:port"
  ```

* **MaxRequest** nnn

  Request maximal size. It limits the total request header length, this includes
  request line (HTTP verb, HTTP URL and HTTP version), the sum of headers and
  the CLRN characters to end each header.  If a request contains more data than
  allowed an error 414 is returned.  If MaxRequest is not defined, it is
  "unlimited", but really it has a size of 64KB which is the connection buffer
  size. This value cannot be modified and it is set in compilation time.

* **AddRequestHeader** "header: to add"

  Add the defined header to the request passed to the back-end server. The
  header is added verbatim. Use multiple AddRequestHeader directives if you need
  to add more than one header.

* **RemoveRequestHeader** "header pattern"

  Remove  certain  headers  from  the incoming requests. All occurences of the
  matching specified header will be removed. Please note that this filtering is
  done prior to other checks (such as HeadRequire or HeadDeny), so you should
  not try to check for these headers in later matches. Multiple directives may
  be specified in order to remove more than one header, and the header itself
  may be a regular pattern (though this should be used with caution).

* **AddResponseHeader** "header: to add"

  Add the defined header to the response passed to the clients. The header is
  added verbatim. Use multiple AddResponseHeader directives if you need to add
  more than one header.

* **RemoveResponseHeader** "header pattern"

  Remove  certain  headers  from  the outcomming response, the header sent by
  the backend is not sent to the client. All occurences of the matching
  specified header will be removed. Multiple directives may be specified in
  order to remove more than one header, and the header itself may be a regular
  pattern (though this should be used with caution).

* **ReplaceHeader** `<Request|Response> "<header-name-regex>"
  "<header-value-match>" "<formated-value-replace>"`

  Replace a header in request or response. If several regex matches in the
  header, only the first one will apply.  The replaceHeader directive in the
  services has priority over the listener one.

  Example:

  ```
  ReplaceHeader  Request    "^Cookie:"         "^COOKIESESSION=(.*)"  "COOKIEUSER=$1"
  ReplaceHeader  Response   "^X-Forward-For:"  "(.*)"                 "$1,10.24.5.89"
  ```

* **RewriteLocation** 0|1 [0|1]

  Changes the Location and Content-Location headers in the responses to show the
  virtual host that was sent in the request.  This directive can be defined in a
  service in order to overwrite its value.  It can apply the rewrite in two
  modes:

  Backend. The rewrite is applied if the location header points to the backend
  itself. This is useful to mask and hide the backend address.  Listener. It
  rewrites the header if it points to the listener but with  the  wrong
  protocol. It is useful for redirecting a request to an HTTPS listener on the
  same server as the HTTP listener.

  The value 0 disables this directive.  The value 1 (by default) enables host
  rewrites.

  _Note: if the URL location contains a hostname, Zproxy should be able to
  resolve it or the rewrite will be skipped._

  The second optional parameter applies if the **RewriteUrl** directive modified
  the request URL. This flag forces to revert the URL transformation that
  RewriteUrl did. Example: if rewrite modified `/svc1/app` to `/svc2/app`, if
  the response location header is `/svc2/app` will be replaced to `/svc1/app`.
  Enabled by default, write a 0 to disable.

* **RewriteDestination** 0|1

  If 1 force Zproxy to change the Destination: header in requests. The header is
  changed to point to the back-end itself with the correct protocol. Default: 0.

* **RewriteHost** 0|1

  If 1 force Zproxy to change the Host: header in requests. The header is
  changed to point to the back-end itself using the IP and port (Example:
  192.168.200.50:80). Default: 0.

* **WafRules** "file_path"

  Apply a WAF ruleset file to the listener. It is possible to add several
  directives of this type. Those will be analyzed sequentially, in the same
  order that  they  appear  in the configuration file. The rule file must be
  compatibility with the Modsecurity syntax (SecLang).

* **Service** "name"

  Defines a private service (see below for service definition syntax). This
  service will be used only by this listener.

### HTTPS Listener (ListenHTTPS)

An HTTPS listener defines an address and port that Zproxy will listen on for
HTTPS requests. All configuration directives enclosed between ListenHTTPS and
End are specific to a single  HTTPS  listener.  At the very least you must
specify and address, a port and a server certificate for each listener. All
directives defined for HTTP listeners are applicable to HTTPS listeners as well.
The following additional directives are also available:

* **Cert** "certificate file"

  Specify the server certificate. The certificate  file is the file containing
  the certificate, possibly a certificate chain and the signature for this
  server. This directive or the CertDir directive is mandatory for HTTPS
  listeners.

  Please note that multiple Cert or CertDir directives are allowed if your
  OpenSSL version supports SNI. In such cases, the first directive is the
  default certificate, with additional certificates used if the client requests
  them.

  The ordering of the directives is important: the first certificate where the
  CN matches the client request will be used, so put your directives in the
  most-specific-to-least specific order (i.e. wildcard certificates after
  host-specific certificates).

  Cert and CertDir directives must precede all other SSL-specific directives.

* **Disable** TLSv1|TLSv1\_1|TLSv1\_2|TLSv1\_3

  Disable the protocol and all lower protocols as well.  This is due to a
  limitation in OpenSSL, which does not support disabling a single protocol. For
  example, Disable  TLSv1\_1 would disable TLSv1 and TLSv1\_1, thus allowing
  only TLSv1\_2 and TLSv1\_3. Disable TLSv1\_3 would disable only
  TLSv1\_3. SSLv2 and SSLv3 are disable by default.

* **Ciphers** "acceptable:cipher:list"

  List of ciphers that will be accepted by the SSL connection; it is a string in
  the same format as in OpenSSL ciphers(1) and SSL_CTX_set_cipher_list(3).

* **SSLHonorCipherOrder** 0|1

  If  this  value  is 1, the server will broadcast a preference to use Ciphers
  in the order supplied in the Ciphers directive.  If the value is 0, the server
  will treat the Ciphers list as the list of Ciphers it will accept, but no
  preference will be indicated.  Default value is 0.

* **SSLAllowClientRenegotiation** 0|1|2

  If this value is 0, client initiated renegotiation will be disabled.  This
  will mitigate DoS exploits based on client renegotiation, regardless of the
  patch status of clients and  servers related to "Secure renegotiation".  If
  the value is 1, secure renegotiation is supported.  If the value is 2,
  insecure renegotiation is supported, with unpatched clients. This can lead to
  a DoS and a Man in the Middle attack!  The default value is 0.

### Service

A service is a definition of which back-end servers Zproxy will use to reply to
incoming requests. A service may be defined as part of a listener (in which case
it will be used only by that listener), or globally (which makes it available to
all listeners).  Zproxy will always try the private services in the order
defined, followed by the global ones.

All configuration directives enclosed between Service and End are specific to a
single service. The following directives are available:

* **URL** "pattern"

  Match the incoming request. If a request fails to match than this service will
  be skipped and next one tried. If all services fail to match Zproxy returns an
  error. You may define multiple URL conditions per service, in which case all
  patterns must match. If no URL was defined then all requests match. The
  matching is by default case-sensitive, but this can be overridden by
  specifying IgnoreCase 1.

* **RewriteUrl** "pattern" "replace" [last]

  Checks a pattern in order to get strings from URL and replace them.  Several
  RewriteUrl directives can be added. All of them will be sequentially applied
  to the incoming URL unless the _last_ flag is set that will finish the rewrite
  url phase.

  Examples: if you specified

  ```
  RewriteUrl "/media/(.+)$" "/svc1/$1" last
  RewriteUrl "^(.*)$" "/sub-default$1"
  ```

  A regex will be applied only once per directive, I.E, the directive
  `RewriteUrl "/param" "/p"` for the URL `/param/1/param/2` will produce
  `/p/1/param/2`.

* **RewriteLocation** 0|1 [0|1]

  Changes the Location and Content-Location headers in the responses to show the
  virtual host that was sent in the request.  This directive can be defined in a
  service in order to overwrite the listener value.  It can apply the rewrite in
  two modes:

  Backend. The rewrite is applied if the location header points to the backend
  itself. This is useful to mask and hide the backend address.  Listener. It
  rewrites the header if it points to the listener but with  the  wrong
  protocol. It is useful for redirecting a request to an HTTPS listener on the
  same server as the HTTP listener.

  The value 0 disables this directive.  The value 1 (by default) enables host
  rewrites.

  _Note: if the URL location contains a hostname, Zproxy should be able to
  resolve it or the rewrite will be skipped._

  The second optional parameter applies if the **RewriteUrl** directive modified
  the request URL. This flag forces to revert the URL transformation that
  RewriteUrl did. Example: if rewrite modified `/svc1/app` to `/svc2/app`, if
  the response location header is `/svc2/app` will be replaced to `/svc1/app`.
  Enabled by default, write a 0 to disable.

* **IgnoreCase** 0|1

  Override the global IgnoreCase setting.

* **HeadRequire** "pattern"

  The request must contain at least on header matching the given pattern.
  Multiple HeadRequire directives may be defined per service, in which case all
  of them must be  satisfied.

* **HeadDeny** "pattern"

  The request may not contain any header matching the given pattern.  Multiple
  HeadDeny directives may be defined per service, in which case all of them must
  be satisfied.

  Please note: if the listener or service defined a _HeadRequestRemove_
  directive, the matching headers are removed before the service matching is
  attempted.

* **AddRequestHeader** "header: to add"

  Overwrites the listener _AddRequestHeader_. Add the defined header to the
  request passed to the back-end server. The header is added verbatim. Use
  multiple AddRequestHeader directives if you need to add more than one header.

* **RemoveRequestHeader** "header pattern"

  Overwrites the listener _RemoveRequestHeader_. Remove  certain  headers  from
  the incoming requests. All occurences of the matching specified header will be
  removed. Please note that this filtering is done prior to other checks (such
  as HeadRequire or HeadDeny), so you should not try to check for these headers
  in later matches. Multiple directives may be specified in order to remove more
  than one header, and the header itself may be a regular pattern (though this
  should be used with caution).

* **AddResponseHeader** "header: to add"

  Overwrites the listener _AddResponseHeader_. Add the defined header to the
  response passed to the clients. The header is added verbatim. Use multiple
  AddResponseHeader directives if you need to add more than one header.

* **RemoveResponseHeader** "header pattern"

  Overwrites the listener _RemoveResponseHeader_. Remove  certain  headers  from
  the outcomming response, the header sent by the backend is not sent to the
  client. All occurences of the matching specified header will be removed.
  Multiple directives may be specified in order to remove more than one header,
  and the header itself may be a regular pattern (though this should be used
  with caution).

* **ReplaceHeader** `<Request|Response> "<header-name-regex>"
  "<header-value-match>" "<formated-value-replace>"`

  Replace a header in request or response. If several regex matches in the
  header, only the first one will apply.  The replaceHeader directive in the
  services has priority over the listener one.

  Example:
  ```
  ReplaceHeader  Request    "^Cookie:"         "^COOKIESESSION=(.*)"  "COOKIEUSER=$1"
  ReplaceHeader  Response   "^X-Forward-For:"  "(.*)"                 "$1,10.24.5.89"
  ```

* **RoutingPolicy** ROUND\_ROBIN|LEAST\_CONNECTIONS|RESPONSE\_TIME|PENDING\_CONNECTIONS

  Specify the routing policy. All the algorithms are weighted with all the
  weights set in each backend.

  * **ROUND\_ROBIN** use the round robin algorithm as a routing policy (used by default).

  * **LEAST\_CONNECTIONS** select the backend with least connections established
    using as a proportion the weights set.

  * **RESPONSE\_TIME** select the backend with the lowest response time using as
    a proportion the weights set.

  * **PENDING\_CONNECTIONS** select the backend with least pending connections
    using as a proportion the weights set.

* **BackEnd**

  Directives enclosed between a BackEnd and the following End directives define
  a single back-end server (see below for details). You may define multiple
  back-ends per service, in which case Zproxy will attempt to load-balance
  between them.

* **Redirect** [http code] "URL"

  With this directive zproxy will generate an HTTP response with the given http
  code or 302 by default, including in the "Location" header the URL provided.
  The new URL redirected could be an absolute including complete URI or relative
  path. In the case that the redirected URL doesn't match with the scheme
  `<protocol>://<something>`, then it would be considered a relative path and it
  would be appended to the original path given by the client.  Some regular
  expressions would be available for replacements from `$1` to `$9` to compound
  the redirected URI, according to the "URL" service matcher.  Also, `${VHOST}`
  variable is available which will use the "Host" header included in the client
  request. If no "Host" is provided, then the Listener IP and port would be
  used.

  Examples: if you specify in the configuration

  ```
  Redirect "http://abc.example"
  ```

  and the client requested `http://xyz/a/b/c` then it will be redirected to
  `http://abc.example`. If you specify in the configuration

  ```
  Redirect 301 "https://${VHOST}"
  ```

  and the client requested `http://abc.example` then it will be redirected to
  `https://abc.example` if the client requested `http://xyz.example` then it
  will be redirected to `https://xyz.example`

  Technical note: in an ideal world Zproxy should reply with a "307 Temporary
  Redirect" status. Unfortunately, that is not yet supported by all clients (in
  particular HTTP 1.0 ones), so Zproxy currently replies by default with a "302
  Found" instead. You may override this behaviour by specifying the code to be
  used (301, 302 or 307).

* **Session**

  Directives enclosed between a Session and the following End directives define
  a session-tracking mechanism for the current service. See below for details.

### BackEnd

A back-end is a definition of a single back-end server Zproxy will use to reply
to incoming requests.  All configuration directives enclosed between BackEnd and
End are specific to a single service. The following directives are available:

* **Address** address

  The address that Zproxy will connect to. This can be a numeric IP address, or
  a symbolic host name that must be resolvable at run-time. If the name cannot
  be resolved to a valid address, Zproxy will assume that it represents the path
  for a Unix-domain socket. This is a mandatory parameter.

* **Port** port

  The port number that Zproxy will connect to. This is a mandatory parameter for
  non Unix-domain back-ends.

* **HTTPS**

  The back-end is using HTTPS.

* **Weight** value

  The weight of this back-end (between 1 and 9, 5 is default). Higher weight
  back-ends will be used more often than lower weight ones, so you should define
  higher weights for more capable servers.

* **Priority** value

  The service priority is 1 initially. If the status of a backend changes, the
  service priority is recalculated by adding one for each backend that is not
  active and has a priority lower than or equal to that of the new service
  priority.

* **ConnLimit** value

  The maximum number of established connection per backend. With a value of 0,
  there will not be a limit in the backend. The client will receive a 503 error
  if there aren't available backends.

* **TimeOut** value (TBI)

  Override the global TimeOut value.

* **ConnTO** value

  Override the global ConnTO value.

* **Nfmark** value

  Allow to mark all the Zproxy back-end connections in order to track them and
  allow to the Kernel network stack to manage them. (Decimal or hexadecimal
  format)

### Session

Defines how a service deals with possible HTTP sessions.  All configuration
directives enclosed between Session and End are specific to a single service.
Once a sessions is identified, Zproxy will attempt to send all requests within
that session to the same back-end server.

The following directives are available:

* **Type** IP|BASIC|URL|PARM|COOKIE|HEADER|COOKIEINSERT

  This is a mandatory parameter that can have once of the following values:

  * **IP**: the client address
  * **BASIC**: basic authentication
  * **URL**: a request parameter
  * **PARM**: a URI parameter
  * **COOKIE**: a certain cookie
  * **HEADER**: a  certain  request header
  * **COOKIEINSERT**: Zproxy will inject a cookie in each response with the
      appropriate backend's key, so that even if the session table is flushed or
      sessions are disabled, the proper backend can be chosen. This allows for
      session databases to be offloaded to the client side via browser cookies.

* **TTL** seconds

  How long can a session be idle (in seconds). A session that has been idle for
  longer than the specified number of seconds will be discarded. This is a
  mandatory parameter.

* **ID** "name"

  The session identifier. This directive is permitted only for sessions of type
  URL (the name of the request parameter we need to track), COOKIE (the name of
  the cookie) and HEADER (the header name).

* **Path** "path\_domain"

  This parameter should be used only for COOKIEINSERT session. It is the path
  value in the cookie header

* **Domain** "cookie\_domain"

  This parameter should be used only for COOKIEINSERT session. It is the domain
  value in the cookie header

## API Description

Zproxy allows you to consult and modify values and configurations during runtime
by means of a control API.  All requests must be directed to the Zproxy unix
socket. You can find more information by reading [the API
specification](/doc/ctl-api.md).

## Contributing

**Pull Requests are WELCOME!** Please submit any fixes or improvements:

* [Project Github Home](https://github.com/zevenet/zproxy)
* [Submit Issues](https://github.com/zevenet/zproxy/issues)
* [Pull Requests](https://github.com/zevenet/zproxy/pulls)

## License

Copyright &copy; 2019 ZEVENET. Licensed under the terms & conditions of the GNU
Affero General Public License (AGPL-3.0).

## Authors

ZEVENET Team
