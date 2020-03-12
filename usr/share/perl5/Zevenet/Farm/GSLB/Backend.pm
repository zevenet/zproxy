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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $id, $fname, $srv ) = @_;

	my $output = 0;
	my $ffile  = &getFarmFile( $fname );

	my @fileconf;
	my $index      = 0;
	my $pluginfile = "";
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

	require Tie::File;

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

	foreach my $line ( @fileconf )
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

	return $output;
}

=begin nd
Function: runGSLBFarmServerDelete

	Delete a resource from a zone

Parameters:
	farmname - Farm name

Returns:
	none - No returned value.

BUG:
	This function has a bad name and is used in wrong way
	It is duplicated with "remGSLBFarmZoneResource"
=cut

sub runGSLBFarmServerDelete    # ($ids,$farm_name,$service)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $ids, $farm_name, $service ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $index         = 0;

	require Tie::File;
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
	none - No returned value.

=cut

sub setGSLBFarmNewBackend    # ($farm_name,$service,$lb,$id,$ipaddress)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $fname, $srv, $lb, $id, $ipaddress ) = @_;

	my $ffile = &getFarmFile( $fname );

	my @fileconf;
	my $found      = 0;
	my $index      = 0;
	my $idx        = 0;
	my $pluginfile = "";

	require Tie::File;

	# Translate to GSLB priority format the BE id.
	if ( $lb eq 'prio' )
	{
		$id = 'primary'   if $id == 1;
		$id = 'secondary' if $id == 2;
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

	foreach my $line ( @fileconf )
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
}

=begin nd
Function: getGSLBFarmBackends

	 Get all backends and theris configuration

Parameters:
	farmname - Farm name
	service - service name

Returns:
	Array ref - Return a array in each element is a hash with the backend
	configuration. The array index is the backend id

=cut

sub getGSLBFarmBackends    # ($farm_name)
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farmname, $service ) = @_;

	require Zevenet::Farm::Base;
	include 'Zevenet::Farm::GSLB::Service';

	my @backendStats;

	my $farmStatus = &getFarmStatus( $farmname );
	my $gslb_stats;

	if ( $farmStatus eq "up" )
	{
		include 'Zevenet::Farm::GSLB::Stats';
		$gslb_stats = &getGSLBGdnsdStats( $farmname );
	}

	# Default port health check

	my $port       = &getGSLBFarmVS( $farmname, $service, "dpc" );
	my $backendsvs = &getGSLBFarmVS( $farmname, $service, "backends" );
	my @be = split ( "\n", $backendsvs );

	#
	# Backends
	#
	foreach my $subline ( @be )
	{
		$subline =~ s/^\s+//;

		if ( $subline =~ /^$/ )
		{
			next;
		}

		# ID and IP
		my @subbe  = split ( " => ", $subline );
		my $id     = $subbe[0];
		my $addr   = $subbe[1];
		my $status = "undefined";

		if ( $farmStatus eq "up" )
		{
			# look for backend status in stats
			foreach my $st_srv ( @{ $gslb_stats->{ 'services' } } )
			{
				if ( $st_srv->{ 'service' } =~ /^$addr\/[\w\-]+$port$/ )
				{
					$status = $st_srv->{ 'real_state' };
					last;
				}
			}
		}

		$id =~ s/^primary$/1/;
		$id =~ s/^secondary$/2/;
		$status = lc $status if defined $status;

		push @backendStats,
		  {
			id     => $id + 0,
			ip     => $addr,
			port   => $port + 0,
			status => $status
		  };
	}

	return \@backendStats;
}

sub getGSLBFarmServiceBackendAvailableID
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $farmname = shift;
	my $service  = shift;

	include 'Zevenet::Farm::GSLB::Service';

	# Get an ID for the new backend
	my $id         = 1;
	my $backendsvs = &getGSLBFarmVS( $farmname, $service, "backends" );
	my @be         = split ( "\n", $backendsvs );

	foreach my $subline ( @be )
	{
		$subline =~ s/^\s+//;
		next unless length $subline;
		$id++;
	}

	return $id;
}

1;

