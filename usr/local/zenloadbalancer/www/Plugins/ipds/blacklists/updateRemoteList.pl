#!/usr/bin/perl 
###############################################################################
#
#     Zen Load Balancer Software License
#     This file is part of the Zen Load Balancer software package.
#
#     Copyright (C) 2014 SOFINTEL IT ENGINEERING SL, Sevilla (Spain)
#
#     This library is free software; you can redistribute it and/or modify it
#     under the terms of the GNU Lesser General Public License as published
#     by the Free Software Foundation; either version 2.1 of the License, or
#     (at your option) any later version.
#
#     This library is distributed in the hope that it will be useful, but
#     WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
#     General Public License for more details.
#
#     You should have received a copy of the GNU Lesser General Public License
#     along with this library; if not, write to the Free Software Foundation,
#     Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
###############################################################################

require "/usr/local/zenloadbalancer/www/functions_ext.cgi";
require "/usr/local/zenloadbalancer/www/blacklists.cgi";

( my $listName ) = @ARGV;
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
