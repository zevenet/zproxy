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

use Zevenet::Log;
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
	my $status = &getGSLBFarmStatus( $fname );

	return 0 if ( $status eq "up" );

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

	$output = &setGSLBFarmBootStatus( $fname, "up" ) if ( $writeconf );

	unlink ( "/tmp/$fname.lock" ) if -f "/tmp/$fname.lock";

	my $exec = &getGSLBStartCommand( $fname );
	&zenlog( "running $exec", "info", "GSLB" );

	$output = &zsystem( "$exec > /dev/null 2>&1" );
	$output = -1 if ( $output != 0 );

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

	my $filename = &getFarmFile( $fname );
	return -1 if ( $filename eq '-1' );

	if ( &getGSLBFarmConfigIsOK( $fname ) )
	{
		&zenlog(
				"Farm $fname can't be stopped, check the logs and modify the configuration",
				"error", "GSLB" );
		return 1;
	}

	unlink ( "/tmp/$fname.lock" ) if -f "/tmp/$fname.lock";

	if ( $writeconf )
	{
		my $output = &setGSLBFarmBootStatus( $fname, "down" );
		return $output if $output;
	}

	return 0 if ( &getGSLBFarmStatus( $fname ) eq "down" );

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

