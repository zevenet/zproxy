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

=begin nd
Function: getZapiRBACUsers

	Adjust the format for zapi of the user struct

Parameters:
	User - User name
					
Returns:
	Hash ref - Configuration of a user
	
=cut

sub getZapiRBACUsers
{
	my $user = shift;
	require Zevenet::RBAC::User::Core;
	my $obj   = &getRBACUserObject( $user );
	my $group = &getRBACUserGroup( $user );

	my $out;
	$out->{ 'name' }               = $user;
	$out->{ 'webgui_permissions' } = $obj->{ 'webgui_permissions' };
	$out->{ 'zapi_permissions' }   = $obj->{ 'zapi_permissions' };
	$out->{ 'group' }              = $group;

	return $out;
}

=begin nd
Function: getZapiRBACUsersAll

	Return a list with all RBAC users and theirs configurations

Parameters:
	None - .
					
Returns:
	Array ref - User list
	
=cut

sub getZapiRBACAllUsers
{
	my @allUsers = ();

	foreach my $user ( &getRBACUserList() )
	{
		push @allUsers, &getZapiRBACUsers( $user );
	}
	return \@allUsers;
}

=begin nd
Function: getZapiRBACGroups

	Adjust the format for zapi of the group struct

Parameters:
	Group - Group name

Returns:
	Hash ref - Configuration of a group

=cut

sub getZapiRBACGroups
{
	my $group = shift;
	require Zevenet::RBAC::Group::Core;
	my $obj = &getRBACGroupObject( $group );

	my $out;
	$out->{ 'name' }  = $group;
	$out->{ 'role' }  = $obj->{ 'role' };
	$out->{ 'users' } = $obj->{ 'users' };
	$out->{ 'resources' } =
	  { 'farms' => $obj->{ 'farms' }, 'interfaces' => $obj->{ 'interfaces' } };

	return $out;
}

=begin nd
Function: getZapiRBACAllGroups

	Return a list with all RBAC groups and theirs configurations

Parameters:
	None - .

Returns:
	Array ref - Group object list

=cut

sub getZapiRBACAllGroups
{
	my @allGroups = ();

	foreach my $group ( &getRBACGroupList() )
	{
		push @allGroups, &getZapiRBACGroups( $group );
	}
	return \@allGroups;
}


sub getZapiRBACRole
{
	my $role = shift;
	require Config::Tiny;
	my $roleFile   = &getRBACRoleFile( $role );
	my $fileHandle = Config::Tiny->read( $roleFile );
	my $out;

	my $paramStruct = &getRBACRoleParamDefaultStruct();

	foreach my $structKey ( keys %{ $paramStruct } )
	{
		foreach my $paramKey ( keys %{ $paramStruct->{ $structKey } } )
		{
			$out->{ $structKey }->{ $paramKey } =
			  $fileHandle->{ $structKey }->{ $paramKey };
		}
	}

	return $out;
}

1;
