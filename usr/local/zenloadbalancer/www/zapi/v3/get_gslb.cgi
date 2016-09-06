#!/usr/bin/perl -w

########### GET GSLB
# curl --tlsv1 -k --header 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/FarmGSLB
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
#  @apiVersion 2.1.0
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
#       -u zapi:<password>  https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/FarmGSLB
#
#@apiSampleRequest off
#
#**

our $origin;
if ( $origin ne 1 )
{
	exit;
}

sub farms_name_gslb()
{

	use CGI;
	my $q = CGI->new;

	my $out_p = [];
	my $out_b = [];
	my $out_s = [];
	my $out_z = [];

##

###
	$vip   = &getFarmVip( "vip",  $1 );
	$vport = &getFarmVip( "vipp", $1 );
	$vport = $vport + 0;

	if ( -e "/tmp/$1.lock" )
	{
		$status = "needed restart";
	}
	else
	{
		$status = "ok";
	}

	push $out_p, { vip => $vip, vport => $vport, status => $status };

	#
	# Services
	#

	my @services = &getGSLBFarmServices( $1 );
	foreach $srv ( @services )
	{

		my @serv = split ( ".cfg", $srv );
		my $srv  = @serv[0];
		my $lb   = &getFarmVS( $1, $srv, "algorithm" );

		# Default port health check
		my $dpc        = &getFarmVS( $1, $srv, "dpc" );
		my $backendsvs = &getFarmVS( $1, $srv, "backends" );
		my @be = split ( "\n", $backendsvs );

		#
		# Backends
		#

		my $out_b      = [];
		my $backendsvs = &getFarmVS( $1, $srv, "backends" );
		my @be         = split ( "\n", $backendsvs );
		foreach $subline ( @be )
		{
			$subline =~ s/^\s+//;
			if ( $subline =~ /^$/ )
			{
				next;
			}

			my @subbe = split ( " => ", $subline );

			push $out_b, { id => @subbe[0], ip => @subbe[1] };
		}

		push $out_s, { id => $srv, algorithm => $lb, port => $dpc, backends => $out_b };
	}

	#
	# Zones
	#

	my @zones   = &getFarmZones( $1 );
	my $first   = 0;
	my $vserver = 0;
	my $pos     = 0;
	foreach $zone ( @zones )
	{

		#if ($first == 0) {
		$pos++;
		$first = 1;
		my $ns         = &getFarmVS( $1, $zone, "ns" );
		my $backendsvs = &getFarmVS( $1, $zone, "resources" );
		my @be = split ( "\n", $backendsvs );
		my $out_re = [];
		foreach $subline ( @be )
		{

			if ( $subline =~ /^$/ )
			{
				next;
			}

			my @subbe  = split ( "\;", $subline );
			my @subbe1 = split ( "\t", @subbe[0] );
			my @subbe2 = split ( "\_", @subbe[1] );
			my $ztype  = @subbe1[1];
			my $la_resource = @subbe1[0];
			my $la_ttl      = @subbe1[1];

			if ( $resource_server ne "" ) { $la_resource = $resource_server; }
			if ( $ttl_server ne "" )      { $la_ttl      = $ttl_server; }

			if (    @subbe1[1] ne "NS"
				 && @subbe1[1] ne "A"
				 && @subbe1[1] ne "CNAME"
				 && @subbe1[1] ne "DYNA"
				 && @subbe1[1] ne "DYNC" )
			{
				$ztype = @subbe1[2];
			}
			my $la_type = $ztype;
			if ( $type_server ne "" ) { $la_type = $type_server; }

			my $rdata = "";
			if ( @subbe1 == 3 )
			{
				$rdata = @subbe1[2];
			}
			elsif ( @subbe1 == 4 )
			{
				$rdata = @subbe1[3];
			}
			elsif ( @subbe1 == 5 )
			{
				$rdata = @subbe1[4];
			}
			chop ( $rdata );

			if (    @subbe1[1] ne "NS"
				 && @subbe1[1] ne "A"
				 && @subbe1[1] ne "CNAME"
				 && @subbe1[1] ne "DYNA"
				 && @subbe1[1] ne "DYNC" )
			{
				$ztype = @subbe1[2];
			}

			push $out_re,
			  {
				id    => @subbe2[1] + 0,
				rname => $la_resource,
				ttl   => $la_ttl,
				type  => $ztype,
				rdata => $rdata
			  };

		}
		my $ns = &getFarmVS( $1, $zone, "ns" );

		push $out_z, { id => $zone, DefaultNameServer => $ns, resources => $out_re };
	}

	# Success
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
							   services    => $out_s,
							   zones       => $out_z,
							 }
	);
	print $output;

}

1
