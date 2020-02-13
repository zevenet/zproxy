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

# Statistics
if ( $q->path_info =~ qr{^/stats} )
{
	my $modules_re = &getValidFormat( 'farm_modules' );
	my $mod        = 'Zevenet::API40::Stats::Statistics';

	# System stats
	GET qr{^/stats/system/network/interfaces$}, 'stats_network_interfaces', $mod;
	GET qr{^/stats/system/memory$},             'stats_mem',                $mod;
	GET qr{^/stats/system/load$},               'stats_load',               $mod;
	GET qr{^/stats/system/cpu$},                'stats_cpu',                $mod;
	GET qr{^/stats/system/connections$},        'stats_conns',              $mod;

	# Farm stats
	GET qr{^/stats/farms/total$},                 'farms_number',        $mod;
	GET qr{^/stats/farms/modules$},               'module_stats_status', $mod;
	GET qr{^/stats/farms/modules/($modules_re)$}, 'module_stats',        $mod;
}

1;
