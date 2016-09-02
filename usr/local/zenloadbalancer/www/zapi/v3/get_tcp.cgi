#!/usr/bin/perl -w

########## GET TCP
# curl tlsv1 -k --header 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/FARMTCP
#
#
#
#####Documentation of GET TCP|UDP####
#**
#  @api {get} /farms/<farmname> Request info of a tcp|udp Farm
#  @apiGroup Farm Get
#  @apiName GetFarmNameTCP
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiDescription Get the Params of a given Farm <farmname> with TCP or UDP profile
#  @apiVersion 2.1.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "backends" : [
#      {
#         "id" : 1,
#         "ip" : "192.68.1.161",
#         "maxconns" : 1001,
#         "port" : 80,
#         "priority" : 2,
#         "weight" : 1
#      },
#      {
#         "id" : 2,
#         "ip" : "192.68.0.160",
#         "maxconns" : 1001,
#         "port" : 81,
#         "priority" : 5,
#         "weight" : 2
#      }
#   ],
#   "description" : "List farm FarmTCP",
#   "params" : [
#      {
#         "algorithm" : "prio",
#         "timeout" : 5,
#         "fgenabled" : "true",
#         "fglog" : "true",
#         "fgscript" : "Farm Guardian",
#         "fgtimecheck" : 5,
#         "maxservers" : 10,
#         "maxclients" : 2049,
#         "tracking" : 10,
#         "connmax" : 257,
#         "persistence" : "false",
#         "blacklist" : 40,
#         "vip" : "178.62.126.152",
#         "vport" : 54321,
#         "xforwardedfor" : "true"
#      }
#   ]
#}
#
#@apiExample {curl} Example Usage:
#       curl tlsv1 -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#       -u zapi:<password>  https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/FarmTCP
#
#@apiSampleRequest off
#
#**

our $origin;
if ( $origin ne 1 )
{
	exit;
}

sub farms_name_tcp()
{

	use CGI;
	my $q = CGI->new;

	my $out_p = [];
	my $out_b = [];
##
	my $algo       = &getFarmAlgorithm( $1 );
	my @array      = &getFarmMaxClientTime( $1 );
	my $maxclients = @array[0];
	my $maxtimemem = @array[1];
	chomp ( $maxclients );
	chomp ( $maxtimemem );
	$maxtimemem = $maxtimemem + 0;
	$maxclients = $maxclients + 0;
	my $timeout = &getFarmTimeout( $1 );
	$timeout = $timeout + 0;
	my $conn_max = &getFarmMaxConn( $1 );
	chomp ( $conn_max );
	$conn_max = $conn_max + 0;
	my $maxbackends = &getFarmMaxServers( $1 );
	my $blacklist   = &getFarmBlacklistTime( $1 );
	$blacklist = $blacklist + 0;
	my $xforw = &getFarmXForwFor( $1 );

	if ( $xforw == -1 )
	{
		$xforw = "false";
	}
###FG
	@fgconfig  = &getFarmGuardianConf( $1, "" );
	$fgttcheck = @fgconfig[1];
	$fgttcheck = $fgttcheck + 0;
	$fgscript  = @fgconfig[2];
	$fgscript =~ s/\n//g;
	$fgscript =~ s/\"/\'/g;
	$fguse = @fgconfig[3];
	$fguse =~ s/\n//g;
	$fglog = @fgconfig[4];
###
	$vip   = &getFarmVip( "vip",  $1 );
	$vport = &getFarmVip( "vipp", $1 );
	$vport = $vport + 0;

	push $out_p,
	  {
		algorithm     => &getFarmAlgorithm( $1 ),
		persistence   => &getFarmPersistence( $1 ),
		maxclients    => $maxclients,
		tracking      => $maxtimemem,
		timeout       => $timeout,
		connmax       => $conn_max,
		maxservers    => $maxbackends,
		blacklist     => $blacklist,
		fgenabled     => $fguse,
		fgtimecheck   => $fgttcheck,
		fgscript      => $fgscript,
		fglog         => $fglog,
		xforwardedfor => $xforw,
		vip           => $vip,
		vport         => $vport
	  };
	#
	#backends
	my @run = &getFarmServers( $1 );
	foreach $l_servers ( @run )
	{
		my @l_serv = split ( "\ ", $l_servers );
		$l_serv[0]  = $l_serv[0] + 0;
		$l_serv[4]  = $l_serv[4] + 0;
		$l_serv[8]  = $l_serv[8] + 0;
		$l_serv[12] = $l_serv[12] + 0;
		$l_serv[14] = $l_serv[14] + 0;
		if ( $l_serv[2] != "0.0.0.0" )
		{
			push $out_b,
			  {
				id       => $l_serv[0],
				ip       => $l_serv[2],
				port     => @l_serv[4],
				maxconns => @l_serv[8],
				weight   => @l_serv[12],
				priority => @l_serv[14]
			  };
		}
	}

	print $q->header(
					  -type    => 'text/plain',
					  -charset => 'utf-8',
					  -status  => '200 OK'
	);

	my $j = JSON::XS->new->utf8->pretty( 1 );
	$j->canonical( $enabled );
	my $output = $j->encode(
							 {
							   description => "List farm $1",
							   params      => $out_p,
							   backends    => $out_b
							 }
	);
	print $output;

}

1
