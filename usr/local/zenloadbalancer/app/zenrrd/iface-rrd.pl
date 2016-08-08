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

$db_if = "iface.rrd";

my $if_name;
my $is_if = 0;
my $in;
my $out;

my @net = &getNetworkStats("raw");

foreach (@net) {

	my $row = shift @net;
	my @rowi = split("\ ",$row->[0]);
	$if_name = $rowi[0];


	if ( $if_name eq /^lo/ || $if_name eq /^sit/ || $if_name eq /\:/ )
	{
		next;
	}

	if ( $rowi[1] eq "in" )
	{
		$in = $row->[1];
		$row = shift @net;
	}

	my @rowi = split("\ ",$row->[0]);

	if ( $if_name eq $rowi[0] && $rowi[1] eq "out" )
	{
		$out = $row->[1];
	}

	if ( $in =~ /^$/ || $out =~ /^$/ )
	{
		print "$0: Error: Unable to get the data\n";
		next;
	}

	if ( ! -f "$rrdap_dir/$rrd_dir/$if_name$db_if" )
	{
		print "$0: Info: Creating the rrd database $if_name $rrdap_dir/$rrd_dir/$if_name$db_if ...\n";
		RRDs::create "$rrdap_dir/$rrd_dir/$if_name$db_if",
			"--step", "300",
			"DS:in:DERIVE:600:0:12500000",
			"DS:out:DERIVE:600:0:12500000",
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
			print "$0: Error: Unable to generate the rrd database for interface $if_name: $ERROR\n";
		}
	}

	print "$0: Info: Network Stats for interface $if_name ...\n";
	print "$0: Info:	in: $in\n";
	print "$0: Info:	out: $out\n";

	print "$0: Info: Updating data in $rrdap_dir/$rrd_dir/$if_name$db_if ...\n";

	RRDs::update "$rrdap_dir/$rrd_dir/$if_name$db_if",
		"-t", "in:out",
		"N:$in:$out";

	if ( $ERROR = RRDs::error )
	{
		print "$0: Error: Unable to update the rrd database for interface $if_name: $ERROR\n";
	}
}

