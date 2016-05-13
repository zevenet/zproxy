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

use IO::Socket;

my $ext = 0;

if ( -e "/usr/local/zenloadbalancer/www/networking_functions_ext.cgi" )
{
	require "/usr/local/zenloadbalancer/www/networking_functions_ext.cgi";
	$ext = 1;
}

#check if a port in a ip is up
sub checkport    # ($host,$port)
{
	my ( $host, $port ) = @_;

	#use strict;
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
		$ip = $s->if_addr( $if );
		my $flags = $s->if_flags( $if );

		if ( $flags & IFF_RUNNING && $ip !~ /127.0.0.1/ && $ip !~ /0.0.0.0/ )
		{
			push ( @listinterfaces, $ip );
		}
	}
	return @listinterfaces;
}

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

#check if a ip is ok structure
sub ipisok    # ($checkip ,$version)
{
	my $checkip = shift;
	my $version = shift;
	my $return  = "false";

	use Data::Validate::IP;

	if ( $version != 6 )
	{
		if ( is_ipv4( $checkip ) )
		{
			$return = "true";
		}
	}

	if ( $version != 4 )
	{
		if ( is_ipv6( $checkip ) )
		{
			$return = "true";
		}
	}

	return $return;
}

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

#function check if interface exist
sub ifexist    # ($nif)
{
	my $nif = shift;

	use IO::Socket;
	use IO::Interface qw(:flags);
	my $s = IO::Socket::INET->new( Proto => 'udp' );
	my @interfaces = $s->if_list;

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

# saving network interfaces config files
sub writeConfigIf    # ($if,$string)
{
	my ( $if, $string ) = @_;

	open CONFFILE, "> $configdir/if\_$if\_conf";
	print CONFFILE "$string\n";
	close CONFFILE;
	return $?;
}

# create table route identification, complemented in delIf()
sub writeRoutes      # ($if_name)
{
	my $if_name = shift;

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
		open ( ROUTINGFILE, ">>$rttables" );
		print ROUTINGFILE "$rtnumber\ttable_$if_name\n";
		close ROUTINGFILE;
	}
}

# add local network into routing table
sub addlocalnet    # ($if_ref)
{
	my $if_ref = shift;

	use NetAddr::IP;
	my $ip = new NetAddr::IP( $$if_ref{ addr }, $$if_ref{ mask } );
	my $net = $ip->network();

	my $ip_cmd =
	  "$ip_bin -$$if_ref{ip_v} route replace $net dev $$if_ref{name} src $$if_ref{addr} table table_$$if_ref{name} $routeparams";

	return &logAndRun( $ip_cmd );
}

# ask for rules
sub isRule    # ($if_ref, $toif)
{
	my ( $if_ref, $toif ) = @_;

	$toif = $$if_ref{ name } if !$toif;

	my $existRule  = 0;
	my @eject      = `$ip_bin -$$if_ref{ip_v} rule list`;
	my $expression = "from $$if_ref{addr} lookup table_$toif";

	$existRule = grep /$expression/, @eject;

	return $existRule;
}

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
	if ( ! defined $$if_ref{ vini } || $$if_ref{ vini } eq '' )
	{
		if ( $table eq "local" )
		{
			# &delRoutes( "local", $if );
			&addlocalnet( $if_ref );

			if ( $$if_ref{ gateway } )
			{
				my $ip_cmd =
				  "$ip_bin -$$if_ref{ip_v} route replace default via $$if_ref{gateway} dev $$if_ref{name} table table_$$if_ref{name} $routeparams";
				$status = &logAndRun( "$ip_cmd" );
			}

			if ( &isRule( $if_ref ) == 0 )
			{
				my $ip_cmd =
				  "$ip_bin -$$if_ref{ip_v} rule add from $$if_ref{addr} table table_$$if_ref{name}";
				$status = &logAndRun( "$ip_cmd" );
			}
		}
		else
		{
			# Apply routes on the global table
			# &delRoutes( "global", $if );
			if ( $gateway )
			{
				my $ip_cmd =
				  "$ip_bin -$$if_ref{ip_v} route replace default via $gateway dev $$if_ref{name} $routeparams";
				$status = &logAndRun( "$ip_cmd" );

				tie my @contents, 'Tie::File', "$globalcfg";
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

		if ( &isRule( $if_ref, $toif ) eq 0 )
		{
			my $ip_cmd =
			  "$ip_bin -$$if_ref{ip_v} rule add from $$if_ref{addr} table table_$toif";
			$status = &logAndRun( "$ip_cmd" );
		}
	}

	return $status;
}

# delete routes
sub delRoutes    # ($table,$if_ref)
{
	my ( $table, $if_ref ) = @_;

	my $status;

	&zenlog(
		   "Deleting $table routes for IPv$$if_ref{ip_v} in interface $$if_ref{name}" );

	if ( ! defined $$if_ref{ vini } || $$if_ref{ vini } eq '' )
	{
		if ( $table eq "local" )
		{
			# Delete routes on the interface table
			if ( ! defined $$if_ref{ vlan } || $$if_ref{ vlan } eq '' )
			{
				return 1;
			}

			my $ip_cmd = "$ip_bin -$$if_ref{ip_v} route flush table table_$$if_ref{name}";
			$status = &logAndRun( "$ip_cmd" );

			$ip_cmd =
			  "$ip_bin -$$if_ref{ip_v} rule del from $$if_ref{addr} table table_$$if_ref{name}";
			$status = &logAndRun( "$ip_cmd" );

			return $status;
		}
		else
		{
			# Delete routes on the global table
			my $ip_cmd = "$ip_bin -$$if_ref{ip_v} route del default";
			$status = &logAndRun( "$ip_cmd" );

			tie my @contents, 'Tie::File', "$globalcfg";
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

			return $status;
		}
	}

	# Delete rules for virtual interfaces
	my ( $iface ) = split ( ':', $$if_ref{ name } );
	my $ip_cmd =
	  "$ip_bin -$$if_ref{ip_v} rule del from $$if_ref{addr} table table_$iface";
	$status = &logAndRun( "$ip_cmd" );

	return $status;
}

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
	$status = &logAndRun( $ip_cmd );

	return $status;
}

# Execute command line to add an IPv4 to an Interface, Vlan or Vini
sub addIp    # ($if_ref)
{
	my ( $if_ref ) = @_;

	&zenlog(
			  "Adding IP $$if_ref{addr}/$$if_ref{mask} to interface $$if_ref{name}" );

	# finish if the address is already assigned
	my $routed_iface = $$if_ref{ dev };
	$routed_iface .= ".$$if_ref{vlan}" if defined $$if_ref{ vlan } && $$if_ref{ vlan } ne '';

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

sub getConfigInterfaceList
{
	my @configured_interfaces;

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
		if ( $type eq "vini" && $$interface{ vini } )
		{
			push @ifaces, $interface;
		}

		# get vlans (including vlan:vini)
		elsif ( $type eq "vlan" && $$interface{ vlan } )
		{
			push @ifaces, $interface;
		}
	}

	return @ifaces;
}

# Check if there are some Virtual Interfaces or Vlan with IPv6 and previous UP status to get it up.
sub setIfacesUp    # ($if_name,$type)
{
	my $if_name = shift;    # Interface's Name
	my $type    = shift;    # Type: vini or vlan

	my @ifaces = &getIfacesFromIf( $if_name, $type );

	if ( @ifaces )
	{
		for my $iface ( @ifaces )
		{
			if ( $type eq "vini" || ( $type eq "vlan" && !$$iface{ vini } ) )
			{
				if ( $$iface{ status } eq 'up' && $$iface{ ip_v } == 6 )
				{
					&addIp( $iface );
				}
			}
		}

		if ( $type eq "vini" )
		{
			&zenlog(
				"All the Virtual Network interfaces with IPv6 and status up of $if_name have been put in up status."
			);
		}
		elsif ( $type eq "vini" )
		{
			&zenlog(
				  "All the Vlan with IPv6 and status up of $if_name have been put in up status."
			);
		}
	}
	else
	{
		&logfile("Error reading directory $configdir: $!");
	}

	return \@configured_interfaces;
}

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

# up network interface
sub upIf    # ($if_ref, $writeconf)
{
	my ( $if_ref, $writeconf ) = @_;

	my $status = 0;
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
					$line = "status=up";
					$found = 1;
					last;
				}
			}

			unshift( @if_lines, 'status=up' ) if ! $found;
			untie @if_lines;
		}
	}

	my $ip_cmd = "$ip_bin link set $$if_ref{name} up";
	$status = &logAndRun( $ip_cmd );

	return $status;
}

# down network interface in system and configuration file
sub downIf    # ($if_ref, $writeconf)
{
	my ( $if_ref, $writeconf ) = @_;

	if ( ref $if_ref ne 'HASH' )
	{
		&zenlog("Wrong argument putting down the interface");
		return -1;
	}

	my $ip_cmd;

	# Set down status in configuration file
	if ( $writeconf )
	{
		my $file = "$configdir/if_$$if_ref{name}_conf";

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

	$status = &logAndRun( $ip_cmd );

	return $status;
}

# stop network interface
sub stopIf    # ($if)
{
	my $if     = shift;
	my $status = 0;

	# If $if is Vini do nothing
	if ( $$if_ref{vini} eq '' )
	{
		# If $if is a Interface, delete that IP
		my $ip_cmd = "$ip_bin addr del $$if_ref{addr}/$$if_ref{mask} dev $$if_ref{name}";
		$status = &logAndRun($ip_cmd);
		
		# If $if is a Vlan, delete Vlan
		if ( $$if_ref{vlan} ne '' )
		{
			$ip_cmd = "$ip_bin link delete $$if_ref{name} type vlan";
			$status = &logAndRun($ip_cmd);
		}
		else
		{
			@eject = `$ip_bin link set dev $if up`;
		}

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

		&logfile( "Stopping if $if" );
		my $ip = &iponif( $if );
		if ( $ip =~ /\./ )
		{
			$ipmask = &maskonif( $if );
			my ( $net, $mask ) = ipv4_network( "$ip / $ipmask" );
			&logfile(
					 "running '$ip_bin addr del $ip/$mask brd + dev @ifphysic[0] label $if' " );
			@eject = `$ip_bin addr del $ip/$mask brd + dev @ifphysic[0] label $if`;

		}

	}

	return $status;
}

# delete network interface configuration and from the system
sub delIf    # ($if_ref)
{
	my ( $if_ref ) = @_;

	my $status;
	my $file = "$configdir/if_$$if_ref{name}\_conf";
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
	unlink ( "/usr/local/zenloadbalancer/app/zenrrd/rrd/$$if_ref{name}iface.rrd" );

	return $status;
}

# get default gw for interface
sub getDefaultGW    # ($if)
{
	my $if = shift;    # optional argument

	if ( $if )
	{
		$cif = $if;
		if ( $if =~ /\:/ )
		{
			@iface = split ( /\:/, $cif );
			$cif = $iface[0];
		}

		@routes = "";
		open ( ROUTINGFILE, $rttables );
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
		@routes = "";
		@routes = `$ip_bin route list`;
		@defgw  = grep ( /^default/, @routes );
		@line   = split ( / /, $defgw[0] );
		$gw     = $line[2];
		return $gw;
	}
}

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

# get interface for default gw
sub getIfDefaultGW    # ()
{
	my @routes = `$ip_bin route list`;
	my @defgw  = grep ( /^default/, @routes );
	my @line   = split ( / /, $defgw[0] );

	return $line[4];
}

#know if and return ip
sub iponif            # ($if)
{
	my $if = shift;

	use IO::Socket;
	use IO::Interface qw(:flags);

	my $s = IO::Socket::INET->new( Proto => 'udp' );
	my @interfaces = $s->if_list;
	$iponif = $s->if_addr( $if );

	return $iponif;
}

# return the mask of an if
sub maskonif    # ($if)
{
	my $if = shift;

	use IO::Socket;
	use IO::Interface qw(:flags);
	my $s = IO::Socket::INET->new( Proto => 'udp' );
	my @interfaces = $s->if_list;
	$maskonif = $s->if_netmask( $if );
	return $maskonif;
}

#return the gw of a if
sub gwofif    # ($if)
{
	my $if = shift;

	open FGW, "<$configdir\/if\_$if\_conf";
	@gw_if = <FGW>;
	close FGW;
	@gw_ifspt = split ( /:/, $gw_if[0] );
	chomp ( $gw_ifspt[5] );
	return $gw_ifspt[5];
}

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

sub getDevData    # ($dev)
{
	my $dev = shift;

	open FI, "<", "/proc/net/dev";

	my $exit = "false";
	my @dataout;

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

# send gratuitous ARP frames
sub sendGArp    # ($if,$ip)
{
	my ( $if, $ip ) = @_;

	my @iface = split ( ":.", $if );
	&zenlog( "sending '$arping_bin -c 2 -A -I $iface[0] $ip' " );
	my @eject = `$arping_bin -c 2 -A -I $iface[0] $ip > /dev/null &`;

	if ( $ext == 1 )
	{
		&sendGPing( $iface[0] );
	}
}

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

# Flush cache routes
sub flushCacheRoutes    # ()
{
	&zenlog( "flushing routes cache" );
	system ( "$ip_bin route flush cache >/dev/null 2>$1" );
}

# Return if interface is used for datalink farm
sub uplinkUsed          # ($if)
{
	my $if = shift;

	my @farms  = &getFarmsByType( "datalink" );
	my $output = "false";

	foreach $farm ( @farms )
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

sub isValidPortNumber    # ($port)
{
	my $port = shift;
	my $valid;

	if ( defined ( $port ) && $port >= 1 && $port <= 65535 )
	{
		$valid = 'true';
	}
	else
	{
		$valid = 'false';
	}

	return $valid;
}

sub getInterfaceList    # ($socket)
{
	my $socket = shift;

	# udp for a basic socket
	$socket = getIOSocket() if !defined ( $socket );

	return $socket->if_list;
}

# IO Socket is needed to get information about interfaces
sub getIOSocket
{
	# udp for a basic socket
	return IO::Socket::INET->new( Proto => 'udp' );
}

sub getVipOutputIp    # ($vip)
{
	my $vip = shift;

	my $socket = &getIOSocket();
	my $device;

	foreach $interface ( &getInterfaceList( $socket ) )
	{
		# ignore/skip localhost
		next if $interface eq "lo";

		# get interface ip
		$ip = $socket->if_addr( $interface );

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

sub getVirtualInterfaceFilenameList
{
	opendir ( DIR, "$configdir" );

	my @filenames = grep ( /^if.*\:.*$/, readdir ( DIR ) );

	closedir ( DIR );

	return @filenames;
}

sub getInterfaceOfIp    # ($ip)
{
	my $ip = shift;

	foreach $iface ( &getInterfaceList() )
	{
		# return interface if fount in the list
		return $iface if &iponif( $iface ) eq $ip;
	}

	# returns an invalid interface name, an undefined variable
	return undef;
}

1;
