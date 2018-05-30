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


my $eload;
if ( eval { require Zevenet::ELoad; } ) { $eload = 1; }

# 	GET /system/users
sub get_system_user
{
	require Zevenet::User;
	my $user = &getUser();

	my $desc = "Retrieve the user $user";

	if ( 'root' eq $user )
	{
		require Zevenet::Zapi;
		my $params = {
					 'user'   	=> $user,
					 #~ 'zapikey'	=> &getZAPI( "keyzapi" ),
					 'status' 	=> &getZAPI( "status" ),
		};

		&httpResponse(
			   { code => 200, body => { description => $desc, params => $params } } );
	}

	elsif ( $eload )
	{
		my $params = &eload(
			module => 'Zevenet::API32::RBAC::User',
			func   => 'get_system_user_rbac',
		);

		if ( $params )
		{
			&httpResponse(
			   { code => 200, body => { description => $desc, params => $params } } );
		}
	}

	else
	{
		my $msg = "The user is not found";
		&httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}
}


#  PUT /system/users
sub set_system_user
{
	my $json_obj = shift;

	require Zevenet::User;
	require Zevenet::Login;

	my $error = 0;
	my $user = &getUser();
	my $desc = "Modify the user $user";

	$desc = "Modify the user $user";
	my $params = {
		  "zapikey"	 => { 'valid_format' => 'zapi_key' },
		  "status"   => { 'valid_format' => 'boolean', 'non_black' => 'true' },   # it is the permissions value
		  "password" => {
						  'non_blank' => 'true',
		  },
		  "newpassword" => {
				  'valid_format' => 'rbac_password',
				  'non_blank'    => 'true',
				  'format_msg' => 'must be alphanumeric and must have at least 8 characters'
		  },
	};

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	# check to change password
	if ( $json_obj->{ 'newpassword' } )
	{
		if ( not exists $json_obj->{ 'password' } )
		{
			my $msg = "The parameter password is required.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}

		elsif ( $json_obj->{ 'newpassword' } eq $json_obj->{ 'password' } )
		{
			my $msg = "The new password must be different to the current password.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}

		elsif ( !&checkValidUser( $user, $json_obj->{ 'password' } ) )
		{
			my $msg = "Invalid current password.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

	if ( $user eq 'root' )
	{
		if ( exists $json_obj->{ 'newpassword' } )
		{
			$error = &changePassword( $user,
								 $json_obj->{ 'newpassword' },
								 $json_obj->{ 'newpassword' } );

			if ( $error )
			{
				my $msg = "Modifying $user.";
				return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
			}
		}

		if ( exists $json_obj->{ 'newpassword' } )
		{
			if (    $json_obj->{ 'status' } eq 'enable'
				&& &getZAPI( "status" ) eq 'false' )
			{
				$error = &setZAPI( "enable" );
			}
			elsif (    $json_obj->{ 'status' } eq 'disable'
					&& &getZAPI( "status" ) eq 'true' )
			{
				$error = &setZAPI( "disable" );
			}

			if ( $error )
			{
				my $msg = "Modifying $user.";
				return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
			}
		}

		# modify zapikey
		if ( exists $json_obj->{ 'zapikey' } )
		{
			include 'Zevenet::Code';
			foreach my $userAux ( &getRBACUserList() )
			{
				next if ( $userAux eq $user );
				if (
					&validateCryptString( &getRBACUserParam( $userAux, 'zapikey' ),
										$json_obj->{ 'zapikey' } )
				)
				{
					my $msg = "The zapikey is not valid.";
					return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
				}
			}
			if ( &setRBACUserZapikey( $user, $json_obj->{ 'zapikey' } ) )
			{
				my $msg = "Changing RBAC $user zapikey.";
				return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
			}
		}
	}

	elsif ( $eload )
	{
		$error = &eload(
			module => 'Zevenet::API32::RBAC::User',
			func   => 'set_system_user_rbac',
			args   => [ $json_obj ],
		);
	}

	else
	{
		my $msg = "The user is not found";
		&httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $msg = "Settings was changed successful.";
	my $body = { description => $desc, message => $msg };

	&httpResponse( { code => 200, body => $body } );
}


1;
