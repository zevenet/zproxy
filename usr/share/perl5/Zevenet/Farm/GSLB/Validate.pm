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
Function: getGSLBFarmConfigIsOK

	Function that check if the config file is OK.
	
Parameters:
	farmname - Farm name

Returns:
	Scalar - 0 on success or -1 on failure
	
=cut
sub getGSLBFarmConfigIsOK    # ($farm_name)
{
	my ( $fname ) = @_;

	my $ffile  = &getFarmFile( $fname );
	my $output = -1;
	my $gdnsd  = &getGlobalConfiguration( 'gdnsd' );

	my $gdnsd_command = "$gdnsd -c $configdir\/$ffile/etc checkconf";

	&zenlog( "running: $gdnsd_command" );
	my $run = `$gdnsd_command 2>&1`;
	$output = $?;
	&zenlog( "output: $run " );

	return $output;
}

=begin nd
Function: getCheckPort

	This function checks if some service uses the tcp default check port

Parameters:
	farmname - Farm name
	checkport - Port to check 

Returns:
	Integer - Number of services that are using the port
               
=cut
sub getCheckPort
{
	my ( $fname, $checkPort ) = @_;

	my $ftype        = &getFarmType( $fname );
	my $servicePorts = 0;

	use Tie::File;

	# select all ports used in plugins
	opendir ( DIR, "$configdir\/$fname\_$ftype.cfg\/etc\/plugins\/" );

	#~ opendir ( DIR, "plugins\/" );
	my @pluginlist = readdir ( DIR );
	closedir ( DIR );
	foreach my $plugin ( @pluginlist )
	{
		if ( $plugin !~ /^\./ )
		{
			my @fileconf = ();

			tie @fileconf, 'Tie::File',
			  "$configdir\/$fname\_$ftype.cfg\/etc\/plugins\/$plugin";

			#~ tie @fileconf, 'Tie::File', "plugins\/$plugin";
			$servicePorts += grep ( /service_types = tcp_$checkPort/,   @fileconf );
			$servicePorts += grep ( /service_types = .+_fg_$checkPort/, @fileconf );

			untie @fileconf;
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
sub getGSLBCheckConf	#  ( $farmname )
{
	my $farmname = shift;

	my $gdnsd = &getGlobalConfiguration( 'gdnsd' );
	my $errormsg = system (
		   "$gdnsd -c $configdir\/$farmname\_gslb.cfg/etc checkconf > /dev/null 2>&1" );
	if ( $errormsg )
	{
		my @run =
		  `$gdnsd -c $configdir\/$farmname\_gslb.cfg/etc checkconf 2>&1`;
		@run = grep ( /# error:/, @run );
		$errormsg = $run[0];
		$errormsg =~ s/# error:\s*//;
		chomp ($errormsg);

		if ( $errormsg =~ /Zone ([\w\.]+).: Zonefile parse error at line (\d+)/ )
		{
			my $fileZone = "$configdir\/$farmname\_gslb.cfg/etc/zones/$1";
			my $numLine  = $2 - 1;

			use Tie::File;
			tie my @filelines, 'Tie::File', $fileZone;
			$errormsg = "The resource $filelines[$numLine] gslb farm break the configuration. Please check the configuration";
			untie @filelines;
		}
	}

	return $errormsg;
}

1;
