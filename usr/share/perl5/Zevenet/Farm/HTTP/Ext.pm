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

my $configdir = &getGlobalConfiguration('configdir');

=begin nd
Function: getHTTPFarm100Continue

	Return 100 continue Header configuration HTTP and HTTPS farms

Parameters:
	farmname - Farm name

Returns:
	scalar - The possible values are: 0 on disabled, 1 on enabled or -1 on failure

=cut
sub getHTTPFarm100Continue    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_type     = &getFarmType( $farm_name );
	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		open FR, '<', "$configdir\/$farm_filename" or return $output;
		$output = 1;	# if the sentence is not in config file, it is enabled
		my @file = <FR>;
		foreach my $line ( @file )
		{
			if ( $line =~ /Ignore100Continue (\d).*/ )
			{
				$output = $1;
				last;
			}
		}
		close FR;
	}

	return $output;
}

=begin nd
Function: setHTTPFarm100Continue

	Enable or disable the HTTP 100 continue header

Parameters:
	farmname - Farm name
	action - The available actions are: 1 to enable or 0 to disable

Returns:
	scalar - The possible values are: 0 on success or -1 on failure

=cut
sub setHTTPFarm100Continue    # ($farm_name, $action)
{
	my ( $farm_name, $action ) = @_;

	my $farm_type     = &getFarmType( $farm_name );
	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		require Tie::File;
		tie my @file, 'Tie::File', "$configdir/$farm_filename";

		# check if 100 continue directive exists
		if ( ! grep(s/^Ignore100Continue\ .*/Ignore100Continue $action/, @file) )
		{
			foreach my $line (@file)
			{
				# put ignore below than rewritelocation
				if ( $line =~ /^Control\s/ )
				{
					$line = "$line\nIgnore100Continue $action";
					last;
				}
			}
		}
		$output = 0;
		untie @file;
	}
	return $output;
}

=begin nd
Function: getHTTPFarmLogs

	Return the log connection tracking status

Parameters:
	farmname - Farm name

Returns:
	scalar - The possible values are: 0 on disabled, possitive value on enabled or -1 on failure

=cut
sub getHTTPFarmLogs    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_type     = &getFarmType( $farm_name );
	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		open FR, '<', "$configdir\/$farm_filename" or return $output;
		$output = 0;	# if the sentence is not in config file, it is disabled
		my @file = <FR>;
		foreach my $line ( @file )
		{
			if ( $line =~ /LogLevel\s+(\d).*/ )
			{
				$output = $1;
				last;
			}
		}
		close FR;
	}

	return $output;
}

=begin nd
Function: setHTTPFarmLogs

	Enable or disable the log connection tracking for a http farm

Parameters:
	farmname - Farm name
	action - The available actions are: "true" to enable or "false" to disable

Returns:
	scalar - The possible values are: 0 on success or -1 on failure

=cut
sub setHTTPFarmLogs    # ($farm_name, $action)
{
	my ( $farm_name, $action ) = @_;

	my $farm_type     = &getFarmType( $farm_name );
	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;

	my $loglvl = ( $action eq "true" ) ? 5 : 0;
	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		require Tie::File;
		tie my @file, 'Tie::File', "$configdir/$farm_filename";

		# check if 100 continue directive exists
		if ( ! grep( s/^LogLevel\s+(\d).*$/LogLevel\t$loglvl/, @file) )
		{
			&zenlog( "Error modifying http logs", "error", "HTTP");
		}
		else
		{
			$output = 0;
		}
		untie @file;
	}
	return $output;
}

1;
