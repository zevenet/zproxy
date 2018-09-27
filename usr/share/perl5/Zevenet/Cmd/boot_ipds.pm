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
use warnings;

include 'Zevenet::IPDS::DoS::Config';

my $blacklistsConf = &getGlobalConfiguration( 'blacklistsConf' );
my $touch          = &getGlobalConfiguration( 'touch' );
my $blacklistsPath = &getGlobalConfiguration( 'blacklistsPath' );

# blacklists
if ( !-d $blacklistsPath )
{
	system ( &getGlobalConfiguration( 'mkdir' ) . " -p $blacklistsPath" );
	&zenlog( "Created $blacklistsPath directory." );
}

# create list config if doesn't exist
if ( !-e $blacklistsConf )
{
	system ( "$touch $blacklistsConf" );
	&zenlog( "Created $blacklistsConf file." );
}

#dos
&setDOSCreateFileConf();

exit 0;
