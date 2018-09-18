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
include 'Zevenet::IPDS::WAF::Core';
include 'Zevenet::API33::IPDS::WAF::Structs';

#GET /ipds/waf
sub list_waf_sets
{
	my @sets = &listWAFSet();
	my $desc   = "List the WAF sets";

	return &httpResponse(
				 { code => 200, body => { description => $desc, params => \@sets } } );
}

#  GET /ipds/waf/<set>
sub get_waf_set
{
	my $set = shift;

	my $desc = "Get the WAF set $set";

	unless ( &existWAFSet( $set ) )
	{
		my $msg = "Requested set $set does not exist.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	# ????? temporal
	include 'Zevenet::IPDS::WAF::Parser';
	my $set_st = &getZapiWAFSet( $set );
	my $body = { description => $desc, params => $set_st };

	return &httpResponse( { code => 200, body => $body } );
}

#  POST ipds/waf
sub create_waf_sets
{
	my $json_obj = shift;

	include 'Zevenet::RBAC::Group::Config';

	my $desc = "Create the RBAC group, $json_obj->{ 'name' }";
	my $params = {
				   "name" => {
							   'valid_format' => 'group_name',
							   'non_blank'    => 'true',
							   'required'     => 'true',
				   },
	};

	# Check if it exists
	if ( &getRBACGroupExists( $json_obj->{ 'name' } ) )
	{
		my $msg = "$json_obj->{ 'name' } already exists.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

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


#  DELETE /ipds/waf/<set>
sub delete_waf_set
{
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

		my $msg = "The RBAC group $group has been deleted successful.";
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

1;
