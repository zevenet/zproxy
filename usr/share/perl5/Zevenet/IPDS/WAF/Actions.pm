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
include 'Zevenet::IPDS::WAF::Core';

=begin nd
Function: initWAFModule

	Create configuration files and run all needed commands requested to WAF module

Parameters:
	None - .

Returns:
	None - .

=cut

sub initWAFModule
{
	use File::Path qw(make_path);

	my $touch = &getGlobalConfiguration( "touch" );
	my $wafSetDir = &getWAFSetDir();
	my $wafConf   = &getWAFFile();

	make_path( $wafSetDir ) if ( !-d $wafSetDir );
	&logAndRun( "$touch $wafConf" ) if ( !-f $wafConf );
}

1;
