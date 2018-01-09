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

use strict;
use Zevenet::Farm::GSLB::Service;
use Zevenet::Farm::GSLB::Backend;
use Zevenet::Farm::GSLB::FarmGuardian;
use Zevenet::Farm::GSLB::Zone;

#	/farms/<GSLBfarm>
sub farms_name_gslb # ( $farmname )
{
	my $farmname = shift;

	require Zevenet::Farm::Config;
	my $farm_ref;
	my @out_s;
	my @out_z;

	my $status = &getFarmVipStatus( $farmname );
	my $vip   = &getFarmVip( "vip",  $farmname );
	my $vport = &getFarmVip( "vipp", $farmname ) + 0;

	$farm_ref = { vip => $vip, vport => $vport, status => $status };

	# Services
	my @services = &getGSLBFarmServices( $farmname );

	foreach my $srv_it ( @services )
	{
		my @serv = split ( ".cfg", $srv_it );
		my $srv  = $serv[0];
		my $lb   = &getGSLBFarmVS( $farmname, $srv, "algorithm" );

		# Default port health check
		my $dpc = &getGSLBFarmVS( $farmname, $srv, "dpc" );

		# Backends
		my @out_b = &getGSLBFarmBackends( $farmname, $srv );

		# Farmguardian
		my ( $fgTime, $fgScrip ) = &getGSLBFarmGuardianParams( $farmname, $srv );
		my $fgStatus = &getGSLBFarmFGStatus( $farmname, $srv );
		
		push @out_s,
		  {
			id          => $srv,
			algorithm   => $lb,
			deftcpport  => $dpc + 0,
			fgenabled   => $fgStatus,
			fgscript    => $fgScrip,
			fgtimecheck => $fgTime + 0,
			backends    => \@out_b,
		  };
	}

	# Zones
	my @zones   = &getGSLBFarmZones( $farmname );
	my $first   = 0;
	my $vserver = 0;
	my $pos     = 0;

	foreach my $zone ( @zones )
	{
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
			id        => $zone,
			defnamesv => $ns,
			resources => $resources,
		  };
	}

	my $body = {
				 description => "List farm $farmname",
				 params      => $farm_ref,
				 services    => \@out_s,
				 zones       => \@out_z,
	};

	if ( eval{ require Zevenet::IPDS; } )
	{
		$body->{ ipds } = &getIPDSfarmsRules( $farmname );
	}

	&httpResponse({ code => 200, body => $body });
}

1;
