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
#
$db_hd="hd.rrd";
use RRDs;
require ("/usr/local/zenloadbalancer/config/global.conf");

my @system = `$df_bin -h`;

foreach $line(@system)
	{
	chomp($line);
	if ($line =~ /^\/dev/)
		{
		my @dd_name = split("\ ",$line);
		chomp(@dd_name[0]);
		$dd_name = @dd_name[0];
		$dd_mame =~ s/"\/"/" "/g;
		my @df_system = `$df_bin -k`;
		for $line_df(@df_system)
				{
				if ($line_df =~ /$dd_name/)
					{
					my @s_line = split("\ ",$line_df);
					chomp(@s_line[0]);
					$partition = @s_line[0];
					$size= @s_line[4];
					$mount = @s_line[5];
					$partitions = @s_line[0];
					$partitions =~ s/\///;
					$partitions =~ s/\//-/g;
					#total
					$tot = @s_line[1]*1024;
					$used = @s_line[2]*1024;
					$free = @s_line[3]*1024;
					if (! -f "$rrdap_dir$rrd_dir$partitions$db_hd")
						{
						print "Creating $partiton rrd database in $rrdap_dir$rrd_dir$partitions$db_hd ...\n";
						RRDs::create "$rrdap_dir$rrd_dir$partitions$db_hd",
						"-s 300", 
						"DS:tot:GAUGE:600:0:U",
						"DS:used:GAUGE:600:0:U",
						"DS:free:GAUGE:600:0:U",
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
						if ($ERROR = RRDs::error) { print "$0: unable to generate $partition database: $ERROR\n"};
						}
					#infomation
					print "Information for $partition in $mount  graph ...\n";
                			print "                Total: $tot Bytes\n";
                			print "                used: $used Bytes\n";
                			print "                size: $size Bytes\n";
                			print "                free: $free Bytes\n";
                			##update rrd info
					$size =~ s/%//g;
					print "Updating Informatino in $rrdap_dir$rrd_dir$partitions$db_hd ...\n";
					RRDs::update "$rrdap_dir$rrd_dir$partitions$db_hd",
						"-t", "tot:used:free",
						"N:$tot:$used:$free";

					if ($ERROR = RRDs::error) { print "$0: unable to generate $partition database: $ERROR\n"};
					$width="500";
					$height="150";
					@time=("d","w","m","y");
					foreach $time_graph(@time)
						{
						$graph = $basedir.$img_dir.$partitions."_".$time_graph.".png";
						print "Creating graph in $graph ...\n";
						RRDs::graph ("$graph",
							"--start=-1$time_graph",
							"-v $partition MOUNTED IN $mount (USED:$size%)",	
							"-h", "$height", "-w", "$width",
							"--lazy",
							"-l 0",
							"-a", "PNG",
					                "DEF:tot=$rrdap_dir$rrd_dir$partitions$db_hd:tot:AVERAGE",
					                "DEF:used=$rrdap_dir$rrd_dir$partitions$db_hd:used:AVERAGE",
					                "DEF:free=$rrdap_dir$rrd_dir$partitions$db_hd:free:AVERAGE",
							"AREA:tot#aaa8e4:Total\\t",
							"GPRINT:tot:LAST:Last\\:%8.2lf %s", 
							"GPRINT:tot:MIN:Min\\:%8.2lf %s",  
							"GPRINT:tot:AVERAGE:Avg\\:%8.2lf %s",  
							"GPRINT:tot:MAX:Max\\:%8.2lf %s\\n",
							"LINE2:used#E0E02D:Used\\t",
							"GPRINT:used:LAST:Last\\:%8.2lf %s", 
							"GPRINT:used:MIN:Min\\:%8.2lf %s",  
							"GPRINT:used:AVERAGE:Avg\\:%8.2lf %s",  
							"GPRINT:used:MAX:Max\\:%8.2lf %s\\n",
							"LINE2:free#46F2A2:Free\\t",
							"GPRINT:free:LAST:Last\\:%8.2lf %s", 
							"GPRINT:free:MIN:Min\\:%8.2lf %s",  
							"GPRINT:free:AVERAGE:Avg\\:%8.2lf %s",  
							"GPRINT:free:MAX:Max\\:%8.2lf %s\\n");

                		       if ($ERROR = RRDs::error) { print "$0: unable to generate $partition graph: $ERROR\n"; }
	
						}
					}
				}
		}
	}

