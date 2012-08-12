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



$db_cpu="cpu.rrd";
$interval=1;
if (-f "/proc/stat")
	{
	open FR,"/proc/stat";
	foreach $line(<FR>)
		{
		if ($line =~ /^cpu\ /)
			{
			my @line_s = split ("\ ",$line);
			$cpu_user1= @line_s[1];
			$cpu_nice1= @line_s[2];
			$cpu_sys1= @line_s[3];
			$cpu_idle1= @line_s[4];
			$cpu_iowait1= @line_s[5];
			$cpu_irq1= @line_s[6];
			$cpu_softirq1= @line_s[7];
			$cpu_total1=$cpu_user1 + $cpu_nice1 + $cpu_sys1 + $cpu_idle1 + $cpu_iowait1 + $cpu_irq1 + $cpu_softirq1
			}
		}
	close FR;
	open FR,"/proc/stat";
	sleep $interval;
	foreach $line(<FR>)
		{
		if ($line =~ /^cpu\ /)
			{
			@line_s = split ("\ ",$line);
			$cpu_user2= @line_s[1];
                        $cpu_nice2= @line_s[2];
                        $cpu_sys2= @line_s[3];
                        $cpu_idle2= @line_s[4];
                        $cpu_iowait2= @line_s[5];
                        $cpu_irq2= @line_s[6];
                        $cpu_softirq2= @line_s[7];
                        $cpu_total2=$cpu_user2 + $cpu_nice2 + $cpu_sys2 + $cpu_idle2 + $cpu_iowait2 + $cpu_irq2 + $cpu_softirq2
			}

		}
	close FR;
	$diff_cpu_user = $cpu_user2 - $cpu_user1;
	$diff_cpu_nice = $cpu_nice2 - $cpu_nice1;
	$diff_cpu_sys = $cpu_sys2 - $cpu_sys1;
	$diff_cpu_idle = $cpu_idle2 - $cpu_idle1;
	$diff_cpu_iowait = $cpu_iowait2 - $cpu_iowait1;
	$diff_cpu_irq = $cpu_irq2 - $cpu_irq1;
	$diff_cpu_softirq = $cpu_softirq2 - $cpu_softirq1;
	$diff_cpu_total = $cpu_total2 - $cpu_total1;
	
	$cpu_user = (100*$diff_cpu_user)/$diff_cpu_total;
	$cpu_nice = (100*$diff_cpu_nice)/$diff_cpu_total;
	$cpu_sys = (100*$diff_cpu_sys)/$diff_cpu_total;
	$cpu_idle = (100*$diff_cpu_idle)/$diff_cpu_total;
	$cpu_iowait = (100*$diff_cpu_iowait)/$diff_cpu_total;
	$cpu_irq = (100*$diff_cpu_irq)/$diff_cpu_total;
	$cpu_softirq = (100*$diff_cpu_softirq)/$diff_cpu_total;
#	$cpu_total = (100*$diff_cpu_total)/$diff_cpu_total;
	$cpu_usage = $cpu_user + $cpu_nice + $cpu_sys + $cpu_iowait + $cpu_irq + $cpu_softirq;
		
	}
	else
	{
	print "File /proc/stat not exist ...\n";
	exit 1;
	
	}
	$cpu_user = sprintf("%.2f",$cpu_user);
	$cpu_nice = sprintf("%.2f",$cpu_nice);
	$cpu_sys = sprintf("%.2f",$cpu_sys);
	$cpu_iowait = sprintf("%.2f",$cpu_iowait);
	$cpu_irq = sprintf("%.2f",$cpu_irq);
	$cpu_softirq = sprintf("%.2f",$cpu_softirq);
	$cpu_idle = sprintf("%.2f",$cpu_idle);
	$cpu_usage = sprintf("%.2f",$cpu_usage);
	
	$cpu_user =~ s/,/\./g;
	$cpu_nice =~ s/,/\./g;
	$cpu_sys =~ s/,/\./g;
	$cpu_iowait =~ s/,/\./g;
	$cpu_softirq =~ s/,/\./g;
	$cpu_idle =~ s/,/\./g;
        $cpu_usage =~ s/,/\./g;



#end recovery information
use RRDs;
require ("/usr/local/zenloadbalancer/config/global.conf");

if (! -f "$rrdap_dir$rrd_dir$db_cpu" )
	{
	print "Creating cpu rrd data base $rrdap_dir$rrd_dir$db_cpu ...\n";
	RRDs::create "$rrdap_dir$rrd_dir$db_cpu",
		"-s 300",
		"DS:user:GAUGE:600:0,00:100,00",
		"DS:nice:GAUGE:600:0,00:100,00",
		"DS:sys:GAUGE:600:0,00:100,00",
		"DS:iowait:GAUGE:600:0,00:100,00",
		"DS:irq:GAUGE:600:0,00:100,00",
		"DS:softirq:GAUGE:600:0,00:100,00",
		"DS:idle:GAUGE:600:0,00:100,00",
		"DS:tused:GAUGE:600:0,00:100,00",
#		"RRA:AVERAGE:0.5:1:600",    
#		"RRA:AVERAGE:0.5:6:700",    
#		"RRA:AVERAGE:0.5:24:775",  
#		"RRA:AVERAGE:0.5:288:797",  
#		"RRA:MIN:0.5:1:288",        
#		"RRA:MIN:0.5:6:2016",        
#		"RRA:MIN:0.5:24:8928",       
#		"RRA:MIN:0.5:288:105120",     
#		"RRA:MAX:0.5:1:288",       
#		"RRA:MAX:0.5:6:2016",        
#		"RRA:MAX:0.5:24:8928",       
#		"RRA:MAX:0.5:288:105120";
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

print "Information for CPU graph ...\n";
	print "		user: $cpu_user %\n";
	print "		nice: $cpu_nice %\n";
	print "		sys: $cpu_sys %\n";
	print "		iowait: $cpu_iowait %\n";
	print "		irq: $cpu_irq %\n";
	print "		softirq: $cpu_softirq %\n";
	print "		idle: $cpu_idle %\n";
	print "		total used: $cpu_usage %\n";
#update rrd info
print "Updating Information in $rrdap_dir$rrd_dir$db_cpu ...\n";		
RRDs::update "$rrdap_dir$rrd_dir$db_cpu",
	"-t", "user:nice:sys:iowait:irq:softirq:idle:tused",
	"N:$cpu_user:$cpu_nice:$cpu_sys:$cpu_iowait:$cpu_irq:$cpu_softirq:$cpu_idle:$cpu_usage";

#size graph
#$weidth="600";
#$height="250";
$weidth="500";
$height="150";
#create graphs
#1 day
$last =  RRDs::last "$rrdap_dir$rrd_dir$db_cpu";


@time=("d","w","m","y");
foreach $time_graph(@time)
	{
	$graph = $basedir.$img_dir."cpu_".$time_graph.".png";
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
		"--vertical-label=CPU USAGE",
		"DEF:user=$rrdap_dir$rrd_dir$db_cpu:user:AVERAGE",
		"DEF:nice=$rrdap_dir$rrd_dir$db_cpu:nice:AVERAGE",
		"DEF:sys=$rrdap_dir$rrd_dir$db_cpu:sys:AVERAGE",
		"DEF:iowait=$rrdap_dir$rrd_dir$db_cpu:iowait:AVERAGE",
		"DEF:irq=$rrdap_dir$rrd_dir$db_cpu:irq:AVERAGE", 
		"DEF:softirq=$rrdap_dir$rrd_dir$db_cpu:softirq:AVERAGE", 
		"DEF:idle=$rrdap_dir$rrd_dir$db_cpu:idle:AVERAGE", 
		"DEF:tused=$rrdap_dir$rrd_dir$db_cpu:tused:AVERAGE", 
		"LINE2:user#AAA8E4:User\\t\\t", 
		"GPRINT:user:LAST:Last\\:%8.2lf %%", 
		"GPRINT:user:MIN:Min\\:%8.2lf %%",  
		"GPRINT:user:AVERAGE:Avg\\:%8.2lf %%",  
		"GPRINT:user:MAX:Max\\:%8.2lf %%\\n",
		"LINE2:nice#EEE8A1:Nice\\t\\t", 
		"GPRINT:nice:LAST:Last\\:%8.2lf %%", 
		"GPRINT:nice:MIN:Min\\:%8.2lf %%",  
		"GPRINT:nice:AVERAGE:Avg\\:%8.2lf %%",  
		"GPRINT:nice:MAX:Max\\:%8.2lf %%\\n",
		"LINE2:sys#FF0000:Sys\\t\\t", 
		"GPRINT:sys:LAST:Last\\:%8.2lf %%", 
		"GPRINT:sys:MIN:Min\\:%8.2lf %%",  
		"GPRINT:sys:AVERAGE:Avg\\:%8.2lf %%",  
		"GPRINT:sys:MAX:Max\\:%8.2lf %%\\n",
		"LINE2:iowait#46F2A2:Iowait\\t", 
		"GPRINT:iowait:LAST:Last\\:%8.2lf %%", 
		"GPRINT:iowait:MIN:Min\\:%8.2lf %%",  
		"GPRINT:iowait:AVERAGE:Avg\\:%8.2lf %%",  
		"GPRINT:iowait:MAX:Max\\:%8.2lf %%\\n",
                "LINE2:irq#E9701F:Irq\\t\\t",
		"GPRINT:irq:LAST:Last\\:%8.2lf %%", 
		"GPRINT:irq:MIN:Min\\:%8.2lf %%",  
		"GPRINT:irq:AVERAGE:Avg\\:%8.2lf %%",  
		"GPRINT:irq:MAX:Max\\:%8.2lf %%\\n",
                "LINE2:softirq#32CD32:Softirq\\t",
		"GPRINT:softirq:LAST:Last\\:%8.2lf %%", 
		"GPRINT:softirq:MIN:Min\\:%8.2lf %%",  
		"GPRINT:softirq:AVERAGE:Avg\\:%8.2lf %%",  
		"GPRINT:softirq:MAX:Max\\:%8.2lf %%\\n",
                "LINE2:idle#E0E02D:Idle\\t\\t",
		"GPRINT:idle:LAST:Last\\:%8.2lf %%", 
		"GPRINT:idle:MIN:Min\\:%8.2lf %%",  
		"GPRINT:idle:AVERAGE:Avg\\:%8.2lf %%",  
		"GPRINT:idle:MAX:Max\\:%8.2lf %%\\n",
                "LINE2:tused#000000:total used\\t",
		"GPRINT:tused:LAST:Last\\:%8.2lf %%", 
		"GPRINT:tused:MIN:Min\\:%8.2lf %%",  
		"GPRINT:tused:AVERAGE:Avg\\:%8.2lf %%",  
		"GPRINT:tused:MAX:Max\\:%8.2lf %%\\n");

		if ($ERROR = RRDs::error) { print "$0: unable to generate $graph: $ERROR\n"};
	}


