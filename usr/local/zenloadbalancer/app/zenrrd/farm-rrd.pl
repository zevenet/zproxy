#!/usr/bin/perl
#This script is part of Zen Load Balancer, that create rrdtool graphs 
#Copyright (C) 2010  Emilio Campos Martin / Laura Garcia Liebana
#
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.


#Created by Emilio Campos Martin
#


use RRDs;
require ("/usr/local/zenloadbalancer/config/global.conf");
require ("/usr/local/zenloadbalancer/www/functions.cgi");

#$db_if="iface.rrd";
#my @system = `$ifconfig_bin -a`;
#my @system = `$ifconfig_bin`;

#$is_if=0;
@farmlist = &getFarmList();
foreach $farmfile(@farmlist){
	@farmargs = split(/_/,$farmfile);
	$farm = @farmargs[0];
	my $ftype = &getFarmType($farm);
	if ($ftype !~ /datalink/ && $ftype !~ /l4.xnat/){
		$db_if="$farm-farm.rrd";
		my @netstat = &getNetstat("atunp");

		$synconns = &getFarmSYNConns($farm,@netstat);
		@gconns=&getFarmEstConns($farm,@netstat);
		$globalconns = @gconns;
		$waitedconns = &getFarmTWConns($farm,@netstat);

		#process farm
		if (! -f "$rrdap_dir$rrd_dir$db_if"){
			print "Creating traffic rrd database for $farm $rrdap_dir$rrd_dir$db_if ...\n";
			RRDs::create "$rrdap_dir$rrd_dir$db_if",
        	               	"-s 300",
        	               	"DS:pending:GAUGE:600:0:12500000",
        	               	"DS:established:GAUGE:600:0:12500000",
       	                	"DS:closed:GAUGE:600:0:12500000",
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
	
			if ($ERROR = RRDs::error) { print "$0: unable to generate $farm database: $ERROR\n"};
		}
		print "Information for $farm farm graph ...\n";
		print "		pending: $synconns\n";
		print "		established: $globalconns\n";
		print "		closed: $waitedconns\n";
		#update rrd info
		print "Updating Information in $rrdap_dir$rrd_dir$db_if ...\n";
		RRDs::update "$rrdap_dir$rrd_dir$db_if",
			"-t", "pending:established:closed",
			"N:$synconns:$globalconns:$waitedconns";
		#size graph
		$width="500";
		$height="150";
		#create graphs
		@time=("d","w","m","y");
		foreach $time_graph(@time){
			$graph = $basedir.$img_dir.$farm."-".farm."_".$time_graph.".png";
			print "Creating graph in $graph ...\n";
			RRDs::graph ("$graph",
               			"--start=-1$time_graph",
				"-h", "$height", "-w", "$width",
              			"--lazy",
               			"-l 0",
               			"-a", "PNG",
               			"-v CONNECTIONS ON $farm farm",
               			"DEF:pending=$rrdap_dir$rrd_dir$db_if:pending:AVERAGE",
               			"DEF:established=$rrdap_dir$rrd_dir$db_if:established:AVERAGE",
               			"DEF:closed=$rrdap_dir$rrd_dir$db_if:closed:AVERAGE",
		"LINE2:pending#FF0000:Pending Conns\\t", 
				"GPRINT:pending:LAST:Last\\:%6.0lf ", 
				"GPRINT:pending:MIN:Min\\:%6.0lf ",  
				"GPRINT:pending:AVERAGE:Avg\\:%6.0lf ",  
				"GPRINT:pending:MAX:Max\\:%6.0lf \\n",
		"LINE2:established#AAA8E4:Established C\\t", 
				"GPRINT:established:LAST:Last\\:%6.0lf ", 
				"GPRINT:established:MIN:Min\\:%6.0lf ",  
				"GPRINT:established:AVERAGE:Avg\\:%6.0lf ",  
				"GPRINT:established:MAX:Max\\:%6.0lf \\n",
		"LINE2:closed#EEE8A1:Closed Conns\\t", 
				"GPRINT:closed:LAST:Last\\:%6.0lf ", 
				"GPRINT:closed:MIN:Min\\:%6.0lf ",  
				"GPRINT:closed:AVERAGE:Avg\\:%6.0lf ",  
				"GPRINT:closed:MAX:Max\\:%6.0lf \\n");
				       if ($ERROR = RRDs::error) { print "$0: unable to generate $farm farm graph: $ERROR\n"; }
		}
			
		#end process rrd for farm
	}
}	


