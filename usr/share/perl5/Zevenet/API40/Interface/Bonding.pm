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

use Zevenet::API40::HTTP;

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

	my $params = {
			 "name" => {
						 'valid_format' => 'bond_interface',
						 'required'     => 'true',
						 'non_blank'    => 'true',
			 },
			 "slaves" => {
						   'required' => 'true',
						   'ref'      => 'array',
			 },
			 "mode" => {
					 'values' => [
								  'balance-rr', 'active-backup', 'balance-xor', 'broadcast',
								  '802.3ad',    'balance-tlb',   'balance-alb'
					 ],
					 'required'  => 'true',
					 'non_blank' => 'true',
			 },
	};

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	zenlog( "ERROR MSG: $error_msg" );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	# size < 16: size = bonding_name.vlan_name:virtual_name
	if ( length $json_obj->{ name } > 11 )
	{
		my $msg = "Bonding interface name has a maximum length of 11 characters";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	unless ( &ifexist( $json_obj->{ name } ) eq 'false' )
	{
		my $msg = "Interface name is not valid";
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
		&zenlog( "Module failed: $@", "error", "net" );
		my $msg = "The $json_obj->{ name } bonding network interface can't be created";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	if ( &saveBondDefaultConfig( $json_obj->{ name } ) )
	{
		my $msg = "There is a problem storing the default configuration";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $if_ref      = &getSystemInterface( $json_obj->{ name } );
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
	&lockBondResource();

	# validate BOND NAME
	my $bonds = &getBondConfig();

	unless ( $bonds->{ $bond } )
	{
		my $msg = "Bond interface name not found";
		&unlockBondResource();
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $params = {
				   "name" => {
							   'valid_format' => 'nic_interface',
							   'required'     => 'true',
							   'non_blank'    => 'true',
				   },
	};

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	if ( $error_msg )
	{
		&unlockBondResource();
		return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg );
	}

	# validate SLAVE
	my $msg;
	if ( grep ( { $json_obj->{ name } eq $_ } @{ $bonds->{ $bond }->{ slaves } } ) )
	{
		$msg = "The '$json_obj->{ name }' interface already is added as slave";
	}
	elsif ( !&getValidFormat( 'nic_interface', $json_obj->{ name } ) )
	{
		$msg = "The interface should be a NIC.";
	}
	elsif ( !grep ( { $json_obj->{ name } eq $_ } &getBondAvailableSlaves() ) )
	{
		$msg = "The '$json_obj->{name}' interface should be down and unset";
	}

	if ( defined $msg )
	{
		&unlockBondResource();
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	push @{ $bonds->{ $bond }->{ slaves } }, $json_obj->{ name };

	eval { die if &applyBondChange( $bonds->{ $bond }, 'writeconf' ); };
	if ( $@ )
	{
		&zenlog( "Module failed: $@", "error", "net" );
		my $msg = "The $json_obj->{ name } bonding network interface can't be created";
		&unlockBondResource();
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
	&unlockBondResource();
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

	include 'Zevenet::Net::Ext';
	my $msg = &isManagementIP( $if_ref->{ addr } );
	if ( $msg ne "" )
	{
		$msg = "The interface cannot be modified. $msg";
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
		if ( defined $if_ref->{ addr } and defined $if_ref->{ mask } )
		{
			die if &delRoutes( "local", $if_ref );
			die if &delIf( $if_ref );
		}

		# remove configuration
		my $if_ref = { name => $bond, status => $if_ref->{ status } };
		die if ( !&setInterfaceConfig( $if_ref ) );
	};

	if ( $@ )
	{
		&zenlog( "Module failed: $@", "error", "net" );
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
	$bond_in_use = 1
	  if (     $bond_hash
		   and defined $bond_hash->{ addr }
		   and length $bond_hash->{ addr } );

	$bond_hash = &getInterfaceConfig( $bond, 6 );
	$bond_in_use = 1
	  if (     $bond_hash
		   and defined $bond_hash->{ addr }
		   and length $bond_hash->{ addr } );

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
		&zenlog( "Module failed: $@", "error", "net" );
		my $msg = "The bonding interface $bond could not be deleted";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	if ( &delBondDefaultConfig( $bond ) )
	{
		my $msg =
		  "The bonding interface $bond default configuration could not be deleted";
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

	my $desc = "Remove bonding slave interface";

	# Locking bond resources
	&lockBondResource();

	my $bonds = &getBondConfig();

	# validate BOND
	unless ( $bonds->{ $bond } )
	{
		my $msg = "Bonding interface not found";
		&unlockBondResource();
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	# validate SLAVE
	unless ( grep ( { $slave eq $_ } @{ $bonds->{ $bond }->{ slaves } } ) )
	{
		my $msg = "The '$slave' bonding slave interface was not found";
		&unlockBondResource();
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	eval {
		@{ $bonds->{ $bond }{ slaves } } =
		  grep ( { $slave ne $_ } @{ $bonds->{ $bond }{ slaves } } );
		die if &applyBondChange( $bonds->{ $bond }, 'writeconf' );
	};

	if ( $@ )
	{
		&zenlog( "Module failed: $@", "error", "net" );
		my $msg = "The bonding slave interface $slave could not be removed";
		&unlockBondResource();
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $message = "The bonding slave interface $slave has been removed.";
	my $body = {
				 description => $desc,
				 success     => "true",
				 message     => $message,
	};
	&unlockBondResource();
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
				 interfaces  => $output_list_ref // [],
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

	my $params = {
				   "action" => {
								 'non_blank' => 'true',
								 'required'  => 'true',
								 'values'    => ['destroy', 'up', 'down'],
				   },
	};

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	unless ( grep { $bond eq $_->{ name } } &getInterfaceTypeList( 'bond' ) )
	{
		my $msg = "Bond interface not found";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $if_ref = &getInterfaceConfig( $bond, $ip_v );

	# validate action parameter
	if ( $json_obj->{ action } eq 'destroy' )
	{
		return &delete_bond( $bond );    # doesn't return
	}
	elsif ( $json_obj->{ action } eq "up" )
	{
		require Zevenet::Net::Route;

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
		include 'Zevenet::Net::Ext';
		my $msg = &isManagementIP( $if_ref->{ addr } );
		if ( $msg ne "" )
		{
			$msg = "The interface cannot be stopped. $msg";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}

		my $state = &downIf( { name => $bond }, 'writeconf' );
		if ( $state )
		{
			my $msg = "The interface $bond could not be set UP";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
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

	# validate BOND NAME
	my $type = &getInterfaceType( $bond );

	unless ( $type eq 'bond' )
	{
		my $msg = "Bonding interface not found.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $params = {
				   "ip" => {
							 'valid_format' => 'ip_addr',
							 'non_blank'    => 'true',
				   },
				   "netmask" => {
								  'valid_format' => 'ip_mask',
								  'non_blank'    => 'true',
				   },
				   "gateway" => {
								  'valid_format' => 'ip_addr',
				   },
				   "force" => {
								'non_blank' => 'true',
								'values'    => ['true'],
				   },
				   "mac" => {
							  'valid_format' => 'mac_addr',
				   },
				   "dhcp" => {
							   'non_blank' => 'true',
							   'values'    => ['true', 'false'],
				   },
	};

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	my $if_ref = &getInterfaceConfig( $bond );

	my @child = &getInterfaceChild( $bond );

	# check if some farm is using this ip
	my @farms;
	if ( exists $json_obj->{ ip }
		 or ( exists $json_obj->{ dhcp } ) )
	{
		include 'Zevenet::Net::Ext';
		my $msg = &isManagementIP( [$if_ref->{ addr }] );
		if ( $msg ne "" )
		{
			$msg = "The interface cannot be modified. $msg";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}

		require Zevenet::Farm::Base;
		@farms = &getFarmListByVip( $if_ref->{ addr } );
		if ( @farms )
		{
			if (    !exists $json_obj->{ ip }
				 and exists $json_obj->{ dhcp }
				 and $json_obj->{ dhcp } eq 'false' )
			{
				my $msg =
				  "This interface is been used by some farms, please, set up a new 'ip' in order to be used as farm vip.";
				&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
			}
			if ( $json_obj->{ force } ne 'true' )
			{
				my $str = join ( ', ', @farms );
				my $msg =
				  "The IP is being used as farm vip in the farm(s): $str. If you are sure, repeat with parameter 'force'. All farms using this interface will be restarted.";
				return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
			}
		}
	}

	my $dhcp_status = $json_obj->{ dhcp } // $if_ref->{ dhcp };

	# only allow dhcp when no other parameter was sent
	if ( $dhcp_status eq 'true' )
	{
		if (    exists $json_obj->{ ip }
			 or exists $json_obj->{ netmask }
			 or exists $json_obj->{ gateway } )
		{
			my $msg =
			  "It is not possible set 'ip', 'netmask' or 'gateway' while 'dhcp' is enabled.";
			&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}
	if ( !exists $json_obj->{ ip } and exists $json_obj->{ dhcp } and @child )
	{
		my $msg =
		  "This interface has appending some virtual interfaces, please, set up a new 'ip' in the current networking range.";
		&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	if ( exists $json_obj->{ dhcp } )
	{
		include 'Zevenet::Net::DHCP';
		my $err =
		  ( $json_obj->{ dhcp } eq 'true' )
		  ? &enableDHCP( $if_ref )
		  : &disableDHCP( $if_ref );
		if ( $err )
		{
			my $msg = "Errors found trying to enabling dhcp for the interface $bond";
			&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

	if (    exists $json_obj->{ ip }
		 or exists $json_obj->{ netmask }
		 or exists $json_obj->{ gateway }
		 or exists $json_obj->{ mac } )
	{
		# Check address errors
		if ( exists $json_obj->{ ip } )
		{
			if ( $json_obj->{ ip } eq '' )
			{
				$json_obj->{ netmask } = '';
				$json_obj->{ gateway } = '';
			}
		}

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
				return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
			}
		}

		if ( exists $json_obj->{ ip } or exists $json_obj->{ netmask } )
		{
			# check ip and netmas are configured
			unless ( $new_if->{ addr } ne "" and $new_if->{ mask } ne "" )
			{
				my $msg =
				  "The networking configuration is not valid. It needs an IP ('$new_if->{addr}') and a netmask ('$new_if->{mask}')";
				&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
			}

	   # Do not modify gateway or netmask if exists a virtual interface using this interface
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
				return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
			}
		}

		my $old_ip = $if_ref->{ addr };

		# Setup new interface configuration structure
		$if_ref->{ addr }    = $json_obj->{ ip }      if exists $json_obj->{ ip };
		$if_ref->{ mask }    = $json_obj->{ netmask } if exists $json_obj->{ netmask };
		$if_ref->{ gateway } = $json_obj->{ gateway } if exists $json_obj->{ gateway };
		$if_ref->{ mac }     = lc $json_obj->{ mac }  if exists $json_obj->{ mac };
		$if_ref->{ ip_v } = &ipversion( $if_ref->{ addr } );
		$if_ref->{ name } = $bond;

		unless (
				 ( exists $if_ref->{ addr } && exists $if_ref->{ mask } )
				 || ( !( exists $if_ref->{ addr } || exists $if_ref->{ mask } )
					  && exists $if_ref->{ mac } )
		  )
		{
			my $msg = "Interface address and netmask must be together set.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
		include 'Zevenet::Net::Bonding';

		# remove custom routes
		include 'Zevenet::Net::Routing';
		&updateRoutingVirtualIfaces( $if_ref->{ parent }, $old_ip ) if ( $old_ip );

		#Change Bonding IP Address
		if ( exists $json_obj->{ ip } || exists $json_obj->{ gateway } )
		{
			if ( &setBondIP( $if_ref ) )
			{
				my $msg = "Errors found trying to modify IP address on interface $bond";
				return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
			}
		}
	}

	#Change MAC Address
	include 'Zevenet::Net::Bonding';
	my $error = &setBondMac( $if_ref ) if ( exists $json_obj->{ mac } );

	if ( $error )
	{
		my $msg = "Errors found trying to modify MAC address on interface $bond";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $if_out = &get_bond_struct( $bond );
	my $body = {
				 description => $desc,
				 params      => $if_out,
	};

	return &httpResponse( { code => 200, body => $body } );
}

1;
