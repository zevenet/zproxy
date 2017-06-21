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

use Zevenet::Farm::HTTP::Stats;
use Zevenet::Farm::L4xNAT::Stats;
use Zevenet::Farm::GSLB::Stats;

=begin nd
Function: getBackendEstConns

	Get all ESTABLISHED connections for a backend
	 
Parameters:
	farmname - Farm name
	ip_backend - IP backend
	port_backend - backend port
	netstat - Conntrack -L output

Returns:
	array - Return all ESTABLISHED conntrack lines for the backend
	
=cut
sub getBackendEstConns    # ($farm_name,$ip_backend,$port_backend,@netstat)
{
	my ( $farm_name, $ip_backend, $port_backend, @netstat ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my @nets      = ();

	if ( $farm_type eq "tcp" || $farm_type eq "udp" )
	{
		@nets =
		  &getTcpUdpBackendEstConns( $farm_name, $ip_backend, $port_backend, @netstat );
	}
	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		@nets =
		  &getHTTPBackendEstConns( $farm_name, $ip_backend, $port_backend, @netstat );
	}
	if ( $farm_type eq "l4xnat" )
	{
		@nets = &getL4BackendEstConns( $farm_name, $ip_backend, @netstat );
	}

	return @nets;
}

=begin nd
Function: getFarmEstConns

	Get all ESTABLISHED connections for a farm
	 
Parameters:
	farmname - Farm name
	netstat - Conntrack -L output

Returns:
	array - Return all ESTABLISHED conntrack lines for a farm

=cut
sub getFarmEstConns    # ($farm_name,@netstat)
{
	my ( $farm_name, @netstat ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my $pid       = &getFarmPid( $farm_name );
	my @nets      = ();

	if ( $pid eq "-" )
	{
		return @nets;
	}

	if ( $farm_type eq "tcp" )
	{
		@nets = &getTcpFarmEstConns( $farm_name, @netstat );
	}

	if ( $farm_type eq "udp" )
	{
		@nets = &getUdpFarmEstConns( $farm_name, @netstat );
	}

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		@nets = &getHTTPFarmEstConns( $farm_name, @netstat );
	}

	if ( $farm_type eq "l4xnat" )
	{
		@nets = &getL4FarmEstConns( $farm_name, @netstat );
	}

	if ( $farm_type eq "gslb" )
	{
		@nets = &getGSLBFarmEstConns( $farm_name, @netstat );
	}

	return @nets;
}

=begin nd
Function: getBackendSYNConns

	Get all SYN connections for a backend
	 
Parameters:
	farmname - Farm name
	ip_backend - IP backend
	port_backend - backend port
	netstat - Conntrack -L output

Returns:
	array - Return all SYN conntrack lines for a backend of a farm

=cut
sub getBackendSYNConns    # ($farm_name,$ip_backend,$port_backend,@netstat)
{
	my ( $farm_name, $ip_backend, $port_backend, @netstat ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my @nets      = ();

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		@nets =
		  &getHTTPBackendSYNConns( $farm_name, $ip_backend, $port_backend, @netstat );
	}
	if ( $farm_type eq "tcp" )
	{
		@nets =
		  &getTcpBackendSYNConns( $farm_name, $ip_backend, $port_backend, @netstat );
	}
	if ( $farm_type eq "udp" )
	{
		@nets =
		  &getUdpBackendSYNConns( $farm_name, $ip_backend, $port_backend, @netstat );
	}
	if ( $farm_type eq "l4xnat" )
	{
		@nets =
		  &getL4BackendSYNConns( $farm_name, $ip_backend, $port_backend, @netstat );
	}

	return @nets;
}

=begin nd
Function: getFarmSYNConns

	Get all SYN connections for a farm
	 
Parameters:
	farmname - Farm name
	netstat - Conntrack -L output

Returns:
	array - Return all SYN conntrack lines for a farm

=cut
sub getFarmSYNConns    # ($farm_name, @netstat)
{
	my ( $farm_name, @netstat ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my @nets      = ();

	if ( $farm_type eq "tcp" )
	{
		@nets = &getTcpFarmSYNConns( $farm_name, @netstat );
	}

	if ( $farm_type eq "udp" )
	{
		@nets = &getUdpFarmSYNConns( $farm_name, @netstat );
	}

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		@nets = &getHTTPFarmSYNConns( $farm_name, @netstat );
	}

	if ( $farm_type eq "l4xnat" )
	{
		@nets = &getL4FarmSYNConns( $farm_name, @netstat );
	}

	return @nets;
}

1;
