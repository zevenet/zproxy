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

my $farm_re       = &getValidFormat( 'farm_name' );
my $l4_session_re = &getValidFormat( 'l4_session' );

my $service_re = &getValidFormat( 'service' );
my $cert_re    = &getValidFormat( 'certificate' );

if ( $ENV{ PATH_INFO } =~ qr{^/farms/$farm_re/sessions} )
{
	my $mod = 'Zevenet::API40::Farm::Session';

	GET qr{^/farms/($farm_re)/sessions$} => 'get_farm_sessions', $mod;

	POST qr{^/farms/($farm_re)/sessions$} => 'add_farm_sessions', $mod;

	DELETE
	  qr{^/farms/($farm_re)/sessions/($l4_session_re)$} => 'delete_farm_sessions',
	  $mod;
}

1;
