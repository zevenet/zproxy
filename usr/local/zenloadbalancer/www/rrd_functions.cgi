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
use MIME::Base64;
require ( "/usr/local/zenloadbalancer/config/global.conf" );

my $width  = "600";
my $height = "150";
$imagetype = "PNG";

#
sub printImgFile    #($file)
{
	my ( $file ) = @_;

	if ( open PNG, "<$file" )
	{
		$raw_string = do { local $/ = undef; <PNG>; };
		$encoded = encode_base64( $raw_string );
		close PNG;
		unlink ( $file );
		return "$encoded";
	}
	else
	{
		return "";
	}
}

#
sub printGraph    #($type,$time)
{
	my ( $type, $time ) = @_;

	my $graph = $basedir . $img_dir . $type . "_" . $time . ".png";

	if ( $type eq "cpu" )
	{
		&genCpuGraph( $type, $graph, $time );
	}

	if ( $type =~ /^dev-*/ )
	{
		&genDiskGraph( $type, $graph, $time );
	}

	if ( $type eq "load" )
	{
		&genLoadGraph( $type, $graph, $time );
	}

	if ( $type eq "mem" )
	{
		&genMemGraph( $type, $graph, $time );
	}

	if ( $type eq "memsw" )
	{
		&genMemSwGraph( $type, $graph, $time );
	}

	if ( $type =~ /iface$/ )
	{
		&genNetGraph( $type, $graph, $time );
	}

	if ( $type =~ /-farm$/ )
	{
		&genFarmGraph( $type, $graph, $time );
	}

	if ( $type eq "temp" )
	{
		&genLoadGraph( $type, $graph, $time );
	}

	return &printImgFile( $graph );
}

#
sub genCpuGraph    #($type,$graph,$time)
{
	my ( $type, $graph, $time ) = @_;

	my $db_cpu = "$type.rrd";

	if ( -e "$rrdap_dir/$rrd_dir/$db_cpu" )
	{
		RRDs::graph(
					 "$graph",
					 "--imgformat=$imagetype",
					 "--start=-1$time",
					 "--width=$width",
					 "--height=$height",
					 "--alt-autoscale-max",
					 "--lower-limit=0",
					 "--title=CPU",
					 "--vertical-label=%",
					 "DEF:user=$rrdap_dir/$rrd_dir/$db_cpu:user:AVERAGE",
					 "DEF:nice=$rrdap_dir/$rrd_dir/$db_cpu:nice:AVERAGE",
					 "DEF:sys=$rrdap_dir/$rrd_dir/$db_cpu:sys:AVERAGE",
					 "DEF:iowait=$rrdap_dir/$rrd_dir/$db_cpu:iowait:AVERAGE",
					 "DEF:irq=$rrdap_dir/$rrd_dir/$db_cpu:irq:AVERAGE",
					 "DEF:softirq=$rrdap_dir/$rrd_dir/$db_cpu:softirq:AVERAGE",
					 "DEF:idle=$rrdap_dir/$rrd_dir/$db_cpu:idle:AVERAGE",
					 "DEF:tused=$rrdap_dir/$rrd_dir/$db_cpu:tused:AVERAGE",
					 "AREA:sys#DC374A:System\\t",
					 "GPRINT:sys:LAST:Last\\:%8.2lf %%",
					 "GPRINT:sys:MIN:Min\\:%8.2lf %%",
					 "GPRINT:sys:AVERAGE:Avg\\:%8.2lf %%",
					 "GPRINT:sys:MAX:Max\\:%8.2lf %%\\n",
					 "STACK:user#6B2E9A:User\\t\\t",
					 "GPRINT:user:LAST:Last\\:%8.2lf %%",
					 "GPRINT:user:MIN:Min\\:%8.2lf %%",
					 "GPRINT:user:AVERAGE:Avg\\:%8.2lf %%",
					 "GPRINT:user:MAX:Max\\:%8.2lf %%\\n",
					 "STACK:nice#ACD936:Nice\\t\\t",
					 "GPRINT:nice:LAST:Last\\:%8.2lf %%",
					 "GPRINT:nice:MIN:Min\\:%8.2lf %%",
					 "GPRINT:nice:AVERAGE:Avg\\:%8.2lf %%",
					 "GPRINT:nice:MAX:Max\\:%8.2lf %%\\n",
					 "STACK:iowait#8D85F3:Iowait\\t",
					 "GPRINT:iowait:LAST:Last\\:%8.2lf %%",
					 "GPRINT:iowait:MIN:Min\\:%8.2lf %%",
					 "GPRINT:iowait:AVERAGE:Avg\\:%8.2lf %%",
					 "GPRINT:iowait:MAX:Max\\:%8.2lf %%\\n",
					 "STACK:irq#46F2A2:Irq\\t\\t",
					 "GPRINT:irq:LAST:Last\\:%8.2lf %%",
					 "GPRINT:irq:MIN:Min\\:%8.2lf %%",
					 "GPRINT:irq:AVERAGE:Avg\\:%8.2lf %%",
					 "GPRINT:irq:MAX:Max\\:%8.2lf %%\\n",
					 "STACK:softirq#595959:Softirq\\t",
					 "GPRINT:softirq:LAST:Last\\:%8.2lf %%",
					 "GPRINT:softirq:MIN:Min\\:%8.2lf %%",
					 "GPRINT:softirq:AVERAGE:Avg\\:%8.2lf %%",
					 "GPRINT:softirq:MAX:Max\\:%8.2lf %%\\n",
					 "STACK:idle#46b971:Idle\\t\\t",
					 "GPRINT:idle:LAST:Last\\:%8.2lf %%",
					 "GPRINT:idle:MIN:Min\\:%8.2lf %%",
					 "GPRINT:idle:AVERAGE:Avg\\:%8.2lf %%",
					 "GPRINT:idle:MAX:Max\\:%8.2lf %%\\n",
					 "LINE1:tused#000000:Total used\\t",
					 "GPRINT:tused:LAST:Last\\:%8.2lf %%",
					 "GPRINT:tused:MIN:Min\\:%8.2lf %%",
					 "GPRINT:tused:AVERAGE:Avg\\:%8.2lf %%",
					 "GPRINT:tused:MAX:Max\\:%8.2lf %%\\n"
		);

		if ( $ERROR = RRDs::error ) { print "$0: unable to generate $graph: $ERROR\n" }
	}
}

#
sub genDiskGraph    #($type,$graph,$time)
{
	my ( $type, $graph, $time ) = @_;

	my $db_hd     = "$type.rrd";
	my @df_system = `$df_bin -k`;
	my $dev       = $type;
	$dev =~ s/hd$//;
	$dev =~ s/dev-//;
	$dev =~ s/-/\// if $dev !~ /dm-/;

	my $mount = &getDiskMountPoint($dev);

	if ( -e "$rrdap_dir/$rrd_dir/$db_hd" )
	{
		RRDs::graph(
					 "$graph",
					 "--start=-1$time",
					 "--title=PARTITION $mount",
					 "--vertical-label=SPACE",
					 "-h",
					 "$height",
					 "-w",
					 "$width",
					 "--lazy",
					 "-l 0",
					 "-a",
					 "$imagetype",
					 "DEF:tot=$rrdap_dir/$rrd_dir/$db_hd:tot:AVERAGE",
					 "DEF:used=$rrdap_dir/$rrd_dir/$db_hd:used:AVERAGE",
					 "DEF:free=$rrdap_dir/$rrd_dir/$db_hd:free:AVERAGE",
					 "CDEF:total=used,free,+",
					 "AREA:used#595959:Used\\t",
					 "GPRINT:used:LAST:Last\\:%8.2lf %s",
					 "GPRINT:used:MIN:Min\\:%8.2lf %s",
					 "GPRINT:used:AVERAGE:Avg\\:%8.2lf %s",
					 "GPRINT:used:MAX:Max\\:%8.2lf %s\\n",
					 "STACK:free#46b971:Free\\t",
					 "GPRINT:free:LAST:Last\\:%8.2lf %s",
					 "GPRINT:free:MIN:Min\\:%8.2lf %s",
					 "GPRINT:free:AVERAGE:Avg\\:%8.2lf %s",
					 "GPRINT:free:MAX:Max\\:%8.2lf %s\\n",
					 "LINE1:total#000000:Total\\t",
					 "GPRINT:total:LAST:Last\\:%8.2lf %s",
					 "GPRINT:total:MIN:Min\\:%8.2lf %s",
					 "GPRINT:total:AVERAGE:Avg\\:%8.2lf %s",
					 "GPRINT:total:MAX:Max\\:%8.2lf %s\\n"
		);

		if ( $ERROR = RRDs::error ) { print "$0: unable to generate $graph: $ERROR\n"; }
	}
}

#
sub genLoadGraph    #($type,$graph,$time)
{
	my ( $type, $graph, $time ) = @_;

	my $db_load = "$type.rrd";

	if ( -e "$rrdap_dir/$rrd_dir/$db_load" )
	{
		RRDs::graph(
					 "$graph",
					 "--imgformat=$imagetype",
					 "--start=-1$time",
					 "--width=$width",
					 "--height=$height",
					 "--alt-autoscale-max",
					 "--lower-limit=0",
					 "--title=LOAD AVERAGE",
					 "--vertical-label=LOAD",
					 "DEF:load=$rrdap_dir/$rrd_dir/$db_load:load:AVERAGE",
					 "DEF:load5=$rrdap_dir/$rrd_dir/$db_load:load5:AVERAGE",
					 "DEF:load15=$rrdap_dir/$rrd_dir/$db_load:load15:AVERAGE",
					 "AREA:load#729e00:last minute\\t\\t",
					 "GPRINT:load:LAST:Last\\:%3.2lf",
					 "GPRINT:load:MIN:Min\\:%3.2lf",
					 "GPRINT:load:AVERAGE:Avg\\:%3.2lf",
					 "GPRINT:load:MAX:Max\\:%3.2lf\\n",
					 "STACK:load5#46b971:last 5 minutes\\t",
					 "GPRINT:load5:LAST:Last\\:%3.2lf",
					 "GPRINT:load5:MIN:Min\\:%3.2lf",
					 "GPRINT:load5:AVERAGE:Avg\\:%3.2lf",
					 "GPRINT:load5:MAX:Max\\:%3.2lf\\n",
					 "STACK:load15#595959:last 15 minutes\\t",
					 "GPRINT:load15:LAST:Last\\:%3.2lf",
					 "GPRINT:load15:MIN:Min\\:%3.2lf",
					 "GPRINT:load15:AVERAGE:Avg\\:%3.2lf",
					 "GPRINT:load15:MAX:Max\\:%3.2lf\\n"
		);

		if ( $ERROR = RRDs::error ) { print "$0: unable to generate $graph: $ERROR\n" }

	}
}

#
sub genMemGraph    #($type,$graph,$time)
{
	my ( $type, $graph, $time ) = @_;

	my $db_mem = "$type.rrd";

	if ( -e "$rrdap_dir/$rrd_dir/$db_mem" )
	{
		RRDs::graph(
					 "$graph",
					 "--imgformat=$imagetype",
					 "-s -1$time",
					 "--width=$width",
					 "--height=$height",
					 "--alt-autoscale-max",
					 "--lower-limit=0",
					 "--title=RAM",
					 "--vertical-label=MEMORY",
					 "--base=1024",
					 "DEF:memt=$rrdap_dir/$rrd_dir/$db_mem:memt:AVERAGE",
					 "DEF:memu=$rrdap_dir/$rrd_dir/$db_mem:memu:AVERAGE",
					 "DEF:memf=$rrdap_dir/$rrd_dir/$db_mem:memf:AVERAGE",
					 "DEF:memc=$rrdap_dir/$rrd_dir/$db_mem:memc:AVERAGE",
					 "AREA:memu#595959:Used\\t\\t",
					 "GPRINT:memu:LAST:Last\\:%8.2lf %s",
					 "GPRINT:memu:MIN:Min\\:%8.2lf %s",
					 "GPRINT:memu:AVERAGE:Avg\\:%8.2lf %s",
					 "GPRINT:memu:MAX:Max\\:%8.2lf %s\\n",
					 "STACK:memf#46b971:Free\\t\\t",
					 "GPRINT:memf:LAST:Last\\:%8.2lf %s",
					 "GPRINT:memf:MIN:Min\\:%8.2lf %s",
					 "GPRINT:memf:AVERAGE:Avg\\:%8.2lf %s",
					 "GPRINT:memf:MAX:Max\\:%8.2lf %s\\n",
					 "LINE2:memc#46F2A2:Cache&Buffer\\t",
					 "GPRINT:memc:LAST:Last\\:%8.2lf %s",
					 "GPRINT:memc:MIN:Min\\:%8.2lf %s",
					 "GPRINT:memc:AVERAGE:Avg\\:%8.2lf %s",
					 "GPRINT:memc:MAX:Max\\:%8.2lf %s\\n",
					 "LINE1:memt#000000:Total\\t\\t",
					 "GPRINT:memt:LAST:Last\\:%8.2lf %s",
					 "GPRINT:memt:MIN:Min\\:%8.2lf %s",
					 "GPRINT:memt:AVERAGE:Avg\\:%8.2lf %s",
					 "GPRINT:memt:MAX:Max\\:%8.2lf %s\\n"
		);

		if ( $ERROR = RRDs::error ) { print "$0: unable to generate $graph: $ERROR\n" }
	}
}

#
sub genMemSwGraph    #($type,$graph,$time)
{
	my ( $type, $graph, $time ) = @_;

	my $db_memsw = "$type.rrd";

	if ( -e "$rrdap_dir/$rrd_dir/$db_memsw" )
	{
		RRDs::graph(
					 "$graph",
					 "--imgformat=$imagetype",
					 "--start=-1$time",
					 "--width=$width",
					 "--height=$height",
					 "--alt-autoscale-max",
					 "--lower-limit=0",
					 "--title=SWAP",
					 "--vertical-label=MEMORY",
					 "--base=1024",
					 "DEF:swt=$rrdap_dir/$rrd_dir/$db_memsw:swt:AVERAGE",
					 "DEF:swu=$rrdap_dir/$rrd_dir/$db_memsw:swu:AVERAGE",
					 "DEF:swf=$rrdap_dir/$rrd_dir/$db_memsw:swf:AVERAGE",
					 "DEF:swc=$rrdap_dir/$rrd_dir/$db_memsw:swc:AVERAGE",
					 "AREA:swu#595959:Used\\t\\t",
					 "GPRINT:swu:LAST:Last\\:%8.2lf %s",
					 "GPRINT:swu:MIN:Min\\:%8.2lf %s",
					 "GPRINT:swu:AVERAGE:Avg\\:%8.2lf %s",
					 "GPRINT:swu:MAX:Max\\:%8.2lf %s\\n",
					 "STACK:swf#46b971:Free\\t\\t",
					 "GPRINT:swf:LAST:Last\\:%8.2lf %s",
					 "GPRINT:swf:MIN:Min\\:%8.2lf %s",
					 "GPRINT:swf:AVERAGE:Avg\\:%8.2lf %s",
					 "GPRINT:swf:MAX:Max\\:%8.2lf %s\\n",
					 "LINE2:swc#46F2A2:Cached\\t",
					 "GPRINT:swc:LAST:Last\\:%8.2lf %s",
					 "GPRINT:swc:MIN:Min\\:%8.2lf %s",
					 "GPRINT:swc:AVERAGE:Avg\\:%8.2lf %s",
					 "GPRINT:swc:MAX:Max\\:%8.2lf %s\\n",
					 "LINE1:swt#000000:Total\\t\\t",
					 "GPRINT:swt:LAST:Last\\:%8.2lf %s",
					 "GPRINT:swt:MIN:Min\\:%8.2lf %s",
					 "GPRINT:swt:AVERAGE:Avg\\:%8.2lf %s",
					 "GPRINT:swt:MAX:Max\\:%8.2lf %s\\n",
		);

		if ( $ERROR = RRDs::error ) { print "$0: unable to generate $graph: $ERROR\n" }
	}
}

#
sub genNetGraph    #($type,$graph,$time)
{
	my ( $type, $graph, $time ) = @_;

	my $db_if   = "$type.rrd";
	my $if_name = $type;
	$if_name =~ s/iface//g;

	if ( -e "$rrdap_dir/$rrd_dir/$db_if" )
	{
		RRDs::graph(
					 "$graph",
					 "--imgformat=$imagetype",
					 "--start=-1$time",
					 "--height=$height",
					 "--width=$width",
					 "--lazy",
					 "-l 0",
					 "--alt-autoscale-max",
					 "--title=TRAFFIC ON $if_name",
					 "--vertical-label=BANDWIDTH",
					 "DEF:in=$rrdap_dir/$rrd_dir/$db_if:in:AVERAGE",
					 "DEF:out=$rrdap_dir/$rrd_dir/$db_if:out:AVERAGE",
					 "CDEF:out_neg=out,-1,*",
					 "AREA:in#46b971:In ",
					 "LINE1:in#000000",
					 "GPRINT:in:LAST:Last\\:%5.1lf %sByte/sec",
					 "GPRINT:in:MIN:Min\\:%5.1lf %sByte/sec",
					 "GPRINT:in:AVERAGE:Avg\\:%5.1lf %sByte/sec",
					 "GPRINT:in:MAX:Max\\:%5.1lf %sByte/sec\\n",
					 "AREA:out_neg#595959:Out",
					 "LINE1:out_neg#000000",
					 "GPRINT:out:LAST:Last\\:%5.1lf %sByte/sec",
					 "GPRINT:out:MIN:Min\\:%5.1lf %sByte/sec",
					 "GPRINT:out:AVERAGE:Avg\\:%5.1lf %sByte/sec",
					 "GPRINT:out:MAX:Max\\:%5.1lf %sByte/sec\\n",
					 "HRULE:0#000000"
		);

		if ( $ERROR = RRDs::error )
		{
			print "$0: unable to generate $if_name traffic graph: $ERROR\n";
		}
	}
}

#
sub genFarmGraph    #($type,$graph,$time)
{
	my ( $type, $graph, $time ) = @_;

	my $db_farm = "$type.rrd";
	my $fname   = $type;
	$fname =~ s/-farm$//g;

	if ( -e "$rrdap_dir/$rrd_dir/$db_farm" )
	{
		RRDs::graph(
			"$graph",
			"--start=-1$time",
			"-h",
			"$height",
			"-w",
			"$width",
			"--lazy",
			"-l 0",
			"-a",
			"$imagetype",
			"--title=CONNECTIONS ON $fname farm",
			"--vertical-label=Connections",
			"DEF:pending=$rrdap_dir/$rrd_dir/$db_farm:pending:AVERAGE",
			"DEF:established=$rrdap_dir/$rrd_dir/$db_farm:established:AVERAGE",

			# "DEF:closed=$rrdap_dir/$rrd_dir/$db_farm:closed:AVERAGE",
			"LINE2:pending#595959:Pending\\t",
			"GPRINT:pending:LAST:Last\\:%6.0lf ",
			"GPRINT:pending:MIN:Min\\:%6.0lf ",
			"GPRINT:pending:AVERAGE:Avg\\:%6.0lf ",
			"GPRINT:pending:MAX:Max\\:%6.0lf \\n",
			"LINE2:established#46b971:Established\\t",
			"GPRINT:established:LAST:Last\\:%6.0lf ",
			"GPRINT:established:MIN:Min\\:%6.0lf ",
			"GPRINT:established:AVERAGE:Avg\\:%6.0lf ",
			"GPRINT:established:MAX:Max\\:%6.0lf \\n"

			  # "LINE2:closed#46F2A2:Closed\\t",
			  # "GPRINT:closed:LAST:Last\\:%6.0lf ",
			  # "GPRINT:closed:MIN:Min\\:%6.0lf ",
			  # "GPRINT:closed:AVERAGE:Avg\\:%6.0lf ",
			  # "GPRINT:closed:MAX:Max\\:%6.0lf \\n"
		);

		if ( $ERROR = RRDs::error )
		{
			print "$0: unable to generate $farm farm graph: $ERROR\n";
		}
	}
}

#Generate the CPU temperature Graph
sub genTempGraph    #($type,$graph,$time)
{
	my $db_temp = "$type.rrd";

	if ( -e "$rrdap_dir/$rrd_dir/$db_temp" )
	{
		RRDs::graph(
					 "$graph",
					 "--imgformat=$imagetype",
					 "--start=-1$time",
					 "--width=$width",
					 "--height=$height",
					 "--alt-autoscale-max",
					 "--lower-limit=0",
					 "--title=CPU TEMPERATURE",
					 "--vertical-label=LOAD",
					 "DEF:temp=$rrdap_dir/$rrd_dir/$db_temp:temp:AVERAGE",
					 "STACK:temp#46b971:CPU temperature\\t",
					 "GPRINT:temp:LAST:Last\\:%4.2lf C",
					 "GPRINT:temp:MIN:Min\\:%4.2lf C",
					 "GPRINT:temp:AVERAGE:Avg\\:%4.2lf C",
					 "GPRINT:temp:MAX:Max\\:%4.2lf C\\n"
		);

		if ( $ERROR = RRDs::error ) { print "$0: unable to generate $graph: $ERROR\n"; }

	}
}

#function that returns the graph list to show
sub getGraphs2Show    #($graphtype)
{
	my ( $graphtype ) = @_;

	my @list = -1;

	if ( $graphtype eq System )
	{
		opendir ( DIR, "$rrdap_dir/$rrd_dir" );
		my @disk = grep ( /^dev-.*$/, readdir ( DIR ) );
		closedir ( DIR );
		for ( @disk ) { s/.rrd//g };    # remove filenames .rrd trailing
		@list = ( "cpu", @disk, "load", "mem", "memsw" );
	}
	elsif ( $graphtype eq Network )
	{
		opendir ( DIR, "$rrdap_dir/$rrd_dir" );
		@list = grep ( /iface.rrd$/, readdir ( DIR ) );
		closedir ( DIR );
		for ( @list ) { s/.rrd//g };    # remove filenames .rrd trailing
	}
	elsif ( $graphtype eq Farm )
	{
		opendir ( DIR, "$rrdap_dir/$rrd_dir" );
		@list = grep ( /farm.rrd$/, readdir ( DIR ) );
		closedir ( DIR );
		for ( @list ) { s/.rrd//g };    # remove filenames .rrd trailing
	}
	else
	{
		opendir ( DIR, "$rrdap_dir/$rrd_dir" );
		@list = grep ( /.rrd$/, readdir ( DIR ) );
		closedir ( DIR );
		for ( @list ) { s/.rrd//g };    # remove filenames .rrd trailing
	}

	return @list;
}

1;
