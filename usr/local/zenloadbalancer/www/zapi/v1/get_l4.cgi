#! /usr/bin/perl -w

########### GET L4XNAT
# curl --tlsv1 -k --header 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/L4FARM
#
#
#
#####Documentation of GET L4XNAT####
#**
#  @api {get} /farms/<farmname> Request info of a l4xnat Farm
#  @apiGroup Farm Get
#  @apiName GetFarmNameL4XNAT
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiDescription Get the Params of a given Farm <farmname> with L4XNAT profile
#  @apiVersion 1.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "backends" : [
#      {
#         "id" : 0,
#         "ip" : "192.168.0.150",
#         "port" : 80,
#         "priority" : 5,
#         "weight" : 2
#      },
#      {
#         "id" : 1,
#         "ip" : "192.168.1.151",
#         "port" : 81,
#         "priority" : 1,
#         "weight" : 1
#      }
#   ],
#   "description" : "List farm L4FARM",
#   "params" : [
#      {
#         "algorithm" : "prio",
#         "fgenabled" : "true",
#         "fgtimecheck" : 5,
#         "fglog" : "true",
#         "fgscript" : "Farm Guardian",
#         "nattype" : "nat",
#         "persistence" : "ip",
#         "protocol" : "tcp",
#         "ttl" : 125,
#         "vip" : "192.168.0.161",
#         "vport" : 81
#      }
#   ]
#}
#
# @apiExample {curl} Example Usage:
#	curl --tlsv1 -k --header 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>" 
#	-u zapi:<password> https://<zenlb_server:444/zapi/v1/zapi.cgi/farms/L4FARM
#
# @apiSampleRequest off
#
#**

our $origin;
if ($origin ne 1){
    exit;
}

sub farms_name_l4(){

########### params
use CGI;
my $q = CGI->new;

my $out_p = [];
my $out_b = [];

$vip = &getFarmVip("vip",$1);
$vport = &getFarmVip("vipp",$1);
$vport = $vport + 0;
@ttl = &getFarmMaxClientTime($1,"");
$timetolimit = @ttl[0] + 0;
##FG
@fgconfig = &getFarmGuardianConf($1,"");
$fguse = @fgconfig[3];
$fgcommand = @fgconfig[2];
$fgtimecheck = @fgconfig[1] + 0;
$fglog = @fgconfig[4];

push $out_p, { vip => $vip, vport => $vport, algorithm => &getFarmAlgorithm($1), nattype => &getFarmNatType($1), persistence => &getFarmPersistence($1), protocol => &getFarmProto($1), ttl =>  $timetolimit , fgenabled => $fguse, fgtimecheck => $fgtimecheck, fgscript => $fgcommand, fglog => $fglog };

########### backends

my @run = &getFarmServers($1);
foreach $l_servers(@run){
        my @l_serv = split(";",$l_servers);
	$l_serv[0] = $l_serv[0] + 0;
	$l_serv[1] = $l_serv[1];
	$l_serv[2] = $l_serv[2] + 0;
	$l_serv[3] = $l_serv[3] + 0;
	$l_serv[4] = $l_serv[4] + 0;
	$l_serv[5] = $l_serv[5] + 0;
        if ($l_serv[1] ne "0.0.0.0"){
            push $out_b, { id => $l_serv[0], ip => $l_serv[1], port => @l_serv[2], weight => @l_serv[4], priority => @l_serv[5] };
        }
}

########### print JSON
print $q->header(
    -type=> 'text/plain',
    -charset=> 'utf-8',
    -status=> '200 OK'
);

my $j = JSON::XS->new->utf8->pretty(1);
$j->canonical($enabled);
my $output = $j->encode({
    description => "List farm $1",
    params => $out_p,
    backends => $out_b
});

print $output;


}

1




