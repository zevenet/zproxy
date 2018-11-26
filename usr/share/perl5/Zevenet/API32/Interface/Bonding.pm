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

use Zevenet::API32::HTTP;

my @bond_modes_short = (
						 'balance-rr',  'active-backup',
						 'balance-xor', 'broadcast',
						 '802.3ad',     'balance-tlb',
						 'balance-alb',
);

sub new_bond    # ( $json_obj )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;

	include 'Zevenet::Net::Bonding';
	require Zevenet::Net::Validate;
	require Zevenet::Net::Interface;
	require Zevenet::System;

	my $desc = "Add a bond interface";

	# validate BOND NAME
	my $bond_re = &getValidFormat( 'bond_interface' );

	# size < 16: size = bonding_name.vlan_name:virtual_name
	if ( length $json_obj->{ name } > 11 )
	{
		my $msg = "Bonding interface name has a maximum length of 11 characters";
		&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	unless (    $json_obj->{ name } =~ /^$bond_re$/
			 && &ifexist( $json_obj->{ name } ) eq 'false' )
	{
		my $msg = "Interface name is not valid";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# validate BOND MODE
	unless (    $json_obj->{ mode }
			 && &getValidFormat( 'bond_mode_short', $json_obj->{ mode } ) )
	{
		my $msg = "Bond mode is not valid";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	$json_obj->{ mode } =
	  &indexOfElementInArray( $json_obj->{ mode }, \@bond_modes_short );

	# validate SLAVES
	my $missing_slave;

	for my $slave ( @{ $json_obj->{ slaves } } )
	{
		if ( &getInterfaceConfig( $slave )
			 && ( &getInterfaceConfig( $slave )->{ status } eq 'up' ) )
		{
			my $msg =
			  "The $slave interface has to be in DOWN status to add it to a bonding.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}

		unless ( grep { $slave eq $_ } &getBondAvailableSlaves() )
		{
			$missing_slave = $slave;
			last;
		}
	}

	if ( $missing_slave )
	{
		my $msg = "The interface $missing_slave is not a valid bond slave.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	if ( !@{ $json_obj->{ slaves } } )
	{
		my $msg = "The slave interfaces list cannot be empty.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	eval { die if &applyBondChange( $json_obj, 'writeconf' ); };

	if ( $@ )
	{
		my $msg = "The $json_obj->{ name } bonding network interface can't be created";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $if_ref      = getSystemInterface( $json_obj->{ name } );
	my @bond_slaves = @{ $json_obj->{ slaves } };
	my @output_slaves;

	push ( @output_slaves, { name => $_ } ) for @bond_slaves;

	my $body = {
				 description => $desc,
				 params      => {
							 name   => $json_obj->{ name },
							 mode   => $bond_modes_short[$json_obj->{ mode }],
							 slaves => \@output_slaves,
							 status => $if_ref->{ status },
							 mac    => $if_ref->{ mac },
				 },
	};

	return &httpResponse( { code => 201, body => $body } );
}

# POST bond slave
# slave: nic
sub new_bond_slave    # ( $json_obj, $bond )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $bond     = shift;

	include 'Zevenet::Net::Bonding';
	require Zevenet::Net::Interface;

	my $desc = "Add a slave to a bond interface";

	# validate BOND NAME
	my $bonds = &getBondConfig();

	unless ( $bonds->{ $bond } )
	{
		my $msg = "Bond interface name not found";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	if ( &getInterfaceConfig( $json_obj->{ name } )
		 && ( &getInterfaceConfig( $json_obj->{ name } )->{ status } eq 'up' ) )
	{
		my $msg = "The NIC interface has to be in DOWN status to add it as slave.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# validate SLAVE
	eval {
		$json_obj->{ name } or die;
		&getValidFormat( 'nic_interface', $json_obj->{ name } ) or die;
		grep ( { $json_obj->{ name } eq $_ } &getBondAvailableSlaves() ) or die;
		die
		  if grep ( { $json_obj->{ name } eq $_ } @{ $bonds->{ $bond }->{ slaves } } );
	};
	if ( $@ )
	{
		my $msg = "Could not add the slave interface to this bonding";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	push @{ $bonds->{ $bond }->{ slaves } }, $json_obj->{ name };

	eval { die if &applyBondChange( $bonds->{ $bond }, 'writeconf' ); };
	if ( $@ )
	{
		my $msg = "The $json_obj->{ name } bonding network interface can't be created";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $if_ref      = getSystemInterface( $bond );
	my @bond_slaves = @{ $bonds->{ $bond }->{ slaves } };
	my @output_slaves;

	push ( @output_slaves, { name => $_ } ) for @bond_slaves;

	my $body = {
				 description => $desc,
				 params      => {
							 name   => $bond,
							 mode   => $bond_modes_short[$bonds->{ $bond }->{ mode }],
							 slaves => \@output_slaves,
							 status => $if_ref->{ status },
							 mac    => $if_ref->{ mac },
				 },
	};

	return &httpResponse( { code => 201, body => $body } );
}

sub delete_interface_bond    # ( $bond )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $bond = shift;

	require Zevenet::Net::Core;
	require Zevenet::Net::Route;
	require Zevenet::Net::Interface;

	my $desc   = "Delete bonding network configuration";
	my $ip_v   = 4;
	my $if_ref = &getInterfaceConfig( $bond, $ip_v );

	if ( !$if_ref )
	{
		my $msg = "There is no configuration for the network interface.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# Do not delete the interface if it has some vlan configured
	my @child = &getInterfaceChild( $bond );

	if ( @child )
	{
		my $child_string = join ( ', ', @child );
		my $msg =
		  "It is not possible to delete $bond because there are virtual interfaces using it: $child_string.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# check if some farm is using this ip
	require Zevenet::Farm::Base;

	my @farms = &getFarmListByVip( $if_ref->{ addr } );

	if ( @farms )
	{
		my $str = join ( ', ', @farms );
		my $msg = "This interface is being used as vip in the farm(s): $str.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	eval {
		die if &delRoutes( "local", $if_ref );
		die if &delIf( $if_ref );
		unlink &getInterfaceConfigFile( $if_ref->{ name } );
	};

	if ( $@ )
	{
		my $msg =
		  "The configuration for the bonding interface $bond couldn't be deleted.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $message =
	  "The configuration for the bonding interface $bond has been deleted.";
	my $body = {
				 description => $desc,
				 success     => "true",
				 message     => $message,
	};

	return &httpResponse( { code => 200, body => $body } );
}

sub delete_bond    # ( $bond )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $bond = shift;

	require Zevenet::Net::Core;
	include 'Zevenet::Net::Bonding';

	my $desc  = "Remove bonding interface";
	my $bonds = &getBondConfig();

	# validate BOND
	unless ( $bonds->{ $bond } )
	{
		my $msg = "Bonding interface name not found";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	#not destroy it if it has a VLAN configured
	my @vlans = grep ( /^$bond\./, &getLinkNameList() );
	if ( @vlans )
	{
		my $child_string = join ( ', ', @vlans );
		my $msg =
		  "It is not possible to delete $bond if it has configured VLAN: $child_string.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	#not destroy it if it has a virtual interface configured
	my @child = &getInterfaceChild( $bond );
	if ( @child )
	{
		my $child_string = join ( ', ', @child );
		my $msg =
		  "It is not possible to delete $bond because there are virtual interfaces using it: $child_string.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $if_ref = &getInterfaceConfig( $bond );

	# check if some farm is using this ip
	require Zevenet::Farm::Base;
	my @farms = &getFarmListByVip( $if_ref->{ addr } );
	if ( @farms )
	{
		my $str = join ( ', ', @farms );
		my $msg = "This interface is being used as vip in the farm(s): $str.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $bond_in_use = 0;
	my $bond_hash = &getInterfaceConfig( $bond, 4 );
	$bond_in_use = 1 if ( $bond_hash and defined $bond_hash->{ addr } );

	$bond_hash = &getInterfaceConfig( $bond, 6 );
	$bond_in_use = 1 if ( $bond_hash and defined $bond_hash->{ addr } );

	if ( $bond_in_use )
	{
		my $msg =
		  "It is not possible to delete the bonding interface because it is configured. First you should unset the bonding configuration.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	eval {
		if ( ${ &getSystemInterface( $bond ) }{ status } eq 'up' )
		{
			die if &downIf( $bonds->{ $bond }, 'writeconf' );
		}

		die if &setBondMaster( $bond, 'del', 'writeconf' );
	};

	if ( $@ )
	{
		my $msg = "The bonding interface $bond could not be deleted";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $message = "The bonding interface $bond has been deleted.";
	my $body = {
				 description => $desc,
				 success     => "true",
				 message     => $message,
	};

	return &httpResponse( { code => 200, body => $body } );
}

sub delete_bond_slave    # ( $bond, $slave )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $bond  = shift;
	my $slave = shift;

	include 'Zevenet::Net::Bonding';

	my $desc  = "Remove bonding slave interface";
	my $bonds = &getBondConfig();

	# validate BOND
	unless ( $bonds->{ $bond } )
	{
		my $msg = "Bonding interface not found";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	# validate SLAVE
	unless ( grep ( { $slave eq $_ } @{ $bonds->{ $bond }->{ slaves } } ) )
	{
		my $msg = "Bonding slave interface not found";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	eval {
		@{ $bonds->{ $bond }{ slaves } } =
		  grep ( { $slave ne $_ } @{ $bonds->{ $bond }{ slaves } } );
		die if &applyBondChange( $bonds->{ $bond }, 'writeconf' );
	};

	if ( $@ )
	{
		my $msg = "The bonding slave interface $slave could not be removed";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $message = "The bonding slave interface $slave has been removed.";
	my $body = {
				 description => $desc,
				 success     => "true",
				 message     => $message,
	};

	return &httpResponse( { code => 200, body => $body } );
}

sub get_bond_list    # ()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	include 'Zevenet::Net::Bonding';

	my $desc            = "List bonding interfaces";
	my $output_list_ref = &get_bond_list_struct();

	my $body = {
				 description => $desc,
				 interfaces  => $output_list_ref,
	};

	return &httpResponse( { code => 200, body => $body } );
}

sub get_bond    # ()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $bond = shift;

	include 'Zevenet::Net::Bonding';
	require Zevenet::Net::Interface;

	my $desc      = "Show bonding interface";
	my $interface = &get_bond_struct( $bond );    # output

	unless ( $interface )
	{
		my $msg = "Bonding interface not found.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $body = {
				 description => $desc,
				 interface   => $interface,
	};

	return &httpResponse( { code => 200, body => $body } );
}

sub actions_interface_bond    # ( $json_obj, $bond )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $bond     = shift;

	require Zevenet::Net::Core;
	require Zevenet::Net::Interface;

	my $desc = "Action on bond interface";
	my $ip_v = 4;

	unless ( grep { $bond eq $_->{ name } } &getInterfaceTypeList( 'bond' ) )
	{
		my $msg = "Bond interface not found";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	if ( grep { $_ ne 'action' } keys %$json_obj )
	{
		my $msg = "Only the parameter 'action' is accepted";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# validate action parameter
	if ( $json_obj->{ action } eq 'destroy' )
	{
		return &delete_bond( $bond );    # doesn't return
	}
	elsif ( $json_obj->{ action } eq "up" )
	{
		require Zevenet::Net::Route;

		my $if_ref = &getInterfaceConfig( $bond, $ip_v );

		if ( exists $if_ref->{ addr } and $if_ref->{ addr } ne "" )
		{
			&delRoutes( "local", $if_ref ) if $if_ref;
			&addIp( $if_ref ) if $if_ref;
		}

		my $state = &upIf( { name => $bond }, 'writeconf' );

		if ( !$state )
		{
			require Zevenet::Net::Util;

			if ( exists $if_ref->{ addr } and $if_ref->{ addr } ne "" )
			{
				&applyRoutes( "local", $if_ref ) if $if_ref;
			}

			# put all dependant interfaces up
			&setIfacesUp( $bond, "vlan" );
			&setIfacesUp( $bond, "vini" ) if $if_ref;
		}
		else
		{
			my $msg = "The interface $bond could not be set UP";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}
	elsif ( $json_obj->{ action } eq "down" )
	{
		my $state = &downIf( { name => $bond }, 'writeconf' );

		if ( $state )
		{
			my $msg = "The interface $bond could not be set UP";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}
	else
	{
		my $msg = "Action accepted values are: up, down or destroy";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $body = {
				 description => $desc,
				 params      => { action => $json_obj->{ action } },
	};

	return &httpResponse( { code => 200, body => $body } );
}

sub modify_interface_bond    # ( $json_obj, $bond )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $bond     = shift;

	require Zevenet::Net::Core;
	require Zevenet::Net::Route;
	require Zevenet::Net::Interface;
	require Zevenet::Net::Validate;

	my $desc = "Modify bond address";
	my @farms;

	# validate BOND NAME
	my $type = &getInterfaceType( $bond );

	unless ( $type eq 'bond' )
	{
		my $msg = "Bonding interface not found.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	if ( grep { !/^(?:ip|netmask|gateway|force)$/ } keys %$json_obj )
	{
		my $msg = "Parameter not recognized";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	unless (    exists $json_obj->{ ip }
			 || exists $json_obj->{ netmask }
			 || exists $json_obj->{ gateway } )
	{
		my $msg = "No parameter received to be configured";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# Check address errors
	if ( exists $json_obj->{ ip } )
	{
		my $defined_ip = defined $json_obj->{ ip } && $json_obj->{ ip } ne '';
		my $ip_ver = &ipversion( $json_obj->{ ip } );

		unless ( !$defined_ip || $ip_ver )
		{
			my $msg = "Invalid IP address.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}

		if ( $json_obj->{ ip } eq '' )
		{
			$json_obj->{ netmask } = '';
			$json_obj->{ gateway } = '';
		}
	}

	# Check netmask errors
	if ( exists $json_obj->{ netmask } )
	{
		my $defined_mask =
		  defined $json_obj->{ netmask } && $json_obj->{ netmask } ne '';

		unless (   !$defined_mask
				 || &getValidFormat( 'ip_mask', $json_obj->{ netmask } ) )
		{
			my $msg = "Invalid network mask.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

	# Check gateway errors
	if ( exists $json_obj->{ gateway } )
	{
		my $defined_gw = defined $json_obj->{ gateway } && $json_obj->{ gateway } ne '';

		unless ( !$defined_gw || &getValidFormat( 'ip_addr', $json_obj->{ gateway } ) )
		{
			my $msg = "Invalid gateway address.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

	# Delete old interface configuration
	my $if_ref = &getInterfaceConfig( $bond );

	# check if network is correct
	my $new_if = {
				   addr    => $json_obj->{ ip }      // $if_ref->{ addr },
				   mask    => $json_obj->{ netmask } // $if_ref->{ mask },
				   gateway => $json_obj->{ gateway } // $if_ref->{ gateway },
	};

	# Make sure the address, mask and gateway belong to the same stack
	if ( $new_if->{ addr } )
	{
		my $ip_v = &ipversion( $new_if->{ addr } );
		my $gw_v = &ipversion( $new_if->{ gateway } );

		my $mask_v =
		    ( $ip_v == 4 && &getValidFormat( 'IPv4_mask', $new_if->{ mask } ) ) ? 4
		  : ( $ip_v == 6 && &getValidFormat( 'IPv6_mask', $new_if->{ mask } ) ) ? 6
		  :                                                                       '';

		if ( $ip_v ne $mask_v
			 || ( $new_if->{ gateway } && $ip_v ne $gw_v ) )
		{
			my $msg = "Invalid IP stack version match.";
			&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

# Do not modify gateway or netmask if exists a virtual interface using this interface
	if ( exists $json_obj->{ ip } or exists $json_obj->{ netmask } )
	{
		my @child = &getInterfaceChild( $bond );
		my @wrong_conf;

		foreach my $child_name ( @child )
		{
			my $child_if = &getInterfaceConfig( $child_name );

			unless (
				  &getNetValidate( $child_if->{ addr }, $new_if->{ mask }, $new_if->{ addr } ) )
			{
				push @wrong_conf, $child_name;
			}
		}

		if ( @wrong_conf )
		{
			my $child_string = join ( ', ', @wrong_conf );
			my $msg =
			  "The virtual interface(s): '$child_string' will not be compatible with the new configuration.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

	# check the gateway is in network
	if ( $new_if->{ gateway } )
	{
		unless (
			 &getNetValidate( $new_if->{ addr }, $new_if->{ mask }, $new_if->{ gateway } ) )
		{
			my $msg = "The gateway is not valid for the network.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

	# check if network exists in other interface
	if ( $json_obj->{ ip } or $json_obj->{ netmask } )
	{
		my $if_used =
		  &checkNetworkExists( $new_if->{ addr }, $new_if->{ mask }, $bond );

		if ( $if_used )
		{
			my $msg = "The network already exists in the interface $if_used.";
			&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

	# check if some farm is using this ip
	if ( $json_obj->{ ip } )
	{
		require Zevenet::Farm::Base;
		@farms = &getFarmListByVip( $if_ref->{ addr } );

		if ( @farms and $json_obj->{ force } ne 'true' )
		{
			my $str = join ( ', ', @farms );
			my $msg =
			  "The IP is being used as farm vip in the farm(s): $str. If you are sure, repeat with parameter 'force'. All farms using this interface will be restarted.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

	# hash reference may exist without key-value pairs
	if ( $if_ref->{ addr } )
	{
		# Delete old IP and Netmask from system to replace it
		&delIp( $if_ref->{ name }, $if_ref->{ addr }, $if_ref->{ mask } );

		# Remove routes if the interface has its own route table: nic and vlan
		&delRoutes( "local", $if_ref );

		$if_ref = undef;
	}

	# Setup new interface configuration structure
	$if_ref = &getInterfaceConfig( $bond ) // &getSystemInterface( $bond );
	$if_ref->{ addr }    = $json_obj->{ ip }      if exists $json_obj->{ ip };
	$if_ref->{ mask }    = $json_obj->{ netmask } if exists $json_obj->{ netmask };
	$if_ref->{ gateway } = $json_obj->{ gateway } if exists $json_obj->{ gateway };
	$if_ref->{ ip_v } = &ipversion( $if_ref->{ addr } );

	unless ( $if_ref->{ addr } && $if_ref->{ mask } )
	{
		my $msg = "Cannot configure the interface without address or without netmask.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	eval {

		# Add new IP, netmask and gateway
		die if &addIp( $if_ref );

		# Writing new parameters in configuration file
		die if &writeRoutes( $if_ref->{ name } );

		# Put the interface up
		my $previous_status = $if_ref->{ status };
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

		&setInterfaceConfig( $if_ref ) or die;

		# if the GW is changed, change it in all appending virtual interfaces
		if ( exists $json_obj->{ gateway } )
		{
			foreach my $appending ( &getInterfaceChild( $bond ) )
			{
				my $app_config = &getInterfaceConfig( $appending );
				$app_config->{ gateway } = $json_obj->{ gateway };
				&setInterfaceConfig( $app_config );
			}
		}

		# put all dependant interfaces up
		require Zevenet::Net::Util;
		&setIfacesUp( $bond, "vini" );

		# change farm vip,
		if ( @farms )
		{
			require Zevenet::Farm::Config;
			&setAllFarmByVip( $json_obj->{ ip }, \@farms );
		}
	};

	if ( $@ )
	{
		my $msg = "Errors found trying to modify interface $bond";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $body = {
				 description => $desc,
				 params      => $json_obj,
	};

	return &httpResponse( { code => 200, body => $body } );
}

1;
