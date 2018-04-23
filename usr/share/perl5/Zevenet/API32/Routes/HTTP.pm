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

my $farm_re    = &getValidFormat( 'farm_name' );
my $service_re = &getValidFormat( 'service' );


if ( $ENV{ PATH_INFO } =~ qr{^/farms/$farm_re/services/$service_re/actions$} )
{
	my $mod = 'Zevenet::API32::Farm::MoveService';

	POST qr{^/farms/($farm_re)/services/($service_re)/actions$}, 'move_services', $mod;
}

if ( $ENV{ PATH_INFO } =~ qr{^/farms/$farm_re/(?:addheader|headremove)(:?/\d+)?$} )
{
	my $mod = 'Zevenet::API32::Farm::HTTP::Ext';

	POST qr{^/farms/($farm_re)/addheader$}, 'add_addheader', $mod;
	DELETE qr{^/farms/($farm_re)/addheader/(\d+)$}, 'del_addheader', $mod;
}



1;
