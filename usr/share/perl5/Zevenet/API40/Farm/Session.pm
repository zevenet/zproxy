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
require Zevenet::Farm::Core;
include 'Zevenet::Farm::L4xNAT::Sessions::Ext';

# GET /farms/<farms>/sessions
sub get_farm_sessions    # ( $farmname )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $farmname = shift;

	require Zevenet::Farm::Core;

	my $desc = "Get farm sessions";

	my $type = &getFarmType( $farmname );

	if ( $type ne "l4xnat" )
	{
		my $msg = "This feature is only available for l4xnat farms.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $sessions = [];

	require Zevenet::Farm::L4xNAT::Config;
	if ( &getL4FarmStatus( $farmname ) ne "down" )
	{
		require Zevenet::Farm::L4xNAT::Sessions;
		$sessions = &listL4FarmSessions( $farmname );
	}
	my $body = {
				 description => $desc,
				 params      => $sessions,
	};

	&httpResponse( { code => 200, body => $body } );
}

#  POST /farms/<farms>/sessions
sub add_farm_sessions
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $farm     = shift;

	my $desc = "Adding a static session to the $farm";
	my $params = {
		"id" => {
				  'non_blank'    => 'true',
				  'required'     => 'true',
				  'valid_format' => 'integer',
		},

# session format:
# mac: 02:8e:6q:33:02:8e
# ip or srcip: 195.2.3.66
# port: 5445
# srcip_srcport or srcip_dstport or : 122.36.54.2_80, the character '_'is used to difference when IP is v6

		"session" => {
					   'non_blank' => 'true',
					   'required'  => 'true',
		},
	};

	my $num_bks = 0;
	require Zevenet::Farm::Backend;
	my $f_type = &getFarmType( $farm );
	if ( $f_type eq 'l4xnat' )
	{
		$num_bks = @{ &getFarmServers( $farm ) };
		if ( $num_bks )
		{
			$params->{ id }->{ 'values' } = [0 .. $num_bks - 1];
			delete $params->{ id }->{ 'valid_format' };
		}
	}

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	if ( $f_type ne 'l4xnat' )
	{
		my $msg = "This feature is only available for l4xnat profiles.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $persis_type = &getL4FarmParam( 'persist', $farm );
	if ( $persis_type eq '' )
	{
		my $msg = "The farm $farm has not configured any persistence.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}
	elsif ( !$num_bks )
	{
		my $msg = "The farm $farm has not configured any backend.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}
	elsif ( !&validateL4FarmSession( $persis_type, $json_obj->{ session } ) )
	{
		my $msg =
		  "The session '$json_obj->{session}' is not valid for the persistence '$persis_type'.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}
	my $session_obj = &getL4FarmSession( $farm, $json_obj->{ session } );
	if ( defined $session_obj and $json_obj->{ type } eq "dynamic" )
	{
		my $msg = "The session '$json_obj->{session}' already exists.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	# executing the action
	my $err =
	  &addL4FarmSession( $farm, $json_obj->{ 'session' }, $json_obj->{ 'id' } );
	if ( !$err )
	{
		#~ include 'Zevenet::Cluster';
		#~ &runZClusterRemoteManager( 'rbac_user', 'add', $json_obj->{ 'name' } );

		my $session = &getL4FarmSession( $farm, $json_obj->{ session } );

		my $msg = "Added a session for the farm '$farm'";
		my $body = {
					 description => $desc,
					 params      => $session,
					 message     => $msg,
		};
		return &httpResponse( { code => 201, body => $body } );
	}
	else
	{
		my $msg = "Error, trying to add the session.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}
}

#  DELETE /farms/<farms>/sessions/<session>
sub delete_farm_sessions
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $farm    = shift;
	my $session = shift;

	my $desc = "Delete a 'static' session";

	if ( &getFarmType( $farm ) ne 'l4xnat' )
	{
		my $msg = "This feature is only available for l4xnat profiles.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $session_obj = &getL4FarmSession( $farm, $session );
	if ( !defined $session_obj )
	{
		my $msg = "The session '$session' does not exist.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}
	elsif ( $session_obj->{ type } ne 'static' )
	{
		my $msg = "Only the 'static' sessions can be managed.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $err = &delL4FarmSession( $farm, $session );
	if ( !$err )
	{
		#~ include 'Zevenet::Cluster';
		#~ &runZClusterRemoteManager( 'rbac_user', 'delete', $user );

		my $msg = "The session '$session' was deleted properly from the farm '$farm'.";
		my $body = {
					 description => $desc,
					 success     => "true",
					 message     => $msg,
		};
		return &httpResponse( { code => 200, body => $body } );
	}

	my $msg = "Error deleting the session '$session' from the farm '$farm'.";
	return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
}

1;

