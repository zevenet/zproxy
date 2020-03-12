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

use Zevenet::Farm::Core;
use Zevenet::Log;

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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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
Function: getGSLBFarmStatus

	Return current farm process status

Parameters:
	farmname - Farm name

Returns:
	string - return "up" if the process is running or "down" if it isn't

=cut

sub getGSLBFarmStatus    # ($farm_name)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farm_name ) = @_;

	my $pid    = &getGSLBFarmPid( $farm_name );
	my $output = -1;
	my $running_pid;
	$running_pid = kill ( 0, $pid ) if $pid ne "-";

	if ( $pid ne "-" && $running_pid )
	{
		$output = "up";
	}
	else
	{
		unlink &getGSLBFarmPidFile( $farm_name ) if ( $pid ne "-" && !$running_pid );
		$output = "down";
	}

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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $fname ) = @_;

	my $farm_filename = &getFarmFile( $fname );
	my $ps            = &getGlobalConfiguration( 'ps' );
	my $gdnsd         = &getGlobalConfiguration( 'gdnsd' );
	my $grep          = &getGlobalConfiguration( 'grep_bin' );
	my $awk           = &getGlobalConfiguration( 'awk' );

	my $pid =
	  &logAndGet(
		"$ps -ef | $grep \"$gdnsd -c $configdir\/$farm_filename\" | $grep -Ev grep | $awk {'print \$2'}"
	  );

	my $output = ( $pid ) ? $pid : "-";

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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $info, $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;
	my $i             = 0;

	open my $fd, '<', "$configdir/$farm_filename/etc/config";
	my @file = <$fd>;
	close $fd;

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

			if ( $info eq "vip" )  { $output = $vip[2]; }
			if ( $info eq "vipp" ) { $output = $vipp[2]; }
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $fname ) = @_;

	require Zevenet::System;

	my $output;
	my $gdnsd = &getGlobalConfiguration( 'gdnsd' );

	my $gdnsd_command = "$gdnsd -c $configdir\/$fname\_gslb.cfg/etc reload-zones";

	&zenlog( "running $gdnsd_command", "info", "GSLB" );

	&logAndRun( "$gdnsd_command" );
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $farmName = shift;
	my $port     = -1;
	my $ffile    = &getFarmFile( $farmName );
	$ffile = "$configdir/$ffile/etc/config";

	open my $fh, '<', $ffile;

	foreach my $line ( <$fh> )
	{
		if ( $line =~ /http_port =\s*(\d+)/ )
		{
			$port = $1 + 0;
			last;
		}
	}
	close $fh;

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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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

=cut

sub setGSLBFarmStatus    # ($farm_name, $status)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farm_name, $status ) = @_;

	my $command;

	unlink ( "/tmp/$farm_name.lock" );

	&setGSLBFarmBootStatus( $farm_name, $status );

	if ( $status eq "start" )
	{
		$command = &getGSLBStartCommand( $farm_name );
	}
	else
	{
		$command = &getGSLBStopCommand( $farm_name );
	}

	&zenlog( "setGSLBFarmStatus(): Executing $command", "info", "GSLB" );
	&zsystem( "$command" );

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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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
			splice ( @fileconf, $index, 1 );

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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $vip, $vipp, $fname ) = @_;

	my $fconf = &getFarmFile( $fname );

	&zenlog( "setting 'VirtualConf $vip $vipp' for $fname farm gslb",
			 "info", "GSLB" );

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

=begin nd
Function: getGSLBFarmStruct

	Get the GSLB farm struct.

Parameters:
	name - The farm name which is wanted to be retrieved

Returns:
hash ref

=cut

sub getGSLBFarmStruct
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $farm = {};
	$farm->{ name }     = shift;
	$farm->{ filename } = &getFarmFile( $farm->{ name } );
	$farm->{ type }     = "gslb";

	require Zevenet::Farm::Config;
	my $config = &getFarmPlainInfo( $farm->{ name }, "etc/config" );
	my $configSimplefo =
	  &getFarmPlainInfo( $farm->{ name }, "etc/plugins/simplefo.cfg" );
	my $configMultifo =
	  &getFarmPlainInfo( $farm->{ name }, "etc/plugins/multifo.cfg" );

	if ( !( defined $config ) )
	{
		&zenlog(
				 "Not able to load as plain text the main configuration file for farm "
				   . $farm->{ name },
				 "error",
				 "GSLB"
		);
		return undef;
	}
	$farm = {
			  %$farm,
			  %{
				  &getGSLBParseFarmConfig( $config, ["vip", "vport", "state", "services"] )
			  }
	};
	&getGSLBParseBe( $configSimplefo, $farm ) if ( defined $configSimplefo );
	&getGSLBParseBe( $configMultifo,  $farm ) if ( defined $configMultifo );
	$farm->{ status } = &getFarmVipStatus( $farm->{ name } );

	return $farm;
}

=begin nd
Function: _getL4ParseFarmConfig

	Parse the farm file configuration and read/write a certain parameter

Parameters:
	param - requested parameter. The options are "family", "vip", "vipp", "status", "mode", "alg", "proto", "persist", "presisttm", "logs"
	value - value to be changed in case of write operation, undef for read only cases
	config - reference of an array with the full configuration file

Returns:
	Scalar - return the parameter value on read or the changed value in case of write as a string or -1 in other case

=cut

sub getGSLBParseFarmConfig    # ($param, $value, $config)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $generalConfig = shift;
	my $paramArray    = shift;
	my $output        = { services => [], };

	# Temporal hash for iteration saving a service
	my $tmpServiceHashRef = { backends => [], cmd => undef };

	# Parsing Flags
	my $serviceFlag = 0;

	# regEx
	my $stateRegex   = qr/\;(?<status>\w+)$/;
	my $vipRegex     = qr/\s+listen\s=\s(?<vip>\d*\.\d*\.\d*\.\d*)/;
	my $vportRegex   = qr/\s*dns_port\s=\s(?<vport>\d*)$/;
	my $serviceRegex = qr/\s*(?<service>.*)_fg_(?<servicePort>\d*)\s+/;
	my $fgRegex      = qr/\s*cmd\s=\s\[(?<cmd>.*)\]/;

	foreach my $line ( @{ $generalConfig } )
	{
		# Let's clean \t from the line
		$line =~ s/(\t)/ /g;
		if ( $line =~ $stateRegex && grep ( /^state$/, @{ $paramArray } ) )
		{
			$output->{ status } = $+{ status };
			next;
		}

		# VIP
		elsif ( $line =~ $vipRegex && grep ( /^vip$/, @{ $paramArray } ) )
		{
			$output->{ vip } = $+{ vip };
			next;
		}

		# VPORT
		elsif ( $line =~ $vportRegex && grep ( /^vport$/, @{ $paramArray } ) )
		{
			$output->{ vport } = $+{ vport };
			next;
		}

		# SERVICE RR
		if ( grep ( /^services$/, @{ $paramArray } ) )
		{
			if ( $line =~ $serviceRegex )
			{
				$serviceFlag                 = 1;
				$tmpServiceHashRef->{ name } = $+{ service };
				$tmpServiceHashRef->{ port } = $+{ servicePort };
				next;
			}
			if ( $line =~ $fgRegex && $serviceFlag == 1 )
			{
				$tmpServiceHashRef->{ cmd } = $+{ cmd };
				next;
			}
			elsif ( $line =~ /\s*}/ && ( $serviceFlag == 1 ) )
			{
				$serviceFlag = 0;
				my %tmpHash = %{ $tmpServiceHashRef };
				push ( @{ $output->{ services } }, \%tmpHash );
				$tmpServiceHashRef = { backends => [], cmd => undef };
				next;
			}
		}
	}

	return $output;
}

sub getGSLBParseBe
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $plainText    = shift;
	my $hashRef      = shift;
	my $serviceFlag  = 0;
	my $indexService = 0;

	my $beRegex      = qr/\s*(?<type>.*)\s=>\s(?<ip>(\d+\.?)+)/;
	my $serviceRegex = qr/\s*(?<service>.*)\s=>\s\{/;

	shift @{ $plainText };

	foreach my $line ( @{ $plainText } )
	{
		# Let's clean \t from the line
		$line =~ s/(\t)/  /g;

		# There is a service name, check it's index in array
		if ( $line =~ $serviceRegex && $serviceFlag == 0 )
		{
			$indexService = 0;
			$serviceFlag  = 1;
			foreach my $ref ( @{ $hashRef->{ services } } )
			{
				if ( $+{ service } eq $ref->{ name } )
				{
					last;
				}
				$indexService += 1;
			}
			next;
		}

		# There is a backend for the actual array
		elsif ( $line =~ $beRegex && $serviceFlag == 1 )
		{
			push (
				   @{ $hashRef->{ services }[$indexService]->{ backends } },
				   { $+{ type } => $+{ ip } }
			);
			next;
		}
		elsif ( $line =~ /\s*}/ && ( $serviceFlag == 1 ) )
		{
			$serviceFlag  = 0;
			$indexService = 0;
			next;
		}
	}
}

1;

