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
use Config::Tiny;
use Data::Dumper;
$Data::Dumper::Sortkeys = 1;

=begin nd
Variable: $if_ref

	Reference to a hash representation of a network interface.
	It can be found dereferenced and used as a (%iface or %interface) hash.

	$if_ref->{ name }     - Interface name.
	$if_ref->{ addr }     - IP address. Empty if not configured.
	$if_ref->{ mask }     - Network mask. Empty if not configured.
	$if_ref->{ gateway }  - Interface gateway. Empty if not configured.
	$if_ref->{ status }   - 'up' for enabled, or 'down' for disabled.
	$if_ref->{ ip_v }     - IP version, 4 or 6.
	$if_ref->{ dev }      - Name without VLAN or Virtual part (same as NIC or Bonding)
	$if_ref->{ vini }     - Part of the name corresponding to a Virtual interface. Can be empty.
	$if_ref->{ vlan }     - Part of the name corresponding to a VLAN interface. Can be empty.
	$if_ref->{ mac }      - Interface hardware address.
	$if_ref->{ type }     - Interface type: nic, bond, vlan, virtual.
	$if_ref->{ parent }   - Interface which this interface is based/depends on.
	$if_ref->{ float }    - Floating interface selected for this interface. For routing interfaces only.
	$if_ref->{ is_slave } - Whether the NIC interface is a member of a Bonding interface. For NIC interfaces only.

See also:
	<getInterfaceConfig>, <setInterfaceConfig>, <getSystemInterface>
=cut

=begin nd
Function: sendGPing

	Send gratuitous ICMP packets for L3 aware.

Parameters:
	pif - ping interface name.

Returns:
	none - .

See Also:
	<sendGArp>
=cut
# send gratuitous ICMP packets for L3 aware
sub sendGPing    # ($pif)
{
	my ( $pif ) = @_;

	my $if_conf = &getInterfaceConfig ( $pif );
	my $gw = $if_conf->{ gateway };
	if ( $gw ne "" )
	{
		my $ping_bin = &getGlobalConfiguration('ping_bin');
		my $pingc = &getGlobalConfiguration('pingc');
		my $ping_cmd = "$ping_bin -c $pingc $gw";

		&zenlog( "$ping_cmd" );
		system( "$ping_cmd >/dev/null 2>&1 &" );
	}
	else
	{
		&zenlog( "Gateway not found for $pif interface." );
	}
}

=begin nd
Function: getConntrackExpect

	[NOT USED] Get conntrack sessions.

Parameters:
	none - .

Returns:
	list - list of conntrack sessions.

Bugs:
	NOT USED
=cut
# get conntrack sessions
sub getConntrackExpect    # ($args)
{
	my ( $args ) = @_;

	open CONNS, "</proc/net/nf_conntrack_expect";

	#open CONNS, "</proc/net/nf_conntrack";
	my @expect = <CONNS>;
	close CONNS;

	return @expect;
}

=begin nd
Function: getInterfaceConfig

	Get a hash reference with the stored configuration of a network interface.

Parameters:
	if_name - Interface name.
	ip_version - Interface stack or IP version. 4 or 6 (Default: 4).

Returns:
	scalar - Reference to a network interface hash ($if_ref). undef if the network interface was not found.

Bugs:
	The configuration file exists but there isn't the requested stack.

See Also:
	<$if_ref>

	zcluster-manager, zenbui.pl, zapi/v?/interface.cgi, zcluster_functions.cgi, networking_functions_ext
=cut
sub getInterfaceConfig    # \%iface ($if_name, $ip_version)
{
	my ( $if_name, $ip_version ) = @_;

	my $if_line;
	my $if_status;
	my $configdir = &getGlobalConfiguration('configdir');
	my $config_filename = "$configdir/if_${if_name}_conf";

	$ip_version = 4 if !$ip_version;

	if ( open my $file, '<', "$config_filename" )
	{
		my @lines = grep { !/^(\s*#|$)/ } <$file>;

		for my $line ( @lines )
		{
			my ( undef, $ip ) = split ';', $line;
			my $line_ipversion;

			if ( defined $ip )
			{
				$line_ipversion =
				    ( $ip =~ /:/ )  ? 6
				  : ( $ip =~ /\./ ) ? 4
				  :                   undef;
			}

			if ( defined $line_ipversion && $ip_version == $line_ipversion && !$if_line )
			{
				$if_line = $line;
			}
			elsif ( $line =~ /^status=/ )
			{
				$if_status = $line;
				$if_status =~ s/^status=//;
				chomp $if_status;
			}
		}
		close $file;
	}

	# includes !$if_status to avoid warning
	if ( !$if_line && (!$if_status || $if_status !~ /up/) )
	{
		return undef;
	}

	chomp ( $if_line );
	my @if_params = split ( ';', $if_line );

	# Example: eth0;10.0.0.5;255.255.255.0;up;10.0.0.1;

	use IO::Socket;
	my $socket = IO::Socket::INET->new( Proto => 'udp' );

	my %iface;

	$iface{ name }    = shift @if_params // $if_name;
	$iface{ addr }    = shift @if_params;
	$iface{ mask }    = shift @if_params;
	$iface{ gateway } = shift @if_params;                        # optional
	$iface{ status }  = $if_status;
	$iface{ ip_v }    = ( $iface{ addr } =~ /:/ ) ? '6' : '4';
	$iface{ dev }     = $if_name;
	$iface{ vini }    = undef;
	$iface{ vlan }    = undef;
	$iface{ mac }     = undef;
	$iface{ type }    = &getInterfaceType( $if_name );
	$iface{ parent }  = &getParentInterfaceName( $iface{ name } );

	if ( $iface{ dev } =~ /:/ )
	{
		( $iface{ dev }, $iface{ vini } ) = split ':', $iface{ dev };
	}

	if ( !$iface{ name } ){
		$iface{ name } = $if_name;
	}

	if ( $iface{ dev } =~ /./ )
	{
		# dot must be escaped
		( $iface{ dev }, $iface{ vlan } ) = split '\.', $iface{ dev };
	}

	$iface{ mac } = $socket->if_hwaddr( $iface{ dev } );

	# Interfaces without ip do not get HW addr via socket,
	# in those cases get the MAC from the OS.
	unless ( $iface{ mac } )
	{
		open my $fh, '<', "/sys/class/net/$if_name/address";
		chomp( $iface{ mac } = <$fh> );
		close $fh;
	}

	# complex check to avoid warnings
	if (
		 (
		      !exists ( $iface{ vini } )
		   || !defined ( $iface{ vini } )
		   || $iface{ vini } eq ''
		 )
		 && $iface{ addr }
	  )
	{
		use Config::Tiny;
		my $float = Config::Tiny->read( &getGlobalConfiguration( 'floatfile' ) );

		$iface{ float } = $float->{ _ }->{ $iface{ name } } // '';
	}

	if ( $iface{ type } eq 'nic' )
	{
		$iface{ is_slave } =
		  ( grep { $iface{ name } eq $_ } &getAllBondsSlaves ) ? 'true' : 'false';
	}

	return \%iface;
}

=begin nd
Function: setInterfaceConfig

	Store a network interface configuration.

Parameters:
	if_ref - Reference to a network interface hash.

Returns:
	boolean - 1 on success, or 0 on failure.

See Also:
	<getInterfaceConfig>, <setInterfaceUp>, zenloadbalancer, zenbui.pl, zapi/v?/interface.cgi
=cut
# returns 1 if it was successful
# returns 0 if it wasn't successful
sub setInterfaceConfig    # $bool ($if_ref)
{
	my $if_ref = shift;

	if ( ref $if_ref ne 'HASH' )
	{
		&zenlog( "Input parameter is not a hash reference" );
		return undef;
	}

	&zenlog( "setInterfaceConfig: " . Dumper $if_ref) if &debug();
	my @if_params = ( 'name', 'addr', 'mask', 'gateway' );

	my $if_line = join ( ';', @{ $if_ref }{ @if_params } ) . ';';
	my $configdir = &getGlobalConfiguration('configdir');
	my $config_filename = "$configdir/if_$$if_ref{ name }_conf";

	if ( $if_ref->{ addr } && ! $if_ref->{ ip_v } )
	{
		$if_ref->{ ip_v } = &ipversion( $if_ref->{ addr } )
	}

	if ( !-f $config_filename )
	{
		open my $fh, '>', $config_filename;
		print $fh "status=up\n";
		close $fh;
	}

	# Example: eth0;10.0.0.5;255.255.255.0;up;10.0.0.1;
	if ( tie my @file_lines, 'Tie::File', "$config_filename" )
	{
		my $ip_line_found;

		for my $line ( @file_lines )
		{
			# skip commented and empty lines
			if ( grep { /^(\s*#|$)/ } $line )
			{
				next;
			}

			my ( undef, $ip ) = split ';', $line;

			if ( $$if_ref{ ip_v } eq &ipversion( $ip ) && !$ip_line_found )
			{
				# replace line
				$line          = $if_line;
				$ip_line_found = 'true';
			}
			elsif ( $line =~ /^status=/ )
			{
				$line = "status=$$if_ref{status}";
			}
		}

		if ( !$ip_line_found )
		{
			push ( @file_lines, $if_line );
		}

		untie @file_lines;
	}
	else
	{
		&zenlog( "$config_filename: $!" );

		# returns zero on failure
		return 0;
	}

	# returns a true value on success
	return 1;
}

=begin nd
Function: getDevVlanVini

	Get a hash reference with the interface name divided into: dev, vlan, vini.

Parameters:
	if_name - Interface name.

Returns:
	Reference to a hash with:
	dev - NIC or Bonding part of the interface name.
	vlan - VLAN part of the interface name.
	vini - Virtual interface part of the interface name.

See Also:
	<getParentInterfaceName>, <getSystemInterfaceList>, <getSystemInterface>, zapi/v2/interface.cgi
=cut
sub getDevVlanVini    # ($if_name)
{
	my %if;
	$if{ dev } = shift;

	if ( $if{ dev } =~ /:/ )
	{
		( $if{ dev }, $if{ vini } ) = split ':', $if{ dev };
	}

	if ( $if{ dev } =~ /\./ )    # dot must be escaped
	{
		( $if{ dev }, $if{ vlan } ) = split '\.', $if{ dev };
	}

	return \%if;
}

=begin nd
Function: getInterfaceSystemStatus

	Get the status of an network interface in the system.

Parameters:
	if_ref - Reference to a network interface hash.

Returns:
	scalar - 'up' or 'down'.

See Also:
	<getActiveInterfaceList>, <getSystemInterfaceList>, <getInterfaceTypeList>, zapi/v?/interface.cgi,
=cut
sub getInterfaceSystemStatus     # ($if_ref)
{
	my $if_ref = shift;

	#~ &zenlog("getInterfaceSystemStatus $$if_ref{name}:$$if_ref{status}");

	my $parent_if_name = &getParentInterfaceName( $if_ref->{ name } );
	my $status_if_name = $if_ref->{ name };

	if ( $if_ref->{ vini } ne '' )    # vini
	{
		$status_if_name = $parent_if_name;
	}

	my $ip_bin = &getGlobalConfiguration('ip_bin');
	my $ip_output = `$ip_bin link show $status_if_name`;
	$ip_output =~ / state (\w+) /;
	my $if_status = lc $1;

	if ( $if_status !~ /^(?:up|down)$/ ) # if not up or down, ex: UNKNOWN
	{
		my ($flags) = $ip_output =~ /<(.+)>/;
		my @flags = split( ',', $flags );

		if ( grep( /^UP$/, @flags ) )
		{
			$if_status = 'up';
		}
		else
		{
			$if_status = 'down';
		}
	}

	# Set as down vinis not available
	$ip_output = `$ip_bin addr show $status_if_name`;

	if ( $ip_output !~ /$$if_ref{ addr }/ && $if_ref->{ vini } ne '' )
	{
		$$if_ref{ status } = 'down';
		return $$if_ref{ status };
	}

	unless ( $if_ref->{ vini } ne '' && $if_ref->{ status } eq 'down' )    # vini
	     #~ if ( not ( $if_ref->{vini} ne '' && $if_ref->{status} ne 'up' ) ) # vini
	     # if   ( $if_ref->{vini} eq '' || $if_ref->{status} eq 'up' ) ) # vini
	{
		$if_ref->{ status } = $if_status;
	}

	#~ &zenlog("getInterfaceSystemStatus $$if_ref{name}:$$if_ref{status}");

	return $if_ref->{ status } if $if_ref->{ status } eq 'down';

	#~ &zenlog("getInterfaceSystemStatus parent_if_name:$parent_if_name");

	my $parent_if_ref = &getInterfaceConfig( $parent_if_name, $if_ref->{ ip_v } );

	# 2) vlans do not require the parent interface to be configured
	if ( !$parent_if_name || !$parent_if_ref )
	{
		return $if_ref->{ status };
	}

#~ &zenlog("getInterfaceSystemStatus $$parent_if_ref{name}:$$parent_if_ref{status}");

	return &getInterfaceSystemStatus( $parent_if_ref );
}

=begin nd
Function: getParentInterfaceName

	Get the parent interface name.

Parameters:
	if_name - Interface name.

Returns:
	string - Parent interface name or undef if there is no parent interface (NIC and Bonding).

See Also:
	<getInterfaceConfig>, <getSystemInterface>, zenloadbalancer, zapi/v?/interface.cgi
=cut
sub getParentInterfaceName    # ($if_name)
{
	my $if_name = shift;

	my $if_ref = &getDevVlanVini( $if_name );
	my $parent_if_name;

	my $is_vlan = defined $if_ref->{ vlan } && length $if_ref->{ vlan };
	my $is_virtual = defined $if_ref->{ vini } && length $if_ref->{ vini };

	# child interface: eth0.100:virtual => eth0.100
	if ( $is_virtual && $is_vlan )
	{
		$parent_if_name = "$$if_ref{dev}.$$if_ref{vlan}";
	}

	# child interface: eth0:virtual => eth0
	elsif ( $is_virtual && !$is_vlan )
	{
		$parent_if_name = $if_ref->{ dev };
	}

	# child interface: eth0.100 => eth0
	elsif ( !$is_virtual && $is_vlan )
	{
		$parent_if_name = $if_ref->{ dev };
	}

	# child interface: eth0 => undef
	elsif ( !$is_virtual && !$is_vlan )
	{
		$parent_if_name = undef;
	}

	#~ &zenlog("if_name:$if_name parent_if_name:$parent_if_name");

	return $parent_if_name;
}

=begin nd
Function: getActiveInterfaceList

	Get a reference to a list of all running (up) and configured network interfaces.

Parameters:
	none - .

Returns:
	scalar - reference to an array of network interface hashrefs.

See Also:
	Zapi v3: post.cgi, put.cgi, system.cgi
=cut
sub getActiveInterfaceList
{
	my @configured_interfaces = @{ &getConfigInterfaceList() };

	# sort list
	@configured_interfaces =
	  sort { $a->{ name } cmp $b->{ name } } @configured_interfaces;

	# apply device status heritage
	$_->{ status } = &getInterfaceSystemStatus( $_ ) for @configured_interfaces;

	# discard interfaces down
	@configured_interfaces = grep { $_->{ status } eq 'up' } @configured_interfaces;

	# find maximun lengths for padding
	my $max_dev_length;
	my $max_ip_length;

	for my $iface ( @configured_interfaces )
	{
		if ( $iface->{ status } == 'up' )
		{
			my $dev_length = length $iface->{ name };
			$max_dev_length = $dev_length if $dev_length > $max_dev_length;

			my $ip_length = length $iface->{ addr };
			$max_ip_length = $ip_length if $ip_length > $max_ip_length;
		}
	}

	# make padding
	for my $iface ( @configured_interfaces )
	{
		my $dev_ip_padded = sprintf ( "%-${max_dev_length}s -> %-${max_ip_length}s",
									  $$iface{ name }, $$iface{ addr } );
		$dev_ip_padded =~ s/ +$//;
		$dev_ip_padded =~ s/ /&nbsp;/g;

		#~ &zenlog("padded interface:$dev_ip_padded");
		$iface->{ dev_ip_padded } = $dev_ip_padded;
	}

	return \@configured_interfaces;
}

=begin nd
Function: getSystemInterfaceList

	Get a reference to a list with all the interfaces, configured and not configured.

Parameters:
	none - .

Returns:
	scalar - reference to an array with configured and system network interfaces.

See Also:
	zapi/v?/interface.cgi, zapi/v3/cluster.cgi
=cut
sub getSystemInterfaceList
{
	my @interfaces;    # output
	my @configured_interfaces = @{ &getConfigInterfaceList() };

	use IO::Interface qw(:flags);
	my $socket = IO::Socket::INET->new( Proto => 'udp' );
	my @system_interfaces = &getInterfaceList();

	## Build system device "tree"
	for my $if_name ( @system_interfaces )    # list of interface names
	{
		# ignore loopback device, ipv6 tunnel, vlans and vinis
		next if $if_name =~ /^lo$|^sit\d+$/;
		next if $if_name =~ /\./;
		next if $if_name =~ /:/;

		my %if_parts = %{ &getDevVlanVini( $if_name ) };

		my $if_ref;
		my $if_flags = $socket->if_flags( $if_name );

		# run for IPv4 and IPv6
		for my $ip_stack ( 4, 6 )
		{
			$if_ref = &getInterfaceConfig( $if_name, $ip_stack );

			if ( !$$if_ref{ addr } )
			{
				# populate not configured interface
				$$if_ref{ status } = ( $if_flags & IFF_UP ) ? "up" : "down";
				$$if_ref{ mac }    = $socket->if_hwaddr( $if_name );
				$$if_ref{ name }   = $if_name;
				$$if_ref{ addr }   = '';
				$$if_ref{ mask }   = '';
				$$if_ref{ dev }    = $if_parts{ dev };
				$$if_ref{ vlan }   = $if_parts{ vlan };
				$$if_ref{ vini }   = $if_parts{ vini };
				$$if_ref{ ip_v }   = $ip_stack;
				$$if_ref{ type }   = &getInterfaceType( $if_name );
			}

			# setup for configured and unconfigured interfaces
			#~ $$if_ref{ gateway } = '-' if ! $$if_ref{ gateway };

			if ( !( $if_flags & IFF_RUNNING ) && ( $if_flags & IFF_UP ) )
			{
				$$if_ref{ link } = "off";
			}

			# add interface to the list
			push ( @interfaces, $if_ref );

			# add vlans
			for my $vlan_if_conf ( @configured_interfaces )
			{
				next if $$vlan_if_conf{ dev } ne $$if_ref{ dev };
				next if $$vlan_if_conf{ vlan } eq '';
				next if $$vlan_if_conf{ vini } ne '';

				if ( $$vlan_if_conf{ ip_v } == $ip_stack )
				{
					#~ $$vlan_if_conf{ gateway } = '-' if ! $$vlan_if_conf{ gateway };

					push ( @interfaces, $vlan_if_conf );

					# add vini of vlan
					for my $vini_if_conf ( @configured_interfaces )
					{
						next if $$vini_if_conf{ dev } ne $$if_ref{ dev };
						next if $$vini_if_conf{ vlan } ne $$vlan_if_conf{ vlan };
						next if $$vini_if_conf{ vini } eq '';

						if ( $$vini_if_conf{ ip_v } == $ip_stack )
						{
							#~ $$vini_if_conf{ gateway } = '-' if ! $$vini_if_conf{ gateway };
							push ( @interfaces, $vini_if_conf );
						}
					}
				}
			}

			# add vini of nic
			for my $vini_if_conf ( @configured_interfaces )
			{
				next if $$vini_if_conf{ dev } ne $$if_ref{ dev };
				next if $$vini_if_conf{ vlan } ne '';
				next if $$vini_if_conf{ vini } eq '';

				if ( $$vini_if_conf{ ip_v } == $ip_stack )
				{
					#~ $$vini_if_conf{ gateway } = '-' if ! $$vini_if_conf{ gateway };
					push ( @interfaces, $vini_if_conf );
				}
			}
		}
	}

	@interfaces = sort { $a->{ name } cmp $b->{ name } } @interfaces;
	$_->{ status } = &getInterfaceSystemStatus( $_ ) for @interfaces;

	return \@interfaces;
}

=begin nd
Function: getSystemInterface

	Get a reference to a network interface hash from the system configuration, not the stored configuration.

Parameters:
	if_name - Interface name.

Returns:
	scalar - reference to a network interface hash as is on the system or undef if not found.

See Also:
	<getInterfaceConfig>, <setInterfaceConfig>
=cut
sub getSystemInterface    # ($if_name)
{
	use IO::Interface qw(:flags);
	my $if_ref = {};
	$$if_ref{ name } = shift;

	#~ $$if_ref{ ip_v } = shift;

	my %if_parts = %{ &getDevVlanVini( $$if_ref{ name } ) };
	my $socket   = IO::Socket::INET->new( Proto => 'udp' );
	my $if_flags = $socket->if_flags( $$if_ref{ name } );

	$$if_ref{ mac } = $socket->if_hwaddr( $$if_ref{ name } );

	return undef if not $$if_ref{ mac };
	$$if_ref{ status } = ( $if_flags & IFF_UP ) ? "up" : "down";
	$$if_ref{ addr }   = '';
	$$if_ref{ mask }   = '';
	$$if_ref{ dev }    = $if_parts{ dev };
	$$if_ref{ vlan }   = $if_parts{ vlan };
	$$if_ref{ vini }   = $if_parts{ vini };
	$$if_ref{ type }   = &getInterfaceType( $$if_ref{ name } );
	$$if_ref{ parent } = &getParentInterfaceName( $$if_ref{ name } );

	if ( $$if_ref{ type } eq 'nic' )
	{
		$$if_ref{ is_slave } =
		  ( grep { $$if_ref{ name } eq $_ } &getAllBondsSlaves ) ? 'true' : 'false';
	}

	return $if_ref;
}

################################## Bonding ##################################

# global variable for bonding modes names
my @bond_modes = (
				'Round-robin policy',
				'Active-backup policy',
				'XOR policy',
				'Broadcast policy',
				'IEEE 802.3ad LACP',
				'Adaptive transmit load balancing',
				'Adaptive load balancing',
);

my @bond_modes_short = (
				'balance-rr',
				'active-backup',
				'balance-xor',
				'broadcast',
				'802.3ad',
				'balance-tlb',
				'balance-alb',
);

=begin nd
Function: getBondList

	Get a reference to a list of all bonding hashes.

	Bonding hash:
	name   - Interface name.
	mode   - Bonding mode
	slaves - NIC interfaces belonging to the bonding interface.

Parameters:
	none - .

Returns:
	scalar - reference to an array of bonding interfaces.

See Also:
	<applyBondChange>, <getAllBondsSlaves>
=cut
sub getBondList
{
	my $bonding_masters_filename = &getGlobalConfiguration('bonding_masters_filename');

	if ( !-f $bonding_masters_filename )
	{
		&zenlog( "Bonding module seems missing" );
		return undef;
	}

	open ( my $bond_file, '<', $bonding_masters_filename );

	if ( !$bond_file )
	{
		&zenlog( "Could not open file $bonding_masters_filename: $!" );
		return undef;
	}

	my @bond_names = split ( ' ', <$bond_file> );
	close $bond_file;
	chomp ( @bond_names );

	my @bonds = ();

	for my $bond_name ( @bond_names )
	{
		my $mode = &getBondMode( $bond_name );
		next if ( ref $mode ne 'ARRAY' );
		$mode = @{ $mode }[1];    # get mode code

		my $slaves = &getBondSlaves( $bond_name );
		next if ( ref $slaves ne 'ARRAY' );

		my %bond = (
					 name   => $bond_name,
					 mode   => $mode,
					 slaves => $slaves,
		);

		push ( @bonds, \%bond );
	}

	return \@bonds;
}

=begin nd
Function: getBondMode

	Get a reference to a list with two ways to express the bonding mode, name and number.

Parameters:
	bond_master - Bonding interface name.

Returns:
	scalar - list reference or undef if not found or an error happened.
	The list has two elements:
	- 0 - Bonding mode short name.
	- 1 - Bonding mode number.

Bugs:
	Returning a reference to a two elements array is making it too complicated.
	There is not need to return a reference. Returning a list is simpler.

See Also:
	
=cut
sub getBondMode
{
	my $bond_master = shift;

	my $sys_net_dir = &getGlobalConfiguration('sys_net_dir');
	my $bond_path = "$sys_net_dir/$bond_master";

	if ( !-d $bond_path )
	{
		&zenlog( "Could not find bonding $bond_path" );
		return undef;
	}

	my $bonding_mode_filename = &getGlobalConfiguration('bonding_mode_filename');

	open ( my $bond_mode_file, '<', "$bond_path/$bonding_mode_filename" );

	if ( !$bond_mode_file )
	{
		&zenlog( "Could not open file $bond_path/$bonding_mode_filename: $!" );
		return undef;
	}

	# input example: balance-rr 0
	# input example: balance-xor 2
	my @mode = split ( ' ', <$bond_mode_file> );
	close $bond_mode_file;
	chomp ( @mode );

# $mode[0] == balance-rr|active-backup|balance-xor|broadcast|802.3ad|balance-tlb|balance-alb
# $mode[1] == 0			| 1 			| 2 		| 3 	| 4 	| 5 		| 6
	return \@mode;
}

=begin nd
Function: getBondSlaves

	Get a reference to a list of NICs part of the bonding interface

Parameters:
	bond_master - Name of bonding interface.

Returns:
	scalar - reference to a list of slaves in bonding interface.

See Also:
	
=cut
sub getBondSlaves
{
	my $bond_master = shift;

	my $sys_net_dir = &getGlobalConfiguration('sys_net_dir');
	my $bond_path = "$sys_net_dir/$bond_master";

	if ( !-d $bond_path )
	{
		&zenlog( "Could not find bonding $bond_path" );
		return undef;
	}

	my $bonding_slaves_filename = &getGlobalConfiguration('bonding_slaves_filename');

	open ( my $bond_slaves_file, '<', "$bond_path/$bonding_slaves_filename" );

	if ( !$bond_slaves_file )
	{
		&zenlog( "Could not open file $bond_path/$bonding_slaves_filename: $!" );
		return undef;
	}

	# input example: eth1 eth2
	my @slaves = split ( ' ', <$bond_slaves_file> );
	close $bond_slaves_file;
	chomp ( @slaves );

	# $slaves[0] == eth1
	# $slaves[1] == eth2
	return \@slaves;
}

=begin nd
Function: applyBondChange

	Configure the bonding interface, and optionally store the configuration.

Parameters:
	bond - reference to bonding interface.
	writeconf - Boolean, true to store the configuration, or false to only apply it.

Returns:
	scalar - 0 on success, -1 on failure.

Bugs:
	Use better return values.

See Also:
	
=cut
sub applyBondChange
{
	my $bond      = shift;
	my $writeconf = shift;    # bool: write config to disk

	my $return_code = -1;

	# validate $bond->{name}
	return $return_code if ref $bond ne 'HASH';
	return $return_code if !$bond->{ name };

	# validate $bond->{mode}
	return $return_code if $bond->{ mode } < 0 || $bond->{ mode } > 6;

	# validate $bond->{slaves}
	return $return_code if ref $bond->{ slaves } ne 'ARRAY';
	return $return_code if scalar @{ $bond->{ slaves } } == 0;

	my $bond_list = &getBondList();
	my $sys_bond;

	# look for bonding master if already configured
	for my $bond_ref ( @{ $bond_list } )
	{
		$sys_bond = $bond_ref if ( $bond->{ name } eq $bond_ref->{ name } );
	}

	# verify every slave interface
	my @interface_list = &getInterfaceList();
	for my $slave ( @{ $bond->{ slaves } } )
	{
		if ( $slave =~ /(:|\.)/ )    # do not allow vlans or vinis
		{
			&zenlog( "$slave is not a NIC" );
			return $return_code;
		}
		elsif (
				grep ( /^$slave$/, @interface_list ) !=
				1 )                  # only allow interfaces in the system
		{
			&zenlog( "Could not find $slave" );
			return $return_code;
		}
	}

	# add bond master and set mode only if it is a new one
	if ( !$sys_bond )
	{
		&zenlog( "Bonding not found, adding new master" );
		&setBondMaster( $bond->{ name }, 'add' );
		&setBondMode( $bond );
	}

	# auxiliar hash to remove unwanted slaves
	my %sys_bond_slaves;
	%sys_bond_slaves = map { $_ => $_ } @{ $sys_bond->{ slaves } } if $sys_bond;

	for my $slave ( @{ $bond->{ slaves } } )
	{
		if ( !$sys_bond )
		{
			&zenlog( "adding $slave" );
			&setBondSlave( $bond->{ name }, $slave, 'add' );
		}
		else
		{
			# add slave if not already configured
			if ( grep ( /^$slave$/, @{ $sys_bond->{ slaves } } ) == 0 )
			{
				&zenlog( "adding $slave" );
				&setBondSlave( $bond->{ name }, $slave, 'add' );
			}

			# discard all checked slaves
			$sys_bond_slaves{ $slave } = undef;
		}
	}

	for my $slave ( keys %sys_bond_slaves )
	{
		if ( $sys_bond_slaves{ $slave } )
		{
			&zenlog( "removing $slave" );
			&setBondSlave( $bond->{ name }, $slave, 'del' );
		}
	}

	# write bonding configuration
	if ( $writeconf )
	{
		my $bond_conf = &getBondConfig();
		$bond_conf->{ $bond->{ name } } = $bond;
		&setBondConfig( $bond_conf );
	}

	$return_code = 0;

	return $return_code;
}

=begin nd
Function: setBondMaster

	Creates or removes master bonding interface.

Parameters:
	bond_name - Name of bonding interface.
	operation - 'add' to or 'del'.
	writeconf - Boolean, true to store configuration changes.

Returns:
	scalar - 0 on success, or 1 on failure.

See Also:
	
=cut
sub setBondMaster
{
	my $bond_name = shift;
	my $operation = shift;    # add || del
	my $writeconf = shift;    # bool: write config to disk

	my $operator;
	my $return_code = 1;

	if ( $operation eq 'add' )
	{
		$operator = '+';
	}
	elsif ( $operation eq 'del' )
	{
		$operator = '-';
	}
	else
	{
		&zenlog( "Wrong bonding master operation" );
		return $return_code;
	}

	my $bonding_masters_filename = &getGlobalConfiguration('bonding_masters_filename');

	if ( !-f $bonding_masters_filename )
	{
		&zenlog( "Bonding module seems missing" );
		return $return_code;
	}

	open ( my $bond_file, '>', $bonding_masters_filename );

	if ( !$bond_file )
	{
		&zenlog( "Could not open file $bonding_masters_filename: $!" );
		return $return_code;
	}

	print $bond_file "$operator$bond_name";
	close $bond_file;

	# miimon
	my $sys_net_dir = &getGlobalConfiguration('sys_net_dir');
	my $bonding_miimon_filename = &getGlobalConfiguration('bonding_miimon_filename');
	my $miimon_filepath = "$sys_net_dir/$bond_name/$bonding_miimon_filename";

	open ( my $miimon_file, '>', $miimon_filepath );

	if ( !$miimon_file )
	{
		&zenlog( "Could not open file $miimon_filepath: $!" );
	}
	else
	{
		print $miimon_file "100";
		close $miimon_file;
	}    # end miimon

	if ( $writeconf )
	{
		my $bond_conf = &getBondConfig();
		delete $bond_conf->{ $bond_name };
		&setBondConfig( $bond_conf );

		my $configdir = &getGlobalConfiguration('configdir');

		unlink "$configdir/if_${bond_name}_conf";
		&delGraph ( $bond_name, "iface" );
	}

	$return_code = 0;

	return $return_code;
}

=begin nd
Function: setBondMode

	Sets a bonding mode. Requires the bonding interface to have no slaves while changing the mode.

Parameters:
	bond - Reference to a bond interface.

Returns:
	scalar - 0 on success, or 1 on failure.

See Also:
	
=cut
sub setBondMode
{
	my $bond = shift;

	my $sys_net_dir = &getGlobalConfiguration('sys_net_dir');
	my $bond_path   = "$sys_net_dir/$bond->{name}";
	my $return_code = 1;

	if ( !-d $bond_path )
	{
		&zenlog( "Could not find bonding $bond_path" );
		return $return_code;
	}

	my $bonding_mode_filename = &getGlobalConfiguration('bonding_mode_filename');

	open ( my $bond_mode_file, '>', "$bond_path/$bonding_mode_filename" );

	if ( !$bond_mode_file )
	{
		&zenlog( "Could not open file $bond_path/$bonding_mode_filename: $!" );
		return $return_code;
	}

	print $bond_mode_file "$bond->{mode}";
	close $bond_mode_file;

	$return_code = 0;

	return $return_code;
}

=begin nd
Function: setBondSlave

	Adds or removes a slave interface to/from a bonding interface.

Parameters:
	bond_name - Name of bonding interface.
	bond_slave - Name of NIC interface.
	operation - 'add' or 'del'.

Returns:
	scalar - 0 on success, or 1 on failure.

See Also:
	
=cut
sub setBondSlave
{
	my $bond_name  = shift;
	my $bond_slave = shift;
	my $operation  = shift;    # add || del

	my $sys_net_dir = &getGlobalConfiguration('sys_net_dir');
	my $bond_path = "$sys_net_dir/$bond_name";
	my $operator;
	my $return_code = 1;

	if ( $operation eq 'add' )
	{
		$operator = '+';
	}
	elsif ( $operation eq 'del' )
	{
		$operator = '-';
	}
	else
	{
		&zenlog( "Wrong slave operation" );
		return $return_code;
	}

	if ( !-d $bond_path )
	{
		&zenlog( "Could not find bonding $bond_name in path $bond_path" );
	#	return $return_code;
	}

	my $bonding_slaves_filename = &getGlobalConfiguration('bonding_slaves_filename');

	#open ( my $bond_slaves_file, '>', "$bond_path/$bonding_slaves_filename" );
	my $bond_slaves_file = "${bond_path}\/${bonding_slaves_filename}";
	my $bondslave = "$bond_path/$bonding_slaves_filename";

	if ( ! -f $bond_slaves_file )
	{
		&zenlog( "Could not open file $bondslave: $!" );
		#return $return_code;
	}

	system("echo $operator$bond_slave > $bondslave");
	#close $bond_slaves_file;

	$return_code = 0;

	return $return_code;
}

=begin nd
Function: getBondConfig

	Get a hash reference with all the stored bonding interfaces configuration.

Parameters:
	none - .

Returns:
	scalar - Hash reference with pairs (bonding name => bonding hashref) of all bonding interfaces.

See Also:
	
=cut
sub getBondConfig
{
	# returns:	0 on failure
	#			Config_tiny object on success

	# requires:
	#~ use Config::Tiny;
	my $bond_config_file = &getGlobalConfiguration('bond_config_file');

	if ( !-f $bond_config_file )
	{
		&zenlog( "Creating bonding configuration file $bond_config_file" );
		open my $bond_file, '>', $bond_config_file;

		if ( !$bond_file )
		{
			&zenlog( "Could not create bonding configuration file $bond_config_file: $!" );
			return 0;
		}

		close $bond_file;
	}

	# Open the config
	my $bond_conf = Config::Tiny->read( $bond_config_file );

	# put slaves as array elements
	for my $bond ( keys %{ $bond_conf } )
	{
		next if $bond eq '_';

		$bond_conf->{ $bond }->{ slaves } =
		  [split ( ' ', $bond_conf->{ $bond }->{ slaves } )];
	}

	# FIXME: error handling?
	return $bond_conf;
}

=begin nd
Function: setBondConfig

	Save/Store the bonding configuration.

Parameters:
	bond_conf - Hashref with all bondings configuration.

Returns:
	none - .

See Also:
	
=cut
sub setBondConfig
{
	my $bond_conf = shift;

	# store slaves as a string
	for my $bond ( keys %{ $bond_conf } )
	{
		next if $bond eq '_';

		$bond_conf->{ $bond }->{ slaves } = "@{ $bond_conf->{ $bond }->{ slaves } }";
	}

	my $bond_config_file = &getGlobalConfiguration('bond_config_file');
	$bond_conf->write( $bond_config_file );

	# put slaves back as array elements
	for my $bond ( keys %{ $bond_conf } )
	{
		next if $bond eq '_';

		$bond_conf->{ $bond }->{ slaves } =
		  [split ( ' ', $bond_conf->{ $bond }->{ slaves } )];
	}

	return;
}

=begin nd
Function: getBondAvailableSlaves

	Get a list with all the nic interfaces with the conditions to be included in a bonding interface as a slave interface.

Parameters:
	none - .

Returns:
	list - list of nic interfaces available.

See Also:
	
=cut
sub getBondAvailableSlaves
{
	my @bond_list = ();
	my $bonding_masters_filename = &getGlobalConfiguration('bonding_masters_filename');

	# get bonding interfaces
	open my $bond_list_file, '<', $bonding_masters_filename;

	if ( $bond_list_file )
	{
		@bond_list = split ' ', <$bond_list_file>;
		close $bond_list_file;
	}

	# get list of all the interfaces
	my $sys_net_dir = &getGlobalConfiguration('sys_net_dir');
	opendir ( my $dir_h, $sys_net_dir );

	if ( !$dir_h )
	{
		&zenlog( "Could not open $sys_net_dir: $!" );
		return -1;
	}

	my @avail_ifaces;

	while ( my $dir_entry = readdir $dir_h )
	{
		next if $dir_entry eq '.';                      # not . dir
		next if $dir_entry eq '..';                     # not .. dir
		next if $dir_entry eq 'bonding_masters';        # not bonding_masters file
		next if $dir_entry =~ /(:|\.)/;                 # not vlan nor vini
		next if grep ( /^$dir_entry$/, @bond_list );    # not a bond
		my $iface = &getSystemInterface( $dir_entry );
		next if $iface->{ status } ne 'down';           # must be down
		#~ next if $iface->{ addr };                       # without address

		push ( @avail_ifaces, $dir_entry );
	}

	close $dir_h;
	return @avail_ifaces;
}

=begin nd
Function: getFloatInterfaceForAddress

	Get floating interface or output interface

Parameters:
	remote_ip_address - .

Returns:
	scalar - Name of output .

See Also:
	
=cut
# get floating interface or output interface
sub getFloatInterfaceForAddress
{
	my $remote_ip_address = shift;

	my $subnet_interface;
	my $gateway_interface;
	my @interface_list = @{ &getConfigInterfaceList() };

	use NetAddr::IP;
	my $remote_ip = NetAddr::IP->new( $remote_ip_address );

	# find interface in range
	for my $iface ( @interface_list )
	{
		next if $iface->{ vini } ne '';

		my $defaultgwif = &getGlobalConfiguration('defaultgwif');

		if ( $defaultgwif eq $iface->{ name } )
		{
			$gateway_interface = $iface;
		}

		my $network = NetAddr::IP->new( $iface->{ addr }, $iface->{ mask } );
		
		if ( $remote_ip->within( $network ) )
		{
			$subnet_interface = $iface;
		}
	}

	# if no interface found get the interface to the default gateway
	if ( ! $subnet_interface )
	{
		$subnet_interface = $gateway_interface;
	}

	my $output_interface;

	if ( $subnet_interface->{ float } )
	{
		# find floating interface
		for my $iface ( @interface_list )
		{
			next if $iface->{ vini } eq '';

			if ( $iface->{ name } eq $subnet_interface->{ float } )
			{
				$output_interface = $iface;
			}
		}
	}
	else
	{
		$output_interface = $subnet_interface;
	}

	return $output_interface;
}

=begin nd
Function: getConfigTiny

	Get a Config::Tiny object from a file name.

Parameters:
	file_path - Path to file.

Returns:
	scalar - reference to Config::Tiny object, or undef on failure.

See Also:
	
=cut
sub getConfigTiny
{
	my $file_path = shift;

	if ( ! -f $file_path )
	{
		open my $fi, '>', $file_path;
		&zenlog("Could not open file $file_path: $!") if ! $fi;
		close $fi;
	}
	
	use Config::Tiny;

	# returns object on success or undef on error.
	return Config::Tiny->read( $file_path );
}

=begin nd
Function: setConfigTiny

	Store a Config::Tiny object in a file.

Parameters:
	file_path - Path to file.
	config_ref - Config::Tiny object reference.

Returns:
	boolean - true on success, or undef on failure.

See Also:
	
=cut
sub setConfigTiny
{
	my $file_path = shift;
	my $config_ref = shift;

	#~ &zenlog("setConfigTiny: setConfigTiny=$file_path") if 1;
	#~ &zenlog("setConfigTiny: config_ref=". ref $config_ref) if 1;
	#~ &zenlog("setConfigTiny: config_ref=". Dumper $config_ref) if 1;

	if ( ! -f $file_path )
	{
		&zenlog("Could not find $file_path: $!");
		return undef;
	}

	if ( ref $config_ref ne 'Config::Tiny' )
	{
		&zenlog("Ilegal configuration argument.");
		return undef;
	}

	use Config::Tiny;

	# returns true on success or undef on error,
	return $config_ref->write( $file_path );
}

=begin nd
Function: setInterfaceUp

	[NOT USED] Configure interface reference in the system, and optionally store the configuration

Parameters:
	interface - interface reference.
	writeconf - true value to store the interface configuration.

Returns:
	scalar - 0 on success, or 1 on failure.

Bugs:
	NOT USED
=cut
# configure interface reference in the system, and optionally save the configuration
sub setInterfaceUp
{
	my $interface = shift;	# Interface reference
	my $writeconf = shift;	# TRUE value to write configuration, FALSE otherwise

	if ( ref $interface ne 'HASH' )
	{
		&zenlog("Argument must be a reference");
		return 1;
	}
	
	# vlans need to be created if they don't already exist
	my $exists = &ifexist( $interface->{ name } );

	if ( $exists eq "false" )
	{
		&createIf( $interface );    # create vlan if needed
	}

	if ( $writeconf )
	{
		my $old_iface_ref =
		&getInterfaceConfig( $interface->{ name }, $interface->{ ip_v } );

		if ( $old_iface_ref )
		{
			# Delete old IP and Netmask
			# delete interface from system to be able to repace it
			&delIp(
					$$old_iface_ref{ name },
					$$old_iface_ref{ addr },
					$$old_iface_ref{ mask }
			);

			# Remove routes if the interface has its own route table: nic and vlan
			if ( $interface->{ vini } eq '' )
			{
				&delRoutes( "local", $old_iface_ref );
			}
		}
	}

	&addIp( $interface );

	my $state = &upIf( $interface, $writeconf );

	if ( $state == 0 )
	{
		$interface->{ status } = "up";
		&zenlog( "Network interface $interface->{name} is now UP" );
	}

	# Writing new parameters in configuration file
	if ( $interface->{ name } !~ /:/ )
	{
		&writeRoutes( $interface->{ name } );
	}

	&setInterfaceConfig( $interface ) if $writeconf;
	&applyRoutes( "local", $interface );

	return 0; # FIXME
}

=begin nd
Function: configureDefaultGW

	Setup the configured default gateway (for IPv4 and IPv6).

Parameters:
	none - .

Returns:
	none - .

See Also:
	zenloadbalancer
=cut
# from zbin/zenloadbalancer, almost exactly
sub configureDefaultGW    #()
{
	my $defaultgw = &getGlobalConfiguration('defaultgw');
	my $defaultgwif = &getGlobalConfiguration('defaultgwif');
	my $defaultgw6 = &getGlobalConfiguration('defaultgw6');
	my $defaultgwif6 = &getGlobalConfiguration('defaultgwif6');

	# input: global variables $defaultgw and $defaultgwif
	if ( $defaultgw && $defaultgwif )
	{
		my $if_ref = &getInterfaceConfig( $defaultgwif, 4 );
		if ( $if_ref )
		{
			print "Default Gateway:$defaultgw Device:$defaultgwif\n";
			&applyRoutes( "global", $if_ref, $defaultgw );
		}
	}

	# input: global variables $$defaultgw6 and $defaultgwif6
	if ( $defaultgw6 && $defaultgwif6 )
	{
		my $if_ref = &getInterfaceConfig( $defaultgwif, 6 );
		if ( $if_ref )
		{
			print "Default Gateway:$defaultgw6 Device:$defaultgwif6\n";
			&applyRoutes( "global", $if_ref, $defaultgw6 );
		}
	}
}

=begin nd
Function: getInterfaceType

	Get the type of a network interface from its name using linux 'hints'.

	Original source code in bash:
	http://stackoverflow.com/questions/4475420/detect-network-connection-type-in-linux

	Translated to perl and adapted by Zevenet

	Interface types: nic, virtual, vlan, bond, dummy or lo.

Parameters:
	if_name - Interface name.

Returns:
	scalar - Interface type: nic, virtual, vlan, bond, dummy or lo.

See Also:
	
=cut
# Source in bash translated to perl:
# http://stackoverflow.com/questions/4475420/detect-network-connection-type-in-linux
#
# Interface types: nic, virtual, vlan, bond
sub getInterfaceType
{
	my $if_name = shift;

	my $type;

	return undef if $if_name eq '' || ! defined $if_name;
	
	# interfaz for cluster when is in maintenance mode
	return 'dummy' if $if_name eq 'cl_maintenance';
	
	if ( ! -d "/sys/class/net/$if_name" )
	{
		my ( $parent_if ) = split( ':', $if_name );
		my $quoted_if = quotemeta $if_name;
		my $ip_bin = &getGlobalConfiguration('ip_bin');
		my $found = grep( /inet .+ $quoted_if$/, `$ip_bin addr show $parent_if 2>/dev/null` );

		if ( ! $found )
		{
			my $configdir = &getGlobalConfiguration('configdir');
			$found = ( -f "$configdir/if_${if_name}_conf" && $if_name =~ /^.+\:.+$/ );
		}

		if ( $found )
		{
			return 'virtual';
		}
		else
		{
			return undef;
		}
	}

	my $code; # read type code
	{
		my $if_type_filename = "/sys/class/net/$if_name/type";

		open( my $type_file, '<', $if_type_filename )
			or die "Could not open file $if_type_filename: $!";
		chomp( $code = <$type_file> );
		close $type_file;
	}

	if ( $code == 1 )
	{
		$type='nic';

		# Ethernet, may also be wireless, ...
		if ( -f "/proc/net/vlan/$if_name" )
		{
			$type = 'vlan';
		}
		elsif ( -d "/sys/class/net/$if_name/bonding" )
		{
			$type = 'bond';
		}
		#elsif ( -d "/sys/class/net/$if_name/wireless" || -l "/sys/class/net/$if_name/phy80211" )
		#{
		#	$type = 'wlan';
		#}
		#elsif ( -d "/sys/class/net/$if_name/bridge" )
		#{
		#	$type = 'bridge';
		#}
		#elsif ( -f "/sys/class/net/$if_name/tun_flags" )
		#{
		#	$type = 'tap';
		#}
		#elsif ( -d "/sys/devices/virtual/net/$if_name" )
		#{
		#	$type = 'dummy' if $if_name =~ /^dummy/;
		#}
	}
	elsif ( $code == 24 )
	{
		$type = 'nic';    # firewire ;; # IEEE 1394 IPv4 - RFC 2734
	}
	elsif ( $code == 32 )
	{
		if ( -d "/sys/class/net/$if_name/bonding" )
		{
			$type = 'bond';
		}
		#elsif ( -d "/sys/class/net/$if_name/create_child" )
		#{
		#	$type = 'ib';
		#}
		#else
		#{
		#	$type = 'ibchild';
		#}
	}
	#elsif ( $code == 512 ) { $type = 'ppp'; }
	#elsif ( $code == 768 )
	#{
	#	$type = 'ipip';    # IPIP tunnel
	#}
	#elsif ( $code == 769 )
	#{
	#	$type = 'ip6tnl';    # IP6IP6 tunnel
	#}
	elsif ( $code == 772 ) { $type = 'lo'; }
	#elsif ( $code == 776 )
	#{
	#	$type = 'sit';       # sit0 device - IPv6-in-IPv4
	#}
	#elsif ( $code == 778 )
	#{
	#	$type = 'gre';       # GRE over IP
	#}
	#elsif ( $code == 783 )
	#{
	#	$type = 'irda';      # Linux-IrDA
	#}
	#elsif ( $code == 801 )   { $type = 'wlan_aux'; }
	#elsif ( $code == 65534 ) { $type = 'tun'; }

	# The following case statement still has to be replaced by something
	# which does not rely on the interface names.
	# case $if_name in
	# 	ippp*|isdn*) type=isdn;;
	# 	mip6mnha*)   type=mip6mnha;;
	# esac

	return $type if defined $type;

	my $msg = "Could not recognize the type of the interface $if_name.";

	&zenlog( $msg );
	die ( $msg ); # This should not happen
}

=begin nd
Function: getInterfaceTypeList

	Get a list of hashrefs with interfaces of a single type.

	Types supported are: nic, bond, vlan and virtual.

Parameters:
	list_type - Network interface type.

Returns:
	list - list of network interfaces hashrefs.

See Also:
	
=cut
sub getInterfaceTypeList
{
	my $list_type = shift;

	my @interfaces;

	if ( $list_type =~ /^(?:nic|bond|vlan)$/ )
	{
		my @system_interfaces = &getInterfaceList();

		for my $if_name ( @system_interfaces )
		{
			if ( $list_type eq &getInterfaceType( $if_name ) )
			{
				my $output_if = &getInterfaceConfig( $if_name );

				if ( ! $output_if || ! $output_if->{ mac } )
				{
					$output_if = &getSystemInterface( $if_name );
				}

				push ( @interfaces, $output_if );
			}
		}
	}
	elsif ( $list_type eq 'virtual' )
	{
		opendir my $conf_dir, &getGlobalConfiguration('configdir');
		my $virt_if_re = &getValidFormat('virt_interface');

		for my $file_name ( readdir $conf_dir )
		{
			if ( $file_name =~ /^if_($virt_if_re)_conf$/ )
			{
				my $iface = &getInterfaceConfig( $1 );
				$iface->{ status } = &getInterfaceSystemStatus( $iface );
				push ( @interfaces, $iface );
			}
		}
	}
	else
	{
		my $msg = "Interface type '$list_type' is not supported.";
		&zenlog( $msg );
		die( $msg );
	}

	return @interfaces;
}

=begin nd
Function: getVirtualInterfaceNameList

	Get a list of the virtual interfaces names.

Parameters:
	none - .

Returns:
	list - Every virtual interface name.
=cut
sub getVirtualInterfaceNameList
{
	opendir ( my $conf_dir, &getGlobalConfiguration( 'configdir' ) );
	my $virt_if_re = &getValidFormat('virt_interface');

	my @filenames = grep { s/^if_($virt_if_re)_conf$/$1/ } readdir ( $conf_dir );

	closedir ( $conf_dir );

	return @filenames;
}

=begin nd
Function: getLinkInterfaceNameList

	Get a list of the link interfaces names.

Parameters:
	none - .

Returns:
	list - Every link interface name.
=cut
sub getLinkNameList
{
	my $sys_net_dir = getGlobalConfiguration( 'sys_net_dir' );

	# Get link interfaces (nic, bond and vlan)
	opendir( my $if_dir, $sys_net_dir );
	my @if_list = grep { -l "$sys_net_dir/$_" } readdir $if_dir;
	closedir $if_dir;

	return @if_list;
}

=begin nd
Function: getAllBondsSlaves

	Get a list of all the nics belonging to a bonding interface.

Parameters:
	none - .

Returns:
	list - list of NIC names used by bonding interfaces.

See Also:
	
=cut
sub getAllBondsSlaves
{
	my @slaves; # output

	my $bond_list_ref = &getBondList();

	if ( $bond_list_ref )
	{
		for my $bond ( @{ $bond_list_ref } )
		{
			push @slaves, @{ &getBondSlaves( $bond->{ name } ) };
		}
	}

	return @slaves;
}

=begin nd
Function: getAppendInterfaces

	Get vlans or virtual interfaces running on a network interface.

Parameters:
	ifaceName - Interface name.
	type - Interface type: vlan or virtual.

Returns:
	scalar - reference to an array of interfaces hashrefs.

See Also:
	
=cut
# Get vlan or virtual interfaces appended from a interface
sub getAppendInterfaces # ( $iface_name, $type )
{
	my ( $ifaceName, $type )  = @_;
	my @output;
	
	my @typeList = &getInterfaceTypeList ( $type );

	foreach my $if ( @typeList )
	{
		my $iface = $if->{ name };
		my $parent = $if->{ parent }; 
		
		# if this interface append from a VLAN interface, will find absolut parent
		if ( &getInterfaceType ( $parent ) eq 'vlan' )
		{
			my $virtualInterface = &getInterfaceConfig ( $parent );
			$parent = $virtualInterface->{ parent }; 
		}
		
		push  @output, $iface if ( $parent eq $ifaceName );
	}
	
	return \@output;		
}
			
1;
