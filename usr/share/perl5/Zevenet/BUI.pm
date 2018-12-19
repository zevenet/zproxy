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

#~ use Net::IP;
use Curses::UI;
use Zevenet::Config;

sub get_system_mem
{
	my $line;
	my (
		 $mname,  $mvalue,  $mfname,  $mfvalue,  $mused,   $mbname,   $mbvalue,
		 $mcname, $mcvalue, $swtname, $swtvalue, $swfname, $swfvalue, $swused
	);

	if ( -f "/proc/meminfo" )
	{
		open FR, "/proc/meminfo";

		while ( $line = <FR> )
		{
			if ( $line =~ /memtotal/i )
			{
				my @memtotal = split ( ": ", $line );
				$mname = $memtotal[0];
				$memtotal[1] =~ s/^\s+//;
				@memtotal = split ( " ", $memtotal[1] );
				$mvalue = $memtotal[0] / 1024;

			}
			if ( $line =~ /memfree/i )
			{
				my @memfree = split ( ": ", $line );
				$mfname = $memfree[0];
				$memfree[1] =~ s/^\s+//;
				@memfree = split ( " ", $memfree[1] );
				$mfvalue = $memfree[0] / 1024;
			}
			if ( $mname && $mfname )
			{
				$mused = $mvalue - $mfvalue;
			}
			if ( $line =~ /buffers/i )
			{
				my @membuf = split ( ": ", $line );
				$mbname = $membuf[0];
				$membuf[1] =~ s/^\s+//;
				@membuf = split ( " ", $membuf[1] );
				$mbvalue = $membuf[0] / 1024;
			}
			if ( $line =~ /^cached/i )
			{
				my @memcached = split ( ": ", $line );
				$mcname = $memcached[0];
				$memcached[1] =~ s/^\s+//;
				@memcached = split ( " ", $memcached[1] );
				$mcvalue = $memcached[0] / 1024;
			}
			if ( $line =~ /swaptotal/i )
			{
				my @swtotal = split ( ": ", $line );
				$swtname = $swtotal[0];
				$swtotal[1] =~ s/^\s+//;
				@swtotal = split ( " ", $swtotal[1] );
				$swtvalue = $swtotal[0] / 1024;

			}
			if ( $line =~ /swapfree/i )
			{
				my @swfree = split ( ": ", $line );
				$swfname = $swfree[0];
				$swfree[1] =~ s/^\s+//;
				@swfree = split ( " ", $swfree[1] );
				$swfvalue = $swfree[0] / 1024;
			}
			if ( $swtname && $swfname )
			{
				$swused = $swtvalue - $swfvalue;
			}
		}
		$mvalue   = sprintf ( "%.0f", $mvalue );
		$mfvalue  = sprintf ( "%.0f", $mfvalue );
		$mused    = sprintf ( "%.0f", $mused );
		$mbvalue  = sprintf ( "%.0f", $mbvalue );
		$mcvalue  = sprintf ( "%.0f", $mcvalue );
		$swtvalue = sprintf ( "%.0f", $swtvalue );
		$swfvalue = sprintf ( "%.0f", $swfvalue );
		$swused   = sprintf ( "%.0f", $swused );
	}
	my @data = (
				 [$mname,     $mvalue],
				 [$mfname,    $mfvalue],
				 ['MemUsed',  $mused],
				 [$mbname,    $mbvalue],
				 [$mcname,    $mcvalue],
				 [$swtname,   $swtvalue],
				 [$swfname,   $swfvalue],
				 ['SwapUsed', $swused],
	);
	return @data;
}

sub get_system_loadavg
{
	my ( $line, $lastline );
	my ( $last, $last5, $last15 );
	if ( -f "/proc/loadavg" )
	{
		open FR, "/proc/loadavg";
		while ( $line = <FR> )
		{
			$lastline = $line;
		}
		my @splitline = split ( " ", $lastline );
		$last   = $splitline[0];
		$last5  = $splitline[1];
		$last15 = $splitline[2];

	}
	my @data = ( ['Last', $last], ['Last 5', $last5], ['Last 15', $last15], );
	return @data;
}

sub get_system_cpu
{
	my $interval = 1;
	my ( $line,         @line_s );
	my ( $cpu_user1,    $cpu_user2, $cpu_user, $diff_cpu_user );
	my ( $cpu_nice1,    $cpu_nice2, $cpu_nice, $diff_cpu_nice );
	my ( $cpu_sys1,     $cpu_sys2, $cpu_sys, $diff_cpu_sys );
	my ( $cpu_idle1,    $cpu_idle2, $cpu_idle, $diff_cpu_idle );
	my ( $cpu_iowait1,  $cpu_iowait2, $cpu_iowait, $diff_cpu_iowait );
	my ( $cpu_irq1,     $cpu_irq2, $cpu_irq, $diff_cpu_irq );
	my ( $cpu_softirq1, $cpu_softirq2, $cpu_softirq, $diff_cpu_softirq );
	my ( $cpu_total1,   $cpu_total2, $cpu_usage, $diff_cpu_total );

	if ( -f "/proc/stat" )
	{
		open FR, "/proc/stat";
		foreach $line ( <FR> )
		{
			if ( $line =~ /^cpu\ / )
			{
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
		open FR, "/proc/stat";
		sleep $interval;
		foreach my $line ( <FR> )
		{
			if ( $line =~ /^cpu\ / )
			{
				my @line_s = split ( "\ ", $line );
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

	}
	my @data = (
				 ['UserCPU',       $cpu_user],
				 ['NiceCPU',       $cpu_nice],
				 ['SysCPU',        $cpu_sys],
				 ['IdleCPU',       $cpu_idle],
				 ['IowaitCPU',     $cpu_iowait],
				 ['IrqCPU',        $cpu_irq],
				 ['SoftIrqCPU',    $cpu_softirq],
				 ['TotalUsageCPU', $cpu_usage],
	);
	return @data;
}

sub set_data_string
{
	my ( @datain ) = @_;

	my $outputstring = "";
	my $i            = 0;
	my $j            = 0;

	for $i ( 0 .. $#datain )
	{
		$outputstring =
		  $outputstring . "\t" . $datain[$i][0] . ": " . $datain[$i][1] . "\n";
	}

	return $outputstring;
}

sub get_interface_stack_ip_mask_gateway    # ($if_name, $ip_version)
{
	my $if_name    = shift;
	my $ip_version = shift;

	my ( $ip, $mask, $gateway );
	$gateway = '';

	if ( $ip_version == 6 )
	{
		$ip =
		  `ifconfig $if_name | grep 'Scope:Global' | awk -F'inet6 addr:' '{print \$2}' | head -n 1 | awk '{printf \$1}'`;
	}
	else    # ipv4
	{
		$ip =
		  `ifconfig $if_name | awk -F'inet addr:' '{print \$2}' | awk '{printf \$1}'`;
	}

	if ( $ip_version == 6 )
	{
		my $defaultgw6 = &getGlobalConfiguration('defaultgw6');
		my $defaultgwif6 = &getGlobalConfiguration('defaultgwif6');
		( $ip, $mask ) = split ( '/', $ip );
		$gateway = $defaultgw6 if $defaultgwif6 eq $if_name;
	}
	else    # ipv4
	{
		$mask = `ifconfig $if_name | awk -F'Mask:' '{printf \$2}'`;
		chomp ( $mask );
		my $ip_bin = &getGlobalConfiguration('ip_bin');
		my ( $default_gw_line ) = `$ip_bin route`;

		$default_gw_line =~ /via (.+)? dev (\w+)? /;
		my $gw_ip = $1;
		my $gw_if = $2;

		#~ &zenlog("default_gw_line:$default_gw_line");
		#~ &zenlog("gw_ip:$gw_ip");
		#~ &zenlog("gw_if:$gw_if");

		$gateway = $gw_ip if $gw_if eq $if_name;
	}

	# required to get empty variables, so curses text_entry widget show empty
	$ip      = $ip      // '';
	$mask    = $mask    // '';
	$gateway = $gateway // '';

	#~ &zenlog("ip:$ip netmask:$mask gateway:$gateway");

	return ( $ip, $mask, $gateway );
}

1;