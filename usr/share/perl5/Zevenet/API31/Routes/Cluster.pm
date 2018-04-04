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

if ( $ENV{ PATH_INFO } =~ qr{^/system/cluster} )
{
	my $mod = 'Zevenet::API31::System::Cluster';

	GET    qr{^/system/cluster$},                 'get_cluster',                  $mod;
	POST   qr{^/system/cluster$},                 'enable_cluster',               $mod;
	PUT    qr{^/system/cluster$},                 'modify_cluster',               $mod;
	DELETE qr{^/system/cluster$},                 'disable_cluster',              $mod;
	POST   qr{^/system/cluster/actions$},         'set_cluster_actions',          $mod;
	GET    qr{^/system/cluster/nodes$},           'get_cluster_nodes_status',     $mod;
	GET    qr{^/system/cluster/nodes/localhost$}, 'get_cluster_localhost_status', $mod;
}

1;
