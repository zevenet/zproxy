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

my $configdir = &getGlobalConfiguration( 'configdir' );

=begin nd
Function: getDatalinkFarmServers

	List all farm backends and theirs configuration

Parameters:
	farmname - Farm name

Returns:
	ref array - list of backends. Each item has the format: ";index;ip;iface;weight;priority;status"
		
FIXME:
	changes output to hash format

=cut

sub getDatalinkFarmServers    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $first         = "true";
	my $sindex        = 0;
	my @servers;

	open my $fd, '<', "$configdir/$farm_filename";

	while ( my $line = <$fd> )
	{
		# ;server;45.2.2.3;eth0;1;1;up
		if ( $line ne "" && $line =~ /^\;server\;/ && $first ne "true" )
		{
			$line =~ s/^\;server/$sindex/g;    #, $line;
			chomp ( $line );
			push ( @servers, $line );
			$sindex = $sindex + 1;
		}
		else
		{
			$first = "false";
		}
	}
	close $fd;

	return \@servers;
}

=begin nd
Function: getDatalinkFarmBackends

	List all farm backends and theirs configuration

Parameters:
	farmname - Farm name

Returns:
	array - list of backends. Each item has the format: ";index;ip;iface;weight;priority;status"

=cut

sub getDatalinkFarmBackends    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $first         = "true";
	my $sindex        = 0;
	my @servers;

	require Zevenet::Farm::Base;
	my $farmStatus = &getFarmStatus( $farm_name );

	require Zevenet::Alias;
	my $alias = &getAlias( "backend" );

	open my $fd, '<', "$configdir/$farm_filename";

	while ( my $line = <$fd> )
	{
		chomp ( $line );

		# ;server;45.2.2.3;eth0;1;1;up
		if ( $line ne "" && $line =~ /^\;server\;/ && $first ne "true" )
		{
			my @aux = split ( ';', $line );
			my $status = $aux[6];
			$status = "undefined" if ( $farmStatus eq "down" );

			push @servers,
			  {
				alias     => $alias->{ $aux[2] },
				id        => $sindex,
				ip        => $aux[2],
				interface => $aux[3],
				weight    => $aux[4] + 0,
				priority  => $aux[5] + 0,
				status    => $status
			  };
			$sindex = $sindex + 1;
		}
		else
		{
			$first = "false";
		}
	}
	close $fd;

	return \@servers;
}

=begin nd
Function: setDatalinkFarmServer

	Set a backend or create it if it doesn't exist

Parameters:
	id - Backend id, if this id doesn't exist, it will create a new backend
	ip - Real server ip
	interface - Local interface used to connect to such backend.
	weight - The higher the weight, the more request will go to this backend.
	priority -  The lower the priority, the most preferred is the backend.
	farmname - Farm name

Returns:
	none - .

FIXME:
	Not return nothing, do error control

=cut

sub setDatalinkFarmServer    # ($ids,$rip,$iface,$weight,$priority,$farm_name)
{
	my ( $ids, $rip, $iface, $weight, $priority, $farm_name ) = @_;

	require Tie::File;

	my $farm_filename = &getFarmFile( $farm_name );
	my $end           = "false";
	my $i             = 0;
	my $l             = 0;

	# default value
	$weight   ||= 1;
	$priority ||= 1;

	tie my @contents, 'Tie::File', "$configdir\/$farm_filename";

	foreach my $line ( @contents )
	{
		if ( $line =~ /^\;server\;/ && $end ne "true" )
		{
			# modify a backend
			if ( $i eq $ids )
			{
				my $dline = "\;server\;$rip\;$iface\;$weight\;$priority\;up\n";
				splice @contents, $l, 1, $dline;
				$end = "true";
			}
			else
			{
				$i++;
			}
		}
		$l++;
	}

	# create a backend
	if ( $end eq "false" )
	{
		push ( @contents, "\;server\;$rip\;$iface\;$weight\;$priority\;up\n" );
	}

	untie @contents;

	# Apply changes online
	require Zevenet::Farm::Base;
	if ( &getFarmStatus( $farm_name ) eq 'up' )
	{
		require Zevenet::Farm::Action;
		&runFarmStop( $farm_name, "true" );
		&runFarmStart( $farm_name, "true" );
	}

	return;
}

=begin nd
Function: runDatalinkFarmServerDelete

	Delete a backend from a datalink farm

Parameters:
	id - Backend id
	farmname - Farm name

Returns:
	Integer - Error code: return 0 on success or -1 on failure

=cut

sub runDatalinkFarmServerDelete    # ($ids,$farm_name)
{
	my ( $ids, $farm_name ) = @_;

	require Tie::File;
	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;
	my $end           = "false";
	my $i             = 0;
	my $l             = 0;

	tie my @contents, 'Tie::File', "$configdir\/$farm_filename";

	foreach my $line ( @contents )
	{
		if ( $line =~ /^\;server\;/ && $end ne "true" )
		{
			if ( $i eq $ids )
			{
				splice @contents, $l, 1,;
				$output = $?;
				$end    = "true";
			}
			else
			{
				$i++;
			}
		}
		$l++;
	}
	untie @contents;

	# Apply changes online
	require Zevenet::Farm::Base;

	if ( &getFarmStatus( $farm_name ) eq 'up' )
	{
		require Zevenet::Farm::Action;
		&runFarmStop( $farm_name, "true" );
		&runFarmStart( $farm_name, "true" );
	}

	return $output;
}

=begin nd
Function: getDatalinkFarmBackendStatusCtl

	Return from datalink config file, all backends with theirs parameters and status

Parameters:
	farmname - Farm name

Returns:
	array - Each item has the next format: ";server;ip;interface;weight;priority;status"

=cut

sub getDatalinkFarmBackendStatusCtl    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my @output;

	tie my @content, 'Tie::File', "$configdir\/$farm_filename";
	@output = grep /^\;server\;/, @content;
	untie @content;

	return @output;
}

sub getDatalinkFarmBackendAvailableID
{
	my $farmname = shift;

	my $id  = 0;
	my @run = &getDatalinkFarmServers( $farmname );

	if ( @run > 0 )
	{
		foreach my $l_servers ( @run )
		{
			my @l_serv = split ( ";", $l_servers );

			if ( $l_serv[1] ne "0.0.0.0" )
			{
				if ( $l_serv[0] > $id )
				{
					$id = $l_serv[0];
				}
			}
		}

		if ( $id >= 0 )
		{
			$id++;
		}
	}

	return $id;
}

1;
