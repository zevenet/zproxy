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

#
sub setFarmBlacklistTime    # ($blacklist_time,$farm_name)
{
	my ( $blacklist_time, $farm_name ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my $output    = -1;

	if ( $farm_type eq "tcp" || $farm_type eq "udp" )
	{
		$output = &setTcpUdpFarmBlacklistTime( $blacklist_time, $farm_name );
	}

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		$output = &setHTTPFarmBlacklistTime( $blacklist_time, $farm_name );
	}

	return $output;
}

#
sub getFarmBlacklistTime    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_type      = &getFarmType( $farm_name );
	my $farm_filename  = &getFarmFile( $farm_name );
	my $blacklist_time = -1;

	if ( $farm_type eq "tcp" || $farm_type eq "udp" )
	{
		$blacklist_time = &getTcpUdpFarmBlacklistTime( $farm_name );
	}

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		$blacklist_time = &getHTTPFarmBlacklistTime( $farm_filename );
	}

	return $blacklist_time;
}

#
sub setFarmSessionType    # ($session,$farm_name)
{
	my ( $session, $farm_name ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my $output    = -1;

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		$output = &setHTTPFarmSessionType( $session, $farm_name );
	}

	if ( $farm_type eq "l4xnat" )
	{
		$output = &setL4FarmSessionType( $session, $farm_name );
	}
	return $output;
}

#
sub getFarmSessionType    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my $output    = -1;

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		$output = &getHTTPFarmSessionType( $farm_name );
	}

	if ( $farm_type eq "l4xnat" )
	{
		$output = &getL4FarmSessionType( $farm_name );
	}

	return $output;
}

#asign a timeout value to a farm
sub setFarmTimeout    # ($timeout,$farm_name)
{
	my ( $timeout, $farm_name ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my $output    = -1;

	&logfile( "setting 'Timeout $timeout' for $farm_name farm $farm_type" );

	if ( $farm_type eq "tcp" || $farm_type eq "udp" )
	{
		$output = &setTcpUdpFarmTimeout( $timeout, $farm_name );
	}

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		$output = &setHTTPFarmTimeout( $timeout, $farm_name );
	}

	return $output;
}

#
sub getFarmTimeout    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my $output    = -1;

	if ( $farm_type eq "tcp" || $farm_type eq "udp" )
	{
		$output = &getTcpUdpFarmTimeout( $farm_name );
	}

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		$output = &getHTTPFarmTimeout( $farm_name );
	}

	return $output;
}

# set the lb algorithm to a farm
sub setFarmAlgorithm    # ($algorithm,$farm_name)
{
	my ( $algorithm, $farm_name ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my $output    = -1;

	&logfile( "setting 'Algorithm $algorithm' for $farm_name farm $farm_type" );

	if ( $farm_type eq "tcp" || $farm_type eq "udp" )
	{
		$output = &setTcpUdpFarmAlgorithm( $algorithm, $farm_name );
	}

	if ( $farm_type eq "datalink" )
	{
		$output = &setDatalinkFarmAlgorithm( $algorithm, $farm_name );
	}

	if ( $farm_type eq "l4xnat" )
	{
		$output = &setL4FarmAlgorithm( $algorithm, $farm_name );
	}

	return $output;
}

#
sub getFarmAlgorithm    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my $algorithm = -1;

	if ( $farm_type eq "tcp" || $farm_type eq "udp" )
	{
		$algorithm = &getTcpUdpFarmAlgorithm( $farm_name );
	}

	if ( $farm_type eq "datalink" )
	{
		$algorithm = &getDatalinkFarmAlgorithm( $farm_name );
	}

	if ( $farm_type eq "l4xnat" )
	{
		$algorithm = &getL4FarmAlgorithm( $farm_name );
	}

	return $algorithm;
}

# set client persistence to a farm
sub setFarmPersistence    # ($persistence,$farm_name)
{
	my ( $persistence, $farm_name ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my $output    = -1;

	if ( $farm_type eq "tcp" || $farm_type eq "udp" )
	{
		$output = &setTcpUdpFarmPersistence( $persistence, $farm_name );
	}

	if ( $farm_type eq "l4xnat" )
	{
		$output = &setL4FarmPersistence( $persistence, $farm_name );
	}

	return $output;
}

#
sub getFarmPersistence    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_type   = &getFarmType( $farm_name );
	my $persistence = -1;

	if ( $farm_type eq "tcp" || $farm_type eq "udp" )
	{
		$persistence = &getTcpUdpFarmPersistence( $farm_name );
	}

	if ( $farm_type eq "l4xnat" )
	{
		$persistence = &getL4FarmPersistence( $farm_name );
	}

	return $persistence;
}

# set the max clients of a farm
sub setFarmMaxClientTime    # ($max_client_time,$track,$farm_name)
{
	my ( $max_client_time, $track, $farm_name ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my $output    = -1;

	&logfile(
		"setting 'MaxClientTime $max_client_time $track' for $farm_name farm $farm_type"
	);

	if ( $farm_type eq "tcp" || $farm_type eq "udp" )
	{
		$output = &setTcpUdpFarmMaxClientTime( $max_client_time, $track, $farm_name );
	}

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		$output = &setHTTPFarmMaxClientTime( $track, $farm_name );
	}

	if ( $farm_type eq "l4xnat" )
	{
		$output = &setL4FarmMaxClientTime( $track, $farm_name );
	}

	return $output;
}

#
sub getFarmMaxClientTime    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my @max_client_time;

	if ( $farm_type eq "tcp" || $farm_type eq "udp" )
	{
		@max_client_time = &getTcpUdpFarmMaxClientTime( $farm_name );
	}

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		@max_client_time = &getHTTPFarmMaxClientTime( $farm_name );
	}

	if ( $farm_type eq "l4xnat" )
	{
		@max_client_time = &getL4FarmMaxClientTime( $farm_name );
	}

	return @max_client_time;
}

# set the max conn of a farm
sub setFarmMaxConn    # ($max_connections,$farm_name)
{
	my ( $max_connections, $farm_name ) = @_;

	my $farm_type     = &getFarmType( $farm_name );
	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;

	&logfile( "setting 'MaxConn $max_connections' for $farm_name farm $farm_type" );

	if ( $farm_type eq "tcp" || $farm_type eq "udp" )
	{
		$output = &setTcpUdpFarmMaxConn( $max_connections, $farm_name );
	}

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		$output = &setHTTPFarmMaxConn( $max_connections, $farm_name );
	}

	return $output;
}

#
sub getFarmServers    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my @servers;

	if ( $farm_type eq "tcp" || $farm_type eq "udp" )
	{
		@servers = &getTcpUdpFarmServers( $farm_name );
	}

	if ( $farm_type eq "datalink" )
	{
		@servers = &getL4FarmServers( $farm_name );
	}

	if ( $farm_type eq "l4xnat" )
	{
		@servers = &getDatalinkFarmServers( $farm_name );
	}

	return @servers;
}

#
sub getFarmGlobalStatus    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my @run;

	if ( $farm_type eq "tcp" || $farm_type eq "udp" )
	{
		@run = &getTcpUdpFarmGlobalStatus( $farm_name );
	}

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		@run = getHTTPFarmGlobalStatus( $farm_name );
	}

	return @run;
}

#
sub getBackendEstConns    # ($farm_name,$ip_backend,$port_backend,@netstat)
{
	my ( $farm_name, $ip_backend, $port_backend, @netstat ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my @nets      = ();

	if ( $farm_type eq "tcp" || $farm_type eq "udp" )
	{
		@nets =
		  &getTcpUdpBackendEstConns( $farm_name, $ip_backend, $port_backend, @netstat );
	}
	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		@nets =
		  &getHTTPBackendEstConns( $farm_name, $ip_backend, $port_backend, @netstat );
	}
	if ( $farm_type eq "l4xnat" )
	{
		@nets = &getL4BackendEstConns( $farm_name, $ip_backend, @netstat );
	}

	return @nets;
}

#
sub getFarmEstConns    # ($farm_name,@netstat)
{
	my ( $farm_name, @netstat ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my $pid       = &getFarmPid( $farm_name );
	my @nets      = ();

	if ( $pid eq "-" )
	{
		return @nets;
	}

	if ( $farm_type eq "tcp" )
	{
		@nets = &getTcpFarmEstConns( $farm_name, @netstat );
	}

	if ( $farm_type eq "udp" )
	{
		@nets = &getUdpFarmEstConns( $farm_name, @netstat );
	}

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		@nets = &getHTTPFarmEstConns( $farm_name, @netstat );
	}

	if ( $farm_type eq "l4xnat" )
	{
		@nets = &getL4FarmEstConns( $farm_name, @netstat );
	}

	return @nets;
}

sub getBackendSYNConns    # ($farm_name,$ip_backend,$port_backend,@netstat)
{
	my ( $farm_name, $ip_backend, $port_backend, @netstat ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my @nets      = ();

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		@nets =
		  &getHTTPBackendSYNConns( $farm_name, $ip_backend, $port_backend, @netstat );
	}
	if ( $farm_type eq "tcp" )
	{
		@nets =
		  &getTcpBackendSYNConns( $farm_name, $ip_backend, $port_backend, @netstat );
	}
	if ( $farm_type eq "udp" )
	{
		@nets =
		  &getUdpBackendSYNConns( $farm_name, $ip_backend, $port_backend, @netstat );
	}
	if ( $farm_type eq "l4xnat" )
	{
		@nets =
		  &getL4BackendSYNConns( $farm_name, $ip_backend, $port_backend, @netstat );
	}

	return @nets;
}

#
sub getFarmSYNConns    # ($farm_name, @netstat)
{
	my ( $farm_name, @netstat ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my @nets      = ();

	if ( $farm_type eq "tcp" )
	{
		@nets = &getTcpFarmSYNConns( $farm_name, @netstat );
	}

	if ( $farm_type eq "udp" )
	{
		@nets = &getUdpFarmSYNConns( $farm_name, @netstat );
	}

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		@nets = &getHTTPFarmSYNConns( $farm_name, @netstat );
	}

	if ( $farm_type eq "l4xnat" )
	{
		@nets = &getL4FarmSYNConns( $farm_name, @netstat );
	}

	return @nets;
}

# Generic function
# Returns farm file name
sub getFarmsByType    # ($farm_type)
{
	my ( $farm_type ) = @_;

	my @farm_names = ();

	opendir ( my $dir, "$configdir" ) || return -1;

  # gslb uses a directory, not a file
  # my @farm_files = grep { /^.*\_.*\.cfg/ && -f "$configdir/$_" } readdir ( $dir );
	my @farm_files = grep { /^.*\_.*\.cfg/ } readdir ( $dir );
	closedir $dir;

	foreach my $farm_filename ( @farm_files )
	{
		next if $farm_filename =~ /.*status.cfg/;
		my $farm_name = &getFarmName( $farm_filename );

		if ( &getFarmType( $farm_name ) eq $farm_type )
		{
			push ( @farm_names, $farm_name );
		}
	}

	return @farm_names;
}

# Generic function
# Returns farm type [udp|tcp|http|https|datalink|l4xnat|gslb]
sub getFarmType    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );

	if ( $farm_filename =~ /$farm_name\_pen\_udp.cfg/ )
	{
		return "udp";
	}
	if ( $farm_filename =~ /$farm_name\_pen.cfg/ )
	{
		return "tcp";
	}
	if ( $farm_filename =~ /$farm_name\_pound.cfg/ )
	{
		use File::Grep qw( fgrep fmap fdo );
		if ( fgrep { /ListenHTTPS/ } "$configdir/$farm_filename" )
		{
			return "https";
		}
		else
		{
			return "http";
		}
	}
	if ( $farm_filename =~ /$farm_name\_datalink.cfg/ )
	{
		return "datalink";
	}
	if ( $farm_filename =~ /$farm_name\_l4xnat.cfg/ )
	{
		return "l4xnat";
	}
	if ( $farm_filename =~ /$farm_name\_gslb.cfg/ )
	{
		return "gslb";
	}
	return 1;
}

# Generic function
# Returns farm file name
sub getFarmFile    # ($farm_name)
{
	my ( $farm_name ) = @_;

	opendir ( my $dir, "$configdir" ) || return -1;
	my @farm_files =
	  grep {
		     /^$farm_name\_.*\.cfg/
		  && !/^$farm_name\_.*guardian\.conf/
		  && !/^$farm_name\_status.cfg/
	  } readdir ( $dir );
	closedir $dir;

	if ( @farm_files )
	{
		return $farm_files[0];
	}
	else
	{
		return -1;
	}
}

# Generic function
# Returns farm status
sub getFarmStatus    # ($farm_name)
{
	my $farm_name = shift;

	my $output = -1;
	return $output if !defined ( $farm_name );    # farm name cannot be empty

	my $farm_type = &getFarmType( $farm_name );

	# for every farm type but datalink or l4xnat
	if ( $farm_type ne "datalink" && $farm_type ne "l4xnat" )
	{
		my $pid = &getFarmPid( $farm_name );
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
		if ( -e "$piddir\/$farm_name\_$farm_type.pid" )
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
sub getFarmBootStatus    # ($farm_name)
{
	my $farm_name = shift;

	my $farm_type = &getFarmType( $farm_name );
	my $output    = "down";

	if ( $farm_type eq "tcp" || $farm_type eq "udp" )
	{
		$output = &getTcpUdpFarmBootStatus( $farm_name );
	}

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		$output = &getHTTPFarmBootStatus( $farm_name );
	}

	if ( $farm_type eq "gslb" )
	{
		$output = &getGSLBFarmBootStatus( $farm_name );
	}

	if ( $farm_type eq "datalink" )
	{
		$output = &getDatalinkFarmBootStatus( $farm_name );
	}

	if ( $farm_type eq "l4xnat" )
	{
		$output = &getL4FarmBootStatus( $farm_name );
	}

	return $output;
}

# Start Farm rutine
sub _runFarmStart    # ($farm_name, $writeconf)
{
	my ( $farm_name, $writeconf ) = @_;

	my $status = &getFarmStatus( $farm_name );

	# finish the function if the tarm is already up
	if ( $status eq "up" )
	{
		return 0;
	}

	my $farm_type     = &getFarmType( $farm_name );
	my $farm_filename = &getFarmFile( $farm_name );

	&logfile( "running 'Start write $writeconf' for $farm_name farm $farm_type" );

	if (    $writeconf eq "true"
		 && $farm_type ne "datalink"
		 && $farm_type ne "l4xnat"
		 && $farm_type ne "gslb" )
	{
		use Tie::File;
		tie @configfile, 'Tie::File', "$configdir\/$farm_filename";
		@configfile = grep !/^\#down/, @configfile;
		untie @configfile;
	}

	if ( $farm_type eq "tcp" || $farm_type eq "udp" )
	{
		$status = &_runTcpUdpFarmStart( $farm_name );
	}

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		$status = &_runHTTPFarmStart( $farm_name );
	}

	if ( $farm_type eq "gslb" )
	{
		$status = &_runGSLBFarmStart( $farm_name, $writeconf );
	}

	if ( $farm_type eq "datalink" )
	{
		$status = &_runDatalinkFarmStart( $farm_name, $writeconf, $status );
	}

	if ( $farm_type eq "l4xnat" )
	{
		$status = &_runL4FarmStart( $farm_name, $writeconf );
	}

	return $status;
}

# Generic function
# Start Farm basic rutine
sub runFarmStart    # ($farm_name,$writeconf)
{
	my ( $farm_name, $writeconf ) = @_;

	my $status = &_runFarmStart( $farm_name, $writeconf );

	if ( $status == 0 )
	{
		&runFarmGuardianStart( $farm_name, "" );
	}

	return $status;
}

# Generic function
# Stop Farm basic rutine
sub runFarmStop    # ($farm_name,$writeconf)
{
	my ( $farm_name, $writeconf ) = @_;

	&runFarmGuardianStop( $farm_name, "" );

	my $status = &_runFarmStop( $farm_name, $writeconf );

	return $status;
}

# Stop Farm rutine
sub _runFarmStop    # ($farm_name,$writeconf)
{
	my ( $farm_name, $writeconf ) = @_;

	my $status = &getFarmStatus( $farm_name );
	if ( $status eq "down" )
	{
		return 0;
	}

	my $farm_filename = &getFarmFile( $farm_name );
	if ( $farm_filename == -1 )
	{
		return -1;
	}

	my $farm_type = &getFarmType( $farm_name );
	$status = $farm_type;

	&logfile( "running 'Stop write $writeconf' for $farm_name farm $farm_type" );

	if ( $farm_type eq "tcp" || $farm_type eq "udp" )
	{
		$status = &_runTcpUdpFarmStop( $farm_name );
	}

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		$status = &_runHTTPFarmStop( $farm_name );
	}

	if ( $farm_type eq "gslb" )
	{
		$status = &_runGSLBFarmStop( $farm_name, $writeconf );
	}

	if ( $farm_type eq "datalink" )
	{
		$status = &_runDatalinkFarmStop( $farm_name, $writeconf );
	}

	if ( $farm_type eq "l4xnat" )
	{
		$status = &_runL4FarmStop( $farm_name, $writeconf );
	}
	&logfile( 'stopFarm: ' . $status );

	if (    $writeconf eq "true"
		 && $farm_type ne "datalink"
		 && $farm_type ne "l4xnat"
		 && $farm_type ne "gslb" )
	{
		open FW, ">>$configdir/$farm_filename";
		print FW "#down\n";
		close FW;
	}

	return $status;
}

#
sub runFarmCreate    # ($farm_type,$vip,$vip_port,$farm_name,$fdev)
{
	my ( $farm_type, $vip, $vip_port, $farm_name, $fdev ) = @_;

	my $output        = -1;
	my $farm_filename = &getFarmFile( $farm_name );

	if ( $farm_filename != -1 )
	{
		# the farm name already exists
		$output = -2;
		return $output;
	}

	&logfile( "running 'Create' for $farm_name farm $farm_type" );

	if ( $farm_type eq "TCP" )
	{
		$output = &runTcpFarmCreate( $vip, $vip_port, $farm_name );
	}

	if ( $farm_type eq "UDP" )
	{
		$output = &runUdpFarmCreate( $vip, $vip_port, $farm_name );
	}

	if ( $farm_type eq "HTTP" || $farm_type eq "HTTPS" )
	{
		$output = &runHTTPFarmCreate( $vip, $vip_port, $farm_name, $farm_type );
	}

	if ( $farm_type eq "DATALINK" )
	{
		$output = &runDatalinkFarmCreate( $farm_name, $vip, $fdev );
	}

	if ( $farm_type eq "L4xNAT" )
	{
		$output = &runL4FarmCreate( $vip, $farm_name );
	}

	if ( $farm_type eq "GSLB" )
	{
		$output = &runGSLBFarmCreate( $vip, $vip_port, $farm_name );
	}

	return $output;
}

# Returns farm max connections
sub getFarmMaxConn    # ($farm_name)
{
	my $farm_name = shift;

	my $farm_type = &getFarmType( $farm_name );
	my $output    = -1;

	if ( $farm_type eq "tcp" || $farm_type eq "udp" )
	{
		$output = &getTcpUdpFarmMaxConn( $farm_name );
	}

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		$output = &getHTTPFarmMaxConn( $farm_name );
	}

	return $output;
}

# Returns farm listen port
sub getFarmPort    # ($farm_name)
{
	my $farm_name = shift;

	my $farm_type = &getFarmType( $farm_name );
	my $output    = -1;

	if ( $farm_type eq "tcp" || $farm_type eq "udp" )
	{
		$output = &getTcpUdpFarmPort( $farm_name );
	}

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		$output = &getHTTPFarmPort( $farm_name );
	}

	return $output;
}

# Returns farm PID
sub getFarmPid    # ($farm_name)
{
	my $farm_name = shift;

	my $farm_type = &getFarmType( $farm_name );
	my $output    = -1;

	if ( $farm_type eq "tcp" || $farm_type eq "udp" )
	{
		$output = &getTcpUdpFarmPid( $farm_name );
	}

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		$output = &getHTTPFarmPid( $farm_name );
	}

	if ( $farm_type eq "gslb" )
	{
		$output = &getGSLBFarmPid( $farm_name );
	}

	return $output;
}

# Returns farm vip
sub getFarmVip    # ($info,$farm_name)
{
	my ( $info, $farm_name ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my $output    = -1;

	if ( $farm_type eq "tcp" || $farm_type eq "udp" )
	{
		$output = &getTcpUdpFarmVip( $info, $farm_name );
	}

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		$output = &getHTTPFarmVip( $info, $farm_name );
	}

	if ( $farm_type eq "l4xnat" )
	{
		$output = &getL4FarmVip( $info, $farm_name );
	}

	if ( $farm_type eq "datalink" )
	{
		$output = &getDatalinkFarmVip( $info, $farm_name );
	}

	if ( $farm_type eq "gslb" )
	{
		$output = &getGSLBFarmVip( $info, $farm_name );
	}

	return $output;
}

# Generic function
# this function creates a file to tell that the farm needs to be restarted to apply changes
sub setFarmRestart    # ($farm_name)
{
	my $farm_name = shift;

	# do nothing if the farm is not running
	return if &getFarmStatus( $farm_name ) ne 'up';

	if ( !-e "/tmp/$farm_name.lock" )
	{
		open FILE, ">/tmp/$farm_name.lock";
		print FILE "";
		close FILE;
	}
}

# Generic function
# this function deletes the file marking the farm to be restarted to apply changes
sub setFarmNoRestart    # ($farm_name)
{
	my $farm_name = shift;

	if ( -e "/tmp/$farm_name.lock" )
	{
		unlink ( "/tmp/$farm_name.lock" );
	}
}

# Generic function
# Returns farms configuration filename list
sub getFarmList    # ()
{
	opendir ( DIR, $configdir );
	my @files1 = grep ( /\_pen.*\.cfg$/, readdir ( DIR ) );
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
	my @files = ( @files1, @files2, @files3, @files4, @files5 );

	return @files;
}

# Generic function
# Returns
sub getFarmName    # ($farm_filename)
{
	my $farm_filename = shift;

	my @filename_split = split ( "_", $farm_filename );

	return $filename_split[0];
}

# Generic function
# Delete Farm rutine
sub runFarmDelete    # ($farm_name)
{
	my $farm_name = shift;

	my $farm_type = &getFarmType( $farm_name );

	&logfile( "running 'Delete' for $farm_name" );
	unlink glob ( "$configdir/$farm_name\_*\.cfg" );
	$status = $?;
	unlink glob ( "$configdir/$farm_name\_*\.html" );
	unlink glob ( "$configdir/$farm_name\_*\.conf" );
	unlink glob ( "$basedir/img/graphs/bar$farm_name*" );
	unlink glob ( "$basedir/img/graphs/$farm_name-farm\_*" );
	unlink glob ( "$rrdap_dir/$rrd_dir/$farm_name-farm*" );
	unlink glob ( "${logdir}/${farm_name}\_*farmguardian*" );

	if ( $farm_type eq "gslb" )
	{
		use File::Path 'rmtree';
		rmtree( ["$configdir/$farm_name\_gslb.cfg"] );
	}

	# delete cron task to check backends
	use Tie::File;
	tie @filelines, 'Tie::File', "/etc/cron.d/zenloadbalancer";
	my @filelines = grep !/\# \_\_$farm_name\_\_/, @filelines;
	untie @filelines;

	# delete nf marks
	delMarks( $farm_name, "" );

	return $status;
}

# Set farm virtual IP and virtual PORT
sub setFarmVirtualConf    # ($vip,$vip_port,$farm_name)
{
	my ( $vip, $vip_port, $farm_name ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my $stat      = -1;

	&logfile(
			  "setting 'VirtualConf $vip $vip_port' for $farm_name farm $farm_type" );

	if ( $farm_type eq "tcp" || $farm_type eq "udp" )
	{
		$stat = &setTcpUdpFarmVirtualConf( $vip, $vip_port, $farm_name );
	}

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		$stat = &setHTTPFarmVirtualConf( $vip, $vip_port, $farm_name );
	}

	if ( $farm_type eq "datalink" )
	{
		$stat = &setDatalinkFarmVirtualConf( $vip, $vip_port, $farm_name );
	}

	if ( $farm_type eq "l4xnat" )
	{
		$stat = &setL4FarmVirtualConf( $vip, $vip_port, $farm_name );
	}

	if ( $farm_type eq "gslb" )
	{
		$stat = &setGSLBFarmVirtualConf( $vip, $vip_port, $farm_name );
	}

	return $stat;
}

# Add a new Backend
sub setFarmServer # $output ($ids,$rip,$port,$max,$weight,$priority,$timeout,$farm_name,$service)
{
	my (
		 $ids,      $rip,     $port,      $max, $weight,
		 $priority, $timeout, $farm_name, $service
	) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my $output    = -1;

	&logfile(
		"setting 'Server $ids $rip $port max $max weight $weight prio $priority timeout $timeout' for $farm_name farm $farm_type"
	);

	if ( $farm_type eq "tcp" || $farm_type eq "udp" )
	{
		$output =
		  &setTcpUdpFarmServer( $ids, $rip, $port, $max, $weight, $priority,
								$farm_name );
	}

	if ( $farm_type eq "datalink" )
	{
		$output =
		  &setDatalinkFarmServer( $ids, $rip, $port, $weight, $priority, $farm_name );
	}

	if ( $farm_type eq "l4xnat" )
	{
		$output = &setL4FarmServer( $ids, $rip, $port, $weight, $priority, $farm_name );
	}

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		$output =
		  &setHTTPFarmServer( $ids, $rip, $port, $priority, $timeout, $farm_name,
							  $service, );
	}

	# FIXME: include setGSLBFarmNewBackend

	return $output;
}

#
sub runFarmServerDelete    # ($ids,$farm_name,$service)
{
	my ( $ids, $farm_name, $service ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my $output    = -1;

	&logfile( "running 'ServerDelete $ids' for $farm_name farm $farm_type" );

	if ( $farm_type eq "tcp" || $farm_type eq "udp" )
	{
		$output = &runTcpUdpFarmServerDelete( $ids, $farm_name );
	}

	if ( $farm_type eq "datalink" )
	{
		$output = &runDatalinkFarmServerDelete( $ids, $farm_name );
	}

	if ( $farm_type eq "l4xnat" )
	{
		$output = &runL4FarmServerDelete( $ids, $farm_name );
	}

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		$output = &runHTTPFarmServerDelete( $ids, $farm_name, $service );
	}

	if ( $farm_type eq "gslb" )
	{
		$output = &runGSLBFarmServerDelete( $ids, $farm_name, $service );
	}

	return $output;
}

#
sub getFarmBackendStatusCtl    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my @output;

	if ( $farm_type eq "tcp" || $farm_type eq "udp" )
	{
		@output = &getTcpUdpFarmBackendStatusCtl( $farm_name );
	}

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		@output = &getHTTPFarmBackendStatusCtl( $farm_name );
	}

	if ( $farm_type eq "datalink" )
	{
		@output = &getDatalinkFarmBackendStatusCtl( $farm_name );
	}

	if ( $farm_type eq "l4xnat" )
	{
		@output = &getL4FarmBackendStatusCtl( $farm_name );
	}

	return @output;
}

#function that return the status information of a farm:
#ip, port, backendstatus, weight, priority, clients
sub getFarmBackendsStatus    # ($farm_name,@content)
{
	my ( $farm_name, @content ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my @output;

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		@output = &getHTTPFarmBackendsStatus( $farm_name, @content );
	}

	if ( $farm_type eq "tcp" || $farm_type eq "udp" )
	{
		@output = &getTcpUdpFarmBackendsStatus( $farm_name, @content );
	}

	if ( $farm_type eq "datalink" )
	{
		@output = &getDatalinkFarmBackendsStatus( @content );
	}

	if ( $farm_type eq "l4xnat" )
	{
		@output = &getL4FarmBackendsStatus( $farm_name, @content );
	}

	return @output;
}

#function that return the status information of a farm:
sub getFarmBackendsClients    # ($idserver,@content,$farm_name)
{
	my ( $idserver, @content, $farm_name ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my $output    = -1;

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		$output = &getHTTPFarmBackendsClients( $idserver, @content, $farm_name );
	}

	if ( $farm_type eq "tcp" || $farm_type eq "udp" )
	{
		$output = &getTcpUdpFarmBackendsClients( $idserver, @content, $farm_name );
	}
	return $output;
}

#function that return the status information of a farm:
sub getFarmBackendsClientsList    # ($farm_name,@content)
{
	my ( $farm_name, @content ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my @output;

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		@output = &getHTTPFarmBackendsClientsList( $farm_name, @content );
	}

	if ( $farm_type eq "tcp" || $farm_type eq "udp" )
	{
		@output = &getTcpUdpFarmBackendsClientsList( $farm_name, @content );
	}

	return @output;
}

sub setFarmBackendStatus    # ($farm_name,$index,$stat)
{
	my ( $farm_name, $index, $stat ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $farm_type     = &getFarmType( $farm_name );

	#	my $output = -1;

	if ( $farm_type eq "datalink" )
	{
		$output = &setDatalinkFarmBackendStatus( $farm_name, $index, $stat );
	}

	if ( $farm_type eq "l4xnat" )
	{
		$output = &setL4FarmBackendStatus( $farm_name, $index, $stat );
	}

	#	return $output;
}

#function that renames a farm
sub setNewFarmName    # ($farm_name,$new_farm_name)
{
	my ( $farm_name, $new_farm_name ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my $output    = -1;

	if ( $new_farm_name =~ /^$/ )
	{
		&logfile( "error 'NewFarmName $new_farm_name' is empty" );
		return -2;
	}

	&logfile(
			  "setting 'NewFarmName $new_farm_name' for $farm_name farm $farm_type" );

	if ( $farm_type eq "tcp" || $farm_type eq "udp" )
	{
		$output = &setTcpUdpNewFarmName( $farm_name, $new_farm_name );
	}

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		$output = &setHTTPNewFarmName( $farm_name, $new_farm_name );
	}

	if ( $farm_type eq "datalink" )
	{
		$output = &setDatalinkNewFarmName( $farm_name, $new_farm_name );
	}

	if ( $farm_type eq "l4xnat" )
	{
		$output = &setL4NewFarmName( $farm_name, $new_farm_name );
	}

	if ( $farm_type eq "gslb" )
	{
		$output = &setGSLBNewFarmName( $farm_name, $new_farm_name );
	}

	# rename rrd
	rename ( "$rrdap_dir$rrd_dir/$farm_name-farm.rrd",
			 "$rrdap_dir$rrd_dir/$new_farm_name-farm.rrd" );

	# delete old graphs
	unlink ( "img/graphs/bar$farm_name.png" );

	# FIXME: farmguardian files
	# FIXME: logfiles
	return $output;
}

#function that check if the config file is OK.
sub getFarmConfigIsOK    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my $output    = -1;

	if ( $farm_type eq "http" || $farm_type eq "https" )
	{
		$output = &getHTTPFarmConfigIsOK( $farm_name );
	}
	if ( $farm_type eq "gslb" )
	{
		$output = &getGSLBFarmConfigIsOK( $farm_name );
	}

	return $output;
}

#function that check if a backend on a farm is on maintenance mode
sub getFarmBackendMaintenance    # ($farm_name,$backend,$service)
{
	my ( $farm_name, $backend, $service ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my $output    = -1;

	if ( $farm_type eq "tcp" || $farm_type eq "udp" )
	{
		$output = &getTcpUdpFarmBackendMaintenance( $farm_name, $backend );
	}
	elsif ( $farm_type eq "http" || $farm_type eq "https" )
	{
		$output = &getHTTPFarmBackendMaintenance( $farm_name, $backend, $service );
	}
	elsif ( $farm_type eq "l4xnat" )
	{
		$output = &getL4FarmBackendMaintenance( $farm_name, $backend );
	}

	return $output;
}

#function that enable the maintenance mode for backend
sub setFarmBackendMaintenance    # ($farm_name,$backend,$service)
{
	my ( $farm_name, $backend, $service ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my $output    = -1;

	if ( $farm_type eq "tcp" || $farm_type eq "udp" )
	{
		$output = &setTcpUdpFarmBackendMaintenance( $farm_name, $backend );
	}
	elsif ( $farm_type eq "http" || $farm_type eq "https" )
	{
		$output = &setHTTPFarmBackendMaintenance( $farm_name, $backend, $service );
	}
	elsif ( $farm_type eq "l4xnat" )
	{
		$output = &setL4FarmBackendMaintenance( $farm_name, $backend );
	}

	return $output;
}

#function that disable the maintenance mode for backend
sub setFarmBackendNoMaintenance    # ($farm_name,$backend,$service)
{
	my ( $farm_name, $backend, $service ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my $output    = -1;

	if ( $farm_type eq "tcp" || $farm_type eq "udp" )
	{
		$output = &setTcpUdpFarmBackendNoMaintenance( $farm_name, $backend );
	}
	elsif ( $farm_type eq "http" || $farm_type eq "https" )
	{
		$output = &setHTTPFarmBackendNoMaintenance( $farm_name, $backend, $service );
	}
	elsif ( $farm_type eq "l4xnat" )
	{
		$output = &setL4FarmBackendNoMaintenance( $farm_name, $backend );
	}

	return $output;
}

# Generic function
#checks thata farmname has correct characters (number, letters and lowercases)
sub checkFarmnameOK    # ($farm_name)
{
	my $farm_name = shift;

	return ( $farm_name =~ /^[a-zA-Z0-9\-]*$/ )
	  ? 0
	  : -1;
}

#function that return indicated value from a HTTP Service
#vs return virtual server
sub getFarmVS    # ($farm_name, $service, $tag)
{
	my ( $farm_name, $service, $tag ) = @_;

	my $output    = "";
	my $farm_type = &getFarmType( $farm_name );

	if ( $farm_type =~ /http/ )
	{
		$output = &getHTTPFarmVS( $farm_name, $service, $tag );
	}
	elsif ( $farm_type eq "gslb" )
	{
		$output = &getGSLBFarmVS( $farm_name, $service, $tag );
	}

	return $output;
}

#set values for a service
sub setFarmVS    # ($farm_name,$service,$tag,$string)
{
	my ( $farm_name, $service, $tag, $string ) = @_;

	my $output    = "";
	my $farm_type = &getFarmType( $farm_name );

	if ( $farm_type =~ /http/ )
	{
		$output = &setHTTPFarmVS( $farm_name, $service, $tag, $string );
	}
	elsif ( $farm_type eq "gslb" )
	{
		$output = &setGSLBFarmVS( $farm_name, $service, $tag, $string );
	}

	return @output;
}

sub setFarmName    # ($farm_name)
{
	$farm_name =~ s/[^a-zA-Z0-9]//g;
}

# do not remove this
1
