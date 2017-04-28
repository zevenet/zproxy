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
Function: getDatalinkFarmAlgorithm

	Get type of balancing algorithm. 
	
Parameters:
	farmname - Farm name

Returns:
	scalar - The possible values are "weight", "priority" or -1 on failure
	
=cut
sub getDatalinkFarmAlgorithm    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $algorithm     = -1;
	my $first         = "true";

	open FI, "<$configdir/$farm_filename";

	while ( my $line = <FI> )
	{
		if ( $line ne "" && $first eq "true" )
		{
			$first = "false";
			my @line = split ( "\;", $line );
			$algorithm = $line[3];
		}
	}
	close FI;

	return $algorithm;
}


=begin nd
Function: setDatalinkFarmAlgorithm

	Set the load balancing algorithm to a farm
	
Parameters:
	algorithm - Type of balancing mode: "weight" or "priority"
	farmname - Farm name

Returns:
	none - .
	
FIXME:
	set a return value, and do error control
	
=cut
sub setDatalinkFarmAlgorithm    # ($algorithm,$farm_name)
{
	my ( $algorithm, $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );

	#~ my $output        = -1;
	my $i = 0;

	use Tie::File;
	tie my @configfile, 'Tie::File', "$configdir\/$farm_filename";

	for my $line ( @configfile )
	{
		if ( $line =~ /^$farm_name\;/ )
		{
			my @args = split ( "\;", $line );
			$line = "$args[0]\;$args[1]\;$args[2]\;$algorithm\;$args[4]";
			splice @configfile, $i, $line;
		}
		$i++;
	}
	untie @configfile;

	# Apply changes online
	if ( &getFarmStatus( $farm_name ) eq 'up' )
	{
		&runFarmStop( $farm_name, "true" );
		&runFarmStart( $farm_name, "true" );
	}

	return;    # $output;
}


=begin nd
Function: getDatalinkFarmServers

	List all farm backends and theirs configuration
	
Parameters:
	farmname - Farm name

Returns:
	array - list of backends. Each item has the format: ";index;ip;iface;weight;priority;status"
		
FIXME:
	changes output to hash format
	
=cut
sub getDatalinkFarmServers    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $farm_type     = &getFarmType( $farm_name );
	my $first         = "true";
	my $sindex        = 0;
	my @servers;

	open FI, "<$configdir/$farm_filename";

	while ( my $line = <FI> )
	{
		# ;server;45.2.2.3;eth0;1;1;up
		if ( $line ne "" && $line =~ /^\;server\;/ && $first ne "true" )
		{
			$line =~ s/^\;server/$sindex/g;    #, $line;
			chomp( $line );
			push ( @servers, $line );
			$sindex = $sindex + 1;
		}
		else
		{
			$first = "false";
		}
	}
	close FI;

	return @servers;
}


=begin nd
Function: getDatalinkFarmBootStatus

	Return the farm status at boot zevenet
	 
Parameters:
	farmname - Farm name

Returns:
	scalar - return "down" if the farm not run at boot or "up" if the farm run at boot

=cut
sub getDatalinkFarmBootStatus    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = "down";
	my $first         = "true";

	open FI, "<$configdir/$farm_filename";

	while ( my $line = <FI> )
	{
		if ( $line ne "" && $first eq "true" )
		{
			$first = "false";
			my @line_a = split ( "\;", $line );
			$output = $line_a[4];
			chomp ( $output );
		}
	}
	close FI;

	return $output;
}


=begin nd
Function: getFarmInterface

	 Get network physical interface used by the farm vip
	 
Parameters:
	farmname - Farm name

Returns:
	scalar - return NIC inteface or -1 on failure

=cut
sub getFarmInterface    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $type   = &getFarmType( $farm_name );
	my $output = -1;
	my $line;

	if ( $type eq "datalink" )
	{
		my $farm_filename = &getFarmFile( $farm_name );
		open FI, "<$configdir/$farm_filename";
		my $first = "true";
		while ( $line = <FI> )
		{
			if ( $line ne "" && $first eq "true" )
			{
				$first = "false";
				my @line_a = split ( "\;", $line );
				my @line_b = split ( "\:", $line_a[2] );
				$output = $line_b[0];
			}
		}
		close FI;
	}

	return $output;
}


=begin nd
Function: _runDatalinkFarmStart

	Run a datalink farm
	
Parameters:
	farmname - Farm name
	writeconf - If this param has the value "true" in config file will be saved the current status
	status - status of a before operation

Returns:
	Integer - Error code: return 0 on success or different of 0 on failure
	
BUG: 
	writeconf must not exist, always it has to be TRUE 
	status parameter is not useful
	
=cut
sub _runDatalinkFarmStart    # ($farm_name, $writeconf, $status)
{
	my ( $farm_name, $writeconf, $status ) = @_;

	return $status if ( $status eq '-1' );

	my $farm_filename = &getFarmFile( $farm_name );

	if ( $writeconf eq "true" )
	{
		use Tie::File;
		tie my @configfile, 'Tie::File', "$configdir\/$farm_filename";
		my $first = 1;

		foreach ( @configfile )
		{
			if ( $first eq 1 )
			{
				s/\;down/\;up/g;
				$first = 0;
			}
		}
		untie @configfile;
	}

	# include cron task to check backends
	use Tie::File;
	tie my @cron_file, 'Tie::File', "/etc/cron.d/zenloadbalancer";
	my @farmcron = grep /\# \_\_$farm_name\_\_/, @cron_file;
	if ( scalar @farmcron eq 0 )
	{
		push ( @cron_file,
			   "* * * * *	root	\/usr\/local\/zenloadbalancer\/app\/libexec\/check_uplink $farm_name \# \_\_$farm_name\_\_"
		);
	}
	untie @cron_file;

	# Apply changes online

	# Set default uplinks as gateways
	my $iface     = &getFarmInterface( $farm_name );
	my $ip_bin    = &getGlobalConfiguration('ip_bin');
	my @eject     = `$ip_bin route del default table table_$iface 2> /dev/null`;
	my @servers   = &getFarmServers( $farm_name );
	my $algorithm = &getFarmAlgorithm( $farm_name );
	my $routes    = "";

	if ( $algorithm eq "weight" )
	{
		foreach my $serv ( @servers )
		{
			chomp ( $serv );
			my @line = split ( "\;", $serv );
			my $stat = $line[5];
			chomp ( $stat );
			my $weight = 1;

			if ( $line[3] ne "" )
			{
				$weight = $line[3];
			}
			if ( $stat eq "up" )
			{
				$routes = "$routes nexthop via $line[1] dev $line[2] weight $weight";
			}
		}
	}

	if ( $algorithm eq "prio" )
	{
		my $bestprio = 100;
		foreach my $serv ( @servers )
		{
			chomp ( $serv );
			my @line = split ( "\;", $serv );
			my $stat = $line[5];
			my $prio = $line[4];
			chomp ( $stat );

			if (    $stat eq "up"
				 && $prio > 0
				 && $prio < 10
				 && $prio < $bestprio )
			{
				$routes   = "nexthop via $line[1] dev $line[2] weight 1";
				$bestprio = $prio;
			}
		}
	}

	if ( $routes ne "" )
	{
		my $ip_command =
		  "$ip_bin route add default scope global table table_$iface $routes";

		&zenlog( "running $ip_command" );
		$status = system ( "$ip_command >/dev/null 2>&1" );
	}
	else
	{
		$status = 0;
	}

	# Set policies to the local network
	my $ip = &iponif( $iface );

	if ( $ip && $ip =~ /\./ )
	{
		my $ipmask = &maskonif( $iface );
		my ( $net, $mask ) = ipv4_network( "$ip / $ipmask" );
		&zenlog( "running $ip_bin rule add from $net/$mask lookup table_$iface" );
		my @eject = `$ip_bin rule add from $net/$mask lookup table_$iface 2> /dev/null`;
	}

	# Enable IP forwarding
	&setIpForward( "true" );

	# Enable active datalink file
	my $piddir = &getGlobalConfiguration('piddir');
	open FI, ">$piddir\/$farm_name\_datalink.pid";
	close FI;

	return $status;
}


=begin nd
Function: _runDatalinkFarmStop

	Stop a datalink farm
	
Parameters:
	farmname - Farm name
	writeconf - If this param has the value "true" in config file will be saved the current status

Returns:
	Integer - Error code: return 0 on success or -1 on failure
	
BUG: 
	writeconf must not exist, always it has to be TRUE 
	
=cut
sub _runDatalinkFarmStop    # ($farm_name,$writeconf)
{
	my ( $farm_name, $writeconf ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $status = ( $writeconf eq "true" ) ? -1 : 0;


	if ( $writeconf eq "true" )
	{
		use Tie::File;
		tie my @configfile, 'Tie::File', "$configdir\/$farm_filename";
		my $first = 1;
		foreach ( @configfile )
		{
			if ( $first == 1 )
			{
				s/\;up/\;down/g;
				$status = $?;
				$first  = 0;
			}
		}
		untie @configfile;
	}

	# delete cron task to check backends
	use Tie::File;
	tie my @cron_file, 'Tie::File', "/etc/cron.d/zenloadbalancer";
	@cron_file = grep !/\# \_\_$farm_name\_\_/, @cron_file;
	untie @cron_file;

	$status = 0 if $writeconf eq 'false';

	# Apply changes online
	if ( $status != -1 )
	{
		my $iface = &getFarmInterface( $farm_name );
		my $ip_bin = &getGlobalConfiguration('ip_bin');

		# Disable policies to the local network
		my $ip = &iponif( $iface );
		if ( $ip && $ip =~ /\./ )
		{
			my $ipmask = &maskonif( $iface );
			my ( $net, $mask ) = ipv4_network( "$ip / $ipmask" );

			&zenlog( "running $ip_bin rule del from $net/$mask lookup table_$iface" );
			my @eject = `$ip_bin rule del from $net/$mask lookup table_$iface 2> /dev/null`;
		}

		# Disable default uplink gateways
		my @eject = `$ip_bin route del default table table_$iface 2> /dev/null`;

		# Disable active datalink file
		my $piddir = &getGlobalConfiguration('piddir');
		unlink ( "$piddir\/$farm_name\_datalink.pid" );
		if ( -e "$piddir\/$farm_name\_datalink.pid" )
		{
			$status = -1;
		}
	}

	return $status;
}


=begin nd
Function: runDatalinkFarmCreate

	Create a datalink farm through its configuration file and run it
	
Parameters:
	farmname - Farm name
	vip - Virtual IP
	port - Virtual port where service is listening

Returns:
	Integer - Error code: return 0 on success or different of 0 on failure
	
FIXME: 
	it is possible calculate here the inteface of VIP and put standard the input as the others create farm functions
		
=cut
sub runDatalinkFarmCreate    # ($farm_name,$vip,$fdev)
{
	my ( $farm_name, $vip, $fdev ) = @_;

	open FO, ">$configdir\/$farm_name\_datalink.cfg";
	print FO "$farm_name\;$vip\;$fdev\;weight\;up\n";
	close FO;
	my $output = $?;

	my $piddir = &getGlobalConfiguration('piddir');
	if ( !-e "$piddir/${farm_name}_datalink.pid" )
	{
		# Enable active datalink file
		open FI, ">$piddir\/$farm_name\_datalink.pid";
		close FI;
	}

	return $output;
}


=begin nd
Function: getDatalinkFarmVip

	Returns farm vip, vport or vip:vport
	
Parameters:
	info - parameter to return: vip, for virtual ip; vipp, for virtual port or vipps, for vip:vipp
	farmname - Farm name

Returns:
	Scalar - return request parameter on success or -1 on failure
		
=cut
sub getDatalinkFarmVip    # ($info,$farm_name)
{
	my ( $info, $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;
	my $first         = "true";

	open FI, "<$configdir/$farm_filename";

	while ( my $line = <FI> )
	{
		if ( $line ne "" && $first eq "true" )
		{
			$first = "false";
			my @line_a = split ( "\;", $line );

			if ( $info eq "vip" )   { $output = $line_a[1]; }
			if ( $info eq "vipp" )  { $output = $line_a[2]; }
			if ( $info eq "vipps" ) { $output = "$line_a[1]\:$line_a[2]"; }
		}
	}
	close FI;

	return $output;
}


=begin nd
Function: setDatalinkFarmVirtualConf

	Set farm virtual IP and virtual PORT
	
Parameters:
	vip - virtual ip
	port - virtual port
	farmname - Farm name

Returns:
	Scalar - Error code: 0 on success or -1 on failure
		
=cut
sub setDatalinkFarmVirtualConf    # ($vip,$vip_port,$farm_name)
{
	my ( $vip, $vip_port, $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $farm_state    = &getFarmStatus( $farm_name );
	my $stat          = -1;
	my $i             = 0;

	&runFarmStop( $farm_name, 'true' ) if $farm_state eq 'up';

	use Tie::File;
	tie my @configfile, 'Tie::File', "$configdir\/$farm_filename";

	for my $line ( @configfile )
	{
		if ( $line =~ /^$farm_name\;/ )
		{
			my @args = split ( "\;", $line );
			$line = "$args[0]\;$vip\;$vip_port\;$args[3]\;$args[4]";
			splice @configfile, $i, $line;
			$stat = $?;
		}
		$i++;
	}
	untie @configfile;
	$stat = $?;

	&runFarmStart( $farm_name, 'true' ) if $farm_state eq 'up';

	return $stat;
}


=begin nd
Function: setDatalinkFarmServer

	Set a backend or create it if it doesn't exist
	
Parameters:
	id - Backend id, if this id doesn't exist, it will create a new backend
	ip - Real server ip
	interface - Local interface used to connect to such backend.
	weight - The higher the weight, the more request will go to this backend.
	priority -  The lower the priority, the most preferred is the backend.
	farmname - Farm name

Returns:
	none - .
	
FIXME:
	Not return nothing, do error control
		
=cut
sub setDatalinkFarmServer    # ($ids,$rip,$iface,$weight,$priority,$farm_name)
{
	my ( $ids, $rip, $iface, $weight, $priority, $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $end           = "false";
	my $i             = 0;
	my $l             = 0;
	
	# default value
	$weight ||= 1;
	$priority ||= 1;

	tie my @contents, 'Tie::File', "$configdir\/$farm_filename";

	foreach my $line ( @contents )
	{
		if ( $line =~ /^\;server\;/ && $end ne "true" )
		{
			# modify a backend
			if ( $i eq $ids )
			{
				my $dline = "\;server\;$rip\;$iface\;$weight\;$priority\;up\n";
				splice @contents, $l, 1, $dline;
				$end = "true";
			}
			else
			{
				$i++;
			}
		}
		$l++;
	}

	# create a backend
	if ( $end eq "false" )
	{
		push ( @contents, "\;server\;$rip\;$iface\;$weight\;$priority\;up\n" );
	}

	untie @contents;

	# Apply changes online
	if ( &getFarmStatus( $farm_name ) eq 'up' )
	{
		&runFarmStop( $farm_name, "true" );
		&runFarmStart( $farm_name, "true" );
	}

	return;
}


=begin nd
Function: runDatalinkFarmServerDelete

	Delete a backend from a datalink farm
	
Parameters:
	id - Backend id
	farmname - Farm name

Returns:
	Integer - Error code: return 0 on success or -1 on failure
	
=cut
sub runDatalinkFarmServerDelete    # ($ids,$farm_name)
{
	my ( $ids, $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $output        = -1;
	my $end           = "false";
	my $i             = 0;
	my $l             = 0;

	tie my @contents, 'Tie::File', "$configdir\/$farm_filename";

	foreach my $line ( @contents )
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

	# Apply changes online
	if ( &getFarmStatus( $farm_name ) eq 'up' )
	{
		&runFarmStop( $farm_name, "true" );
		&runFarmStart( $farm_name, "true" );
	}

	return $output;
}


=begin nd
Function: getDatalinkFarmBackendsStatus

	Get the backend status from a datalink farm
	
Parameters:
	content - Not used, it is necessary create a function to generate content

Returns:
	array - Each item has the next format: "ip;port;backendstatus;weight;priority;clients"
	
BUG:
	Not used. This function exist but is not contemplated in zapi v3
	Use farmname as parameter
	It is necessary creates backend checks and save backend status
	
=cut
sub getDatalinkFarmBackendsStatus    # (@content)
{
	my ( @content ) = @_;

	my @backends_data;

	foreach my $server ( @content )
	{
		my @serv = split ( ";", $server );
		push ( @backends_data, "$serv[2]\;$serv[3]\;$serv[4]\;$serv[5]\;$serv[6]" );
	}

	return @backends_data;
}


=begin nd
Function: setDatalinkFarmBackendStatus

	Change backend status to up or down
	
Parameters:
	farmname - Farm name
	backend - Backend id
	status - Backend status, "up" or "down"

Returns:
	none - .
	
FIXME:
	Not return nothing, do error control	
	
=cut
sub setDatalinkFarmBackendStatus    # ($farm_name,$index,$stat)
{
	my ( $farm_name, $index, $stat ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );

	my $fileid   = 0;
	my $serverid = 0;

	use Tie::File;
	tie my @configfile, 'Tie::File', "$configdir\/$farm_filename";

	foreach my $line ( @configfile )
	{
		if ( $line =~ /\;server\;/ )
		{
			if ( $serverid eq $index )
			{
				my @lineargs = split ( "\;", $line );
				@lineargs[6] = $stat;
				@configfile[$fileid] = join ( "\;", @lineargs );
			}
			$serverid++;
		}
		$fileid++;
	}
	untie @configfile;

	# Apply changes online
	if ( &getFarmStatus( $farm_name ) eq 'up' )
	{
		&runFarmStop( $farm_name, "true" );
		&runFarmStart( $farm_name, "true" );
	}

	return;
}


=begin nd
Function: getDatalinkFarmBackendStatusCtl

	Return from datalink config file, all backends with theirs parameters and status
	
Parameters:
	farmname - Farm name

Returns:
	array - Each item has the next format: ";server;ip;interface;weight;priority;status"
	
=cut
sub getDatalinkFarmBackendStatusCtl    # ($farm_name)
{
	my ( $farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my @output;

	tie my @content, 'Tie::File', "$configdir\/$farm_filename";
	@output = grep /^\;server\;/, @content;
	untie @content;

	return @output;
}


=begin nd
Function: setDatalinkNewFarmName

	Function that renames a farm
	
Parameters:
	farmname - Farm name
	newfarmname - New farm name

Returns:
	Integer - Error code: return 0 on success or -1 on failure
	
=cut
sub setDatalinkNewFarmName    # ($farm_name,$new_farm_name)
{
	my ( $farm_name, $new_farm_name ) = @_;

	my $farm_filename = &getFarmFile( $farm_name );
	my $farm_type     = &getFarmType( $farm_name );
	my $newffile      = "$new_farm_name\_$farm_type.cfg";
	my $output        = -1;

	use Tie::File;
	tie my @configfile, 'Tie::File', "$configdir\/$farm_filename";

	for ( @configfile )
	{
		s/^$farm_name\;/$new_farm_name\;/g;
	}
	untie @configfile;

	my $piddir = &getGlobalConfiguration('piddir');
	rename ( "$configdir\/$farm_filename", "$configdir\/$newffile" );
	rename ( "$piddir\/$farm_name\_$farm_type.pid",
			 "$piddir\/$new_farm_name\_$farm_type.pid" );
	$output = $?;

	return $output;
}

1;
