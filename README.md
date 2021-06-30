
# ZPROXY

ZEVENET zproxy is a high-performance multithreaded and event-driven L7 reverse proxy and load balancer inspired by Pound reverse proxy simplicity.

Zproxy main features:

* HTTP, HTTPS handling
* Pound load balancer configuration file compatibility.
* Managed by REST API requests in JSON format.
* Load balancing algorithms: Round Robin, Least Connections, Response Time, Pending Connections
* Connection pinning.
* Backend output traffic marking.
* Simple HTTP Caching - WIP
* Pound control interface like binary (zproxyctl)

## Table of Contents

- [Getting Started](#getting-started)
	- [Build Prerequisites](#build-prerequisites)
	- [Building The Project](#building-the-project)
- [Configuration File](#configuration-file)
	- [Global Directives](#global-directives)
	- [HTTP Listener](#http-listener)
	- [HTTPS Listener](#https-listener)
	- [Service](#service)
	- [Cache](#cache)
	- [Backend](#backend)
	- [Session](#session)
- [API Description](#api-description)
- [Other Binaries](#other-binaries)
- [Benchmark](#benchmark)
- [Contributing](#contributing)
- [License](#license)
- [Authors](#authors)


## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Build prerequisites

* A modern C/C++ compiler (>= C++17)
* CMake >= 3.6
* Openssl >= 1.1
* zlib
* doxygen for source code documentation generation

*Note: You can download and build zlib and libssl during the zproxy compilation by enabling BUNDLED_ZLIB and BUNDLED_OPENSSL.*

### Building The Project

#### Git Clone

First, we need to check out the git repo:

```bash
$ git clone https://github.com/zevenet/zproxy zproxy.git
$ cd zproxy.git
$ mkdir build
$ cd build && cmake ..
$ make [&& make install]

# Check the command line interface controller help output:
$ bin/zproxyctl

# Run the tests: WIP
$ bin/zproxytests
```

#### Project Structure

* `src/*` — C++ code that compiles into a library (libl7proxy.a) and the main zproxy binary.
* `src/ctl` — Generate a pound command line interface like binary - zproxyctl
* `tests/lib` — C++ libraries used for tests ( Google Test).
* `tests/src` — C++ test suite.
* `cmake/*` — Cmake input files.
* `docs/` _ Doxygen configuration file (Doxyfile) and man pages.

#### Quick start guide

By following this guide you will end up having a zproxy deployed and running.

1. Download and build zproxy.

2. Take one of the example configuration files at `tests/`. It is recommended to use `simple_http.cfg` or `simple_https.cfg` and modify it to use your infrastructure.

3. Run `$ bin/zproxy -f /path/to/config_file.cfg`

4. Now it is ready! You can check the global proxy status by using the control API.


## Configuration File

In general zproxy needs three types of objects defined in order to function: listeners, services and back-ends.

#### Listeners

A  listener  is  a  definition of how zproxy receives requests from the clients (browsers). Two types of listeners may be defined: regular HTTP listeners and HTTPS (HTTP over SSL/TLS) listeners.  At the very least a listener must define the address and port to listen on, with additional requirements for HTTPS listeners.

#### Services

A service is the definition of how the requests are answered. The services may be defined within a listener or at the top level (global). When a request  is  received  zproxy attempts  to  match them to each service in turn, starting with the services defined in the listener itself and, if needed, continuing with the services defined at the global level. The services may define their own conditions as to which requests they can answer: typically this involves certain URLs (images only, or a certain  path)  or  specific headers (such as the Host header). A service may also define a session mechanism: if defined future requests from a given client will always be answered by the same back-end.

#### Back-ends

The back-ends are the actual servers for the content requested. By itself, zproxy supplies no responses - all contents must be received from a "real" web server. The back-end defines how the server should be contacted.

Three types of back-ends may be defined: a "regular" back-end which receives requests and returns responses, a "redirect" back-end in which case zproxy will  respond  with  a redirect response, without accessing any back-end at all, or an "emergency" back-end which will be used only if all other backends are "dead".

Multiple back-ends may be defined within a service, in which case zproxy will load-balance between the available back-ends.

If  a back-end fails to respond it will be considered "dead", in which case zproxy will stop sending requests to it. Dead back-ends are periodically checked for availability, and once they respond again they are "resurected" and requests are sent again their way. If no back-ends are available (none were defined, or all are "dead") then zproxy will reply with "503 Service Unavailable", without checking additional services.

The connection between zproxy and the back-ends is always via HTTP(S), regardless of the actual protocol used between zproxy and the client.


### Global Directives

Global directives may appear anywhere within the configuration file, though it is customary for them to be at the start. They may appear in any order.

- **User** "user_name"

	Specify the user zproxy will run as (must be defined in /etc/passwd).

- **Group** "group_name"

	Specify the group zproxy will run as (must be defined in /etc/group).

- **Name** SortName

	Specify a Sort name without blank spaces for the Process, this information will shown in logs

- **RootJail** "directory_path_and_name"

	Specify the directory that zproxy will chroot to at runtime. Please note that OpenSSL requires access to /dev/urandom, so make sure you create a device by that name, accessible from the root jail directory.  zproxy may also require access to /dev/syslog or similar.

- **Daemon** 0|1

	Have zproxy run in the foreground (if 0) or as a daemon (if 1). By default zproxy runs as a daemon (detaches itself from the controlling terminal and puts itself in the background). By specifying this option you can force zproxy to work like a regular process. Useful for debugging or if you want to use something like daemontools.

- **Threads** nnn

	How many Thread workers zproxy should use, (default: automatic). Default to system concurrency level see nproc command.

- **LogFacility** value

	Specify  the  log facility to use.  value (default: daemon) must be one of the symbolic facility names defined in syslog.h. This facility shall be used for logging. Using a for the facility name causes zproxy to log to stdout/stderr.

- **DHParams** "path/to/dhparams.pem"

	Use the supplied dhparams pem file for DH key exchange for non-export-controlled negotiations.  Generate such a file with openssl dhparam.  This can be  used  to  do  2048bit DHE.

- **LogLevel** value

	Specify  the logging level following the syslog scheme, 0 for no logging, 1 (default) for regular information about the Service and BackEnd used).  This value can be overridden for specific listeners.

- **IgnoreCase** 0|1

	Ignore case when matching URLs (default: 0). This value can be overridden for specific services.

- **Ignore100continue** 0|1

	Ignore Header Expect: 100-continue (default: 1, Ignored).  If 0 zproxy manages Expect: 100-continue headers.

- **CompressionAlgorithm** gzip|deflate

	Specify the compression algorithm to use. If the client supports it and the response from the backend is not already compressed, zproxy applies the compression.

- **Alive** value

	Specify how often zproxy will check for resurected back-end hosts (default: 30 seconds). In general, it is a good idea to  set  this  as  low  as  possible  -  it  will  find resurected hosts faster. However, if you set it too low it will consume resources - so beware.

- **Client** value

	Specify for how long zproxy will wait for a client request (default: 10 seconds). After this long has passed without the client sending any data zproxy will close the connection. Set it higher if your clients time-out on a slow network or over-loaded server, lower if you start getting DOS attacks or run into problems with IE clients.  This value can be overridden for specific listeners.

- **TimeOut** value

	How long should zproxy wait for a response from the back-end (in seconds). Default: 15 seconds.  This value can be overridden for specific back-ends.

- **ConnTO** value

	How long should zproxy wait for a connection to the back-end (in seconds). Default: the TimeOut value. This value can be overridden for specific back-ends.

- **CacheRamSize** value

	The  maximum size (in bytes by default) that the cache will use from RAM. It is allowed to us some byte modifiers as k, K, m, M, g and G, pay attention not to set higher values than the available RAM free.

- **CacheRamPath** "path"

	Indicate the path to an existing directory to use as the root point where the RAM cache storage will be mounted using ramfs filesystem.

- **CacheDiskPath** "path"

	Path to an existing directory which will be used as the root point for the on disk cache storage.

- **CacheThreshold** value

	Percentage of the total size that the cache will use to determine whether an entry should go to ram or to disk.

- **WSTimeOut** value

	How long should zproxy wait for data from either back-end or client in a connection upgraded to a WebSocket (in seconds). Default: 600 seconds.  This value can be  overridden for specific back-ends.

- **Grace** value

	How long should zproxy continue to answer existing connections after a receiving and INT or HUP signal (default: 30 seconds). The configured listeners are closed immediately. You can bypass this behaviour by stopping zproxy with a TERM or QUIT signal, in which case the program exits without any delay.

- **SSLEngine** "name"

	Use an OpenSSL hardware acceleration card called name. Available only if OpenSSL-engine is installed on your system.

- **ECDHcurve** "name"

	Use for listener the named curve for elliptical curve encryption (default: automatic).

- **Control** "/path/to/socket"

	Set the control socket path. If not defined zproxy does not listen for any commands. The commands may be issued by using the zproxyctl(8) program.

- **ControlIP**    IP

	Set the control IP. If not defined zproxy does not listen for any commands. The commands may be issued by using the zproxyctl(8) program.

- **ControlPort**  port

	Set the control port. If not defines zproxy does not listen for any commands. The commands may be issued by using zproxyctl(8) program.

- **ControlUser** "user"

	The username to chown the Control socket to.

- **ControlGroup** "group"

	The groupname to chgrp the Control socket to.

- **ControlMode** 0660

	The mode the Control socket should use, in octal.

- **Include** "/path/to/file"

	Include the file as though it were part of the configuration file.

- **HTTP Listener**

	An HTTP listener defines an address and port that zproxy will listen on for HTTP requests. All configuration directives enclosed between ListenHTTP and End are specific to  a single HTTP listener. At the very least you must specify and address and a port for each listener. The following directives are available:

### HTTP Listener

- **Address address**

	The address that zproxy will listen on. This can be a numeric IP address, or a symbolic host name that must be resolvable at run-time.  This is a mandatory parameter. The address 0.0.0.0 may be used as an alias for 'all available addresses on this machine', but this practice is strongly discouraged, as it will interfere with the rewriting mechanisms (see below).

- **Port** port

	The port number that zproxy will listen on.  This is a mandatory parameter.

- **Key** "key"

	The key associated to this backend, if using BackendCookie in the service.  If left blank, it'll be autogenerated from the backend address.

- **xHTTP** value

	Defines which HTTP verbs are accepted. The possible values are:

	- **0** (default) accept only standard HTTP requests (GET, POST, HEAD).

	- **1** additionally allow extended HTTP requests (PUT, PATCH, DELETE).

	- **2** additionally allow standard WebDAV verbs (LOCK, UNLOCK, PROPFIND, PROPPATCH, SEARCH, MKCOL, MOVE, COPY, OPTIONS, TRACE, MKACTIVITY, CHECKOUT, MERGE, REPORT).

	- **3** additionally allow MS extensions WebDAV verbs (SUBSCRIBE, UNSUBSCRIBE, NOTIFY, BPROPFIND, BPROPPATCH, POLL, BMOVE, BCOPY, BDELETE, CONNECT).

	- **4** additionally allow MS RPC extensions verbs (RPC_IN_DATA, RPC_OUT_DATA).

- **Client** value

	Override the global Client time-out value.

- **CheckURL** "pattern to match"

	Define  a  pattern  that  must be matched by each request sent to this listener. A request that does not match is considered to be illegal.  By default zproxy accepts all requests (i.e. the pattern is ".*"), but you are free to limit it to something more reasonable. Please note that this applies only to the request path - zproxy will still check that the request is syntactically correct.

- **ErrWAF** "filename"

	A file with the text to be displayed if the WAF reject a request.  Default: "The request was rejected by the server.".

- **Err414** "filename"

	A file with the text to be displayed if an Error 414 occurs.  Default: "Request URI is too long.".

- **Err500** "filename"

	A file with the text to be displayed if an Error 500 occurs.  Default: "An internal server error occurred. Please try again later.".

- **Err501** "filename"

	A file with the text to be displayed if an Error 501 occurs.  Default: "This method may not be used.".

- **Err503** "filename"

	A file with the text to be displayed if an Error 503 occurs.  Default: "The service is not available. Please try again later.".

- **ErrNoSsl** [code] "filename"

	A file with the text to be displayed if a user connects to a HTTPS listener with HTTP.  Default: "Please use HTTPS.".

	The optional parameter "code" is the HTTP response code, it expects an 4xx or 5xx value. Default: "400".

	Only valid for HTTPS listeners.

- **NoSslRedirect** [code] "url"

	A url that the user will be redirected to if the user connects to a HTTPS listener with HTTP. The code here is just like the code in Redirect blocks. It defaults to 302, but could be 301 or 307. Only valid for HTTPS listeners.

		Example:
		*NoSslRedirect "https://thishost:port"*

- **MaxRequest** nnn

	Request maximal size. All requests will be limited to these many bytes. If a request contains more data than allowed an error 414 is returned. Default: unlimited.

- **HeadRemove** "header pattern"

	Remove  certain  headers  from  the incoming requests. All occurences of the matching specified header will be removed. Please note that this filtering is done prior to other checks (such as HeadRequire or HeadDeny), so you should not try to check for these headers in later matches. Multiple directives may be specified in order to remove more than one header, and the header itself may be a regular pattern (though this should be used with caution).

- **AddHeader** "header: to add"

	Add the defined header to the request passed to the back-end server. The header is added verbatim. Use multiple AddHeader directives if you need to add more than one header.

- **AddResponseHeader** "header: to add"

	Add the defined header to the response passed to the clients. The header is added verbatim. Use multiple AddHeader directives if you need to add more than one header.

- **RemoveResponseHead** "header pattern"

	Remove  certain  headers  from  the outcomming response, the header sent by the backend is not sent to the client. All occurences of the matching specified header will be removed. Multiple directives may be specified in order to remove more than one header, and the header itself may be a regular pattern (though this should be used with caution).

- **ReplaceHeader** `<Request|Response> <header-name-regex> <header-value-match> <formated-value-replace>`

	Replace a header in request or response. If several regex matches in the header, only the first one will apply.
	The replaceHeader directive in the services has priority over the listener one.

		Example:
		  ReplaceHeader  Request    "^Cookie:"         "^COOKIESESSION=(.*)"  "COOKIEUSER=$1"
		  ReplaceHeader  Response   "^X-Forward-For:"  "(.*)"                 "$1,10.24.5.89"

- **RewriteLocation** 0|1|2

	This directive changes the Location and Content-Location headers in the responses to show the virtual host that was sent in the request.
	It can apply the rewrite in two modes:

	Backend. The rewrite is applied if the location header points to the backend itself. This is useful to mask and hide the backend address.
	Listener. It rewrites the header if it points to the listener but with  the  wrong  protocol. It is useful for redirecting a request to an HTTPS listener on the same server as the HTTP listener.

	The value 0 disables this directive.
	The value 1 (by default) enables the backend and listener rewrites.
	The value 2 only enables the backend rewrites.

	*Note: if the URL location contains a hostname, zproxy should be able to resolve it or the rewrite will be skipped.*

- **RewriteDestination** 0|1

	If 1 force zproxy to change the Destination: header in requests. The header is changed to point to the back-end itself with the correct protocol. Default: 0.

- **RewriteHost** 0|1

	If 1 force zproxy to change the Host: header in requests. The header is changed to point to the back-end itself using the IP and port (Example: 192.168.200.50:80). Default: 0.

- **WafRules** "file path"

	Apply a WAF ruleset file to the listener. It is possible to add several directives of this type. Those will be analyzed sequentially, in the same order that  they  appear  in the configuration file. The rule file must be compatibility with the Modsecurity syntax (SecLang).

- **LogLevel** value

	Override the global LogLevel value.

- **Service** [ "name" ]

	This  defines a private service (see below for service definition syntax). This service will be used only by this listener. The service may be optionally named, with the name showing in the zproxyctl listings.


### HTTPS Listener
An HTTPS listener defines an address and port that zproxy will listen on for HTTPS requests. All configuration directives enclosed between ListenHTTPS and End are specific to a single  HTTPS  listener.  At the very least you must specify and address, a port and a server certificate for each listener. All directives defined for HTTP listeners are applicable to HTTPS listeners as well. The following additional directives are also available:

- **SSLConfigFile** "ssl config file"

	Specify the OpenSSL configuration file. This file must follow the OpenSSL .cnf file format. Here is an example of an openSSL configuration file.

                  zproxy = test_sect

                  [ test_sect ]
                  ssl_conf = start_point

                  [ start_point ]
                  lis = listener

                  [ listener ]
                  RSA.Certificate = /path/to/your/cert.pem

- **SSLConfigSection**  section

	Specify the OpenSSL configuration section. This section must be in the OpenSSL configuration file specified before.

- **Cert** "certificate file"

	Specify the server certificate. The certificate file is the file containing the certificate, possibly a certificate chain and the signature for this server. This directive or the CertDir directive is mandatory for HTTPS listeners.

	Please note that multiple Cert or CertDir directives are allowed if your OpenSSL version supports SNI. In such cases, the first directive is the default certificate, with additional certificates used if the client requests them.

	The ordering of the directives is important: the first certificate where the CN matches the client request will be used, so put your directives in the  most-specific-to-least specific order (i.e. wildcard certificates after host-specific certificates).

	Cert and CertDir directives must precede all other SSL-specific directives.

- **CertDir** "certificate directory"

	Specify the server certificate or certificates. The certificate directory is a directory path containing one or more certificates, possibly a certificate chain and the signature for this server. This directive or Cert is mandatory for HTTPS listeners.

	If a wildcard is specified, it will be honored.  Otherwise all files will be loaded from that directory.  For example, "/etc/certs/*.pem" will load all files from that directory that match the file extension given.

	Please note that multiple Cert or CertDir directives are allowed if your OpenSSL version supports SNI. In such cases, the first directive is the default certificate, with additional certificates used if the client requests them.

	The filenames in the directory will be sorted before being loaded. The order of files is important: the first certificate where the CN matches  the  client  request  will  be used, so sort your files in the most-specific-to-least specific order (i.e. wildcard certificates after host-specific certificates).

	Cert and CertDir directives must precede all other SSL-specific directives.

- **ClientCert** 0|1|2|3 depth

	Ask  for the client's HTTPS certificate: 0 - don't ask (default), 1 - ask, 2 - ask and fail if no certificate was presented, 3 - ask but do not verify.  Depth is the depth of verification for a client certificate (up to 9). The default depth limit is 9, allowing for the peer certificate and additional 9 CA certificates that must be verified.

- **Disable** SSLv2|SSLv3|TLSv1|TLSv1_1|TLSv1_2|TLSv1_3

	Disable the protocol and all lower protocols as well.  This is due to a limitation in OpenSSL, which does not support disabling a single protocol. For example, Disable  TLSv1 would disable SSLv2, SSLv3 and TLSv1, thus allowing only TLSv1_1 and TLSv1_2.  [NOTE]Disable TLSv1_3 would disable only TLSv1_3.

- **ECDHcurve** "name"

	Use the named curve for elliptical curve encryption (default: automatic), overwrite global ECDHcurve.

- **Ciphers** "acceptable:cipher:list"

	This is the list of ciphers that will be accepted by the SSL connection; it is a string in the same format as in OpenSSL ciphers(1) and SSL_CTX_set_cipher_list(3).

- **SSLHonorCipherOrder** 0|1

	If  this  value  is 1, the server will broadcast a preference to use Ciphers in the order supplied in the Ciphers directive.  If the value is 0, the server will treat the Ciphers list as the list of Ciphers it will accept, but no preference will be indicated.  Default value is 0.

- **SSLAllowClientRenegotiation** 0|1|2
              If this value is 0, client initiated renegotiation will be disabled.  This will mitigate DoS exploits based on client renegotiation, regardless of the patch status of clients and  servers related to "Secure renegotiation".  If the value is 1, secure renegotiation is supported.  If the value is 2, insecure renegotiation is supported, with unpatched clients. This can lead to a DoS and a Man in the Middle attack!  The default value is 0.

- **CAlist** "CAcert_file"

	Set the list of "trusted" CA's for this server. The CAcert_file is a file containing a sequence of CA certificates (PEM format). The names of the defined CA certificates will be sent to the client on connection.

- **VerifyList** "Verify_file"

	Set the CA (Certificate Authority). The Verify_file is a file that contains the CA root certificates (in PEM format).

	Please note: there is an important difference between the CAlist and the VerifyList. The CAlist tells the client (browser) which client certificates it should send. The VerifyList defines which CAs are actually used for the verification of the returned certificate.

- **CRLlist** "CRL_file"

	Set the CRL (Certificate Revocation List) file. The CRL_file is a file that contains the CRLs (in PEM format).

- **ForwardSNI** "0|1 default=1"

	Enable SNI server host name forwarding to https backends if it presented by client.


### Service

A service is a definition of which back-end servers zproxy will use to reply to incoming requests. A service may be defined as part of a listener (in which case it will be used only by that listener), or globally (which makes it available to all listeners).  zproxy will always try the private services in the order defined, followed by the global ones.

All configuration directives enclosed between Service and End are specific to a single service. The following directives are available:

- **URL** "pattern"

	Match  the  incoming request. If a request fails to match than this service will be skipped and next one tried. If all services fail to match zproxy returns an error. You may define multiple URL conditions per service, in which case all patterns must match. If no URL was defined then all requests match. The matching is by  default  case-sensitive, but this can be overridden by specifying IgnoreCase 1

- **RewriteUrl** "pattern" "replace" [last]

	It checks a pattern in order to get strings from URL and replace them.
	Several RewriteUrl directives can be added. All of them will be sequentially applied to the incoming URL unless the *last* flag is set that will finish the rewrite url phase.

              Examples: if you specified

                  RewriteUrl "/media/(.+)$" "/svc1/$1" last
                  RewriteUrl "^(.*)$" "/sub-default$1"

	A regex will be applied only once per directive, I.E, the directive `RewriteUrl "/param" "/p"` for the URL `/param/1/param/2` will produce `/p/1/param/2`.

- **ReplaceHeader** `<Request|Response> <header-name-regex> <header-value-match> <formated-value-replace>`

	Replace a header in request or response. If several regex matches in the header, only the first one will apply.
	The replaceHeader directive in the services has priority over the listener one.

		Example:
		  ReplaceHeader  Request    "^Cookie:"         "^COOKIESESSION=(.*)"  "COOKIEUSER=$1"
		  ReplaceHeader  Response   "^X-Forward-For:"  "(.*)"                 "$1,10.24.5.89"

- **OrURLs**

	Defines a block of URL directives that should be merged into a single pattern, all OR'd together.  This creates a pattern like ((url1)|(url2)|(url3)) for as many URL directives as are specified within the block.  End the block with an End directive.

- **BackendCookie** "cookiename" "domain" "path" age|Session

	If defined, zproxy will inject a cookie in each response with the appropriate backend's key, so that even if the session table is flushed or sessions are disabled, the proper backend can be chosen.  This allows for session databases to be offloaded to the client side via browser cookies.  See Key in the backend definition.  The given age  will  be how  many  seconds  the cookie will persist for.  If set to 0, it will be a so-called "memory" cookie which will expire when the browser closes.  If set to "Session", it will mimick the session TTL behavior.

- **IgnoreCase** 0|1

	Override the global IgnoreCase setting.

- **HeadRequire** "pattern"

	The request must contain at least on header matching the given pattern.  Multiple HeadRequire directives may be defined per service, in which case all of them must be  satisfied.

- **HeadDeny** "pattern"

	The request may not contain any header matching the given pattern.  Multiple HeadDeny directives may be defined per service, in which case all of them must be satisfied.

	Please note: if the listener defined a HeadRemove directive, the matching headers are removed before the service matching is attempted.

- **RoutingPolicy** ROUND_ROBIN|LEAST_CONNECTIONS|RESPONSE_TIME|PENDING_CONNECTIONS

	Specify the routing policy. All the algorithms are weighted with all the weights set in each backend.

	- **ROUND_ROBIN** use the round robin algorithm as a routing policy (used by default).

	- **LEAST_CONNECTIONS** select the backend with least connections established
                  using as a proportion the weights set.

	- **RESPONSE_TIME** select the backend with the lowest response time using
                  as a proportion the weights set.

	- **PENDING_CONNECTIONS** select the backend with least pending connections
                  using as a proportion the weights set.

- **PinnedConnection**  0|1

	Specify if we want to pin all the connections, (default: 0, no pinned). If PinnedConnection is set to 1, zproxy directly forwards all data without parsing or editing.
- **DynScale** 0|1

	Enable or disable dynamic rescaling for the current service. This value will override the value globally defined.

- **Disabled** 0|1

	Start zproxy with this service disabled (1) or enabled (0). If started as disabled, the service can be later enabled with zproxyctl (8).

- **Cache**

	Directives enclosed between a Cache and the following End directives enable and define an HTTP1.1 Cache mechanism and its behaviour for the current Service. See below for details.

- **BackEnd**

	Directives enclosed between a BackEnd and the following End directives define a single back-end server (see below for details). You may define multiple back-ends per service, in which case zproxy will attempt to load-balance between them.

- **[Redirect | RedirectAppend | RedirectDynamic]** [code] "url"

	This is a special type of back-end. Instead of sending the request to a back-end zproxy replies immediately with a redirection to the given URL. You may define multiple redirectors in a service, as well as mixing them with regular back-ends.

	The address the client is redirected to is determined by the command you specify.  If you specify Redirect, the url is taken as an absolute host and path to redirect to.   If you use RedirectAppend, the original request path will be appended to the host and path you specified.  If you use RedirectDynamic, then url can contain RegEx replacements in the form $1 through $9 which indicate expression captured from the original request path. You must have a URL directive, and the first URL directive for the  service  is  the one used for capturing expressions.

              Examples: if you specified

                  Redirect "http://abc.example"

              and the client requested http://xyz/a/b/c then it will be redirected to http://abc.example, but if you specified

                  RedirectAppend "http://abc.example"

              it will be sent to http://abc.example/a/b/c.

              If you specified
                  URL "^/a(/([^/]*)(/[^/]*)"
                  RedirectDynamic "http://abc.example$2$1/index.html"

              it will be sent to http://abc.example/c/b/index.html.

	Technical  note: in an ideal world zproxy should reply with a "307 Temporary Redirect" status. Unfortunately, that is not yet supported by all clients (in particular HTTP 1.0 ones), so zproxy currently replies by default with a "302 Found" instead. You may override this behaviour by specifying the code to be used (301, 302 or 307).

- **Server** Max-request

	Create a dummy server with a hello world 200 OK response and 100 as the maximum number of requests allowed on the same connection.

		Service "server"
		    Url "/server"
		    Server 100
		End

- **Emergency**

	Directives enclosed between an Emergency and the following End directives define an emergency back-end server (see below for details).  You  may  define  only  one  emergency server per service, which zproxy will attempt to use if all backends are down.

- **Session**

	Directives enclosed between a Session and the following End directives define a session-tracking mechanism for the current service. See below for details.

### Cache

The zproxy HTTP1.1 Cache mechanism is based on RFC 7234 and uses regular expressions and HTTP headers in order to determine if a HTTP response should be put in cache or not. The following directives determine how the Cache will behave:

- **Content** "PCRE regular expression"

	Regular expression following PCRE format, determines which kind of resources will be put in Cache depending on its URI.

- **CacheTO** Seconds

	Time in seconds that the cache will use to determine whether a cache entry is staled or not. This value may change for specific entries depending on HTTP cache related headers.

- **MaxSize** Bytes

	The maximum number of bytes that a response can have in order to be put on the cache system. Any entry with higher Content-Length header won't be stored in the cache.


### BackEnd

A back-end is a definition of a single back-end server zproxy will use to reply to incoming requests.  All configuration directives enclosed between BackEnd and End are specific to a single service. The following directives are available:

- **Address** address

	The address that zproxy will connect to. This can be a numeric IP address, or a symbolic host name that must be resolvable at run-time. If the name cannot be resolved to a valid address, zproxy will assume that it represents the path for a Unix-domain socket. This is a mandatory parameter.

- **Port** port

	The port number that zproxy will connect to. This is a mandatory parameter for non Unix-domain back-ends.

- **HTTPS**

	The back-end is using HTTPS.

- **Cert** "certificate file"

	Specify the certificate that zproxy will use as a client. The certificate file is the file containing the certificate, possibly a certificate chain and the signature.  This directive may appear only  after the HTTPS directive.

- **Disable** SSLv2|SSLv3|TLSv1|TLSv1_1|TLSv1_2|TLSv1_3

	Disable  the protocol and all lower protocols as well.  This is due to a limitation in OpenSSL, which does not support disabling a single protocol. For example, Disable TLSv1 would disable SSLv2, SSLv3 and TLSv1, thus allowing only TLSv1_1 and TLSv1_2.

	*NOTE: Disable TLSv1_3 would disable only TLSv1_3.  HTTPS directive.*

- **Ciphers** "acceptable:cipher:list"

	This is the list of ciphers that will be accepted by the SSL connection; it is a string in the same format as in OpenSSL ciphers(1) and SSL_CTX_set_cipher_list(3).  This directive may appear only after the HTTPS directive.

- **Weight** value

	The weight of this back-end (between 1 and 9, 5 is default). Higher weight back-ends will be used more often than lower weight ones, so you should define higher weights for more capable servers.

- **Priority** value

	The  priority  of this back-end (between 1 and 9, 1 is default). The requests will be forwarded to the backends with higher priority (1 is the highest priority).  When a back-end with high priority becomes unreacheable the priority level is decreased.

- **ConnLimit** value

	The maximum number of established connection per backend. With a value of 0, there will not be a limit in the backend. The client will receive a 503 error if there aren't available backends.

- **TimeOut** value

	Override the global TimeOut value.

- **ConnTO** value

	Override the global ConnTO value.

- **WSTimeOut** value

	Override the global WSTimeOut value.

- **HAport** [ address ] port

	A port (and optional address) to be used for server function checks. See below the "High Availability" section for a more detailed discussion. By default zproxy  uses  the  same  address  as  the  back-end server, but you may use a separate address if you wish. This directive applies only to non Unix-domain servers.

- **Disabled** 0|1

	Start zproxy with this back-end disabled (1) or enabled (0). If started as disabled, the back-end can be later enabled with zproxyctl (8).

- **Nfmark** value

	Allow to mark all the zproxy back-end connections in order to track them and allow to the Kernel network stack to manage them. (Decimal format)

- **Emergency**

	The  emergency  server  will  be used once all existing back-ends are "dead".  All configuration directives enclosed between Emergency and End are specific to a single service.

	The following directives are available:

	- **Address** address

		The address that zproxy will connect to. This can be a numeric IP address, or a symbolic host name that must be resolvable at run-time. If the name cannot be resolved to a valid address, zproxy will assume that it represents the path for a Unix-domain socket. This is a mandatory parameter.

	- **Port** port

		The port number that zproxy will connect to. This is a mandatory parameter for non Unix-domain back-ends.


### Session

Defines how a service deals with possible HTTP sessions.  All configuration directives enclosed between Session and End are specific to a single service. Once a sessions is identified, zproxy will attempt to send all requests within that session to the same back-end server.

The following directives are available:

- **Type** IP|BASIC|URL|PARM|COOKIE|HEADER

	What kind of sessions are we looking for: IP (the client address), BASIC (basic authentication), URL (a request parameter), PARM (a URI parameter), COOKIE (a certain cookie), or HEADER (a  certain  request header).  This is a mandatory parameter.

- **TTL** seconds

	How long can a session be idle (in seconds). A session that has been idle for longer than the specified number of seconds will be discarded.  This is a mandatory parameter.

- **ID** "name"

	The session identifier. This directive is permitted only for sessions of type URL (the name of the request parameter we need to track), COOKIE (the name of the cookie) and HEADER (the header name).



## API Description


*All request must be directed to the zproxy unix socket or to the control IP address and port. The response is going to be a JSON formatted response with all the information requested or the operation result.*

### API Requests

**Get the services status of the listener with the id "listener_id"**

GET http://address:port/listener/<listener_id>/services

**Get the service with the id "service_id" general status**

GET http://address:port/listener/<listener_id>/service/<service_id>

**Get the backend with the id "backend_id" general status**

GET http://address:port/listener/<listener_id>/service/<service_id>/backend/<backend_id>

**WIP - not all fields changes supported yet**

*Get any field of a service or backend*

GET http://address:port/listener/<listener_id>/service/<service_id>/<field_name>

GET http://address:port/listener/<listener_id>/service/<service_id>/backend/<backend_id>/<field_name>

*Modify any field of a service or backend*

POST {field_name: value} http://address:port/listener/<listener_id>/service/<service_id>/<field_name>

POST {field_name: value} http://address:port/listener/<listener_id>/service/<service_id>/backend/<backend_id>/<field_name>

*Reload all listeners in configuration file in use, draining connections*

PATCH  http://address:port/config


### API status response parameters

The following list of parameters are returned by the API after a GET request

#### Global

The global section defines global daemon configuration and information about the virtual entry

- **3xx-code-hits** "integer"

	It is the number of 3xx codes that the zproxy generated and responded to the clients. These responses don't come
from the backends.

- **4xx-code-hits** "integer"

	It is the number of 4xx codes that the zproxy generated and responded to the clients. These responses don't come
from the backends.

- **5xx-code-hits** "integer"

	It is the number of 5xx codes that the zproxy generated and responded to the clients. These responses don't come
from the backends.

- **waf-hits** "integer"

	It is the number of requests rejected by zproxy. They will be counted in *xxx-code-hits* depend on the response code.

- **address** "string"

	It is the IPv4/IPv6 address used by the zproxy to listen to HTTP requests. This parameter can be modified through a configuration file directive.

- **connections** "integer"

	It is the number of currently established connections that zproxy has established with the clients (on the VIP).

- **https** "bool"

	It informs if the listener is configured with SSL. This parameter can be modified through a configuration file directive.

- **id** "integer"

	It is the listener identifier.

- **name** "string"

	It is a friendly name for the listener. This parameter can be modified through a configuration file directive.

- **pending-connections** "integer"

	It is the number of connections that zproxy has received but they are not established in any backend. It is the number of established connection in the vip substranting it the established connection in all backends of the farm.

- **port** "integer"

	It is the virtual port open in the system where zproxy is listening. This parameter can be modified through a configuration file directive.

- **status** "string"

	It informs about the listener status. It can be *active* or *down* (if it is disabled).	It can be modified through the API.

- **services** "service list"

	It is a list of the service objects with their configuration and status.


#### Service Object

- **backends** "backend list"

	It is a list of the backend objects with their configuration and status.

- **id** "integer"

	It is the service identifier.

- **name** "string"

	It is a friendly name for the service. This parameter can be modified through a configuration file directive.

- **sessions** "session list"

	It is a list of the session objects registered in zproxy.

- **status** "string"

	It informs about the listener status. It can be *active* or *down* (if it is disabled).	It can be modified through the API.

#### Session Object

- **backend-id** "integer"

	It is the backend id to which the session is pinned.

- **id** "integer"

	It is a unique identifier for the session.

- **last-seen** "integer"

	It is the number of seconds since the last packet regarding this session was managed by zproxy.

#### Backend Object

- **2xx-code-hits** "integer"

	It is the number of 2xx codes that the zproxy forwarded from the backend to the client.

- **3xx-code-hits** "integer"

	It is the number of 3xx codes that the zproxy forwarded from the backend to the client.

- **4xx-code-hits** "integer"

	It is the number of 4xx codes that the zproxy forwarded from the backend to the client.

- **5xx-code-hits** "integer"

	It is the number of 5xx codes that the zproxy forwarded from the backend to the client.

- **address** "string"

	It is the IPv4/IPv6 of the backend. This parameter can be modified through a configuration file directive.

- **connect-time** "floating"

	It is the average time that zproxy takes to connect with this backend.

- **connections** "integer"

	It is the number of currently established connections that zproxy has with this backend.

- **connections-limit** "integer"

	It is the number of maximum concurrent connections that zproxy will send to this backend. This parameter can be modified through a configuration file directive.

- **https** "bool"

	It informs if the backend is configured with SSL. This parameter can be modified through a configuration file directive.

- **id** "integer"

	It is the backend identifier.

- **name** "string"

	It is a friendly name for the backend. This parameter can be modified through a configuration file directive.

- **pending-connections** "integer"

	It is the number of connections that were sent to this backend and they are not accepted yet.

- **port** "integer"

	It is the port in the backend where zproxy will send the HTTP requests. This parameter can be modified through a configuration file directive.

- **response-time** "floating"

	It is the average of seconds that a backend takes to respond a request

- **status** "string"

	It informs about the backend status. It can be *active* or *down* (if it is disabled).	It can be modified through the API.

- **type** "integer"

	It informs about the kind of backend 0 (it's a remote backend) or 1 (it's a redirect).

- **weight** "integer"

	It is a value to select more a backend than others. This parameter can be modified through a configuration file directive.




### Examples of the API usage

**Reload current configuration file.**

```bash
curl -X PATCH  --unix-socket /tmp/zproxy.socket http://localhost/config
[{"result":"ok"}]
```

**Get the status of a listener and its objects.**

GET <http://localhost/listener/0

```bash
curl --unix-socket /tmp/zproxy.socket http://localhost/listener/0/services
{
  "3xx-code-hits": 0,
  "4xx-code-hits": 2,
  "5xx-code-hits": 0,
  "address": "0.0.0.0",
  "connections": 0,
  "https": false,
  "id": 0,
  "name": "env",
  "pending-connections": 0,
  "port": 8080,
  "services": [
    {
      "backends": [
        {
          "2xx-code-hits": 0,
          "3xx-code-hits": 0,
          "4xx-code-hits": 1,
          "5xx-code-hits": 0,
          "address": "127.0.0.1",
          "connect-time": 0.004252,
          "connections": 0,
          "connections-limit": 0,
          "https": false,
          "id": 0,
          "name": "bck_0",
          "pending-connections": 0,
          "port": 80,
          "priority": 1,
          "response-time": 0.000268,
          "status": "active",
          "type": 0,
          "weight": 9
        }
      ],
      "id": 0,
      "name": "default",
      "sessions": [
                {"backend-id": 2,"id": "127.0.0.1","last-seen": 1540807787}
            ],
      "priority": 0,
      "sessions": [],
      "status": "active"
    },
    {
      "backends": [
        {
          "2xx-code-hits": 1,
          "3xx-code-hits": 0,
          "4xx-code-hits": 1,
          "5xx-code-hits": 0,
          "address": "127.0.0.1",
          "connect-time": 0.003715,
          "connections": 0,
          "connections-limit": 0,
          "https": false,
          "id": 0,
          "name": "bck_0",
          "pending-connections": 0,
          "port": 80,
          "priority": 1,
          "response-time": 0.001529,
          "status": "active",
          "type": 0,
          "weight": 1
        }
      ],
      "id": 1,
      "name": "default",
      "priority": 0,
      "sessions": [],
      "status": "active"
    }
  ],
  "status": "active",
  "waf-hits": 2
}
```

**Get the status of the services**

```bash
curl --unix-socket /tmp/zproxy.socket http://localhost/listener/0/service/0/status
{"result":"ok"}
```

**Disable a backend**

```bash
curl -X PATCH --data-ascii '{"status": "disabled"}'  --unix-socket /tmp/zproxy.socket http://localhost/listener/0/service/0/backend/0/status
{"result":"ok"}
```

**Flush service sessions**

```
$ curl -X DELETE --data-binary '{"backend-id" : 0}' --unix-socket /tmp/simple_https.socket  http://localhost/listener/0/service/0/session
```


**Flush service sessions for backend id**

```
$ curl -X DELETE --unix-socket /tmp/simple_https.socket  http://localhost/listener/0/service/0/session
```


**Delete service session with id "value**

```
$ curl -X DELETE --data-binary '{"id" : "value"}' --unix-socket /tmp/simple_https.socket  http://localhost/listener/0/service/0/session
```

**Create new session**

```
$ curl -X PUT --data-ascii '{"backend-id": 0,"id": "ba2","last-seen": 1593307875}'  --unix-socket /tmp/simple_https.socket http://localhost/listener/0/service/0/sessions
```

**get low level debug info**

```
curl -s --unix-socket /tmp/zproxy.socket  http://localhost/debug
```

**Add backend to service in runtime**

```
curl -X PUT --data-ascii '{"id": "1", "name": "bck", "address": "127.0.0.1", "port": 8000, "weight": 5}'  --unix-socket /tmp/zproxy.socket http://localhost/listener/0/service/0/backends
```

#### Other binaries

Ctl:

- The ctl compile into a single binary zproxyctl, please checkout the zproxyctl manpage to use it.

Tests:

* Tests compile into a single binary `zproxytest` that is run on a command line to run the tests.
* In addition, we support multiple functional tests.

**Functional tests requirements**

- Perl 5.

- Term::ANSIColor perl module

- JSON perl module

- Getopt::Long perl module (It should be installed by default)

- Digest::MD5 perl module

- Digest::MD5::File perl module

- curl

- docker

**Functional tests arguments**

- -http_cfg_file : Path to the config file used by zproxy in the HTTP tests. Default: test_http.cfg

- -https_cfg_file : Path to the config file used by zproxy in the HTTPS tests. Default: test_https.cfg

- -ip : Destination IP/URL used to do the requests. Default: localhost

- -port : Port used to do the requests in the HTTP tests. Default: 8000

- -port_https : Port used to do the requests in the HTTPS tests. Default: 8443

- -post_file : Path to the custom file to be send in the POST request tests. Default: data/test_text.txt

- -binary : Path to the zproxy binary. Default: ../build/bin/zproxy

- -https : If this flag is set the HTTPS tests are going to be executed.

- -no_zproxy : If this flag is set, zproxy is not going to be launched.

- -control : Path to the control socket used to test de API. Default: /tmp/zproxy.socket

**Usage examples**

```bash
# Runs the functional tests over the backend without starting zproxy.
zproxy_functional_tests -no_zproxy

# Runs the functional tests enabling HTTPS tests
zproxy_functional_tests -https

# Runs the functional tests over the backend without starting zproxy, setting a different ip and port.
zproxy_functional_tests -https -no_zproxy -ip 192.168.100.20 -port 8080 -port_https 8443
```
#### Benchmark

The tests below was done using two backends running nginx and a running zproxy / pound / haproxy in an Intel  i5-6500, 4G RAM, 16 GB MSata.

zproxy result:
```bash
Running 15s test @ http://172.16.1.1:80/hello.html
  10 threads and 400 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency     8.13ms   63.38ms   1.01s    98.68%
    Req/Sec    23.97k     3.25k   56.34k    94.30%
  3599282 requests in 15.10s, 0.93GB read
  Socket errors: connect 0, read 1, write 0, timeout 0
Requests/sec: 238374.98
Transfer/sec:     63.19MB
```
haproxy result:
```bash
Running 15s test @ http://172.16.1.1:83/hello.html
  10 threads and 400 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency    97.55ms  235.66ms   1.24s    87.56%
    Req/Sec    14.93k     2.26k   30.92k    80.93%
  2243804 requests in 15.10s, 543.52MB read
  Socket errors: connect 0, read 0, write 0, timeout 7
Requests/sec: 148604.42
Transfer/sec:     36.00MB
```

pound reverse proxy result:
```bash
Running 15s test @ http://172.16.1.1:80/hello.html
  10 threads and 400 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency     5.97ms   21.62ms 275.10ms   95.73%
    Req/Sec    11.28k     9.22k   65.39k    59.49%
  834725 requests in 15.10s, 221.31MB read
Requests/sec:  55281.33
Transfer/sec:     14.66MB
```

Comparing Requests/sec and latency, results are very impressive, zproxy is almost 100k requests per second faster than haproxy and almost 4,3 times faster than pound.


#### Contributing

**Pull Requests are WELCOME!** Please submit any fixes or improvements:

* [Project Github Home](https://github.com/zevenet/zproxy)
* [Submit Issues](https://github.com/zevenet/zproxy/issues)
* [Pull Requests](https://github.com/zevenet/zproxy/pulls)

### License

&copy; 2019 ZEVENET.
AGPL-3.0.

### Authors

ZEVENET Team
