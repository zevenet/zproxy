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
Function: runGSLBFarmCreate

	Create a gslb farm
	
Parameters:
	vip - Virtual IP
	port - Virtual port
	farmname - Farm name

Returns:
	Integer - Error code: 0 on success or different of 0 on failure
	
=cut
sub runGSLBFarmCreate    # ($vip,$vip_port,$farm_name)
{
	my ( $fvip, $fvipp, $fname ) = @_;

	my $httpport = &getRandomPort();
	my $type     = "gslb";
	my $ffile    = &getFarmFile( $fname );
	my $output   = -1;
	if ( $ffile != -1 )
	{
		# the farm name already exists
		$output = -2;
		return $output;
	}

	my $farm_path = "$configdir/${fname}_${type}\.cfg";
	&zenlog( "running 'Create' for $fname farm $type in path $farm_path " );

	mkdir "$farm_path";
	mkdir "$farm_path\/etc";
	mkdir "$farm_path\/etc\/zones";
	mkdir "$farm_path\/etc\/plugins";

	open ( my $file, ">", "$configdir\/$fname\_$type.cfg\/etc\/config" );
	print $file ";up\n"
	  . "options => {\n"
	  . "   listen = $fvip\n"
	  . "   dns_port = $fvipp\n"
	  . "   http_port = $httpport\n"
	  . "   http_listen = 127.0.0.1\n" . "}\n\n";
	print $file "service_types => { \n\n}\n\n";
	print $file
	  "plugins => { \n\textmon => { helper_path => \"/usr/local/zenloadbalancer/app/gdnsd/gdnsd_extmon_helper\" },\n}\n\n";
	close $file;

	#run farm
	my $exec = &getGSLBStartCommand( $fname );
	&zenlog( "running $exec" );
	zsystem( "$exec > /dev/null 2>&1" );

	#TODO
	#$output = $?;
	$output = 0;

	if ( $output != 0 )
	{
		&runFarmDelete( $fname );
	}
	return $output;
}

1;
