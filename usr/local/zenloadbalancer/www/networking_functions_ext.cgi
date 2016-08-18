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

use Config::Tiny;

use Data::Dumper;
$Data::Dumper::Sortkeys = 1;

# send gratuitous ICMP packets for L3 aware
sub sendGPing    # ($pif)
{
	my ( $pif ) = @_;

	my $gw = &gwofif( $pif );
	if ( $gw ne "" )
	{
		&zenlog( "sending '$ping_bin -c $pingc $gw' " );
		my @eject = `$ping_bin -c $pingc $gw > /dev/null &`;
	}
}

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

sub getInterfaceConfig    # \%iface ($if_name, $ip_version)
{
	my ( $if_name, $ip_version ) = @_;

	my $if_line;
	my $if_status;
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

	if ( !$if_line || !$if_status )
	{
		return undef;
	}

	chomp ( $if_line );
	my @if_params = split ( ';', $if_line );

	# Example: eth0;10.0.0.5;255.255.255.0;up;10.0.0.1;

	use IO::Socket;
	my $socket = IO::Socket::INET->new( Proto => 'udp' );

	my %iface;

	$iface{ name }    = shift @if_params;
	$iface{ addr }    = shift @if_params;
	$iface{ mask }    = shift @if_params;
	$iface{ gateway } = shift @if_params;                        # optional
	$iface{ status }  = $if_status;
	$iface{ ip_v }    = ( $iface{ addr } =~ /:/ ) ? '6' : '4';
	$iface{ dev }     = $iface{ name };
	$iface{ vini }    = undef;
	$iface{ vlan }    = undef;
	$iface{ mac }     = undef;

	if ( $iface{ dev } =~ /:/ )
	{
		( $iface{ dev }, $iface{ vini } ) = split ':', $iface{ dev };
	}

	if ( $iface{ dev } =~ /./ )
	{
		# dot must be escaped
		( $iface{ dev }, $iface{ vlan } ) = split '\.', $iface{ dev };
	}

	$iface{ mac } = $socket->if_hwaddr( $iface{ dev } );

	return \%iface;
}

# returns 1 if it was sucessfull
# returns 0 if it wasn't sucessfull
sub setInterfaceConfig    # $bool ($if_ref)
{
	my $if_ref = shift;

	if ( ref $if_ref ne 'HASH' )
	{
		&zenlog( "Input parameter is not a hash reference" );
		return undef;
	}

	&zenlog( "setInterfaceConfig: " . Dumper $if_ref);
	my @if_params = qw( name addr mask gateway );

	#~ my $if_line = join (';', @if_params);
	my $if_line =
	  join ( ';', @{ $if_ref }{ 'name', 'addr', 'mask', 'gateway' } ) . ';';
	my $config_filename = "$configdir/if_$$if_ref{ name }_conf";

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

		&zenlog( "setInterfaceConfig: if_line:$if_line status:$$if_ref{status}" );

		if ( !$ip_line_found )
		{
			&zenlog( "setInterfaceConfig: push  if_line:$if_line" );
			push ( @file_lines, $if_line );
		}

		untie @file_lines;
	}
	else
	{
		&zenlog( "$config_filename: $!" );

		return 0;
	}

	return 1;
}

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

	my $ip_output = `$ip_bin link show $status_if_name`;
	$ip_output =~ / state (\w+) /;
	my $if_status = lc $1;

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

sub getParentInterfaceName    # ($if_name)
{
	my $if_name = shift;

	my $if_ref = &getDevVlanVini( $if_name );
	my $parent_if_name;

	# child interface: eth0.100:virtual => eth0.100
	if ( $if_ref->{ vini } ne '' && $if_ref->{ vlan } ne '' )
	{
		$parent_if_name = "$$if_ref{dev}.$$if_ref{vlan}";
	}

	# child interface: eth0:virtual => eth0
	elsif ( $if_ref->{ vini } ne '' && $if_ref->{ vlan } eq '' )
	{
		$parent_if_name = $if_ref->{ dev };
	}

	# child interface: eth0.100 => eth0
	elsif ( $if_ref->{ vini } eq '' && $if_ref->{ vlan } ne '' )
	{
		$parent_if_name = $if_ref->{ dev };
	}

	# child interface: eth0 => undef
	elsif ( $if_ref->{ vini } eq '' && $if_ref->{ vlan } eq '' )
	{
		$parent_if_name = undef;
	}

	#~ &zenlog("if_name:$if_name parent_if_name:$parent_if_name");

	return $parent_if_name;
}

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

sub getSystemInterfaceList
{
	my @interfaces;    # output
	my @configured_interfaces = @{ &getConfigInterfaceList() };

	my $socket = IO::Socket::INET->new( Proto => 'udp' );
	my @system_interfaces = $socket->if_list;

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
			}

			# setup for configured and unconfigured interfaces
			#~ $$if_ref{ gateway } = '-' if ! $$if_ref{ gateway };

			if ( !( $if_flags & IFF_RUNNING ) && ( $if_flags & IFF_UP ) )
			{
				$if_ref{ link } = "off";
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

sub getSystemInterface    # ($if_name)
{
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

	return $if_ref;
}

################################## Bonding ##################################

# global variable for bonding modes names
@bond_modes = (
				'Round-robin policy',
				'Active-backup policy',
				'XOR policy',
				'Broadcast policy',
				'IEEE 802.3ad LACP',
				'Adaptive transmit load balancing',
				'Adaptive load balancing',
);

sub getBondList
{
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
	close $bondfile;
	chomp ( @bond_names );

	my @bonds;

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

sub getBondMode
{
	my $bond_master = shift;

	my $bond_path = "$sys_net_dir/$bond_master";

	if ( !-d $bond_path )
	{
		&zenlog( "Could not find bonding $bond_path" );
		return undef;
	}

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

sub getBondSlaves
{
	my $bond_master = shift;

	my $bond_path = "$sys_net_dir/$bond_master";

	if ( !-d $bond_path )
	{
		&zenlog( "Could not find bonding $bond_path" );
		return undef;
	}

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

		unlink "$configdir/if_${bond_name}_conf";
	}

	$return_code = 0;

	return $return_code;
}

sub setBondMode
{
	my $bond = shift;

	my $bond_path   = "$sys_net_dir/$bond->{name}";
	my $return_code = 1;

	if ( !-d $bond_path )
	{
		&zenlog( "Could not find bonding $bond_path" );
		return $return_code;
	}

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

sub setBondSlave
{
	my $bond_name  = shift;
	my $bond_slave = shift;
	my $operation  = shift;    # add || del

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

	#open ( my $bond_slaves_file, '>', "$bond_path/$bonding_slaves_filename" );
	my $bond_slave_file = "${bond_path}\/${bonding_slaves_filename}";
	my $bondslave = "$bond_path/$bonding_slaves_filename";

	if ( !$bond_slaves_file )
	{
		&zenlog( "Could not open file $bondslave: $!" );
		#return $return_code;
	}

	system("echo $operator$bond_slave > $bondslave");
	#close $bond_slaves_file;

	$return_code = 0;

	return $return_code;
}

sub getBondConfig
{
	# returns:	0 on failure
	#			Config_tiny object on success

	# requires:
	#~ use Config::Tiny;

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

	for my $bond ( keys %{ $bond_conf } )
	{
		next if $bond eq '_';

		$bond_conf->{ $bond }->{ slaves } =
		  [split ( ' ', $bond_conf->{ $bond }->{ slaves } )];
	}

	# FIXME: error handling?
	return $bond_conf;
}

sub setBondConfig
{
	my $bond_conf = shift;

	for my $bond ( keys %{ $bond_conf } )
	{
		next if $bond eq '_';

		$bond_conf->{ $bond }->{ slaves } = "@{ $bond_conf->{ $bond }->{ slaves } }";
	}

	$bond_conf->write( $bond_config_file );

	return;
}

sub getBondAvailableSlaves
{
	my @bond_list = ();

	# get bonding interfaces
	open my $bond_list_file, '<', $bonding_masters_filename;

	if ( $bond_list_file )
	{
		@bond_list = split ' ', <$bond_list_file>;
		close $bond_list_file;
	}

	# get list of all the interfaces
	opendir my $dir_h, $sys_net_dir;

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
		next if $iface->{ addr };                       # without address

		push ( @avail_ifaces, $dir_entry );
	}

	close $dir_h;
	return @avail_ifaces;
}

1;
