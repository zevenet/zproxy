#!/usr/bin/perl
###############################################################################
#
#    Zevenet Software License
#    This file is part of the Zevenet Load Balancer software package.
#
#    Copyright (C) 2014-today ZEVENET SL, Sevilla (Spain)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

use strict;

require "/usr/local/zenloadbalancer/www/functions_ext.cgi";

=begin nd
Function: getMemStats

	Get stats of memory usage of the system.

Parameters:
	format - "b" for bytes, "kb" for KBytes and "mb" for MBytes (default: mb).

Returns:
	list - Two dimensional array.

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

See Also:
	memory-rrd.pl, zapi/v3/system_stats.cgi, zapi/v2/system_stats.cgi
=cut
sub getMemStats
{
	my ( $format ) = @_;
	my @data;
	my (
		 $mvalue,   $mfvalue,  $mused,  $mbvalue, $mcvalue,
		 $swtvalue, $swfvalue, $swused, $swcvalue
	);
	my ( $mname, $mfname, $mbname, $mcname, $swtname, $swfname, $swcname );

	if ( !-f "/proc/meminfo" )
	{
		print "$0: Error: File /proc/meminfo not exist ...\n";
		exit 1;
	}

	$format = "mb" unless $format;

	open FR, "/proc/meminfo";
	my $line;
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

			# capture first number found
			$memfree[1] =~ /^\s+(\d+)\ /;
			$mfvalue = $1;

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
			my @swcached = split /[:\ ]+/, $line;
			$swcvalue = $swcached[1];
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

=begin nd
Function: getLoadStats

	Get the system load values.

Parameters:
	none - .

Returns:
	list - Two dimensional array.

	@data = (
		['Last', $last],
		['Last 5', $last5],
		['Last 15', $last15]
	);

See Also:
	load-rrd.pl, zapi/v3/system_stats.cgi, zapi/v2/system_stats.cgi
=cut
sub getLoadStats
{
	my $last;
	my $last5;
	my $last15;

	if ( -f "/proc/loadavg" )
	{
		my $lastline;
		
		my $line;
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

=begin nd
Function: getNetworkStats

	Get stats for the network interfaces.

Parameters:
	format - 'raw', 'hash' or nothing.

Returns:
	When 'format' is not defined:

		@data = (
			  [
				'eth0 in',
				'46.11'
			  ],
			  [
				'eth0 out',
				'63.02'
			  ],
			  ...
		);

	When 'format' is 'raw':

		@data = (
			  [
				'eth0 in',
				'48296309'
			  ],
			  [
				'eth0 out',
				'66038087'
			  ],
			  ...
		);

	When 'format' is 'hash':

		@data = (
			  {
				'in' => '46.12',
				'interface' => 'eth0',
				'out' => '63.04'
			  },
			  ...
		);

See Also:
	iface-rrd.pl, zapi/v3/system_stats.cgi, zapi/v2/system_stats.cgi
=cut
sub getNetworkStats
{
	my ( $format ) = @_;

	$format = "" unless defined $format; # removes undefined variable warnings

	if ( !-f "/proc/net/dev" )
	{
		print "$0: Error: File /proc/net/dev not exist ...\n";
		exit 1;
	}

	my @outHash;

	open DEV, '/proc/net/dev' or die $!;
	my ( $in, $out );
	my @data;
	my @interface;
	my @interfacein;
	my @interfaceout;

	my $i = -1;
	while ( <DEV> )
	{
		if ( $_ =~ /\:/ && $_ !~ /lo/ )
		{
			$i++;
			my @iface = split ( ":", $_ );
			my $if = $iface[0];
			$if =~ s/\ //g;

			if ( $_ =~ /:\ / )
			{
				( $in, $out ) = ( split )[1, 9];
			}
			else
			{
				( $in, $out ) = ( split )[0, 8];
				$in = ( split /:/, $in )[1];
			}

			if ( $format ne "raw" )
			{
				$in  = ( ( $in / 1024 ) / 1024 );
				$out = ( ( $out / 1024 ) / 1024 );
				$in  = sprintf ( '%.2f', $in );
				$out = sprintf ( '%.2f', $out );
			}

			$if =~ s/\ //g;

			# not show cluster maintenance interface
			next if $if eq 'cl_maintenance';

			push @interface,    $if;
			push @interfacein,  $in;
			push @interfaceout, $out;

			push @outHash, { 'interface' => $if, 'in' => $in, 'out' => $out };
		}
	}

	for ( my $j = 0 ; $j <= $i ; $j++ )
	{
		push @data, [$interface[$j] . ' in', $interfacein[$j]],
		  [$interface[$j] . ' out', $interfaceout[$j]];
	}

	close DEV;
	
	@data = @outHash if ( $format eq 'hash' );
	
	return @data;
}

=begin nd
Function: getDate

	Get date string

Parameters:
	none - .

Returns:
	string - Date string.

	Example:

		"Mon May 22 10:42:39 2017"

See Also:
	zapi/v3/system.cgi, zapi/v3/system_stats.cgi, zapi/v2/system_stats.cgi
=cut
sub getDate
{
	#$timeseconds = time();
	my $now = ctime();

	return $now;
}

=begin nd
Function: getHostname

	Get system hostname

Parameters:
	none - .

Returns:
	string - Hostname.

See Also:
	setConntrackdConfig

	getZClusterLocalIp, setKeepalivedConfig, getZClusterRemoteHost, runSync, getZCusterStatusInfo

	setNotifCreateConfFile, setNotifData, getNotifData

	zapi/v3/cluster.cgi, zapi/v3/system_stats.cgi, zapi/v3/zapi.cgi, zapi/v2/system_stats.cgi

	zenloadbalancer
=cut
sub getHostname
{
	my $hostname = `uname -n`;
	chomp $hostname;

	return $hostname;
}

=begin nd
Function: getCPU

	Get system CPU usage stats.

Parameters:
	none - .

Returns:
	list - Two dimensional array.

	Example:

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

See Also:
	zapi/v3/system_stats.cgi, zapi/v2/system_stats.cgi, cpu-rrd.pl
=cut
sub getCPU
{
	my @data;
	my $interval = 1;

	if ( !-f "/proc/stat" )
	{
		print "$0: Error: File /proc/stat not exist ...\n";
		exit 1;
	}
	
	my $cpu_user1;
	my $cpu_nice1;
	my $cpu_sys1;
	my $cpu_idle1;
	my $cpu_iowait1;
	my $cpu_irq1;
	my $cpu_softirq1; 
	my $cpu_total1;

	my $cpu_user2;
	my $cpu_nice2;
	my $cpu_sys2;
	my $cpu_idle2;
	my $cpu_iowait2;
	my $cpu_irq2;
	my $cpu_softirq2; 
	my $cpu_total2;

	my @line_s;
	my $line;
	open FR, "/proc/stat";
	foreach $line ( <FR> )
	{
		if ( $line =~ /^cpu\ / )
		{
			@line_s = split ( "\ ", $line );
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
	foreach $line ( <FR> )
	{
		if ( $line =~ /^cpu\ / )
		{
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

	my $diff_cpu_user    = $cpu_user2 - $cpu_user1;
	my $diff_cpu_nice    = $cpu_nice2 - $cpu_nice1;
	my $diff_cpu_sys     = $cpu_sys2 - $cpu_sys1;
	my $diff_cpu_idle    = $cpu_idle2 - $cpu_idle1;
	my $diff_cpu_iowait  = $cpu_iowait2 - $cpu_iowait1;
	my $diff_cpu_irq     = $cpu_irq2 - $cpu_irq1;
	my $diff_cpu_softirq = $cpu_softirq2 - $cpu_softirq1;
	my $diff_cpu_total   = $cpu_total2 - $cpu_total1;

	my $cpu_user    = ( 100 * $diff_cpu_user ) / $diff_cpu_total;
	my $cpu_nice    = ( 100 * $diff_cpu_nice ) / $diff_cpu_total;
	my $cpu_sys     = ( 100 * $diff_cpu_sys ) / $diff_cpu_total;
	my $cpu_idle    = ( 100 * $diff_cpu_idle ) / $diff_cpu_total;
	my $cpu_iowait  = ( 100 * $diff_cpu_iowait ) / $diff_cpu_total;
	my $cpu_irq     = ( 100 * $diff_cpu_irq ) / $diff_cpu_total;
	my $cpu_softirq = ( 100 * $diff_cpu_softirq ) / $diff_cpu_total;

	my $cpu_usage =
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

=begin nd
Function: getCpuCores

	Get the number of CPU cores in the system.

Parameters:
	none - .

Returns:
	integer - Number of CPU cores.

See Also:
	zapi/v3/system_stats.cgi
=cut
sub getCpuCores
{
	my $cores = 1;

	open my $stat_file, "/proc/stat";

	while( my $line = <$stat_file> )
	{
		next unless $line =~ /^cpu(\d) /;
		$cores = $1 + 1;
	}

	close $stat_file;

	return $cores;
}

=begin nd
Function: getDiskSpace

	Return total, used and free space for every partition in the system.

Parameters:
	none - .

Returns:
	list - Two dimensional array.

	@data = (
          [
            'dev-dm-0 Total',
            1981104128
          ],
          [
            'dev-dm-0 Used',
            1707397120
          ],
          [
            'dev-dm-0 Free',
            154591232
          ],
          ...
	);

See Also:
	disk-rrd.pl
=cut
sub getDiskSpace
{
	my @data;       # output

	my $df_bin = &getGlobalConfiguration( 'df_bin' );
	my @system = `$df_bin -k`;
	chomp ( @system );
	my @df_system = @system;

	foreach my $line ( @system )
	{
		next if $line !~ /^\/dev/;

		my @dd_name = split ( ' ', $line );
		my $dd_name = $dd_name[0];

		my ( $line_df ) = grep ( { /^$dd_name\s/ } @df_system );
		my @s_line = split ( /\s+/, $line_df );

		my $partitions = $s_line[0];
		$partitions =~ s/\///;
		$partitions =~ s/\//-/g;

		my $tot  = $s_line[1] * 1024;
		my $used = $s_line[2] * 1024;
		my $free = $s_line[3] * 1024;

		push ( @data,
			   [$partitions . ' Total', $tot],
			   [$partitions . ' Used',  $used],
			   [$partitions . ' Free',  $free] );
	}

	return @data;
}

=begin nd
Function: getDiskPartitionsInfo

	Get a reference to a hash with the partitions devices, mount points and name of rrd database.

Parameters:
	none - .

Returns:
	scalar - Hash reference.

	Example:

	$partitions = {
		'/dev/dm-0' => {
							'mount_point' => '/',
							'rrd_id' => 'dev-dm-0hd'
						},
		'/dev/mapper/zva64-config' => {
										'mount_point' => '/usr/local/zenloadbalancer/config',
										'rrd_id' => 'dev-mapper-zva64-confighd'
										},
		'/dev/mapper/zva64-log' => {
									'mount_point' => '/var/log',
									'rrd_id' => 'dev-mapper-zva64-loghd'
									},
		'/dev/xvda1' => {
							'mount_point' => '/boot',
							'rrd_id' => 'dev-xvda1hd'
						}
	};

See Also:
	zapi/v3/system_stats.cgi
=cut
sub getDiskPartitionsInfo
{
	my $partitions;          # output

	my $df_bin    = &getGlobalConfiguration( 'df_bin' );

	my @df_lines = grep { /^\/dev/ } `$df_bin -k`;
	chomp ( @df_lines );

	foreach my $line ( @df_lines )
	{
		my @df_line = split ( /\s+/, $line );

		my $mount_point = $df_line[5];
		my $partition   = $df_line[0];
		my $part_id     = $df_line[0];
		$part_id =~ s/\///;
		$part_id =~ s/\//-/g;

		$partitions->{ $partition } = {
										mount_point => $mount_point,
										rrd_id      => "${part_id}hd",
		};
	}

	return $partitions;
}

=begin nd
Function: getDiskMountPoint

	Get the mount point of a partition device

Parameters:
	dev - Partition device.

Returns:
	string - Mount point for such partition device.
	undef  - The partition device is not mounted

See Also:
	<genDiskGraph>
=cut
sub getDiskMountPoint
{
	my ( $dev ) = @_;

	my $df_bin    = &getGlobalConfiguration( 'df_bin' );
	my @df_system = `$df_bin -k`;
	my $mount;

	for my $line_df ( @df_system )
	{
		if ( $line_df =~ /$dev/ )
		{
			my @s_line = split ( "\ ", $line_df );
			chomp ( @s_line );

			$mount = $s_line[5];
		}
	}

	return $mount;
}

=begin nd
Function: getCPUTemp

	Get the CPU temperature in celsius degrees.

Parameters:
	none - .

Returns:
	string - Temperature in celsius degrees.

See Also:
	temperature-rrd.pl
=cut
sub getCPUTemp
{
	my $file = &getGlobalConfiguration( "temperatureFile" );
	my $lastline;

	if ( !-f "$file" )
	{
		print "$0: Error: File $file not exist ...\n";
		exit 1;
	}

	my $line;
	open FT, $file;
	while ( $line = <FT> )
	{
		$lastline = $line;
	}
	close FT;

	my @lastlines = split ( "\:", $lastline );

	my $temp = $lastlines[1];
	$temp =~ s/\ //g;
	$temp =~ s/\n//g;
	$temp =~ s/C//g;

	return $temp;
}

=begin nd
Function: zsystem

	Run a command with tuned system parameters.

Parameters:
	exec - Command to run.

Returns:
	integer - ERRNO or return code.

See Also:
	<runFarmGuardianStart>, <_runHTTPFarmStart>, <runHTTPFarmCreate>, <_runGSLBFarmStart>, <_runGSLBFarmStop>, <runFarmReload>, <runGSLBFarmCreate>, <setGSLBFarmStatus>
=cut
sub zsystem
{
	my ( @exec ) = @_;

	#~ system ( ". /etc/profile && @exec" ); 
	my $out = `. /etc/profile && @exec`;
	
	my $error = $?;
	&zenlog ("running: @exec");
	&zenlog ("output: $out") if ( $error );
	
	return $error;
}

=begin nd
Function: getDns

	Get the dns servers.

Parameters:
	none - .

Returns:
	scalar - Hash reference.

	Example:

	$dns = {
			primary => "value",
			secundary => "value",
	};

See Also:
	zapi/v3/system.cgi
=cut
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
		$dns->{ 'secondary' } = $aux[1];
	}
	else
	{
		$dns->{ 'secondary' } = "";
	}
	untie @dnsArr;

	return $dns;
}

=begin nd
Function: setDns

	Set a primary or secondary dns server.

Parameters:
	dns - 'primary' or 'secondary'.
	value - ip addres of dns server.

Returns:
	none - .

Bugs:
	Returned value.

See Also:
	zapi/v3/system.cgi
=cut
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

=begin nd
Function: getSsh

	Returns hash reference to ssh configuration.

Parameters:
	none - .

Returns:
	scalar - Hash reference.

	Example:

	$ssh = {
			'port'   => 22,
			'listen' => "*",
	};

See Also:
	zapi/v3/system.cgi, dos.cgi
=cut
sub getSsh
{
	my $sshFile = &getGlobalConfiguration( 'sshConf' );
	my $ssh     = {                                       # conf
				'port'   => 22,
				'listen' => "*",
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

	$ssh->{ 'listen' } = '*' if ( $ssh->{ 'listen' } eq '0.0.0.0' );
	return $ssh;
}

=begin nd
Function: setSsh

	Set ssh configuration.

	To listen on all the ip addresses set 'listen' to '*'.

Parameters:
	sshConf - Hash reference with ssh configuration.

	Example:

	$ssh = {
			'port'   => 22,
			'listen' => "*",
	};

Returns:
	integer - ERRNO or return code of ssh restart.

See Also:
	zapi/v3/system.cgi
=cut
sub setSsh
{
	my ( $sshConf ) = @_;
	my $sshFile     = &getGlobalConfiguration( 'sshConf' );
	my $output      = 1;
	my $index       = 5
	  ; # default, it is the line where will add port and listen if one of this doesn't exist

	# create flag to check all params are changed
	my $portFlag   = 1 if ( exists $sshConf->{ 'port' } );
	my $listenFlag = 1 if ( exists $sshConf->{ 'listen' } );
	$sshConf->{ 'listen' } = '0.0.0.0' if ( $sshConf->{ 'listen' } eq '*' );

	if ( !-e $sshFile )
	{
		&zenlog( "SSH configuration file doesn't exist." );
		return -1;
	}

	tie my @file, 'Tie::File', $sshFile;
	foreach my $line ( @file )
	{
		if ( $portFlag )
		{
			if ( $line =~ /^Port\s+/ )
			{
				$line     = "Port $sshConf->{ 'port' }";
				$output   = 0;
				$portFlag = 0;
			}
		}
		if ( $listenFlag )
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
	
	&setDOSParam( 'ssh_brute_force', 'port', $sshConf->{ 'port' } );
	# restart sshbruteforce ipds rule if this is actived
	if ( &getDOSParam( 'ssh_brute_force', 'status' ) eq 'up' )
	{
		&setDOSParam( 'ssh_brute_force', 'status', 'down' );
		&setDOSParam( 'ssh_brute_force', 'status', 'up' );
	}
	else
	{
		
	}

	return $output;
}

=begin nd
Function: getHttpServerPort

	Get the web GUI port.

Parameters:
	none - .

Returns:
	integer - Web GUI port.

See Also:
	zapi/v3/system.cgi
=cut
sub getHttpServerPort
{
	my $gui_port;    # output

	my $confhttp = &getGlobalConfiguration( 'confhttp' );
	open my $fh, "<", "$confhttp";

	# read line matching 'server!bind!1!port = <PORT>'
	my $config_item = 'server!bind!1!port';

	while ( my $line = <$fh> )
	{
		if ( $line =~ /$config_item/ )
		{
			( undef, $gui_port ) = split ( "=", $line );
			last;
		}
	}

	#~ my @httpdconffile = <$fr>;
	close $fh;

	chomp ( $gui_port );
	$gui_port =~ s/\s//g;
	$gui_port = 444 if ( !$gui_port );

	return $gui_port;
}

=begin nd
Function: setHttpServerPort

	Set the web GUI port.

Parameters:
	httpport - Port number.

Returns:
	none - .

See Also:
	zapi/v3/system.cgi
=cut
sub setHttpServerPort
{
	my ( $httpport ) = @_;
	$httpport =~ s/\ //g;

	my $confhttp = &getGlobalConfiguration( 'confhttp' );
	use Tie::File;
	tie my @array, 'Tie::File', "$confhttp";
	@array[2] = "server!bind!1!port = $httpport\n";
	untie @array;
}

=begin nd
Function: getHttpServerIp

	Get the GUI service ip address

Parameters:
	none - .

Returns:
	scalar - GUI ip address or '*' for all local addresses

See Also:
	zapi/v3/system.cgi, zenloadbalancer
=cut
sub getHttpServerIp
{
	my $gui_ip;        # output

	my $confhttp = &getGlobalConfiguration( 'confhttp' );
	open my $fh, "<", "$confhttp";

	# read line matching 'server!bind!1!interface = <IP>'
	my $config_item = 'server!bind!1!interface';

	while ( my $line = <$fh> )
	{
		if ( $line =~ /$config_item/ )
		{
			( undef, $gui_ip ) = split ( "=", $line );
			last;
		}
	}

	close $fh;

	chomp ( $gui_ip );
	$gui_ip =~ s/\s//g;

	if ( &ipisok( $gui_ip, 4 ) ne "true" )
	{
		$gui_ip = "*";
	}

	return $gui_ip;
}

=begin nd
Function: setHttpServerIp

	Set the GUI service ip address

Parameters:
	ip - IP address.

Returns:
	none - .

See Also:
	zapi/v3/system.cgi
=cut
sub setHttpServerIp
{
	my $ip = shift;

	my $confhttp = &getGlobalConfiguration( 'confhttp' );

	#action save ip
	use Tie::File;
	tie my @array, 'Tie::File', "$confhttp";
	if ( $ip =~ /^\*$/ )
	{
		@array[1] = "#server!bind!1!interface = \n";
		&zenlog( "The interface where is running is --All interfaces--" );
	}
	else
	{
		@array[1] = "server!bind!1!interface = $ip\n";

		#~ if ( &ipversion( $ipgui ) eq "IPv6" )
		#~ {
		#~ @array[4] = "server!ipv6 = 1\n";
		#~ &zenlog(
		#~ "The interface where is running the GUI service is: $ipgui with IPv6" );
		#~ }
		#~ elsif ( &ipversion( $ipgui ) eq "IPv4" )
		#~ {
		#~ @array[4] = "server!ipv6 = 0\n";
		#~ &zenlog(
		#~ "The interface where is running the GUI service is: $ipgui with IPv4" );
		#~ }
	}
	untie @array;
}

use File::stat;
use File::Basename;

=begin nd
Function: getBackup

	List the backups in the system.

Parameters:
	none - .

Returns:
	scalar - Array reference.

See Also:
	<getExistsBackup>, zapi/v3/system.cgi
=cut
sub getBackup
{
	my @backups;
	my $backupdir = &getGlobalConfiguration( 'backupdir' );
	my $backup_re = &getValidFormat( 'backup' );

	opendir ( DIR, $backupdir );
	my @files = grep ( /^backup.*/, readdir ( DIR ) );
	closedir ( DIR );

	foreach my $line ( @files )
	{
		my $filepath = "$backupdir$line";
		chomp ( $filepath );

		$line =~ s/backup-($backup_re).tar.gz/$1/;

		my $datetime_string = ctime( stat ( $filepath )->mtime );
		push @backups, { 'name' => $line, 'date' => $datetime_string };

	}

	return \@backups;
}

=begin nd
Function: getExistsBackup

	Check if there is a backup with the given name.

Parameters:
	name - Backup name.

Returns:
	1     - if the backup exists.
	undef - if the backup does not exist.

See Also:
	zapi/v3/system.cgi
=cut
sub getExistsBackup
{
	my $name = shift;
	my $find;

	foreach my $backup ( @{ &getBackup } )
	{
		if ( $backup->{ 'name' } =~ /^$name/, )
		{
			$find = 1;
			last;
		}
	}
	return $find;
}

=begin nd
Function: createBackup

	Creates a backup with the given name

Parameters:
	name - Backup name.

Returns:
	integer - ERRNO or return code of backup creation process.

See Also:
	zapi/v3/system.cgi
=cut
sub createBackup
{
	my $name      = shift;
	my $zenbackup = &getGlobalConfiguration( 'zenbackup' );
	my $error     = system ( "$zenbackup $name -c 2> /dev/null" );

	return $error;
}

=begin nd
Function: downloadBackup

	Get zapi client to download a backup file.

Parameters:
	backup - Backup name.

Returns:
	1 - on error.

	Does not return on success.

See Also:
	zapi/v3/system.cgi
=cut
sub downloadBackup
{
	my $backup = shift;
	my $error;

	$backup = "backup-$backup.tar.gz";
	my $backupdir = &getGlobalConfiguration( 'backupdir' );
	open ( my $download_fh, '<', "$backupdir/$backup" );

	if ( -f "$backupdir\/$backup" && $download_fh )
	{
		my $cgi = &getCGI();
		print $cgi->header(
							-type            => 'application/x-download',
							-attachment      => $backup,
							'Content-length' => -s "$backupdir/$backup",
		);

		binmode $download_fh;
		print while <$download_fh>;
		close $download_fh;
		exit;
	}
	else
	{
		$error = 1;
	}
	return $error;
}

=begin nd
Function: uploadBackup

	Store an uploaded backup.

Parameters:
	filename - Uploaded backup file name.
	upload_filehandle - File handle or file content.

Returns:
	1     - on failure.
	undef - on success.

See Also:
	zapi/v3/system.cgi
=cut
sub uploadBackup
{
	my $filename          = shift;
	my $upload_filehandle = shift;
	my $error;
	my $configdir = &getGlobalConfiguration( 'backupdir' );
	$filename = "backup-$filename.tar.gz";

	if ( !-f "$configdir/$filename" )
	{
		open ( my $filehandle, '>', "$configdir/$filename" ) or die "$!";
		print $filehandle $upload_filehandle;
		close $filehandle;
	}
	else
	{
		$error = 1;
	}
	return $error;
}

=begin nd
Function: deleteBackup

	Delete a backup.

Parameters:
	file - Backup name.

Returns:
	1     - on failure.
	undef - on success.

See Also:
	zapi/v3/system.cgi
=cut
sub deleteBackup
{
	my $file      = shift;
	$file      = "backup-$file.tar.gz";
	my $backupdir = &getGlobalConfiguration( "backupdir" );
	my $filepath  = "$backupdir$file";
	my $error;

	if ( -e $filepath )
	{
		unlink ( $filepath );
		&zenlog( "Deleted backup file $file" );
	}
	else
	{
		&zenlog( "File $file not found" );
		$error = 1;
	}

	return $error;
}

=begin nd
Function: applyBackup

	Restore files from a backup.

Parameters:
	backup - Backup name.

Returns:
	integer - ERRNO or return code of restarting load balancing service.

See Also:
	zapi/v3/system.cgi
=cut
sub applyBackup
{
	my $backup = shift;
	my $error;
	my $tar  = &getGlobalConfiguration( 'tar' );
	my $file = &getGlobalConfiguration( 'backupdir' ) . "/backup-$backup.tar.gz";

	my @eject = `$tar -xvzf $file -C /`;

	&zenlog( "Restoring backup $file" );
	&zenlog( "unpacking files: @eject" );
	$error = system ( "/etc/init.d/zenloadbalancer restart 2> /dev/null" );

	if ( !$error )
	{
		&zenlog( "Backup applied and Zen Load Balancer restarted..." );
	}
	else
	{
		&zenlog( "Problem restarting Zen Load Balancer service" );
	}

	return $error;
}

=begin nd
Function: getLogs

	Get list of log files.

Parameters:
	none - .

Returns:
	scalar - Array reference.

	Array element example:

	{
		'file' => $line,
		'date' => $datetime_string
	}

See Also:
	zapi/v3/system.cgi
=cut
sub getLogs
{
	my @logs;
	my $logdir = &getGlobalConfiguration( 'logdir' );

	opendir ( DIR, $logdir );
	my @files = grep ( /^syslog/, readdir ( DIR ) );
	closedir ( DIR );

	foreach my $line ( @files )
	{
		my $filepath = "$logdir/$line";
		chomp ( $filepath );
		my $datetime_string = ctime( stat ( $filepath )->mtime );
		push @logs, { 'file' => $line, 'date' => $datetime_string };
	}

	return \@logs;
}

=begin nd
Function: downloadLog

	Download a log file.

	This function ends the current precess on success.

	Should this function be part of the API?

Parameters:
	logFile - log file name in /var/log.

Returns:
	1 - on failure.

See Also:
	zapi/v3/system.cgi
=cut
sub downloadLog
{
	my $logFile = shift;
	my $error;

	my $logdir = &getGlobalConfiguration( 'logdir' );
	open ( my $download_fh, '<', "$logdir/$logFile" );

	if ( -f "$logdir\/$logFile" && $download_fh )
	{
		my $cgi = &getCGI();
		print $cgi->header(
							-type            => 'application/x-download',
							-attachment      => $logFile,
							'Content-length' => -s "$logdir/$logFile",
		);

		binmode $download_fh;
		print while <$download_fh>;
		close $download_fh;
		exit;
	}
	else
	{
		$error = 1;
	}
	return $error;
}

=begin nd
Function: getTotalConnections

	Get the number of current connections on this appliance.

Parameters:
	none - .

Returns:
	integer - The number of connections.

See Also:
	zapi/v3/system_stats.cgi
=cut
sub getTotalConnections
{
	my $conntrack = &getGlobalConfiguration ( "conntrack" );
	my $conns = `$conntrack -C`;
	$conns =~ s/(\d+)/$1/;
	$conns += 0;
	
	return $conns;
}

=begin nd
Function: getApplianceVersion

	Returns a string with the description of the appliance.

Parameters:
	none - .

Returns:
	string - Version string.

See Also:
	zapi/v3/system.cgi, zenbui.pl, zenloadbalancer
=cut
sub getApplianceVersion
{
	my $version;
	my $hyperv;
	my $applianceFile = &getGlobalConfiguration ( 'applianceVersionFile' );
	my $lsmod = &getGlobalConfiguration ( 'lsmod' );
	my @packages = `$lsmod`;
	my @hypervisor = grep ( /(xen|vm|hv|kvm)_/ , @packages );
	
	# look for appliance vesion
	if ( -f $applianceFile )
	{
		use Tie::File;
		tie my @filelines, 'Tie::File', $applianceFile;
		$version = $filelines[0];
		untie @filelines;
	}
	
	# generate appliance version
	if ( ! $version )
	{
		my $uname = &getGlobalConfiguration( 'uname' );
		my $kernel = `$uname -r`;
		#~ $kernel = "$uname -r";
		my $awk = &getGlobalConfiguration( 'awk' );
		my $ifconfig = &getGlobalConfiguration( 'ifconfig' );
		
		# look for mgmt interface
		my @ifaces = `ifconfig -s | awk '{print $1}'`;
		# Network appliance
		if ( $kernel =~ /3\.2\.0\-4/ && grep ( /mgmt/, @ifaces ) )
		{
			$version = "ZNA 3300";
		}
		else
		{
			# select appliance verison
			if ( $kernel =~ /3\.2\.0\-4/ ) 				{ $version = "3110"; }
			elsif ( $kernel =~ /3\.16\.0\-4/ ) 			{ $version = "4000"; }
			elsif ( $kernel =~ /3\.16\.7\-ckt20/ ) 	{ $version = "4100"; }
			else													{ $version = "System version not detected"; }

			# virtual appliance
			if ( $hypervisor[0] =~ /(xen|vm|hv|kvm)_/ )
			{
				$version = "ZVA $version";
			}
			# baremetal appliance
			else
			{
				$version = "ZBA $version";
			}
		}
		# save version for future request
		use Tie::File;
		tie my @filelines, 'Tie::File', $applianceFile;
		$filelines[0] = $version;
		untie @filelines;
	}
	
	# virtual appliance
	if ( $hypervisor[0] =~ /(xen|vm|hv|kvm)_/ )
	{
		$hyperv= $1;
		$hyperv = 'HyperV' if ( $hyperv eq 'hv' );
		$hyperv = 'Vmware' if ( $hyperv eq 'vm' );
		$hyperv = 'Xen' if ( $hyperv eq 'xen' );
		$hyperv = 'KVM' if ( $hyperv eq 'kvm' );
	}

	# before zevenet versions had hypervisor in appliance version file, so not inclue it in the chain
	if ($hyperv && $version !~ /hypervisor/ )
	{
		$version = "$version, hypervisor: $hyperv";
	}
	
	return $version;
}

1;
