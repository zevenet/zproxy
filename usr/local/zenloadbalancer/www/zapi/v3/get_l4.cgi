#! /usr/bin/perl -w

########### GET L4XNAT
#
# curl --tlsv1 -k --header 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/L4FARM
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
#  @apiVersion 3.0.0
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
#         "status" : "ok",
#         "ttl" : 125,
#         "vip" : "192.168.0.161",
#         "vport" : 81
#      }
#   ]
#}
#
# @apiExample {curl} Example Usage:
#	curl --tlsv1 -k --header 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#	 https://<zenlb_server:444/zapi/v3/zapi.cgi/farms/L4FARM
#
# @apiSampleRequest off
#
#**

sub farms_name_l4 # ( $farmname )
{
	my $farmname = shift;

	my @out_p;
	my @out_b;

	my $vip   = &getFarmVip( "vip",  $farmname );
	my $vport = &getFarmVip( "vipp", $farmname );

	if ( $vport =~ /^\d+$/ )
	{
		$vport = $vport + 0;
	}

	my @ttl = &getFarmMaxClientTime( $farmname, "" );
	my $timetolimit = $ttl[0] + 0;
	
	############ FG
	my @fgconfig    = &getFarmGuardianConf( $farmname, "" );
	my $fguse       = $fgconfig[3];
	my $fgcommand   = $fgconfig[2];
	my $fgtimecheck = $fgconfig[1];
	my $fglog       = $fgconfig[4];
	
	if ( !$fgtimecheck ) { $fgtimecheck = 5; }
    if ( !$fguse ) { $fguse = "false"; }
    if ( !$fglog  ) { $fglog = "false"; }
    if ( !$fgcommand ) { $fgcommand = ""; }

	if ( -e "/tmp/$farmname.lock" )
	{
		$status = "needed restart";
	}
	else
	{
		$status = "ok";
	}

	push @out_p,
	  {
		status      => $status,
		vip         => $vip,
		vport       => $vport,
		algorithm   => &getFarmAlgorithm( $farmname ),
		nattype     => &getFarmNatType( $farmname ),
		persistence => &getFarmPersistence( $farmname ),
		protocol    => &getFarmProto( $farmname ),
		ttl         => $timetolimit,
		fgenabled   => $fguse,
		fgtimecheck => $fgtimecheck + 0,
		fgscript    => $fgcommand,
		fglog       => $fglog
	  };

	########### backends
	my @run = &getFarmServers( $farmname );
	foreach my $l_servers ( @run )
	{
		my @l_serv = split ( ";", $l_servers );

		$l_serv[0] = $l_serv[0] + 0;
		$l_serv[1] = $l_serv[1];

		if ( !$l_serv[2] =~ /^$/ )
		{
			$l_serv[2] = $l_serv[2] + 0;
		}

		$l_serv[3] = $l_serv[3] + 0;
		$l_serv[4] = $l_serv[4] + 0;
		$l_serv[5] = $l_serv[5] + 0;

		if ( $l_serv[1] ne "0.0.0.0" )
		{
			push @out_b,
			  {
				id       => $l_serv[0],
				ip       => $l_serv[1],
				port     => $l_serv[2],
				weight   => $l_serv[4],
				priority => $l_serv[5]
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
