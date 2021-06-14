# Description

This test tool deploy a lab with N clients and M backends in order to apply
different proxy configuration files and analyze its HTTP responses.

# Getting Started

The following steps are required to configure the test application:

* Adding the variables file. This file contains all the environment configuration

`cp tpl/variables.ini variables`

* Setting up the benchmark reference. This measure is used to comparate with other benchmark tests to determine the proxy efficiency.
During the test execution, an alert could appear if the performance increases more or decreases less than an error range

`./test.sh bck_benchmark`

* The value printed by the previous command has to be configured in the variable **BENCH_WITHOUT_PROXY** (file variables)

* The tests are now configured, just coding confident executing it:

`./test.sh all`

*Note*: For more options check the command: `./test.sh -h`



# Files

This is a description of the files that can be found in this test directory

- variables: They are the variables to configure the lab and tests

- lib: They are the functions used by the test.sh script

- exec.sh: It is a macro to execute only one function from the lib file

- test.sh: It is the main script, it is the test launcher

- tests/

	- <test_name>/

		- zproxy.cfg : If this file exists, the proxy service is STARTED with this config file

		- reload_zproxy.cfg : first is loaded the zproxy.cfg and after this file is reloaded to overwrite de configuration

		- ctl.in  : they are the parameter for the request to the ctl service, the body is in another file

		- ctl.json: it is the body of the request to the ctl service

		- ctl.out  : it is the response of the request to the ctl service

		- test.in: It is a configuration file that defines the command executed for this test. See the *tests define* section

		- test_N.out : it is the output of executing the exec.sh script

		- test_N.out.tmp : it is the temporal file used to comparate with *test_N.out*

		- test_N.out.new : it is the benchmark result if this was better

- report.tmp: It is the report generated after executing the tests

- tpl: They are files used to configure the test environment

# How to add a new test

At the beginning of each test, the zproxy will be restarted or reloaded if the test directory contains the files **zproxy.cfg** or **reload_zproxy**, else the test will continue with the last started zproxy.

The files **test.in** define the commands that will be executed in order to try the zproxy daemon. This file has sequential blocks separated by the line '###' and they contain the following parameters regarding the command to execute:


## test.in

Several directives have been created, these can execute requests (curl, average, wrk, benchmark) or apply configuration (ctl, reload) or control actions (wait, killwrk).


### wait

It orders to the test tool to wait N seconds

| Parameter      | Description     | Required |
| ----------- | ----------- | ----------- |
| DESCRIPTION   | This parameter is not used. It is a commentary to add more information about the executed command |
| CMD      | It is the command to execute. *wait* should be defined to wait N seconds. This is useful as grace time after execute some command that required time to consolidate it | True
| TIMEOUT      | It is the time in seconds to wait | True

```
CMD=wait
TIMEOUT=1
DESCRIPTION="Grace time to wait the configuration will be reloaded"
```

### killwrk

It kills all wrk processes that are running in background

| Parameter      | Description     | Required |
| ----------- | ----------- | ----------- |
| DESCRIPTION   | This parameter is not used. It is a commentary to add more information about the executed command |
| CMD      | It is the command to execute. *killwrk* should be defined to kill al the wrk background processes | True

```
CMD=killwrk
DESCRIPTION="kill the wrk used to feed the stats"
```

### ctl

It executes an API request and dumps the configuration if the request don't have the GET method

| Parameter      | Description     | Required |
| ----------- | ----------- | ----------- |
| DESCRIPTION   | This parameter is not used. It is a commentary to add more information about the executed command |
| CMD      | It is the command to execute. *ctl* should be defined to send a request to the zproxy API | True
| METHOD   | It is the HTTP method used in the request to the zproxy API | True
| URL  	 	| It is the HTTP URL used in the request to the zproxy API | True
| BODY  	| It is the HTTP body sent in the request. It has to be saved in a file | True

```
CMD=ctl
METHOD="PATCH"
BODY=ctl.json
URL="/listener/0/service/0/backend/0/status"
DESCRIPTION="Disable the backend 0 in the service 0"
```

### reload

It is a macro of the ctl command to simplify the configuration reload.

| Parameter      | Description     | Required |
| ----------- | ----------- | ----------- |
| DESCRIPTION   | This parameter is not used. It is a commentary to add more information about the executed command |
| CMD      | It is the command to execute. *reload* should be defined to reload the proxy configuration from a file | True
| FILE      | It is a zproxy configuration file that will be loaded without restart the proxy process | True

```
CMD=reload
FILE="zproxy_new.cfg"
DESCRIPTION="Disable the backend 0 in the service 0"
```

### curl

| Parameter      | Description     | Required |
| ----------- | ----------- | ----------- |
| DESCRIPTION   | This parameter is not used. It is a commentary to add more information about the executed command |
| CMD      | It is the command to execute. *curl* should be defined for a simple HTTP(S) request | True
| CL      | It is the client ID that will execute the command       | True
| METHOD      | It is the HTTP Verb used for the request (GET, POST, PUT..)      | True
| URL      | It is the HTTP URL used for the request (/, /svc...)       | True
| VHOST      | It is the virtual hostname, it will be put in the URL. If it is not defined the virtual IP and virtual port will be used instead. This vhost is added to the curl command in order to be resolved. |
| SSL      | If this flag is set with **1** the request will use the HTTPS protocol |
| HEADERS     | It is a list of headers to add in the request. If more than one headers will be added, they should be separated by the character comma ';'       |
| BODY      | They are the data to send in the HTTP body. It should be a file in the same directory. *FILE* and *BODY* parameters are not compatible       |
| FILE      | It is a file that will be upload. It should be a file in the same directory. *FILE* and *BODY* parameters are not compatible       |
| BACKGROUND     | If this flag is set with **1** the request will be executed in background. The command **killwrk** can be defined to stop it |

```
DESCRIPTION="it executes the curl command 'curl -X GET https//service.test/' in the client 1"
CMD=curl
CL=1
METHOD="GET"
URL="/"
VHOST=service.test
SSL=1
```

### average

It executes the same *curl* command N times. It is useful to get metrics about algorithms, sessions...
It executes the curls sequentially.

| Parameter      | Description     | Required |
| ----------- | ----------- | ----------- |
| DESCRIPTION   | This parameter is not used. It is a commentary to add more information about the executed command |
| CMD      | It is the command to execute. *average* executes a set of curls in order to get an output average | True
| CL      | It is the client ID that will execute the command       | True
| METHOD  | It is the HTTP Verb used for the request (GET, POST, PUT..)      | True
| URL     | It is the HTTP URL used for the request (/, /svc...)       | True
| VHOST   | It is the virtual hostname, it will be put in the URL. If it is not defined the virtual IP and virtual port will be used instead. This vhost is added to the curl command in order to be resolved. |
| SSL      | If this flag is set with **1** the request will use the HTTPS protocol |
| HEADERS     | It is a list of headers to add in the request. If more than one headers will be added, they should be separated by the character comma ';'       |
| BODY      | They are the data to send in the HTTP body. It should be a file in the same directory. *FILE* and *BODY* parameters are not compatible       |
| FILE      | It is a file that will be upload. It should be a file in the same directory. *FILE* and *BODY* parameters are not compatible       |
| REQUESTS  | It is the number of times to execute the curl      |
| BACKGROUND     | If this flag is set with **1** the request will be executed in background. The command **killwrk** can be defined to stop it |


```
DESCRIPTION="it executes the curl command 'curl -X GET http//zproxy/index.html' in the client 1 four times"
CMD=average
CL=1
REQUESTS=4
METHOD="GET"
VHOST="zproxy"
URL="/index.html"
```

### wrk

It executes the wrk tool in order to create a stable flow of connections and requests.
This can be executed in bg to check the zproxy stats

| Parameter      | Description     | Required |
| ----------- | ----------- | ----------- |
| DESCRIPTION   | This parameter is not used. It is a commentary to add more information about the executed command |
| CMD      | It is the command to execute. *wrk* executes the wrk tool in order to get a stable number of concurrent connections  | True
| CL      | It is the client ID that will execute the command       | True
| URL      | It is the HTTP URL used for the request (/, /svc...)       | True
| VHOST      | It is the virtual hostname, it will be put in the URL. If it is not defined the virtual IP and virtual port will be used instead. This vhost is added to the curl command in order to be resolved. |
| CONNS      | Number of concurrent connections that are managed by the client | True
| TIMEOUT      | Time for the test | True
| THREADS      | If this flag is set with **1** the request will use the HTTPS protocol | True
| SSL      | If this flag is set with **1** the request will use the HTTPS protocol |
| BACKGROUND     | If this flag is set with **1** the request will be executed in background. The command **killwrk** can be defined to stop it |

```
DESCRIPTION="it executes 10 concurrent connections in background to the URI https://vip:vport/"
CMD=wrk
BACKGROUND=1
CL=1
URL="/"
TIMEOUT=20
CONNS=10
THREADS=2
```

### benchmark

It executes the wrk tool and the performance regarding the value without proxy (client->backend).
After the test is approved if the value is not dispersed mor than an error range.

| Parameter      | Description     | Required |
| ----------- | ----------- | ----------- |
| DESCRIPTION   | This parameter is not used. It is a commentary to add more information about the executed command |
| CMD      | It is the command to execute. *benchmark* executes the wrk tool in order to get the number of request/sec that zproxy can manage        | True
| CL      | It is the client ID that will execute the command       | True
| URL      | It is the HTTP URL used for the request (/, /svc...)       | True
| VHOST      | It is the virtual hostname, it will be put in the URL. If it is not defined the virtual IP and virtual port will be used instead. This vhost is added to the curl command in order to be resolved. |
| SSL      | If this flag is set with **1** the request will use the HTTPS protocol |

```
DESCRIPTION="it executes the curl command 'curl -X GET https//service.test/' in the client 1"
CMD=benchmark
CL=1
URL="/"
```

*Note*: Some global parameters used for the benchmark command are modified in the **variables** file, these values are used for all the benchmark tests:

| Parameter      | Description
| ----------- | -----------
| BENCH_CONNS      | Number of concurrent connections opened by the client
| BENCH_DELAY      | It is the number of seconds that the client will send requests
| BENCH_CL_THREADS      | Number of threads used to execute the client
| BENCH_ERR_ACCEPTED	| It is the error range to accept the benchmark as good. It is checked with the value saved in the test file test_N_benchmark.out

# Lab scheme

```
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
```

# Backend responses

All the backend responses include a "Backend" header that identifies which is responding.

The backend responses are managed by the Nginx HTTP echo module.
The following requests are available:

| Method      | URL      | Description
| ----------- | ----------- | -----------
| GET, POST	      			| /					| The server will respond backend ID ignoring the request body
| GET		      			| /download/`<file>`	| The server will respond a static file saved in the tpl download directory
| GET		      			| /body-size/`<tiny,large>`	| **TBI**. The server will respond a static body with a large or tiny size. It is useful to trigger the HTTP fragmented response
| GET		      			| /body-size/`<size>`/chunked	| The server will respond a body of "size" bytes. The response is chunked encoding.
| GET		      			| /client-ip		| The server will respond the client IP
| GET		      			| /sleep-response/`<seconds>`	| The server will wait N seconds before responding
| GET		      			| /sleep-body/`<seconds>`		| The server will send the first body part, will wait N seconds and later will continue sending the body
| GET, POST, PUT, DELETE	| /status/`<code>`	| The server will respond with the code required. The possible codes are: 200, 201, 301, 302, 400, 401, 403, 404, 405, 500, 503
| GET      					| /echo				| The server will add to its body the GET arguments
| POST, PUT 				| /echo				| The server will return the body and content-type that the request send
| GET 						| /headers			| The server will return the request headers in the body.
| POST 						| /headers			| **TBI**.
| DELETE					| /headers/`<header>`	| **TBI**. It deletes the "header" of the response
| GET						| /resp-headers/location/`<value>`	| It adds the location and content-location headers in the backend response
| GET 						| /cookie			| **TBI**. Use CGI or the backend id to build the cookie? backend_id+date?
| POST	 					| /cookie			| **TBI**. Use CGI or the backend id to build the cookie? backend_id+date?
| DELETE 					| /cookie			| **TBI**. Use CGI or the backend id to build the cookie? backend_id+date?

