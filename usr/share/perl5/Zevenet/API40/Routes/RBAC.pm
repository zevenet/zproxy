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

if ( $ENV{ PATH_INFO } =~ qr{^/rbac/ldap} )
{
	my $mod = 'Zevenet::API40::RBAC::LDAP';

	#  GET /rbac/ldap
	GET qr{^/rbac/ldap$}, 'get_rbac_ldap', $mod;

	#  POST /rbac/ldap
	POST qr{^/rbac/ldap$}, 'set_rbac_ldap', $mod;

	#  POST /rbac/ldap/actions
	POST qr{^/rbac/ldap/actions$}, 'set_rbac_ldap_actions', $mod;

	#  DELETE /rbac/ldap/actions
	DELETE qr{^/rbac/ldap$}, 'del_rbac_ldap', $mod;
}

if ( $ENV{ PATH_INFO } =~ qr{^/rbac/menus} )
{
	my $mod = 'Zevenet::API40::RBAC::Menus';

	#  GET /rbac/users
	GET qr{^/rbac/menus$}, 'get_rbac_menus', $mod;
}

if ( $ENV{ PATH_INFO } =~ qr{^/rbac/(?:users)} )
{
	my $mod = 'Zevenet::API40::RBAC::User';

	my $user_name = &getValidFormat( 'user_name' );

	#  GET /rbac/users
	GET qr{^/rbac/users$}, 'get_rbac_all_users', $mod;

	#  POST /rbac/users
	POST qr{^/rbac/users$}, 'add_rbac_user', $mod;

	#  GET /rbac/users/<user>
	GET qr{^/rbac/users/($user_name)$}, 'get_rbac_user', $mod;

	#  PUT /rbac/users/<user>
	PUT qr{^/rbac/users/($user_name)$}, 'set_rbac_user', $mod;

	#  DELETE /rbac/users/<user>
	DELETE qr{^/rbac/users/($user_name)$}, 'del_rbac_user', $mod;
}

if ( $ENV{ PATH_INFO } =~ qr{^/rbac/groups} )
{
	my $mod = 'Zevenet::API40::RBAC::Group';

	my $group_name  = &getValidFormat( 'group_name' );
	my $user_name   = &getValidFormat( 'user_name' );
	my $iface_re    = &getValidFormat( 'virt_interface' );
	my $farmname_re = &getValidFormat( 'farm_name' );

	#  GET /rbac/groups
	GET qr{^/rbac/groups$}, 'get_rbac_all_groups', $mod;

	#  POST /rbac/groups
	POST qr{^/rbac/groups$}, 'add_rbac_group', $mod;

	#  GET /rbac/groups/<group>
	GET qr{^/rbac/groups/($group_name)$}, 'get_rbac_group', $mod;

	#  PUT /rbac/groups/<group>
	PUT qr{^/rbac/groups/($group_name)$}, 'set_rbac_group', $mod;

	#  DELETE /rbac/groups/<group>
	DELETE qr{^/rbac/groups/($group_name)$}, 'del_rbac_group', $mod;

	#  POST /rbac/groups/<group>/(intefarces|farms|users)
	POST qr{^/rbac/groups/($group_name)/(interfaces|farms|users)$},
	  'add_rbac_group_resource', $mod;

	#  DELETE /rbac/groups/<group>/(interfaces|farms|users)/<resource_name>
	DELETE
	  qr{^/rbac/groups/($group_name)/(interfaces|farms|users)/($user_name|$iface_re|$farmname_re|\*)$},
	  'del_rbac_group_resource', $mod;
}

if ( $ENV{ PATH_INFO } =~ qr{^/rbac/roles} )
{
	my $mod       = 'Zevenet::API40::RBAC::Role';
	my $role_name = &getValidFormat( 'role_name' );

	# GET /rbac/roles
	GET qr{^/rbac/roles$}, 'get_rbac_all_roles', $mod;

	# GET /rbac/roles/ROLE
	GET qr{^/rbac/roles/($role_name)$}, 'get_rbac_role', $mod;

	# POST /rbac/roles
	POST qr{^/rbac/roles$}, 'add_rbac_role', $mod;

	# DELETE /rbac/roles/ROLE
	DELETE qr{^/rbac/roles/($role_name)$}, 'del_rbac_role', $mod;

	# PUT /rbac/roles/ROLE
	PUT qr{^/rbac/roles/($role_name)$}, 'set_rbac_role', $mod;
}

1;

