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
use Zevenet::Core;

my $configdir = &getGlobalConfiguration( 'configdir' );

=begin nd
Function: getGSLBFarmConfigIsOK

	Function that check if the config file is OK.

Parameters:
	farmname - Farm name

Returns:
	Scalar - 0 on success or -1 on failure

=cut

sub getGSLBFarmConfigIsOK    # ($farm_name)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $fname ) = @_;

	my $ffile         = &getFarmFile( $fname );
	my $gdnsd         = &getGlobalConfiguration( 'gdnsd' );
	my $gdnsd_command = "$gdnsd -c $configdir\/$ffile/etc checkconf";

	# does not use logAndGet because here it is necessary the error output
	my $run         = `$gdnsd_command 2>&1`;
	my $return_code = $?;

	if ( $return_code or &debug() )
	{
		my $message = $return_code ? 'failure' : 'running';
		&zenlog( "$message: $gdnsd_command", "info", "GSLB" );
		&zenlog( "output: $run ",            "info", "GSLB" );
	}

	return $return_code;
}

=begin nd
Function: getGSLBCheckPort

	This function checks if some service uses the tcp default check port

Parameters:
	farmname - Farm name
	checkport - Port to check

Returns:
	Integer - Number of services that are using the port

=cut

sub getGSLBCheckPort
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $fname, $checkPort ) = @_;

	my $servicePorts = 0;
	my $ftype        = getFarmType( $fname );
	require Tie::File;

	# select all ports used in plugins
	opendir ( DIR, "$configdir\/$fname\_gslb.cfg\/etc\/plugins\/" );
	my @pluginlist = readdir ( DIR );
	closedir ( DIR );

	foreach my $plugin ( @pluginlist )
	{
		if ( $plugin !~ /^\./ )
		{
			open my $fh, '<', "$configdir\/$fname\_$ftype.cfg\/etc\/plugins\/$plugin";
			$servicePorts += grep ( /service_types = tcp_$checkPort([^\d]*)$/, <$fh> );
			close $fh;
		}
	}

	return $servicePorts;
}

=begin nd
Function: getGSLBCheckConf

	Check gslb configuration file. If exist a error, it returns where the error is

Parameters:
	farmname - Farm name

Returns:
	Scalar - 0 on successful or string with error on failure

FIXME:
	Rename with same name used for http farms: getGLSBFarmConfigIsOK
=cut

sub getGSLBCheckConf    #  ( $farmname )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $farmname = shift;

	my $gdnsd = &getGlobalConfiguration( 'gdnsd' );
	my $error =
	  &logAndRunCheck( "$gdnsd -c $configdir\/$farmname\_gslb.cfg/etc checkconf" );

	if ( $error )
	{
		# does not use logAndGet because here it is necessary the error output
		my @run = `$gdnsd -c $configdir\/$farmname\_gslb.cfg/etc checkconf 2>&1`;
		@run = grep ( /# error:/, @run );
		$error = $run[0];
		$error =~ s/# error:\s*//;
		chomp ( $error );

		if ( $error =~ /Zone ([\w\.]+).: Zonefile parse error at line (\d+)/ )
		{
			my $fileZone = "$configdir\/$farmname\_gslb.cfg/etc/zones/$1";
			my $numLine  = $2 - 1;

			require Tie::File;
			tie my @filelines, 'Tie::File', $fileZone;
			$error =
			  "The resource $filelines[$numLine] gslb farm break the configuration. Please check the configuration";
			untie @filelines;
		}
	}

	return $error;
}

1;
