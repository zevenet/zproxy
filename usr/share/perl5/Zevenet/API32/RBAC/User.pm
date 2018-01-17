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
use Zevenet::RBAC::User::Core;
use Zevenet::API32::RBAC::Structs;

#GET /rbac/users
sub get_rbac_all_users
{
	my $users = &getZapiRBACAllUsers();
	my $desc  = "List the RBAC users";

	return &httpResponse(
				  { code => 200, body => { description => $desc, params => $users } } );
}

#  GET /rbac/users/<user>
sub get_rbac_user
{
	my $user = shift;

	my $desc = "Get the user $user";

	unless ( &getRBACUserExists( $user ) )
	{
		my $msg = "Requested user doesn't exist.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $userHash = &getZapiRBACUsers( $user );
	my $body = { description => $desc, params => $userHash };

	return &httpResponse( { code => 200, body => $body } );
}

#  POST /rbac/users

=begin nd
Function: add_rbac_user

	Create a RBAC user

Parameters:
	name - name for the new user
	password - password for logging
					
Returns:
	return example - .
	
	{
		"description" : "Create the RBAC user, user1",
		"message" : "Added the RBAC user user1",
		"params" : {
			"user" : {
				"name" : "user1",
				"webgui_permissions" : "false",
				"zapi_permissions" : "false",
				"zapikey" : ""
			}
		}
	}
	
=cut

sub add_rbac_user
{
	my $json_obj = shift;

	require Zevenet::RBAC::User::Config;

	my $desc = "Create the RBAC user, $json_obj->{ 'name' }";
	my $params = {
		"name" => {
					'valid_format' => 'user_name',
					'non_blank'    => 'true',
					'required'     => 'true',
					'exceptcions'  => ["zapi"]
		},
		"password" =>
		  { 'valid_format' => 'password', 'non_blank' => 'true', 'required' => 'true' },
	};

	# Check if it exists
	if ( &getRBACUserExists( $json_obj->{ 'name' } ) )
	{
		my $msg = "$json_obj->{ 'name' } already exists.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	# executing the action
	&createRBACUser( $json_obj->{ 'name' }, $json_obj->{ 'password' } );

	my $output = &getZapiRBACUsers( $json_obj->{ 'name' } );

	# check result and return success or failure
	if ( $output )
	{
		require Zevenet::Cluster;
		&runZClusterRemoteManager( 'rbac_user', 'add', $json_obj->{ 'name' } );

		my $msg = "Added the RBAC user $json_obj->{ 'name' }";
		my $body = {
					 description => $desc,
					 params      => { 'user' => $output },
					 message     => $msg,
		};
		return &httpResponse( { code => 200, body => $body } );
	}
	else
	{
		my $msg = "Error, trying to create the RBAC user $json_obj->{ name }";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}
}

=begin nd
Function: add_rbac_user

	Create a RBAC user

Parameters:
	name - name for the new user
	password - password for logging
					
Returns:
	return example - .
	
	{
		"description" : "Create the RBAC user, user1",
		"message" : "Added the RBAC user user1",
		"params" : {
			"user" : {
				"name" : "user1",
				"webgui_permissions" : "false",
				"zapi_permissions" : "false",
				"zapikey" : ""
			}
		}
	}
=cut

#  PUT /rbac/users/<user>
sub set_rbac_user
{
	my $json_obj = shift;
	my $user     = shift;

	require Zevenet::RBAC::User::Config;
	my $desc = "Modify the RBAC user $user";
	my $params = {
		 "zapikey"            => { 'valid_format' => 'zapi_key' },
		 "zapi_permissions"   => { 'valid_format' => 'boolean', 'non_black' => 'true' },
		 "webgui_permissions" => { 'valid_format' => 'boolean', 'non_black' => 'true' },
		 "password" => { 'valid_format' => 'password', 'non_blank' => 'true' },
		 "newpassword" => { 'valid_format' => 'password', 'non_blank' => 'true' },
	};

	# check if the user exists
	unless ( &getRBACUserExists( $user ) )
	{
		my $msg = "The RBAC user $user doesn't exist";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	# modify zapi permissions
	if ( exists $json_obj->{ 'zapi_permissions' } )
	{
		if ( &setRBACUserZapiPermissions( $user, $json_obj->{ 'zapi_permissions' } ) )
		{
			my $msg = "Changing RBAC $user zapi permissions.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

	# modify webgui permissions
	if ( exists $json_obj->{ 'webgui_permissions' } )
	{
		if ( &setRBACUserWebPermissions( $user, $json_obj->{ 'webgui_permissions' } ) )
		{
			my $msg = "Changing RBAC $user webgui permissions.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

	# modify zapikey
	if ( exists $json_obj->{ 'zapikey' } )
	{
		if ( &setRBACUserZapikey( $user, $json_obj->{ 'zapikey' } ) )
		{
			my $msg = "Changing RBAC $user zapikey.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

	# change password
	if ( exists $json_obj->{ 'password' } || exists $json_obj->{ 'newpassword' } )
	{
		unless (    exists $json_obj->{ 'password' }
				 && exists $json_obj->{ 'newpassword' } )
		{
			my $msg =
			  "The parameters password and new password are necessary to change the password.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
		require Zevenet::Login;
		if ( !&checkValidUser( $user, $json_obj->{ 'password' } ) )
		{
			my $msg = "Invalid current password.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}

		if ( &setRBACUserPassword( $user, $json_obj->{ 'newpassword' } ) )
		{
			my $msg = "Changing RBAC $user password.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

	require Zevenet::Cluster;
	&runZClusterRemoteManager( 'rbac_user', 'update', $user );

	my $msg    = "Settings was changed successful.";
	my $output = &getZapiRBACUsers( $user );
	my $body   = { description => $desc, params => $output, message => $msg };

	&httpResponse( { code => 200, body => $body } );

}

#  DELETE /rbac/users/<user>
sub del_rbac_user
{
	my $user = shift;

	require Zevenet::RBAC::User::Config;

	my $desc = "Delete the RBAC user $user";

	unless ( &getRBACUserExists( $user ) )
	{
		my $msg = "The RBAC user $user doesn't exist";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	&delRBACUser( $user );

	if ( !&getRBACUserExists( $user ) )
	{
		require Zevenet::Cluster;
		&runZClusterRemoteManager( 'rbac_user', 'delete', $user );

		my $msg = "The RBAC user $user has been deleted successful.";
		my $body = {
					 description => $desc,
					 success     => "true",
					 message     => $msg,
		};
		return &httpResponse( { code => 200, body => $body } );
	}
	else
	{
		my $msg = "Deleting the RBAC $user.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}
}

1;
