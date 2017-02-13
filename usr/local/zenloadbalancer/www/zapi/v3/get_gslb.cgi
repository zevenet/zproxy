#!/usr/bin/perl -w

use strict;

#	/farms/<GSLBfarm>
sub farms_name_gslb # ( $farmname )
{
	my $farmname = shift;

	my $farm_ref;
	my @out_s;
	my @out_z;

	my $status = &getFarmStatus( $farmname );
	my $vip   = &getFarmVip( "vip",  $farmname );
	my $vport = &getFarmVip( "vipp", $farmname );
	$vport = $vport + 0;

	if ( $status == 'up' && -e "/tmp/$farmname.lock" )
	{
		$status = "needed restart";
	}

	$farm_ref = { vip => $vip, vport => $vport, status => $status };

	#
	# Services
	#

	my @services = &getGSLBFarmServices( $farmname );

	foreach my $srv_it ( @services )
	{
		my @serv = split ( ".cfg", $srv_it );
		my $srv  = $serv[0];
		my $lb   = &getFarmVS( $farmname, $srv, "algorithm" );

		# Default port health check
		my $dpc        = &getFarmVS( $farmname, $srv, "dpc" );
		my $backendsvs = &getFarmVS( $farmname, $srv, "backends" );
		my @be = split ( "\n", $backendsvs );

		#
		# Backends
		#

		my @out_b;
		$backendsvs = &getFarmVS( $farmname, $srv, "backends" );
		@be         = split ( "\n", $backendsvs );

		foreach my $subline ( @be )
		{
			$subline =~ s/^\s+//;
			if ( $subline =~ /^$/ )
			{
				next;
			}

			my @subbe = split ( " => ", $subline );

			$subbe[0] =~ s/^primary$/1/;
			$subbe[0] =~ s/^secondary$/2/;
			#~ @subbe[0]+0 if @subbe[0] =~ /^\d+$/;

			push @out_b,
			  {
				id => $subbe[0]+0,
				ip => $subbe[1],
			  };
		}

		# farm guardian 
		my ( $fgTime, $fgScrip ) = &getGSLBFarmGuardianParams( $farmname, $srv );
		my $fgStatus = &getGSLBFarmFGStatus( $farmname, $srv );
		
		push @out_s,
		  {
			id        => $srv,
			algorithm => $lb,
			deftcpport      => $dpc + 0,
			fgenabled => $fgStatus,
			fgscript => $fgScrip,
			fgtimecheck => $fgTime + 0,
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

		for my $resource ( @{ $resources } )
		{
			$resource->{ ttl } = undef if ! $resource->{ ttl };
			$resource->{ ttl } += 0 if $resource->{ ttl };
		}

		push @out_z,
		  {
			id                => $zone,
			DefaultNameServer => $ns,
			resources         => $resources
		  };
	}

	my $ipds = &getIPDSfarmsRules( $farmname );

	# Success
	my $body = {
				 description => "List farm $farmname",
				 params      => $farm_ref,
				 services    => \@out_s,
				 zones       => \@out_z,
				 ipds			=>  $ipds,
	};

	&httpResponse({ code => 200, body => $body });
}

#	/farms/<GSLBfarm>/zones/<zone>/resources
sub gslb_zone_resources # ( $farmname, $zone )
{
	my $farmname = shift;
	my $zone = shift;

	my $description = "List zone resources";

	# validate FARM NAME
	if ( &getFarmFile( $farmname ) == -1 )
	{
		# Error
		my $errormsg = "Farm name not found";
		my $body = {
				description => $description,
				error => "true",
				message => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	# validate FARM TYPE
	if ( &getFarmType( $farmname ) ne 'gslb' )
	{
		my $errormsg = "Only GSLB profile is supported for this request.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	# validate ZONE
	if ( ! scalar grep { $_ eq $zone } &getFarmZones( $farmname ) )
	{
		my $errormsg = "Could not find the requested zone.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	#
	# Zones
	#

	my $resources = &getGSLBResources  ( $farmname, $zone );

	for my $resource ( @{ $resources } )
	{
		$resource->{ ttl } = undef if ! $resource->{ ttl };
		$resource->{ ttl } += 0 if $resource->{ ttl };
	}

	# Success
	my $body = {
				 description => $description,
				 params      => $resources,
	};

	&httpResponse({ code => 200, body => $body });
}

1;
