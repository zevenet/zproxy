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

use Zevenet::Config;
include 'Zevenet::IPDS::Blacklist::Core';
include 'Zevenet::IPDS::Blacklist::Runtime';

my ( $listName ) = @ARGV;
my $logger = &getGlobalConfiguration( 'logger' );
my $output;

&setBLDownloadRemoteList( $listName );
if ( &getBLStatus( $listName ) eq 'up' )
{
	$output = &setBLRefreshList( $listName );

	if ( !$output )
	{
		system ( "$logger \"$listName was updated successfully\" -i -t updatelist" );
	}
	else
	{
		system ( "$logger \"Error, updating $listName.\" -i -t updatelist" );
	}
}

exit $output;

