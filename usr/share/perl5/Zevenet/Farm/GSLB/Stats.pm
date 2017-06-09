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

=begin nd
Function: getGSLBGdnsdStats

	Get gslb farm stats from a local socket enabled by gdnsd service

Parameters:
	farmname - Farm name

Returns:     
	String - Return a string with json format
		
=cut
sub getGSLBGdnsdStats    # &getGSLBGdnsdStats ( )
{
	my $farmName   = shift;
	my $wget       = &getGlobalConfiguration( 'wget' );
	my $httpPort   = &getGSLBControlPort( $farmName );
	my $gdnsdStats = `$wget -qO- http://127.0.0.1:$httpPort/json`;

	my $stats;
	if ( $gdnsdStats )
	{
		$stats = decode_json( $gdnsdStats );
	}
	return $stats;
}

=begin nd
Function: getGSLBFarmEstConns

	Get total established connections in a gslb farm

Parameters:
	farmname - Farm name
	netstat - Conntrack -L output

Returns:     
	array - Return all ESTABLISHED conntrack lines for a farm

FIXME:
	change to monitoring libs

=cut
sub getGSLBFarmEstConns    # ($farm_name,@netstat)
{
	my ( $farm_name, @netstat ) = @_;

	my $vip      = &getFarmVip( "vip",  $farm_name );
	my $vip_port = &getFarmVip( "vipp", $farm_name );

	return
	  &getNetstatFilter( "udp", "",
						 "src=.* dst=$vip sport=.* dport=$vip_port .*src=.*",
						 "", @netstat );
}

1;
