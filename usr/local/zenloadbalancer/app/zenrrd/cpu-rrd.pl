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

use RRDs;
require ("/usr/local/zenloadbalancer/config/global.conf");
require ("/usr/local/zenloadbalancer/www/system_functions.cgi");

$db_cpu="cpu.rrd";

my @cpu=&getCPU();

my $cpu_user;
my $cpu_nice;
my $cpu_sys;
my $cpu_iowait;
my $cpu_irq;
my $cpu_softirq;
my $cpu_idle;
my $cpu_usage;

foreach my $row(@cpu) {

	if ($row->[0] eq "CPUuser") {
		$cpu_user = $row->[1];
		next;
	}

	if ($row->[0] eq "CPUnice") {
		$cpu_nice = $row->[1];
		next;
	}

	if ($row->[0] eq "CPUsys") {
		$cpu_sys = $row->[1];
		next;
	}

	if ($row->[0] eq "CPUiowait") {
		$cpu_iowait = $row->[1];
		next;
	}

	if ($row->[0] eq "CPUirq") {
		$cpu_irq = $row->[1];
		next;
	}

	if ($row->[0] eq "CPUsoftirq") {
		$cpu_softirq = $row->[1];
		next;
	}

	if ($row->[0] eq "CPUidle") {
		$cpu_idle = $row->[1];
		next;
	}

	if ($row->[0] eq "CPUusage") {
		$cpu_usage = $row->[1];
		next;
	}

}

if ($cpu_user =~ /^$/ || $cpu_nice =~ /^$/ || $cpu_sys =~ /^$/ || $cpu_iowait =~ /^$/ || $cpu_irq =~ /^$/ || $cpu_softirq =~ /^$/ || $cpu_idle =~ /^$/ || $cpu_usage =~ /^$/) {
	exit;
}

if (! -f "$rrdap_dir/$rrd_dir/$db_cpu" ) {
	print "Creating cpu rrd data base $rrdap_dir/$rrd_dir/$db_cpu ...\n";
	RRDs::create "$rrdap_dir/$rrd_dir/$db_cpu",
		"--step", "300",
		"DS:user:GAUGE:600:0.00:100.00",
		"DS:nice:GAUGE:600:0.00:100.00",
		"DS:sys:GAUGE:600:0.00:100.00",
		"DS:iowait:GAUGE:600:0.00:100.00",
		"DS:irq:GAUGE:600:0.00:100.00",
		"DS:softirq:GAUGE:600:0.00:100.00",
		"DS:idle:GAUGE:600:0.00:100.00",
		"DS:tused:GAUGE:600:0.00:100.00",
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

	if ($ERROR = RRDs::error) {
		print "$0: unable to generate database: $ERROR\n";
	}
}

print "Information for CPU graph ...\n";
	print "		user: $cpu_user %\n";
	print "		nice: $cpu_nice %\n";
	print "		sys: $cpu_sys %\n";
	print "		iowait: $cpu_iowait %\n";
	print "		irq: $cpu_irq %\n";
	print "		softirq: $cpu_softirq %\n";
	print "		idle: $cpu_idle %\n";
	print "		total used: $cpu_usage %\n";

print "Updating Information in $rrdap_dir/$rrd_dir/$db_cpu ...\n";		
RRDs::update "$rrdap_dir/$rrd_dir/$db_cpu",
	"-t", "user:nice:sys:iowait:irq:softirq:idle:tused",
	"N:$cpu_user:$cpu_nice:$cpu_sys:$cpu_iowait:$cpu_irq:$cpu_softirq:$cpu_idle:$cpu_usage";



