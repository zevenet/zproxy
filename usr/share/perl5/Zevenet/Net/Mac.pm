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

require Zevenet::Config;
my $ip_bin = &getGlobalConfiguration( 'ip_bin' );

=begin nd
Function: addMAC

	Add a MAC Address to an Interface, Vlan or Bonding

Parameters:
	if_ref - network interface hash reference.

Returns:
	integer - ip link set command return code.

=cut

# Execute command line to add a MAC Address to a VLAN or Bonding
sub addMAC    # ($if_ref)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $if_name = shift;
	my $if_mac  = shift;

	&zenlog( "Adding MAC address $if_mac to $if_name", "info", "NETWORK" );

	my $ip_cmd = "$ip_bin link set $if_name address $if_mac";

	my $status = &logAndRun( $ip_cmd );

	return $status;
}

1;
