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

use Zevenet::Farm;

my $configdir = &getGlobalConfiguration( 'configdir' );

=begin nd
Function: getGSLBFarmBootStatus

	Return the farm status at boot zevenet

Parameters:
	farmname - Farm name

Returns:
	Scalar - "up" the farm must run at boot, "down" the farm must not run at boot or -1 on failure

=cut

sub getGSLBFarmBootStatus    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = "down";

	open my $fh, '<', "$configdir/$farm_filename/etc/config";

	while ( my $line = <$fh> )
	{
		next unless length $line;    # skip empty lines

		( undef, $output ) = split ( /;/, $line );
		chomp ( $output );

		last;
	}
	close $fh;

	$output = "down" if ( !$output );

	return $output;
}

=begin nd
Function: getGSLBFarmPid

	Returns farm PID. Through ps command

Parameters:
	farmname - Farm name

Returns:
	Scalar - pid, the farm is running; '-' the farm is stopped or -1 on failure

FIXME:
	Do this function uses pid gslb farms file

=cut

sub getGSLBFarmPid    # ($farm_name)
{
	my ( $fname ) = @_;

	my $farm_filename = &getFarmFile( $fname );
	my $output        = -1;
	my $ps            = &getGlobalConfiguration( 'ps' );
	my $gdnsd         = &getGlobalConfiguration( 'gdnsd' );

	my @run =
	  `$ps -ef | grep "$gdnsd -c $configdir\/$farm_filename" | grep -v grep | awk {'print \$2'}`;

	chomp ( @run );

	if ( $run[0] )
	{
		$output = $run[0];
	}
	else
	{
		$output = "-";
	}

	return $output;
}

=begin nd
Function: getGSLBFarmPidFile

	Returns farm PID. Through ps command

Parameters:
	farmname - Farm name

Returns:
	Scalar - pid, the farm is running; '-' the farm is stopped or -1 on failure

FIXME:
	Use this function to get gslb farms pid

=cut

sub getGSLBFarmPidFile    # ($farm_name)
{
	my ( $farm_name ) = @_;

	return "$configdir\/$farm_name\_gslb.cfg\/etc\/gdnsd.pid";
}

=begin nd
Function: getGSLBFarmVip

	Returns farm vip or farm port

Parameters:
	tag - requested parameter. The options are vip, for virtual ip or vipp, for virtual port
	farmname - Farm name

Returns:
	Scalar - return vip or port of farm or -1 on failure

FIXME:
	return a hash with all parameters

=cut

sub getGSLBFarmVip    # ($info,$farm_name)
{
	my ( $info, $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;
	my $i             = 0;

	open FI, "<$configdir/$farm_filename/etc/config";
	my @file = <FI>;
	close FI;

	foreach my $line ( @file )
	{
		if ( $line =~ /^options =>/ )
		{
			my $vip  = $file[$i + 1];
			my $vipp = $file[$i + 2];

			chomp ( $vip );
			chomp ( $vipp );

			my @vip  = split ( "\ ", $vip );
			my @vipp = split ( "\ ", $vipp );

			if ( $info eq "vip" )   { $output = $vip[2]; }
			if ( $info eq "vipp" )  { $output = $vipp[2]; }
			if ( $info eq "vipps" ) { $output = "$vip[2]\:$vipp[2]"; }
		}
		$i++;
	}

	return $output;
}

=begin nd
Function: runGSLBFarmReload

	Reload zones of a gslb farm

Parameters:
	farmname - Farm name

Returns:
	Integer - Error code: 0 on success or different of 0 on failure

=cut

sub runGSLBFarmReload    # ($farm_name)
{
	my ( $fname ) = @_;

	require Zevenet::System;

	my $type = &getFarmType( $fname );
	my $output;
	my $gdnsd = &getGlobalConfiguration( 'gdnsd' );

	my $gdnsd_command = "$gdnsd -c $configdir\/$fname\_$type.cfg/etc reload-zones";

	&zenlog( "running $gdnsd_command", "info", "GSLB" );

	zsystem( "$gdnsd_command >/dev/null 2>&1" );
	$output = $?;
	if ( $output != 0 )
	{
		$output = -1;
	}

	return $output;
}

=begin nd
Function: getGSLBControlPort

	Get http port where it is the gslb stats

Parameters:
	farmname - Farm name

Returns:
	Integer - port on success or -1 on failure
=cut

sub getGSLBControlPort    # ( $farm_name )
{
	my $farmName = shift;
	my $port     = -1;
	my $ffile    = &getFarmFile( $farmName );
	$ffile = "$configdir/$ffile/etc/config";

	require Tie::File;
	tie my @file, 'Tie::File', $ffile;

	foreach my $line ( @file )
	{
		if ( $line =~ /http_port =\s*(\d+)/ )
		{
			$port = $1 + 0;
			last;
		}
	}
	untie @file;

	return $port;
}

=begin nd
Function: setGSLBControlPort

	Set http port where it is the gslb stats. This port is assigned randomly

Parameters:
	farmname - Farm name

Returns:
	Integer - port on success or -1 on failure
=cut

sub setGSLBControlPort    # ( $farm_name )
{
	my $farmName = shift;

	require Zevenet::Net::Util;

	# set random port
	my $port  = &getRandomPort();
	my $ffile = &getFarmFile( $farmName );
	$ffile = "$configdir/$ffile/etc/config";

	require Tie::File;
	tie my @file, 'Tie::File', $ffile;

	foreach my $line ( @file )
	{
		if ( $line =~ /http_port =/ )
		{
			$line = "   http_port = $port\n";
			last;
		}
	}
	untie @file;

	return $port;
}

=begin nd
Function: setGSLBFarmBootStatus

	Set status at boot zevenet

Parameters:
	farmname - Farm name

Returns:
	integer - Always return 0

FIXME:
	Set a output and do error control
=cut

sub setGSLBFarmBootStatus    # ($farm_name, $status)
{
	my ( $farm_name, $status ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output;
	my $first = 1;

	require Tie::File;
	tie my @filelines, 'Tie::File', "$configdir\/$farm_filename\/etc\/config";

	foreach ( @filelines )
	{
		if ( $first eq 1 )
		{
			if ( $status eq "start" )
			{
				s/\;down/\;up/g;
			}
			else
			{
				s/\;up/\;down/g;
			}
			$first = 0;
			last;
		}
	}
	untie @filelines;

	return $output;
}

=begin nd
Function: setGSLBFarmStatus

	Start or stop a gslb farm

Parameters:
	farmname - Farm name
	zone - Zone name

Returns:
	Integer - Error code: 0 on success or -1 on failure

BUG:
	Always return success

FIXME:
	writeconf is obsolete parameter, always write configuration
=cut

sub setGSLBFarmStatus    # ($farm_name, $status, $writeconf)
{
	my ( $farm_name, $status, $writeconf ) = @_;

	my $command;

	unlink ( "/tmp/$farm_name.lock" );

	if ( $writeconf eq "true" )
	{
		&setGSLBFarmBootStatus( $farm_name, $status );
	}

	if ( $status eq "start" )
	{
		$command = &getGSLBStartCommand( $farm_name );
	}
	else
	{
		$command = &getGSLBStopCommand( $farm_name );
	}

	require Zevenet::System;
	&zenlog( "setGSLBFarmStatus(): Executing $command", "info", "GSLB" );
	zsystem( "$command > /dev/null 2>&1" );

	#TODO
	my $output = 0;

	if ( $output != 0 )
	{
		$output = -1;
	}

	return $output;
}

=begin nd
Function: setGSLBRemoveTcpPort

	This functions removes the tcp default check port from gdnsd config file

Parameters:
	farmnmae - Farm name
	port  - tcp default check port

Returns:
	Ingeter - Error code: 0 on success or -3 on failure
=cut

sub setGSLBRemoveTcpPort
{
	my ( $fname, $port ) = @_;

	my $ffile = &getFarmFile( $fname );
	my $found = 0;
	my $index = 1;

	require Tie::File;
	tie my @fileconf, 'Tie::File', "$configdir/$ffile/etc/config";

	while ( ( $fileconf[$index] !~ /^plugins => / ) && ( $found !~ 2 ) )
	{
		my $line = $fileconf[$index];

		if ( $line =~ /tcp_$port => / )
		{
			$found = 1;
		}

		if ( $found == 1 )
		{
			my $rs = splice ( @fileconf, $index, 1 );

			if ( $line =~ /\}/ )
			{
				$found = 2;
			}
		}

		if ( !$found )
		{
			$index++;
		}
	}

	untie @fileconf;

	$found = -3 if ( $found == 1 );
	$found = 0 if ( $found == 0 || $found == 2 );

	return $found;
}

=begin nd
Function: setGSLBFarmVirtualConf

	Set farm virtual IP and virtual PORT

Parameters:
	vip - Virtual IP
	port - Virtual port. If the port is not sent, the port will not be changed
	farmname - Farm name

Returns:
	none - No returned value

Bug:
	The exit is not well controlled
=cut

sub setGSLBFarmVirtualConf    # ($vip,$vip_port,$farm_name)
{
	my ( $vip, $vipp, $fname ) = @_;

	my $fconf = &getFarmFile( $fname );
	my $type  = &getFarmType( $fname );

	&zenlog( "setting 'VirtualConf $vip $vipp' for $fname farm $type", "info", "GSLB" );

	my $index = 0;
	my $found = 0;

	require Tie::File;
	tie my @fileconf, 'Tie::File', "$configdir/$fconf/etc/config";

	foreach my $line ( @fileconf )
	{
		if ( $line =~ /options => / )
		{
			$found = 1;
		}
		if ( $found == 1 && $line =~ / listen = / )
		{
			$line =~ s/$line/   listen = $vip/g;
		}
		if ( $found == 1 && $line =~ /dns_port = / && $vipp )
		{
			$line =~ s/$line/   dns_port = $vipp/g;
		}
		if ( $found == 1 && $line =~ /\}/ )
		{
			last;
		}
		$index++;
	}

	untie @fileconf;

	return 0;
}

1;
