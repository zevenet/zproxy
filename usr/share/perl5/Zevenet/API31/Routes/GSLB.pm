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


if ( $ENV{ PATH_INFO } =~ qr{^/farms/modules/gslb$} )
{
	my $mod = 'Zevenet::API31::Farm::GSLB';

	GET qr{^/farms/modules/gslb$}, 'farms_gslb', $mod;
}

my $farm_re = &getValidFormat( 'farm_name' );


if ( $ENV{ PATH_INFO } =~ qr{^/farms/$farm_re/zones} )
{
	my $mod = 'Zevenet::API31::Farm::Zone';

	my $zone_re        = &getValidFormat( 'zone' );
	my $resource_id_re = &getValidFormat( 'resource_id' );

	POST   qr{^/farms/($farm_re)/zones$},            'new_farm_zone', $mod;
	PUT    qr{^/farms/($farm_re)/zones/($zone_re)$}, 'modify_zones',  $mod;
	DELETE qr{^/farms/($farm_re)/zones/($zone_re)$}, 'delete_zone',   $mod;
	GET    qr{^/farms/($farm_re)/zones/($zone_re)/resources$}, 'gslb_zone_resources',    $mod;
	POST   qr{^/farms/($farm_re)/zones/($zone_re)/resources$}, 'new_farm_zone_resource', $mod;
	PUT    qr{^/farms/($farm_re)/zones/($zone_re)/resources/($resource_id_re)$}, 'modify_zone_resource', $mod;
	DELETE qr{^/farms/($farm_re)/zones/($zone_re)/resources/($resource_id_re)$}, 'delete_zone_resource', $mod;
}

1;
