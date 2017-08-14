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

my $q = getCGI();
my $farm_re    = &getValidFormat( 'farm_name' );


if ( $q->path_info =~ qr{/ipds/dos} )
{
	require Zevenet::API3::IPDS::DoS;

	my $dos_rule = &getValidFormat( 'dos_name' );

	#  GET dos settings
	GET qr{^/ipds/dos/rules$} => \&get_dos_rules;

	#  GET dos settings
	GET qr{^/ipds/dos$} => \&get_dos;

	#  GET dos configuration
	GET qr{^/ipds/dos/($dos_rule)$} => \&get_dos_rule;

	#  POST dos settings
	POST qr{^/ipds/dos$} => \&create_dos_rule;

	#  PUT dos rule
	PUT qr{^/ipds/dos/($dos_rule)$} => \&set_dos_rule;

	#  DELETE dos rule
	DELETE qr{^/ipds/dos/($dos_rule)$} => \&del_dos_rule;

	#  POST DoS to a farm
	POST qr{^/farms/($farm_re)/ipds/dos$} => \&add_dos_to_farm;

	#  DELETE DoS from a farm
	DELETE qr{^/farms/($farm_re)/ipds/dos/($dos_rule)$} => \&del_dos_from_farm;
}

1;
