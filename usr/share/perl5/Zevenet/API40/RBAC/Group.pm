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

include 'Zevenet::RBAC::Group::Core';
include 'Zevenet::API40::RBAC::Structs';

#GET /rbac/groups
sub get_rbac_all_groups
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $groups = &getZapiRBACAllGroups();
	my $desc   = "List the RBAC groups";

	return &httpResponse(
				 { code => 200, body => { description => $desc, params => $groups } } );
}

#  GET /rbac/groups/<group>
sub get_rbac_group
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $group = shift;

	my $desc = "Get the group $group";

	unless ( &getRBACGroupExists( $group ) )
	{
		my $msg = "Requested group doesn't exist.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $groupHash = &getZapiRBACGroups( $group );
	my $body = { description => $desc, params => $groupHash };

	return &httpResponse( { code => 200, body => $body } );
}

#  POST /rbac/groups
sub add_rbac_group
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;

	include 'Zevenet::RBAC::Group::Config';

	my $desc = "Create a RBAC group";
	my $params = {
				   "name" => {
							   'valid_format' => 'group_name',
							   'non_blank'    => 'true',
							   'required'     => 'true',
				   },
	};

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	# Check if it exists
	if ( my $output = &getRBACGroupExists( $json_obj->{ 'name' } ) )
	{
		my $msg = "$json_obj->{ 'name' } already exists.";
		if ( $output == 2 )
		{
			$msg = "$json_obj->{ 'name' } is a Operating System Group.";
		}

		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# executing the action
	&createRBACGroup( $json_obj->{ 'name' }, $json_obj->{ 'password' } );

	my $output = &getZapiRBACGroups( $json_obj->{ 'name' } );

	# check result and return success or failure
	if ( $output )
	{
		include 'Zevenet::Cluster';
		&runZClusterRemoteManager( 'rbac_group', 'add', $json_obj->{ 'name' } );

		my $msg = "Added the RBAC group $json_obj->{ 'name' }";
		my $body = {
					 description => $desc,
					 params      => { 'group' => $output },
					 message     => $msg,
		};
		return &httpResponse( { code => 201, body => $body } );
	}
	else
	{
		my $msg = "Error, trying to create the RBAC group $json_obj->{ name }";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}
}

#  PUT /rbac/groups/<group>
sub set_rbac_group
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $group    = shift;

	include 'Zevenet::RBAC::Group::Config';

	my $desc = "Modify the RBAC group $group";
	my $params = {
				   "role" => {
							   'valid_format' => 'role_name',
							   'non_blank'    => 'true',
							   'non_blank'    => 'true'
				   },
	};

	# check if the group exists
	unless ( &getRBACGroupExists( $group ) )
	{
		my $msg = "The RBAC group $group doesn't exist";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	# Check if role exists
	include 'Zevenet::RBAC::Role::Config';

	if ( !grep ( /^$json_obj->{ role }$/, &getRBACRolesList() ) )
	{
		my $msg = "The role $json_obj->{ 'role' } doesn't exist.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	&setRBACGroupConfigFile( $group, 'role', $json_obj->{ 'role' } );

	my $msg    = "Settings were changed successfully.";
	my $output = &getZapiRBACGroups( $group );
	my $body   = { description => $desc, params => $output, message => $msg };

	return &httpResponse( { code => 200, body => $body } );
}

#  DELETE /rbac/groups/<group>
sub del_rbac_group
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $group = shift;

	include 'Zevenet::RBAC::Group::Config';

	my $desc = "Delete the RBAC group $group";

	unless ( &getRBACGroupExists( $group ) )
	{
		my $msg = "The RBAC group $group doesn't exist";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	&delRBACGroup( $group );

	if ( !&getRBACGroupExists( $group ) )
	{
		include 'Zevenet::Cluster';
		&runZClusterRemoteManager( 'rbac_group', 'delete', $group );

		my $msg = "The RBAC group $group has been deleted successfully.";
		my $body = {
					 description => $desc,
					 success     => "true",
					 message     => $msg,
		};
		return &httpResponse( { code => 200, body => $body } );
	}
	else
	{
		my $msg = "Deleting the RBAC group $group.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}
}

#  POST /rbac/groups/<group>/(intefarces|farms|users)
sub add_rbac_group_resource
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $group    = shift;
	my $type     = shift;
	my $resource = $json_obj->{ 'name' };

	my $type_msg = $type;
	$type_msg =~ s/s$//;

	&lockRBACGroupResource();

	include 'Zevenet::RBAC::Group::Config';

	my $desc = "Add a $type to the group $group";
	my $params = {
				   "name" => {
							   'non_blank' => 'true',
							   'required'  => 'true',
				   },
	};

	# Check if it exists
	if ( !&getRBACGroupExists( $group ) )
	{
		my $msg = "The RBAC group '$group' does not exist";
		&unlockRBACGroupResource();
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );

	if ( $error_msg )
	{
		&unlockRBACGroupResource();
		return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg );
	}

	# check if the object resource exists in the group
	my @resource_list = @{ &getRBACGroupParam( $group, $type ) };
	if ( $resource eq '*' )
	{
		if ( $resource_list[0] eq '*' )
		{
			my $msg = "The $type_msg '$resource' is already in the group '$group'";
			&unlockRBACGroupResource();
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}
	else
	{
		if ( $resource_list[0] eq '*' or grep ( /^$resource$/, @resource_list ) )
		{
			my $msg = "The $type_msg '$resource' is already in the group '$group'";
			&unlockRBACGroupResource();
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}

		# check if the resource exists
		if ( $type eq "interfaces" )
		{
			require Zevenet::Net::Interface;
			if ( !grep ( /^$json_obj->{ 'name' }$/, &getInterfaceList() ) )
			{
				my $msg = "The interface '$resource' does not exist.";
				&unlockRBACGroupResource();
				return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
			}
		}
		elsif ( $type eq "farms" )
		{
			require Zevenet::Farm::Core;
			if ( !&getFarmExists( $resource ) )
			{
				my $msg = "The farm '$resource' does not exist.";
				&unlockRBACGroupResource();
				return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
			}
		}
	}

	if ( $type eq "users" )
	{
		include 'Zevenet::RBAC::User::Core';
		if ( !&getRBACUserExists( $resource ) )
		{
			my $msg = "The user '$resource' does not exist.";
			&unlockRBACGroupResource();
			return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
		}

		if ( &getRBACUserGroup( $resource ) )
		{
			my $msg = "The user '$resource' is already in a group.";
			&unlockRBACGroupResource();
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

	# executing the action
	&addRBACGroupResource( $group, $json_obj->{ 'name' }, $type );

	my $output = &getZapiRBACGroups( $group );

	# check result and return success or failure

	if ( $output )
	{
		if ( $type eq 'users' )
		{
			include 'Zevenet::Cluster';
			&runZClusterRemoteManager( 'rbac_group', 'add_user', $group,
									   $json_obj->{ 'name' } );
		}

		my $msg = "Added the $type_msg '$json_obj->{ name }' to the group '$group'";
		my $body = {
					 description => $desc,
					 params      => { 'group' => $output },
					 message     => $msg,
		};
		&unlockRBACGroupResource();
		return &httpResponse( { code => 200, body => $body } );
	}
	else
	{
		my $msg = "Adding the $type_msg '$json_obj->{ name }' to the group '$group'";
		&unlockRBACGroupResource();
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}
}

#  DELETE /rbac/groups/<group>/(interfaces|farms|users)/<resource_name>
sub del_rbac_group_resource
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $group    = shift;
	my $type     = shift;
	my $resource = shift;

	my $type_msg = $type;
	$type_msg =~ s/s$//;

	include 'Zevenet::RBAC::Group::Config';

	my $desc = "Removing the $type_msg '$resource' from the group '$group'";

	unless ( &getRBACGroupExists( $group ) )
	{
		my $msg = "The RBAC group '$group' does not exist";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	# check if the object resource exists in the group
	unless ( grep ( /^$resource$/, @{ &getRBACGroupParam( $group, $type ) } ) )
	{
		my $msg = "The $type_msg '$resource' is not been used by the group '$group'";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# delete the object resource from the group
	&delRBACGroupResource( $group, $resource, $type );

	if ( !grep ( /^$resource$/, @{ &getRBACGroupParam( $group, $type ) } ) )
	{
		if ( $type eq 'users' )
		{
			include 'Zevenet::Cluster';
			&runZClusterRemoteManager( 'rbac_group', 'del_user', $group, $resource );
		}

		my $msg =
		  "The $type_msg '$resource' has been unlinked successfully from the group '$group'.";
		my $body = {
					 description => $desc,
					 success     => "true",
					 message     => $msg,
		};
		return &httpResponse( { code => 200, body => $body } );
	}
	else
	{
		my $msg = "Removing the $type_msg '$resource' from the group '$group'.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

}

1;
