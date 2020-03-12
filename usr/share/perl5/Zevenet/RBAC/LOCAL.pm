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
use Zevenet::Config;
include 'Zevenet::RBAC::Core';

=begin nd
Function: authLOCAL

	Authenticate a user locally

Parameters:
	User - User name
	Password - User password

Returns:
	Integer - Return 1 if the user was properly validated or another value if it failed

=cut

sub authLOCAL
{
	my ( $user, $pass ) = @_;
	my $suc = 0;
	if ( &getRBACServiceEnabled( 'local' ) eq 'true' )
	{
		require Authen::Simple::Passwd;
		Authen::Simple::Passwd->import;

		my $passfile = "/etc/shadow";
		my $simple = Authen::Simple::Passwd->new( path => "$passfile" );

		if ( $simple->authenticate( $user, $pass ) )
		{
			&zenlog( "The user '$user' login with local auth service", "debug", "auth" );
			$suc = 1;
		}
	}
	else
	{
		&zenlog( "LOCAL Authentication Service is not active", "debug", "rbac" );
	}

	return $suc;
}

1;

