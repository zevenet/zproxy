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
$db_memsw="memsw.rrd";
#create db memory if not existS
if (! -f "$rrdap_dir$rrd_dir$db_memsw" )

	{
	print "Creating memory swap rrd data base $rrdap_dir$rrd_dir$db_memsw ...\n";
	RRDs::create "$rrdap_dir$rrd_dir$db_memsw",
		"-s 300",
		"DS:swt:GAUGE:600:0:U",
		"DS:swu:GAUGE:600:0:U",
		"DS:swf:GAUGE:600:0:U",
		"DS:swc:GAUGE:600:0:U",
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
	if ($ERROR = RRDs::error) { print "$0: unable to generate $rrdap_dir$rrd_dir$db_memsw: $ERROR\n"};
	}

#information
if (-f "/proc/meminfo")
	{
	open FR,"/proc/meminfo";
	while ($line=<FR>)
		{
		if ($line =~ /swaptotal/i)
			{
			my @memtotal = split(": ",$line);
			$mvalue = @memtotal[1]*1024;
			}
		if ($line =~ /swapfree/i)
			{
			my @memfree = split(": ",$line);
			$mfvalue = @memfree[1]*1024;
			}
		if ($mvalue && $mfvalue)
			{
			$mused = $mvalue-$mfvalue;
			}
		if ($line =~ /^swapcached/i)
			{
			my @memcached = split(": ",$line);
			$mcvalue = @memcached[1]*1024;
			}
		
		}
	
print "Information for swap memory graph ...\n";
	print "		Total Memory Swap: $mvalue Bytes\n";
	print "		Used Memory Swap: $mused Bytes\n";
	print "		Free Memory Swap: $mfvalue Bytes\n";
	print "		Cached Memory Swap: $mcvalue Bytes\n";
	}
	else
	{
	print "Error /proc/meminfo not exist...";
	exit 1;
	}

#update rrd info
print "Updating Information in $rrdap_dir$rrd_dir$db_memsw ...\n";		
RRDs::update "$rrdap_dir$rrd_dir$db_memsw",
	"-t", "swt:swu:swf:swc",
	"N:$mvalue:$mused:$mfvalue:$mcvalue";

#size graph
$weidth="500";
$height="150";
#create graphs
#1 day
$last =  RRDs::last "$rrdap_dir$rrd_dir$db_memsw";


@time=("d","w","m","y");
foreach $time_graph(@time)
	{

	$graph = $basedir.$img_dir."memsw_".$time_graph.".png";
	print "Creating graph in $graph ...\n";
	#print "creating graph" .$rrd_dir.$png_mem. "...\n";

	#print "Creating image 1".$time_graph." ".$rrd_dir.$png_mem.$time_graph." ...\n";
	RRDs::graph ("$graph",
		"--imgformat=PNG",
		"--start=-1$time_graph",
		"--width=$weidth",
		"--height=$height",  
		"--alt-autoscale-max",
		"--lower-limit=0",
		"--vertical-label=SWAP MEMORY",
		"--base=1024",
		"DEF:swt=$rrdap_dir$rrd_dir$db_memsw:swt:AVERAGE",
		"DEF:swu=$rrdap_dir$rrd_dir$db_memsw:swu:AVERAGE",
		"DEF:swf=$rrdap_dir$rrd_dir$db_memsw:swf:AVERAGE",
		"DEF:swc=$rrdap_dir$rrd_dir$db_memsw:swc:AVERAGE",
		"AREA:swt#AAA8E4:Total Swap\\t\\t", 
				"GPRINT:swt:LAST:Last\\:%8.2lf %s", 
				"GPRINT:swt:MIN:Min\\:%8.2lf %s",  
				"GPRINT:swt:AVERAGE:Avg\\:%8.2lf %s",  
				"GPRINT:swt:MAX:Max\\:%8.2lf %s\\n",
		"LINE2:swu#EEE8A1:Used Swap\\t\\t", 
				"GPRINT:swu:LAST:Last\\:%8.2lf %s", 
				"GPRINT:swu:MIN:Min\\:%8.2lf %s",  
				"GPRINT:swu:AVERAGE:Avg\\:%8.2lf %s",  
				"GPRINT:swu:MAX:Max\\:%8.2lf %s\\n",
		"LINE2:swf#FF0000:Free Swap\\t\\t", 
				"GPRINT:swf:LAST:Last\\:%8.2lf %s", 
				"GPRINT:swf:MIN:Min\\:%8.2lf %s",  
				"GPRINT:swf:AVERAGE:Avg\\:%8.2lf %s",  
				"GPRINT:swf:MAX:Max\\:%8.2lf %s\\n",
		"LINE2:swc#46F2A2:Cached Swap\\t\\t", 
				"GPRINT:swc:LAST:Last\\:%8.2lf %s", 
				"GPRINT:swc:MIN:Min\\:%8.2lf %s",  
				"GPRINT:swc:AVERAGE:Avg\\:%8.2lf %s",  
				"GPRINT:swc:MAX:Max\\:%8.2lf %s\\n");
		if ($ERROR = RRDs::error) { print "$0: unable to generate $graph: $ERROR\n"};
	}

