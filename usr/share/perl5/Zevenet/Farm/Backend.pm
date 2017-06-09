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

use Zevenet::Farm::Backend::Maintenance;

=begin nd
Function: getFarmServers

	List all farm backends and theirs configuration
	
Parameters:
	farmname - Farm name

Returns:
	array - list of backends
		
FIXME:
	changes output to hash format
	
=cut
sub getFarmServers    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my @servers;

	if ( $farm_type eq "tcp" || $farm_type eq "udp" )
	{
		@servers = &getTcpUdpFarmServers( $farm_name );
	}

	if ( $farm_type eq "datalink" )
	{
		@servers = &getDatalinkFarmServers( $farm_name );
	}

	if ( $farm_type eq "l4xnat" )
	{
		@servers = &getL4FarmServers( $farm_name );
	}

	return @servers;
}

=begin nd
Function: setFarmServer

	Add a new Backend
	
Parameters:
	id - Backend id, if this id doesn't exist, it will create a new backend
	ip - Real server ip
	port | iface - Real server port or interface if the farm is datalink
	max - parameter for l4xnat farm
	weight - The higher the weight, the more request will go to this backend.
	priority -  The lower the priority, the most preferred is the backend.
	timeout - HTTP farm parameter
	farmname - Farm name
	service - service name. For HTTP farms

Returns:
	Scalar - Error code: undef on success or -1 on error 
	
FIXME:
	Use a hash
	max parameter is only used by tcp farms
		
=cut
sub setFarmServer # $output ($ids,$rip,$port|$iface,$max,$weight,$priority,$timeout,$farm_name,$service)
{
	my (
		 $ids,      $rip,     $port,      $max, $weight,
		 $priority, $timeout, $farm_name, $service
	) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my $output    = -1;

	&zenlog(
		"setting 'Server $ids $rip $port max $max weight $weight prio $priority timeout $timeout' for $farm_name farm $farm_type"
	);

	if ( $farm_type eq "tcp" || $farm_type eq "udp" )
	{
		$output =
		  &setTcpUdpFarmServer( $ids, $rip, $port, $max, $weight, $priority,
								$farm_name );
	}

	if ( $farm_type eq "datalink" )
	{
		$output =
		  &setDatalinkFarmServer( $ids, $rip, $port, $weight, $priority, $farm_name );
	}

	if ( $farm_type eq "l4xnat" )
	{
		$output = &setL4FarmServer( $ids, $rip, $port, $weight, $priority, $farm_name, $max );
	}

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		$output =
		  &setHTTPFarmServer( $ids, $rip, $port, $priority, $timeout, $farm_name,
							  $service, );
	}

	# FIXME: include setGSLBFarmNewBackend

	return $output;
}

=begin nd
Function: runFarmServerDelete

	Delete a Backend
	
Parameters:
	id - Backend id, if this id doesn't exist, it will create a new backend
	farmname - Farm name
	service - service name. For HTTP farms

Returns:
	Scalar - Error code: undef on success or -1 on error 
			
=cut
sub runFarmServerDelete    # ($ids,$farm_name,$service)
{
	my ( $ids, $farm_name, $service ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my $output    = -1;

	&zenlog( "running 'ServerDelete $ids' for $farm_name farm $farm_type" );

	if ( $farm_type eq "tcp" || $farm_type eq "udp" )
	{
		$output = &runTcpUdpFarmServerDelete( $ids, $farm_name );
	}

	if ( $farm_type eq "datalink" )
	{
		$output = &runDatalinkFarmServerDelete( $ids, $farm_name );
	}

	if ( $farm_type eq "l4xnat" )
	{
		$output = &runL4FarmServerDelete( $ids, $farm_name );
	}

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		$output = &runHTTPFarmServerDelete( $ids, $farm_name, $service );
	}

	if ( $farm_type eq "gslb" )
	{
		$output = &runGSLBFarmServerDelete( $ids, $farm_name, $service );
	}

	return $output;
}

=begin nd
Function: getFarmBackendStatusCtl

	get information about status and configuration of backend
	
Parameters:
	farmname - Farm name

Returns:
	Array - Each profile has a different output format
			
=cut
sub getFarmBackendStatusCtl    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my @output;

	if ( $farm_type eq "tcp" || $farm_type eq "udp" )
	{
		@output = &getTcpUdpFarmBackendStatusCtl( $farm_name );
	}

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		@output = &getHTTPFarmBackendStatusCtl( $farm_name );
	}

	if ( $farm_type eq "datalink" )
	{
		@output = &getDatalinkFarmBackendStatusCtl( $farm_name );
	}

	if ( $farm_type eq "l4xnat" )
	{
		@output = &getL4FarmBackendStatusCtl( $farm_name );
	}

	return @output;
}

=begin nd

Function: getFarmBackendStatus

	Get processed information about status and configuration of backends
	
Parameters:
	farmname - Farm name
	content - Raw backend info

Returns:
	Array - List of backend. Each profile has a different output format 
	
FIXME:
	1. Always is called getFarmBackendStatusCtl function before this function, to pass @content array, then will be useful for avoid bugs call getFarmBackendStatusCtl inside this function.
	Better, call getHTTPFarmBackendStatusCtl inside that getHTTPFarmBackendsStatus function, so it is not necessary work with @content variable
	2. Return a hash
	
=cut
sub getFarmBackendsStatus    # ($farm_name,@content)
{
	my ( $farm_name, @content ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my @output;

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		@output = &getHTTPFarmBackendsStatus( $farm_name, @content );
	}

	if ( $farm_type eq "tcp" || $farm_type eq "udp" )
	{
		@output = &getTcpUdpFarmBackendsStatus( $farm_name, @content );
	}

	if ( $farm_type eq "datalink" )
	{
		@output = &getDatalinkFarmBackendsStatus( @content );
	}

	if ( $farm_type eq "l4xnat" )
	{
		@output = &getL4FarmBackendsStatus( $farm_name, @content );
	}

	return @output;
}

=begin nd

Function: getFarmBackendsClients

	Function that return the status information of sessions
	
Parameters:
	backend - Backend id
	content - Raw backend info
	farmname - Farm name

Returns:
	Integer - Number of clients with session in a backend or -1 on failure
	
FIXME: 
	used in zapi v2 and tcp farms
	
=cut
sub getFarmBackendsClients    # ($idserver,@content,$farm_name)
{
	my ( $idserver, @content, $farm_name ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my $output    = -1;

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		$output = &getHTTPFarmBackendsClients( $idserver, @content, $farm_name );
	}

	if ( $farm_type eq "tcp" || $farm_type eq "udp" )
	{
		$output = &getTcpUdpFarmBackendsClients( $idserver, @content, $farm_name );
	}
	return $output;
}

=begin nd

Function: getFarmBackendsClientsList

	Return session status of all backends of a farm
	
Parameters:
	content - Raw backend info
	farmname - Farm name

Returns:
	Array - The format for each line is: "service" . "\t" . "session_id" . "\t" . "session_value" . "\t" . "backend_id"
	
FIXME: 
	Same name than getFarmBackendsClients function but different uses
	
=cut
sub getFarmBackendsClientsList    # ($farm_name,@content)
{
	my ( $farm_name, @content ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my @output;

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		@output = &getHTTPFarmBackendsClientsList( $farm_name, @content );
	}

	if ( $farm_type eq "tcp" || $farm_type eq "udp" )
	{
		@output = &getTcpUdpFarmBackendsClientsList( $farm_name, @content );
	}

	return @output;
}

=begin nd
Function: setFarmBackendStatus

	Set backend status for a farm
		
Parameters:
	farmname - Farm name
	backend - Backend id
	status - Backend status. The possible values are: "up" or "down"

Returns:
	Integer - 0 on success or other value on failure
	
=cut
sub setFarmBackendStatus    # ($farm_name,$index,$stat)
{
	my ( $farm_name, $index, $stat ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $farm_type     = &getFarmType( $farm_name );

	my $output = -1;

	if ( $farm_type eq "datalink" )
	{
		$output = &setDatalinkFarmBackendStatus( $farm_name, $index, $stat );
	}

	if ( $farm_type eq "l4xnat" )
	{
		$output = &setL4FarmBackendStatus( $farm_name, $index, $stat );
	}

	return $output;
}

1;
