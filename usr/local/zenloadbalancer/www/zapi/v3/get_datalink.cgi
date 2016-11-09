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
# curl --tlsv1 -k --header 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/DATAFARM
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
#  @apiVersion 3.0.0
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
#	 https://<zenlb_server:444/zapi/v3/zapi.cgi/farms/DATAFARM
#
# @apiSampleRequest off
#
#**

sub farms_name_datalink # ( $farmname )
{
	my $farmname = shift;

	my @out_p;
	my @out_b;

	my $vip = &getFarmVip( "vip", $farmname );

	push @out_p, {
		vip => $vip,
		algorithm => &getFarmAlgorithm( $farmname ),
	};

########### backends
	my @run = &getFarmServers( $farmname );

	foreach my $l_servers ( @run )
	{
		my @l_serv = split ( ";", $l_servers );

		$l_serv[0] = $l_serv[0] + 0;
		$l_serv[3] = ($l_serv[3]) ? $l_serv[3]+0: undef;
		$l_serv[4] = ($l_serv[4]) ? $l_serv[4]+0: undef;
		$l_serv[5] = $l_serv[5] + 0;

		if ( $l_serv[1] ne "0.0.0.0" )
		{
			push @out_b,
			  {
				id        => $l_serv[0],
				ip        => $l_serv[1],
				interface => @l_serv[2],
				weight    => @l_serv[3],
				priority  => @l_serv[4]
			  };
		}
	}

	my $body = {
				 description => "List farm $farmname",
				 params      => \@out_p,
				 backends    => \@out_b
	};

	&httpResponse({ code => 200, body => $body });
}

1;
