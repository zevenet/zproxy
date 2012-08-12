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
$db_mem="mem.rrd";
#create db memory if not existS
if (! -f "$rrdap_dir$rrd_dir$db_mem" )

	{
	print "Creating memory rrd data base $rrdap_dir$rrd_dir$db_mem ...\n";
	RRDs::create "$rrdap_dir$rrd_dir$db_mem",
		"-s 300",
		"DS:memt:GAUGE:600:0:U",
		"DS:memu:GAUGE:600:0:U",
		"DS:memf:GAUGE:600:0:U",
		"DS:memc:GAUGE:600:0:U",
	#	"RRA:AVERAGE:0.5:1:288",    
	#	"RRA:AVERAGE:0.5:6:2016",    
	#	"RRA:AVERAGE:0.5:24:8928",  
	#	"RRA:AVERAGE:0.5:288:105120",  
	#	"RRA:MIN:0.5:1:288",        
	#	"RRA:MIN:0.5:6:2016",        
	#	"RRA:MIN:0.5:24:8928",       
	#	"RRA:MIN:0.5:288:105120",     
	#	"RRA:MAX:0.5:1:288",       
	#	"RRA:MAX:0.5:6:2016",        
	#	"RRA:MAX:0.5:24:8928",       
	#	"RRA:MAX:0.5:288:105120";
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
	}

#information
if (-f "/proc/meminfo")
	{
	open FR,"/proc/meminfo";
	while ($line=<FR>)
		{
		if ($line =~ /memtotal/i)
			{
			my @memtotal = split(": ",$line);
			$mvalue = @memtotal[1]*1024;
			}
		if ($line =~ /memfree/i)
			{
			my @memfree = split(": ",$line);
			$mfvalue = @memfree[1]*1024;
			}
		if ($mvalue && $mfvalue)
			{
			$mused = $mvalue-$mfvalue;
			}
		if ($line =~ /^cached/i)
			{
			my @memcached = split(": ",$line);
			$mcvalue = @memcached[1]*1024;
			}
		
		}
	
print "Information for Memory graph ...\n";
	print "		Total Memory: $mvalue Bytes\n";
	print "		Used Memory: $mused Bytes\n";
	print "		Free Memory: $mfvalue Bytes\n";
	print "		Cached Memory: $mcvalue Bytes\n";
	}
	else
	{
	print "Error /proc/meminfo not exist...";
	exit 1;
	}

#update rrd info
print "Updating Information in $rrdap_dir$rrd_dir$db_mem ...\n";		
RRDs::update "$rrdap_dir$rrd_dir$db_mem",
	"-t", "memt:memu:memf:memc",
	"N:$mvalue:$mused:$mfvalue:$mcvalue";

#size graph
$weidth="500";
$height="150";
#create graphs
#1 day
$last =  RRDs::last "$rrdap_dir$rrd_dir$db_mem";


@time=("d","w","m","y");
foreach $time_graph(@time)
	{

	$graph = $basedir.$img_dir."mem_".$time_graph.".png";
	print "Creating graph in $graph ...\n";
	#print "creating graph" .$rrd_dir.$png_mem. "...\n";

	#print "Creating image 1".$time_graph." ".$rrd_dir.$png_mem.$time_graph." ...\n";
	RRDs::graph ("$graph",
		"--imgformat=PNG",
		"-s -1$time_graph",
		"--width=$weidth",
		"--height=$height",  
		"--alt-autoscale-max",
		"--lower-limit=0",
		"--vertical-label=RAM MEMORY",
		"--base=1024",
		"DEF:memt=$rrdap_dir$rrd_dir$db_mem:memt:AVERAGE",
		"DEF:memu=$rrdap_dir$rrd_dir$db_mem:memu:AVERAGE",
		"DEF:memf=$rrdap_dir$rrd_dir$db_mem:memf:AVERAGE",
		"DEF:memc=$rrdap_dir$rrd_dir$db_mem:memc:AVERAGE",
		"AREA:memt#AAA8E4:Total Memory\\t", 
				"GPRINT:memt:LAST:Last\\:%8.2lf %s", 
				"GPRINT:memt:MIN:Min\\:%8.2lf %s",  
				"GPRINT:memt:AVERAGE:Avg\\:%8.2lf %s",  
				"GPRINT:memt:MAX:Max\\:%8.2lf %s\\n",
		"LINE2:memu#EEE8A1:Used Memory\\t\\t", 
				"GPRINT:memu:LAST:Last\\:%8.2lf %s", 
				"GPRINT:memu:MIN:Min\\:%8.2lf %s",  
				"GPRINT:memu:AVERAGE:Avg\\:%8.2lf %s",  
				"GPRINT:memu:MAX:Max\\:%8.2lf %s\\n",
		"LINE2:memf#FF0000:Free Memory\\t\\t", 
				"GPRINT:memf:LAST:Last\\:%8.2lf %s", 
				"GPRINT:memf:MIN:Min\\:%8.2lf %s",  
				"GPRINT:memf:AVERAGE:Avg\\:%8.2lf %s",  
				"GPRINT:memf:MAX:Max\\:%8.2lf %s\\n",
		"LINE2:memc#46F2A2:Cached Memory\\t", 
				"GPRINT:memc:LAST:Last\\:%8.2lf %s", 
				"GPRINT:memc:MIN:Min\\:%8.2lf %s",  
				"GPRINT:memc:AVERAGE:Avg\\:%8.2lf %s",  
				"GPRINT:memc:MAX:Max\\:%8.2lf %s\\n");
		if ($ERROR = RRDs::error) { print "$0: unable to generate $graph: $ERROR\n"};
	}

