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
Function: getFarmServices

	Get a list of services name for a farm
	
Parameters:
	farmname - Farm name

Returns:
	Array - list of service names or -1 on failure
	
=cut
sub getFarmServices    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my $output    = -1;

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		require Zevenet::Farm::HTTP::Service;
		$output = &getHTTPFarmServices( $info, $farm_name );
	}

	if ( $farm_type eq "gslb" )
	{
		require Zevenet::Farm::GSLB::Service;
		$output = &getGSLBFarmServices( $info, $farm_name );
	}

	return $output;
}

1;
