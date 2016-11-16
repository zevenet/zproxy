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

#get Memory usage of the System.
#input $format Parameter format could be "b" for bytes, "kb" for KBytes and "mb" for MBytes (default: mb)
#return @array
#	name,value
sub getMemStats    # ()
{
	my ( $format ) = @_;
	my @data;
	my ( $mvalue, $mfvalue, $mused, $mbvalue, $mcvalue, $swtvalue, $swfvalue, $swused, $swcvalue );
	my ( $mname, $mfname, $mbname, $mcname, $swtname, $swfname, $swcname );

	if ( ! -f "/proc/meminfo" )
	{
		print "$0: Error: File /proc/meminfo not exist ...\n";
		exit 1;
	}

	$format = "mb" if $format eq "";

	open FR, "/proc/meminfo";
	while ( $line = <FR> )
	{
		if ( $line =~ /memtotal/i )
		{
			my @memtotal = split /[:\ ]+/, $line;
			$mvalue = $memtotal[1];
			$mvalue = $mvalue / 1024 if $format eq "mb";
			$mvalue = $mvalue * 1024 if $format eq "b";
			$mname  = $memtotal[0];
		}
		if ( $line =~ /memfree/i )
		{
			my @memfree = split ( ": ", $line );
			$mfvalue = $memfree[1];
			$mfvalue = $mfvalue / 1024 if $format eq "mb";
			$mfvalue = $mfvalue * 1024 if $format eq "b";
			$mfname  = $memfree[0];
		}
		if ( $mname && $mfname )
		{
			$mused = $mvalue - $mfvalue;
		}
		if ( $line =~ /buffers/i )
		{
			my @membuf = split /[:\ ]+/, $line;
			$mbvalue = $membuf[1];
			$mbvalue = $mbvalue / 1024 if $format eq "mb";
			$mbvalue = $mbvalue * 1024 if $format eq "b";
			$mbname  = $membuf[0];
		}
		if ( $line =~ /^cached/i )
		{
			my @memcached = split /[:\ ]+/, $line;
			$mcvalue = $memcached[1];
			$mcvalue = $mcvalue / 1024 if $format eq "mb";
			$mcvalue = $mcvalue * 1024 if $format eq "b";
			$mcname  = $memcached[0];
		}
		if ( $line =~ /swaptotal/i )
		{
			my @swtotal = split /[:\ ]+/, $line;
			$swtvalue = $swtotal[1];
			$swtvalue = $swtvalue / 1024 if $format eq "mb";
			$swtvalue = $swtvalue * 1024 if $format eq "b";
			$swtname  = $swtotal[0];
		}
		if ( $line =~ /swapfree/i )
		{
			my @swfree = split /[:\ ]+/, $line;
			$swfvalue = $swfree[1];
			$swfvalue = $swfvalue / 1024 if $format eq "mb";
			$swfvalue = $swfvalue * 1024 if $format eq "b";
			$swfname  = $swfree[0];
		}
		if ( $swtname && $swfname )
		{
			$swused = $swtvalue - $swfvalue;
		}
		if ( $line =~ /swapcached/i )
		{
			my @swcached = split /[:\ ]+/, $line ;
			$swcvalue = @swcached[1];
			$swcvalue = $swcvalue / 1024 if $format eq "mb";
			$swcvalue = $swcvalue * 1024 if $format eq "b";
			$swcname  = $swcached[0];
		}
	}

	close FR;

	$mvalue   = sprintf ( '%.2f', $mvalue );
	$mfvalue  = sprintf ( '%.2f', $mfvalue );
	$mused    = sprintf ( '%.2f', $mused );
	$mbvalue  = sprintf ( '%.2f', $mbvalue );
	$mcvalue  = sprintf ( '%.2f', $mcvalue );
	$swtvalue = sprintf ( '%.2f', $swtvalue );
	$swfvalue = sprintf ( '%.2f', $swfvalue );
	$swused   = sprintf ( '%.2f', $swused );
	$swcvalue = sprintf ( '%.2f', $swcvalue );

	@data = (
			  [$mname,     $mvalue],
			  [$mfname,    $mfvalue],
			  ['MemUsed',  $mused],
			  [$mbname,    $mbvalue],
			  [$mcname,    $mcvalue],
			  [$swtname,   $swtvalue],
			  [$swfname,   $swfvalue],
			  ['SwapUsed', $swused],
			  [$swcname,   $swcvalue],
	);

	return @data;
}

#get Load usage of the System.
#return @array
#       name,value
sub getLoadStats    # ()
{
	my $last;
	my $last5;
	my $last15;

	if ( -f "/proc/loadavg" )
	{
		my $lastline;

		open FR, "/proc/loadavg";
		while ( $line = <FR> )
		{
			$lastline = $line;
		}
		close FR;

		( $last, $last5, $last15 ) = split ( " ", $lastline );
	}

	my @data = ( ['Last', $last], ['Last 5', $last5], ['Last 15', $last15], );

	return @data;
}

sub getNetworkStats    # ()
{
	( $format ) = @_;

	if ( ! -f "/proc/net/dev" ) {
		print "$0: Error: File /proc/net/dev not exist ...\n";
		exit 1;
	}

	open DEV, '/proc/net/dev' or die $!;
	my ( $in, $out );
	my @data;
	my $interface;

	$i = -1;
	while ( <DEV> )
	{
		if ( $_ =~ /\:/ && $_ !~ /lo/ )
		{
			$i++;
			my @iface = split ( ":", $_ );
			$if =~ s/\ //g;
			$if = $iface[0];

			if ( $_ =~ /:\ / )
			{
				( $in, $out ) = ( split )[1, 9];
			}
			else
			{
				( $in, $out ) = ( split )[0, 8];
				$in = ( split /:/, $in )[1];
			}
			if ($format ne "raw")
			{
				$in  = ( ( $in / 1024 ) / 1024 );
				$out = ( ( $out / 1024 ) / 1024 );
				$in  = sprintf ( '%.2f', $in );
				$out = sprintf ( '%.2f', $out );
			}
			$if =~ s/\ //g;

			$interface[$i]    = $if;
			$interfacein[$i]  = $in;
			$interfaceout[$i] = $out;
		}

	}

	for ( $j = 0 ; $j <= $i ; $j++ )
	{
		push @data, [$interface[$j] . ' in', $interfacein[$j]],
		  [$interface[$j] . ' out', $interfaceout[$j]];
	}

	close DEV;
	return @data;
}

#get Date
sub getDate    # ()
{

	#$timeseconds = time();
	$now = ctime();
	return $now;

}

#get hostname
sub getHostname    # ()
{
	my $hostname = `uname -n`;
	chomp $hostname;

	return $hostname;
}

#get total CPU usage
sub getCPU         # ()
{
	my @data;
	my $interval = 1;

	if ( ! -f "/proc/stat" ) {
		print "$0: Error: File /proc/stat not exist ...\n";
		exit 1;
	}

	open FR, "/proc/stat";
	foreach $line ( <FR> ) {
		if ( $line =~ /^cpu\ / ) {
			my @line_s = split ( "\ ", $line );
			$cpu_user1    = $line_s[1];
			$cpu_nice1    = $line_s[2];
			$cpu_sys1     = $line_s[3];
			$cpu_idle1    = $line_s[4];
			$cpu_iowait1  = $line_s[5];
			$cpu_irq1     = $line_s[6];
			$cpu_softirq1 = $line_s[7];
			$cpu_total1 =
			  $cpu_user1 +
			  $cpu_nice1 +
			  $cpu_sys1 +
			  $cpu_idle1 +
			  $cpu_iowait1 +
			  $cpu_irq1 +
			  $cpu_softirq1;
		}
	}
	close FR;

	sleep $interval;

	open FR, "/proc/stat";
	foreach $line ( <FR> ) {
		if ( $line =~ /^cpu\ / ) {
			@line_s       = split ( "\ ", $line );
			$cpu_user2    = $line_s[1];
			$cpu_nice2    = $line_s[2];
			$cpu_sys2     = $line_s[3];
			$cpu_idle2    = $line_s[4];
			$cpu_iowait2  = $line_s[5];
			$cpu_irq2     = $line_s[6];
			$cpu_softirq2 = $line_s[7];
			$cpu_total2 =
			  $cpu_user2 +
			  $cpu_nice2 +
			  $cpu_sys2 +
			  $cpu_idle2 +
			  $cpu_iowait2 +
			  $cpu_irq2 +
			  $cpu_softirq2;
		}
	}
	close FR;

	$diff_cpu_user    = $cpu_user2 - $cpu_user1;
	$diff_cpu_nice    = $cpu_nice2 - $cpu_nice1;
	$diff_cpu_sys     = $cpu_sys2 - $cpu_sys1;
	$diff_cpu_idle    = $cpu_idle2 - $cpu_idle1;
	$diff_cpu_iowait  = $cpu_iowait2 - $cpu_iowait1;
	$diff_cpu_irq     = $cpu_irq2 - $cpu_irq1;
	$diff_cpu_softirq = $cpu_softirq2 - $cpu_softirq1;
	$diff_cpu_total   = $cpu_total2 - $cpu_total1;

	$cpu_user    = ( 100 * $diff_cpu_user ) / $diff_cpu_total;
	$cpu_nice    = ( 100 * $diff_cpu_nice ) / $diff_cpu_total;
	$cpu_sys     = ( 100 * $diff_cpu_sys ) / $diff_cpu_total;
	$cpu_idle    = ( 100 * $diff_cpu_idle ) / $diff_cpu_total;
	$cpu_iowait  = ( 100 * $diff_cpu_iowait ) / $diff_cpu_total;
	$cpu_irq     = ( 100 * $diff_cpu_irq ) / $diff_cpu_total;
	$cpu_softirq = ( 100 * $diff_cpu_softirq ) / $diff_cpu_total;

	$cpu_usage =
	  $cpu_user + $cpu_nice + $cpu_sys + $cpu_iowait + $cpu_irq + $cpu_softirq;

	$cpu_user    = sprintf ( "%.2f", $cpu_user );
	$cpu_nice    = sprintf ( "%.2f", $cpu_nice );
	$cpu_sys     = sprintf ( "%.2f", $cpu_sys );
	$cpu_iowait  = sprintf ( "%.2f", $cpu_iowait );
	$cpu_irq     = sprintf ( "%.2f", $cpu_irq );
	$cpu_softirq = sprintf ( "%.2f", $cpu_softirq );
	$cpu_idle    = sprintf ( "%.2f", $cpu_idle );
	$cpu_usage   = sprintf ( "%.2f", $cpu_usage );

	$cpu_user =~ s/,/\./g;
	$cpu_nice =~ s/,/\./g;
	$cpu_sys =~ s/,/\./g;
	$cpu_iowait =~ s/,/\./g;
	$cpu_softirq =~ s/,/\./g;
	$cpu_idle =~ s/,/\./g;
	$cpu_usage =~ s/,/\./g;

	@data = (
			  ['CPUuser',    $cpu_user],
			  ['CPUnice',    $cpu_nice],
			  ['CPUsys',     $cpu_sys],
			  ['CPUiowait',  $cpu_iowait],
			  ['CPUirq',     $cpu_irq],
			  ['CPUsoftirq', $cpu_softirq],
			  ['CPUidle',    $cpu_idle],
			  ['CPUusage',   $cpu_usage],
	);

	return @data;
}

#Obtain system disk usage
#return @array
#       name,value
sub getDiskSpace    # ()
{
	my @data;	# output

	my $df_bin = &getGlobalConfiguration( 'df_bin' );
	my @system = `$df_bin -k`;
	chomp ( @system );
	my @df_system = @system;

	foreach my $line ( @system )
	{
		next if $line !~ /^\/dev/;

		my @dd_name = split ( ' ', $line );
		my $dd_name = $dd_name[0];

		my ( $line_df ) = grep( { /^$dd_name\s/ } @df_system );
		my @s_line = split ( /\s+/, $line_df );

		my $partitions = @s_line[0];
		$partitions =~ s/\///;
		$partitions =~ s/\//-/g;

		my $tot  = @s_line[1] * 1024;
		my $used = @s_line[2] * 1024;
		my $free = @s_line[3] * 1024;

		push ( @data,
			   [$partitions . ' Total', $tot],
			   [$partitions . ' Used',  $used],
			   [$partitions . ' Free',  $free] );
	}

	return @data;
}

sub getDiskPartitionsInfo	#()
{
	my $partitions; # output

	my $df_bin = &getGlobalConfiguration( 'df_bin' );
	my $rrdap_dir = &getGlobalConfiguration( 'rrdap_dir' );
	my $rrd_dir = &getGlobalConfiguration( 'rrd_dir' );
	my $db_hd = "hd.rrd";

	my @df_lines = grep { /^\/dev/ } `$df_bin -k`;
	chomp ( @df_lines );

	foreach my $line ( @df_lines )
	{
		my @df_line = split ( /\s+/, $line );

		my $mount_point = @df_line[5];
		my $partition = @df_line[0];
		my $part_id = @df_line[0];
		$part_id =~ s/\///;
		$part_id =~ s/\//-/g;

		$partitions->{ $partition } = {
										mount_point => $mount_point,
										rrd_id => "${part_id}hd",
		};
	}

	return $partitions;
}

#Obtain disk mount point from a device
sub getDiskMountPoint    # ($dev)
{
	( $dev ) = @_;

	my $df_bin = &getGlobalConfiguration('df_bin');
	my @df_system = `$df_bin -k`;
	my $mount;

	for $line_df ( @df_system )
	{
		if ( $line_df =~ /$dev/ )
		{
			my @s_line = split ( "\ ", $line_df );
			chomp ( @s_line );

			$mount     = $s_line[5];
		}
	}

	return $mount;
}

#Obtain the CPU temperature
sub getCPUTemp    # ()
{
	$file = "/proc/acpi/thermal_zone/THRM/temperature";
	my $lastline;

	if ( ! -f "$file" )
	{
		print "$0: Error: File $file not exist ...\n";
		exit 1;
	}

	open FT,"$file";
	while ( $line=<FT> )
	{
		$lastline = $line;
	}
	close FT;

	my @lastlines = split("\:", $lastline);

	$temp = @lastlines[1];
	$temp =~ s/\ //g;
	$temp =~ s/\n//g;
	$temp =~ s/C//g;

	return $temp;
}

#
sub zsystem    # (@exec)
{
	( @exec ) = @_;

	system ( ". /etc/profile && @exec" );
	return $?;
}

dns:

# return a hash ref = {
#		primary => "value",
#		secundary => "value",
#		}
sub getDns
{
	my $dns;
	my $dnsFile = &getGlobalConfiguration( 'filedns' );

	if ( !-e $dnsFile )
	{
		return undef;
	}
	tie my @dnsArr, 'Tie::File', $dnsFile;

	#primary
	my @aux = split ( ' ', $dnsArr[0] );
	$dns->{ 'primary' } = $aux[1];

	# secondary
	if ( defined $dnsArr[1] )
	{
		@aux = split ( ' ', $dnsArr[1] );
		$dns->{ 'secundary' } = $aux[1];
	}
	else
	{
		$dns->{ 'secundary' } = "";
	}
	untie @dnsArr;

	return $dns;
}

# dns = primary|secondary;
# &setDns( $dns, $value );
sub setDns
{
	my ( $dns, $value ) = @_;
	my $dnsFile = &getGlobalConfiguration( 'filedns' );
	my $output;

	if ( !-e $dnsFile )
	{
		$output = system ( &getGlobalConfiguration( 'touch' ) . " $dnsFile" );
	}

	tie my @dnsArr, 'Tie::File', $dnsFile;
	my $line;

	if ( $dns eq 'primary' )
	{
		$line = 0;
	}

	# secondary:   $dns eq 'secondary'
	else
	{
		$line = 1;
	}
	$dnsArr[$line] = "nameserver $value";

	untie @dnsArr;
	return $output;
}

ssh:

# return ssh port
sub getSsh
{
	my $sshFile = &getGlobalConfiguration( 'sshConf' );
	my $ssh     = {                                       # conf
				'port'   => 22,
				'listen' => "0.0.0.0",
	};
	my $listen_format = &getValidFormat( 'ssh_listen' );

	if ( !-e $sshFile )
	{
		return undef;
	}
	else
	{
		tie my @file, 'Tie::File', $sshFile;
		foreach my $line ( @file )
		{
			if ( $line =~ /^Port\s+(\d+)/ )
			{
				$ssh->{ 'port' } = $1;
			}
			elsif ( $line =~ /^ListenAddress\s+($listen_format)/ )
			{
				$ssh->{ 'listen' } = $1;
			}
		}

		untie @file;
	}
	return $ssh;
}

# &setSsh( $hashRef );
sub setSsh
{
	my ( $sshConf ) = @_;
	my $sshFile     = &getGlobalConfiguration( 'sshConf' );
	my $output      = 1;
	my $index       = 5
	  ; # default, it is the line where will add port and listen if one of this doesn't exist

	# create flag to check all params are changed
	my $portFlag;
	my $listenFlag;
	$portFlag   = 1 if ( exists $sshConf->{ 'port' } );
	$listenFlag = 1 if ( exists $sshConf->{ 'listen' } );

	if ( !-e $sshFile )
	{
		&zenlog( "SSH configuration file doesn't exist." );
		return -1;
	}

	tie my @file, 'Tie::File', $sshFile;
	foreach my $line ( @file )
	{
		if ( exists $sshConf->{ 'port' } )
		{
			if ( $line =~ /^Port\s+/ )
			{
				$line     = "Port $sshConf->{ 'port' }";
				$output   = 0;
				$portFlag = 0;
			}
		}
		if ( exists $sshConf->{ 'listen' } )
		{
			if ( $line =~ /^ListenAddress\s+/ )
			{
				$line       = "ListenAddress $sshConf->{ 'listen' }";
				$listenFlag = 0;
			}
		}
	}

	# Didn't find port and required a change
	if ( $portFlag )
	{
		splice @file, $index, 0, "Port $sshConf->{ 'port' }";
	}

	# Didn't find listen and required a change
	if ( $listenFlag )
	{
		splice @file, $index, 0, "ListenAddress $sshConf->{ 'listen' }";
	}
	untie @file;

	# restart service to apply changes
	$output = system ( &getGlobalConfiguration( 'sshService' ) . " restart" );

	return $output;
}

# get ntp settings
sub getGuiconf
{
	my $guiConf;

	return $guiConf;
}

#do not remove this
1;
