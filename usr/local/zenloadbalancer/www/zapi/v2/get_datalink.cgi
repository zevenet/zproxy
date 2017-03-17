###############################################################################
#
#    Zevenet Software License
#    This file is part of the Zevenet Load Balancer software package.
#
#    Copyright (C) 2014-today ZEVENET SL, Sevilla (Spain)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
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
#  @apiVersion 2.0.0
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
#	-u zapi:<password> https://<zenlb_server:444/zapi/v2/zapi.cgi/farms/DATAFARM
#
# @apiSampleRequest off
#
#**

our $origin;
if ( $origin ne 1 )
{
	exit;
}

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

1;
