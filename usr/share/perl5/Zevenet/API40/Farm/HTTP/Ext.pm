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
my $eload;
if ( eval { require Zevenet::ELoad; } )
{
	$eload = 1;
}

use Zevenet::API40::HTTP;

include 'Zevenet::Farm::Base';
include 'Zevenet::Farm::Config';
include 'Zevenet::Farm::HTTP::Ext';

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
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
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
	return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
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
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
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
	return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
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

# POST	/farms/<>/addheader
sub add_addResponseheader    # ( $json_obj, $farmname )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $farmname = shift;

	my $desc = "Add a header to the backend repsonse.";

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
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	# check if the header is already added
	if (
		 grep ( /^$json_obj->{ header }$/, @{ &getHTTPAddRespHeader( $farmname ) } ) )
	{
		my $msg = "The header is already added.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	unless ( &addHTTPAddRespheader( $farmname, $json_obj->{ header } ) )
	{
		# success
		my $message = "Added a new header to the backend response";
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
	my $msg = "Error adding a new response header";
	return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
}

#  DELETE	/farms/<>/addheader/<>
sub del_addResponseheader
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $farmname = shift;
	my $index    = shift;

	my $desc = "Delete a header previously added to the backend response.";

	# Check that the farm exists
	if ( !&getFarmExists( $farmname ) )
	{
		my $msg = "The farm '$farmname' does not exist.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	# check if the header is already added
	if ( ( scalar @{ &getHTTPAddRespHeader( $farmname ) } ) < $index + 1 )
	{
		my $msg = "The index has not been found.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	unless ( &delHTTPAddRespheader( $farmname, $index ) )
	{
		# success
		my $message = "The header $index was deleted successfully";
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
	my $msg = "Error deleting the response header $index";
	return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
}

# POST	/farms/<>/headremove
sub add_removeResponseheader    # ( $json_obj, $farmname )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $farmname = shift;

	my $desc = "Remove a header from the backend response.";

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
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	# check if the pattern is already added
	if (
		 grep ( /^$json_obj->{ pattern }$/, @{ &getHTTPRemRespHeader( $farmname ) } ) )
	{
		my $msg = "The pattern is already added.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	unless ( &addHTTPRemRespHeader( $farmname, $json_obj->{ pattern } ) )
	{
		# success
		my $message = "Added a patter to remove reponse headers";
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
	my $msg = "Error adding the remove pattern";
	return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
}

#  DELETE	/farms/<>/addheader/<>
sub del_removeResponseHeader
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $farmname = shift;
	my $index    = shift;

	my $desc = "Delete a pattern to remove response headers.";

	# Check that the farm exists
	if ( !&getFarmExists( $farmname ) )
	{
		my $msg = "The farm '$farmname' does not exist.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	# check if the headremove is already added
	if ( ( scalar @{ &getHTTPRemRespHeader( $farmname ) } ) < $index + 1 )
	{
		my $msg = "The index has not been found.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	unless ( &delHTTPRemRespHeader( $farmname, $index ) )
	{
		# success
		my $message = "The pattern $index was deleted successfully";
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
	my $msg = "Error deleting the pattern $index";
	return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
}

#  move certs
sub farm_move_certs
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $json_obj, $farmname, $cert ) = @_;

	require Zevenet::Farm::Base;
	include 'Zevenet::Farm::HTTP::HTTPS::Ext';

	my $desc = "Move service";
	my $moveservice;

	# validate FARM NAME
	if ( !&getFarmExists( $farmname ) )
	{
		my $msg = "The farmname $farmname does not exists.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my @cert_list = &getFarmCertificatesSNI( $farmname );

	unless ( grep ( /^$cert$/, @cert_list ) )
	{
		my $msg = "The certificate $cert is not been used by the farm $farmname.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $certs_num = scalar @cert_list;
	my $params = {
				   "position" => {
								   'interval'  => "0,$certs_num",
								   'non_blank' => 'true',
								   'required'  => 'true',
				   },
	};

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	if ( $cert_list[$json_obj->{ 'position' }] eq $cert )
	{
		my $msg = "The certificate already is in required position.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $err =
	  &setHTTPFarmMoveCertificates( $farmname, $cert, $json_obj->{ 'position' },
									\@cert_list );
	if ( $err )
	{
		my $msg = "Error moving certificate. $err";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# checking the current position to prove the cert was moved properly
	my @cert_list_new = &getFarmCertificatesSNI( $farmname );
	unless ( $cert_list_new[$json_obj->{ 'position' }] eq $cert )
	{
		#~ my $msg = "There was an error moving the certificate.";
		my $msg = "There was an error moving the certificate.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $msg = "$cert was moved successfully.";
	my $body = { description => $desc, params => $json_obj, message => $msg };

	# start farm if his status was up
	if ( &getFarmStatus( $farmname ) eq 'up' )
	{
		require Zevenet::Farm::Action;
		if ( &getGlobalConfiguration( 'proxy_ng' ) ne 'true' )
		{
			&setFarmRestart( $farmname );
			$body->{ status } = 'needed restart';
			$body->{ info } =
			  "There're changes that need to be applied, stop and start farm to apply them!";

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

1;
