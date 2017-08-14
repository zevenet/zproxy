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
my $nic_re  = &getValidFormat( 'nic_interface' );
my $bond_re = &getValidFormat( 'bond_interface' );
my $vlan_re = &getValidFormat( 'vlan_interface' );


if ( $q->path_info =~ qr{^/interfaces/floating} )
{
	require Zevenet::API3::Interface::Floating;

	GET qr{^/interfaces/floating$} => \&get_interfaces_floating;
	GET qr{^/interfaces/floating/($nic_re|$bond_re|$vlan_re)$} => \&get_floating;
	PUT qr{^/interfaces/floating/($nic_re|$bond_re|$vlan_re)$} =>
	  \&modify_interface_floating;
	DELETE qr{^/interfaces/floating/($nic_re|$bond_re|$vlan_re)$} =>
	  \&delete_interface_floating;
}

1;
