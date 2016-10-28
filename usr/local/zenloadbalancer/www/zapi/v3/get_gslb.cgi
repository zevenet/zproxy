#!/usr/bin/perl -w

########### GET GSLB
# curl --tlsv1 -k --header 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/FarmGSLB
#
#
#
#####Documentation of GET GSLB####
#**
#  @api {get} /farms/<farmname> Request info of a gslb Farm
#  @apiGroup Farm Get
#  @apiName GetFarmNameGSLB
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiDescription Get the Params of a given Farm <farmname> with GSLB profile
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "List farm FarmGSLB",
#   "params" : [
#      {
#         "status" : "needed restart",
#         "vip" : "178.62.126.152",
#         "vport" : 53
#      }
#   ],
#   "services" : [
#      {
#         "algorithm" : "roundrobin",
#         "backends" : [
#            {
#               "ip" : "192.168.0.155",
#               "id" : "1"
#            }
#         ],
#         "id" : "sev1",
#         "port" : "80"
#      }
#   ],
#   "zones" : [
#      {
#         "DefaultNameServer" : "ns1",
#         "id" : "zone2",
#         "resources" : [
#            {
#               "id" : 0,
#               "rdata" : "ns1",
#               "rname" : "@",
#               "ttl" : "",
#               "type" : "NS"
#            },
#            {
#               "id" : 1,
#               "rdata" : "0.0.0.0",
#               "rname" : "ns1",
#               "ttl" : "",
#               "type" : "A"
#            }
#         ]
#      },
#      {
#         "DefaultNameServer" : "ns1",
#         "id" : "zone1",
#         "resources" : [
#            {
#               "id" : 0,
#               "rdata" : "ns1",
#               "rname" : "@",
#               "ttl" : "",
#               "type" : "NS"
#            },
#            {
#               "id" : 1,
#               "rdata" : "0.0.0.0",
#               "rname" : "ns1",
#               "ttl" : "",
#               "type" : "A"
#            },
#            {
#               "id" : 2,
#               "rdata" : "sev1",
#               "rname" : "www",
#               "ttl" : "5",
#               "type" : "DYNA"
#            },
#            {
#               "id" : 3,
#               "rdata" : "1.1.1.1",
#               "rname" : "www",
#               "ttl" : "10",
#               "type" : "NS"
#            }
#         ]
#      }
#
#   ]
#}
#
#
#@apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#         https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/FarmGSLB
#
#@apiSampleRequest off
#
#**

sub farms_name_gslb # ( $farmname )
{
	my $farmname = shift;

	my @out_p;
	my @out_s;
	my @out_z;

	my $vip   = &getFarmVip( "vip",  $farmname );
	my $vport = &getFarmVip( "vipp", $farmname );
	$vport = $vport + 0;

	if ( -e "/tmp/$farmname.lock" )
	{
		$status = "needed restart";
	}
	else
	{
		$status = "ok";
	}

	push @out_p, { vip => $vip, vport => $vport, status => $status };

	#
	# Services
	#

	my @services = &getGSLBFarmServices( $farmname );

	foreach my $srv ( @services )
	{
		my @serv = split ( ".cfg", $srv );
		my $srv  = @serv[0];
		my $lb   = &getFarmVS( $farmname, $srv, "algorithm" );

		# Default port health check
		my $dpc        = &getFarmVS( $farmname, $srv, "dpc" );
		my $backendsvs = &getFarmVS( $farmname, $srv, "backends" );
		my @be = split ( "\n", $backendsvs );

		#
		# Backends
		#

		my @out_b;
		my $backendsvs = &getFarmVS( $farmname, $srv, "backends" );
		my @be         = split ( "\n", $backendsvs );

		foreach my $subline ( @be )
		{
			$subline =~ s/^\s+//;
			if ( $subline =~ /^$/ )
			{
				next;
			}

			my @subbe = split ( " => ", $subline );

			push @out_b,
			  {
				id => @subbe[0],
				ip => @subbe[1],
			  };
		}

		# farm guardian 
		my ( $fgTime, $fgScrip ) = &getGSLBFarmGuardianParams( $farmname, $srv );
		my $fgStatus = &getGSLBFarmFGStatus( $farmname, $srv );
		
		push @out_s,
		  {
			id        => $srv,
			algorithm => $lb,
			port      => $dpc,
			fgenabled => $fgStatus,
			fgscript => $fgScrip,
			fgtimecheck => $fgTime,
			backends  => \@out_b,
		  };
	}

	#
	# Zones
	#

	my @zones   = &getFarmZones( $farmname );
	my $first   = 0;
	my $vserver = 0;
	my $pos     = 0;

	foreach my $zone ( @zones )
	{
		#if ($first == 0) {
		$pos++;
		$first = 1;
		my $ns         = &getFarmVS( $farmname, $zone, "ns" );
		my $backendsvs = &getFarmVS( $farmname, $zone, "resources" );
		my @be = split ( "\n", $backendsvs );
		my @out_re;

		my $resources = &getGSLBResources  ( $farmname, $zone );
		my $ns = &getFarmVS( $farmname, $zone, "ns" );

		push @out_z,
		  {
			id                => $zone,
			DefaultNameServer => $ns,
			resources         => $resources
		  };
		  
	}

	# Success
	my $body = {
				 description => "List farm $farmname",
				 params      => \@out_p,
				 services    => \@out_s,
				 zones       => \@out_z,
	};

	&httpResponse({ code => 200, body => $body });
}

1;
