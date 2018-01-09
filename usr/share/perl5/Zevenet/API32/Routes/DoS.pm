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


if ( $ENV{ PATH_INFO } =~ qr{/ipds/dos} )
{
	my $mod = 'Zevenet::API32::IPDS::DoS';

	my $farm_re  = &getValidFormat( 'farm_name' );
	my $dos_rule = &getValidFormat( 'dos_name' );

	#  GET dos settings
	GET qr{^/ipds/dos/rules$}, 'get_dos_rules', $mod;

	#  GET dos settings
	GET qr{^/ipds/dos$}, 'get_dos', $mod;

	#  GET dos configuration
	GET qr{^/ipds/dos/($dos_rule)$}, 'get_dos_rule', $mod;

	#  POST dos settings
	POST qr{^/ipds/dos$}, 'create_dos_rule', $mod;

	#  PUT dos rule
	PUT qr{^/ipds/dos/($dos_rule)$}, 'set_dos_rule', $mod;

	#  DELETE dos rule
	DELETE qr{^/ipds/dos/($dos_rule)$}, 'del_dos_rule', $mod;

	#  POST DoS to a farm
	POST qr{^/farms/($farm_re)/ipds/dos$}, 'add_dos_to_farm', $mod;

	#  DELETE DoS from farm
	DELETE qr{^/farms/($farm_re)/ipds/dos/($dos_rule)$}, 'del_dos_from_farm', $mod;
	
	#  action for a DoS rule
	POST qr{^/ipds/dos/($dos_rule)/actions$}, 'actions_dos', $mod;
	
}

1;
