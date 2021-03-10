# Description
This test tool deploy a lab with N clients and M backends in order to apply
different proxy configuration files and analyze its HTTP responses.

# Files
variables: They are the variables to configure the lab and tests
lib: They are the functions used by the test.sh script
exec.sh: It is a macro to execute only one function from the lib file
test.sh: main script, it is the test launcher
tests/
	<test_name>/
		zproxy.cfg : If this file exists, the proxy service is STARTED with this config file
		reload_zproxy.cfg : first is loaded the zproxy.cfg and after this file is reloaded to overwrite de cfg
		ctl.in  : they are the parameter for the request to the ctl service, the body is in other file **TBI**
		ctl.json: it is the body of the request to the ctl service **TBI**
		ctl.out  : it is the response of the request to the ctl service **TBI**
		test.in: It is a configuration file that defines the command executed for this test. See the *tests define* section.
		test_N.out : it is the output of executing the exec.sh script
		test_N.out.tmp : it is the tmp file used to comparate with *test_N.out*
		test_N.out.new : it is the benchmark result if this was better
report.tmp: It is the report generated after executing the tests
tpl: They are files used to configure the test envirovement

# Test define
The files **test.in** define the commands that will be executed in order to try the proxy daemon
after restarting or reloading its configuration.

This file are sequential blocks splitted by the line '###' and they contain the
following parameters regarding the command to execute:

## test.in

| Parameter      | Description     | Required |
| ----------- | ----------- | ----------- |
| CMD      | It is the command to execute. *curl* should be defined for a simple HTTP(S) request; *average* executes a set of curls in order to get an output average; *benchmark* executes the wrk tool in order to get the number of request/sec that zproxy can manage        | True
| CL      | It is the client ID that will execute the command       | True
| METHOD      | It is the HTTP Verb used for the request (GET, POST, PUT..)      | True
| URL      | It is the HTTP URL used for the request (/, /svc...)       | True
| VHOST      | It is the virtual hostname, it will be put in the URL. If it is not defined the virtual IP and virtual port will be used instead. This vhost is added to the curl command in order to be resolved. |
| SSL      | If this flag is set with **1** the request will use the HTTPS protocol |
| HEADERS     | TBI       |
| BODY      | TBI       |

```
CMD=curl
CL=1
METHOD="GET"
URL="/"
VHOST=service.test
SSL=1
```

*Note*: Some global benchmark parameters can be modified in the **variables** file:

| Parameter      | Description
| ----------- | -----------
| BENCH_CONNS      | Number of concurrent connections opened by the client
| BENCH_DELAY      | It is the number of seconds that the client will send requests
| BENCH_CL_THREADS      | Number of threads used to execute the client
| BENCH_ERR_ACCEPTED	| It is the error range to accept the benchmark as good. It is check with the value saved in the test file test_N_benchmark.out

# Lab scheme

	host

               ---------  ---------     ---------
               |  cl1  |  |  cl2  |     |  clN  |
   Clents      |(vcl1) |  |(vcl2) | ... |(vclN) |     (10.1.1.X/16)
               ---------  ---------     ---------
                    |         |             |
             --------------------------------------
             |   (vcl1)     (vcl2)  ...   (vclN)  |  (10.1.0.X/16) client gw
   Proxy     |              (VIP)                 |  (10.1.2.1/16) vip
             |                                    |
             | (vbck1)      (vbck2) ...  (vbckN)  |  (10.2.0.X/16) proxy_back
             --------------------------------------   There is a routing rule for each backend
                   |           |            |
               ---------  ---------     ---------
               |  bk1  |  |  bk2  | ... |  bkN  |
   Backends    |(vbck1)|  |(vbck2)|     |(vbckN)|     (10.2.1.X/16)
               ---------  ---------     ---------

# Backend responses

All the backend responses incluid the "backend" header that.

The backend responses are managed by the Nginx HTTP echo module.
The following requests are available:

| Method      | URL      | Description
| ----------- | ----------- | -----------
| GET, POST	      			| /					| The server will respond backend ID ignoring the request body
| GET		      			| /body-size/<tiny|large>	| **TBI**. The server will respond a static body with a large or tiny size. It is useful to trigger the HTTP fragmented response
| GET		      			| /body-size/<size>/chunked	| The server will respond a body of "size" bytes. The response is chunked encoding.
| GET		      			| /client-ip		| The server will respond the client IP
| GET		      			| /sleep-resonse/<seconds>	| The server will wait N seconds before responding
| GET		      			| /sleep-body/<seconds>		| The server will send the first body part, will wait N seconds and later will continue sending the body
| GET, POST, PUT, DELETE	| /status/<code>	| The server will respond with the code required. The possible codes are: 200, 201, 301, 302, 400, 401, 403, 404, 405, 500, 503
| GET      					| /echo				| The server will add to its body the GET arguments
| POST, PUT 				| /echo				| The server will return the body and content-type that the request send
| POST 						| /headers			| **TBI**.
| DELETE					| /headers/<header>	| **TBI**. It deletes the "header" of the response
| GET 						| /cookie			| **TBI**. Use CGI or the backend id to build the cookie? backend_id+date?
| POST	 					| /cookie			| **TBI**. Use CGI or the backend id to build the cookie? backend_id+date?
| DELETE 					| /cookie			| **TBI**. Use CGI or the backend id to build the cookie? backend_id+date?

