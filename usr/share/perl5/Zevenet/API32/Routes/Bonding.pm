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


if ( $ENV{ PATH_INFO } =~ qr{^/interfaces/bonding} )
{
	my $mod = 'Zevenet::API32::Interface::Bonding';

	my $bond_re = &getValidFormat( 'bond_interface' );
	my $nic_re  = &getValidFormat( 'nic_interface' );

	GET    qr{^/interfaces/bonding$},                             'get_bond_list',          $mod;
	POST   qr{^/interfaces/bonding$},                             'new_bond',               $mod;
	GET    qr{^/interfaces/bonding/($bond_re)$},                  'get_bond',               $mod;
	PUT    qr{^/interfaces/bonding/($bond_re)$},                  'modify_interface_bond',  $mod;
	DELETE qr{^/interfaces/bonding/($bond_re)$},                  'delete_interface_bond',  $mod;
	POST   qr{^/interfaces/bonding/($bond_re)/slaves$},           'new_bond_slave',         $mod;
	DELETE qr{^/interfaces/bonding/($bond_re)/slaves/($nic_re)$}, 'delete_bond_slave',      $mod;
	POST   qr{^/interfaces/bonding/($bond_re)/actions$},          'actions_interface_bond', $mod;
}

1;
