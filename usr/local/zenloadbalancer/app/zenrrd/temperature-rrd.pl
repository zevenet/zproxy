#!/usr/bin/perl
###############################################################################
#
#     Zen Load Balancer Software License
#     This file is part of the Zen Load Balancer software package.
#
#     Copyright (C) 2014-2016 SOFINTEL IT ENGINEERING SL, Sevilla (Spain)
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

use RRDs;
require ("/usr/local/zenloadbalancer/config/global.conf");
require ("/usr/local/zenloadbalancer/www/system_functions.cgi");
require ("/usr/local/zenloadbalancer/www/functions_ext.cgi");

my $rrdap_dir = &getGlobalConfiguration('rrdap_dir');
my $rrd_dir = &getGlobalConfiguration('rrd_dir');
my $db_temp = "temp.rrd";

my $temp = &getCPUTemp();

if ( $temp =~ /^$/ )
{
	print "$0: Error: Unable to get the data\n";
	exit;
}

if ( ! -f "$rrdap_dir/$rrd_dir/$db_temp" )
{
	print "$0: Info: Creating the rrd database $rrdap_dir/$rrd_dir/$db_temp ...\n";
	RRDs::create "$rrdap_dir/$rrd_dir/$db_temp",
		"--step", "300",
		"DS:temp:GAUGE:600:0:100",
		"RRA:LAST:0.5:1:288",		# daily - every 5 min - 288 reg
		"RRA:MIN:0.5:1:288",		# daily - every 5 min - 288 reg
		"RRA:AVERAGE:0.5:1:288",	# daily - every 5 min - 288 reg
		"RRA:MAX:0.5:1:288",		# daily - every 5 min - 288 reg
		"RRA:LAST:0.5:12:168",		# weekly - every 1 hour - 168 reg
		"RRA:MIN:0.5:12:168",		# weekly - every 1 hour - 168 reg
		"RRA:AVERAGE:0.5:12:168",	# weekly - every 1 hour - 168 reg
		"RRA:MAX:0.5:12:168",		# weekly - every 1 hour - 168 reg
		"RRA:LAST:0.5:96:93",		# monthly - every 8 hours - 93 reg
		"RRA:MIN:0.5:96:93",		# monthly - every 8 hours - 93 reg
		"RRA:AVERAGE:0.5:96:93",	# monthly - every 8 hours - 93 reg
		"RRA:MAX:0.5:96:93",		# monthly - every 8 hours - 93 reg
		"RRA:LAST:0.5:288:372",		# yearly - every 1 day - 372 reg
		"RRA:MIN:0.5:288:372",		# yearly - every 1 day - 372 reg
		"RRA:AVERAGE:0.5:288:372",	# yearly - every 1 day - 372 reg
		"RRA:MAX:0.5:288:372";		# yearly - every 1 day - 372 reg

	if ( $ERROR = RRDs::error )
	{
		print "$0: Error: Unable to generate the rrd database: $ERROR\n";
	}
}

print "$0: Info: Temperature Stats ...\n";
print "$0: Info:	Temp: $temp\n";

print "$0: Info: Updating data in $rrdap_dir/$rrd_dir/$db_temp ...\n";
RRDs::update "$rrdap_dir/$rrd_dir/$db_temp",
	"-t", "temp",
	"N:$temp";

if ( $ERROR = RRDs::error )
{
	print "$0: Error: Unable to update the rrd database: $ERROR\n";
}
