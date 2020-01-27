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

use Zevenet::Core;
include 'Zevenet::RBAC::Core';

=begin nd
Function: runRBACAuthUser

	It executes the authentication method for a user

Parameters:
	User - User name
	Password - Password

Returns:
	Integer -  Error code: 1 on success or other value on failure

=cut

sub runRBACAuthUser
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $user         = shift;
	my $pass         = shift;
	my $auth_service = uc ( &getRBACUserAuthservice( $user ) );
	include 'Zevenet::RBAC::' . $auth_service;
	my $functi = 'auth' . $auth_service;

	#my $output = (\&$functi)->( $user,$pass );
	return ( \&$functi )->( $user, $pass );
}
1;
