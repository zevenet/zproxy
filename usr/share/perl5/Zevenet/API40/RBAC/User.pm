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

include 'Zevenet::RBAC::User::Core';
include 'Zevenet::API40::RBAC::Structs';

#GET /rbac/users
sub get_rbac_all_users
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $users = &getZapiRBACAllUsers();
	my $desc  = "List the RBAC users";

	return &httpResponse(
				  { code => 200, body => { description => $desc, params => $users } } );
}

#  GET /rbac/users/<user>
sub get_rbac_user
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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
sub add_rbac_user
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;

	require Zevenet::User;
	include 'Zevenet::RBAC::User::Config';

	my $desc = "Create the RBAC user, $json_obj->{ 'name' }";
	my $params = {
		"name" => {
					'valid_format' => 'user_name',
					'non_blank'    => 'true',
					'required'     => 'true',
					'exceptions'   => ["zapi"]
		},

		"service" => {
					   'values'    => ['local', 'ldap'],
					   'non_blank' => 'true',
		},

		# this parameter is required when authentication method is local.
		"password" => {
			'valid_format' => 'rbac_password',
			'non_blank'    => 'true',
			'format_msg' => 'must be alphanumeric and must have between 8 and 16 characters'
		},

	};
	$json_obj->{ 'service' } = 'local' if !( defined $json_obj->{ 'service' } );
	if (     ( defined $json_obj->{ 'service' } )
		 and ( $json_obj->{ 'service' } eq 'local' ) )
	{
		$params->{ 'password' }->{ 'required' } = 'true';
	}
	else
	{
		if ( &getSysUserExists( $json_obj->{ 'name' } ) )
		{
			my $msg = "$json_obj->{ 'name' } is a Operating System User.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	# Check if it exists
	if ( &getRBACUserExists( $json_obj->{ 'name' } ) )
	{
		my $msg = "$json_obj->{ 'name' } already exists.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}
	else
	{
		if ( &getSysUserExists( $json_obj->{ 'name' } ) )
		{
			my $msg = "$json_obj->{ 'name' } is a Operating System User.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

	# executing the action
	&createRBACUser(
					 $json_obj->{ 'name' },
					 $json_obj->{ 'password' },
					 $json_obj->{ 'service' }
	);

	my $output = &getZapiRBACUsers( $json_obj->{ 'name' } );

	# check result and return success or failure
	if ( $output )
	{
		include 'Zevenet::Cluster';
		&runZClusterRemoteManager( 'rbac_user', 'add', $json_obj->{ 'name' } );

		my $msg = "Added the RBAC user $json_obj->{ 'name' }";
		my $body = {
					 description => $desc,
					 params      => { 'user' => $output },
					 message     => $msg,
		};
		return &httpResponse( { code => 201, body => $body } );
	}
	else
	{
		my $msg = "Error, trying to create the RBAC user $json_obj->{ name }";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}
}

#  PUT /rbac/users/<user>
sub set_rbac_user
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $user     = shift;

	include 'Zevenet::RBAC::User::Core';
	include 'Zevenet::RBAC::User::Config';

	my $desc = "Modify the RBAC user $user";
	my $params = {
		 "zapikey"            => { 'valid_format' => 'zapi_key' },
		 "zapi_permissions"   => { 'valid_format' => 'boolean', 'non_blank' => 'true' },
		 "webgui_permissions" => { 'valid_format' => 'boolean', 'non_blank' => 'true' },
	};

	# check if the user exists
	unless ( &getRBACUserExists( $user ) )
	{
		my $msg = "The RBAC user $user doesn't exist";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}
	$params->{ "newpassword" } = {
		'valid_format' => 'rbac_password',
		'non_blank'    => 'true',
		'format_msg' => 'must be alphanumeric and must have between 8 and 16 characters'
	};

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	if (     ( &getRBACUserAuthservice( $user ) ne 'local' )
		 and ( exists $json_obj->{ 'newpassword' } ) )
	{
		$error_msg = "The parameter 'newpassword' is only expected with local users";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
		  if ( $error_msg );
	}

	# Checking the user has a group
	if (    exists $json_obj->{ 'webgui_permissions' }
		 or exists $json_obj->{ 'zapi_permissions' } )
	{
		#Lock resource
		include 'Zevenet::RBAC::Group::Core';
		&lockRBACGroupResource();

		my $userGroup = &getRBACUserGroup( $user );

		&unlockRBACGroupResource();

		unless ( $userGroup )
		{

			my $msg = "The user needs a group to enable permissions.";
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
		my $zapi_user = &getRBACUserbyZapikey( $json_obj->{ 'zapikey' } );
		if ( $zapi_user and $zapi_user ne $user )
		{
			my $msg = "The zapikey is not valid.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}

		&setRBACUserZapikey( $user, $json_obj->{ 'zapikey' } );
	}

	# modify zapi permissions
	if ( exists $json_obj->{ 'zapi_permissions' } )
	{
		if ( not &getRBACUserParam( $user, 'zapikey' ) )
		{
			my $msg = "It is necessary a zapikey to enable the zapi permissions.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}

		if ( &setRBACUserZapiPermissions( $user, $json_obj->{ 'zapi_permissions' } ) )
		{
			my $msg = "Changing RBAC $user zapi permissions.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

	# change password
	if ( exists $json_obj->{ 'newpassword' } )
	{
		if ( &setRBACUserPassword( $user, $json_obj->{ 'newpassword' } ) )
		{
			my $msg = "Changing RBAC $user password.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

	include 'Zevenet::Cluster';
	&runZClusterRemoteManager( 'rbac_user', 'update', $user );

	my $msg    = "Settings were changed successfully.";
	my $output = &getZapiRBACUsers( $user );
	my $body   = { description => $desc, params => $output, message => $msg };

	return &httpResponse( { code => 200, body => $body } );

}

#  DELETE /rbac/users/<user>
sub del_rbac_user
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $user = shift;

	include 'Zevenet::RBAC::User::Config';

	my $desc = "Delete the RBAC user $user";

	unless ( &getRBACUserExists( $user ) )
	{
		my $msg = "The RBAC user $user doesn't exist";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	&delRBACUser( $user );

	if ( !&getRBACUserExists( $user ) )
	{
		include 'Zevenet::Cluster';
		&runZClusterRemoteManager( 'rbac_user', 'delete', $user );

		my $msg = "The RBAC user $user has been deleted successfully.";
		my $body = {
					 description => $desc,
					 success     => "true",
					 message     => $msg,
		};
		return &httpResponse( { code => 200, body => $body } );
	}
	else
	{
		my $msg = "Deleting the RBAC user $user.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}
}

# 	GET /system/users
sub get_system_user_rbac
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	require Zevenet::User;
	my $user = &getUser();

	my $desc = "Retrieve the user $user";
	my $obj  = &getRBACUserObject( $user );

	if ( $obj )
	{
		my $params = {
					   'user'             => $user,
					   'zapi_permissions' => $obj->{ 'zapi_permissions' },
		};

		return &httpResponse(
					 { code => 200, body => { description => $desc, params => $params } } );
	}
}

# 	POST /system/users
sub set_system_user_rbac
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;

	include 'Zevenet::RBAC::User::Config';
	include 'Zevenet::User';

	my $error = 0;
	my $user  = &getUser();
	my $desc  = "Modify the user $user";

	$desc = "Modify the user $user";

	if ( !&getRBACUserExists( $user ) )
	{
		my $msg = "The user is not a RBAC user";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# modify password
	if ( exists $json_obj->{ 'newpassword' } )
	{
		if ( &setRBACUserPassword( $user, $json_obj->{ 'newpassword' } ) )
		{
			my $msg = "Changing the password in the RBAC user $user.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

	# modify zapikey
	if ( exists $json_obj->{ 'zapikey' } )
	{
		my $zapi_user = &getRBACUserbyZapikey( $json_obj->{ 'zapikey' } );
		if ( $zapi_user and $zapi_user ne $user )
		{
			my $msg = "The zapikey is not valid.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
		if ( &setRBACUserZapikey( $user, $json_obj->{ 'zapikey' } ) )
		{
			my $msg = "Changing RBAC $user zapikey.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

	# modify zapi permissions
	if ( exists $json_obj->{ 'zapi_permissions' } )
	{
		if ( not &getRBACUserParam( $user, 'zapikey' ) )
		{
			my $msg = "It is necessary a zapikey to enable the zapi permissions.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}

		if ( &setRBACUserZapiPermissions( $user, $json_obj->{ 'zapi_permissions' } ) )
		{
			my $msg = "Changing RBAC $user zapi permissions.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

	my $msg = "Settings was changed successfully.";
	my $body = { description => $desc, message => $msg };
	return &httpResponse( { code => 200, body => $body } );
}

1;
