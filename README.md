# ZPROXY

Zevenet zproxy is a high-performance multithreaded and event-driven L7 reverse proxy and load balancer inspired by Pound reverse proxy simplicity.

zproxy main features:

    * HTTP, HTTPS handling
    * Pound load balancer configuration file compatibility.
    * Managed by REST API requests in JSON format.
    * Load balancing algorithms: Round Robin, Least Connections, Response Time, Pending Connections
    * Connection pinning.
    * Backend output traffic marking.
    * Simple HTTP Caching - WIP
    * Pound control interface like binary (zproxyctl)


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
* `test/lib` — C++ libraries used for tests ( Google Test).
* `test/src` — C++ test suite.
* `cmake/*` — Cmake input files.
* `docs/` _ Doxygen configuration file (Doxyfile) and man pages.

#### Quick start guide

By following this guide you will end up having a zproxy deployed and running.

1. Download and build zproxy.

2. Take one of the example configuration files at `tests/data`. It is recommended to use `simple_http.cfg` or `simple_https.cfg` and modify it to use your infrastructure.

3. Run `$ bin/zproxy -f /path/to/config_file.cfg`

4. Now it is ready! You can check the global proxy status by using the control API.

## API Description


*All request must be directed to the zproxy unix socket or to the control IP address and port. The response is going to be a JSON formatted response with all the information requested or the operation result.*

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


- Examples of the API usage

**Get all the services status.**

GET <http://localhost/listener/0/services>

```bash
curl --unix-socket /tmp/zproxy.socket http://localhost/listener/0/services
{
    "address": "0.0.0.0",
    "port": 9999,
    "services": [
        {
            "backends": [
                {
                    "address": "192.168.0.253",
                    "connect-time": 0.0,
                    "connections": 0,
                    "id": 1,
                    "name": "bck_1",
                    "pending-connections": 0,
                    "port": 80,
                    "response-time": -1.0,
                    "status": "active",
                    "weight": 5
                },
                {
                    "address": "192.168.0.254",
                    "connect-time": 0.0,
                    "connections": 0,
                    "id": 2,
                    "name": "bck_2",
                    "pending-connections": 0,
                    "port": 80,
                    "response-time": 0.007924,
                    "status": "active",
                    "weight": 6
                }
            ],
            "id": 1,
            "name": "srv1",
            "sessions": [
                {"backend-id": 2,"id": "127.0.0.1","last-seen": 1540807787}
            ],
            "status": "active"
        },
        {
            "backends": [
                {
                    "address": "192.168.0.253",
                    "connect-time": 0.0,
                    "connections": 0,
                    "id": 1,
                    "name": "bck_1",
                    "pending-connections": 0,
                    "port": 80,
                    "response-time": -1.0,
                    "status": "active",
                    "weight": 5
                },
                {
                    "address": "192.168.0.254",
                    "connect-time": 0.0,
                    "connections": 0,
                    "id": 2,
                    "name": "bck_2",
                    "pending-connections": 0,
                    "port": 80,
                    "response-time": -1.0,
                    "status": "active",
                    "weight": 6
                }
            ],
            "id": 2,
            "name": "srv2",
            "sessions": [],
            "status": "active"
        }
    ]
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
**Insert new session to service **
```bash
curl -X PUT --data-ascii '{"backend-id": 1,"id": "127.0.0.1","last-seen": 1570807787}'  --unix-socket //tmp/zproxy.socket http://localhost/listener/0/service/0/sessions
{"result":"ok"}
```


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

* [Project Github Home](https://github.com/abdessamad-zevenet/zproxy)
* [Submit Issues](https://github.com/abdessamad-zevenet/zproxy/issues)
* [Pull Requests](https://github.com/abdessamad-zevenet/zproxy/pulls)

### License

&copy; 2019 Zevenet.
AGPL-3.0.

### Authors

Zevenet Team 
