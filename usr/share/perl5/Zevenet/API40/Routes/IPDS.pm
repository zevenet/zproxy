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

if ( $ENV{ PATH_INFO } =~ qr{^/ipds} )
{
	my $mod = 'Zevenet::API40::IPDS::IPDS';

	GET qr{^/ipds$},         'get_ipds_rules_list', $mod;
	GET qr{^/ipds/package$}, 'get_ipds_package',    $mod;

	PUT qr{^/ipds/package/actions$}, 'set_ipds_package', $mod;
}

1;
