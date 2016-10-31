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

require '/usr/local/zenloadbalancer/config/global.conf';
require '/usr/local/zenloadbalancer/www/functions_ext.cgi';

my $name   = $ARGV[0];
my $action = $ARGV[1];

my $backupdir = &getGlobalConfiguration( 'backupdir' );

if ( $action eq "-c" )
{
	my $backupfor = &getGlobalConfiguration( 'backupfor' );

	my @eject = `$tar -czvf $backupdir\/backup-$name.tar.gz $backupfor`;
}

if ( $action eq "-d" )
{
	my @eject = `$tar -xzvf $backupdir\/backup-$name.tar.gz -C /`;
}

