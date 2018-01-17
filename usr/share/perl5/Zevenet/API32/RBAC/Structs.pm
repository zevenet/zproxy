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
	my $obj    = &getRBACUserObject( $user );
	my @groups = &getRBACUserGroups( $user );

	my $out;
	$out->{ 'name' }               = $user;
	$out->{ 'webgui_permissions' } = $obj->{ 'webgui_permissions' };
	$out->{ 'zapi_permissions' }   = $obj->{ 'zapi_permissions' };

	#~ $out->{ 'zapikey' } = $obj->{ 'zapikey' };
	$out->{ 'groups' } = \@groups;

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
	use Zevenet::RBAC::User::Core;
	my @allUsers = ();

	foreach my $user ( &getRBACUserList() )
	{
		push @allUsers, &getZapiRBACUsers( $user );
	}
	return \@allUsers;
}

1;
