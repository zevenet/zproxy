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
						 'balance-rr',  'active-backup',
						 'balance-xor', 'broadcast',
						 '802.3ad',     'balance-tlb',
						 'balance-alb',
);

my $lock_file = undef;
my $lock_fh   = undef;

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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $bonding_masters_filename =
	  &getGlobalConfiguration( 'bonding_masters_filename' );

	if ( !-f $bonding_masters_filename )
	{
		# No bonding interface found
		return;
	}

	open ( my $bond_file, '<', $bonding_masters_filename );

	if ( !$bond_file )
	{
		&zenlog( "Could not open file $bonding_masters_filename: $!",
				 "error", "NETWORK" );
		return;
	}

	my @bond_names = split ( ' ', <$bond_file> // '' );
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

sub getBondMacInterface
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $slave_name = shift;

	my $sys_net_dir = &getGlobalConfiguration( 'sys_net_dir' );
	my $hwaddr_path = "$sys_net_dir/$slave_name/device/net/$slave_name/";

	if ( !-d $hwaddr_path )
	{
		&zenlog( "Could not find file $hwaddr_path", "error", "NETWORK" );
		return;
	}

	my $hwaddr_filename = &getGlobalConfiguration( 'bonding_hwaddr_filename' );

	open ( my $hwaddr_file, '<', "$hwaddr_path/$hwaddr_filename" );

	if ( !$hwaddr_file )
	{
		&zenlog( "Could not open file $hwaddr_path/$hwaddr_filename: $!",
				 "error", "NETWORK" );
		return;
	}

	# input example: 11:aa:22:bb:33:cc
	my $hwaddr = <$hwaddr_file>;
	close $hwaddr_file,;
	chomp ( $hwaddr );

	return $hwaddr;
}

sub getBondMode
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $bond_master = shift;

	my $sys_net_dir = &getGlobalConfiguration( 'sys_net_dir' );
	my $bond_path   = "$sys_net_dir/$bond_master";

	if ( !-d $bond_path )
	{
		&zenlog( "Could not find bonding $bond_path", "error", "NETWORK" );
		return;
	}

	my $bonding_mode_filename = &getGlobalConfiguration( 'bonding_mode_filename' );

	open ( my $bond_mode_file, '<', "$bond_path/$bonding_mode_filename" );

	if ( !$bond_mode_file )
	{
		&zenlog( "Could not open file $bond_path/$bonding_mode_filename: $!",
				 "error", "NETWORK" );
		return;
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $bond_master = shift;

	my $sys_net_dir = &getGlobalConfiguration( 'sys_net_dir' );
	my $bond_path   = "$sys_net_dir/$bond_master";

	if ( !-d $bond_path )
	{
		&zenlog( "Could not find bonding $bond_path", "error", "NETWORK" );
		return;
	}

	my $bonding_slaves_filename =
	  &getGlobalConfiguration( 'bonding_slaves_filename' );

	open ( my $bond_slaves_file, '<', "$bond_path/$bonding_slaves_filename" );

	if ( !$bond_slaves_file )
	{
		&zenlog( "Could not open file $bond_path/$bonding_slaves_filename: $!",
				 "error", "NETWORK" );
		return;
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
Function: getBondSlavesStatus

	Get a reference to a list of Slaves of the bonding interface with specific status

Parameters:
	bond_master - Name of bonding interface.
	status - Status to check

Returns:
	scalar - reference to a list of slaves matching the status.

See Also:

=cut

sub getBondSlavesStatus
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $bond_master = shift;
	my $status      = shift;
	my @slaves;
	require Zevenet::Net::Interface;
	foreach my $slave ( @{ &getBondSlaves( $bond_master ) } )
	{
		push @slaves, $slave if &getSystemInterface( $slave )->{ status } eq $status;
	}
	return \@slaves;
}

=begin nd
Function: applyBondChange

	Configure the bonding interface, and optionally store the configuration.

Parameters:
	bond - reference to bonding interface.
	writeconf - Boolean, true to store the configuration, or omit it for false.

Returns:
	scalar - 0 on success, -1 on failure.

Bugs:
	Use better return values.

See Also:

=cut

sub applyBondChange
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $bond      = shift;
	my $writeconf = shift;

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
	require Zevenet::Net::Interface;
	my @interface_list = &getInterfaceList();

	for my $slave ( @{ $bond->{ slaves } } )
	{
		if ( $slave =~ /(:|\.)/ )    # do not allow vlans or vinis
		{
			&zenlog( "$slave is not a NIC", "error", "NETWORK" );
			return $return_code;
		}
		elsif (
				grep ( /^$slave$/, @interface_list ) !=
				1 )                  # only allow interfaces in the system
		{
			&zenlog( "Could not find $slave", "error", "NETWORK" );
			return $return_code;
		}
	}

	# add bond master and set mode only if it is a new one
	if ( !$sys_bond )
	{
		&zenlog( "Bonding not found, adding new master", "info", "NETWORK" );
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
			&zenlog( "adding $slave", "info", "NETWORK" );
			&setBondSlave( $bond->{ name }, $slave, 'add' );
		}
		else
		{
			# add slave if not already configured
			if ( grep ( /^$slave$/, @{ $sys_bond->{ slaves } } ) == 0 )
			{
				&zenlog( "adding $slave", "info", "NETWORK" );
				&setBondSlave( $bond->{ name }, $slave, 'add' );
			}

			# discard all checked slaves
			$sys_bond_slaves{ $slave } = undef;
		}
	}

	my $mac_updated = 0;
	for my $slave ( keys %sys_bond_slaves )
	{
		if ( $sys_bond_slaves{ $slave } )
		{
			&zenlog( "removing $slave", "info", "NETWORK" );
			&setBondSlave( $bond->{ name }, $slave, 'del' );
			if ( $slave eq @{ $sys_bond->{ slaves } }[0] )
			{
				my $bond_local = &getBondLocalConfig( $bond->{ name } );
				$mac_updated = 1 if ( $bond_local->{ mac } eq "" );
			}
		}
	}

	# write bonding configuration
	if ( $writeconf )
	{
		my $bond_conf = &getBondConfig();
		$bond_conf->{ $bond->{ name } } = $bond;
		&setBondConfig( $bond_conf );

		# creating configuration file
		if ( !$sys_bond or $mac_updated )
		{
			my $if_ref = {
						   name => $bond->{ name },
						   mac  => "",
			};
			&setBondMac( $if_ref );
		}
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $bond_name = shift;
	my $operation = shift;    # add || del
	my $writeconf = shift;

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
		&zenlog( "Wrong bonding master operation", "error", "NETWORK" );
		return $return_code;
	}

	my $bonding_masters_filename =
	  &getGlobalConfiguration( 'bonding_masters_filename' );

	if ( !-f $bonding_masters_filename )
	{
		&zenlog( "Bonding module seems missing", "error", "NETWORK" );
		return $return_code;
	}

	open ( my $bond_file, '>', $bonding_masters_filename );

	if ( !$bond_file )
	{
		&zenlog( "Could not open file $bonding_masters_filename: $!",
				 "error", "NETWORK" );
		return $return_code;
	}

	print $bond_file "$operator$bond_name";
	close $bond_file;

	# miimon
	my $sys_net_dir = &getGlobalConfiguration( 'sys_net_dir' );
	my $bonding_miimon_filename =
	  &getGlobalConfiguration( 'bonding_miimon_filename' );
	my $miimon_filepath = "$sys_net_dir/$bond_name/$bonding_miimon_filename";

	open ( my $miimon_file, '>', $miimon_filepath );

	if ( !$miimon_file )
	{
		&zenlog( "Could not open file $miimon_filepath: $!", "error", "NETWORK" );
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

		my $configdir = &getGlobalConfiguration( 'configdir' );

		unlink "$configdir/if_${bond_name}_conf";
		require Zevenet::RRD;
		&delGraph( $bond_name, "iface" );
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $bond = shift;

	my $sys_net_dir = &getGlobalConfiguration( 'sys_net_dir' );
	my $bond_path   = "$sys_net_dir/$bond->{name}";
	my $return_code = 1;

	if ( !-d $bond_path )
	{
		&zenlog( "Could not find bonding $bond_path", "error", "NETWORK" );
		return $return_code;
	}

	my $bonding_mode_filename = &getGlobalConfiguration( 'bonding_mode_filename' );

	open ( my $bond_mode_file, '>', "$bond_path/$bonding_mode_filename" );

	if ( !$bond_mode_file )
	{
		&zenlog( "Could not open file $bond_path/$bonding_mode_filename: $!",
				 "error", "NETWORK" );
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $bond_name  = shift;
	my $bond_slave = shift;
	my $operation  = shift;    # add || del

	my $sys_net_dir = &getGlobalConfiguration( 'sys_net_dir' );
	my $bond_path   = "$sys_net_dir/$bond_name";
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
		&zenlog( "Wrong slave operation", "error", "NETWORK" );
		return $return_code;
	}

	if ( !-d $bond_path )
	{
		&zenlog( "Could not find bonding $bond_name in path $bond_path",
				 "error", "NETWORK" );

		#	return $return_code;
	}

	my $bonding_slaves_filename =
	  &getGlobalConfiguration( 'bonding_slaves_filename' );

	#open ( my $bond_slaves_file, '>', "$bond_path/$bonding_slaves_filename" );
	my $bond_slaves_file = "${bond_path}\/${bonding_slaves_filename}";
	my $bondslave        = "$bond_path/$bonding_slaves_filename";

	if ( !-f $bond_slaves_file )
	{
		&zenlog( "Could not open file $bondslave: $!", "error", "NETWORK" );

		#return $return_code;
	}

	&logAndRun( "echo $operator$bond_slave > $bondslave" );

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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	# returns:	0 on failure
	#			Config_tiny object on success

	# requires:
	#~ use Config::Tiny;
	my $bond_config_file = &getGlobalConfiguration( 'bond_config_file' );

	if ( !-f $bond_config_file )
	{
		&zenlog( "Creating bonding configuration file $bond_config_file",
				 "info", "NETWORK" );
		open my $bond_file, '>', $bond_config_file;

		if ( !$bond_file )
		{
			&zenlog( "Could not create bonding configuration file $bond_config_file: $!",
					 "error", "NETWORK" );
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $bond_conf = shift;

	# store slaves as a string
	for my $bond ( keys %{ $bond_conf } )
	{
		next if $bond eq '_';

		$bond_conf->{ $bond }->{ slaves } = "@{ $bond_conf->{ $bond }->{ slaves } }";
	}

	my $bond_config_file = &getGlobalConfiguration( 'bond_config_file' );
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my @bond_list = ();
	my $bonding_masters_filename =
	  &getGlobalConfiguration( 'bonding_masters_filename' );

	# get bonding interfaces
	open my $bond_list_file, '<', $bonding_masters_filename;

	if ( $bond_list_file )
	{
		@bond_list = split ' ', <$bond_list_file>;
		close $bond_list_file;
	}

	# get list of all the interfaces
	my $sys_net_dir = &getGlobalConfiguration( 'sys_net_dir' );
	opendir ( my $dir_h, $sys_net_dir );

	if ( !$dir_h )
	{
		&zenlog( "Could not open $sys_net_dir: $!", "error", "NETWORK" );
		return -1;
	}

	require Zevenet::Net::Interface;
	my @avail_ifaces;

	while ( my $dir_entry = readdir $dir_h )
	{
		next if $dir_entry eq '.';                      # not . dir
		next if $dir_entry eq '..';                     # not .. dir
		next if $dir_entry eq 'bonding_masters';        # not bonding_masters file
		next if $dir_entry =~ /(:|\.)/;                 # not vlan nor vini
		next if grep ( /^$dir_entry$/, @bond_list );    # not a bond
		my $iface = &getSystemInterface( $dir_entry );
		next
		  if $iface->{ status } ne 'down'
		  ; # must be down		next if $iface->{ addr };                       # without address
		$iface = &getInterfaceConfig( $iface->{ name } );
		next if $iface->{ addr };

		push ( @avail_ifaces, $dir_entry );
	}

	close $dir_h;
	return @avail_ifaces;
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my @slaves;    # output

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

sub get_bond_struct
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $bond ) = @_;

	require Zevenet::Net::Interface;

	my $bond_ref;

	for my $if_ref ( &getInterfaceTypeList( 'bond' ) )
	{
		next unless $if_ref->{ name } eq $bond;

		$bond_ref = $if_ref;
	}

	# End here if the bonding interface was not found
	return unless $bond_ref;

	include 'Zevenet::Alias';
	my $alias = &getAlias( 'interface' );

	my $bond_conf = &getBondConfig();

	$bond_ref->{ status } = &getInterfaceSystemStatus( $bond_ref );

	# Any key must contain a value or "" but can't be null
	if ( !defined $bond_ref->{ name } )    { $bond_ref->{ name }    = ""; }
	if ( !defined $bond_ref->{ addr } )    { $bond_ref->{ addr }    = ""; }
	if ( !defined $bond_ref->{ mask } )    { $bond_ref->{ mask }    = ""; }
	if ( !defined $bond_ref->{ gateway } ) { $bond_ref->{ gateway } = ""; }
	if ( !defined $bond_ref->{ status } )  { $bond_ref->{ status }  = ""; }
	if ( !defined $bond_ref->{ mac } )     { $bond_ref->{ mac }     = ""; }

	my @bond_slaves = @{ $bond_conf->{ $bond_ref->{ name } }->{ slaves } };
	my @output_slaves;
	push ( @output_slaves, { name => $_ } ) for @bond_slaves;

	# Output bonding interface hash reference
	my $interface = {
			   alias   => $alias->{ $bond_ref->{ name } },
			   name    => $bond_ref->{ name },
			   ip      => $bond_ref->{ addr },
			   netmask => $bond_ref->{ mask },
			   gateway => $bond_ref->{ gateway },
			   status  => $bond_ref->{ status },
			   mac     => $bond_ref->{ mac },
			   slaves  => \@output_slaves,
			   dhcp    => $bond_ref->{ dhcp } // 'false',
			   mode => $bond_modes_short[$bond_conf->{ $bond_ref->{ name } }->{ mode }],
	};

	return $interface;
}

sub get_bond_list_struct
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $output_list = ();

	require Zevenet::Net::Interface;
	include 'Zevenet::Cluster';

	my $desc      = "List bonding interfaces";
	my $bond_conf = &getBondConfig();

	# get cluster interface
	my $cluster_if;

	my $zcl_conf = &getZClusterConfig();
	$cluster_if = $zcl_conf->{ _ }->{ interface } if $zcl_conf;

	include 'Zevenet::Alias';
	my $alias = &getAlias( 'interface' );

	for my $if_ref ( &getInterfaceTypeList( 'bond' ) )
	{
		next unless $bond_conf->{ $if_ref->{ name } };

		$if_ref->{ status } = &getInterfaceSystemStatus( $if_ref );

		# Any key must cotain a value or "" but can't be null
		if ( !defined $if_ref->{ name } )    { $if_ref->{ name }    = ""; }
		if ( !defined $if_ref->{ addr } )    { $if_ref->{ addr }    = ""; }
		if ( !defined $if_ref->{ mask } )    { $if_ref->{ mask }    = ""; }
		if ( !defined $if_ref->{ gateway } ) { $if_ref->{ gateway } = ""; }
		if ( !defined $if_ref->{ status } )  { $if_ref->{ status }  = ""; }
		if ( !defined $if_ref->{ mac } )     { $if_ref->{ mac }     = ""; }

		my @bond_slaves = @{ $bond_conf->{ $if_ref->{ name } }->{ slaves } };
		my @output_slaves;
		push ( @output_slaves, { name => $_ } ) for @bond_slaves;

		my $if_conf = {
			alias   => $alias->{ $if_ref->{ name } },
			name    => $if_ref->{ name },
			ip      => $if_ref->{ addr },
			netmask => $if_ref->{ mask },
			gateway => $if_ref->{ gateway },
			status  => $if_ref->{ status },
			mac     => $if_ref->{ mac },
			dhcp    => $if_ref->{ dhcp } // 'false',
			slaves  => \@output_slaves,
			mode    => $bond_modes_short[$bond_conf->{ $if_ref->{ name } }->{ mode }],

			#~ ipv     => $if_ref->{ ip_v },
		};

		$if_conf->{ is_cluster } = 'true'
		  if $cluster_if && $cluster_if eq $if_ref->{ name };

		push @{ $output_list }, $if_conf;
	}

	return $output_list;
}

=begin nd
Function: setBondIP

	Handle all the operations to modify the bonding IP,

Parameters:
	if_ref - Hash reference with the new configuration.

Returns:
	Integer - 0 on success other value on error.

See Also:

=cut

sub setBondIP
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $if_ref = shift;

	# Retrieve old configuration
	my $old_ref = &getInterfaceConfig( $if_ref->{ name } );

	#Retrieve list of farm using this interface
	require Zevenet::Farm::Base;
	my $farms_ref = &getFarmListByVip( $if_ref->{ addr } );

	# Delete old IP and Netmask from system to replace it
	if ( defined $old_ref->{ addr } && $old_ref->{ addr } ne "" )
	{
		return 1
		  if &delIp( $old_ref->{ name }, $old_ref->{ addr }, $old_ref->{ mask } );

		# Remove routes if the interface has its own route table: nic and vlan
		return 1 if &delRoutes( "local", $old_ref );
	}

	# Add new IP, netmask and gateway
	return 1 if ( &addIp( $if_ref ) );

	# Writing new parameters in configuration file
	return 1 if ( &writeRoutes( $if_ref->{ name } ) );
	return 1 if ( !&setInterfaceConfig( $if_ref ) );

	# Put the interface up
	my $previous_status = $old_ref->{ status };

	if ( $previous_status eq "up" )
	{
		my $state = &upIf( $if_ref, 'writeconf' );

		if ( $state == 0 )
		{
			$if_ref->{ status } = "up";
			&applyRoutes( "local", $if_ref );
		}
		else
		{
			$if_ref->{ status } = $previous_status;
		}
	}

	# if the GW is changed, change it in all appending virtual interfaces
	if ( exists $if_ref->{ gateway } )
	{
		foreach my $appending ( &getInterfaceChild( $if_ref->{ name } ) )
		{
			my $app_config = &getInterfaceConfig( $appending );
			$app_config->{ gateway } = $if_ref->{ gateway };
			&setInterfaceConfig( $app_config );
		}
	}

	# if the netmask is changed, change it in all appending virtual interfaces
	if ( $if_ref->{ mask } ne $old_ref->{ mask } )
	{
		foreach my $appending ( &getInterfaceChild( $if_ref->{ name } ) )
		{
			my $app_config = &getInterfaceConfig( $appending );
			&delRoutes( "local", $app_config );
			&downIf( $app_config );
			$app_config->{ mask } = $if_ref->{ mask };
			&setInterfaceConfig( $app_config );
		}
	}

	# put all dependant interfaces up
	require Zevenet::Net::Util;
	&setIfacesUp( $if_ref->{ name }, "vini" );

	# change farm vip,
	if ( $farms_ref )
	{
		require Zevenet::Farm::Config;
		&setAllFarmByVip( $if_ref->{ ip }, $farms_ref );
	}
	return 0;
}

=begin nd
Function: setBondMac

	Set slaves down to allow the mac change, then set the new mac and finally
	put slaves up again.

Parameters:
	if_ref - Hash reference with the bonding interface configuration to be used.

Returns:
	status - 0 on success, other than 0 in other case.

See Also:

=cut

sub setBondMac
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $if_ref     = shift;
	my $status     = 0;
	my $bondSlaves = getBondSlaves( $if_ref->{ name } );

	#Error if not mac in the hash reference
	return 1 unless ( exists $if_ref->{ mac } );

	# If the mac is clear, let's restore the mac address
	my $mac = $if_ref->{ mac };
	if ( length $if_ref->{ mac } == 0 )
	{
		$mac = &getBondDefaultMac( $if_ref->{ name } );
	}

	my $if_system = &getSystemInterface( $if_ref->{ name } );

	# change mac if mac on system is not equal
	if ( $if_system->{ mac } ne $if_ref->{ mac } )
	{
		&zenlog( "Turning slaves of $if_ref->{ name } down", "info", "NETWORK" );
		foreach my $slave ( @{ $bondSlaves } )
		{
			my $slaveConf = &getSystemInterface( $slave );
			require Zevenet::Net::Core;
			$status += &downIf( $slaveConf ) if ( $slaveConf->{ status } ne "down" );
		}
		include 'Zevenet::Net::Mac';
		$status += &addMAC( $if_ref->{ name }, $mac );

		&zenlog( "Turning slaves of $if_ref->{ name } up", "info", "NETWORK" );
		foreach my $slave ( @{ $bondSlaves } )
		{
			my $slaveConf = &getSystemInterface( $slave );
			$status += &upIf( $slaveConf );
		}
	}

	my $config_ref = &getInterfaceConfig( $if_ref->{ name } )
	  // &getSystemInterface( $if_ref->{ name } );
	$config_ref->{ mac } = $mac;
	&setInterfaceConfig( $config_ref );
	&saveBondMacConfig( $if_ref->{ name }, $if_ref->{ mac } );

	return $status;
}

=begin nd
Function: saveBondDefaultConfig

	Store the current configuration in the non replicable directory
	/usr/local/zevenet/local to restore the mac address.

	Parameters:
		bondName - The bond name which will be retrieved and stored as the default config

	Returns:
		status - 0 on success, other than 0 in other case.

See Also:

=cut

sub saveBondDefaultConfig
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $bond_name = shift;

	my $bond_conf = &getBondConfig( $bond_name );

	return 1 unless $bond_conf;

	#Get the slave conf to store the mac
	my $slave_conf =
	  &getInterfaceConfig( @{ $bond_conf->{ $bond_name }->{ slaves } }[0] );

	require Zevenet::Config;
	my $local_dir       = &getGlobalConfiguration( "localconfig" );
	my $local_bond_file = $local_dir . "/bonding.conf";

	use Config::Tiny;
	my $file_h = Config::Tiny->read( $local_bond_file )
	  // Config::Tiny->new( $local_bond_file );
	$file_h->{ $bond_name }->{ mac } = $slave_conf->{ mac };

	$file_h->write( $local_bond_file );

	return 0;
}

=begin nd
Function: saveBondMacConfig

	Store the current mac configuration in the non replicable directory
	/usr/local/zevenet/local

	Parameters:
		bond_name - The bond name which will be stored,
		macaddress - The macaddress to be stored. Empty means default ( first slave )

	Returns:
		status - 0 on success, other than 0 in other case.

See Also:

=cut

sub saveBondMacConfig
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $bond_name  = shift;
	my $macaddress = shift;

	my $bond_conf = &getBondConfig( $bond_name );

	require Zevenet::Config;
	my $local_dir       = &getGlobalConfiguration( "localconfig" );
	my $local_bond_file = $local_dir . "/bonding.conf";

	use Config::Tiny;
	my $file_h = Config::Tiny->read( $local_bond_file )
	  // Config::Tiny->new( $local_bond_file );
	$file_h->{ $bond_name }->{ mac } = $macaddress;

	$file_h->write( $local_bond_file );

	return 0;
}

=begin nd
Function: getBondDefaultConfig

	Get the mac configuration from the non replicable directory
	/usr/local/zevenet/local

	Parameters:
		bond_name - The bond name

	Returns:
		Hash - hash reference on success, 1 in other case.

See Also:

=cut

sub getBondDefaultConfig
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $bond_name = shift;

	require Zevenet::Config;
	my $local_dir       = &getGlobalConfiguration( "localconfig" );
	my $local_bond_file = $local_dir . "/bonding.conf";

	return 1 if ( !-f $local_bond_file );

	use Config::Tiny;
	my $file_h = Config::Tiny->read( $local_bond_file );

	return 1 if ( !exists $file_h->{ $bond_name } );

	return $file_h->{ $bond_name };
}

=begin nd
Function: getBondLocalConfig

	Get the mac configuration from the non replicable directory
	/usr/local/zevenet/local

	Parameters:
		bond_name - The bond name

	Returns:
		Hash - hash reference on success, 1 in other case.
=cut

sub getBondLocalConfig
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $bond_name = shift;

	require Zevenet::Config;
	my $local_dir       = &getGlobalConfiguration( "localconfig" );
	my $local_bond_file = $local_dir . "/bonding.conf";

	return 1 if ( !-f $local_bond_file );

	use Config::Tiny;
	my $file_h = Config::Tiny->read( $local_bond_file );

	return 1 if ( !exists $file_h->{ $bond_name } );

	return $file_h->{ $bond_name };
}

=begin nd
Function: getBondDefaultMac

	Get the default Mac definition: the first slave mac.
	Parameters:
		bond_name - The bond name which will be stored,

	Returns:
		string - mac on success, 1 in other case.
=cut

sub getBondDefaultMac
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $bond_name = shift;

	my $bond_conf = &getBondConfig( $bond_name );

	return 1 unless $bond_conf;

	include 'Zevenet::Net::Mac';
	return &genMACRandom();
}

=begin nd
Function: delBondDefaultConfig

	Deletes the stored default configuration for a bonding interface

	Parameters:
		bondName - The bond name of the bonding

	Returns:
		status - 0 on success, other than 0 in other case.

See Also:

=cut

sub delBondDefaultConfig
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $bond_name = shift;

	require Zevenet::Config;
	my $local_dir       = &getGlobalConfiguration( "localconfig" );
	my $local_bond_file = $local_dir . "/bonding.conf";

	#return 1 if the config file doesn't exists
	return 1 if ( !-f $local_bond_file );

	use Config::Tiny;
	my $file_h = Config::Tiny->read( $local_bond_file );
	delete $file_h->{ $bond_name };
	$file_h->write( $local_bond_file );

	return 0;

}

=begin nd
Function: lockBondResource

	Lock the bonding resource to avoid overlaping problems.

See Also:

=cut

sub lockBondResource
{
	my $bond_config_file = &getGlobalConfiguration( 'bond_config_file' );
	&lockResource( $bond_config_file, "l" );
	return;
}

=begin nd
Function: unlockBondResource

	unlock the bonding resource to allow other process to use the resource.

See Also:

=cut

sub unlockBondResource
{
	my $bond_config_file = &getGlobalConfiguration( 'bond_config_file' );
	&lockResource( $bond_config_file, "ud" );
	return;
}

1;
