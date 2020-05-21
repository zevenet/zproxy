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

if ( $ENV{ PATH_INFO } =~ qr{^/routing} )
{
	my $mod = 'Zevenet::API40::Interface::Routing';

	my $id_rule   = &getValidFormat( 'route_rule_id' );
	my $id_table  = &getValidFormat( 'route_table_id' );
	my $id_route  = &getValidFormat( 'route_entry_id' );
	my $interface = &getValidFormat( 'interface' );

	GET qr{^/routing/rules$},               'list_routing_rules',  $mod;
	POST qr{^/routing/rules$},              'create_routing_rule', $mod;
	PUT qr{^/routing/rules/($id_rule)$},    'modify_routing_rule', $mod;
	DELETE qr{^/routing/rules/($id_rule)$}, 'delete_routing_rule', $mod;

	GET qr{^/routing/tables$},                     'list_routing_tables',  $mod;
	GET qr{^/routing/tables/($id_table)$},         'get_routing_table',    $mod;
	POST qr{^/routing/tables/($id_table)/routes$}, 'create_routing_entry', $mod;
	PUT qr{^/routing/tables/($id_table)/routes/([^\/]+)$},
	  'modify_routing_entry', $mod;
	DELETE qr{^/routing/tables/($id_table)/routes/($id_route)$},
	  'delete_routing_entry', $mod;

	GET qr{^/routing/tables/($id_table)/unmanaged$}, 'get_routing_isolate', $mod;
	POST qr{^/routing/tables/($id_table|\*)/unmanaged$}, 'add_routing_isolate',
	  $mod;
	DELETE qr{^/routing/tables/($id_table|\*)/unmanaged/($interface)$},
	  'del_routing_isolate', $mod;
}

1;
