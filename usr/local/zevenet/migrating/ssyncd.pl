#!/usr/bin/perl
###############################################################################
#
#    Zevenet Software License
#    This file is part of the Zevenet Load Balancer software package.
#
#    Copyright (C) 2020-today ZEVENET SL, Sevilla (Spain)
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

# Description:
# set the new path for ssyncd binaries

use strict;
use Zevenet::Config;

my $err      = 0;
my $proxy_ng = &getGlobalConfiguration( 'proxy_ng' );
my $ssyncd_bin;
my $ssyncdctl_bin;
my $ssyncd_base;

print "Setting new path for ssyncd ";
if ( $proxy_ng eq "true" )
{
	$ssyncd_bin    = &getGlobalConfiguration( 'ssyncd_zproxy_bin' );
	$ssyncdctl_bin = &getGlobalConfiguration( 'ssyncdctl_zproxy_bin' );
	$ssyncd_base   = &getGlobalConfiguration( 'base_ssyncd_zproxy' );
}
elsif ( $proxy_ng eq "false" )
{
	$ssyncd_bin    = &getGlobalConfiguration( 'ssyncd_pound_bin' );
	$ssyncdctl_bin = &getGlobalConfiguration( 'ssyncdctl_pound_bin' );
	$ssyncd_base   = &getGlobalConfiguration( 'base_ssyncd_pound' );
}

$err += &setGlobalConfiguration( 'ssyncd_bin', $ssyncd_bin );
print ".";
$err += &setGlobalConfiguration( 'ssyncdctl_bin', $ssyncdctl_bin );
print ".";
$err += &setGlobalConfiguration( 'base_ssyncd', $ssyncd_base );
print ".";

$err ? print " ERROR\n" : print " OK\n";
1;
