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

if ( -e "/usr/local/zenloadbalancer/www/farms_functions_ext.cgi" )
{
	require "/usr/local/zenloadbalancer/www/farms_functions_ext.cgi";
}

#asign a port for manage a pen Farm
sub setFarmPort()
{
	#down limit
	$inf = "10000";

	#up limit
	$sup = "20000";

	$lock = "true";
	do
	{
		$randport = int ( rand ( $sup - $inf ) ) + $inf;
		use IO::Socket;
		my $host = "127.0.0.1";
		my $sock = new IO::Socket::INET(
										 PeerAddr => $host,
										 PeerPort => $randport,
										 Proto    => 'tcp'
		);
		if ( $sock )
		{
			close ( $sock );
		}
		else
		{
			$lock = "false";
		}
	} while ( $lock eq "true" );

	return $randport;
}

#
sub setFarmBlacklistTime($fbltime,$fname)
{
	my ( $fbltime, $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;

	if ( $type eq "tcp" || $type eq "udp" )
	{
		$output = &setTcpUdpFarmBlacklistTime( $fbltime, $fname, $type, $ffile );
	}

	if ( $type eq "http" || $type eq "https" )
	{
		$output = &setHTTPFarmBlacklistTime( $fbltime, $fname, $ffile );
	}

	return $output;
}

#
sub getFarmBlacklistTime($fname)
{
	my ( $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;

	if ( $type eq "tcp" || $type eq "udp" )
	{
		$output = &getTcpUdpFarmBlacklistTime( $fname );
	}

	if ( $type eq "http" || $type eq "https" )
	{
		$output = &getHTTPFarmBlacklistTime( $ffile );
	}

	return $output;
}

#
sub setFarmSessionType($session,$fname)
{
	my ( $session, $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;

	if ( $type eq "http" || $type eq "https" )
	{
		$output = &setHTTPFarmSessionType( $session, $ffile );
	}

	if ( $type eq "l4xnat" )
	{
		$output = &setL4FarmSessionType( $session, $ffile );
	}
	return $output;
}

#
sub getFarmSessionType($fname)
{
	my ( $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;

	if ( $type eq "http" || $type eq "https" )
	{
		$output = &getHTTPFarmSessionType( $fname );
	}

	if ( $type eq "l4xnat" )
	{
		$output = &getL4FarmSessionType( $ffile );
	}

	return $output;
}

#asign a timeout value to a farm
sub setFarmTimeout($timeout,$fname)
{
	my ( $timeout, $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;

	&logfile( "setting 'Timeout $timeout' for $fname farm $type" );

	if ( $type eq "tcp" || $type eq "udp" )
	{
		$output = &setTcpUdpFarmTimeout( $timeout, $fname );
	}

	if ( $type eq "http" || $type eq "https" )
	{
		$output = &setHTTPFarmTimeout( $timeout, $ffile );
	}

	return $output;
}

#
sub getFarmTimeout($fname)
{
	my ( $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;

	if ( $type eq "tcp" || $type eq "udp" )
	{
		$output = &getTcpUdpFarmTimeout( $fname );
	}

	if ( $type eq "http" || $type eq "https" )
	{
		$output = &getHTTPFarmTimeout( $ffile );
	}

	return $output;
}

# set the lb algorithm to a farm
sub setFarmAlgorithm($alg,$fname)
{
	my ( $alg, $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;

	&logfile( "setting 'Algorithm $alg' for $fname farm $type" );

	if ( $type eq "tcp" || $type eq "udp" )
	{
		$output = &setTcpUdpFarmAlgorithm( $alg, $fname );
	}

	if ( $type eq "datalink" )
	{
		$output = &setDatalinkFarmAlgorithm( $alg, $ffile );
	}

	if ( $type eq "l4xnat" )
	{
		$output = &setL4FarmAlgorithm( $alg, $ffile );
	}

	return $output;
}

#
sub getFarmAlgorithm($fname)
{
	my ( $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;

	if ( $type eq "tcp" || $type eq "udp" )
	{
		$output = &getTcpUdpFarmAlgorithm( $ffile );
	}

	if ( $type eq "datalink" )
	{
		$output = &getDatalinkFarmAlgorithm( $fname );
	}

	if ( $type eq "l4xnat" )
	{
		$output = &getL4FarmAlgorithm( $ffile );
	}

	return $output;
}

# set client persistence to a farm
sub setFarmPersistence($persistence,$fname)
{
	my ( $persistence, $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;

	if ( $type eq "tcp" || $type eq "udp" )
	{
		$output = &setTcpUdpFarmPersistence( $persistence, $fname, $type );
	}

	if ( $type eq "l4xnat" )
	{
		$output = &setL4FarmPersistence( $persistence, $ffile );
	}

	return $output;
}

#
sub getFarmPersistence($fname)
{
	my ( $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;

	if ( $type eq "tcp" || $type eq "udp" )
	{
		$output = &getTcpUdpFarmPersistence( $ffile );
	}

	if ( $type eq "l4xnat" )
	{
		$output = &getL4FarmPersistence( $ffile );
	}

	return $output;
}

# set the max clients of a farm
sub setFarmMaxClientTime($maxcl,$track,$fname)
{
	my ( $maxcl, $track, $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;

	&logfile( "setting 'MaxClientTime $maxcl $track' for $fname farm $type" );
	if ( $type eq "tcp" || $type eq "udp" )
	{
		$output = &setTcpUdpFarmMaxClientTime( $maxcl, $track, $fname, $ffile );
	}

	if ( $type eq "http" || $type eq "https" )
	{
		$output = &setHTTPFarmMaxClientTime( $track, $ffile );
	}

	if ( $type eq "l4xnat" )
	{
		$output = &setL4FarmMaxClientTime( $track, $ffile );
	}

	return $output;
}

#
sub getFarmMaxClientTime($fname)
{
	my ( $fname ) = @_;

	my $type = &getFarmType( $fname );
	my @output;

	if ( $type eq "tcp" || $type eq "udp" )
	{
		$output = &getTcpUdpFarmMaxClientTime( $fname );
	}

	if ( $type eq "http" || $type eq "https" )
	{
		$output = &getHTTPFarmMaxClientTime( $fname );
	}

	if ( $type eq "l4xnat" )
	{
		@output = &getL4FarmMaxClientTime( $ffile );
	}

	return @output;
}

# set the max conn of a farm
sub setFarmMaxConn($maxc,$fname)
{
	my ( $maxc, $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;

	&logfile( "setting 'MaxConn $maxc' for $fname farm $type" );
	if ( $type eq "tcp" || $type eq "udp" )
	{
		$output = &setTcpUdpFarmMaxConn( $maxc, $ffile );
	}

	if ( $type eq "http" || $type eq "https" )
	{
		$output = &setHTTPFarmMaxConn( $maxc, $ffile );
	}

	return $output;
}

#
sub getFarmServers($fname)
{
	my ( $fname ) = @_;

	my $type = &getFarmType( $fname );
	my @output;

	if ( $type eq "tcp" || $type eq "udp" )
	{
		@output = &getTcpUdpFarmServers( $fname );
	}

	if ( $type eq "datalink" || $type eq "l4xnat" )
	{
		my $file = &getFarmFile( $fname );
		open FI, "<$configdir/$file";
		my $first  = "true";
		my $sindex = 0;
		while ( $line = <FI> )
		{
			if ( $line ne "" && $line =~ /^\;server\;/ && $first ne "true" )
			{
				#print "$line<br>";
				$line =~ s/^\;server/$sindex/g, $line;
				push ( @output, $line );
				$sindex = $sindex + 1;
			}
			else
			{
				$first = "false";
			}
		}
		close FI;
	}

	#&logfile("getting 'Servers @output' for $fname farm $type");
	return @output;
}

#
sub getFarmGlobalStatus($fname)
{
	my ( $fname ) = @_;

	my $type = &getFarmType( $fname );
	my @run;

	if ( $type eq "tcp" || $type eq "udp" )
	{
		@run = &getTcpUdpFarmGlobalStatus( $fname );
	}

	if ( $type eq "http" || $type eq "https" )
	{
		@run = getHTTPFarmGlobalStatus( $fname );
	}

	return @run;
}

sub getBackendEstConns($fname,$ip_backend,$port_backend,@netstat)
{
	my ( $fname, $ip_backend, $port_backend, @netstat ) = @_;
	my $type  = &getFarmType( $fname );
	my $fvip  = &getFarmVip( "vip", $fname );
	my $fvipp = &getFarmVip( "vipp", $fname );
	my @nets  = ();
	if ( $type eq "tcp" || $type eq "udp" || $type =~ "http" )
	{
		if ( $type =~ "http" )
		{
			$type = "tcp";
		}
		@nets = &getNetstatFilter(
			"$type",
			"",
			"\.*ESTABLISHED src=\.* dst=$ip_backend sport=\.* dport=$port_backend \.*src=$ip_backend \.*",
			"",
			@netstat
		);
	}
	if ( $type eq "l4xnat" )
	{
		@nets = &getL4BackendEstConns( $fname, $ip_backend, @netstat );
	}
	return @nets;
}

#
sub getFarmEstConns($fname,@netstat)
{
	my ( $fname, @netstat ) = @_;

	my $type  = &getFarmType( $fname );
	my $fvip  = &getFarmVip( "vip", $fname );
	my $fvipp = &getFarmVip( "vipp", $fname );
	my $pid   = &getFarmPid( $fname );
	my @nets  = ();

	if ( $pid eq "-" )
	{
		return @nets;
	}

	if ( $type eq "tcp" )
	{
		@nets = &getTcpFarmEstConns( @nets, @netstat, $fvip, $fvipp );
	}

	if ( $type eq "udp" )
	{
		@nets = &getUdpFarmEstConns( @nets, @netstat, $fvip, $fvipp );
	}

	if ( $type eq "http" || $type eq "https" )
	{
		@nets = &getHTTPFarmEstConns( @nets, @netstat, $fvip, $fvipp );
	}

	if ( $type eq "l4xnat" )
	{
		@nets = &getL4FarmEstConns( $fname, @netstat );
	}

	return @nets;
}

sub getBackendTWConns($fname,$ip_backend,$port_backend,@netstat)
{
	my ( $fname, $ip_backend, $port_backend, @netstat ) = @_;

	my $type  = &getFarmType( $fname );
	my $fvip  = &getFarmVip( "vip", $fname );
	my $fvipp = &getFarmVip( "vipp", $fname );
	my @nets  = ();

	if ( $type eq "tcp" || $type eq "udp" || $type eq "http" )
	{
		if ( $type eq "http" )
		{
			$type = "tcp";
		}
		@nets =
		  &getNetstatFilter( "$type", "",
			 "\.*TIME\_WAIT src=$fvip dst=$ip_backend sport=\.* dport=$port_backend \.*",
			 "", @netstat );
	}
	if ( $type eq "l4xnat" )
	{
		@nets = &getL4BackendTWConns( $fname, $ip_backend, @netstat );
	}

	return @nets;
}

#
sub getFarmTWConns($fname,@netstat)
{
	my ( $fname, @netstat ) = @_;

	my $type  = &getFarmType( $fname );
	my $fvip  = &getFarmVip( "vip", $fname );
	my $fvipp = &getFarmVip( "vipp", $fname );
	my @nets  = ();

	#&logfile("getting 'TWConns' for $fname farm $type");
	if ( $type eq "tcp" || $type eq "http" || $type eq "https" )
	{
		push (
			   @nets,
			   &getNetstatFilter(
								 "tcp", "",
								 "\.*\_WAIT src=\.* dst=$fvip sport=\.* dport=$fvipp .*src=\.*",
								 "", @netstat
			   )
		);
	}

	if ( $type eq "udp" )
	{
		@nets = &getNetstatFilter( "udp", "\.\*\_WAIT\.\*", $ninfo, "", @netstat );
	}

	if ( $type eq "l4xnat" )
	{
		@nets = &getL4FarmTWConns( $fname, @netstat );
	}

	return @nets;
}

sub getBackendSYNConns($fname,$ip_backend,$port_backend,@netstat)
{
	my ( $fname, $ip_backend, $port_backend, @netstat ) = @_;

	my $type = &getFarmType( $fname );
	my @nets = ();

	if ( $type eq "tcp" || $type eq "http" )
	{
		@nets = &getTcpBackendSYNConns( $ip_backend, $port_backend, @netstat );
	}
	if ( $type eq "udp" )
	{
		@nets = &getUdpBackendSYNConns( $ip_backend, $port_backend, @netstat );
	}
	if ( $type eq "l4xnat" )
	{
		@nets = &getL4BackendSYNConns( $fname, $ip_backend, @netstat );
	}
	return @nets;
}

#
sub getFarmSYNConns($fname,@netstat)
{
	my ( $fname, @netstat ) = @_;

	my $type  = &getFarmType( $fname );
	my $fvip  = &getFarmVip( "vip", $fname );
	my $fvipp = &getFarmVip( "vipp", $fname );
	my @nets  = ();

	if ( $type eq "tcp" )
	{
		@nets = &getTcpFarmSYNConns( @netstat, $fvip, $fvipp );
	}

	if ( $type eq "udp" )
	{
		@nets = &getUdpFarmSYNConns( @netstat, $fvip, $fvipp );
	}

	if ( $type eq "http" || $type eq "https" )
	{
		@nets = &getHTTPFarmSYNConns( @nets, @netstat, $fvip, $fvipp );
	}

	if ( $type eq "l4xnat" )
	{
		@nets = &getL4FarmSYNConns( $fname, @netstat );
	}

	return @nets;
}

# Generic function
# Returns farm file name
sub getFarmsByType($ftype)
{
	my ( $ftype ) = @_;
	opendir ( my $dir, "$configdir" ) || return -1;
	my @ffiles = grep { /^.*\_.*\.cfg/ && -f "$configdir/$_" } readdir ( $dir );
	closedir $dir;
	my @farms;
	foreach ( @ffiles )
	{
		my $fname = &getFarmName( $_ );
		my $tp    = &getFarmType( $fname );
		if ( $tp eq $ftype )
		{
			push ( @farms, $fname );
		}
	}
	return @farms;
}

# Generic function
# Returns farm type [udp|tcp|http|https|datalink|l4xnat|gslb]
sub getFarmType($fname)
{
	my ( $fname ) = @_;
	my $filename = &getFarmFile( $fname );
	if ( $filename =~ /$fname\_pen\_udp.cfg/ )
	{
		return "udp";
	}
	if ( $filename =~ /$fname\_pen.cfg/ )
	{
		return "tcp";
	}
	if ( $filename =~ /$fname\_pound.cfg/ )
	{
		my $out = "http";
		use File::Grep qw( fgrep fmap fdo );
		if ( fgrep { /ListenHTTPS/ } "$configdir/$filename" )
		{
			$out = "https";
		}
		return $out;
	}
	if ( $filename =~ /$fname\_datalink.cfg/ )
	{
		return "datalink";
	}
	if ( $filename =~ /$fname\_l4xnat.cfg/ )
	{
		return "l4xnat";
	}
	if ( $filename =~ /$fname\_gslb.cfg/ )
	{
		return "gslb";
	}
	return 1;
}

# Generic function
# Returns farm file name
sub getFarmFile($fname)
{
	my ( $fname ) = @_;
	opendir ( my $dir, "$configdir" ) || return -1;

	my @ffiles =
	  grep {
		     /^$fname\_.*\.cfg/
		  && !/^$fname\_.*guardian\.conf/
		  && !/^$fname\_status.cfg/
	  } readdir ( $dir );
	closedir $dir;
	if ( @ffiles )
	{
		return @ffiles[0];
	}
	else
	{
		return -1;
	}
}

# Generic function
# Returns farm status
sub getFarmStatus($fname)
{
	my ( $fname ) = @_;

	my $ftype  = &getFarmType( $fname );
	my $output = -1;

	# for every farm type but datalink or l4xnat
	if ( $ftype ne "datalink" && $ftype ne "l4xnat" )
	{
		my $pid = &getFarmPid( $fname );
		if ( $pid eq "-" )
		{
			$output = "down";
		}
		else
		{
			$output = "up";
		}
	}
	else
	{
		# Only for datalink and l4xnat
		if ( -e "$piddir\/$fname\_$ftype.pid" )
		{
			$output = "up";
		}
		else
		{
			$output = "down";
		}
	}

	return $output;
}

# Returns farm status
sub getFarmBootStatus($fname)
{
	my ( $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $file   = &getFarmFile( $fname );
	my $output = "down";

	if (    $type eq "tcp"
		 || $type eq "udp"
		 || $type eq "http"
		 || $type eq "https" )
	{
		open FO, "<$configdir/$file";
		while ( $line = <FO> )
		{
			$lastline = $line;
		}
		close FO;
		if ( $lastline !~ /^#down/ )
		{
			$output = "up";
		}
	}

	if ( $type eq "gslb" )
	{
		$output = &getFarmGSLBBootStatus( $file );
	}

	if ( $type eq "datalink" )
	{
		$output = &getDatalinkFarmBootStatus( $file );
	}

	if ( $type eq "l4xnat" )
	{
		$output = &getL4FarmBootStatus( $file );
	}

	return $output;
}

# Start Farm rutine
sub _runFarmStart($fname,$writeconf)
{
	my ( $fname, $writeconf ) = @_;

	my $status = &getFarmStatus( $fname );
	chomp ( $status );

	if ( $status eq "up" )
	{
		return 0;
	}

	my $type = &getFarmType( $fname );
	my $file = &getFarmFile( $fname );

	&logfile( "running 'Start write $writeconf' for $fname farm $type" );

	if (    $writeconf eq "true"
		 && $type ne "datalink"
		 && $type ne "l4xnat"
		 && $type ne "gslb" )
	{
		use Tie::File;
		tie @filelines, 'Tie::File', "$configdir\/$file";
		@filelines = grep !/^\#down/, @filelines;
		untie @filelines;
	}

	if ( $type eq "tcp" || $type eq "udp" )
	{
		$status = &_runTcpUdpFarmStart( $fname );
	}

	if ( $type eq "http" || $type eq "https" )
	{
		$status = &_runHTTPFarmStart( $fname, $file, $status );
	}

	if ( $type eq "gslb" )
	{
		$output = &setFarmGSLBStatus( $fname, "start", $writeconf );
	}

	if ( $type eq "datalink" )
	{
		$status = &_runDatalinkFarmStart();
	}

	if ( $type eq "l4xnat" )
	{
		$status = &_runL4FarmStart( $file, $writeconf, $status );
	}

	return $status;
}

# Start Farm basic rutine
sub runFarmStart($fname,$writeconf)
{
	my ( $fname, $writeconf ) = @_;

	my $status = &_runFarmStart( $fname, $writeconf );

	if ( $status == 0 )
	{
		&runFarmGuardianStart( $fname, "" );
	}

	return $status;
}

# Stop Farm basic rutine
sub runFarmStop($fname,$writeconf)
{
	my ( $fname, $writeconf ) = @_;

	&runFarmGuardianStop( $fname, "" );

	my $status = &_runFarmStop( $fname, $writeconf );

	return $status;
}

# Stop Farm rutine
sub _runFarmStop($fname,$writeconf)
{
	my ( $fname, $writeconf ) = @_;

	my $status = &getFarmStatus( $fname );
	if ( $status eq "down" )
	{
		return 0;
	}

	my $filename = &getFarmFile( $fname );
	if ( $filename == -1 )
	{
		return -1;
	}

	my $type   = &getFarmType( $fname );
	my $status = $type;

	&logfile( "running 'Stop write $writeconf' for $fname farm $type" );
	if ( $type eq "tcp" || $type eq "udp" )
	{
		$status = &_runTcpUdpFarmStop( $fname );
	}

	if ( $type eq "http" || $type eq "https" )
	{
		$status = &_runHTTPFarmStop( $fname, $status );
	}

	if ( $type eq "gslb" )
	{
		$status = &_runGSLBFarmStop( $fname, $writeconf, $status );
	}

	if ( $type eq "datalink" )
	{
		$status = &_runDatalinkFarmStop( $fname, $writeconf, $status );
	}

	if ( $type eq "l4xnat" )
	{
		$status = &_runL4FarmStop( $filename, $writeconf, $status );
	}

	if (    $writeconf eq "true"
		 && $type ne "datalink"
		 && $type ne "l4xnat"
		 && $type ne "gslb" )
	{
		open FW, ">>$configdir/$filename";
		print FW "#down\n";
		close FW;
	}

	return $status;
}

#
sub runFarmCreate($fproto,$fvip,$fvipp,$fname,$fdev)
{
	my ( $fproto, $fvip, $fvipp, $fname, $fdev ) = @_;

	my $output = -1;
	my $ffile  = &getFarmFile( $fname );
	if ( $ffile != -1 )
	{
		# the farm name already exists
		$output = -2;
		return $output;
	}

	&logfile( "running 'Create' for $fname farm $type" );
	if ( $fproto eq "TCP" )
	{
		$output = &runTcpFarmCreate( $fvip, $fvipp, $fname );
	}

	if ( $fproto eq "UDP" )
	{
		$output = &runUdpFarmCreate( $fvip, $fvipp, $fname );
	}

	if ( $fproto eq "HTTP" || $fproto eq "HTTPS" )
	{
		$output = &runHTTPFarmCreate( $fproto, $fvip, $fvipp, $fname );
	}

	if ( $fproto eq "DATALINK" )
	{
		$output = &runDatalinkFarmCreate( $fname, $fvip, $fdev );
	}

	if ( $fproto eq "L4xNAT" )
	{
		$output = &runL4FarmCreate( $fvip, $fname );
	}

	if ( $fproto eq "GSLB" )
	{
		$output = &setFarmGSLB( $fvip, $fvipp, $fname );
	}

	return $output;
}

# Returns farm max connections
sub getFarmMaxConn($fname)
{
	my ( $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $file   = &getFarmFile( $fname );
	my $output = -1;

	if ( $type eq "tcp" || $type eq "udp" )
	{
		$output = &getTcpUdpFarmMaxConn( $file, $type );
	}

	if ( $type eq "http" || $type eq "https" )
	{
		$output = &getHTTPFarmMaxConn( $fname );
	}

	return $output;
}

# Returns farm listen port
sub getFarmPort($fname)
{
	my ( $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $file   = &getFarmFile( $fname );
	my $output = -1;

	if ( $type eq "tcp" || $type eq "udp" )
	{
		$output = &getTcpUdpFarmPort( $file );
	}

	if ( $type eq "http" || $type eq "https" )
	{
		$output = &getHTTPFarmPort( $fname );
	}

	return $output;
}

# Returns farm PID
sub getFarmPid($fname)
{
	my ( $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $file   = &getFarmFile( $fname );
	my $output = -1;

	if ( $type eq "tcp" || $type eq "udp" )
	{
		$output = &getTcpUdpFarmPid( $file );
	}

	if ( $type eq "http" || $type eq "https" )
	{
		$output = &getHTTPFarmPid( $fname );
	}

	if ( $type eq "gslb" )
	{
		$output = &getGSLBFarmPid( $fname, $file );
	}

	return $output;
}

# Returns farm vip
sub getFarmVip($info,$fname)
{
	my ( $info, $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $file   = &getFarmFile( $fname );
	my $output = -1;

	if ( $type eq "tcp" || $type eq "udp" )
	{
		$output = &getTcpUdpFarmVip( $info, $file );
	}

	if ( $type eq "http" || $type eq "https" )
	{
		$output = &getHTTPFarmVip( $info, $file );
	}

	if ( $type eq "l4xnat" )
	{
		$output = &getL4FarmVip( $info, $file );
	}

	if ( $type eq "datalink" )
	{
		$output = &getDatalinkFarmVip( $info, $file );
	}

	if ( $type eq "gslb" )
	{
		$output = &getGSLBFarmVip( $info, $file );
	}

	return $output;
}

# Generic function
# this function creates a file to tell that the farm needs to be restarted to apply changes
sub setFarmRestart($farmname)
{
	my ( $farmname ) = @_;
	if ( !-e "/tmp/$farmname.lock" )
	{
		open FILE, ">/tmp/$farmname.lock";
		print FILE "";
		close FILE;
	}
}

# Generic function
# this function deletes the file marking the farm to be restarted to apply changes
sub setFarmNoRestart($farmname)
{
	my ( $farmname ) = @_;
	if ( -e "/tmp/$farmname.lock" )
	{
		unlink ( "/tmp/$farmname.lock" );
	}
}

# Generic function
# Returns farm file list
sub getFarmList()
{
	opendir ( DIR, $configdir );
	my @files = grep ( /\_pen.*\.cfg$/, readdir ( DIR ) );
	closedir ( DIR );
	opendir ( DIR, $configdir );
	my @files2 = grep ( /\_pound.cfg$/, readdir ( DIR ) );
	closedir ( DIR );
	opendir ( DIR, $configdir );
	my @files3 = grep ( /\_datalink.cfg$/, readdir ( DIR ) );
	closedir ( DIR );
	opendir ( DIR, $configdir );
	my @files4 = grep ( /\_l4xnat.cfg$/, readdir ( DIR ) );
	closedir ( DIR );
	opendir ( DIR, $configdir );
	my @files5 = grep ( /\_gslb.cfg$/, readdir ( DIR ) );
	closedir ( DIR );
	my @files = ( @files, @files2, @files3, @files4, @files5 );
	return @files;
}

# Generic function
sub getFarmName($farmfile)
{
	my ( $farmfile ) = @_;
	my @ffile = split ( "_", $farmfile );
	return @ffile[0];
}

# Generic function
# Delete Farm rutine
sub runFarmDelete($fname)
{
	my ( $fname ) = @_;

	my $ftype = &getFarmType( $fname );

	&logfile( "running 'Delete' for $fname" );
	unlink glob ( "$configdir/$fname\_*\.cfg" );
	$status = $?;
	unlink glob ( "$configdir/$fname\_*\.html" );
	unlink glob ( "$configdir/$fname\_*\.conf" );
	unlink glob ( "$basedir/img/graphs/bar$fname*" );
	unlink glob ( "$basedir/img/graphs/$fname-farm\_*" );
	unlink glob ( "$rrdap_dir$rrd_dir/$fname-farm*" );
	unlink glob ( "${logdir}/${fname}\_*farmguardian*" );

	if ( $ftype eq "gslb" )
	{
		use File::Path 'rmtree';
		rmtree( ["$configdir/$fname\_gslb.cfg"] );
	}

	# delete cron task to check backends
	use Tie::File;
	tie @filelines, 'Tie::File', "/etc/cron.d/zenloadbalancer";
	my @filelines = grep !/\# \_\_$farmname\_\_/, @filelines;
	untie @filelines;

	# delete nf marks
	delMarks( $fname, "" );

	return $status;
}

# Set farm virtual IP and virtual PORT
sub setFarmVirtualConf($vip,$vipp,$fname)
{
	my ( $vip, $vipp, $fname ) = @_;

	my $fconf = &getFarmFile( $fname );
	my $type  = &getFarmType( $fname );
	my $stat  = -1;

	&logfile( "setting 'VirtualConf $vip $vipp' for $fname farm $type" );
	if ( $type eq "tcp" || $type eq "udp" )
	{
		$stat = &setTcpUdpFarmVirtualConf( $vip, $vipp, $fname, $fconf );
	}

	if ( $type eq "http" || $type eq "https" )
	{
		$stat = &setHTTPFarmVirtualConf( $vip, $vipp, $fconf );
	}

	if ( $type eq "datalink" )
	{
		$stat = &setDatalinkFarmVirtualConf( $vip, $vipp, $fname, $fconf );
	}

	if ( $type eq "l4xnat" )
	{
		$stat = &setL4FarmVirtualConf( $vip, $vipp, $fname, $fconf );
	}

	if ( $type eq "gslb" )
	{
		$stat = &setGSLBFarmVirtualConf( $vip, $vipp, $fconf );
	}

	return $stat;
}

#
sub setFarmServer($ids,$rip,$port,$max,$weight,$priority,$timeout,$fname,$service)
{
	my ( $ids, $rip, $port, $max, $weight, $priority, $timeout, $fname, $svice ) =
	  @_;

	my $type      = &getFarmType( $fname );
	my $file      = &getFarmFile( $fname );
	my $output    = -1;
	my $nsflag    = "false";
	my $backend   = 0;
	my $idservice = 0;

	&logfile(
		"setting 'Server $ids $rip $port max $max weight $weight prio $priority timeout $timeout' for $fname farm $type"
	);

	if ( $type eq "tcp" || $type eq "udp" )
	{
		$output =
		  &setTcpUdpFarmServer( $ids, $rip, $port, $max, $weight, $priority, $fname,
								$file );
	}

	if ( $type eq "datalink" )
	{
		$output =
		  &setDatalinkFarmServer( $file, $ids, $rip, $port, $weight, $priority );
	}

	if ( $type eq "l4xnat" )
	{
		$output =
		  &setL4FarmServer( $ids, $rip, $port, $weight, $priority, $fname, $file );
	}

	if ( $type eq "http" || $type eq "https" )
	{
		$output = setHTTPFarmServer(
									 $ids,     $rip,     $port,  $priority,
									 $timeout, $fname,   $svice, $file,
									 $nsflag,  $backend, $idservice
		);
	}

	return $output;
}

#
sub runFarmServerDelete($ids,$fname,$service)
{
	( $ids, $fname, $svice ) = @_;

	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;

	&logfile( "running 'ServerDelete $ids' for $fname farm $type" );

	if ( $type eq "tcp" || $type eq "udp" )
	{
		$output = &runTcpUdpFarmServerDelete( $ids, $fname, $ffile );
	}

	if ( $type eq "datalink" )
	{
		$output = &runDatalinkFarmServerDelete( $ids, $ffile );
	}

	if ( $type eq "l4xnat" )
	{
		$output = &runL4FarmServerDelete( $ids, $ffile );
	}

	if ( $type eq "http" || $type eq "https" )
	{
		$output = &runHTTPFarmServerDelete( $ids, $fname, $ffile );
	}

	if ( $type eq "gslb" )
	{
		$output = &runGSLBFarmServerDelete( $ids, $ffile, $service );
	}

	return $output;
}

#
sub getFarmBackendStatusCtl($fname)
{
	my ( $fname ) = @_;
	my $type      = &getFarmType( $fname );
	my @output    = -1;

	if ( $type eq "tcp" || $type eq "udp" )
	{
		$output = &getTcpUdpFarmBackendStatusCtl( $fname );
	}

	if ( $type eq "http" || $type eq "https" )
	{
		@output = &getHTTPFarmBackendStatusCtl( $fname );
	}

	if ( $type eq "datalink" )
	{
		@output = &getDatalinkFarmBackendStatusCtl( $fname );
	}

	if ( $type eq "l4xnat" )
	{
		@output = &getL4FarmBackendStatusCtl( $fname );
	}

	return @output;
}

#function that return the status information of a farm:
#ip, port, backendstatus, weight, priority, clients
sub getFarmBackendsStatus($fname,@content)
{
	my ( $fname, @content ) = @_;
	my $type   = &getFarmType( $fname );
	my @output = -1;

	if ( $type eq "http" || $type eq "https" )
	{
		@output = &getHTTPFarmBackendsStatus( $fname, @content );
	}

	if ( $type eq "tcp" || $type eq "udp" )
	{
		@output = &getTcpUdpFarmBackendsStatus( $fname, @content );
	}

	if ( $type eq "datalink" )
	{
		@output = &getDatalinkFarmBackendsStatus( @content );
	}

	if ( $type eq "l4xnat" )
	{
		@output = &getL4FarmBackendsStatus( $fname, @content );
	}

	return @output;
}

#function that return the status information of a farm:
sub getFarmBackendsClients($idserver,@content,$fname)
{
	my ( $idserver, @content, $fname ) = @_;
	my $type   = &getFarmType( $fname );
	my $output = -1;

	if ( $type eq "http" || $type eq "https" )
	{
		$output = &getHTTPFarmBackendsClients( $idserver, @content, $fname );
	}

	if ( $type eq "tcp" || $type eq "udp" )
	{
		$output = &getTcpUdpFarmBackendsClients( $idserver, @content, $fname );
	}
	return $output;
}

#function that return the status information of a farm:
sub getFarmBackendsClientsList($fname,@content)
{
	( $fname, @content ) = @_;
	my $type   = &getFarmType( $fname );
	my @output = -1;

	if ( $type eq "http" || $type eq "https" )
	{
		@output = &getHTTPFarmBackendsClientsList( $fname, @content );
	}

	if ( $type eq "tcp" || $type eq "udp" )
	{
		@output = &getFarmBackendsClientsList( $fname, @content );
	}
	return @output;
}

sub setFarmBackendStatus($fname,$index,$stat)
{
	( $fname, $index, $stat ) = @_;

	my $type   = &getFarmType( $fname );
	my $file   = &getFarmFile( $fname );
	my $output = -1;

	if ( $type eq "datalink" )
	{
		$output = &setDatalinkFarmBackendStatus( $file, $index, $stat );
	}

	if ( $type eq "l4xnat" )
	{
		$output = &setL4FarmBackendStatus( $file, $index, $stat );
	}

	return $output;
}

#function that renames a farm
sub setNewFarmName($fname,$newfname)
{
	my ( $fname, $newfname ) = @_;
	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;

	if ( $newfname =~ /^$/ )
	{
		&logfile( "error 'NewFarmName $newfname' is empty" );
		return -2;
	}

	&logfile( "setting 'NewFarmName $newfname' for $fname farm $type" );

	if ( $type eq "tcp" || $type eq "udp" )
	{
		$output = &setTcpUdpNewFarmName( $fname, $newfname );
	}

	if ( $type eq "http" || $type eq "https" )
	{
		$output = &setHTTPNewFarmName( $fname, $newfname );
	}

	if ( $type eq "datalink" || $type eq "l4xnat" )
	{
		if ( $type eq "l4xnat" )
		{
			&runFarmStop( $fname, "false" );
		}
		my $newffile = "$newfname\_$type.cfg";
		use Tie::File;
		tie @filelines, 'Tie::File', "$configdir\/$ffile";
		for ( @filelines )
		{
			s/^$fname\;/$newfname\;/g;
		}
		untie @filelines;
		rename ( "$configdir\/$ffile",         "$configdir\/$newffile" );
		rename ( "$piddir\/$fname\_$type.pid", "$piddir\/$newfname\_$type.pid" );
		$output = $?;
	}

	if ( $type eq "l4xnat" )
	{

		# Rename fw marks for this farm
		&renameMarks( $fname, $newfname );
		&runFarmStart( $newfname, "false" );
		$output = 0;
	}

	if ( $type eq "gslb" )
	{
		$output = &setGSLBNewFarmName( $newfname, $ffile, $type );
	}

	# rename rrd
	rename ( "$rrdap_dir$rrd_dir/$fname-farm.rrd",
			 "$rrdap_dir$rrd_dir/$newfname-farm.rrd" );

	# delete old graphs
	unlink ( "img/graphs/bar$fname.png" );

	return $output;
}

#function that check if the config file is OK.
sub getFarmConfigIsOK($fname)
{
	( $fname ) = @_;

	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;

	if ( $type eq "http" || $type eq "https" )
	{
		$output = &getHTTPFarmConfigIsOK( $ffile );
	}
	if ( $type eq "gslb" )
	{
		$output = &getFarmGSLBConfigIsOK( $ffile );
	}
	return $output;
}

#function that check if a backend on a farm is on maintenance mode
sub getFarmBackendMaintenance($fname,$backend,$service)
{
	my ( $fname, $backend, $service ) = @_;
	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;

	if ( $type eq "tcp" || $type eq "udp" )
	{
		$output = &getTcpUdpFarmBackendMaintenance( $fname, $backend );
	}

	if ( $type eq "http" || $type eq "https" )
	{
		$output = &getHTTPFarmBackendMaintenance( $fname, $backend, $service );
	}

	return $output;
}

#function that enable the maintenance mode for backend
sub setFarmBackendMaintenance($fname,$backend,$service)
{
	my ( $fname, $backend, $service ) = @_;
	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );
	my $output = -1;

	if ( $type eq "tcp" || $type eq "udp" )
	{
		$output = &setTcpUdpFarmBackendMaintenance( $fname, $backend );
	}

	if ( $type eq "http" || $type eq "https" )
	{
		$output = &setHTTPFarmBackendMaintenance( $fname, $backend, $service );
	}

	return $output;
}

#function that disable the maintenance mode for backend
sub setFarmBackendNoMaintenance($fname,$backend,$service)
{
	my ( $fname, $backend, $service ) = @_;
	my $type  = &getFarmType( $fname );
	my $ffile = &getFarmFile( $fname );
	$output = -1;

	if ( $type eq "tcp" || $type eq "udp" )
	{
		$output = &setTcpUdpFarmBackendNoMaintenance( $fname, $backend );
	}

	if ( $type eq "http" || $type eq "https" )
	{
		$output = &setHTTPFarmBackendNoMaintenance( $fname, $backend, $service );
	}

	return $output;
}

# Generic function
#checks thata farmname has correct characters (number, letters and lowercases)
sub checkFarmnameOK($fname)
{
	( $check_name ) = @_;
	$output = -1;

	#if ($fname =~ /^\w+$/){
	if ( $check_name =~ /^[a-zA-Z0-9\-]*$/ )
	{
		$output = 0;
	}

	return $output;
}

#function that return indicated value from a HTTP Service
#vs return virtual server
sub getFarmVS($farmname,$service,$tag)
{
	my ( $fname, $service, $tag ) = @_;

	my $output = "";
	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );

	if ( $type eq "http" || $type eq "https" )
	{
		$output = &getHTTPFarmVS( $ffile, $service, $tag );
	}

	if ( $type eq "gslb" )
	{
		$output = &getGSLBFarmVS( $ffile, $service, $tag );
	}

	return $output;
}

#set values for a service
sub setFarmVS($farmname,$service,$tag,$string)
{
	my ( $fname, $service, $tag, $string ) = @_;

	my $output = "";
	my $type   = &getFarmType( $fname );
	my $ffile  = &getFarmFile( $fname );

	if ( $type eq "http" || $type eq "https" )
	{
		$output = &setHTTPFarmVS( $ffile, $service, $tag, $string );
	}

	if ( $type eq "gslb" )
	{
		$output = &setGSLBFarmVS( $ffile, $service, $tag, $string );
	}

	return @output;
}

sub setFarmName($farmname)
{

	$farmname =~ s/[^a-zA-Z0-9]//g;

}

# do not remove this
1
