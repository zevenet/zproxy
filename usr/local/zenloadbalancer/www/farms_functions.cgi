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

if ( -e "/usr/local/zenloadbalancer/www/farms_functions_ext.cgi" )
{
	require "/usr/local/zenloadbalancer/www/farms_functions_ext.cgi";
}

require "/usr/local/zenloadbalancer/www/rrd_functions.cgi";
require "/usr/local/zenloadbalancer/www/http_functions.cgi";

my $configdir = &getGlobalConfiguration('configdir');


=begin nd
Function: setFarmBlacklistTime

	Configure check time for resurected back-end. It is a farm paramter.
	
Parameters:
	checktime - time for resurrected checks
	farmname - Farm name

Returns:
	Integer - Error code: 0 on success, or -1 on failure.

=cut
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


=begin nd
Function: getFarmBlacklistTime

	Return  time for resurrected checks for a farm.
	
Parameters:
	farmname - Farm name

Returns:
	integer - seconds for check or -1 on failure.

=cut
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


=begin nd
Function: setFarmSessionType

	Configure type of persistence
	
Parameters:
	session - type of session: nothing, HEADER, URL, COOKIE, PARAM, BASIC or IP, for HTTP farms; none or ip, for l4xnat farms
	farmname - Farm name

Returns:
	Integer - Error code: 0 on success, or -1 on failure.

=cut
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


=begin nd
Function: getFarmSessionType

	Return the type of session persistence for a farm.
	
Parameters:
	farmname - Farm name

Returns:
	scalar - type of persistence or -1 on failure.

=cut
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


=begin nd
Function: setFarmTimeout

	Asign a timeout value to a farm
	
Parameters:
	timeout - Time out in seconds
	farmname - Farm name

Returns:
	Integer - Error code: 0 on success, or -1 on failure.

=cut
sub setFarmTimeout    # ($timeout,$farm_name)
{
	my ( $timeout, $farm_name ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my $output    = -1;

	&zenlog( "setting 'Timeout $timeout' for $farm_name farm $farm_type" );

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


=begin nd
Function: getFarmTimeout

	Return the farm time out
	
Parameters:
	farmname - Farm name

Returns:
	Integer - Return time out, or -1 on failure.

=cut
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


=begin nd
Function: setFarmAlgorithm

	Set the load balancing algorithm to a farm
	
Parameters:
	algorithm - Type of balancing mode
	farmname - Farm name

Returns:
	none - .
	
FIXME:
	set a return value, and do error control
	
=cut
sub setFarmAlgorithm    # ($algorithm,$farm_name)
{
	my ( $algorithm, $farm_name ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my $output    = -1;

	&zenlog( "setting 'Algorithm $algorithm' for $farm_name farm $farm_type" );

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


=begin nd
Function: getFarmAlgorithm

	Get type of balancing algorithm. 
	
Parameters:
	farmname - Farm name

Returns:
	scalar - return a string with type of balancing algorithm or -1 on failure
	
=cut
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


=begin nd
Function: setFarmPersistence

	Set client persistence to a farm
	
Parameters:
	persistence - Type of persitence
	farmname - Farm name

Returns:
	scalar - Error code: 0 on success or -1 on failure
	
BUG:
	Obsolet, only used in tcp farms
	
=cut
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


=begin nd
Function: getFarmPersistence

	Get type of persistence session for a farm
	
Parameters:
	farmname - Farm name

Returns:
	Scalar - persistence type or -1 on failure
	
BUG
	DUPLICATED, use for l4 farms getFarmSessionType
	obsolete for tcp farms
	
=cut
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


=begin nd
Function: setFarmMaxClientTime

	Set the maximum time for a client
	
Parameters:
	maximumTO - Maximum client time
	farmname - Farm name

Returns:
	Integer - Error code: 0 on success, or -1 on failure.

=cut
sub setFarmMaxClientTime    # ($max_client_time,$track,$farm_name)
{
	my ( $max_client_time, $track, $farm_name ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my $output    = -1;

	&zenlog(
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


=begin nd
Function: getFarmMaxClientTime

	Return the maximum time for a client
	
Parameters:
	farmname - Farm name

Returns:
	Integer - Return maximum time, or -1 on failure.

=cut
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


=begin nd
Function: setFarmMaxConn

	set the max conn of a farm
	
Parameters:
	maxiConns - Maximum number of allowed connections
	farmname - Farm name

Returns:
	Integer - always return 0

BUG:
	Not used in zapi v3. It is used "setFarmMaxClientTime"

=cut
sub setFarmMaxConn    # ($max_connections,$farm_name)
{
	my ( $max_connections, $farm_name ) = @_;

	my $farm_type     = &getFarmType( $farm_name );
	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;

	&zenlog( "setting 'MaxConn $max_connections' for $farm_name farm $farm_type" );

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


=begin nd
Function: getFarmServers

	List all farm backends and theirs configuration
	
Parameters:
	farmname - Farm name

Returns:
	array - list of backends
		
FIXME:
	changes output to hash format
	
=cut
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
		@servers = &getDatalinkFarmServers( $farm_name );
	}

	if ( $farm_type eq "l4xnat" )
	{
		@servers = &getL4FarmServers( $farm_name );
	}

	return @servers;
}


=begin nd
Function: getFarmGlobalStatus

	[NOT USED] Get the status of a farm and its backends
	
Parameters:
	farmname - Farm name

Returns:
	array - ???

BUG:
	NOT USED
	
=cut
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


=begin nd
Function: getBackendEstConns

	Get all ESTABLISHED connections for a backend
	 
Parameters:
	farmname - Farm name
	ip_backend - IP backend
	port_backend - backend port
	netstat - Conntrack -L output

Returns:
	array - Return all ESTABLISHED conntrack lines for the backend
	
=cut
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


=begin nd
Function: getFarmEstConns

	Get all ESTABLISHED connections for a farm
	 
Parameters:
	farmname - Farm name
	netstat - Conntrack -L output

Returns:
	array - Return all ESTABLISHED conntrack lines for a farm

=cut
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

	if ( $farm_type eq "gslb" )
	{
		@nets = &getGSLBFarmEstConns( $farm_name, @netstat );
	}

	return @nets;
}


=begin nd
Function: getBackendSYNConns

	Get all SYN connections for a backend
	 
Parameters:
	farmname - Farm name
	ip_backend - IP backend
	port_backend - backend port
	netstat - Conntrack -L output

Returns:
	array - Return all SYN conntrack lines for a backend of a farm

=cut
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


=begin nd
Function: getFarmSYNConns

	Get all SYN connections for a farm
	 
Parameters:
	farmname - Farm name
	netstat - Conntrack -L output

Returns:
	array - Return all SYN conntrack lines for a farm

=cut
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


=begin nd
Function: getFarmsByType

	Get all farms of a type 
	 
Parameters:
	type - Farm type. The available options are "http", "https", "datalink", "l4xnat" or "gslb"

Returns:
	Array - List of farm name of a type

NOTE:
	Generic function

=cut
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


=begin nd
Function: getFarmType

	Get the farm type for a farm
	 
Parameters:
	farmname - Farm name

Returns:
	String - "http", "https", "datalink", "l4xnat", "gslb" or 1 on failure

NOTE:
	Generic function
	
=cut
sub getFarmType    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );

	if ( $farm_filename =~ /^$farm_name\_pen\_udp.cfg/ )
	{
		return "udp";
	}
	if ( $farm_filename =~ /^$farm_name\_pen.cfg/ )
	{
		return "tcp";
	}
	if ( $farm_filename =~ /^$farm_name\_pound.cfg/ )
	{
		use File::Grep qw( fgrep );
		if ( fgrep { /ListenHTTPS/ } "$configdir/$farm_filename" )
		{
			return "https";
		}
		else
		{
			return "http";
		}
	}
	if ( $farm_filename =~ /^$farm_name\_datalink.cfg/ )
	{
		return "datalink";
	}
	if ( $farm_filename =~ /^$farm_name\_l4xnat.cfg/ )
	{
		return "l4xnat";
	}
	if ( $farm_filename =~ /^$farm_name\_gslb.cfg/ )
	{
		return "gslb";
	}
	return 1;
}


=begin nd
Function: getFarmType

	Returns farm file name
	 
Parameters:
	farmname - Farm name

Returns:
	String - file name or -1 on failure
	
NOTE:
	Generic function

=cut
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


=begin nd
Function: getFarmType

	Return farm status checking if pid file exists
	 
Parameters:
	farmname - Farm name

Returns:
	String - "down", "up" or -1 on failure

NOTE:
	Generic function
		
=cut
sub getFarmStatus    # ($farm_name)
{
	my $farm_name = shift;

	my $output = -1;
	return $output if !defined ( $farm_name );    # farm name cannot be empty

	my $farm_type = &getFarmType( $farm_name );
	my $piddir = &getGlobalConfiguration('piddir');

	# for every farm type but datalink or l4xnat
	if ( $farm_type ne "datalink" && $farm_type ne "l4xnat" )
	{
		my $pid = &getFarmPid( $farm_name );
		my $running_pid;
		$running_pid = kill ( 0, $pid ) if $pid ne "-";

		if ( $pid ne "-" && $running_pid )
		{
			$output = "up";
		}
		else
		{
			if ( $pid ne "-" && !$running_pid )
			{
				unlink &getGSLBFarmPidFile( $farm_name ) if ( $farm_type eq 'gslb' );
				unlink "$piddir\/$farm_name\_pound.pid"  if ( $farm_type =~ /http/ );
			}

			$output = "down";
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


=begin nd
Function: getFarmBootStatus

	Return the farm status at boot zevenet
	 
Parameters:
	farmname - Farm name

Returns:
	scalar - return "down" if the farm not run at boot or "up" if the farm run at boot

=cut
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


=begin nd
Function: _runFarmStart

	Run a farm
	
Parameters:
	farmname - Farm name
	writeconf - write this change in configuration status "true" or omit it "false"

Returns:
	Integer - return 0 on success or different of 0 on failure
	
=cut
sub _runFarmStart    # ($farm_name, $writeconf)
{
	my ( $farm_name, $writeconf ) = @_;

	my $status = -1;

	# finish the function if the tarm is already up
	if ( &getFarmStatus( $farm_name ) eq "up" )
	{
		zenlog("Farm $farm_name already up");
		return 0;
	}

	my $farm_type     = &getFarmType( $farm_name );
	my $farm_filename = &getFarmFile( $farm_name );

	&zenlog( "running 'Start write $writeconf' for $farm_name farm $farm_type" );

	if (    $writeconf eq "true"
		 && $farm_type ne "datalink"
		 && $farm_type ne "l4xnat"
		 && $farm_type ne "gslb" )
	{
		use Tie::File;
		tie my @configfile, 'Tie::File', "$configdir\/$farm_filename";
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


=begin nd
Function: runFarmStart

	Run a farm completely a farm. Run farm, its farmguardian and ipds rules
	
Parameters:
	farmname - Farm name
	writeconf - write this change in configuration status "true" or omit it "false"

Returns:
	Integer - return 0 on success or different of 0 on failure

NOTE:
	Generic function
	
=cut
sub runFarmStart    # ($farm_name,$writeconf)
{
	my ( $farm_name, $writeconf ) = @_;

	my $status = &_runFarmStart( $farm_name, $writeconf );

	if ( $status == 0 )
	{
		&runFarmGuardianStart( $farm_name, "" );
	}

	# run ipds rules
	require "/usr/local/zenloadbalancer/www/blacklists.cgi";
	require "/usr/local/zenloadbalancer/www/dos.cgi";
	my $ipds = &getIPDSfarmsRules( $farm_name );
	foreach my $list ( @{ $ipds->{ 'blacklists' } } )
	{
		&setBLCreateRule ( $farm_name, $list );
	}
	foreach my $rule ( @{ $ipds->{ 'dos' } } )
	{
		&setDOSRunRule( $rule, $farm_name );
	}

	return $status;
}


=begin nd
Function: runFarmStop

	Stop a farm completely a farm. Stop the farm, its farmguardian and ipds rules
	
Parameters:
	farmname - Farm name
	writeconf - write this change in configuration status "true" or omit it "false"

Returns:
	Integer - return 0 on success or different of 0 on failure

NOTE:
	Generic function
		
=cut
sub runFarmStop    # ($farm_name,$writeconf)
{
	my ( $farm_name, $writeconf ) = @_;

	# stop ipds rules
	require "/usr/local/zenloadbalancer/www/blacklists.cgi";
	require "/usr/local/zenloadbalancer/www/dos.cgi";
	my $ipds = &getIPDSfarmsRules( $farm_name );
	foreach my $list ( @{ $ipds->{ 'blacklists' } } )
	{
		&setBLDeleteRule ( $farm_name, $list );
	}
	foreach my $rule ( @{ $ipds->{ 'dos' } } )
	{
		&setDOSStopRule( $rule, $farm_name );
	}

	&runFarmGuardianStop( $farm_name, "" );

	my $status = &_runFarmStop( $farm_name, $writeconf );
	
	return $status;
}


=begin nd
Function: _runFarmStop

	Stop a farm
	
Parameters:
	farmname - Farm name
	writeconf - write this change in configuration status "true" or omit it "false"

Returns:
	Integer - return 0 on success or different of 0 on failure
	
=cut
sub _runFarmStop    # ($farm_name,$writeconf)
{
	my ( $farm_name, $writeconf ) = @_;

	my $status = &getFarmStatus( $farm_name );
	if ( $status eq "down" )
	{
		return 0;
	}

	my $farm_filename = &getFarmFile( $farm_name );
	if ( $farm_filename eq '-1' )
	{
		return -1;
	}

	my $farm_type = &getFarmType( $farm_name );
	$status = $farm_type;

	&zenlog( "running 'Stop write $writeconf' for $farm_name farm $farm_type" );

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


=begin nd
Function: runFarmCreate

	Create a farm
	
Parameters:
	type - Farm type. The available options are: "http", "https", "datalink", "l4xnat" or "gslb"
	vip - Virtual IP where the virtual service is listening
	port - Virtual port where the virtual service is listening
	farmname - Farm name
	type - Specify if farm is HTTP or HTTPS
	iface - Inteface wich uses the VIP. This parameter is only used in datalink farms

Returns:
	Integer - return 0 on success or different of 0 on failure
		
FIXME:
	Use hash to pass the parameters
		
=cut
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

	&zenlog( "running 'Create' for $farm_name farm $farm_type" );

	if ( $farm_type =~ /^TCP$/i )
	{
		$output = &runTcpFarmCreate( $vip, $vip_port, $farm_name );
	}

	if ( $farm_type =~ /^UDP$/i )
	{
		$output = &runUdpFarmCreate( $vip, $vip_port, $farm_name );
	}

	if ( $farm_type =~ /^HTTP[S]?$/i )
	{
		$output = &runHTTPFarmCreate( $vip, $vip_port, $farm_name, $farm_type );
	}

	if ( $farm_type =~ /^DATALINK$/i )
	{
		$output = &runDatalinkFarmCreate( $farm_name, $vip, $fdev );
	}

	if ( $farm_type =~ /^L4xNAT$/i )
	{
		$output = &runL4FarmCreate( $vip, $farm_name, $vip_port );
	}

	if ( $farm_type =~ /^GSLB$/i )
	{
		$output = &runGSLBFarmCreate( $vip, $vip_port, $farm_name );
	}

	return $output;
}


=begin nd
Function: getFarmMaxConn

	Returns farm max connections
	
Parameters:
	none - .

Returns:
	Integer - always return 0
	
BUG:
	It is only used in tcp, for http farms profile does nothing
		
=cut
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


=begin nd
Function: getFarmPort

	Returns farm port
	
Parameters:
	farmname - Farm name

Returns:
	Integer - port of farm or -1 on failure

BUG:
	Only it is used by tcp farms
	DUPLICATE function. Use "getFarmVip" 
	for http profile, return error response
				
=cut
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

	if ( $farm_type eq "l4xnat" )
	{
		$output = &getL4FarmVip( 'vipp', $farm_name );
	}

	if ( $farm_type eq "gslb" )
	{
		$output = &getGSLBFarmVip( 'vipp', $farm_name );
	}

	if ( $farm_type eq "datalink" )
	{
		$output = &getDatalinkFarmVip( 'vipp', $farm_name );
	}

	return $output;
}


=begin nd
Function: getFarmProto

	Return basic transport protocol used by the farm protocol
		
Parameters:
	farmname - Farm name

Returns:
	String - "udp" or "tcp"
	
BUG:
	Gslb works with tcp protocol too
	
FIXME:
	Use getL4ProtocolTransportLayer to get l4xnat protocol
	
=cut
sub getFarmProto    # ($farm_name)
{
	my $farm_name = shift;

	my $farm_type     = &getFarmType( $farm_name );
	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;

	if ( $farm_type eq "l4xnat" )
	{
		open FI, "<", "$configdir/$farm_filename";
		my $first = "true";
		while ( my $line = <FI> )
		{
			if ( $line ne "" && $first eq "true" )
			{
				$first = "false";
				my @line = split ( "\;", $line );
				$output = $line[1];
			}
		}
		close FI;
	}
	
	elsif ( $farm_type eq "gslb" )
	{
		$output = "UDP";
	}
	
	elsif ( $farm_type =~ /http/i )
	{
		$output = "TCP";
	}

	return $output;
}


=begin nd
Function: getFarmPid

	Returns farm PID
		
Parameters:
	farmname - Farm name

Returns:
	Integer - return pid of farm, '-' if pid not exist or -1 on failure
			
=cut
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


=begin nd
Function: getFarmVip

	Returns farm vip or farm port
		
Parameters:
	tag - requested parameter. The options are "vip" for virtual ip or "vipp" for virtual port
	farmname - Farm name

Returns:
	Scalar - return vip or port of farm or -1 on failure
	
FIXME
	vipps parameter is only used in tcp farms. Soon this parameter will be obsolete
			
=cut
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


=begin nd
Function: getFarmLock

	Check if a farm is locked. A farm locked need to restart. 
		
Parameters:
	farmname - Farm name

Returns:
	Scalar - Return content of lock file if it is locked or -1 the farm is not locked

NOTE:
	Generic function
		
=cut
sub getFarmLock    # ($farm_name)
{
	my $farm_name = shift;
	my $output = -1;
	my $lockfile = "/tmp/$farm_name.lock";

	if ( -e "$lockfile" )
	{
		open FILE, "$lockfile";
		read FILE, $output, 255;
		close FILE;
	}

	return $output;

}


=begin nd
Function: setFarmLock

	Set the lock status to "on" or "off"
	If the new status in "on" it's possible to set a message inside
		
Parameters:
	farmname - Farm name
	status - This parameter can value "on" or "off"
	message - Text for lock file

Returns:
	Integer - Always return 0
	
FIXME:
	always return 0

NOTE:
	Generic function
	
=cut
sub setFarmLock    # ($farm_name, $status, $msg)
{
	my ( $farm_name, $status, $msg ) = @_;
	my $output = 0;
	my $lockfile = "/tmp/$farm_name.lock";
	my $lockstatus = &getFarmLock( "$farm_name" );

	if ( $status eq "on" && $lockstatus == -1 )
	{
		open FD, ">$lockfile";
		print FD "$msg";
		close FD;
	}

	if ( $status eq "off" )
	{
		unlink ( "$lockfile" ) if -e "$lockfile";
	}

	return $output;
}


=begin nd
Function: setFarmRestart

	This function creates a file to tell that the farm needs to be restarted to apply changes
		
Parameters:
	farmname - Farm name

Returns:
	undef
	
NOTE:
	Generic function
	
=cut
sub setFarmRestart    # ($farm_name)
{
	my $farm_name = shift;

	# do nothing if the farm is not running
	return if &getFarmStatus( $farm_name ) ne 'up';

	&setFarmLock( $farm_name, "on" );
}


=begin nd
Function: setFarmNoRestart

	This function deletes the file marking the farm to be restarted to apply changes
		
Parameters:
	farmname - Farm name

Returns:
	none - .
	
NOTE:
	Generic function
	
=cut
sub setFarmNoRestart    # ($farm_name)
{
	my $farm_name = shift;

	&setFarmLock( $farm_name, "off");
}


=begin nd
Function: getFarmList

	Returns farms configuration filename list
		
Parameters:
	none - .

Returns:
	Array - List of configuration files
	
NOTE:
	Generic function
	
=cut
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


=begin nd
Function: getFarmName

	Returns farms configuration filename list
		
Parameters:
	file - Farm file

Returns:
	String - farm name
	
NOTE:
	Generic function
	
=cut
sub getFarmName    # ($farm_filename)
{
	my $farm_filename = shift;

	my @filename_split = split ( "_", $farm_filename );

	return $filename_split[0];
}


=begin nd
Function: runFarmDelete

	Delete a farm
		
Parameters:
	farmname - Farm name

Returns:
	String - farm name
	
NOTE:
	Generic function
	
=cut
sub runFarmDelete    # ($farm_name)
{
	my $farm_name = shift;

	# global variables
	my $basedir = &getGlobalConfiguration('basedir');
	my $configdir = &getGlobalConfiguration('configdir');
	my $rrdap_dir = &getGlobalConfiguration('rrdap_dir');
	my $logdir = &getGlobalConfiguration('logdir');
	my $rrd_dir = &getGlobalConfiguration('rrd_dir');
	
	#delete IPDS rules
	require "/usr/local/zenloadbalancer/www/blacklists.cgi";
	require "/usr/local/zenloadbalancer/www/dos.cgi";
	my $ipds = &getIPDSfarmsRules( $farm_name );
	# delete black lists
	foreach my $listName ( @{$ipds->{'blacklists'}} )
	{ 
		&setBLRemFromFarm( $farm_name, $listName );
	}
	# delete dos rules
	foreach my $dos ( @{$ipds->{'dos'}} )
	{ 
		&setDOSDeleteRule( $dos, $farm_name );
	}
	
	
	my $farm_type = &getFarmType( $farm_name );
	my $status = 1;

	&zenlog( "running 'Delete' for $farm_name" );

	if ( $farm_type eq "gslb" )
	{
		use File::Path 'rmtree';
		$status = 0
		  if rmtree( ["$configdir/$farm_name\_gslb.cfg"] );
	}
	else
	{
		$status = 0
		  if unlink glob ( "$configdir/$farm_name\_*\.cfg" );

		if ( $farm_type eq "http" || $farm_type eq "https" )
		{
			unlink glob ( "$configdir/$farm_name\_*\.html" );

			# For HTTPS farms only
			my $dhfile = "$configdir\/$farm_name\_dh2048.pem";
			unlink ( "$dhfile" ) if -e "$dhfile";
		}
		elsif ( $farm_type eq "datalink" )
		{
			# delete cron task to check backends
			use Tie::File;
			tie my @filelines, 'Tie::File', "/etc/cron.d/zenloadbalancer";
			@filelines = grep !/\# \_\_$farm_name\_\_/, @filelines;
			untie @filelines;
		}
		elsif ( $farm_type eq "l4xnat" )
		{
			# delete nf marks
			delMarks( $farm_name, "" );
		}
	}

	unlink glob ( "$configdir/$farm_name\_*\.conf" );
	unlink glob ( "${logdir}/${farm_name}\_*farmguardian*" );
	
	&delGraph( $farm_name, "farm" );
	
	return $status;
}


=begin nd
Function: setFarmVirtualConf

	Set farm virtual IP and virtual PORT		
	
Parameters:
	vip - virtual ip
	port - virtual port
	farmname - Farm name

Returns:
	Integer - return 0 on success or other value on failure
	
=cut
sub setFarmVirtualConf    # ($vip,$vip_port,$farm_name)
{
	my ( $vip, $vip_port, $farm_name ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my $stat      = -1;

	&zenlog(
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


=begin nd
Function: setFarmServer

	Add a new Backend
	
Parameters:
	id - Backend id, if this id doesn't exist, it will create a new backend
	ip - Real server ip
	port | iface - Real server port or interface if the farm is datalink
	max - parameter for tcp farm
	weight - The higher the weight, the more request will go to this backend.
	priority -  The lower the priority, the most preferred is the backend.
	timeout - HTTP farm parameter
	farmname - Farm name
	service - service name. For HTTP farms

Returns:
	Scalar - Error code: undef on success or -1 on error 
	
FIXME:
	Use a hash
	max parameter is only used by tcp farms
		
=cut
sub setFarmServer # $output ($ids,$rip,$port|$iface,$max,$weight,$priority,$timeout,$farm_name,$service)
{
	my (
		 $ids,      $rip,     $port,      $max, $weight,
		 $priority, $timeout, $farm_name, $service
	) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my $output    = -1;

	&zenlog(
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
		$output = &setL4FarmServer( $ids, $rip, $port, $weight, $priority, $farm_name, $max );
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


=begin nd
Function: runFarmServerDelete

	Delete a Backend
	
Parameters:
	id - Backend id, if this id doesn't exist, it will create a new backend
	farmname - Farm name
	service - service name. For HTTP farms

Returns:
	Scalar - Error code: undef on success or -1 on error 
			
=cut
sub runFarmServerDelete    # ($ids,$farm_name,$service)
{
	my ( $ids, $farm_name, $service ) = @_;

	my $farm_type = &getFarmType( $farm_name );
	my $output    = -1;

	&zenlog( "running 'ServerDelete $ids' for $farm_name farm $farm_type" );

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


=begin nd
Function: getFarmBackendStatusCtl

	get information about status and configuration of backend
	
Parameters:
	farmname - Farm name

Returns:
	Array - Each profile has a different output format
			
=cut
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


=begin nd

Function: getFarmBackendStatus

	Get processed information about status and configuration of backends
	
Parameters:
	farmname - Farm name
	content - Raw backend info

Returns:
	Array - List of backend. Each profile has a different output format 
	
FIXME:
	1. Always is called getFarmBackendStatusCtl function before this function, to pass @content array, then will be useful for avoid bugs call getFarmBackendStatusCtl inside this function.
	Better, call getHTTPFarmBackendStatusCtl inside that getHTTPFarmBackendsStatus function, so it is not necessary work with @content variable
	2. Return a hash
	
=cut
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


=begin nd

Function: getFarmBackendsClients

	Function that return the status information of sessions
	
Parameters:
	backend - Backend id
	content - Raw backend info
	farmname - Farm name

Returns:
	Integer - Number of clients with session in a backend or -1 on failure
	
FIXME: 
	used in zapi v2 and tcp farms
	
=cut
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


=begin nd

Function: getFarmBackendsClientsList

	Return session status of all backends of a farm
	
Parameters:
	content - Raw backend info
	farmname - Farm name

Returns:
	Array - The format for each line is: "service" . "\t" . "session_id" . "\t" . "session_value" . "\t" . "backend_id"
	
FIXME: 
	Same name than getFarmBackendsClients function but different uses
	
=cut
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


=begin nd
Function: setFarmBackendStatus

	Set backend status for a farm
		
Parameters:
	farmname - Farm name
	backend - Backend id
	status - Backend status. The possible values are: "up" or "down"

Returns:
	Integer - 0 on success or other value on failure
	
=cut
sub setFarmBackendStatus    # ($farm_name,$index,$stat)
{
	my ( $farm_name, $index, $stat ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $farm_type     = &getFarmType( $farm_name );

	my $output = -1;

	if ( $farm_type eq "datalink" )
	{
		$output = &setDatalinkFarmBackendStatus( $farm_name, $index, $stat );
	}

	if ( $farm_type eq "l4xnat" )
	{
		$output = &setL4FarmBackendStatus( $farm_name, $index, $stat );
	}

	return $output;
}


=begin nd
Function: setNewFarmName

	Function that renames a farm. Before call this function, stop the farm.
	
Parameters:
	farmname - Farm name
	newfarmname - New farm name

Returns:
	Integer - return 0 on success or -1 on failure
		
=cut
sub setNewFarmName    # ($farm_name,$new_farm_name)
{
	my ( $farm_name, $new_farm_name ) = @_;

	my $rrdap_dir = &getGlobalConfiguration('rrdap_dir');
	my $rrd_dir = &getGlobalConfiguration('rrd_dir');

	my $farm_type = &getFarmType( $farm_name );
	my $output    = -1;

	my @fg_files;
	my $fg_status;
	my $farm_status;

	# farmguardian renaming
	if ( $farm_type =~ /http/ )
	{
		opendir ( my $dir, "$configdir" );
		@fg_files = grep { /^$farm_name\_.+guardian\.conf/ } readdir ( $dir );
		closedir $dir;
	}
	elsif ( $farm_type =~ /l4xnat|tcp|udp/ )
	{
		$fg_files[0] = &getFarmGuardianFile( $farm_name );
		&zlog( "found farmguardian file:@fg_files" ) if &debug;
	}

	if ( @fg_files )
	{
		$fg_status = &getFarmGuardianStatus( $farm_name ) if @fg_files;
		$farm_status = &getFarmStatus( $farm_name );

		if ( $fg_status == 1 && $farm_status eq 'up' )
		{
			&zlog( "stopping farmguardian" ) if &debug;
			&runFarmGuardianStop( $farm_name );
		}
	}

	# end of farmguardian renaming

	&zenlog(
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

	# farmguardian renaming
	if ( $output == 0 && @fg_files )
	{
		foreach my $filename ( @fg_files )
		{
			my $new_filename = $filename;
			$new_filename =~ s/$farm_name/$new_farm_name/;

			&zlog( "renaming $filename =>> $new_filename" ) if &debug;
			rename ( "$configdir/$filename", "$configdir/$new_filename" );

			#~ TODO: rename farmguardian logs
		}

		if ( $fg_status == 1 && $farm_status eq 'up' )
		{
			&zlog( "restarting farmguardian" ) if &debug;
			&runFarmGuardianStart( $new_farm_name );
		}
	}

	# end of farmguardian renaming

	# rename rrd
	rename ( "$rrdap_dir/$rrd_dir/$farm_name-farm.rrd",
			 "$rrdap_dir/$rrd_dir/$new_farm_name-farm.rrd" );

	# delete old graphs
	unlink ( "img/graphs/bar$farm_name.png" );

	# FIXME: farmguardian files
	# FIXME: logfiles
	return $output;
}


=begin nd
Function: getFarmConfigIsOK

	Function that check if the config file is OK.
	
Parameters:
	farmname - Farm name

Returns:
	scalar - return 0 on success or different on failure
		
=cut
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


=begin nd
Function: getFarmBackendMaintenance

	Function that check if a backend on a farm is on maintenance mode
	
Parameters:
	farmname - Farm name
	backend - Backend id
	service - Service name

Returns:
	scalar - if backend is in maintenance mode, return 0 else return -1
		
=cut
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


=begin nd
Function: setFarmBackendMaintenance

	Function that enable the maintenance mode for backend
	
Parameters:
	farmname - Farm name
	backend - Backend id
	service - Service name

Returns:
	Integer - return 0 on success or -1 on failure
		
=cut
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


=begin nd
Function: setFarmBackendNoMaintenance

	Function that disable the maintenance mode for backend
	
Parameters:
	farmname - Farm name
	backend - Backend id
	service - Service name

Returns:
	Integer - return 0 on success or -1 on failure
		
=cut
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


=begin nd
Function: checkFarmnameOK

	Checks the farmname has correct characters (number, letters and lowercases)
	
Parameters:
	farmname - Farm name

Returns:
	Integer - return 0 on success or -1 on failure
	
FIXME:
	Use check_function.cgi regexp
	
NOTE:
	Generic function
		
=cut
sub checkFarmnameOK    # ($farm_name)
{
	my $farm_name = shift;

	return ( $farm_name =~ /^[a-zA-Z0-9\-]+$/ )
	  ? 0
	  : -1;
}


=begin nd
Function: getFarmVS

	Return virtual server parameter
	
Parameters:
	farmname - Farm name
	service - Service name
	tag - Indicate which field will be returned

Returns:
	Integer - The requested parameter value

=cut
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


=begin nd
Function: setFarmVS

	Set values for service parameters
	
Parameters:
	farmname - Farm name
	service - Service name
	tag - Indicate which parameter modify
	string - value for the field "tag"

Returns:
	Integer - Error code: 0 on success or -1 on failure
		
=cut
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

	return $output;
}


=begin nd
Function: setFarmName

	Set values for service parameters
	
Parameters:
	farmname - Farm name

Returns:
	none - .
		
BUG:
	This function not return nothing. Farm name never will change. This function worked before with global variables. 
	Only it is used in zapi v2. Do this sentence in zapi v2 and remove function
		
=cut
sub setFarmName    # ($farm_name)
{
	my $farm_name = shift;
	$farm_name =~ s/[^a-zA-Z0-9]//g;
}


=begin nd
Function: getServiceStruct

	Get a struct with all parameters of a service
	
Parameters:
	farmname - Farm name
	service - Farm name

Returns:
	hash ref - It is a struct with all information about a farm service
	
FIXME: 
	Complete with more farm profiles.
	Use it in zapi to get services from a farm
		
=cut
sub getServiceStruct
{
	my ( $farmname, $service ) = @_;
	my $output;
	
	my $farm_type = &getFarmType( $farmname );
	if ( $farm_type =~ /http/ )
	{
		$output = &getHTTPServiceStruct( $farmname, $service );
	}
	else
	{
		$output = -1;
	}
	
	return $output;
}


1;
