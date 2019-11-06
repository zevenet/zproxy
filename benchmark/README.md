# ZPROXY benchmark


#### Benchmark

The tests bellow were done using two backends running nginx v.1.10.3-1+deb9u3, and zproxy v0.1.2/ pound 2.8a / haproxy v1.8.19-1 (Debian Buster package) as load balancers.

zproxy result:
```bash
Running 15s test @ http://172.16.1.1:80/hello.html
  10 threads and 400 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency     8.13ms   63.38ms   1.01s    98.68%
    Req/Sec    23.97k     3.25k   56.34k    94.30%
  3599282 requests in 15.10s, 0.93GB read
  Socket errors: connect 0, read 1, write 0, timeout 0
Requests/sec: *238374.98*
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
Requests/sec: *148604.42*
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
Requests/sec:  *55281.33*
Transfer/sec:     14.66MB
```

Comparing Requests/sec and latency, results are very impressive, zproxy is almost 100k requests per second faster than haproxy and almost 4,3 times faster than pound.

This directory contains:
* `zproxy.cfg` — Zproxy and pound configuration file used in the load balancer for this test.
* `haproxy` —  Haproxy configuration file used in the load balancer for this test.


To be neutral, the 3 tests have been executed with the same Client, same load balancer and receiving traffic with the same backends.  

Used hardware in server:  Intel(R) Xeon(R) CPU E3-1245 v5 @ 3.50GHz (8 cores), in Debian Buster Kernel 4.19.37.  
Used hardware in client:  Intel(R) Core(TM) i5-6500 CPU @ 3.20GHz (8 cores), in Debian Buster Kernel 4.19.37.  
Used hardware in backend: Intel(R) Xeon(R) CPU E3-1245 v5 @ 3.50GHz (8 cores), in Debian Buster Kernel 4.19.110.  

The used stress tool is wrk, source code here: https://github.com/wg/wrk.  
Command executed from client for the 3 tests: ./wrk -d 15 -t 10 -c 400 http://172.16.1.1:83/hello.html.   
&nbsp;  -c : Number of connections that the stress tool will keep opened (400)  
&nbsp;  -d : Duration of the test (15 seconds)  
&nbsp;  -t : Number of threads running in the client managing connections (10 threads)  
  
*HTML response of 42 bytes (Content-Length: 42).  
