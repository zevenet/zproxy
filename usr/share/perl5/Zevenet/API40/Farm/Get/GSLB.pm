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

use Zevenet::API40::HTTP;

include 'Zevenet::Farm::GSLB::Service';
include 'Zevenet::Farm::GSLB::Backend';
include 'Zevenet::Farm::GSLB::FarmGuardian';
include 'Zevenet::Farm::GSLB::Zone';

#	/farms/<GSLBfarm>
sub farms_name_gslb    # ( $farmname )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $farmname = shift;

	require Zevenet::Farm::Config;
	require Zevenet::Farm::Base;

	my $status = &getFarmVipStatus( $farmname );
	my $vip    = &getFarmVip( "vip", $farmname );
	my $vport  = &getFarmVip( "vipp", $farmname ) + 0;

	my $farm_ref = {
					 vip    => $vip,
					 vport  => $vport,
					 status => $status,
	};

	# Services and zones
	my $services_aref = &getGSLBFarmServicesStruct( $farmname );
	my $zones_aref    = &getGSLBFarmZonesStruct( $farmname );

	my $body = {
				 description => "List farm $farmname",
				 params      => $farm_ref,
				 services    => $services_aref,
				 zones       => $zones_aref,
	};

	include 'Zevenet::IPDS::Core';

	$body->{ ipds } = &getIPDSfarmsRules( $farmname );

	return &httpResponse( { code => 200, body => $body } );
}

1;

