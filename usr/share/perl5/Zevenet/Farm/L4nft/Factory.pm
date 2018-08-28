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

use Zevenet::Farm::L4xNAT::Action;

my $configdir = &getGlobalConfiguration('configdir');

=begin nd
Function: runL4FarmCreate

	Create a l4xnat farm

Parameters:
	vip - Virtual IP
	port - Virtual port. In l4xnat it ls possible to define multiport using ',' for add ports and ':' for ranges
	farmname - Farm name

Returns:
	Integer - return 0 on success or other value on failure

=cut
sub runL4FarmCreate    # ($vip,$farm_name,$vip_port)
{
	my ( $vip, $farm_name, $vip_port ) = @_;

	my $output    = -1;
	my $farm_type = 'l4xnat';
	my $farm_filename = "$configdir/$farm_name\_$farm_type.cfg";

	require Zevenet::Farm::L4xNAT::Action;
	require Zevenet::Farm::L4xNAT::Config;

	$vip_port = 80 if not defined $vip_port;

#	open FO, ">$configdir\/$farm_name\_$farm_type.cfg";
	# farmname;protocol;vip;vport;nattype;algorithm;persistence;ttl;status;logs
#	print FO "$farm_name\;tcp\;$vip\;$vip_port\;nat\;weight\;none\;120\;up;false\n";
#	close FO;

	my $pid = &runNLBStart();
	if ( $pid <= 0 ) {
		return -1;
	}

	$output = &httpNLBRequest( { farm => $farm_name, configfile => "$farm_filename", method => "PUT", uri => "/farms", body =>  qq({"farms" : [ { "name" : "$farm_name", "virtual-addr" : "$vip", "virtual-ports" : "$vip_port", "protocol" : "tcp", "mode" : "snat", "scheduler" : "weight", "state" : "up" } ] })  } );


#	my $piddir = &getGlobalConfiguration('piddir');
#	if ( !-e "$piddir/${farm_name}_$farm_type.pid" )
#	{
#		# Enable active l4xnat file
#		open FI, ">$piddir\/$farm_name\_$farm_type.pid";
#		close FI;
#	}

	&startL4Farm( $farm_name );

	return $output;    # FIXME
}

=begin nd
Function: runL4FarmDelete

	Delete a l4xnat farm

Parameters:

	farmname - Farm name

Returns:
	Integer - return 0 on success or other value on failure

=cut
sub runL4FarmDelete    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $output    = -1;
#	my $farm_type = 'l4xnat';
#	my $farm_filename = "$configdir/$farm_name\_$farm_type.cfg";

	require Zevenet::Farm::L4xNAT::Action;
#	require Zevenet::Farm::L4xNAT::Config;

#	$vip_port = 80 if not defined $vip_port;

#	open FO, ">$configdir\/$farm_name\_$farm_type.cfg";
	# farmname;protocol;vip;vport;nattype;algorithm;persistence;ttl;status;logs
#	print FO "$farm_name\;tcp\;$vip\;$vip_port\;nat\;weight\;none\;120\;up;false\n";
#	close FO;

	my $pid = &getNLBPid();
	if ( $pid <= 0 ) {
		return 0;
	}

	$output = &httpNLBRequest( { farm => $farm_name, method => "DELETE", uri => "/farms" } );


#	my $piddir = &getGlobalConfiguration('piddir');
#	if ( !-e "$piddir/${farm_name}_$farm_type.pid" )
#	{
#		# Enable active l4xnat file
#		open FI, ">$piddir\/$farm_name\_$farm_type.pid";
#		close FI;
#	}

#	&startL4Farm( $farm_name );

	return $output;    # FIXME
}

1;
