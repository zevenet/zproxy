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
sub setTcpUdpFarmBlacklistTime($fbltime,$fname,$type,$ffile)
{
	my ( $fbltime, $fname, $type, $ffile ) = @_;

	my $output = -1;

	&logfile( "setting 'Blacklist time $fbltime' for $fname farm $type" );
	my $fport       = &getFarmPort( $fname );
	my $fmaxservers = &getFarmMaxServers( $fname );
	&logfile( "running '$pen_ctl 127.0.0.1:$fport blacklist $fbltime'" );
	my @run = `$pen_ctl 127.0.0.1:$fport blacklist $fbltime 2> /dev/null`;
	$output = $?;
	&logfile( "running '$pen_ctl 127.0.0.1:$fport write '$configdir/$ffile''" );
	my @run = `$pen_ctl 127.0.0.1:$fport write '$configdir/$ffile'`;
	$output = $? && $output;
	&setFarmMaxServers( $fmaxservers, $fname );

	return $output;
}

#
sub getTcpUdpFarmBlacklistTime($fname)
{
	my ( $fname ) = @_;
	my $output = -1;

	my $fport = &getFarmPort( $fname );
	&logfile( "running '$pen_ctl 127.0.0.1:$fport blacklist' for $fname farm" );
	$output = `$pen_ctl 127.0.0.1:$fport blacklist 2> /dev/null`;

	return $output;
}

#asign a timeout value to a farm
sub setTcpUdpFarmTimeout($timeout,$fname)
{
	my ( $timeout, $fname ) = @_;

	my $output      = -1;
	my $fport       = &getFarmPort( $fname );
	my $fmaxservers = &getFarmMaxServers( $fname );

	&logfile(
		 "running '$pen_ctl 127.0.0.1:$fport timeout $timeout' for $fname farm $type" );

	my @run = `$pen_ctl 127.0.0.1:$fport timeout $timeout 2> /dev/null`;
	$output = $?;

	&logfile(
		"running '$pen_ctl 127.0.0.1:$fport write '$configdir/$ffile'' for $fname farm $type"
	);

	my @run = `$pen_ctl 127.0.0.1:$fport write '$configdir/$ffile'`;
	$output = $? && $output;
	&setFarmMaxServers( $fmaxservers, $fname );

	return $output;
}

#
sub getTcpUdpFarmTimeout($fname)
{
	my ( $fname ) = @_;

	my $output = -1;
	my $fport  = &getFarmPort( $fname );

	$output = `$pen_ctl 127.0.0.1:$fport timeout 2> /dev/null`;
	&logfile( "running '$pen_ctl 127.0.0.1:$fport timeout' for $fname farm $type" );

	return $output;
}

# set the lb algorithm to a farm
sub setTcpUdpFarmAlgorithm($alg,$fname)
{
	my ( $alg, $fname ) = @_;

	my $output      = -1;
	my $fport       = &getFarmPort( $fname );
	my $fmaxservers = &getFarmMaxServers( $fname );
	my @run         = `$pen_ctl 127.0.0.1:$fport no hash 2> /dev/null`;
	my @run         = `$pen_ctl 127.0.0.1:$fport no prio 2> /dev/null`;
	my @run         = `$pen_ctl 127.0.0.1:$fport no weight 2> /dev/null`;
	$output = $?;
	if ( $alg ne "roundrobin" )
	{
		&logfile( "running '$pen_ctl 127.0.0.1:$fport $alg'" );
		my @run = `$pen_ctl 127.0.0.1:$fport $alg 2> /dev/null`;
		$output = $?;
	}
	my @run = `$pen_ctl 127.0.0.1:$fport write '$configdir/$ffile'`;
	&setFarmMaxServers( $fmaxservers, $fname );

	return $output;
}

#
sub getTcpUdpFarmAlgorithm($ffile)
{
	my ( $ffile ) = @_;

	my $flb = "roundrobin";

	use File::Grep qw( fgrep fmap fdo );
	if ( fgrep { /^roundrobin/ } "$configdir/$ffile" )
	{
		$flb = "roundrobin";
	}
	if ( fgrep { /^hash/ } "$configdir/$ffile" )
	{
		$flb = "hash";
	}
	if ( fgrep { /^weight/ } "$configdir/$ffile" )
	{
		$flb = "weight";
	}
	if ( fgrep { /^prio/ } "$configdir/$ffile" )
	{
		$flb = "prio";
	}

	return $flb;
}

# set client persistence to a farm
sub setTcpUdpFarmPersistence($persistence,$fname,$type,$ffile)
{
	my ( $persistence, $fname, $type ) = @_;

	my $output = -1;

	&logfile( "setting 'Persistence $persistence' for $fname farm $type" );
	my $fport       = &getFarmPort( $fname );
	my $fmaxservers = &getFarmMaxServers( $fname );
	if ( $persistence eq "true" )
	{
		&logfile(
				"running '$pen_ctl 127.0.0.1:$fport no roundrobin' for $fname farm $type" );
		my @run = `$pen_ctl 127.0.0.1:$fport no roundrobin 2> /dev/null`;
		$output = $?;
	}
	else
	{
		&logfile(
				  "running '$pen_ctl 127.0.0.1:$fport roundrobin' for $fname farm $type" );
		my @run = `$pen_ctl 127.0.0.1:$fport roundrobin 2> /dev/null`;
		$output = $?;
	}
	my @run = `$pen_ctl 127.0.0.1:$fport write '$configdir/$ffile'`;
	&setFarmMaxServers( $fmaxservers, $fname );

	return $output;
}

#
sub getTcpUdpFarmPersistence($ffile)
{
	my ( $ffile ) = @_;

	my $output = "false";

	use File::Grep qw( fgrep fmap fdo );
	if ( fgrep { /^no\ roundrobin/ } "$configdir/$ffile" )
	{
		$output = "true";
	}

	return $output;
}

# set the max clients of a farm
sub setTcpUdpFarmMaxClientTime($maxcl,$track,$fname,$ffile)
{
	my ( $maxcl, $track, $fname, $ffile ) = @_;

	my $output      = -1;
	my $fport       = &getFarmPort( $fname );
	my $fmaxservers = &getFarmMaxServers( $fname );
	my @run         = `$pen_ctl 127.0.0.1:$fport tracking $track 2> /dev/null`;
	my @run         = `$pen_ctl 127.0.0.1:$fport write '$configdir/$ffile'`;

	use Tie::File;
	tie @array, 'Tie::File', "$configdir/$ffile";

	for ( @array )
	{
		if ( $_ =~ "# pen" )
		{
			s/-c [0-9]*/-c $maxcl/g;
			$output = $?;
		}
	}
	untie @array;
	&setFarmMaxServers( $fmaxservers, $fname );

	return $output;
}

#
sub getTcpUdpFarmMaxClientTime($fname)
{
	my ( $fname ) = @_;

	my @output;
	push ( @output, "" );
	push ( @output, "" );
	my $fport = &getFarmPort( $fname );
	&logfile( "running '$pen_ctl 127.0.0.1:$fport clients_max' " );
	@output[0] = `$pen_ctl 127.0.0.1:$fport clients_max 2> /dev/null`;
	@output[1] = `$pen_ctl 127.0.01:$fport tracking 2> /dev/null`;

	return $output;
}

# set the max conn of a farm
sub setTcpUdpFarmMaxConn($maxc,$ffile)
{
	my ( $maxc, $ffile ) = @_;

	my $output = -1;

	use Tie::File;
	tie @array, 'Tie::File', "$configdir/$ffile";
	for ( @array )
	{
		if ( $_ =~ "# pen" )
		{
			s/-x [0-9]*/-x $maxc/g;
			$output = $?;
		}
	}
	untie @array;

	return $output;
}

# Tcp/Udp only function
# set the max servers of a farm
sub setFarmMaxServers($maxs,$fname)
{
	my ( $maxs, $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;

	&logfile( "setting 'MaxServers $maxs' for $fname farm $type" );
	if ( $type eq "tcp" || $type eq "udp" )
	{
		use Tie::File;
		tie @array, 'Tie::File', "$configdir/$ffile";
		for ( @array )
		{
			if ( $_ =~ "# pen" )
			{
				if ( $_ !~ "-S " )
				{
					s/# pen/# pen -S $maxs/g;
					$output = $?;
				}
				else
				{
					s/-S [0-9]*/-S $maxs/g;
					$output = $?;
				}
			}
		}
		untie @array;
	}

	return $output;
}

# Tcp/Udp only function
sub getFarmMaxServers($fname)
{
	my ( $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $output = -1;

	if ( $type eq "tcp" || $type eq "udp" )
	{
		my $fport = &getFarmPort( $fname );
		&logfile( "running '$pen_ctl 127.0.0.1:$fport servers' " );
		my @out = `$pen_ctl 127.0.0.1:$fport servers 2> /dev/null`;
		$output = @out;
	}

	#&logfile("getting 'MaxServers $output' for $fname farm $type");
	return $output;
}

#
sub getTcpUdpFarmServers($fname)
{
	my ( $fname ) = @_;

	my @output;
	my $fport = &getFarmPort( $fname );

	&logfile( "running '$pen_ctl 127.0.0.1:$fport servers' " );

	@output = `$pen_ctl 127.0.0.1:$fport servers 2> /dev/null`;

	return @output;
}

# Tcp/Udp only function
# set xforwarder for feature for a farm
sub setFarmXForwFor($isset,$fname)
{
	my ( $isset, $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;

	&logfile( "setting 'XForwFor $isset' for $fname farm $type" );
	if ( $type eq "tcp" || $type eq "udp" )
	{
		my $fport       = &getFarmPort( $fname );
		my $fmaxservers = &getFarmMaxServers( $fname );
		if ( $isset eq "true" )
		{
			&logfile( "running '$pen_ctl 127.0.0.1:$fport http'" );
			my @run = `$pen_ctl 127.0.0.1:$fport http 2> /dev/null`;
			$output = $?;
		}
		else
		{
			&logfile( "running '$pen_ctl 127.0.0.1:$fport no http'" );
			my @run = `$pen_ctl 127.0.0.1:$fport no http 2> /dev/null`;
			$output = $?;
		}

		if ( $output != -1 )
		{
			my @run = `$pen_ctl 127.0.0.1:$fport write '$configdir/$ffile'`;
			&logfile( "configuration saved in $configdir/$ffile file" );
			&setFarmMaxServers( $fmaxservers, $fname );
		}
	}

	return $output;
}

# Tcp/Udp only function
sub getFarmXForwFor($fname)
{
	my ( $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;

	if ( $type eq "tcp" || $type eq "udp" )
	{
		use Tie::File;
		tie @array, 'Tie::File', "$configdir/$ffile";
		$output = "false";
		if ( grep ( /^http/, @array ) )
		{
			$output = "true";
		}
		untie @array;
	}

	#&logfile("getting 'XForwFor $output' for $fname farm $type");
	return $output;
}

#
sub getTcpUdpFarmGlobalStatus($fname)
{
	my ( $fname ) = @_;

	my @run;
	my $port = &getFarmPort( $fname );
	@run = `$pen_ctl 127.0.0.1:$port status`;

	return @run;
}

#
sub getTcpFarmEstConns(@nets,@netstat,$fvip,$fvipp)
{
	my ( @nets, @netstat, $fvip, $fvipp ) = @_;

	push (
		   @nets,
		   &getNetstatFilter(
					   "tcp", "",
					   "\.* ESTABLISHED src=\.* dst=$fvip sport=\.* dport=$fvipp .*src=\.*",
					   "", @netstat
		   )
	);

	return @nets;
}

#
sub getUdpFarmEstConns(@nets,@netstat,$fvip,$fvipp)
{
	my ( @nets, @netstat, $fvip, $fvipp ) = @_;

	push (
		   @nets,
		   &getNetstatFilter(
							  "udp", "",
							  "\.* src=\.* dst=$fvip sport=\.* dport=$fvipp .*src=\.*",
							  "", @netstat
		   )
	);

	return @nets;
}

sub getTcpBackendSYNConns($ip_backend,$port_backend,@netstat)
{
	my ( @nets, $ip_backend, $port_backend, @netstat ) = @_;

	return
	  &getNetstatFilter( "tcp", "",
				"\.*SYN\.* src=\.* dst=$ip_backend sport=\.* dport=$port_backend\.*",
				"", @netstat );
}

sub getUdpBackendSYNConns($ip_backend,$port_backend,@netstat)
{
	my ( @nets, $ip_backend, $port_backend, @netstat ) = @_;

	return
	  &getNetstatFilter( "udp", "",
		"\.* src=\.* dst=$ip_backend \.* dport=$port_backend \.*UNREPLIED\.* src=\.*",
		"", @netstat );
}

#
sub getTcpFarmSYNConns(@netstat,$fvip,$fvipp)
{
	my ( @netstat, $fvip, $fvipp ) = @_;
	my @nets = ();

	push (
		   @nets,
		   &getNetstatFilter(
						   "tcp", "",
						   "\.*SYN\.* src=\.* dst=$fvip sport=\.* dport=$fvipp \.* src=\.*",
						   "", @netstat
		   )
	);

	return @nets;
}
#
sub getUdpFarmSYNConns(@netstat,$fvip,$fvipp)
{
	my ( @netstat, $fvip, $fvipp ) = @_;
	my @nets = ();

	push (
		   @nets,
		   &getNetstatFilter(
						   "udp", "",
						   "\.* src=\.* dst=$fvip \.* dport=$fvipp \.*UNREPLIED\.* src=\.*",
						   "", @netstat
		   )
	);

	return @nets;
}

# Start Farm rutine
sub _runTcpUdpFarmStart($fname)
{
	my ( $fname ) = @_;
	my $status = -1;

	my $run_farm = &getFarmCommand( $fname );
	&logfile( "running $pen_bin $run_farm" );
	zsystem( "$pen_bin $run_farm" );
	$status = $?;

	return $status;
}

# Stop Farm rutine
sub _runTcpUdpFarmStop($fname)
{
	my ( $fname ) = @_;

	my $pid = &getFarmPid( $fname );

	&logfile( "running 'kill 15, $pid'" );
	kill 15, $pid;

	return $?;
}

#
sub runTcpFarmCreate($fvip,$fvipp,$fname)
{
	my ( $fvip, $fvipp, $fname ) = @_;

	my $output = -1;
	my $fport  = &setFarmPort();

	# execute pen command
	my $pen_command =
	  "$pen_bin $fvip:$fvipp -c 2049 -x 257 -S 10 -C 127.0.0.1:$fport";
	&logfile( "running '$pen_command'" );
	my @run = `$pen_command`;
	$output = $?;

	# execute pen_ctl command
	my $pen_ctl_command = "$pen_ctl 127.0.0.1:$fport acl 9 deny 0.0.0.0 0.0.0.0";
	&logfile( "running '$pen_ctl_command" );
	my @run = `$pen_ctl_command`;

	# write configuration file
	$pen_ctl_command =
	  "$pen_ctl 127.0.0.1:$fport write '$configdir/$fname\_pen.cfg'";
	&logfile( "running $pen_ctl_command" );
	my @run = `$pen_ctl_command`;

	return $output;
}

#
sub runUdpFarmCreate($fvip,$fvipp,$fname)
{
	my ( $fvip, $fvipp, $fname ) = @_;

	my $output = -1;
	my $fport  = &setFarmPort();

	# execute pen command
	my $pen_command =
	  "$pen_bin $fvip:$fvipp -U -t 1 -b 3 -c 2049 -x 257 -S 10 -C 127.0.0.1:$fport";
	&logfile( "running '$pen_command'" );
	my @run = `$pen_command`;
	$output = $?;

	# execute pen_ctl command
	my $pen_ctl_command = "$pen_ctl 127.0.0.1:$fport acl 9 deny 0.0.0.0 0.0.0.0";
	&logfile( "running '$pen_ctl_command" );
	my @run = `$pen_ctl_command`;

	# write configuration file
	$pen_ctl_command =
	  "$pen_ctl 127.0.0.1:$fport write '$configdir/$fname\_pen\_udp.cfg'";
	&logfile( "running $pen_ctl_command" );
	my @run = `$pen_ctl_command`;

	return $output;
}

# Returns Farm blacklist
sub getFarmBlacklist($fname)
{
	my ( $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $file   = &getFarmFile( $fname );
	my $output = -1;

	if ( $type eq "tcp" || $type eq "udp" )
	{
		open FI, "$configdir/$file";
		my $exit = "false";
		while ( $line = <FI> || $exit eq "false" )
		{
			if ( $line =~ /^# pen/ )
			{
				$exit = "true";
				my @line_a = split ( "\ ", $line );
				if ( $type eq "tcp" )
				{
					$admin_ip = @line_a[11];
				}
				else
				{
					$admin_ip = @line_a[12];
				}
				my @blacklist = `$pen_ctl $admin_ip blacklist 2> /dev/null`;
				if   ( @blacklist =~ /^[1-9].*/ ) { $output = "@blacklist"; }
				else                              { $output = "-"; }
			}
		}
		close FI;
	}

	return $output;
}

# Returns farm max connections
sub getTcpUdpFarmMaxConn($file,$type)
{
	my ( $file, $type ) = @_;

	my $output = -1;

	open FI, "$configdir/$file";
	my $exit = "false";
	while ( $line = <FI> || $exit eq "false" )
	{
		if ( $line =~ /^# pen/ )
		{
			$exit = "true";
			my @line_a = split ( "\ ", $line );
			if ( $type eq "tcp" )
			{
				$admin_ip = @line_a[11];
			}
			else
			{
				$admin_ip = @line_a[12];
			}
			my @conn_max = `$pen_ctl $admin_ip conn_max 2> /dev/null`;
			if ( @conn_max =~ /^[1-9].*/ )
			{
				$output = "@conn_max";
			}
			else
			{
				$output = "-";
			}
		}
	}
	close FI;

	return $output;
}

# Returns farm listen port
sub getTcpUdpFarmPort($file)
{
	my ( $file ) = @_;

	my $output = -1;

	open FI, "$configdir/$file";
	my $exit = "false";
	while ( my $line = <FI> || $exit eq "false" )
	{
		if ( $line =~ /^# pen/ )
		{
			$exit = "true";
			my @line_a = split ( "\ ", $line );
			if ( $type eq "tcp" )
			{
				$port_manage = @line_a[11];
			}
			else
			{
				$port_manage = @line_a[12];
			}
			my @managep = split ( ":", $port_manage );
			$output = @managep[1];
		}
	}
	close FI;

	return $output;
}

# Only used by tcpudp_func
# Returns farm command
sub getFarmCommand($fname)
{
	my ( $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $file   = &getFarmFile( $fname );
	my $output = -1;

	if ( $type eq "tcp" || $type eq "udp" )
	{
		open FI, "$configdir/$file";
		my $exit = "false";
		while ( $line = <FI> || $exit eq "false" )
		{
			if ( $line =~ /^# pen/ )
			{
				$exit = "true";
				$line =~ s/^#\ pen//;
				$output = $line;
			}
		}
		close FI;
	}

	return $output;
}

# Returns farm PID
sub getTcpUdpFarmPid($file)
{
	my ( $file ) = @_;

	my $output = -1;

	open FI, "$configdir/$file";
	my $exit = "false";
	while ( my $line = <FI> || $exit eq "false" )
	{
		if ( $line =~ /^# pen/ )
		{
			$exit = "true";
			my @line_a = split ( "\ ", $line );
			@ip_and_port = split ( ":", @line_a[-2] );
			$admin_ip = "@ip_and_port[0]:@ip_and_port[1]";
			my @pid = `$pen_ctl $admin_ip pid 2> /dev/null`;

			if ( @pid =~ /^[1-9].*/ )
			{
				$output = "@pid";
			}
			else
			{
				$output = "-";
			}
		}
	}
	close FI;

	return $output;
}

# Returns farm vip
sub getTcpUdpFarmVip($info,$file)
{
	my ( $info, $file ) = @_;

	my $output = -1;

	open FI, "$configdir/$file";
	my $exit = "false";
	while ( my $line = <FI> || $exit eq "false" )
	{

		# find line with pen command
		if ( $line =~ /^# pen/ )
		{
			$exit = "true";
			my @line_a = split ( "\ ", $line );

			# use last argument
			$vip_port = @line_a[-1];
			my @vipp = split ( ":", $vip_port );
			if ( $info eq "vip" )   { $output = @vipp[0]; }
			if ( $info eq "vipp" )  { $output = @vipp[1]; }
			if ( $info eq "vipps" ) { $output = "$vip_port"; }
		}
	}
	close FI;

	return $output;
}

# Set farm virtual IP and virtual PORT
sub setTcpUdpFarmVirtualConf($vip,$vipp,$fname,$fconf)
{
	my ( $vip, $vipp, $fname, $fconf ) = @_;

	my $stat = -1;
	my $vips = &getFarmVip( "vipps", $fname );

	use Tie::File;
	tie @filelines, 'Tie::File', "$configdir\/$fconf";

	for ( @filelines )
	{
		if ( $_ =~ "# pen" )
		{
			s/$vips/$vip:$vipp/g;
			$stat = $?;
		}
	}
	untie @filelines;

	return $stat;
}

#
sub setTcpUdpFarmServer($ids,$rip,$port,$max,$weight,$priority,$fname,$file)
{
	my ( $ids, $rip, $port, $max, $weight, $priority, $fname, $file ) = @_;

	my $output      = -1;
	my $fport       = &getFarmPort( $fname );
	my $fmaxservers = &getFarmMaxServers( $fname );

	if ( $max ne "" )      { $max      = "max $max"; }
	if ( $weight ne "" )   { $weight   = "weight $weight"; }
	if ( $priority ne "" ) { $priority = "prio $priority"; }

	# pen setup server
	my $pen_ctl_command =
	  "$pen_ctl 127.0.0.1:$fport server $ids address $rip port $port $max $weight $priority";
	&logfile( "running '$pen_ctl_command' in $fname farm" );
	my @run = `$pen_ctl_command`;
	$output = $?;

	# pen write configuration file
	my $pen_write_config_command =
	  "$pen_ctl 127.0.0.1:$fport write '$configdir/$file'";
	&logfile( "running '$pen_write_config_command'" );
	my @run = `$pen_write_config_command`;

	&setFarmMaxServers( $fmaxservers, $fname );

	return $output;
}

#
sub runTcpUdpFarmServerDelete($ids,$fname,$ffile)
{
	my ( $ids, $fname, $ffile ) = @_;

	my $output = -1;

	my $fport       = &getFarmPort( $fname );
	my $fmaxservers = &getFarmMaxServers( $fname );

	my $pen_ctl_command =
	  "$pen_ctl 127.0.0.1:$fport server $ids address 0 port 0 max 0 weight 0 prio 0' deleting server $ids in $fname farm";

	&logfile( "running '$pen_ctl_command' deleting server $ids in $fname farm" );
	my @run = `$pen_ctl_command`;
	$output = $?;

	my $pen_write_config_command =
	  "$pen_ctl 127.0.0.1:$fport write '$configdir/$ffile'";
	&logfile( "running '$pen_write_config_command'" );
	my @run = `$pen_write_config_command`;

	&setFarmMaxServers( $fmaxservers, $fname );

	return $output;
}

#
sub getTcpUdpFarmBackendStatusCtl($fname)
{
	my ( $fname ) = @_;

	my @output = -1;

	my $mport = &getFarmPort( $fname );
	@output = `$pen_ctl 127.0.0.1:$mport status`;

	return @output;
}

#function that return the status information of a farm:
#ip, port, backendstatus, weight, priority, clients
sub getTcpUdpFarmBackendsStatus($fname,@content)
{
	my ( $fname, @content ) = @_;

	my @output = -1;

	if ( !@content )
	{
		@content = &getFarmBackendStatusCtl( $fname );
	}

	foreach ( @content )
	{
		$i++;
		if ( $_ =~ /\<tr\>/ )
		{
			$trc++;
		}
		if ( $_ =~ /Time/ )
		{
			$_ =~ s/\<p\>//;
			my @value_backend = split ( ",", $_ );
		}
		if ( $trc >= 2 && $_ =~ /\<tr\>/ )
		{
			#backend ID
			@content[$i] =~ s/\<td\>//;
			@content[$i] =~ s/\<\/td\>//;
			@content[$i] =~ s/\n//;
			my $id_backend = @content[$i];
			$line = $id_backend;

			#backend IP,PORT
			@content[$i + 1] =~ s/\<td\>//;
			@content[$i + 1] =~ s/\<\/td\>//;
			@content[$i + 1] =~ s/\n//;
			my $ip_backend = @content[$i + 1];
			$line = $line . "\t" . $ip_backend;

			#
			@content[$i + 3] =~ s/\<td\>//;
			@content[$i + 3] =~ s/\<\/td\>//;
			@content[$i + 3] =~ s/\n//;
			my $port_backend = @content[$i + 3];
			$line = $line . "\t" . $port_backend;

			#status
			@content[$i + 2] =~ s/\<td\>//;
			@content[$i + 2] =~ s/\<\/td\>//;
			@content[$i + 2] =~ s/\n//;
			my $status_maintenance = &getFarmBackendMaintenance( $fname, $id_backend );
			my $status_backend = @content[$i + 2];
			if ( $status_maintenance eq "0" )
			{
				$status_backend = "MAINTENANCE";
			}
			elsif ( $status_backend eq "0" )
			{
				$status_backend = "UP";
			}
			else
			{
				$status_backend = "DEAD";
			}
			$line = $line . "\t" . $status_backend;

			#weight
			@content[$i + 9] =~ s/\<td\>//;
			@content[$i + 9] =~ s/\<\/td\>//;
			@content[$i + 9] =~ s/\n//;
			my $w_backend = @content[$i + 9];
			$line = $line . "\t" . $w_backend;

			#priority
			@content[$i + 10] =~ s/\<td\>//;
			@content[$i + 10] =~ s/\<\/td\>//;
			@content[$i + 10] =~ s/\n//;
			my $p_backend = @content[$i + 10];
			$line = $line . "\t" . $p_backend;

			#sessions
			if ( $ip_backend ne "0\.0\.0\.0" )
			{
				my $clients = &getFarmBackendsClients( $id_backend, @content, $fname );
				if ( $clients != -1 )
				{
					$line = $line . "\t" . $clients;
				}
				else
				{
					$line = $line . "\t-";
				}
			}

			#end
			push ( @b_data, $line );
		}
		if ( $_ =~ /\/table/ )
		{
			last;
		}
	}
	@output = @b_data;

	return @output;
}

#function that return the status information of a farm:
sub getTcpUdpFarmBackendsClients($idserver,@content,$fname)
{
	my ( $idserver, @content, $fname ) = @_;

	my $output = -1;

	if ( !@content )
	{
		@content = &getFarmBackendStatusCtl( $fname );
	}
	if ( !@sessions )
	{
		@sessions = &getFarmBackendsClientsList( $fname, @content );
	}
	my $numclients = 0;
	foreach ( @sessions )
	{
		my @ses_client = split ( "\t", $_ );
		chomp ( @ses_client[3] );
		chomp ( $idserver );
		if ( @ses_client[3] eq $idserver )
		{
			$numclients++;
		}
	}
	$output = $numclients;

	return $output;
}

#function that return the status information of a farm:
sub getFarmBackendsClientsList($fname,@content)
{
	my ( $fname, @content ) = @_;

	my @output = -1;

	if ( !@content )
	{
		@content = &getFarmBackendStatusCtl( $fname );
	}

	my $line;
	my @sess;
	my @s_data;
	my $ac_header = 0;
	my $tr        = 0;
	my $i         = -1;

	foreach ( @content )
	{
		$i++;
		if ( $_ =~ /Active clients/ )
		{
			$ac_header = 1;
			@value_session = split ( "\<\/h2\>", $_ );
			@value_session[1] =~ s/\<p\>\<table bgcolor\=\"#c0c0c0\">//;
			$line = @value_session[1];
			push ( @s_data, "Client sessions status\t$line" );
		}
		if ( $ac_header == 1 && $_ =~ /\<tr\>/ )
		{
			$tr++;
		}
		if ( $tr >= 2 && $_ =~ /\<tr\>/ )
		{
			@content[$i + 1] =~ s/\<td\>//;
			@content[$i + 1] =~ s/\<\/td\>//;
			chomp ( @content[$i + 1] );
			$line = @content[$i + 1];

			#
			@content[$i + 2] =~ s/\<td\>//;
			@content[$i + 2] =~ s/\<\/td\>//;
			chomp ( @content[$i + 2] );

			#
			$line = $line . "\t" . @content[$i + 2];
			@content[$i + 3] =~ s/\<td\>//;
			@content[$i + 3] =~ s/\<\/td\>//;
			chomp ( @content[$i + 3] );

			#
			$line = $line . "\t" . @content[$i + 3];
			@content[$i + 4] =~ s/\<td\>//;
			@content[$i + 4] =~ s/\<\/td\>//;

			#
			$line = $line . "\t" . @content[$i + 4];
			@content[$i + 5] =~ s/\<td\>//;
			@content[$i + 5] =~ s/\<\/td\>//;

			#
			$line = $line . "\t" . @content[$i + 5];
			@content[$i + 6] =~ s/\<td\>//;
			@content[$i + 6] =~ s/\<\/td\>//;
			@content[$i + 6] = @content[$i + 6] / 1024 / 1024;
			@content[$i + 6] = sprintf ( '%.2f', @content[$i + 6] );

			#
			$line = $line . "\t" . @content[$i + 6];
			@content[$i + 7] =~ s/\<td\>//;
			@content[$i + 7] =~ s/\<\/td\>//;
			@content[$i + 7] = @content[$i + 7] / 1024 / 1024;
			@content[$i + 7] = sprintf ( '%.2f', @content[$i + 7] );

			#
			$line = $line . "\t" . @content[$i + 7];
			push ( @s_data, $line );
		}
		if ( $ac_header == 1 && $_ =~ /\<\/table\>/ )
		{
			last;
		}
	}
	@output = @s_data;

	return @output;
}

# Only used for tcp/udp
sub getFarmBackendsClientsActives($fname,@content)
{
	my ( $fname, @content ) = @_;

	my $type   = &getFarmType( $fname );
	my @output = -1;

	if ( $type eq "tcp" || $type eq "udp" )
	{
		if ( !@content )
		{
			@content = &getFarmBackendStatusCtl( $fname );
		}

		my $line;
		my @sess;
		my @s_data;
		my $ac_header = 0;
		my $tr        = 0;
		my $i         = -1;

		foreach ( @content )
		{
			$i++;
			if ( $_ =~ /Active connections/ )
			{
				$ac_header = 1;
				my @value_conns = split ( "\<\/h2\>", $_ );
				@value_conns[1] =~ s/\<p\>\<table bgcolor\=\"#c0c0c0\"\>//;
				@value_conns[1] =~ s/Number of connections\://;
				$line = "Active connections\t@value_conns[1]";
				push ( @s_data, $line );
			}
			if ( $ac_header == 1 && $_ =~ /\<tr\>/ )
			{
				$tr++;
			}
			if ( $tr >= 2 && $_ =~ /\<tr\>/ )
			{
				@content[$i + 1] =~ s/\<td\>//;
				@content[$i + 1] =~ s/\<\/td\>//;
				chomp ( @content[$i + 1] );
				$line = @content[$i + 1];

				#
				@content[$i + 6] =~ s/\<td\>//;
				@content[$i + 6] =~ s/\<\/td\>//;
				$line = $line . "\t" . @content[$i + 6];

				#
				@content[$i + 7] =~ s/\<td\>//;
				@content[$i + 7] =~ s/\<\/td\>//;
				$line = $line . "\t" . @content[$i + 7];

				push ( @s_data, $line );
			}
			if ( $ac_header == 1 && $_ =~ /\<\/table\>/ )
			{
				last;
			}

		}
		@output = @s_data;
	}

	return @output;
}

#function that renames a farm
sub setTcpUdpNewFarmName($fname,$newfname)
{
	my ( $fname, $newfname ) = @_;
	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;

	my $newffile = "$newfname\_pen.cfg";
	if ( $type eq "udp" )
	{
		$newffile = "$newfname\_pen\_udp.cfg";
	}
	my $gfile = "$fname\_guardian.conf";
	use Tie::File;
	tie @filelines, 'Tie::File', "$configdir\/$ffile";
	for ( @filelines )
	{
		s/$fname/$newfname/g;
	}
	untie @filelines;

	rename ( "$configdir\/$ffile", "$configdir\/$newffile" );
	$output = $?;
	&logfile( "configuration saved in $configdir/$newffile file" );
	if ( -e "$configdir\/$gfile" )
	{
		my $newgfile = "$newfname\_guardian.conf";
		use Tie::File;
		tie @filelines, 'Tie::File', "$configdir\/$gfile";
		for ( @filelines )
		{
			s/$fname/$newfname/g;
		}
		untie @filelines;
		rename ( "$configdir\/$gfile", "$configdir\/$newgfile" );
		$output = $?;
		&logfile( "configuration saved in $configdir/$newgfile file" );
	}

	return $output;
}

#function that check if a backend on a farm is on maintenance mode
sub getTcpUdpFarmBackendMaintenance($fname,$backend)
{
	my ( $fname, $backend ) = @_;
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;

	open FR, "<$configdir\/$ffile";
	my @content = <FR>;
	foreach $line ( @content )
	{
		if ( $line =~ /^server $backend acl 9/ )
		{
			$output = 0;
		}
		close FR;
	}

	return $output;
}

#function that enable the maintenance mode for backend
sub setTcpUdpFarmBackendMaintenance($fname,$backend)
{
	my ( $fname, $backend ) = @_;
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;

	&logfile( "setting Maintenance mode for $fname backend $backend" );

	my $fport       = &getFarmPort( $fname );
	my $fmaxservers = &getFarmMaxServers( $fname );

	&logfile( "running '$pen_ctl 127.0.0.1:$fport server $id_server acl 9'" );

	my @run = `$pen_ctl 127.0.0.1:$fport server $id_server acl 9  2> /dev/null`;
	$output = $?;

	&logfile( "running '$pen_ctl 127.0.0.1:$fport write '$configdir/$ffile'" );
	my @run = `$pen_ctl 127.0.0.1:$fport write '$configdir/$ffile'`;

	&setFarmMaxServers( $fmaxservers, $fname );

	return $output;
}

#function that disable the maintenance mode for backend
sub setTcpUdpFarmBackendNoMaintenance($fname,$backend)
{
	my ( $fname, $backend ) = @_;
	my $ffile = &getFarmFile( $fname );
	$output = -1;

	&logfile( "setting Disabled maintenance mode for $fname backend $backend" );

	my $fport       = &getFarmPort( $fname );
	my $fmaxservers = &getFarmMaxServers( $fname );

	&logfile( "running '$pen_ctl 127.0.0.1:$fport server $id_server acl 0'" );

	my @run = `$pen_ctl 127.0.0.1:$fport server $id_server acl 0  2> /dev/null`;
	$output = $?;
	&logfile( "running '$pen_ctl 127.0.0.1:$fport write '$configdir/$ffile'" );

	my @run = `$pen_ctl 127.0.0.1:$fport write '$configdir/$ffile'`;

	&setFarmMaxServers( $fmaxservers, $fname );

	return $output;
}

# do not remove this
1
