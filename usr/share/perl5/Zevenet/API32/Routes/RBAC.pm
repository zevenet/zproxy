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


if ( $ENV{ PATH_INFO } =~ qr{/rbac/users} )
{
	my $mod = 'Zevenet::API32::RBAC::User';

	my $user_name    = &getValidFormat( 'user_name' );

	#GET /rbac/users
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

1;
