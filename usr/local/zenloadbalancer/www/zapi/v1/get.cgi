#!/usr/bin/perl -w

require "/usr/local/zenloadbalancer/www/zapi/v1/get_tcp.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v1/get_http.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v1/get_gslb.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v1/get_l4.cgi";
require "/usr/local/zenloadbalancer/www/zapi/v1/get_datalink.cgi";

our $origin;
if ($origin ne 1){
   exit;
}

#**
#  @api {get} /farms Request farms list
#  @apiGroup Farm Get
#  @apiDescription Get the list of all Farms
#  @apiName GetFarmList
#  @apiVersion 1.0.0
#  
# 
# @apiSuccessExample Success-Response:
#{
#   "description" : "List farms",
#   "params" : [
#      {
#         "farmname" : "newfarmGSLB55",
#         "profile" : "gslb",
#         "status" : "up"
#      }
#   ]
#}
#@apiExample {curl} Example Usage:
#	curl --tlsv1  -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>
#	-u zapi:<password> https://<zenlb_server>:444/zapi/v1/zapi.cgi/farms
# 
#@apiSampleRequest off
#**
#GET /farms
sub farms() {

use CGI;
my $q = CGI->new;

my $out = [];
@files = &getFarmList();
foreach $file (@files){
        $name = &getFarmName($file);
        $type = &getFarmType($name);
       $status = &getFarmStatus($name);
       push $out, { farmname => $name, profile => $type , status => $status};

}
# Success
print $q->header(
    -type=> 'text/plain',
    -charset=> 'utf-8',
    -status=> '200 OK'
);

my $j = JSON::XS->new->utf8->pretty(1);
$j->canonical([$enabled]);
my $output = $j->encode({
    description => "List farms",
    params => $out
});
print $output;
}

#GET /farms/<name>
sub farms_name() {

use Switch;
use CGI;
my $q = CGI->new;
my $j = JSON::XS->new->utf8->pretty(1);
$j->canonical([$enabled]);

# Check that the farm exists
if ( &getFarmFile( $1 ) == -1 ) {
	# Error
	print $q->header(
	-type=> 'text/plain',
	-charset=> 'utf-8',
	-status=> '404 Not Found'
	);
	$errormsg = "The farmname $1 does not exist.";
	my $output = $j->encode({
			description => "Get farm",
			error => "true",
			message => $errormsg
	});
	print $output;
	exit;

}


my $type = &getFarmType($1);

switch ($type) {
	case /tcp|udp/	{ &farms_name_tcp() }
	case /http.*/	{ &farms_name_http() }
	case /gslb/	{ &farms_name_gslb() }
	case /l4xnat/	{ &farms_name_l4() }
	case /datalink/ { &farms_name_datalink() }

}
}

#**
#  @api {get} /stats Request system statistics
#  @apiGroup System Stats
#  @apiDescription Get the system's stats
#  @apiName GetStats
#  @apiVersion 1.0.0
#  
# 
# @apiSuccessExample Success-Response:
#{
#   "description" : "System stats",
#   "params" : [
#      {
#         "hostname" : "zvclouddev01"
#      },
#      {
#         "date" : "Wed Mar 18 16:17:09 2015"
#      },
#      {
#         "MemTotal" : 497.02
#      },
#      {
#         "MemFree" : 58.7
#      },
#      {
#         "MemUsed" : 438.32
#      },
#      {
#         "Buffers" : 103.57
#      },
#      {
#         "Cached" : 162.53
#      },
#      {
#         "SwapTotal" : 0
#      },
#      {
#         "SwapFree" : 0
#      },
#      {
#         "SwapUsed" : 0
#      },
#      {
#         "Last" : 0.05
#      },
#      {
#         "Last 5" : 0.04
#      },
#      {
#         "Last 15" : 0.05
#      },
#      {
#         "CPUuser" : 2
#      },
#      {
#         "CPUnice" : 0
#      },
#      {
#         "CPUsys" : 3
#      },
#      {
#         "CPUiowait" : 0
#      },
#      {
#         "CPUirq" : 0
#      },
#      {
#         "CPUsoftirq" : 0
#      },
#      {
#         "CPUidle" : 95
#      },
#      {
#         "CPUusage" : 5
#      },
#      {
#         "eth0 in" : 527.57
#      },
#      {
#         "eth0 out" : 592.84
#      }
#   ]
#}

#@apiExample {curl} Example Usage:
#       curl --tlsv1  -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING> \
#       -u zapi:<password> https://<zenlb_server>:444/zapi/v1/zapi.cgi/stats
# 
#@apiSampleRequest off
#**


#GET /stats
sub stats() {

use CGI;
my $q = CGI->new;

my $out = [];
my ($x,$y);

my @data_mem = &getMemStats();
my @data_load = &getLoadStats();
my @data_net = &getNetworkStats();
my @data_cpu = &getCPU();



#date
push $out, { 'hostname' => &getHostname()};
push $out, { 'date' => &getDate()};
#splice $out, $#out, 0, { 'date' => &getDate()};



foreach $x (0..@data_mem-1){

	$name = $data_mem[$x][0];
	$value = $data_mem[$x][1]+0;
       push $out, { $name => $value};

}

foreach $x (0..@data_load-1){

        $name = $data_load[$x][0];
        $value = $data_load[$x][1]+0;
        push $out, { $name => $value};

}

foreach $x ( 0 .. @data_cpu-1 ){
                $name = $data_cpu[$x][0];
                $value = $data_cpu[$x][1]+0;
                push $out, { $name => $value};
        }

foreach $x ( 0 .. @data_net-1 ){
		
		if ( $x % 2 == 0){
                	$name = $data_net[$x][0] .' in';

		}else{
                	$name = $data_net[$x][0] .' out';

		}
                $value = $data_net[$x][1]+0;
                push $out, { $name => $value};
        }


# Success
print $q->header(
    -type=> 'text/plain',
    -charset=> 'utf-8',
    -status=> '200 OK'
);

my $j = JSON::XS->new->utf8->pretty(1);
$j->canonical([$enabled]);
my $output = $j->encode({
    description => "System stats",
    params => $out
});
print $output;



}

1
