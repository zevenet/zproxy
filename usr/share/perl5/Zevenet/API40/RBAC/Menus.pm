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

include 'Zevenet::RBAC::User::Core';
include 'Zevenet::API40::RBAC::Structs';

#GET /rbac/users
sub get_rbac_menus
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $desc = "List available menus.";

	my $role;
	my $user = &getUser();

	if ( $user eq 'root' )
	{
		# get struct default
		include 'Zevenet::RBAC::Role::Config';
		$role = &getRBACRoleParamDefaultStruct();
	}
	else
	{
		include 'Zevenet::RBAC::Group::Core';
		include 'Zevenet::API40::RBAC::Struct';
		my $group = &getRBACUserGroup( $user );
		my $role_name = &getRBACGroupParam( $group, 'role' );
		$role = &getZapiRBACRole( $role_name );
	}

	# build the strcuct
	my $menus = {};
	foreach my $sect ( keys %{ $role } )
	{
		next if ( !exists $role->{ $sect }->{ menu } );

		# all menus are allowed for root
		$menus->{ $sect } =
		  ( $user eq 'root' )
		  ? 'true'
		  : $role->{ $sect }->{ menu };
	}

	return &httpResponse(
				  { code => 200, body => { description => $desc, params => $menus } } );
}

1;

