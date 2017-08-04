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

my $configdir = &getGlobalConfiguration('configdir');

=begin nd
Function: setHTTPFarmServer

	Add a new backend to a HTTP service or modify if it exists
	
Parameters:
	ids - backend id
	rip - backend ip
	port - backend port
	priority - The priority of this backend (between 1 and 9). Higher priority backends will be used more often than lower priority ones
	timeout - Override the global time out for this backend
	farmname - Farm name
	service - service name

Returns:
	Integer - return 0 on success or -1 on failure
	
=cut
sub setHTTPFarmServer # ($ids,$rip,$port,$priority,$timeout,$farm_name,$service)
{
	my ( $ids, $rip, $port, $priority, $timeout, $farm_name, $service ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;

	tie my @contents, 'Tie::File', "$configdir\/$farm_filename";

	if ( $ids !~ /^$/ )
	{
		my $index_count = -1;
		my $i           = -1;
		my $sw          = 0;
		foreach my $line ( @contents )
		{
			$i++;

			#search the service to modify
			if ( $line =~ /Service \"$service\"/ )
			{
				$sw = 1;
			}
			if ( $line =~ /BackEnd/ && $line !~ /#/ && $sw eq 1 )
			{
				$index_count++;
				if ( $index_count == $ids )
				{
					#server for modify $ids;
					#HTTPS
					my $httpsbe = &getFarmVS( $farm_name, $service, "httpsbackend" );
					if ( $httpsbe eq "true" )
					{
						#add item
						$i++;
					}
					$output           = $?;
					$contents[$i + 1] = "\t\t\tAddress $rip";
					$contents[$i + 2] = "\t\t\tPort $port";
					my $p_m = 0;
					if ( $contents[$i + 3] =~ /TimeOut/ )
					{
						$contents[$i + 3] = "\t\t\tTimeOut $timeout";
						&zenlog( "Modified current timeout" );
					}
					if ( $contents[$i + 4] =~ /Priority/ )
					{
						$contents[$i + 4] = "\t\t\tPriority $priority";
						&zenlog( "Modified current priority" );
						$p_m = 1;
					}
					if ( $contents[$i + 3] =~ /Priority/ )
					{
						$contents[$i + 3] = "\t\t\tPriority $priority";
						$p_m = 1;
					}

					#delete item
					if ( $timeout =~ /^$/ )
					{
						if ( $contents[$i + 3] =~ /TimeOut/ )
						{
							splice @contents, $i + 3, 1,;
						}
					}
					if ( $priority =~ /^$/ )
					{
						if ( $contents[$i + 3] =~ /Priority/ )
						{
							splice @contents, $i + 3, 1,;
						}
						if ( $contents[$i + 4] =~ /Priority/ )
						{
							splice @contents, $i + 4, 1,;
						}
					}

					#new item
					if (
						 $timeout !~ /^$/
						 && (    $contents[$i + 3] =~ /End/
							  || $contents[$i + 3] =~ /Priority/ )
					  )
					{
						splice @contents, $i + 3, 0, "\t\t\tTimeOut $timeout";
					}
					if (
						    $p_m eq 0
						 && $priority !~ /^$/
						 && (    $contents[$i + 3] =~ /End/
							  || $contents[$i + 4] =~ /End/ )
					  )
					{
						if ( $contents[$i + 3] =~ /TimeOut/ )
						{
							splice @contents, $i + 4, 0, "\t\t\tPriority $priority";
						}
						else
						{
							splice @contents, $i + 3, 0, "\t\t\tPriority $priority";
						}
					}
				}
			}
		}
	}
	else
	{
		#add new server
		my $nsflag     = "true";
		my $index      = -1;
		my $backend    = 0;
		my $be_section = -1;

		foreach my $line ( @contents )
		{
			$index++;
			if ( $be_section == 1 && $line =~ /Address/ )
			{
				$backend++;
			}
			if ( $line =~ /Service \"$service\"/ )
			{
				$be_section++;
			}
			if ( $line =~ /#BackEnd/ && $be_section == 0 )
			{
				$be_section++;
			}
			if ( $be_section == 1 && $line =~ /#End/ )
			{
				splice @contents, $index, 0, "\t\tBackEnd";
				$output = $?;
				$index++;
				splice @contents, $index, 0, "\t\t\tAddress $rip";
				my $httpsbe = &getFarmVS( $farm_name, $service, "httpsbackend" );
				if ( $httpsbe eq "true" )
				{
					#add item
					splice @contents, $index, 0, "\t\t\tHTTPS";
					$index++;
				}
				$index++;
				splice @contents, $index, 0, "\t\t\tPort $port";
				$index++;

				#Timeout?
				if ( $timeout )
				{
					splice @contents, $index, 0, "\t\t\tTimeOut $timeout";
					$index++;
				}

				#Priority?
				if ( $priority )
				{
					splice @contents, $index, 0, "\t\t\tPriority $priority";
					$index++;
				}
				splice @contents, $index, 0, "\t\tEnd";
				$be_section = -1;
			}

			# if backend added then go out of form
		}
		if ( $nsflag eq "true" )
		{
			my $idservice = &getFarmVSI( $farm_name, $service );
			if ( $idservice ne "" )
			{
				&setHTTPFarmBackendStatusFile( $farm_name, $backend, "active", $idservice );
			}
		}
	}
	untie @contents;

	return $output;
}

=begin nd
Function: runHTTPFarmServerDelete

	Delete a backend in a HTTP service
	
Parameters:
	ids - backend id to delete it
	farmname - Farm name
	service - service name where is the backend

Returns:
	Integer - return 0 on success or -1 on failure
	
=cut
sub runHTTPFarmServerDelete    # ($ids,$farm_name,$service)
{
	my ( $ids, $farm_name, $service ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;
	my $i             = -1;
	my $j             = -1;
	my $sw            = 0;

	tie my @contents, 'Tie::File', "$configdir\/$farm_filename";

	foreach my $line ( @contents )
	{
		$i++;
		if ( $line =~ /Service \"$service\"/ )
		{
			$sw = 1;
		}
		if ( $line =~ /BackEnd/ && $line !~ /#/ && $sw == 1 )
		{
			$j++;
			if ( $j == $ids )
			{
				splice @contents, $i, 1,;
				$output = $?;
				while ( $contents[$i] !~ /End/ )
				{
					splice @contents, $i, 1,;
				}
				splice @contents, $i, 1,;
			}
		}
	}
	untie @contents;

	if ( $output != -1 )
	{
		&runRemoveHTTPBackendStatus( $farm_name, $ids, $service );
	}

	return $output;
}

=begin nd
Function: getHTTPFarmBackendStatusCtl

	Get status of a HTTP farm and its backends
	
Parameters:
	farmname - Farm name

Returns:
	array - return the output of poundctl command for a farm
	
=cut
sub getHTTPFarmBackendStatusCtl    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $poundctl = &getGlobalConfiguration('poundctl');

	return `$poundctl -c  /tmp/$farm_name\_pound.socket`;
}

=begin nd
Function: getHTTPFarmBackendsStatus

	Function that return the status information of a farm: ip, port, backend status, weight, priority, clients, connections and service
	
Parameters:
	farmname - Farm name
	content - command output where parsing backend status

Returns:
	array - backends_data, each line is: "id" . "\t" . "ip" . "\t" . "port" . "\t" . "status" . "\t-\t" . "priority" . "\t" . "clients" . "\t" . "connections" . "\t" . "service"
	usage - @backend = split ( '\t', $backend_data )
				backend[0] = id, 
				backend[1] = ip, 
				backend[2] = port, 
				backend[3] = status,
				backend[4] = -, 
				backend[5] = priority, 
				backend[6] = clients, 
				backend[7] = connections, 
				backend[8] = service 
		
FIXME:
	Sustitute by getHTTPFarmBackendsStats function
	
=cut
sub getHTTPFarmBackendsStatus    # ($farm_name,@content)
{
	my ( $farm_name, @content ) = @_;

	my @backends_data;
	my @serviceline;
	my $service;
	my $connections;

	if ( !@content )
	{
		@content = &getHTTPFarmBackendStatusCtl( $farm_name );
	}

	foreach ( @content )
	{
		my @serviceline;
		if ( $_ =~ /Service/ )
		{
			@serviceline = split ( "\ ", $_ );
			$serviceline[2] =~ s/"//g;
			chomp ( $serviceline[2] );
			$service = $serviceline[2];
		}
		if ( $_ =~ /Backend/ )
		{
			#backend ID
			my @backends = split ( "\ ", $_ );
			$backends[0] =~ s/\.//g;
			my $line = $backends[0];

			#backend IP,PORT
			my @backends_ip  = split ( ":", $backends[2] );
			my $ip_backend   = $backends_ip[0];
			my $port_backend = $backends_ip[1];
			$line         = $line . "\t" . $ip_backend . "\t" . $port_backend;

			#status
			my $status_backend = $backends[7];
			my $backend_disabled = $backends[3];
			if ( $backend_disabled eq "DISABLED" )
			{
				#Checkstatusfile
				$status_backend =
				  &getHTTPBackendStatusFromFile( $farm_name, $backends[0], $service );
			}
			elsif ( $status_backend eq "alive" )
			{
				$status_backend = "up";
			}
			elsif ( $status_backend eq "DEAD" )
			{
				$status_backend = "down";
			}
			$line = $line . "\t" . $status_backend;

			#priority
			my $priority_backend = $backends[4];
			$priority_backend =~ s/\(//g;
			$line = $line . "\t" . "-\t" . $priority_backend;
			my $clients = &getFarmBackendsClients( $backends[0], @content, $farm_name );
			if ( $clients != -1 )
			{
				$line = $line . "\t" . $clients;
			}
			else
			{
				$line = $line . "\t-";
			}

			$connections = $backends[8];
			$connections =~ s/[\(\)]//g;			
			if ( !( $connections >= 0 ) )
			{
				$connections = 0;
			}
			$line = $line . "\t" . $connections . "\t" . $service;
			
			push ( @backends_data, $line );
		}
	}
	return @backends_data;
}

=begin nd
Function: getHTTPFarmBackendsStats

	This function is the same than getHTTPFarmBackendsStatus but return a hash with http farm information
	This function take data from pounctl and it gives hash format 
	
Parameters:
	farmname - Farm name

Returns:
	hash ref - hash with backend farm stats
		
		backendStats = 
		{
			"farmname" = $farmname
			"queue" = $pending_conns
			"services" = \@services
		}
		
		\@servcies = 
		[
			{
				"id" = $service_id		# it is the index in the service array too
				"service" = $service_name
				"backends" = \@backends
				"sessions" = \@sessions
			}
		]
		
		\@backends = 
		[
			{
				"id" = $backend_id		# it is the index in the backend array too
				"ip" = $backend_ip
				"port" = $backend_port
				"status" = $backend_status
				"established" = $established_connections
			}
		]
		
		\@sessions = 
		[
			{
				"client" = $client_id 		# it is the index in the session array too
				"id" = $session_id		# id associated to a bacckend, it can change depend of session type
				"backends" = $backend_id
			}
		]
		
FIXME: 
		Put output format same format than "GET /stats/farms/BasekitHTTP"
		
=cut
sub getHTTPFarmBackendsStats    # ($farm_name,@content)
{
	my ( $farm_name ) = @_;

	my $stats;
	my @sessions;
	my $serviceName;
	my $hashService;
	my $firstService = 1;
	
	my $service_re = &getValidFormat( 'service' );

	#i.e. of poundctl:
	
	#Requests in queue: 0
	#0. http Listener 185.76.64.223:80 a
		#0. Service "HTTP" active (4)
		#0. Backend 172.16.110.13:80 active (1 0.780 sec) alive (61)
		#1. Backend 172.16.110.14:80 active (1 0.878 sec) alive (90)
		#2. Backend 172.16.110.11:80 active (1 0.852 sec) alive (99)
		#3. Backend 172.16.110.12:80 active (1 0.826 sec) alive (75)
	my @poundctl = &getHTTPFarmGlobalStatus ($farm_name);

	foreach my $line ( @poundctl )
	{
		#i.e.
		#Requests in queue: 0
		#~ if ( $line =~ /Requests in queue: (\d+)/ )
		#~ {
			#~ $stats->{ "queue" } = $1;
		#~ }
		
		# i.e.
		#     0. Service "HTTP" active (10)
		if ( $line =~ /(\d+)\. Service "($service_re)"/ )
		{
				$serviceName = $2;
		}
			
		# i.e.
		#      0. Backend 192.168.100.254:80 active (5 0.000 sec) alive (0)
		if ( $line =~ /(\d+)\. Backend (\d+\.\d+\.\d+\.\d+):(\d+) (\w+) .+ (\w+) \((\d+)\)/ )
		{
			my $backendHash =
 				{ 
					id => $1+0,
					ip => $2,
					port => $3+0,
					status => $5,
					established => $6+0,
					service => $serviceName,
				};
				
			my $backend_disabled = $4;
			if ( $backend_disabled eq "DISABLED" )
			{
				#Checkstatusfile
				$backendHash->{ "status" } =
				  &getHTTPBackendStatusFromFile( $farm_name, $backendHash->{id}, $serviceName );
			}
			elsif ( $backendHash->{ "status" } eq "alive" )
			{
				$backendHash->{ "status" } = "up";
			}
			elsif ( $backendHash->{ "status" } eq "DEAD" )
			{
				$backendHash->{ "status" } = "down";
			}
			
			push @{ $stats->{backends} }, $backendHash;
		}

		# i.e.
		#      1. Session 107.178.194.117 -> 1
		if ( $line =~ /(\d+)\. Session (.+) \-\> (\d+)/ )
		{
			push @{ $stats->{sessions} },
				{ 
					client => $1+0,
					session => $2,
					id => $3+0,
					service => $serviceName,
				};
		}
		
	}
	
	return $stats;
}

=begin nd
Function: getHTTPBackendStatusFromFile

	Function that return if a pound backend is active, down by farmguardian or it's in maintenance mode
	
Parameters:
	farmname - Farm name
	backend - backend id
	service - service name

Returns:
	scalar - return backend status: "maintentance", "fgDOWN", "active" or -1 on failure
		
=cut
sub getHTTPBackendStatusFromFile    # ($farm_name,$backend,$service)
{
	my ( $farm_name, $backend, $service ) = @_;
	my $index;
	my $line;
	my $stfile = "$configdir\/$farm_name\_status.cfg";
	# if the status file does not exist the backend is ok
	my $output = "active";

	if ( -e "$stfile" )
	{
		$index = &getFarmVSI( $farm_name, $service );
		open FG, "$stfile";
		while ( $line = <FG> )
		{
			#service index
			if ( $line =~ /\ 0\ ${index}\ ${backend}/ )
			{
				if ( $line =~ /maintenance/ )
				{
					$output = "maintenance";
				}
				elsif ( $line =~ /fgDOWN/ )
				{
					$output = "fgDOWN";
				}
				else
				{
					$output = "active";
				}
			}
		}
		close FG;
	}

	return $output;
}

=begin nd
Function: getHTTPFarmBackendsClients

	Function that return number of clients with session in a backend server
	
Parameters:
	backend - backend id
	content - command output where parsing backend status
	farmname - Farm name

Returns:
	Integer - return number of clients in the backend
		
=cut
sub getHTTPFarmBackendsClients    # ($idserver,@content,$farm_name)
{
	my ( $idserver, @content, $farm_name ) = @_;

	if ( !@content )
	{
		@content = &getHTTPFarmBackendStatusCtl( $farm_name );
	}
	my $numclients = 0;
	foreach ( @content )
	{
		if ( $_ =~ / Session .* -> $idserver$/ )
		{
			$numclients++;
		}
	}

	return $numclients;
}

=begin nd
Function: getHTTPFarmBackendsClientsList

	Function that return sessions of clients
	
Parameters:
	farmname - Farm name
	content - command output where it must be parsed backend status

Returns:
	array - return information about existing sessions. The format for each line is: "service" . "\t" . "session_id" . "\t" . "session_value" . "\t" . "backend_id"
		
FIXME:
	will be useful change output format to hash format
	
=cut
sub getHTTPFarmBackendsClientsList    # ($farm_name,@content)
{
	my ( $farm_name, @content ) = @_;

	my @client_list;
	my $s;

	if ( !@content )
	{
		@content = &getHTTPFarmBackendStatusCtl( $farm_name );
	}

	foreach ( @content )
	{
		my $line;
		if ( $_ =~ /Service/ )
		{
			my @service = split ( "\ ", $_ );
			$s = $service[2];
			$s =~ s/"//g;
		}
		if ( $_ =~ / Session / )
		{
			my @sess = split ( "\ ", $_ );
			my $id = $sess[0];
			$id =~ s/\.//g;
			$line = $s . "\t" . $id . "\t" . $sess[2] . "\t" . $sess[4];
			push ( @client_list, $line );
		}
	}

	return @client_list;
}

=begin nd
Function: getHTTPFarmBackendMaintenance

	Function that check if a backend on a farm is on maintenance mode
	
Parameters:
	farmname - Farm name
	backend - Backend id
	service - Service name

Returns:
	scalar - if backend is in maintenance mode, return 0 else return -1
		
=cut
sub getHTTPFarmBackendMaintenance    # ($farm_name,$backend,$service)
{
	my ( $farm_name, $backend, $service ) = @_;

	require Zevenet::Farm::Base;

	my $output = -1;
	
	# if the farm is running, take status from poundctl
	if ( &getFarmStatus ($farm_name) eq 'up' )
	{
		my $poundctl = &getGlobalConfiguration('poundctl');
		my @run    = `$poundctl -c "/tmp/$farm_name\_pound.socket"`;
		
		my $sw     = 0;
	
		foreach my $line ( @run )
		{
			if ( $line =~ /Service \"$service\"/ )
			{
				$sw = 1;
			}
	
			if ( $line =~ /$backend\. Backend/ && $sw == 1 )
			{
				my @line = split ( "\ ", $line );
				my $backendstatus = $line[3];
	
				if ( $backendstatus eq "DISABLED" )
				{
					$backendstatus =
					&getHTTPBackendStatusFromFile( $farm_name, $backend, $service );
	
					if ( $backendstatus =~ /maintenance/ )
					{
						$output = 0;
					}
				}
				last;
			}
		}
	}
	# if the farm is not running, take status from status file
	else
	{
		my $statusfile = "$configdir\/$farm_name\_status.cfg";

		if ( -e $statusfile )
		{
			use Tie::File;
			tie my @filelines, 'Tie::File', "$statusfile";
			
			my @sol;
			my $service_index = &getFarmVSI( $farm_name, $service );
			if ( @sol = grep ( /0 $service_index $backend maintenance/, @filelines ) )
			{
				$output = 0;
			}
			untie @filelines;
		}
	}

	return $output;
}

=begin nd
Function: setHTTPFarmBackendMaintenance

	Function that enable the maintenance mode for backend
	
Parameters:
	farmname - Farm name
	backend - Backend id
	service - Service name

Returns:
	Integer - return 0 on success or -1 on failure
		
=cut
sub setHTTPFarmBackendMaintenance    # ($farm_name,$backend,$service)
{
	my ( $farm_name, $backend, $service ) = @_;

	my $output = -1;

	#find the service number
	my $idsv = &getFarmVSI( $farm_name, $service );

	&zenlog(
		  "setting Maintenance mode for $farm_name service $service backend $backend" );

	if ( &getFarmStatus( $farm_name ) eq 'up' )
	{
		my $poundctl = &getGlobalConfiguration('poundctl');
		my $poundctl_command =
		"$poundctl -c /tmp/$farm_name\_pound.socket -b 0 $idsv $backend";
	
		&zenlog( "running '$poundctl_command'" );
		my @run = `$poundctl_command`;
		$output = $?;
	}

	&setHTTPFarmBackendStatusFile( $farm_name, $backend, "maintenance", $idsv );

	return $output;
}

=begin nd
Function: setHTTPFarmBackendMaintenance

	Function that disable the maintenance mode for backend
	
Parameters:
	farmname - Farm name
	backend - Backend id
	service - Service name

Returns:
	Integer - return 0 on success or -1 on failure
		
=cut
sub setHTTPFarmBackendNoMaintenance    # ($farm_name,$backend,$service)
{
	my ( $farm_name, $backend, $service ) = @_;

	my $output = -1;

	#find the service number
	my $idsv = &getFarmVSI( $farm_name, $service );

	&zenlog(
		"setting Disabled maintenance mode for $farm_name service $service backend $backend"
	);

	if ( &getFarmStatus( $farm_name ) eq 'up' ) 
	{
		my $poundctl = &getGlobalConfiguration('poundctl');
		my $poundctl_command =
			"$poundctl -c /tmp/$farm_name\_pound.socket -B 0 $idsv $backend";

		&zenlog( "running '$poundctl_command'" );
		my @run    = `$poundctl_command`;
		$output = $?;
	}
	
	# save backend status in status file
	&setHTTPFarmBackendStatusFile( $farm_name, $backend, "active", $idsv );

	return $output;
}

=begin nd
Function: setHTTPFarmBackendStatusFile

	Function that save in a file the backend status (maintenance or not)
	
Parameters:
	farmname - Farm name
	backend - Backend id
	status - backend status to save in the status file
	service_id - Service id

Returns:
	none - .
		
FIXME:
	Rename the function, something like saveFarmHTTPBackendstatus, not is "get", this function makes changes in the system
	Not return nothing, do error control
		
=cut
sub setHTTPFarmBackendStatusFile    # ($farm_name,$backend,$status,$idsv)
{
	my ( $farm_name, $backend, $status, $idsv ) = @_;

	my $statusfile = "$configdir\/$farm_name\_status.cfg"; 
	my $changed    = "false";

	if ( !-e $statusfile )
	{
		open FW, ">$statusfile";
		my $poundctl = &getGlobalConfiguration('poundctl');
		my @run = `$poundctl -c /tmp/$farm_name\_pound.socket`;
		my @sw;
		my @bw;

		foreach my $line ( @run )
		{
			if ( $line =~ /\.\ Service\ / )
			{
				@sw = split ( "\ ", $line );
				$sw[0] =~ s/\.//g;
				chomp $sw[0];
			}
			if ( $line =~ /\.\ Backend\ / )
			{
				@bw = split ( "\ ", $line );
				$bw[0] =~ s/\.//g;
				chomp $bw[0];
				if ( $bw[3] eq "active" )
				{
					#~ print FW "-B 0 $sw[0] $bw[0] active\n";
				}
				else
				{
					print FW "-b 0 $sw[0] $bw[0] fgDOWN\n";
				}
			}
		}
		close FW;
	}
	use Tie::File;
	tie my @filelines, 'Tie::File', "$statusfile";

	my $i;
	foreach my $linea ( @filelines )
	{
		if ( $linea =~ /\ 0\ $idsv\ $backend/ )
		{
			if ( $status =~ /maintenance/ || $status =~ /fgDOWN/ )
			{
				$linea   = "-b 0 $idsv $backend $status";
				$changed = "true";
			}
			else
			{
				splice @filelines, $i, 1,;
				$changed = "true";
			}
		}
		$i++;
	}
	untie @filelines;

	if ( $changed eq "false" )
	{
		open FW, ">>$statusfile";
		if ( $status =~ /maintenance/ || $status =~ /fgDOWN/ )
		{
			print FW "-b 0 $idsv $backend $status\n";
		}
		else
		{
			splice @filelines, $i, 1,;
		}
		close FW;
	}

}

=begin nd
Function: runRemoveHTTPBackendStatus

	Function that removes a backend from the status file
	
Parameters:
	farmname - Farm name
	backend - Backend id
	service - Service name

Returns:
	none - .
		
FIXME:
	This function returns nothing, do error control
		
=cut
sub runRemoveHTTPBackendStatus    # ($farm_name,$backend,$service)
{
	#~ my ( $farm_name, $backend, $service ) = @_;

	#~ my $i      = -1;
	#~ my $j      = -1;
	#~ my $change = "false";
	#~ my $sindex = &getFarmVSI( $farm_name, $service );
	#~ tie my @contents, 'Tie::File', "$configdir\/$farm_name\_status.cfg";
	#~ foreach my $line ( @contents )
	#~ {
		#~ $i++;
		#~ if ( $line =~ /0\ ${sindex}\ ${backend}/ )
		#~ {
			#~ splice @contents, $i, 1,;
		#~ }
	#~ }
	#~ untie @contents;
	#~ my $index = -1;
	#~ tie my @filelines, 'Tie::File', "$configdir\/$farm_name\_status.cfg";
	#~ for ( @filelines )
	#~ {
		#~ $index++;
		#~ if ( $_ !~ /0\ ${sindex}\ $index/ )
		#~ {
			#~ my $jndex = $index + 1;
			#~ $_ =~ s/0\ ${sindex}\ $jndex/0\ ${sindex}\ $index/g;
		#~ }
	#~ }
	#~ untie @filelines;

	my ( $farm_name, $backend, $service ) = @_;

	my $i      = -1;
	my $serv_index = &getFarmVSI( $farm_name, $service );
	tie my @contents, 'Tie::File', "$configdir\/$farm_name\_status.cfg";
	foreach my $line ( @contents )
	{
		$i++;
		if ( $line =~ /0\ ${serv_index}\ ${backend}/ )
		{
			splice @contents, $i, 1,;
			last;
		}
	}
	untie @contents;
	
	tie my @filelines, 'Tie::File', "$configdir\/$farm_name\_status.cfg";
	# decrease backend index in greater backend ids
	foreach my $line ( @filelines )
	{
		if ( $line =~ /0\ ${serv_index}\ (\d+) (\w+)/ )
		{
			my $backend_index = $1 ;
			my $status = $2;
			if ( $backend_index > $backend )
			{
				$backend_index = $backend_index -1;
				$line = "-b 0 $serv_index $backend_index $status";
			}
		}
	}
	untie @filelines;
		
}

=begin nd
Function: setHTTPFarmBackendStatus

	For a HTTP farm, it gets each backend status from status file and set it in pound daemon
	
Parameters:
	farmname - Farm name

Returns:
	none - .
		
FIXME:
	This function returns nothing, do error control
		
=cut
sub setHTTPFarmBackendStatus    # ($farm_name)
{
	my $farm_name = shift;

	&zenlog( "Setting backends status in farm $farm_name" );

	my $be_status_filename = "$configdir\/$farm_name\_status.cfg";

	unless ( -f $be_status_filename )
	{
		open my $fh, ">", $be_status_filename;
		close $fh;
	}

	open my $fh, "<", $be_status_filename;

	unless ( $fh )
	{
		my $msg = "Error opening $be_status_filename: $!. Aborting execution.";

		&zenlog( $msg );
		die $msg;
	}

	my $poundctl = &getGlobalConfiguration('poundctl');
	
	while ( my $line_aux = <$fh> )
	{
		my @line = split ( "\ ", $line_aux );
		my @run =
		  `$poundctl -c /tmp/$farm_name\_pound.socket $line[0] $line[1] $line[2] $line[3]`;
	}
	close $fh;
}

=begin nd
Function: setFarmBackendsSessionsRemove

	Remove all the active sessions enabled to a backend in a given service
	Used by farmguardian
	
Parameters:
	farmname - Farm name
	service - Service name
	backend - Backend id

Returns:
	none - .
	
FIXME: 
		
=cut
sub setFarmBackendsSessionsRemove    #($farm_name,$service,$backendid)
{
	my ( $farm_name, $service, $backendid ) = @_;

	my @content = &getHTTPFarmBackendStatusCtl( $farm_name );
	my @sessions = &getHTTPFarmBackendsClientsList( $farm_name, @content );
	my @service;
	my $sw = 0;
	my $serviceid;
	my @sessionid;
	my $sessid;
	my $sessionid2;
	my $poundctl = &getGlobalConfiguration('poundctl');
	my @output;

	&zenlog(
		"Deleting established sessions to a backend $backendid from farm $farm_name in service $service"
	);

	foreach ( @content )
	{
		if ( $_ =~ /Service/ && $sw eq 1 )
		{
			$sw = 0;
		}

		if ( $_ =~ /Service\ \"$service\"/ && $sw eq 0 )
		{
			$sw        = 1;
			@service   = split ( /\./, $_ );
			$serviceid = $service[0];
		}

		if ( $_ =~ /Session.*->\ $backendid/ && $sw eq 1 )
		{
			@sessionid  = split ( /Session/, $_ );
			$sessionid2 = $sessionid[1];
			@sessionid  = split ( /\ /, $sessionid2 );
			$sessid     = $sessionid[1];
			@output = `$poundctl -c  /tmp/$farm_name\_pound.socket -n 0 $serviceid $sessid`;
			&zenlog(
				"Executing:  $poundctl -c /tmp/$farm_name\_pound.socket -n 0 $serviceid $sessid"
			);
		}
	}
}

1;
