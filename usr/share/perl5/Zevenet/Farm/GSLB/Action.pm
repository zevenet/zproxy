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

include 'Zevenet::Farm::GSLB::Config';

my $configdir = &getGlobalConfiguration( 'configdir' );

=begin nd
Function: _runGSLBFarmStart

	Start a gslb farm rutine

Parameters:
	fname - Farm name
	writeconf - write this change in configuration status "writeconf" for true or omit it for false

Returns:
	Integer - return 0 on success or -1 on failure

BUG:
	the returned variable must be $output and not $status

=cut

sub _runGSLBFarmStart    # ($fname, $writeconf)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $fname, $writeconf ) = @_;

	require Tie::File;
	include 'Zevenet::Farm::GSLB::Service';
	include 'Zevenet::Farm::GSLB::FarmGuardian';
	require Zevenet::Farm::Base;
	require Zevenet::FarmGuardian;

	my $output;
	my $status = &getFarmStatus( $fname );
	my $file   = &getFarmFile( $fname );

	chomp ( $status );
	if ( $status eq "up" )
	{
		return 0;
	}

	# set fg foreach service
	foreach my $srv ( &getGSLBFarmServices( $fname ) )
	{
		my $fg = &getFGFarm( $fname, $srv );

		if ( !$fg )
		{
			&enableGSLBFarmGuardian( $fname, $srv, 'down' );
		}
		else
		{
			my $obj = &getFGObject( $fg );
			&setGSLBFarmGuardianParams( $fname, $srv, 'time', $obj->{ interval } );
			&setGSLBFarmGuardianParams( $fname, $srv, 'cmd',  $obj->{ command } );
			&enableGSLBFarmGuardian( $fname, $srv, 'up' );
		}
	}

	if ( $writeconf )
	{
		unlink ( "/tmp/$fname.lock" );
		tie my @filelines, 'Tie::File', "$configdir\/$file\/etc\/config";
		my $first = 1;

		foreach ( @filelines )
		{
			if ( $first eq 1 )
			{
				s/\;down/\;up/g;
				$first = 0;
				last;
			}
		}
		untie @filelines;
	}

	my $exec = &getGSLBStartCommand( $fname );

	&zenlog( "running $exec", "info", "GSLB" );

	require Zevenet::System;
	$output = zsystem( "$exec > /dev/null 2>&1" );

	if ( $output != 0 )
	{
		$output = -1;
	}

	return $output;
}

=begin nd
Function: _runGSLBFarmStop

	Stop a gslb farm rutine

Parameters:
	fname - Farm name
	writeconf - write this change in configuration status "writeconf" for true or omit it for false

Returns:
	Integer - return 0 on success or -1 on failure

=cut

sub _runGSLBFarmStop    # ($fname, $writeconf)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $fname, $writeconf ) = @_;

	include 'Zevenet::Farm::GSLB::Validate';
	include 'Zevenet::Farm::GSLB::Config';
	require Zevenet::Farm::Base;

	my $status = &getFarmStatus( $fname );
	if ( $status eq "down" )
	{
		return 0;
	}

	my $filename = &getFarmFile( $fname );
	if ( $filename eq '-1' )
	{
		return -1;
	}

	my $checkfarm = &getGSLBFarmConfigIsOK( $fname );

	if ( $checkfarm )
	{
		&zenlog(
				"Farm $fname can't be stopped, check the logs and modify the configuration",
				"error", "GSLB" );
		return 1;
	}

	if ( $writeconf )
	{
		require Tie::File;
		tie my @filelines, 'Tie::File', "$configdir\/$filename\/etc\/config";
		my $first = 1;

		foreach ( @filelines )
		{
			if ( $first eq 1 )
			{
				s/\;up/\;down/g;
				$status = $?;
				$first  = 0;
			}
		}
		untie @filelines;
	}

	my $exec    = &getGSLBStopCommand( $fname );
	my $pidfile = &getGSLBFarmPidFile( $fname );

	require Zevenet::System;
	&logAndRun( $exec );

	# $exec returns 0 even when gslb stop fails, checked, so force TERM
	my $pid_gslb = &getGSLBFarmPid( $fname );
	&zenlog( "Forcing stop to gslb with PID $pid_gslb", "info", "GSLB" );

	if ( $pid_gslb ne "-" )
	{
		&zenlog( "forcing to stop gslb farm $fname with PID $pid_gslb" );
		kill 'TERM' => $pid_gslb;
	}
	unlink ( $pidfile );

	# since gdnsd is always stopped or killed, we return 0 always
	return 0;
}

=begin nd
Function: getGSLBStartCommand

	Create a string with the gslb farm start command

Parameters:
	farmname - Farm name

Returns:
	string - command

=cut

sub getGSLBStartCommand    # ($farm_name)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farm_name ) = @_;

	my $gdnsd = &getGlobalConfiguration( 'gdnsd' );
	return "$gdnsd -c $configdir\/$farm_name\_gslb.cfg/etc start";
}

=begin nd
Function: getGSLBStopCommand

	Create a string with the gslb farm stop command

Parameters:
	farmname - Farm name

Returns:
	string - command

=cut

sub getGSLBStopCommand    # ($farm_name)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farm_name ) = @_;

	my $gdnsd = &getGlobalConfiguration( 'gdnsd' );
	return "$gdnsd -c $configdir\/$farm_name\_gslb.cfg/etc stop";
}

=begin nd
Function: copyGSLBFarm

	Function that does a copy of a farm configuration.
	If the flag has the value 'del', the old farm will be deleted.

Parameters:
	farmname - Farm name
	newfarmname - New farm name
	flag - It expets a 'del' string to delete the old farm. It is used to copy or rename the farm.

Returns:
	Integer - Error code: return 0 on success or -1 on failure

=cut

sub copyGSLBFarm    # ($farm_name,$new_farm_name)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $fname, $newfname, $del ) = @_;

	use Tie::File;

	my $configdir = &getGlobalConfiguration( "configdir" );
	my $cp        = &getGlobalConfiguration( "cp" );
	my $ffile     = &getFarmFile( $fname );
	my $newffile  = "$newfname\_gslb.cfg";
	my $output    = 0;

	&zenlog( "copying the farm '$fname' in '$newfname'", "info", "GSLB" );

	&logAndRun( "$cp -r $configdir\/$ffile $configdir\/$newffile" );

	# substitute paths in config file
	tie my @lines, 'Tie::File', "$configdir\/$newffile\/etc\/config";
	s/$configdir\/$ffile/$configdir\/$newffile/ for @lines;
	untie @lines;

	if ( $del eq 'del' )
	{
		require File::Path;
		File::Path->import( 'rmtree' );

		$output = 0 if rmtree( ["$configdir/$ffile"] );
	}

	return $output;
}

1;
