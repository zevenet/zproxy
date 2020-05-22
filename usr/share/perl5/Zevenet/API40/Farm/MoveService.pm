#!/usr/bin/perl
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

sub move_services
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $json_obj, $farmname, $service ) = @_;

	require Zevenet::Farm::Base;
	require Zevenet::Farm::HTTP::Service;
	include 'Zevenet::Farm::HTTP::Service::Ext';    # Load MoveService functions

	my $desc = "Move service";

	# validate FARM NAME
	if ( !&getFarmExists( $farmname ) )
	{
		my $msg = "The farmname $farmname does not exist.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my @services     = &getHTTPFarmServices( $farmname );
	my $services_num = scalar @services;

	if ( !grep ( /^$service$/, @services ) )
	{
		my $msg = "$service not found.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $params = {
				   "position" => {
								   'interval'  => "0,$services_num",
								   'non_blank' => 'true',
								   'required'  => 'true',
				   },
	};

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	my $srv_position = &getFarmVSI( $farmname, $service );
	if ( $srv_position == $json_obj->{ 'position' } )
	{
		my $msg = "The service already is in required position.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# stopping farm
	my $farm_status = &getFarmStatus( $farmname );
	if ( $farm_status eq 'up' )
	{
		require Zevenet::Farm::Action;
		if ( &runFarmStop( $farmname, "true" ) != 0 )
		{
			my $msg = "Error stopping the farm.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}

		&zenlog( "Farm stopped successfully.", "info", "LSLB" );
	}

	&setHTTPFarmMoveService( $farmname, $service, $json_obj->{ 'position' } );

	# start farm if his status was up
	if ( $farm_status eq 'up' )
	{
		if ( &runFarmStart( $farmname, "true" ) )
		{
			my $msg = "The $farmname farm hasn't been restarted";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}

		&setHTTPFarmBackendStatus( $farmname );

		include 'Zevenet::Cluster';

		&runZClusterRemoteManager( 'farm', 'restart', $farmname );
	}

	my $msg = "$service was moved successfully.";
	my $body = { description => $desc, params => $json_obj, message => $msg };

	return &httpResponse( { code => 200, body => $body } );
}

1;

