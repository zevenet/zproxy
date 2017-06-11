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

my $configdir = &getGlobalConfiguration('configdir');

=begin nd
Function: remFarmServiceBackend

	Remove a backend from a gslb service
	
Parameters:
	backend - Backend id
	farmname - Farm name
	service - Service name

Returns:
	Integer - Error code: 0 on success or different of 0 on failure

=cut
sub remFarmServiceBackend    # ($id,$farm_name,$service)
{
	my ( $id, $fname, $srv ) = @_;

	my $output = 0;
	my $ftype  = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );

	my @fileconf;
	my $line;
	my $index      = 0;
	my $pluginfile = "";
	use Tie::File;
	my $found;
	
	# this backend is used if the round robin service has not backends. This one need to have one backend almost.
	my $default_ip = '127.0.0.1';
	my $flagNoDel;
	my @backends = split ( "\n", &getFarmVS( $fname, $srv, "backends" ) );
	if ( scalar @backends == 1 )
	{
		# replace backend and no delete it
		$flagNoDel = 1;
	}

	#Find the plugin file
	opendir ( DIR, "$configdir\/$ffile\/etc\/plugins\/" );
	my @pluginlist = readdir ( DIR );
	foreach my $plugin ( @pluginlist )
	{
		tie @fileconf, 'Tie::File', "$configdir\/$ffile\/etc\/plugins\/$plugin";
		if ( grep ( /^\t$srv => /, @fileconf ) )
		{
			$pluginfile = $plugin;
		}
		untie @fileconf;
	}
	closedir ( DIR );

	tie @fileconf, 'Tie::File', "$configdir/$ffile/etc/plugins/$pluginfile";
	foreach $line ( @fileconf )
	{
		if ( $line =~ /^\t$srv => / )
		{
			$found = 1;
			$index++;
			next;
		}
		if ( $found == 1 && $line =~ /primary => / )
		{
			$output = -2;
			last;
		}
		if ( $found == 1 && $line =~ /$id => / )
		{
			my @backendslist = grep ( /^\s+[1-9].* =>/, @fileconf );
			my $nbackends = @backendslist;
			if ( $nbackends == 1 )
			{
				$output = -2;
			}
			else
			{
				if ( $flagNoDel )
				{
					$line = "\t\t$id => $default_ip";
				}
				else
				{
					splice @fileconf, $index, 1;
				}
			}
			last;
		}
		$index++;
	}
	untie @fileconf;
	$output = $output + $?;

	return $output;
}

=begin nd
Function: runGSLBFarmServerDelete

	Delete a resource from a zone
	
Parameters:
	farmname - Farm name

Returns:
	Integer - Error code: 0 on success or different of 0 on failure
	
BUG:
	This function has a bad name and is used in wrong way
	It is duplicated with "remFarmZoneResource"
	
=cut
sub runGSLBFarmServerDelete    # ($ids,$farm_name,$service)
{
	my ( $ids, $farm_name, $service ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;
	my $index         = 0;

	use Tie::File;
	tie my @configfile, 'Tie::File', "$configdir/$farm_filename/etc/zones/$service";

	foreach my $line ( @configfile )
	{
		if ( $line =~ /\;index_/ )
		{
			my @linesplt = split ( "\;index_", $line );
			my $param = $linesplt[1];
			if ( $ids !~ /^$/ && $ids eq $param )
			{
				splice @configfile, $index, 1,;
			}
		}
		$index++;
	}
	untie @configfile;
	$output = $?;

	return $output;
}

=begin nd
Function: setGSLBFarmNewBackend

	Create a new backend in a gslb service
	 
Parameters:
	farmname - Farm name
	service - Service name
	algorithm - Balancing algorithm. This field can value: "prio" for priority balancing or "roundrobin" for round robin balancing
	backend - Backend id. If algorithm is prio this field must have the value "primary" or "secondary", else backend id will be a integer
	ip - Backend IP

Returns:
	Integer - Error code: 0 on success or -1 on failure

=cut
sub setGSLBFarmNewBackend    # ($farm_name,$service,$lb,$id,$ipaddress)
{
	my ( $fname, $srv, $lb, $id, $ipaddress ) = @_;

	my $output = 0;
	my $ftype  = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );

	my @fileconf;
	my $line;
	my @linesplt;
	my $found      = 0;
	my $index      = 0;
	my $idx        = 0;
	my $pluginfile = "";
	use Tie::File;

	#Find the plugin file
	opendir ( DIR, "$configdir\/$ffile\/etc\/plugins\/" );
	my @pluginlist = readdir ( DIR );
	foreach my $plugin ( @pluginlist )
	{
		tie @fileconf, 'Tie::File', "$configdir\/$ffile\/etc\/plugins\/$plugin";
		if ( grep ( /^\t$srv => /, @fileconf ) )
		{
			$pluginfile = $plugin;
		}
		untie @fileconf;
	}
	closedir ( DIR );
	tie @fileconf, 'Tie::File', "$configdir/$ffile/etc/plugins/$pluginfile";
	foreach $line ( @fileconf )
	{
		if ( $line =~ /^\t$srv => / )
		{
			$found = 1;
			$index++;
			next;
		}
		if ( $found == 1 && $lb eq "prio" && $line =~ /\}/ && $id eq "primary" )
		{
			splice @fileconf, $index, 0, "		$id => $ipaddress";
			last;
		}
		if (    $found == 1
			 && $lb eq "prio"
			 && $line =~ /primary => /
			 && $id eq "primary" )
		{
			splice @fileconf, $index, 1, "		$id => $ipaddress";
			last;
		}
		if ( $found == 1 && $lb eq "prio" && $line =~ /\}/ && $id eq "secondary" )
		{
			splice @fileconf, $index, 0, "		$id => $ipaddress";
			last;
		}
		if (    $found == 1
			 && $lb eq "prio"
			 && $line =~ /secondary => /
			 && $id eq "secondary" )
		{
			splice @fileconf, $index, 1, "		$id => $ipaddress";
			last;
		}
		if ( $found == 1 && $lb eq "roundrobin" && $line =~ /\t\t$id => / )
		{
			splice @fileconf, $index, 1, "		$id => $ipaddress";
			last;
		}
		if ( $found == 1 && $lb eq "roundrobin" && $line =~ / => / )
		{
			# What is the latest id used?
			my @temp = split ( " => ", $line );
			$idx = $temp[0];
			$idx =~ s/^\s+//;
		}
		if ( $found == 1 && $lb eq "roundrobin" && $line =~ /\}/ )
		{
			$idx++;
			splice @fileconf, $index, 0, "		$idx => $ipaddress";
			last;
		}
		$index++;
	}
	untie @fileconf;
	$output = $?;

	return $output;
}

1;
