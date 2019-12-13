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

include 'Zevenet::RBAC::Core';
include 'Zevenet::RBAC::Role::Config';
include 'Zevenet::API40::RBAC::Structs';

# GET /rbac/roles
#list
sub get_rbac_all_roles
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my @roleList = sort &getRBACRolesList();
	my $desc     = "List the RBAC roles";

	return &httpResponse(
			  { code => 200, body => { description => $desc, params => \@roleList } } );
}

# GET /rbac/roles/ROLE
#show
sub get_rbac_role
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $role = shift;
	my $desc = "Get the role $role";

	unless ( &getRBACRoleExists( $role ) )
	{
		my $msg = "Requested role doesn't exist.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $roleHash = &getZapiRBACRole( $role );
	my $body = { description => $desc, params => $roleHash };

	return &httpResponse( { code => 200, body => $body } );
}

# POST /rbac/roles
# create
sub add_rbac_role
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;

	my $desc = "Create the RBAC role, $json_obj->{ 'name' }";
	my $params = {
				   "name" => {
							   'valid_format' => 'role_name',
							   'non_blank'    => 'true',
							   'required'     => 'true',
				   },
	};

	# Check if it exists
	if ( &getRBACRoleExists( $json_obj->{ 'name' } ) )
	{
		my $msg = "$json_obj->{ 'name' } already exists.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	# executing the action
	&createRBACRole( $json_obj->{ 'name' } );

	my $output = &getZapiRBACRole( $json_obj->{ 'name' } );

	# check result and return success or failure
	if ( $output )
	{
		my $msg = "Added the RBAC role $json_obj->{ 'name' }";
		my $body = {
					 description => $desc,
					 params      => { 'role' => $output },
					 message     => $msg,
		};
		return &httpResponse( { code => 201, body => $body } );
	}
	else
	{
		my $msg = "Error, trying to create the RBAC role $json_obj->{ name }";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}
}

# DELETE /rbac/roles/ROLE
# delete
sub del_rbac_role
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $role = shift;

	my $desc = "Delete the RBAC role $role";

	unless ( &getRBACRoleExists( $role ) )
	{
		my $msg = "The RBAC role $role doesn't exist";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $used_flag;
	include 'Zevenet::RBAC::Group::Core';
	foreach my $group_it ( &getRBACGroupList() )
	{
		if ( &getRBACGroupParam( $group_it, 'role' ) eq $role )
		{
			$used_flag = 1;
			last;
		}
	}
	if ( $used_flag )
	{
		my $msg = "The RBAC role $role is being used by some group";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	&delRBACRole( $role );

	if ( !&getRBACRoleExists( $role ) )
	{
		my $msg = "The RBAC role $role has been deleted successfully.";
		my $body = {
					 description => $desc,
					 success     => "true",
					 message     => $msg,
		};
		return &httpResponse( { code => 200, body => $body } );
	}
	else
	{
		my $msg = "Deleting the RBAC role $role.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}
}

# PUT /rbac/roles/ROLE
# modify
sub set_rbac_role
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $role     = shift;

	my $desc = "Modify the RBAC role $role";

	# check if the role exists
	unless ( &getRBACRoleExists( $role ) )
	{
		my $msg = "The RBAC role $role does not exist";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	# Check allowed parameters
	my $confStruct = &getRBACRoleParamDefaultStruct();
	foreach my $key ( keys %{ $json_obj } )
	{
		foreach my $param ( keys %{ $json_obj->{ $key } } )
		{
			if ( !exists $confStruct->{ $key }->{ $param } )
			{
				my $msg = "The parameter '$param' is not correct.";
				return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
			}
			elsif ( $json_obj->{ $key }->{ $param } !~ /^(?:true|false)$/ )
			{
				my $msg = "The possible values for a permission are 'true' or 'false'";
				return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
			}
		}
	}

	&setRBACRoleConfigFile( $role, $json_obj );

	my $msg    = "Settings were changed successfully.";
	my $output = &getZapiRBACRole( $role );
	my $body   = { description => $desc, params => $output, message => $msg };

	return &httpResponse( { code => 200, body => $body } );

}

1;
