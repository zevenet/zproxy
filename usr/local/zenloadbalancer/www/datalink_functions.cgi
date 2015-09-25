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

#
sub getDatalinkFarmAlgorithm($ffile)
{
	my ( $ffile ) = @_;
	my $output = -1;
	open FI, "<$configdir/$ffile";
	my $first = "true";
	while ( my $line = <FI> )
	{
		if ( $line ne "" && $first eq "true" )
		{
			$first = "false";
			my @line = split ( "\;", $line );
			$output = @line[3];
		}
	}
	close FI;
	return $output;
}

# set the lb algorithm to a farm
sub setDatalinkFarmAlgorithm($alg,$ffile)
{
	my ( $alg, $ffile ) = @_;
	my $output = -1;
	use Tie::File;
	tie @filelines, 'Tie::File', "$configdir\/$ffile";
	my $i = 0;
	for $line ( @filelines )
	{
		if ( $line =~ /^$fname\;/ )
		{
			my @args = split ( "\;", $line );
			$line = "@args[0]\;@args[1]\;@args[2]\;$alg\;@args[4]";
			splice @filelines, $i, $line;
			$output = $?;
		}
		$i++;
	}
	untie @filelines;
	$output = $?;

	# Apply changes online
	if ( $output != -1 )
	{
		&runFarmStop( $farmname, "true" );
		&runFarmStart( $farmname, "true" );
	}
	return $output;
}

#
sub getDatalinkFarmBootStatus($file)
{
	my ( $file ) = @_;
	my $output = "down";
	open FI, "<$configdir/$file";
	my $first = "true";
	while ( my $line = <FI> )
	{
		if ( $line ne "" && $first eq "true" )
		{
			$first = "false";
			my @line_a = split ( "\;", $line );
			$output = @line_a[4];
			chomp ( $output );
		}
	}
	close FI;
	return $output;
}

# get network physical (vlan included) interface used by the farm vip
sub getFarmInterface($fname)
{
	my ( $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $output = -1;

	if ( $type eq "datalink" )
	{
		my $file = &getFarmFile( $fname );
		open FI, "<$configdir/$file";
		my $first = "true";
		while ( $line = <FI> )
		{
			if ( $line ne "" && $first eq "true" )
			{
				$first = "false";
				my @line_a = split ( "\;", $line );
				my @line_b = split ( "\:", @line_a[2] );
				$output = @line_b[0];
			}
		}
		close FI;
	}

	return $output;
}

#
sub _runDatalinkFarmStart($file,$writeconf,$status)
{
	my ( $file, $writeconf, $status ) = @_;
	if ( $writeconf eq "true" )
	{
		use Tie::File;
		tie @filelines, 'Tie::File', "$configdir\/$file";
		my $first = 1;
		foreach ( @filelines )
		{
			if ( $first eq 1 )
			{
				s/\;down/\;up/g;
				$first = 0;
			}
		}
		untie @filelines;
	}

	# include cron task to check backends
	use Tie::File;
	tie @filelines, 'Tie::File', "/etc/cron.d/zenloadbalancer";
	my @farmcron = grep /\# \_\_$fname\_\_/, @filelines;
	my $cron = @farmcron;
	if ( $cron eq 0 )
	{
		push ( @filelines,
			   "* * * * *	root	\/usr\/local\/zenloadbalancer\/app\/libexec\/check_uplink $fname \# \_\_$fname\_\_"
		);
	}
	untie @filelines;

	# Apply changes online
	if ( $status != -1 )
	{
		# Set default uplinks as gateways
		my $iface     = &getFarmInterface( $fname );
		my @eject     = `$ip_bin route del default table table_$iface 2> /dev/null`;
		my @servers   = &getFarmServers( $fname );
		my $algorithm = &getFarmAlgorithm( $fname );
		my $routes    = "";
		if ( $algorithm eq "weight" )
		{

			foreach $serv ( @servers )
			{
				chomp ( $serv );
				my @line = split ( "\;", $serv );
				my $stat = @line[5];
				chomp ( $stat );
				my $wei = 1;
				if ( @line[3] ne "" )
				{
					$wei = @line[3];
				}
				if ( $stat eq "up" )
				{
					$routes = "$routes nexthop via @line[1] dev @line[2] weight $wei";
				}
			}
		}
		if ( $algorithm eq "prio" )
		{
			my $bestprio = 100;
			foreach $serv ( @servers )
			{
				chomp ( $serv );
				my @line = split ( "\;", $serv );
				my $stat = @line[5];
				my $prio = @line[4];
				chomp ( $stat );
				if (    $stat eq "up"
					 && $prio > 0
					 && $prio < 10
					 && $prio < $bestprio )
				{
					$routes   = "nexthop via @line[1] dev @line[2] weight 1";
					$bestprio = $prio;
				}
			}
		}
		if ( $routes ne "" )
		{
			&logfile(
				  "running $ip_bin route add default scope global table table_$iface $routes" );
			my @eject =
			  `$ip_bin route add default scope global table table_$iface $routes 2> /dev/null`;
			$status = $?;
		}
		else
		{
			$status = 0;
		}

		# Set policies to the local network
		my $ip = &iponif( $iface );
		if ( $ip =~ /\./ )
		{
			my $ipmask = &maskonif( $if );
			my ( $net, $mask ) = ipv4_network( "$ip / $ipmask" );
			&logfile( "running $ip_bin rule add from $net/$mask lookup table_$iface" );
			my @eject = `$ip_bin rule add from $net/$mask lookup table_$iface 2> /dev/null`;
		}

		# Enable IP forwarding
		&setIpForward( "true" );

		# Enable active datalink file
		open FI, ">$piddir\/$fname\_datalink.pid";
		close FI;
	}
	return $status;
}

#
sub _runDatalinkFarmStop($filename,$writeconf,$status)
{
	my ( $filename, $writeconf, $status ) = @_;
	if ( $writeconf eq "true" )
	{
		use Tie::File;
		tie @filelines, 'Tie::File', "$configdir\/$filename";
		my $first = 1;
		foreach ( @filelines )
		{
			if ( $first eq 1 )
			{
				s/\;up/\;down/g;
				$status = $?;
				$first  = 0;
			}
		}
		untie @filelines;
	}

	# delete cron task to check backends
	use Tie::File;
	tie @filelines, 'Tie::File', "/etc/cron.d/zenloadbalancer";
	@filelines = grep !/\# \_\_$farmname\_\_/, @filelines;
	untie @filelines;

	# Apply changes online
	if ( $status != -1 )
	{
		my $iface = &getFarmInterface( $fname );

		# Disable policies to the local network
		my $ip = &iponif( $iface );
		if ( $ip =~ /\./ )
		{
			my $ipmask = &maskonif( $if );
			my ( $net, $mask ) = ipv4_network( "$ip / $ipmask" );
			&logfile( "running $ip_bin rule del from $net/$mask lookup table_$iface" );
			my @eject = `$ip_bin rule del from $net/$mask lookup table_$iface 2> /dev/null`;
		}

		# Disable default uplink gateways
		my @eject = `$ip_bin route del default table table_$iface 2> /dev/null`;

		# Disable active datalink file
		unlink ( "$piddir\/$fname\_datalink.pid" );
		if ( -e "$piddir\/$fname\_datalink.pid" )
		{
			$status = -1;
		}
		else
		{
			$status = 0;
		}
	}
	return $status;
}

#
sub runDatalinkFarmCreate($fname,$fvip,$fdev)
{
	my ( $fname, $fvip, $fdev ) = @_;
	open FO, ">$configdir\/$fname\_datalink.cfg";
	print FO "$fname\;$fvip\;$fdev\;weight\;up\n";
	close FO;
	$output = $?;

	if ( !-e "$piddir/$fname_datalink.pid" )
	{

		# Enable active datalink file
		open FI, ">$piddir\/$fname\_datalink.pid";
		close FI;
	}
	return $output;
}

# Returns farm vip
sub getDatalinkFarmVip($info,$file)
{
	my ( $info, $file ) = @_;
	my $output = -1;
	open FI, "<$configdir/$file";
	my $first = "true";
	while ( $line = <FI> )
	{
		if ( $line ne "" && $first eq "true" )
		{
			$first = "false";
			my @line_a = split ( "\;", $line );
			if ( $info eq "vip" )   { $output = @line_a[1]; }
			if ( $info eq "vipp" )  { $output = @line_a[2]; }
			if ( $info eq "vipps" ) { $output = "@vip[1]\:@vipp[2]"; }
		}
	}
	close FI;
	return $output;
}

# Set farm virtual IP and virtual PORT
sub setDatalinkFarmVirtualConf($vip,$vipp,$fname,$fconf)
{
	my ( $vip, $vipp, $fname, $fconf ) = @_;
	my $stat = -1;
	use Tie::File;
	tie @filelines, 'Tie::File', "$configdir\/$fconf";
	my $i = 0;
	for $line ( @filelines )
	{
		if ( $line =~ /^$fname\;/ )
		{
			my @args = split ( "\;", $line );
			$line = "@args[0]\;$vip\;$vipp\;@args[3]\;@args[4]";
			splice @filelines, $i, $line;
			$stat = $?;
		}
		$i++;
	}
	untie @filelines;
	$stat = $?;
	return $stat;
}

#
sub setDatalinkFarmServer($file,$ids,$rip,$iface,$weight,$priority)
{
	my ( $file, $ids, $rip, $iface, $weight, $priority ) = @_;
	my $output = -1;
	tie @contents, 'Tie::File', "$configdir\/$file";
	my $i   = 0;
	my $l   = 0;
	my $end = "false";
	foreach $line ( @contents )
	{

		if ( $line =~ /^\;server\;/ && $end ne "true" )
		{
			if ( $i eq $ids )
			{
				my $dline = "\;server\;$rip\;$iface\;$weight\;$priority\;up\n";
				splice @contents, $l, 1, $dline;
				$output = $?;
				$end    = "true";
			}
			else
			{
				$i++;
			}
		}
		$l++;
	}
	if ( $end eq "false" )
	{
		push ( @contents, "\;server\;$rip\;$iface\;$weight\;$priority\;up\n" );
		$output = $?;
	}
	untie @contents;

	# Apply changes online
	if ( $output != -1 )
	{
		&runFarmStop( $farmname, "true" );
		&runFarmStart( $farmname, "true" );
	}
	return $output;
}

#
sub runDatalinkFarmServerDelete($ids,$ffile)
{
	my ( $ids, $ffile ) = @_;
	my $output = -1;
	tie my @contents, 'Tie::File', "$configdir\/$ffile";
	my $i   = 0;
	my $l   = 0;
	my $end = "false";
	foreach $line ( @contents )
	{

		if ( $line =~ /^\;server\;/ && $end ne "true" )
		{
			if ( $i eq $ids )
			{
				splice @contents, $l, 1,;
				$output = $?;
				$end    = "true";
			}
			else
			{
				$i++;
			}
		}
		$l++;
	}
	untie @contents;
	return $output;
}

#function that return the status information of a farm:
#ip, port, backendstatus, weight, priority, clients
sub getDatalinkFarmBackendsStatus(@content)
{
	my ( @content ) = @_;
	my @output = -1;
	my @servers;
	foreach $server ( @content )
	{
		my @serv = split ( ";", $server );
		push ( @servers, "@serv[2]\;@serv[3]\;@serv[4]\;@serv[5]\;@serv[6]" );
	}
	@output = @servers;

	return $output;
}

sub setDatalinkFarmBackendStatus($file,$index,$stat)
{
	my ( $file, $index, $stat ) = @_;
	my $output = -1;

	use Tie::File;
	tie @filelines, 'Tie::File', "$configdir\/$file";
	my $fileid   = 0;
	my $serverid = 0;
	foreach $line ( @filelines )
	{
		if ( $line =~ /\;server\;/ )
		{
			if ( $serverid eq $index )
			{
				my @lineargs = split ( "\;", $line );
				@lineargs[6] = $stat;
				@filelines[$fileid] = join ( "\;", @lineargs );
			}
			$serverid++;
		}
		$fileid++;
	}
	untie @filelines;

	return $output;
}

# do not remove this
1
