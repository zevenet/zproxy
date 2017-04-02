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
require "/usr/local/zenloadbalancer/www/networking_functions_ext.cgi";

use IO::Socket;

my $ip_bin = &getGlobalConfiguration( 'ip_bin' );

=begin nd
Function: getRandomPort

	Get a random available port number from 35060 to 35160.

Parameters:
	none - .

Returns:
	scalar - encoded in base 64 if exists file.

Bugs:
	If no available port is found you will get an infinite loop.
	FIXME: $check not used.

See Also:
	<runGSLBFarmCreate>, <setGSLBControlPort>
=cut
#get a random available port
sub getRandomPort    # ()
{
	#down limit
	my $min = "35060";

	#up limit
	my $max = "35160";

	my $random_port;
	do
	{
		$random_port = int ( rand ( $max - $min ) ) + $min;
	} while ( &checkport( '127.0.0.1', $random_port ) eq 'false' );
	my $check = &checkport( '127.0.0.1', $random_port );

	return $random_port;
}

=begin nd
Function: checkport

	Check if a TCP port is open in a local or remote IP.

Parameters:
	host - IP address (or hostname?).
	port - TCP port number.

Returns:
	boolean - string "true" or "false".

See Also:
	<getRandomPort>
=cut
#check if a port in a ip is up
sub checkport    # ($host, $port)
{
	my ( $host, $port ) = @_;

	# check local ports;
	if ( $host eq '127.0.0.1' || $host =~ /local/ )
	{
		my $flag = system ( "netstat -putan | grep $port" );
		if ( $flag )
		{
			return "true";
		}
	}

	# check remote ports
	else
	{
		use IO::Socket;
		my $sock = new IO::Socket::INET(
										 PeerAddr => $host,
										 PeerPort => $port,
										 Proto    => 'tcp'
		);

		if ( $sock )
		{
			close ( $sock );
			return "true";
		}
		else
		{
			return "false";
		}
	}
	return "false";
}

=begin nd
Function: listallips

	List IP addresses up (flag IFF_RUNNING), excluding 127.0.0.1.

Parameters:
	none - .

Returns:
	list - All IP addresses up.

Bugs:
	$ip !~ /127.0.0.1/
	$ip !~ /0.0.0.0/

See Also:
	zapi/v3/interface.cgi <new_vini>, <new_vlan>,
	zapi/v3/post.cgi <new_farm>,
	zapi/v2/interface.cgi <new_vini>, <new_vlan>, <ifaction>
=cut
#list ALL IPS UP
sub listallips    # ()
{
	use IO::Socket;
	use IO::Interface qw(:flags);

	my @listinterfaces = ();
	my $s              = IO::Socket::INET->new( Proto => 'udp' );
	my @interfaces     = $s->if_list;
	for my $if ( @interfaces )
	{
		my $ip = $s->if_addr( $if );
		my $flags = $s->if_flags( $if );

		if ( $flags & IFF_RUNNING && $ip !~ /127.0.0.1/ && $ip !~ /0.0.0.0/ )
		{
			# if $ip: skip an empty element in the array
			push ( @listinterfaces, $ip ) if $ip;
		}
	}
	return @listinterfaces;
}

=begin nd
Function: listActiveInterfaces

	[NOT USED] List all interfaces.

Parameters:
	class - ?????.

Returns:
	list - All interfaces name.

Bugs:
	NOT USED
=cut
# list all interfaces
sub listActiveInterfaces    # ($class)
{
	my $class = shift;

	my $s = IO::Socket::INET->new( Proto => 'udp' );
	my @interfaces = $s->if_list;
	my @aifaces;

	for my $if ( @interfaces )
	{
		if ( $if !~ /^lo|sit0/ )
		{
			if ( ( $class eq "phvlan" && $if !~ /\:/ ) || $class eq "" )
			{
				my $flags = $s->if_flags( $if );
				if ( $flags & IFF_UP )
				{
					push ( @aifaces, $if );
				}
			}
		}
	}

	return @aifaces;
}

=begin nd
Function: ipisok

	Check if a string has a valid IP address format.

Parameters:
	checkip - IP address string.
	version - 4 or 6 to validate IPv4 or IPv6 only. Optional.

Returns:
	boolean - string "true" or "false".
=cut
#check if a ip is ok structure
sub ipisok    # ($checkip, $version)
{
	my $checkip = shift;
	my $version = shift;
	my $return  = "false";

	use Data::Validate::IP;

	if ( !$version || $version != 6 )
	{
		if ( is_ipv4( $checkip ) )
		{
			$return = "true";
		}
	}

	if ( !$version || $version != 4 )
	{
		if ( is_ipv6( $checkip ) )
		{
			$return = "true";
		}
	}

	return $return;
}

=begin nd
Function: ipversion

	Returns IP version number of input IP address.

Parameters:
	checkip - string to .

Returns:
	list - All IP addresses up.

Bugs:
	Fix return on non IPv4 or IPv6 valid address.
=cut
#check if a ip is IPv4 or IPv6
sub ipversion    # ($checkip)
{
	my $checkip = shift;
	my $output  = "-";

	use Data::Validate::IP;

	if ( is_ipv4( $checkip ) )
	{
		$output = 4;
	}
	elsif ( is_ipv6( $checkip ) )
	{
		$output = 6;
	}

	return $output;
}

=begin nd
Function: ipinrange

	[NOT USED] Check if an IP is in a range.

Parameters:
	netmask - .
	toip - .
	newip - .

Returns:
	boolean - string "true" or "false".

Bugs:
	NOT USED
=cut
#function checks if ip is in a range
sub ipinrange    # ($netmask, $toip, $newip)
{
	my ( $netmask, $toip, $newip ) = @_;

	use Net::IPv4Addr qw( :all );

	#$ip_str1="10.234.18.13";
	#$mask_str1="255.255.255.0";
	#$cidr_str2="10.234.18.23";
	#print "true" if ipv4_in_network( $toip, $netmask, $newip );
	if ( ipv4_in_network( $toip, $netmask, $newip ) )
	{
		return "true";
	}
	else
	{
		return "false";
	}
}

=begin nd
Function: ifexist

	Check if interface exist.

	Look for link interfaces, Virtual interfaces return "false".
	If the interface is IFF_RUNNING or configuration file exists return "true".
	If interface found but not IFF_RUNNING nor configutaion file exists returns "created".

Parameters:
	nif - network interface name.

Returns:
	string - "true", "false" or "created".

Bugs:
	"created"
=cut
#function check if interface exist
sub ifexist    # ($nif)
{
	my $nif = shift;

	use IO::Socket;
	use IO::Interface qw(:flags);
	my $s          = IO::Socket::INET->new( Proto => 'udp' );
	my @interfaces = $s->if_list;
	my $configdir  = &getGlobalConfiguration( 'configdir' );

	my $status;
	for my $if ( @interfaces )
	{
		if ( $if eq $nif )
		{
			my $flags = $s->if_flags( $if );

			if   ( $flags & IFF_RUNNING ) { $status = "up"; }
			else                          { $status = "down"; }

			if ( $status eq "up" || -e "$configdir/if_$nif\_conf" )
			{
				return "true";
			}

			return "created";
		}
	}

	return "false";
}

=begin nd
Function: writeConfigIf

	[NOT USED] Saves network interface config to file.

Parameters:
	if - interface name.
	string - replaces config file with this string.

Returns:
	$? - .

Bugs:
	returns $?

	NOT USED
=cut
# saving network interfaces config files
sub writeConfigIf    # ($if,$string)
{
	my ( $if, $string ) = @_;

	my $configdir = &getGlobalConfiguration( 'configdir' );

	open CONFFILE, ">", "$configdir/if\_$if\_conf";
	print CONFFILE "$string\n";
	close CONFFILE;
	return $?;
}

=begin nd
Function: writeRoutes

	Sets a routing table id and name pair in rt_tables file.

	Only required setting up a routed interface. Complemented in delIf()

Parameters:
	if_name - network interface name.

Returns:
	undef - .
=cut
# create table route identification, complemented in delIf()
sub writeRoutes    # ($if_name)
{
	my $if_name = shift;

	my $rttables = &getGlobalConfiguration( 'rttables' );

	open ROUTINGFILE, '<', $rttables;
	my @contents = <ROUTINGFILE>;
	close ROUTINGFILE;

	if ( grep /^...\ttable_$if_name$/, @contents )
	{
		# the table is already in the file, nothig to do
		return;
	}

	my $found = "false";
	my $rtnumber;

	# Find next table number available
	for ( my $i = 200 ; $i < 1000 && $found eq "false" ; $i++ )
	{
		next if ( grep /^$i\t/, @contents );

		$found    = "true";
		$rtnumber = $i;
	}

	if ( $found eq "true" )
	{
		open ( ROUTINGFILE, ">>", "$rttables" );
		print ROUTINGFILE "$rtnumber\ttable_$if_name\n";
		close ROUTINGFILE;
	}

	return;
}

=begin nd
Function: addlocalnet

	Set route to interface subnet into the interface routing table.

Parameters:
	if_ref - network interface hash reference.

Returns:
	integer - return code of ip command.

See Also:
	Only used here: <applyRoutes>
=cut
# add local network into routing table
sub addlocalnet    # ($if_ref)
{
	my $if_ref = shift;

	use NetAddr::IP;
	my $ip = new NetAddr::IP( $$if_ref{ addr }, $$if_ref{ mask } );
	my $net = $ip->network();
	my $routeparams = &getGlobalConfiguration('routeparams');

	my $ip_cmd =
	  "$ip_bin -$$if_ref{ip_v} route replace $net dev $$if_ref{name} src $$if_ref{addr} table table_$$if_ref{name} $routeparams";

	return &logAndRun( $ip_cmd );
}

=begin nd
Function: isRule

	Check if routing rule for $if_ref subnet in $toif table exists.

Parameters:
	if_ref - network interface hash reference.
	toif - interface name.

Returns:
	scalar - number of times the rule was found. True if found.

Bugs:
	Rules for Datalink farms are included.

See Also:
	Only used here: <applyRoutes>
=cut
# ask for rules
sub isRule    # ($if_ref, $toif)
{
	my ( $if_ref, $toif ) = @_;

	$toif = $$if_ref{ name } if !$toif;

	my $existRule  = 0;

	my ( $net, $mask ) = ipv4_network( "$$if_ref{addr} / $$if_ref{mask}" );

	my @eject      = `$ip_bin -$$if_ref{ip_v} rule list`;
	my $expression = "from $net/$mask lookup table_$toif";

	$existRule = grep /$expression/, @eject;

	return $existRule;
}

=begin nd
Function: applyRoutes

	Apply routes for interface or default gateway.

	For "local" table set route for interface.
	For "global" table set route for default gateway and save the default
	gateway in global configuration file.

Parameters:
	table - "local" for interface routes or "global" for default gateway route.
	if_ref - network interface hash reference.
	gateway - Default gateway. Only required if table parameter is "global".

Returns:
	integer - ip command return code.

See Also:
	<delRoutes>
=cut
# apply routes
sub applyRoutes    # ($table,$if_ref,$gateway)
{
	my ( $table, $if_ref, $gateway ) = @_;

	# $gateway: The 3rd argument, '$gateway', is only used for 'global' table,
	#           to assign a default gateway.

	my $status = 0;

	&zenlog(
		"Appling $table routes in stack IPv$$if_ref{ip_v} to $$if_ref{name} with gateway \"$$if_ref{gateway}\""
	);

	# not virtual interface
	if ( !defined $$if_ref{ vini } || $$if_ref{ vini } eq '' )
	{
		if ( $table eq "local" )
		{
			# &delRoutes( "local", $if );
			&addlocalnet( $if_ref );

			if ( $$if_ref{ gateway } )
			{
				my $routeparams = &getGlobalConfiguration('routeparams');
				my $ip_cmd =
				  "$ip_bin -$$if_ref{ip_v} route replace default via $$if_ref{gateway} dev $$if_ref{name} table table_$$if_ref{name} $routeparams";
				$status = &logAndRun( "$ip_cmd" );
			}

			if ( &isRule( $if_ref ) == 0 )
			{
				my ( $net, $mask ) = ipv4_network( "$$if_ref{addr} / $$if_ref{mask}" );
				my $ip_cmd =
				  "$ip_bin -$$if_ref{ip_v} rule add from $net/$mask table table_$$if_ref{name}";
				$status = &logAndRun( "$ip_cmd" );
			}
		}
		else
		{
			# Apply routes on the global table
			# &delRoutes( "global", $if );
			if ( $gateway )
			{
				my $routeparams = &getGlobalConfiguration('routeparams');
				my $ip_cmd =
				  "$ip_bin -$$if_ref{ip_v} route replace default via $gateway dev $$if_ref{name} $routeparams";
				$status = &logAndRun( "$ip_cmd" );

				tie my @contents, 'Tie::File', &getGlobalConfiguration( 'globalcfg' );
				for my $line ( @contents )
				{
					if ( grep /^\$defaultgw/, $line )
					{
						if ( $$if_ref{ ip_v } == 6 )
						{
							$line =~ s/^\$defaultgw6=.*/\$defaultgw6=\"$gateway\"\;/g;
							$line =~ s/^\$defaultgwif6=.*/\$defaultgwif6=\"$$if_ref{name}\"\;/g;
						}
						else
						{
							$line =~ s/^\$defaultgw=.*/\$defaultgw=\"$gateway\"\;/g;
							$line =~ s/^\$defaultgwif=.*/\$defaultgwif=\"$$if_ref{name}\"\;/g;
						}
					}
				}
				untie @contents;

				&reloadL4FarmsSNAT() if $status == 0;
			}
		}
	}

	# virtual interface
	else
	{
		# Include rules for virtual interfaces
		# &delRoutes( "global", $if );
		#~ if ( $$if_ref{addr} !~ /\./ && $$if_ref{addr} !~ /\:/)
		#~ {
		#~ return 1;
		#~ }

		my ( $toif ) = split ( /:/, $$if_ref{ name } );

		if ( &isRule( $if_ref, $toif ) == 0 )
		{
			my ( $net, $mask ) = ipv4_network( "$$if_ref{addr} / $$if_ref{mask}" );
			my $ip_cmd =
			  "$ip_bin -$$if_ref{ip_v} rule add from $net/$mask table table_$toif";
			$status = &logAndRun( "$ip_cmd" );
		}
	}

	return $status;
}

=begin nd
Function: delRoutes

	Delete routes for interface or default gateway.

	For "local" table remove route for interface.
	For "global" table remove route for default gateway and removes the
	default gateway in global configuration file.

Parameters:
	table - "local" for interface routes or "global" for default gateway route.
	if_ref - network interface hash reference.

Returns:
	integer - ip command return code.

See Also:
	<applyRoutes>
=cut
# delete routes
sub delRoutes    # ($table,$if_ref)
{
	my ( $table, $if_ref ) = @_;

	my $status = 0;

	&zenlog(
		   "Deleting $table routes for IPv$$if_ref{ip_v} in interface $$if_ref{name}" );

	if ( !defined $$if_ref{ vini } || $$if_ref{ vini } eq '' )
	{
		if ( $table eq "local" )
		{
			# Delete routes on the interface table
			#~ if ( ! defined $$if_ref{ vlan } || $$if_ref{ vlan } eq '' )
			#~ {
			#~ return 1;
			#~ }

			my $ip_cmd = "$ip_bin -$$if_ref{ip_v} route flush table table_$$if_ref{name}";
			$status = &logAndRun( "$ip_cmd" );

			my ( $net, $mask ) = ipv4_network( "$$if_ref{addr} / $$if_ref{mask}" );
			$ip_cmd =
			  "$ip_bin -$$if_ref{ip_v} rule del from $net/$mask table table_$$if_ref{name}";
			$status = &logAndRun( "$ip_cmd" );

			return $status;
		}
		else
		{
			# Delete routes on the global table
			my $ip_cmd = "$ip_bin -$$if_ref{ip_v} route del default";
			$status = &logAndRun( "$ip_cmd" );

			tie my @contents, 'Tie::File', &getGlobalConfiguration( 'globalcfg' );
			for my $line ( @contents )
			{
				if ( grep /^\$defaultgw/, $line )
				{
					if ( $$if_ref{ ip_v } == 6 )
					{
						$line =~ s/^\$defaultgw6=.*/\$defaultgw6=\"\"\;/g;
						$line =~ s/^\$defaultgwif6=.*/\$defaultgwif6=\"\"\;/g;
					}
					else
					{
						$line =~ s/^\$defaultgw=.*/\$defaultgw=\"\"\;/g;
						$line =~ s/^\$defaultgwif=.*/\$defaultgwif=\"\"\;/g;
					}
				}
			}
			untie @contents;

			&reloadL4FarmsSNAT() if $status == 0;

			return $status;
		}
	}

	return $status;
}

=begin nd
Function: delIp

	Deletes an IP address from an interface

Parameters:
	if - Name of interface.
	ip - IP address.
	netmask - Network mask.

Returns:
	integer - ip command return code.

See Also:
	<addIp>
=cut
# Execute command line to delete an IP from an interface
sub delIp    # 	($if, $ip ,$netmask)
{
	my ( $if, $ip, $netmask ) = @_;

	&zenlog( "Deleting ip $ip/$netmask from interface $if" );

	# Vini
	if ( $if =~ /\:/ )
	{
		( $if ) = split ( /\:/, $if );
	}

	my $ip_cmd = "$ip_bin addr del $ip/$netmask dev $if";
	my $status = &logAndRun( $ip_cmd );

	return $status;
}

=begin nd
Function: addIp

	Add an IPv4 to an Interface, Vlan or Vini

Parameters:
	if_ref - network interface hash reference.

Returns:
	integer - ip command return code.

See Also:
	<delIp>, <setIfacesUp>
=cut
# Execute command line to add an IPv4 to an Interface, Vlan or Vini
sub addIp    # ($if_ref)
{
	my ( $if_ref ) = @_;

	&zenlog(
			 "Adding IP $$if_ref{addr}/$$if_ref{mask} to interface $$if_ref{name}" );

	# finish if the address is already assigned
	my $routed_iface = $$if_ref{ dev };
	$routed_iface .= ".$$if_ref{vlan}"
	  if defined $$if_ref{ vlan } && $$if_ref{ vlan } ne '';

	my $extra_params = '';
	$extra_params = 'nodad' if $$if_ref{ ip_v } == 6;

	my @ip_output = `$ip_bin -$$if_ref{ip_v} addr show dev $routed_iface`;

	if ( grep /$$if_ref{addr}\//, @ip_output )
	{
		return 0;
	}

	my $ip_cmd;

	my $broadcast_opt = ( $$if_ref{ ip_v } == 4 ) ? 'broadcast +' : '';

	# $if is a Virtual Network Interface
	if ( defined $$if_ref{ vini } && $$if_ref{ vini } ne '' )
	{
		my ( $toif ) = split ( ':', $$if_ref{ name } );

		$ip_cmd =
		  "$ip_bin addr add $$if_ref{addr}/$$if_ref{mask} $broadcast_opt dev $toif label $$if_ref{name} $extra_params";
	}

	# $if is a Vlan
	elsif ( defined $$if_ref{ vlan } && $$if_ref{ vlan } ne '' )
	{
		$ip_cmd =
		  "$ip_bin addr add $$if_ref{addr}/$$if_ref{mask} $broadcast_opt dev $$if_ref{name} $extra_params";
	}

	# $if is a Network Interface
	else
	{
		$ip_cmd =
		  "$ip_bin addr add $$if_ref{addr}/$$if_ref{mask} $broadcast_opt dev $$if_ref{name} $extra_params";
	}

	my $status = &logAndRun( $ip_cmd );

	return $status;
}

=begin nd
Function: getConfigInterfaceList

	Get a reference to an array of all the interfaces saved in files.

Parameters:
	none - .

Returns:
	scalar - reference to array of configured interfaces.

See Also:
	zenloadbalanacer, zcluster-manager, <getIfacesFromIf>,
	<getActiveInterfaceList>, <getSystemInterfaceList>, <getFloatInterfaceForAddress>
=cut
sub getConfigInterfaceList
{
	my @configured_interfaces;
	my $configdir = &getGlobalConfiguration( 'configdir' );

	if ( opendir my $dir, "$configdir" )
	{
		for my $filename ( readdir $dir )
		{
			if ( $filename =~ /if_(.+)_conf/ )
			{
				my $if_name = $1;
				my $if_ref;

				$if_ref = &getInterfaceConfig( $if_name, 4 );
				if ( $$if_ref{ addr } )
				{
					push @configured_interfaces, $if_ref;
				}

				$if_ref = &getInterfaceConfig( $if_name, 6 );
				if ( $$if_ref{ addr } )
				{
					push @configured_interfaces, $if_ref;
				}
			}
		}

		closedir $dir;
	}
	else
	{
		&zenlog( "Error reading directory $configdir: $!" );
	}

	return \@configured_interfaces;
}

=begin nd
Function: getIfacesFromIf

	Get List of Vinis or Vlans from a network interface.

Parameters:
	if_name - interface name.
	type - "vini" or "vlan".

Returns:
	list - list of interface references.

See Also:
	Only used in: <setIfacesUp>
=cut
# Get List of Vinis or Vlans from an interface
sub getIfacesFromIf    # ($if_name, $type)
{
	my $if_name = shift;    # Interface's Name
	my $type    = shift;    # Type: vini or vlan
	my @ifaces;

	my @configured_interfaces = @{ &getConfigInterfaceList() };

	for my $interface ( @configured_interfaces )
	{
		next if $$interface{ name } !~ /^$if_name.+/;

		# get vinis
		if ( $type eq "vini" && $$interface{ vini } ne '' )
		{
			push @ifaces, $interface;
		}

		# get vlans (including vlan:vini)
		elsif (    $type eq "vlan"
				&& $$interface{ vlan } ne ''
				&& $$interface{ vini } eq '' )
		{
			push @ifaces, $interface;
		}
	}

	return @ifaces;
}

=begin nd
Function: setIfacesUp

	Bring up all Virtual or VLAN interfaces on a network interface.

Parameters:
	if_name - Name of interface.
	type - "vini" or "vlan".

Returns:
	undef - .

Bugs:
	Set VLANs up.

See Also:
	zapi/v3/interfaces.cgi
=cut
# Check if there are some Virtual Interfaces or Vlan with IPv6 and previous UP status to get it up.
sub setIfacesUp    # ($if_name,$type)
{
	my $if_name = shift;    # Interface's Name
	my $type    = shift;    # Type: vini or vlan

	die ( "setIfacesUp: type variable must be 'vlan' or 'vini'" )
	  if $type !~ /^(?:vlan|vini)$/;

	my @ifaces = &getIfacesFromIf( $if_name, $type );

	if ( @ifaces )
	{
		for my $iface ( @ifaces )
		{
			if ( $iface->{ status } eq 'up' )
			{
				&addIp( $iface );
			}
		}

		if ( $type eq "vini" )
		{
			&zenlog( "Virtual interfaces of $if_name have been put up." );
		}
		elsif ( $type eq "vlan" )
		{
			&zenlog( "VLAN interfaces of $if_name have been put up." );
		}
	}

	return;
}

=begin nd
Function: createIf

	Create VLAN network interface

Parameters:
	if_ref - Network interface hash reference.

Returns:
	integer - ip command return code.

See Also:
	zenloadbalancer, <setInterfaceUp>, zapi/v?/interface.cgi
=cut
# create network interface
sub createIf    # ($if_ref)
{
	my $if_ref = shift;

	my $status = 0;

	if ( defined $$if_ref{ vlan } && $$if_ref{ vlan } ne '' )
	{
		&zenlog( "Creating vlan $$if_ref{name}" );

		# enable the parent physical interface
		my $parent_if = &getInterfaceConfig( $$if_ref{ dev }, $$if_ref{ ip_v } );
		$status = &upIf( $parent_if, 'writeconf' );

		my $ip_cmd =
		  "$ip_bin link add link $$if_ref{dev} name $$if_ref{name} type vlan id $$if_ref{vlan}";
		$status = &logAndRun( $ip_cmd );
	}

	return $status;
}

=begin nd
Function: upIf

	Bring up network interface in system and optionally in configuration file

Parameters:
	if_ref - network interface hash reference.
	writeconf - true value to apply change in interface configuration file. Optional.

Returns:
	integer - return code of ip command.

See Also:
	<downIf>
=cut
# up network interface
sub upIf    # ($if_ref, $writeconf)
{
	my ( $if_ref, $writeconf ) = @_;

	my $configdir = &getGlobalConfiguration( 'configdir' );
	my $status    = 0;
	$if_ref->{ status } = 'up';

	if ( $writeconf )
	{
		my $file = "$configdir/if_$$if_ref{name}_conf";

		if ( -f $file )
		{
			my $found = 0;
			tie my @if_lines, 'Tie::File', "$file";
			for my $line ( @if_lines )
			{
				if ( $line =~ /^status=/ )
				{
					$line  = "status=up";
					$found = 1;
					last;
				}
			}

			unshift ( @if_lines, 'status=up' ) if !$found;
			untie @if_lines;
		}
	}

	my $ip_cmd = "$ip_bin link set $$if_ref{name} up";

	$status = &logAndRun( $ip_cmd );

	return $status;
}

=begin nd
Function: downIf

	Bring down network interface in system and optionally in configuration file

Parameters:
	if_ref - network interface hash reference.
	writeconf - true value to apply change in interface configuration file. Optional.

Returns:
	integer - return code of ip command.

See Also:
	<upIf>, <stopIf>, zapi/v?/interface.cgi
=cut
# down network interface in system and configuration file
sub downIf    # ($if_ref, $writeconf)
{
	my ( $if_ref, $writeconf ) = @_;

	if ( ref $if_ref ne 'HASH' )
	{
		&zenlog( "Wrong argument putting down the interface" );
		return -1;
	}

	my $ip_cmd;

	# Set down status in configuration file
	if ( $writeconf )
	{
		my $configdir = &getGlobalConfiguration( 'configdir' );
		my $file      = "$configdir/if_$$if_ref{name}_conf";

		tie my @if_lines, 'Tie::File', "$file";
		for my $line ( @if_lines )
		{
			if ( $line =~ /^status=/ )
			{
				$line = "status=down";
				last;
			}
		}
		untie @if_lines;
	}

	# For Eth and Vlan
	if ( $$if_ref{ vini } eq '' )
	{
		$ip_cmd = "$ip_bin link set $$if_ref{name} down";
	}

	# For Vini
	else
	{
		my ( $routed_iface ) = split ( ":", $$if_ref{ name } );

		$ip_cmd = "$ip_bin addr del $$if_ref{addr}/$$if_ref{mask} dev $routed_iface";
	}

	my $status = &logAndRun( $ip_cmd );

	return $status;
}

=begin nd
Function: stopIf

	Stop network interface, this removes the IP address instead of putting the interface down.

	This is an alternative to downIf which performs better in hardware
	appliances. Because if the interface is not brought down it wont take
	time to bring the interface back up and enable the link.

Parameters:
	if_ref - network interface hash reference.

Returns:
	integer - return code of ip command.

Bugs:
	Remove VLAN interface and bring it up.

See Also:
	<downIf>

	Only used in: zenloadbalancer
=cut
# stop network interface
sub stopIf    # ($if_ref)
{
	my $if_ref = shift;
	my $status = 0;
	
	my $if = $$if_ref{name};
	# If $if is Vini do nothing
	if ( $$if_ref{ vini } eq '' )
	{
		# If $if is a Interface, delete that IP
		my $ip_cmd = "$ip_bin address flush dev $$if_ref{name}";
		$status = &logAndRun( $ip_cmd );

		# If $if is a Vlan, delete Vlan
		if ( $$if_ref{ vlan } ne '' )
		{
			$ip_cmd = "$ip_bin link delete $$if_ref{name} type vlan";
			$status = &logAndRun( $ip_cmd );
		}

		#ensure Link Up
		if ( $$if_ref{ status } eq 'up' )
		{
			$ip_cmd = "$ip_bin link set $$if_ref{name} up";
			$status = &logAndRun( $ip_cmd );
		}

		my $rttables = &getGlobalConfiguration( 'rttables' );

		# Delete routes table
		open ROUTINGFILE, '<', $rttables;
		my @contents = <ROUTINGFILE>;
		close ROUTINGFILE;

		@contents = grep !/^...\ttable_$if$/, @contents;

		open ROUTINGFILE, '>', $rttables;
		print ROUTINGFILE @contents;
		close ROUTINGFILE;
	}

	#if virtual interface
	if ( $if =~ /\:/ )
	{
		my @ifphysic = split ( /:/, $if );

		&zenlog( "Stopping if $if" );
		my $ip = $$if_ref{addr};
		if ( $ip =~ /\./ )
		{
			my ( $net, $mask ) = ipv4_network( "$ip / $$if_ref{mask}" );
			&zenlog(
					 "running '$ip_bin addr del $ip/$mask brd + dev $ifphysic[0] label $if' " );
			my @eject = `$ip_bin addr del $ip/$mask brd + dev $ifphysic[0] label $if`;

		}

	}

	return $status;
}

=begin nd
Function: delIf

	Remove system and stored settings and statistics of a network interface.

Parameters:
	if_ref - network interface hash reference.

Returns:
	integer - return code ofip command.

See Also:
	
=cut
# delete network interface configuration and from the system
sub delIf    # ($if_ref)
{
	my ( $if_ref ) = @_;

	my $status;
	my $configdir = &getGlobalConfiguration( 'configdir' );
	my $file      = "$configdir/if_$$if_ref{name}\_conf";
	my $has_more_ips;

	# remove stack line
	open ( my $in_fh,  '<', "$file" );
	open ( my $out_fh, '>', "$file.new" );

	if ( $in_fh && $out_fh )
	{
		while ( my $line = <$in_fh> )
		{
			if ( $line !~ /$$if_ref{addr}/ )
			{
				print $out_fh $line;
				$has_more_ips++ if $line =~ /;/;
			}
		}

		close $in_fh;
		close $out_fh;

		rename "$file.new", "$file";

		if ( !$has_more_ips )
		{
			# remove file only if not a nic interface
			# nics need to store status even if not configured, for vlans
			if ( $$if_ref{ name } ne $$if_ref{ dev } )
			{
				unlink ( $file ) or return 1;
			}
		}
	}
	else
	{
		&zenlog( "Error opening $file: $!" );
		$status = 1;
	}

	if ( $status )
	{
		return $status;
	}

	# If $if is Vini do nothing
	if ( $$if_ref{ vini } eq '' )
	{
		# If $if is a Interface, delete that IP
		my $ip_cmd =
		  "$ip_bin addr del $$if_ref{addr}/$$if_ref{mask} dev $$if_ref{name}";
		$status = &logAndRun( $ip_cmd );

		# If $if is a Vlan, delete Vlan
		if ( $$if_ref{ vlan } ne '' )
		{
			$ip_cmd = "$ip_bin link delete $$if_ref{name} type vlan";
			$status = &logAndRun( $ip_cmd );
		}

		# check if alternative stack is in use
		my $ip_v_to_check = ( $$if_ref{ ip_v } == 4 ) ? 6 : 4;
		my $interface = &getInterfaceConfig( $$if_ref{ name }, $ip_v_to_check );

		if ( !$interface )
		{
			my $rttables = &getGlobalConfiguration( 'rttables' );

			# Delete routes table, complementing writeRoutes()
			open ROUTINGFILE, '<', $rttables;
			my @contents = <ROUTINGFILE>;
			close ROUTINGFILE;

			@contents = grep !/^...\ttable_$$if_ref{name}$/, @contents;

			open ROUTINGFILE, '>', $rttables;
			print ROUTINGFILE @contents;
			close ROUTINGFILE;
		}
	}

	# delete graphs
	&delGraph ( $$if_ref{name}, "iface" );
	#~ unlink ( "/usr/local/zenloadbalancer/www/img/graphs/$$if_ref{name}\_d.png" );
	#~ unlink ( "/usr/local/zenloadbalancer/www/img/graphs/$$if_ref{name}\_m.png" );
	#~ unlink ( "/usr/local/zenloadbalancer/www/img/graphs/$$if_ref{name}\_w.png" );
	#~ unlink ( "/usr/local/zenloadbalancer/www/img/graphs/$$if_ref{name}\_y.png" );
	#~ unlink ( "/usr/local/zenloadbalancer/app/zenrrd/rrd/$$if_ref{name}iface.rrd" );

	return $status;
}

=begin nd
Function: getDefaultGW

	Get system or interface default gateway.

Parameters:
	if - interface name. Optional.

Returns:
	scalar - Gateway IP address.

See Also:
	<getIfDefaultGW>
=cut
# get default gw for interface
sub getDefaultGW    # ($if)
{
	my $if = shift;    # optional argument

	my @line;
	my @defgw;
	my $gw;
	my @routes = "";
	
	if ( $if )
	{
		my $cif = $if;
		if ( $if =~ /\:/ )
		{
			my @iface = split ( /\:/, $cif );
			$cif = $iface[0];
		}

		open ( ROUTINGFILE, &getGlobalConfiguration( 'rttables' ) );

		if ( grep { /^...\ttable_$cif$/ } <ROUTINGFILE> )
		{
			@routes = `$ip_bin route list table table_$cif`;
		}

		close ROUTINGFILE;
		@defgw = grep ( /^default/, @routes );
		@line = split ( / /, $defgw[0] );
		$gw = $line[2];
		return $gw;
	}
	else
	{
		@routes = `$ip_bin route list`;
		@defgw  = grep ( /^default/, @routes );
		@line   = split ( / /, $defgw[0] );
		$gw     = $line[2];
		return $gw;
	}
}

=begin nd
Function: getIPv6DefaultGW

	Get system IPv6 default gateway.

Parameters:
	none - .

Returns:
	scalar - IPv6 default gateway address.

See Also:
	<getDefaultGW>, <getIPv6IfDefaultGW>
=cut
sub getIPv6DefaultGW    # ()
{
	my @routes = `$ip_bin -6 route list`;
	my ( $default_line ) = grep { /^default/ } @routes;

	my $default_gw;
	if ( $default_line )
	{
		$default_gw = ( split ( ' ', $default_line ) )[2];
	}

	return $default_gw;
}

=begin nd
Function: getIPv6IfDefaultGW

	Get network interface to IPv6 default gateway.

Parameters:
	none - .

Returns:
	scalar - Interface to IPv6 default gateway.

See Also:
	<getIPv6DefaultGW>, <getIfDefaultGW>
=cut
sub getIPv6IfDefaultGW    # ()
{
	my @routes = `$ip_bin -6 route list`;
	my ( $default_line ) = grep { /^default/ } @routes;

	my $if_default_gw;
	if ( $default_line )
	{
		$if_default_gw = ( split ( ' ', $default_line ) )[4];
	}

	return $if_default_gw;
}

=begin nd
Function: getIfDefaultGW

	Get network interface to default gateway.

Parameters:
	none - .

Returns:
	scalar - Interface to default gateway address.

See Also:
	<getDefaultGW>, <getIPv6IfDefaultGW>
=cut
# get interface for default gw
sub getIfDefaultGW    # ()
{
	my @routes = `$ip_bin route list`;
	my @defgw  = grep ( /^default/, @routes );
	my @line   = split ( / /, $defgw[0] );

	return $line[4];
}

=begin nd
Function: iponif

	Get the (primary) ip address on a network interface.

	A copy of this function is in zeninotify.

Parameters:
	if - interface namm.

Returns:
	scalar - string with IP address.

See Also:
	<getInterfaceOfIp>, <_runDatalinkFarmStart>, <_runDatalinkFarmStop>, <zeninotify.pl>
=cut
#know if and return ip
sub iponif            # ($if)
{
	my $if = shift;

	use IO::Socket;
	use IO::Interface qw(:flags);

	my $s = IO::Socket::INET->new( Proto => 'udp' );
	my @interfaces = $s->if_list;
	my $iponif = $s->if_addr( $if );

	return $iponif;
}

=begin nd
Function: maskonif

	Get the network mask of an network interface (primary) address.

Parameters:
	if - interface namm.

Returns:
	scalar - string with network address.

See Also:
	<_runDatalinkFarmStart>, <_runDatalinkFarmStop>
=cut
# return the mask of an if
sub maskonif    # ($if)
{
	my $if = shift;

	use IO::Socket;
	use IO::Interface qw(:flags);
	my $s = IO::Socket::INET->new( Proto => 'udp' );
	my @interfaces = $s->if_list;
	my $maskonif = $s->if_netmask( $if );
	return $maskonif;
}

=begin nd
Function: getNetstatFilter

	Filter conntrack output

Parameters:
	proto - Protocol: "tcp", "udp", more?
	state - State: ??
	ninfo - Ninfo: ??
	fpid - Fpid: ??
	netstat - Output from getConntrack

Returns:
	list - Filtered netstat array.

See Also:
	Input from: <getConntrack>

	<farm-rrd.pl>, zapi/v?/system_stats.cgi

	<getBackendEstConns>, <getFarmEstConns>, <getBackendSYNConns>, <getFarmSYNConns>

	<getL4BackendEstConns>, <getL4FarmEstConns>, <getL4BackendSYNConns>, <getL4FarmSYNConns>
	<getHTTPBackendEstConns>, <getHTTPFarmEstConns>, <getHTTPBackendTWConns>, <getHTTPBackendSYNConns>, <getHTTPFarmSYNConns>, <getGSLBFarmEstConns>
=cut
# Returns array execution of netstat
sub getNetstatFilter    # ($proto,$state,$ninfo,$fpid,@netstat)
{
	my ( $proto, $state, $ninfo, $fpid, @netstat ) = @_;

	my $lfpid = $fpid;
	chomp ( $lfpid );

	#print "proto $proto ninfo $ninfo state $state pid $fpid<br/>";
	if ( $lfpid )
	{
		$lfpid = "\ $lfpid\/";
	}
	if ( $proto ne "tcp" && $proto ne "udp" )
	{
		$proto = "";
	}
	my @output =
	  grep { /${proto}.*\ ${ninfo}\ .*\ ${state}.*${lfpid}/ } @netstat;

	return @output;
}

=begin nd
Function: getDevData

	[NOT USED] Get network interfaces statistics.

	Includes bytes and packets received and transmited.

Parameters:
	dev - interface name. Optional.

Returns:
	list - array with statistics?

Bugs:
	NOT USED
=cut
sub getDevData    # ($dev)
{
	my $dev = shift;

	open FI, "<", "/proc/net/dev";

	my $exit = "false";
	my @dataout;
	
	my $line;
	while ( $line = <FI> && $exit eq "false" )
	{
		if ( $dev ne "" )
		{
			my @curline = split ( ":", $line );
			my $ini = $curline[0];
			chomp ( $ini );
			if ( $ini ne "" && $ini =~ $dev )
			{
				$exit = "true";
				my @datain = split ( " ", $curline[1] );
				push ( @dataout, $datain[0] );
				push ( @dataout, $datain[1] );
				push ( @dataout, $datain[8] );
				push ( @dataout, $datain[9] );
			}
		}
		else
		{
			if ( $line ne // )
			{
				push ( @dataout, $line );
			}
			else
			{
				$exit = "true";
			}
		}
	}
	close FI;

	return @dataout;
}

=begin nd
Function: sendGArp

	Send gratuitous ARP frames.

	Broadcast an ip address with ARP frames through a network interface.
	Also, pings the interface gateway.

Parameters:
	if - interface name.
	ip - ip address.

Returns:
	undef - .

See Also:
	<broadcastInterfaceDiscovery>, <sendGPing>
=cut
# send gratuitous ARP frames
sub sendGArp    # ($if,$ip)
{
	my ( $if, $ip ) = @_;

	my @iface      = split ( ":", $if );
	my $arping_bin = &getGlobalConfiguration( 'arping_bin' );
	my $arping_cmd = "$arping_bin -c 2 -A -I $iface[0] $ip";

	&zenlog( "$arping_cmd" );
	system ( "$arping_cmd &" );

	&sendGPing( $iface[0] );
}

=begin nd
Function: setIpForward

	Set IP forwarding on/off

Parameters:
	arg - "true" to turn it on or ("false" to turn it off).

Returns:
	scalar - return code setting the value.

See Also:
	<_runL4FarmStart>, <_runDatalinkFarmStart>
=cut
# Enable(true) / Disable(false) IP Forwarding
sub setIpForward    # ($arg)
{
	my $arg = shift;

	my $status = -1;

	my $switch = ( $arg eq 'true' )
	  ? 1           # set switch on if arg == 'true'
	  : 0;          # switch is off by default

	&zenlog( "setting $arg to IP forwarding " );

	# switch forwarding as requested
	system ( "echo $switch > /proc/sys/net/ipv4/conf/all/forwarding" );
	system ( "echo $switch > /proc/sys/net/ipv4/ip_forward" );
	$status = $?;
	system ( "echo $switch > /proc/sys/net/ipv6/conf/all/forwarding" );

	return $status;
}

=begin nd
Function: flushCacheRoutes

	[NOT USED] Flush cache routes

Parameters:
	none - .

Returns:
	none - .

Bugs:
	NOT USED
=cut
# Flush cache routes
sub flushCacheRoutes    # ()
{
	&zenlog( "flushing routes cache" );
	system ( "$ip_bin route flush cache >/dev/null 2>$1" );
}

=begin nd
Function: uplinkUsed

	[NOT USED] Return if interface is used for datalink farm

Parameters:
	none - .

Returns:
	boolean - "true" or "false".

Bugs:
	NOT USED
=cut
# Return if interface is used for datalink farm
sub uplinkUsed          # ($if)
{
	my $if = shift;

	my @farms  = &getFarmsByType( "datalink" );
	my $output = "false";

	foreach my $farm ( @farms )
	{
		my $farmif = &getFarmVip( "vipp", $farm );
		my $status = &getFarmStatus( $farm );
		if ( $status eq "up" && $farmif eq $if )
		{
			$output = "true";
		}
	}
	return $output;
}

=begin nd
Function: isValidPortNumber

	Check if the input is a valid port number.

Parameters:
	port - Port number.

Returns:
	boolean - "true" or "false".

See Also:
	snmp_functions.cgi, check_functions.cgi, zapi/v3/post.cgi, zapi/v3/put.cgi
=cut
sub isValidPortNumber    # ($port)
{
	my $port = shift;
	my $valid;

	if ( $port >= 1 && $port <= 65535 )
	{
		$valid = 'true';
	}
	else
	{
		$valid = 'false';
	}

	return $valid;
}

=begin nd
Function: getInterfaceList

	Return a list of all network interfaces detected in the system.

Parameters:
	None.

Returns:
	array - list of network interface names.
	array empty - if no network interface is detected.

See Also:
	<listActiveInterfaces>
=cut
sub getInterfaceList
{
	my @interfaces;
	my $iface;
	my $localiface;

	my @iplist = `ip addr list`;
	foreach my $line ( @iplist )
	{
		if ( $line =~ /^\d+: / )
		{
			my @linelist = split /[:@,\s\/]+/, $line;
			$iface      = $linelist[1];
			$localiface = $iface;
			goto addiface;
		}
		if ( $iface ne "" && $line =~ /inet.*$iface.+/ )
		{
			my @linelist = split /[\s\/]+/, $line;
			$localiface = $linelist[scalar @linelist - 1];
			goto addiface;
		}
		next;
	  addiface:
		push ( @interfaces, $localiface );
		next;
	}

	return @interfaces;
}

=begin nd
Function: getIOSocket

	Get a IO Socket. Used to get information about interfaces.

Parameters:
	none - .

Returns:
	scalar - IO::Socket::INET object reference.

See Also:
	<getVipOutputIp>, <zenloadbalancer>
=cut
# IO Socket is needed to get information about interfaces
sub getIOSocket
{
	# udp for a basic socket
	return IO::Socket::INET->new( Proto => 'udp' );
}

=begin nd
Function: getVipOutputIp

	[NOT USED] Get outbound IP address (actually NIC) of vip.

Parameters:
	vip - vip address.

Returns:
	scalar - IP address string.

Bugs:
	NOT USED
=cut
sub getVipOutputIp    # ($vip)
{
	my $vip = shift;

	my $socket = &getIOSocket();
	my $device;

	foreach my $interface ( &getInterfaceList( $socket ) )
	{
		# ignore/skip localhost
		next if $interface eq "lo";

		# get interface ip
		my $ip = $socket->if_addr( $interface );

		# get NIC of our vip
		if ( $ip eq $vip )
		{
			# remove alias part of interface name
			( $device ) = split ( ":", $interface );
			last;
		}
	}

	return $socket->if_addr( $device );
}

=begin nd
Function: getVirtualInterfaceFilenameList

	[NOT USED] Get a list of the virtual interfaces configuration filenames.

Parameters:
	none - .

Returns:
	list - Every configuration file of virtual interfaces.

Bugs:
	NOT USED
=cut
sub getVirtualInterfaceFilenameList
{
	opendir ( DIR, &getGlobalConfiguration( 'configdir' ) );

	my @filenames = grep ( /^if.*\:.*$/, readdir ( DIR ) );

	closedir ( DIR );

	return @filenames;
}

=begin nd
Function: getInterfaceOfIp

	Get the name of the interface with such IP address.

Parameters:
	ip - string with IP address.

Returns:
	scalar - Name of interface, if found, undef otherwise.

See Also:
	<enable_cluster>, <new_farm>, <modify_datalink_farm>
=cut
sub getInterfaceOfIp    # ($ip)
{
	my $ip = shift;

	foreach my $iface ( &getInterfaceList() )
	{
		# return interface if found in the list
		return $iface if &iponif( $iface ) eq $ip;
	}

	# returns an invalid interface name, an undefined variable
	return undef;
}

1;
