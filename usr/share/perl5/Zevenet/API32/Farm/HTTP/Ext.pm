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

use Zevenet::API32::HTTP;

include 'Zevenet::Farm::Base';
include 'Zevenet::Farm::Config';
include 'Zevenet::Farm::HTTP::Ext';

my $eload;
if ( eval { require Zevenet::ELoad; } )
{
	$eload = 1;
}

# POST	/farms/<>/addheader
sub add_addheader    # ( $json_obj, $farmname )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $farmname = shift;

	my $desc = "Add addheader directive.";

	# Check that the farm exists
	if ( !&getFarmExists( $farmname ) )
	{
		my $msg = "The farm '$farmname' does not exist.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $params = {
				   "header" => {
								 'non_blank' => 'true',
								 'required'  => 'true',
				   },
	};

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	# check if the header is already added
	if (
		 grep ( /^$json_obj->{ header }$/, @{ &getHTTPAddReqHeader( $farmname ) } ) )
	{
		my $msg = "The header is already added.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	unless ( &addHTTPAddheader( $farmname, $json_obj->{ header } ) )
	{
		# success
		my $message = "Added a new item to the addheader list";
		my $body = {
					 description => $desc,
					 success     => "true",
					 message     => $message,
		};

		if ( &getFarmStatus( $farmname ) ne 'down' )
		{
			include 'Zevenet::Farm::Action';
			if ( &getGlobalConfiguration( 'proxy_ng' ) ne 'true' )
			{
				&setFarmRestart( $farmname );
				$body->{ status } = 'needed restart';
			}
			else
			{
				&runFarmReload( $farmname );
				&eload(
						module => 'Zevenet::Cluster',
						func   => 'runZClusterRemoteManager',
						args   => ['farm', 'reload', $farmname],
				) if ( $eload );
			}
		}

		return &httpResponse( { code => 200, body => $body } );
	}

	# error
	my $msg = "Error adding a new addheader";
	&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
}

#  DELETE	/farms/<>/addheader/<>
sub del_addheader
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $farmname = shift;
	my $index    = shift;

	my $desc = "Delete addheader directive.";

	# Check that the farm exists
	if ( !&getFarmExists( $farmname ) )
	{
		my $msg = "The farm '$farmname' does not exist.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	# check if the header is already added
	if ( ( scalar @{ &getHTTPAddReqHeader( $farmname ) } ) < $index + 1 )
	{
		my $msg = "The index has not been found.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	unless ( &delHTTPAddheader( $farmname, $index ) )
	{
		# success
		my $message = "The addheader $index was deleted successfully";
		my $body = {
					 description => $desc,
					 success     => "true",
					 message     => $message,
		};

		if ( &getFarmStatus( $farmname ) ne 'down' )
		{
			include 'Zevenet::Farm::Action';
			if ( &getGlobalConfiguration( 'proxy_ng' ) ne 'true' )
			{
				&setFarmRestart( $farmname );
				$body->{ status } = 'needed restart';
			}
			else
			{
				&runFarmReload( $farmname );
				&eload(
						module => 'Zevenet::Cluster',
						func   => 'runZClusterRemoteManager',
						args   => ['farm', 'reload', $farmname],
				) if ( $eload );
			}
		}

		return &httpResponse( { code => 200, body => $body } );
	}

	# error
	my $msg = "Error deleting the addheader $index";
	return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
}

# POST	/farms/<>/headremove
sub add_headremove    # ( $json_obj, $farmname )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $farmname = shift;

	my $desc = "Add headremove directive.";

	# Check that the farm exists
	if ( !&getFarmExists( $farmname ) )
	{
		my $msg = "The farm '$farmname' does not exist.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $params = {
				   "pattern" => {
								  'non_blank' => 'true',
								  'required'  => 'true',
				   },
	};

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	# check if the pattern is already added
	if (
		 grep ( /^$json_obj->{ pattern }$/, @{ &getHTTPRemReqHeader( $farmname ) } ) )
	{
		my $msg = "The pattern is already added.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	unless ( &addHTTPHeadremove( $farmname, $json_obj->{ pattern } ) )
	{
		# success
		my $message = "Added a new item to the headremove list";
		my $body = {
					 description => $desc,
					 success     => "true",
					 message     => $message,
		};

		if ( &getFarmStatus( $farmname ) ne 'down' )
		{
			include 'Zevenet::Farm::Action';
			if ( &getGlobalConfiguration( 'proxy_ng' ) ne 'true' )
			{
				&setFarmRestart( $farmname );
				$body->{ status } = 'needed restart';
			}
			else
			{
				&runFarmReload( $farmname );
				&eload(
						module => 'Zevenet::Cluster',
						func   => 'runZClusterRemoteManager',
						args   => ['farm', 'reload', $farmname],
				) if ( $eload );
			}
		}

		return &httpResponse( { code => 200, body => $body } );
	}

	# error
	my $msg = "Error adding a new headremove";
	&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
}

#  DELETE	/farms/<>/addheader/<>
sub del_headremove
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $farmname = shift;
	my $index    = shift;

	my $desc = "Delete headremove directive.";

	# Check that the farm exists
	if ( !&getFarmExists( $farmname ) )
	{
		my $msg = "The farm '$farmname' does not exist.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	# check if the headremove is already added
	if ( ( scalar @{ &getHTTPRemReqHeader( $farmname ) } ) < $index + 1 )
	{
		my $msg = "The index has not been found.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	unless ( &delHTTPHeadremove( $farmname, $index ) )
	{
		# success
		my $message = "The headremove $index was deleted successfully";
		my $body = {
					 description => $desc,
					 success     => "true",
					 message     => $message,
		};

		if ( &getFarmStatus( $farmname ) ne 'down' )
		{
			include 'Zevenet::Farm::Action';
			if ( &getGlobalConfiguration( 'proxy_ng' ) ne 'true' )
			{
				&setFarmRestart( $farmname );
				$body->{ status } = 'needed restart';
			}
			else
			{
				&runFarmReload( $farmname );
				&eload(
						module => 'Zevenet::Cluster',
						func   => 'runZClusterRemoteManager',
						args   => ['farm', 'reload', $farmname],
				) if ( $eload );
			}
		}

		return &httpResponse( { code => 200, body => $body } );
	}

	# error
	my $msg = "Error deleting the headremove $index";
	return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
}

1;
