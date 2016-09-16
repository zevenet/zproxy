#! /usr/bin/perl -w

##############################################################################
#
#     This file is part of the Zen Load Balancer Enterprise Edition software
#     package.
#
#     Copyright (C) 2014 SOFINTEL IT ENGINEERING SL, Sevilla (Spain)
#
#     This file cannot be distributed, released in public domain and/or for
#     commercial purposes.
#
###############################################################################

########### GET DATALINK
# curl --tlsv1 -k --header 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/DATAFARM
#
#
#
#####Documentation of GET DATALINK####
#**
#  @api {get} /farms/<farmname> Request info of a datalink Farm
#  @apiGroup Farm Get
#  @apiName GetFarmNameDATALINK
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiDescription Get the Params of a given Farm <farmname> with DATALINK profile
#  @apiVersion 2.1.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "backends" : [
#      {
#         "id" : 0,
#         "ip" : "192.168.0.150",
#         "interface" : "eth0",
#         "priority" : 5,
#         "weight" : 2
#      },
#      {
#         "id" : 1,
#         "ip" : "192.168.1.151",
#         "interface" : "eth0",
#         "priority" : 1,
#         "weight" : 1
#      }
#   ],
#   "description" : "List farm DATAFARM",
#   "params" : [
#      {
#         "algorithm" : "weight",
#         "vip" : "178.62.126.152",
#      }
#   ]
#}
#
# @apiExample {curl} Example Usage:
#	curl --tlsv1 -k --header 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#	-u zapi:<password> https://<zenlb_server:444/zapi/v3/zapi.cgi/farms/DATAFARM
#
# @apiSampleRequest off
#
#**

sub farms_name_datalink()
{

########### params
	use CGI;
	my $q = CGI->new;

	my $out_p = [];
	my $out_b = [];

	$vip = &getFarmVip( "vip", $1 );

	push $out_p, { vip => $vip, algorithm => &getFarmAlgorithm( $1 ) };

########### backends

	my @run = &getFarmServers( $1 );
	foreach $l_servers ( @run )
	{
		my @l_serv = split ( ";", $l_servers );
		$l_serv[0] = $l_serv[0] + 0;
		$l_serv[3] = $l_serv[3] + 0;
		$l_serv[4] = $l_serv[4] + 0;
		$l_serv[5] = $l_serv[5] + 0;
		if ( $l_serv[1] ne "0.0.0.0" )
		{
			push $out_b,
			  {
				id        => $l_serv[0],
				ip        => $l_serv[1],
				interface => @l_serv[2],
				weight    => @l_serv[3],
				priority  => @l_serv[4]
			  };
		}
	}

########### print JSON
	print $q->header(
					  -type    => 'text/plain',
					  -charset => 'utf-8',
					  -status  => '200 OK',
					  'Access-Control-Allow-Origin'  => '*'
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
