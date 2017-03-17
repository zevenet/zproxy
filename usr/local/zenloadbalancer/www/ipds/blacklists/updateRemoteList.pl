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

require "/usr/local/zenloadbalancer/www/functions_ext.cgi";
require "/usr/local/zenloadbalancer/www/blacklists.cgi";

my ( $listName ) = @ARGV;
my $logger = &getGlobalConfiguration ( 'logger' );
my $ipset = &getGlobalConfiguration ( 'ipset' );
my $output;

if ( ! system ( "ipset -L $listName 2>/dev/null" ) )
{
	&setBLDownloadRemoteList ( $listName );
	$output = &setBLRefreshList ( $listName );
	
	if ( ! $output )
	{	
		system ("$logger \"$listName was updated successful\" -i -t updatelist");
	}
	else
	{
		system ("$logger \"Error, updatign $listName.\" -i -t updatelist");
	}	
}
else 
{
	$output = -2;
	system ("$logger \"Error, updatign $listName.\" -i -t updatelist");
}

exit $output;
