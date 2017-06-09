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
Function: runFarmCreate

	Create a farm

Parameters:
	type - Farm type. The available options are: "http", "https", "datalink", "l4xnat" or "gslb"
	vip - Virtual IP where the virtual service is listening
	port - Virtual port where the virtual service is listening
	farmname - Farm name
	type - Specify if farm is HTTP or HTTPS
	iface - Inteface wich uses the VIP. This parameter is only used in datalink farms

Returns:
	Integer - return 0 on success or different of 0 on failure

FIXME:
	Use hash to pass the parameters
=cut
sub runFarmCreate    # ($farm_type,$vip,$vip_port,$farm_name,$fdev)
{
	my ( $farm_type, $vip, $vip_port, $farm_name, $fdev ) = @_;

	my $output        = -1;
	my $farm_filename = &getFarmFile( $farm_name );

	if ( $farm_filename != -1 )
	{
		# the farm name already exists
		$output = -2;
		return $output;
	}

	&zenlog( "running 'Create' for $farm_name farm $farm_type" );

	if ( $farm_type =~ /^TCP$/i )
	{
		$output = &runTcpFarmCreate( $vip, $vip_port, $farm_name );
	}

	if ( $farm_type =~ /^UDP$/i )
	{
		$output = &runUdpFarmCreate( $vip, $vip_port, $farm_name );
	}

	if ( $farm_type =~ /^HTTP[S]?$/i )
	{
		$output = &runHTTPFarmCreate( $vip, $vip_port, $farm_name, $farm_type );
	}

	if ( $farm_type =~ /^DATALINK$/i )
	{
		$output = &runDatalinkFarmCreate( $farm_name, $vip, $fdev );
	}

	if ( $farm_type =~ /^L4xNAT$/i )
	{
		$output = &runL4FarmCreate( $vip, $farm_name, $vip_port );
	}

	if ( $farm_type =~ /^GSLB$/i )
	{
		$output = &runGSLBFarmCreate( $vip, $vip_port, $farm_name );
	}

	return $output;
}

1;
