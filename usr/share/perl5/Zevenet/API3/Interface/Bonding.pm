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

my @bond_modes_short = (
				'balance-rr',
				'active-backup',
				'balance-xor',
				'broadcast',
				'802.3ad',
				'balance-tlb',
				'balance-alb',
);

sub new_bond # ( $json_obj )
{
	my $json_obj = shift;

	my $description = "Add a bond interface";

	# validate BOND NAME
	my $bond_re = &getValidFormat( 'bond_interface' );

	require Zevenet::Net::Validate;

	unless ( $json_obj->{ name } =~ /^$bond_re$/ && &ifexist($json_obj->{ name }) eq 'false' )
	{
		# Error
		my $errormsg = "Interface name is not valid";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	# validate BOND MODE
	unless ( $json_obj->{ mode } && &getValidFormat( 'bond_mode_short', $json_obj->{ mode } ) )
	{
		# Error
		my $errormsg = "Bond mode is not valid";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	require Zevenet::System;
	$json_obj->{ mode } = &indexOfElementInArray( $json_obj->{ mode }, \@bond_modes_short );

	# validate SLAVES
	require Zevenet::Net::Bonding;
	my $missing_slave;
	for my $slave ( @{ $json_obj->{slaves} } )
	{
		unless ( grep { $slave eq $_ } &getBondAvailableSlaves() )
		{
			$missing_slave = $slave;
			last;
		}
	}

	if ( $missing_slave || !@{ $json_obj->{ slaves } } )
	{
		&zenlog("missing_slave:$missing_slave slaves:@{ $json_obj->{ slaves } }");
		# Error
		my $errormsg = "Error loading the slave interfaces list";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	eval {
		die if &applyBondChange( $json_obj, 'writeconf' );
	};

	if ( ! $@ )
	{
		my $if_ref = getSystemInterface( $json_obj->{ name } );

		# Success
		my @bond_slaves = @{ $json_obj->{ slaves } };
		my @output_slaves;
		push( @output_slaves, { name => $_ } ) for @bond_slaves;

		my $body = {
					 description => $description,
					 params      => {
								 name   => $json_obj->{ name },
								 mode   => $bond_modes_short[$json_obj->{ mode }],
								 slaves => \@output_slaves,
								 status => $if_ref->{ status },
								 mac    => $if_ref->{ mac },
					 },
		};

		&httpResponse({ code => 201, body => $body });
	}
	else
	{
		# Error
		my $errormsg = "The $json_obj->{ name } bonding network interface can't be created";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

# POST bond slave
# slave: nic
sub new_bond_slave # ( $json_obj, $bond )
{
	my $json_obj = shift;
	my $bond     = shift;

	my $description = "Add a slave to a bond interface";

	require Zevenet::Net::Bonding;

	# validate BOND NAME
	my $bonds = &getBondConfig();

	unless ( $bonds->{ $bond } )
	{
		# Error
		my $errormsg = "Bond interface name not found";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	# validate SLAVE
	eval {
		$json_obj->{ name } or die;
		&getValidFormat( 'nic_interface', $json_obj->{ name } ) or die;
		grep ( { $json_obj->{ name } eq $_ } &getBondAvailableSlaves() ) or die;
		die if grep ( { $json_obj->{ name } eq $_ } @{ $bonds->{ $bond }->{ slaves } } );
	};
	if ( $@ )
	{
		# Error
		my $errormsg = "Could not add the slave interface to this bonding";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	push @{ $bonds->{ $bond }->{ slaves } }, $json_obj->{ name };

	eval {
		die if &applyBondChange( $bonds->{ $bond }, 'writeconf' );
	};
	if ( ! $@ )
	{
		my $if_ref = getSystemInterface( $bond );

		# Success
		my @bond_slaves = @{ $bonds->{ $bond }->{ slaves } };
		my @output_slaves;
		push( @output_slaves, { name => $_ } ) for @bond_slaves;

		my $body = {
					 description => $description,
					 params      => {
								 name   => $bond,
								 mode   => $bond_modes_short[$bonds->{ $bond }->{ mode }],
								 slaves => \@output_slaves,
								 status => $if_ref->{ status },
								 mac    => $if_ref->{ mac },
					 },
		};

		&httpResponse({ code => 201, body => $body });
	}
	else
	{
		# Error
		my $errormsg = "The $json_obj->{ name } bonding network interface can't be created";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

sub delete_interface_bond # ( $bond )
{
	my $bond = shift;

	require Zevenet::Net::Interface;

	my $description = "Delete bonding network configuration";
	my $ip_v = 4;
	my $if_ref = &getInterfaceConfig( $bond, $ip_v );

	if ( !$if_ref )
	{
		# Error
		my $errormsg = "There is no configuration for the network interface.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 400, body => $body });
	}

	require Zevenet::Net::Core;
	require Zevenet::Net::Route;

	eval {
		die if &delRoutes( "local", $if_ref );
		die if &downIf( $if_ref, 'writeconf' ); # FIXME: To be removed
		die if &delIf( $if_ref );
	};

	if ( ! $@ )
	{
		# Success
		my $message = "The configuration for the bonding interface $bond has been deleted.";
		my $body = {
					 description => $description,
					 success     => "true",
					 message     => $message,
		};

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		# Error
		my $errormsg = "The configuration for the bonding interface $bond can't be deleted: $@";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 400, body => $body });
	}
}

sub delete_bond # ( $bond )
{
	my $bond = shift;

	my $description = "Remove bonding interface";
	my $bonds = &getBondConfig();

	# validate BOND
	unless ( $bonds->{ $bond } )
	{
		# Error
		my $errormsg = "Bonding interface name not found";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	my $bond_in_use = 0;
	$bond_in_use = 1 if &getInterfaceConfig( $bond, 4 );
	$bond_in_use = 1 if &getInterfaceConfig( $bond, 6 );
	$bond_in_use = 1 if grep ( /^$bond(:|\.)/, &getInterfaceList() );

	if ( $bond_in_use )
	{
		# Error
		my $errormsg = "Bonding interface is being used";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	require Zevenet::Net::Core;

	eval {
		if ( ${ &getSystemInterface( $bond ) }{ status } eq 'up' )
		{
			die if &downIf( $bonds->{ $bond }, 'writeconf' );
		}

		die if &setBondMaster( $bond, 'del', 'writeconf' );
	};

	if ( ! $@ )
	{
		# Success
		my $message = "The bonding interface $bond has been deleted.";
		my $body = {
					 description => $description,
					 success     => "true",
					 message     => $message,
		};

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		# Error
		my $errormsg = "The bonding interface $bond could not be deleted";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 400, body => $body });
	}
}

sub delete_bond_slave # ( $bond, $slave )
{
	my $bond  = shift;
	my $slave = shift;

	require Zevenet::Net::Bonding;

	my $description = "Remove bonding slave interface";
	my $bonds = &getBondConfig();

	# validate BOND
	unless ( $bonds->{ $bond } )
	{
		# Error
		my $errormsg = "Bonding interface not found";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	# validate SLAVE
	unless ( grep ( { $slave eq $_ } @{ $bonds->{ $bond }->{ slaves } } ) )
	{
		# Error
		my $errormsg = "Bonding slave interface not found";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	eval {
		@{ $bonds->{ $bond }->{ slaves } } = grep ( { $slave ne $_ } @{ $bonds->{ $bond }->{ slaves } } );
		die if &applyBondChange( $bonds->{ $bond }, 'writeconf' );
	};
	if ( ! $@ )
	{
		# Success
		my $message = "The bonding slave interface $slave has been removed.";
		my $body = {
					 description => $description,
					 success     => "true",
					 message     => $message,
		};

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		# Error
		my $errormsg = "The bonding slave interface $slave could not be removed";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 400, body => $body });
	}
}

sub get_bond_list # ()
{
	require Zevenet::Net::Bonding;
	require Zevenet::Cluster;
	require Zevenet::Net::Interface;

	my @output_list;

	my $description = "List bonding interfaces";
	my $bond_conf = &getBondConfig();

	# get cluster interface
	my $zcl_conf  = &getZClusterConfig();
	my $cluster_if = $zcl_conf->{ _ }->{ interface };
	
	for my $if_ref ( &getInterfaceTypeList( 'bond' ) )
	{
		$if_ref->{ status } = &getInterfaceSystemStatus( $if_ref );

		# Any key must cotain a value or "" but can't be null
		if ( ! defined $if_ref->{ name } )    { $if_ref->{ name }    = ""; }
		if ( ! defined $if_ref->{ addr } )    { $if_ref->{ addr }    = ""; }
		if ( ! defined $if_ref->{ mask } )    { $if_ref->{ mask }    = ""; }
		if ( ! defined $if_ref->{ gateway } ) { $if_ref->{ gateway } = ""; }
		if ( ! defined $if_ref->{ status } )  { $if_ref->{ status }  = ""; }
		if ( ! defined $if_ref->{ mac } )     { $if_ref->{ mac }     = ""; }
		
		my @bond_slaves = @{ $bond_conf->{ $if_ref->{ name } }->{ slaves } };
		my @output_slaves;
		push( @output_slaves, { name => $_ } ) for @bond_slaves;

		my $if_conf = 
		  {
			name    => $if_ref->{ name },
			ip      => $if_ref->{ addr },
			netmask => $if_ref->{ mask },
			gateway => $if_ref->{ gateway },
			status  => $if_ref->{ status },
			mac     => $if_ref->{ mac },

			slaves => \@output_slaves,
			mode => $bond_modes_short[$bond_conf->{ $if_ref->{ name } }->{ mode }],
			#~ ipv     => $if_ref->{ ip_v },
		  };
		  
		  $if_conf->{ is_cluster } = 'true' if $cluster_if eq $if_ref->{ name };
		  
		  push @output_list, $if_conf;
	}

	my $body = {
			description => $description,
			interfaces  => \@output_list,
		};

	&httpResponse({ code => 200, body => $body });
}

sub get_bond # ()
{
	my $bond = shift;

	require Zevenet::Net::Bonding;
	require Zevenet::Net::Interface;

	my $interface; # output
	my $description = "Show bonding interface";
	my $bond_conf = &getBondConfig();

	for my $if_ref ( &getInterfaceTypeList( 'bond' ) )
	{
		next unless $if_ref->{ name } eq $bond;

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
		push( @output_slaves, { name => $_ } ) for @bond_slaves;

		$interface = {
					 name    => $if_ref->{ name },
					 ip      => $if_ref->{ addr },
					 netmask => $if_ref->{ mask },
					 gateway => $if_ref->{ gateway },
					 status  => $if_ref->{ status },
					 mac     => $if_ref->{ mac },
					 slaves  => \@output_slaves,
					 mode => $bond_modes_short[$bond_conf->{ $if_ref->{ name } }->{ mode }],
		};
	}

	if ( $interface )
	{
		my $body = {
					 description => $description,
					 interface   => $interface,
		};

		&httpResponse( { code => 200, body => $body } );
	}
	else
	{
		# Error
		my $errormsg = "Bonding interface not found.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 404, body => $body } );
	}
}

sub actions_interface_bond # ( $json_obj, $bond )
{
	my $json_obj = shift;
	my $bond 	 = shift;

	my $description = "Action on bond interface";
	my $ip_v = 4;

	require Zevenet::Net::Interface;

	unless ( grep { $bond eq $_->{ name } } &getInterfaceTypeList( 'bond' ) )
	{
		# Error
		my $errormsg = "Bond interface not found";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	if ( grep { $_ ne 'action' } keys %$json_obj )
	{
		# Error
		my $errormsg = "Only the parameter 'action' is accepted";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	require Zevenet::Net::Core;

	# validate action parameter
	if ( $json_obj->{ action } eq 'destroy' )
	{
		&delete_bond( $bond ); # doesn't return
	}
	elsif ( $json_obj->{ action } eq "up" )
	{
		my $if_ref = &getInterfaceConfig( $bond, $ip_v );

		require Zevenet::Net::Route;

		# Delete routes in case that it is not a vini
		&delRoutes( "local", $if_ref ) if $if_ref;

		# Add IP
		&addIp( $if_ref ) if $if_ref;

		my $state = &upIf( { name => $bond }, 'writeconf' );

		if ( ! $state )
		{
			&applyRoutes( "local", $if_ref ) if $if_ref;

			# put all dependant interfaces up
			require Zevenet::Net::Util;
			&setIfacesUp( $bond, "vlan" );
			&setIfacesUp( $bond, "vini" ) if $if_ref;
		}
		else
		{
			# Error
			my $errormsg = "The interface $bond could not be set UP";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}
	}
	elsif ( $json_obj->{ action } eq "down" )
	{
		my $state = &downIf( { name => $bond }, 'writeconf' );

		if ( $state )
		{
			# Error
			my $errormsg = "The interface $bond could not be set UP";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}
	}
	else
	{
		# Error
		my $errormsg = "Action accepted values are: up, down or destroy";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	# Success
	my $body = {
				 description => $description,
				 params      =>  { action => $json_obj->{ action } },
	};

	&httpResponse({ code => 200, body => $body });
}

sub modify_interface_bond # ( $json_obj, $bond )
{
	my $json_obj = shift;
	my $bond = shift;

	my $description = "Modify bond address";
	my $ip_v = 4;

	# validate BOND NAME
	require Zevenet::Net::Interface;
	my @system_interfaces = &getInterfaceList();
	my $type = &getInterfaceType( $bond );

	unless ( grep( { $bond eq $_ } @system_interfaces ) && $type eq 'bond' )
	{
		# Error
		my $errormsg = "Nic interface not found.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	if ( grep { !/^(?:ip|netmask|gateway)$/ } keys %$json_obj )
	{
		# Error
		my $errormsg = "Parameter not recognized";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 400, body => $body });
	}

	unless ( exists $json_obj->{ ip } || exists $json_obj->{ netmask } || exists $json_obj->{ gateway } )
	{
		# Error
		my $errormsg = "No parameter received to be configured";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 400, body => $body });
	}

	# Check address errors
	if ( exists $json_obj->{ ip } )
	{
		unless ( defined( $json_obj->{ ip } ) && &getValidFormat( 'IPv4_addr', $json_obj->{ ip } ) || $json_obj->{ ip } eq '' )
		{
			# Error
			my $errormsg = "IP Address is not valid.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
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
		unless ( defined( $json_obj->{ netmask } ) && &getValidFormat( 'IPv4_mask', $json_obj->{ netmask } ) )
		{
			# Error
			my $errormsg = "Netmask Address $json_obj->{netmask} structure is not ok. Must be IPv4 structure or numeric.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}
	}

	# Check gateway errors
	if ( exists $json_obj->{ gateway } )
	{
		unless ( defined( $json_obj->{ gateway } ) && &getValidFormat( 'IPv4_addr', $json_obj->{ gateway } ) || $json_obj->{ gateway } eq '' )
		{
			# Error
			my $errormsg = "Gateway Address $json_obj->{gateway} structure is not ok.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}
	}

	# Delete old interface configuration
	my $if_ref = &getInterfaceConfig( $bond, $ip_v );

	if ( $if_ref )
	{
		require Zevenet::Net::Core;
		require Zevenet::Net::Route;

		# Delete old IP and Netmask from system to replace it
		&delIp( $if_ref->{name}, $if_ref->{addr}, $if_ref->{mask} );

		# Remove routes if the interface has its own route table: nic and vlan
		&delRoutes( "local", $if_ref );

		$if_ref = undef;
	}

	# Setup new interface configuration structure
	$if_ref              = &getInterfaceConfig( $bond ) // &getSystemInterface( $bond );
	$if_ref->{ addr }    = $json_obj->{ ip } if exists $json_obj->{ ip };
	$if_ref->{ mask }    = $json_obj->{ netmask } if exists $json_obj->{ netmask };
	$if_ref->{ gateway } = $json_obj->{ gateway } if exists $json_obj->{ gateway };
	$if_ref->{ ip_v }    = 4;

	unless ( $if_ref->{ addr } && $if_ref->{ mask } )
	{
		# Error
		my $errormsg = "Cannot configure the interface without address or without netmask.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 400, body => $body });
	}

	require Zevenet::Net::Core;
	require Zevenet::Net::Route;

	eval {

		# Add new IP, netmask and gateway
		die if &addIp( $if_ref );

		# Writing new parameters in configuration file
		die if &writeRoutes( $if_ref->{ name } );

		# Put the interface up
		{
			my $previous_status = $if_ref->{ status };
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
	};

	# Print params
	if ( ! $@ )
	{
		# Success
		my $body = {
					 description => $description,
					 params      => $json_obj,
		};

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		# Error
		my $errormsg = "Errors found trying to modify interface $bond";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}


1;
