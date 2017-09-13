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

#	GET	/system/users
sub get_all_users
{
	require Zevenet::Zapi;

	my $description = "Get users";
	my $zapiStatus = &getZAPI( "status" );
	my @users = ( { "user"=>"root", "status"=>"true" }, { "user"=>"zapi","status"=>"$zapiStatus" } );
	
	&httpResponse(
		  { code => 200, body => { description => $description, params => \@users } } );
}

#	GET	/system/users/zapi
sub get_user
{
	my $user        = shift;

	my $description = "Zapi user configuration.";
	my $errormsg;

	if ( $user ne 'zapi' )
	{
		$errormsg = "Actually only is available information about 'zapi' user";
	}
	else
	{
		require Zevenet::Zapi;

		my $zapi->{ 'key' } = &getZAPI( "keyzapi" );
		$zapi->{ 'status' } = &getZAPI( "status" );

		&httpResponse(
				{ code => 200, body => { description => $description, params => $zapi } } );
	}

	my $body =
	  { description => $description, error => "true", message => $errormsg };

	&httpResponse( { code => 404, body => $body } );
}

# POST /system/users/zapi
sub set_user_zapi
{
	my $json_obj    = shift;

	require Zevenet::Login;

	my $description = "Zapi user settings.";

	#~ my @requiredParams = ( "key", "status", "password", "newpassword" );
	my @requiredParams = ( "key", "status", "newpassword" );
	my $errormsg = &getValidOptParams( $json_obj, \@requiredParams );

	if ( !$errormsg )
	{
		if ( !&getValidFormat( "zapi_key", $json_obj->{ 'key' } ) )
		{ 
			$errormsg = "Error, character incorrect in key zapi.";
		}
		elsif ( !&getValidFormat( "zapi_password", $json_obj->{ 'newpassword' } ) )
		{
			$errormsg = "Error, character incorrect in password zapi.";
		}
		elsif ( !&getValidFormat( "zapi_status", $json_obj->{ 'status' } ) )
		{
			$errormsg = "Error, character incorrect in status zapi.";
		}
		else
		{
			require Zevenet::Zapi;

			if (    $json_obj->{ 'status' } eq 'enable'
				 && &getZAPI( "status") eq 'false' )
			{
				&setZAPI( "enable" );
			}
			elsif (    $json_obj->{ 'status' } eq 'disable'
					&& &getZAPI( "status" ) eq 'true' )
			{
				&setZAPI( "disable" );
			}

			if ( exists $json_obj->{ 'key' } )
			{
				&setZAPI( 'key', $json_obj->{ 'key' } );
			}

			&changePassword( 'zapi',
							 $json_obj->{ 'newpassword' },
							 $json_obj->{ 'newpassword' } )
			  if ( exists $json_obj->{ 'newpassword' } );

			$errormsg = "Settings was changed successful.";
			&httpResponse(
				 {
				   code => 200,
				   body =>
					 { description => $description, params => $json_obj, message => $errormsg }
				 }
			);
		}
	}

	my $body =
	  { description => $description, error => "true", message => $errormsg };

	&httpResponse( { code => 400, body => $body } );
}

# POST /system/users/root
sub set_user
{
	my $json_obj       = shift;
	my $user           = shift;

	my $description    = "User settings.";
	my @requiredParams = ( "password", "newpassword" );
	my $errormsg = &getValidReqParams( $json_obj, \@requiredParams, \@requiredParams );

	if ( !$errormsg )
	{
		if ( $user ne 'root' )
		{
			$errormsg =
			  "Error, actually only is available to change password in root user.";
		}
		else
		{
			require Zevenet::Login;

			if ( !&getValidFormat( 'password', $json_obj->{ 'newpassword' } ) )
			{
				$errormsg = "Error, character incorrect in password.";
			}
			elsif ( !&checkValidUser( $user, $json_obj->{ 'password' } ) )
			{
				$errormsg = "Error, invalid current password.";
			}
			else
			{
				$errormsg = &changePassword( $user,
											 $json_obj->{ 'newpassword' },
											 $json_obj->{ 'newpassword' } );
				if ( $errormsg )
				{
					$errormsg = "Error, changing $user password.";
				}
				else
				{
					$errormsg = "Settings was changed successful.";
					&httpResponse(
						 {
						   code => 200,
						   body =>
							 { description => $description, params => $json_obj, message => $errormsg }
						 }
					);
				}
			}
		}
	}

	my $body =
	  { description => $description, error => "true", message => $errormsg };

	&httpResponse( { code => 400, body => $body } );
}

1;
