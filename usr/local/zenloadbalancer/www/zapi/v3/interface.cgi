#!/usr/bin/perl -w

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

# POST /addvini/<interface> Create a new virtual network interface
sub new_vini # ( $json_obj )
{
	my $json_obj = shift;

	my $description = "Add a virtual interface";

	my $nic_re = &getValidFormat( 'nic_interface' );
	my $vlan_re = &getValidFormat( 'vlan_interface' );
	my $virtual_tag_re = &getValidFormat( 'virtual_tag' );

	if ( $json_obj->{ name } =~ /^($nic_re|$vlan_re):($virtual_tag_re)$/ )
	{
		$json_obj->{ parent } = $1;
		$json_obj->{ vini } = $2;

		my $vlan_tag_re = &getValidFormat( 'vlan_tag' );
		$json_obj->{ parent } =~ /^($nic_re)(?:\.($vlan_tag_re))?$/;
		$json_obj->{ dev } = $1;
		$json_obj->{ vlan } = $2;
	}
	else
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

	# validate IP
	unless ( defined( $json_obj->{ ip } ) && &getValidFormat( 'IPv4_addr', $json_obj->{ ip } ) )
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

	$json_obj->{ ip_v } = ipversion( $json_obj->{ ip } );

	# validate PARENT
	# virtual interfaces require a configured parent interface
	my $parent_exist = &ifexist( $json_obj->{ parent } );
	unless ( $parent_exist eq "true" && &getInterfaceConfig( $json_obj->{ parent }, $json_obj->{ ip_v } ) )
	{
		# Error
		my $errormsg = "The parent interface $json_obj->{ parent } doesn't exist.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
	
	# Check network interface errors
	# A virtual interface cannnot exist in two stacks
	my $if_ref = &getInterfaceConfig( $json_obj->{ name }, $json_obj->{ ip_v } );
	
	if ( $if_ref )
	{
		# Error
		my $errormsg = "Network interface $json_obj->{ name } already exists.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	# Check new IP address is not in use
	my @activeips = &listallips();
	for my $ip ( @activeips )
	{
		if ( $ip eq $json_obj->{ ip } )
		{
			# Error
			my $errormsg = "IP Address $json_obj->{ip} is already in use.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}
	}

	# setup parameters of virtual interface
	$if_ref = &getInterfaceConfig( $json_obj->{ parent }, $json_obj->{ ip_v } );

	$if_ref->{ status } = &getInterfaceSystemStatus( $json_obj );
	$if_ref->{ name } = $json_obj->{ name };
	$if_ref->{ vini } = $json_obj->{ vini };
	$if_ref->{ addr } = $json_obj->{ ip };
	$if_ref->{ gateway } = "" if ! $if_ref->{ gateway };
	$if_ref->{ type } = 'virtual';

	# No errors
	eval {
		die if &addIp( $if_ref );

		my $state = &upIf( $if_ref, 'writeconf' );

		if ( $state == 0 )
		{
			$if_ref->{ status } = "up";
			&applyRoutes( "local", $if_ref );
		}

		&setInterfaceConfig( $if_ref ) or die;
	};

	if ( !$@ )
	{
		# Success
		&runZClusterRemoteManager( 'interface', 'start', $if_ref->{ name } );

		my $body = {
					 description => $description,
					 params      => {
								 name    => $if_ref->{ name },
								 ip      => $if_ref->{ addr },
								 netmask => $if_ref->{ mask },
								 gateway => $if_ref->{ gateway },
								 mac     => $if_ref->{ mac },
					 },
		};

		&httpResponse( { code => 201, body => $body } );
	}
	else
	{
		# Error
		my $errormsg = "The $json_obj->{ name } virtual network interface can't be created";
		my $body = {
					   description => $description,
					   error       => "true",
					   message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

#  POST /addvlan/<interface> Create a new vlan network interface
sub new_vlan # ( $json_obj )
{
	my $json_obj = shift;

	my $description = "Add a vlan interface";

	# validate VLAN NAME
	my $nic_re = &getValidFormat( 'nic_interface' );
	my $vlan_tag_re = &getValidFormat( 'vlan_tag' );

	if ( $json_obj->{ name } =~ /^($nic_re)\.($vlan_tag_re)$/ )
	{
		$json_obj->{ parent } = $1;
		$json_obj->{ tag } = $2;
	}
	else
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
	
	# validate PARENT
	my $parent_exist = &ifexist($json_obj->{ parent });
	unless ( $parent_exist eq "true" )
	{
		# Error
		my $errormsg = "The parent interface $json_obj->{ parent } doesn't exist";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
	# check that nic interface is no slave of a bonding
	my $is_slave;
	for my $if_ref ( &getInterfaceTypeList( 'nic' ) )
	{
		if ( $if_ref->{ name } eq $json_obj->{ parent } )
		{
			$is_slave = $if_ref->{ is_slave };
			last;
		}
	}
	if ( $is_slave eq 'true' )
	{
		# Error
		my $errormsg = "It is not possible create a VLAN interface from a NIC slave.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	# validate VLAN TAG
	unless ( $json_obj->{ tag } >= 1 && $json_obj->{ tag } <= 4094 )
	{
		# Error
		my $errormsg = "The vlan tag must be in the range 1-4094, both included";
		my $body = {
					   description => $description,
					   error       => "true",
					   message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	# validate IP
	unless ( defined( $json_obj->{ ip } ) && &getValidFormat( 'IPv4_addr', $json_obj->{ ip } ) )
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

	$json_obj->{ ip_v } = ipversion( $json_obj->{ ip } );

	# Check if interface already exists
	my $if_ref = &getInterfaceConfig( $json_obj->{ name }, $json_obj->{ ip_v } );

	if ( $if_ref )
	{
		# Error
		my $errormsg = "Vlan network interface $json_obj->{ name } already exists.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	# FIXME: Check IPv6 compatibility
	# Check new IP address is not in use
	my @activeips = &listallips();
	for my $ip ( @activeips )
	{
		if ( $ip eq $json_obj->{ ip } )
		{
			# Error
			my $errormsg = "IP Address $json_obj->{ip} is already in use.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}
	}

	# Check netmask errors
	if ( $json_obj->{ ip_v } == 4 && ($json_obj->{ netmask } == undef || ! &getValidFormat( 'IPv4_mask', $json_obj->{ ip } )) )
	{
		# Error
		my $errormsg = "Netmask parameter not valid";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	## Check netmask errors for IPv6
	#if ( $json_obj->{ ip_v } == 6 && ( $json_obj->{netmask} !~ /^\d+$/ || $json_obj->{netmask} > 128 || $json_obj->{netmask} < 0 ) )
	#{
	#	# Error
    #    my $errormsg = "Netmask Address $json_obj->{netmask} structure is not ok. Must be numeric [0-128].";
	#	my $body = {
	#				 description => $description,
	#				 error       => "true",
	#				 message     => $errormsg
	#	};
    #
    #    &httpResponse({ code => 400, body => $body });
	#}
	
	# Check gateway errors
	unless ( ! defined( $json_obj->{ gateway } ) || &getValidFormat( 'IPv4_addr', $json_obj->{ gateway } ) )
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

	# setup parameters of vlan
	my $socket = IO::Socket::INET->new( Proto => 'udp' );
	#~ my @system_interfaces = $socket->if_list;

	$if_ref = {
				name    => $json_obj->{ name },
				dev     => $json_obj->{ parent },
				status  => "up",
				vlan    => $json_obj->{ tag },
				addr    => $json_obj->{ ip },
				mask    => $json_obj->{ netmask },
				gateway => $json_obj->{ gateway } // '',
				ip_v    => &ipversion( $json_obj->{ ip } ),
				mac     => $socket->if_hwaddr( $if_ref->{ dev } ),
	};

	# No errors
	eval {
		die if &createIf( $if_ref );
		die if &addIp( $if_ref );
		&writeRoutes( $if_ref->{name} );

		my $state = &upIf( $if_ref, 'writeconf' );

		if ( $state == 0 )
		{
			$if_ref->{status} = "up";
			&applyRoutes( "local", $if_ref );
		}

		&setInterfaceConfig( $if_ref ) or die;
	};

	if ( ! $@ )
	{
		# Success
		my $body = {
					 description => $description,
					 params      => {
								 name    => $if_ref->{ name },
								 ip      => $if_ref->{ addr },
								 netmask => $if_ref->{ mask },
								 gateway => $if_ref->{ gateway },
								 mac     => $if_ref->{ mac },
					 },
		};

		&httpResponse({ code => 201, body => $body });
	}
	else
	{
		# Error
		my $errormsg = "The $json_obj->{ name } vlan network interface can't be created";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

sub new_bond # ( $json_obj )
{
	my $json_obj = shift;

	my $description = "Add a bond interface";

	# validate BOND NAME
	my $bond_re = &getValidFormat( 'bond_interface' );

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

	$json_obj->{ mode } = &indexOfElementInArray( $json_obj->{ mode }, \@bond_modes_short );

	# validate SLAVES
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

# DELETE /deleteif/<interface>/<ip_version> Delete a interface
sub delete_interface # ( $if )
{
	my $if = shift;
	my $ip_v;

	my $error = "false";

	# If $if contain '/' means that we have received 2 parameters, interface_name and ip_version
	if ( $if =~ /\// )
	{
		# Get interface_name and ip_version from $if
		my @ifandipv = split ( '/', $if );
		$if = $ifandipv[0];
		$ip_v = $ifandipv[1];
		
		# If $ip_v is empty, establish IPv4 like default protocol
		$ip_v = 4 if not $ip_v;
		
		if ( $ip_v != 4 && $ip_v != 6 )
		{
			# Error
			my $errormsg = "The ip version value $ip_v must be 4 or 6";
			my $body = {
						 description => "Delete interface $if",
						 error       => "true",
						 message     => $errormsg,
			};

			&httpResponse({ code => 400, body => $body });
		}
	}
	
	# If ip_v is empty, default value is 4
	if ( !$ip_v ) { $ip_v = 4; }

	# Check input errors and delete interface
	if ( $if =~ /^$/ )
	{
		# Error
		my $errormsg = "Interface name $if can't be empty";
		my $body = {
					 description => "Delete interface $if",
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 400, body => $body });
	}
	
	my $if_ref = &getInterfaceConfig( $if, $ip_v );
	
	if ( !$if_ref )
	{
		# Error
		my $errormsg = "The stack IPv$ip_v in Network interface $if doesn't exist.";
		my $body = {
					 description => "Delete interface $if",
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 400, body => $body });
	}

	if ( $error eq "false" )
	{
		&delRoutes( "local", $if_ref );
		&downIf( $if_ref, 'writeconf' );
		&delIf( $if_ref );

		# Success
		my $message = "The stack IPv$ip_v in Network interface $if has been deleted.";
		my $body = {
					 description => "Delete interface $if",
					 success     => "true",
					 message     => $message,
		};

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		# Error
		my $errormsg = "The stack IPv$ip_v in Network interface $if can't be deleted";
		my $body = {
					 description => "Delete interface $if",
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 400, body => $body });
	}
}

sub delete_interface_nic # ( $nic )
{
	my $nic = shift;

	my $description = "Delete nic interface";
	my $ip_v = 4;
	my $if_ref = &getInterfaceConfig( $nic, $ip_v );

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

	eval {
		die if &delRoutes( "local", $if_ref );
		die if &downIf( $if_ref, 'writeconf' ); # FIXME: To be removed
		die if &delIf( $if_ref );
	};

	if ( ! $@ )
	{
		# Success
		my $message = "The configuration for the network interface $nic has been deleted.";
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
		my $errormsg = "The configuration for the network interface $nic can't be deleted.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 400, body => $body });
	}
}

sub delete_interface_vlan # ( $vlan )
{
	my $vlan = shift;

	my $description = "Delete VLAN interface";
	my $ip_v = 4;
	my $if_ref = &getInterfaceConfig( $vlan, $ip_v );

	# validate VLAN interface
	if ( !$if_ref )
	{
		# Error
		my $errormsg = "The VLAN interface $vlan doesn't exist.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 400, body => $body });
	}

	eval {
		die if &delRoutes( "local", $if_ref );
		die if &downIf( $if_ref, 'writeconf' );
		die if &delIf( $if_ref );
	};

	if ( ! $@ )
	{
		# Success
		my $message = "The VLAN interface $vlan has been deleted.";
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
		my $errormsg = "The VLAN interface $vlan can't be deleted";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 400, body => $body });
	}
}

sub delete_interface_virtual # ( $virtual )
{
	my $virtual = shift;

	my $description = "Delete virtual interface";
	my $ip_v = 4;
	my $if_ref = &getInterfaceConfig( $virtual, $ip_v );

	if ( !$if_ref )
	{
		# Error
		my $errormsg = "The virtual interface $virtual doesn't exist.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 400, body => $body });
	}

	eval {
		die if &delRoutes( "local", $if_ref );
		die if &downIf( $if_ref, 'writeconf' );
		die if &delIf( $if_ref );
	};

	if ( ! $@ )
	{
		# Success
		&runZClusterRemoteManager( 'interface', 'stop', $if_ref->{ name } );
		&runZClusterRemoteManager( 'interface', 'delete', $if_ref->{ name } );

		my $message = "The virtual interface $virtual has been deleted.";
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
		my $errormsg = "The virtual interface $virtual can't be deleted";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 400, body => $body });
	}
}

sub delete_interface_bond # ( $bond )
{
	my $bond = shift;

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

	&zenlog( Dumper $if_ref );

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

	my $bond_name = $bonds->{ $bond };
	my $bond_in_use = 0;
	$bond_in_use = 1 if &getInterfaceConfig( $bond_name, 4 );
	$bond_in_use = 1 if &getInterfaceConfig( $bond_name, 6 );
	$bond_in_use = 1 if grep ( /^$bond_name(:|\.)/, &getInterfaceList() );

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

	eval {
		if ( ${ &getSystemInterface( $bond ) }{ status } eq 'up' )
		{
			die if &downIf( $bond, 'writeconf' );
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

sub delete_interface_floating # ( $floating )
{
	my $floating = shift;

	my $description = "Remove floating interface";
	my $floatfile = &getGlobalConfiguration('floatfile');
	my $float_ifaces_conf = &getConfigTiny( $floatfile );

	# validate BOND
	unless ( $float_ifaces_conf->{_}->{ $floating } )
	{
		# Error
		my $errormsg = "Floating interface not found";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	eval {
		delete $float_ifaces_conf->{_}->{ $floating };

		&setConfigTiny( $floatfile, $float_ifaces_conf ) or die;

		# refresh l4xnat rules
		&reloadL4FarmsSNAT();
		#~ &runZClusterRemoteManager( 'interface', 'float-update' );
	};
	if ( ! $@ )
	{
		# Success
		my $message = "The floating interface has been removed.";
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
		my $errormsg = "The floating interface could not be removed";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 400, body => $body });
	}
}

# GET /interfaces Get params of the interfaces
sub get_interfaces # ()
{
	my @output_list;

	my $description = "List interfaces";

	# Configured interfaces list
	my @interfaces = @{ &getSystemInterfaceList() };
	
	# get cluster interface
	my $zcl_conf  = &getZClusterConfig();
	my $cluster_if = $zcl_conf->{ _ }->{ interface };

	# to include 'has_vlan' to nics
	my @vlans = &getInterfaceTypeList( 'vlan' );

	for my $if_ref ( @interfaces )
	{
		# Exclude IPv6
		next if $if_ref->{ ip_v } == 6 && &getGlobalConfiguration( 'ipv6_enabled' ) ne 'true';

		# Exclude cluster maintenance interface
		next if $if_ref->{ type } eq 'dummy';

		$if_ref->{ status } = &getInterfaceSystemStatus( $if_ref );

		# Any key must cotain a value or "" but can't be null
		if ( ! defined $if_ref->{ name } )    { $if_ref->{ name }    = ""; }
		if ( ! defined $if_ref->{ addr } )    { $if_ref->{ addr }    = ""; }
		if ( ! defined $if_ref->{ mask } )    { $if_ref->{ mask }    = ""; }
		if ( ! defined $if_ref->{ gateway } ) { $if_ref->{ gateway } = ""; }
		if ( ! defined $if_ref->{ status } )  { $if_ref->{ status }  = ""; }
		if ( ! defined $if_ref->{ mac } )     { $if_ref->{ mac }     = ""; }

		my $if_conf = {
			name    => $if_ref->{ name },
			ip      => $if_ref->{ addr },
			netmask => $if_ref->{ mask },
			gateway => $if_ref->{ gateway },
			status  => $if_ref->{ status },
			mac     => $if_ref->{ mac },
			type    => $if_ref->{ type },

			#~ ipv     => $if_ref->{ ip_v },
		};

		if ( $if_ref->{ type } eq 'nic' )
		{
			$if_conf->{ is_slave } =
			( grep { $$if_ref{ name } eq $_ } &getAllBondsSlaves ) ? 'true' : 'false';

			# include 'has_vlan'
			for my $vlan_ref ( @vlans )
			{
				if ( $vlan_ref->{ parent } eq $if_ref->{ name } )
				{
					$if_conf->{ has_vlan } = 'true';
					last;
				}
			}

			$if_conf->{ has_vlan } = 'false' unless $if_conf->{ has_vlan };
		}

		$if_conf->{ is_cluster } = 'true' if $cluster_if && $cluster_if eq $if_ref->{ name };
		  
		push @output_list, $if_conf;
	}

	my $body = {
			description => $description,
			interfaces  => \@output_list,
		};

	&httpResponse({ code => 200, body => $body });
}

# GET /interfaces Get params of the interfaces
sub get_nic_list # ()
{
	my @output_list;

	my $description = "List NIC interfaces";

	# get cluster interface
	my $zcl_conf  = &getZClusterConfig();
	my $cluster_if = $zcl_conf->{ _ }->{ interface };
	my @vlans = &getInterfaceTypeList( 'vlan' );

	for my $if_ref ( &getInterfaceTypeList( 'nic' ) )
	{
		$if_ref->{ status } = &getInterfaceSystemStatus( $if_ref );

		# Any key must cotain a value or "" but can't be null
		if ( ! defined $if_ref->{ name } )    { $if_ref->{ name }    = ""; }
		if ( ! defined $if_ref->{ addr } )    { $if_ref->{ addr }    = ""; }
		if ( ! defined $if_ref->{ mask } )    { $if_ref->{ mask }    = ""; }
		if ( ! defined $if_ref->{ gateway } ) { $if_ref->{ gateway } = ""; }
		if ( ! defined $if_ref->{ status } )  { $if_ref->{ status }  = ""; }
		if ( ! defined $if_ref->{ mac } )     { $if_ref->{ mac }     = ""; }

		my $if_conf = {
						name     => $if_ref->{ name },
						ip       => $if_ref->{ addr },
						netmask  => $if_ref->{ mask },
						gateway  => $if_ref->{ gateway },
						status   => $if_ref->{ status },
						mac      => $if_ref->{ mac },
						is_slave => $if_ref->{ is_slave },
		};

		$if_conf->{ is_cluster } = 'true' if $cluster_if eq $if_ref->{ name };

		# include 'has_vlan'
		for my $vlan_ref ( @vlans )
		{
			if ( $vlan_ref->{ parent } eq $if_ref->{ name } )
			{
				$if_conf->{ has_vlan } = 'true';
				last;
			}
		}

		$if_conf->{ has_vlan } = 'false' unless $if_conf->{ has_vlan };
		  
		push @output_list, $if_conf;
	}

	my $body = {
			description => $description,
			interfaces  => \@output_list,
		};

	&httpResponse({ code => 200, body => $body });
}

sub get_nic # ()
{
	my $nic = shift;

	my $description = "Show NIC interface";
	my $interface;

	for my $if_ref ( &getInterfaceTypeList( 'nic' ) )
	{
		next unless $if_ref->{ name } eq $nic;

		$if_ref->{ status } = &getInterfaceSystemStatus( $if_ref );

		# Any key must cotain a value or "" but can't be null
		if ( ! defined $if_ref->{ name } )    { $if_ref->{ name }    = ""; }
		if ( ! defined $if_ref->{ addr } )    { $if_ref->{ addr }    = ""; }
		if ( ! defined $if_ref->{ mask } )    { $if_ref->{ mask }    = ""; }
		if ( ! defined $if_ref->{ gateway } ) { $if_ref->{ gateway } = ""; }
		if ( ! defined $if_ref->{ status } )  { $if_ref->{ status }  = ""; }
		if ( ! defined $if_ref->{ mac } )     { $if_ref->{ mac }     = ""; }

		$interface = {
			name    => $if_ref->{ name },
			ip      => $if_ref->{ addr },
			netmask => $if_ref->{ mask },
			gateway => $if_ref->{ gateway },
			status  => $if_ref->{ status },
			mac     => $if_ref->{ mac },
			is_slave => $if_ref->{ is_slave },
		};
	}

	if ( $interface )
	{
		my $body = {
				description => $description,
				interface  => $interface,
			};

		&httpResponse({ code => 200, body => $body });
	}
	else
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
}

sub get_vlan_list # ()
{
	my @output_list;

	my $description = "List VLAN interfaces";

	# get cluster interface
	my $zcl_conf  = &getZClusterConfig();
	my $cluster_if = $zcl_conf->{ _ }->{ interface };
	
	for my $if_ref ( &getInterfaceTypeList( 'vlan' ) )
	{
		$if_ref->{ status } = &getInterfaceSystemStatus( $if_ref );

		# Any key must cotain a value or "" but can't be null
		if ( ! defined $if_ref->{ name } )    { $if_ref->{ name }    = ""; }
		if ( ! defined $if_ref->{ addr } )    { $if_ref->{ addr }    = ""; }
		if ( ! defined $if_ref->{ mask } )    { $if_ref->{ mask }    = ""; }
		if ( ! defined $if_ref->{ gateway } ) { $if_ref->{ gateway } = ""; }
		if ( ! defined $if_ref->{ status } )  { $if_ref->{ status }  = ""; }
		if ( ! defined $if_ref->{ mac } )     { $if_ref->{ mac }     = ""; }

		my $if_conf =
		  {
			name    => $if_ref->{ name },
			ip      => $if_ref->{ addr },
			netmask => $if_ref->{ mask },
			gateway => $if_ref->{ gateway },
			status  => $if_ref->{ status },
			mac     => $if_ref->{ mac },
			parent  => $if_ref->{ parent },
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

sub get_vlan # ()
{
	my $vlan = shift;

	my $interface;

	my $description = "Show VLAN interface";

	for my $if_ref ( &getInterfaceTypeList( 'vlan' ) )
	{
		next unless $if_ref->{ name } eq $vlan;

		$if_ref->{ status } = &getInterfaceSystemStatus( $if_ref );

		# Any key must cotain a value or "" but can't be null
		if ( ! defined $if_ref->{ name } )    { $if_ref->{ name }    = ""; }
		if ( ! defined $if_ref->{ addr } )    { $if_ref->{ addr }    = ""; }
		if ( ! defined $if_ref->{ mask } )    { $if_ref->{ mask }    = ""; }
		if ( ! defined $if_ref->{ gateway } ) { $if_ref->{ gateway } = ""; }
		if ( ! defined $if_ref->{ status } )  { $if_ref->{ status }  = ""; }
		if ( ! defined $if_ref->{ mac } )     { $if_ref->{ mac }     = ""; }

		$interface = {
					   name    => $if_ref->{ name },
					   ip      => $if_ref->{ addr },
					   netmask => $if_ref->{ mask },
					   gateway => $if_ref->{ gateway },
					   status  => $if_ref->{ status },
					   mac     => $if_ref->{ mac },
		};
	}

	if ( $interface )
	{
		my $body = {
					 description => $description,
					 interface   => $interface,
		};

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		# Error
		my $errormsg = "VLAN interface not found.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}
}

sub get_bond_list # ()
{
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

sub get_virtual_list # ()
{
	my @output_list;

	my $description = "List virtual interfaces";

	for my $if_ref ( &getInterfaceTypeList( 'virtual' ) )
	{
		$if_ref->{ status } = &getInterfaceSystemStatus( $if_ref );

		# Any key must cotain a value or "" but can't be null
		if ( ! defined $if_ref->{ name } )    { $if_ref->{ name }    = ""; }
		if ( ! defined $if_ref->{ addr } )    { $if_ref->{ addr }    = ""; }
		if ( ! defined $if_ref->{ mask } )    { $if_ref->{ mask }    = ""; }
		if ( ! defined $if_ref->{ gateway } ) { $if_ref->{ gateway } = ""; }
		if ( ! defined $if_ref->{ status } )  { $if_ref->{ status }  = ""; }
		if ( ! defined $if_ref->{ mac } )     { $if_ref->{ mac }     = ""; }

		push @output_list,
		  {
			name    => $if_ref->{ name },
			ip      => $if_ref->{ addr },
			netmask => $if_ref->{ mask },
			gateway => $if_ref->{ gateway },
			status  => $if_ref->{ status },
			mac     => $if_ref->{ mac },
			parent  => $if_ref->{ parent },
		  };
	}

	my $body = {
			description => $description,
			interfaces  => \@output_list,
		};

	&httpResponse({ code => 200, body => $body });
}

sub get_virtual # ()
{
	my $virtual = shift;

	my $interface; # output
	my $description = "Show virtual interface";

	for my $if_ref ( &getInterfaceTypeList( 'virtual' ) )
	{
		next unless $if_ref->{ name } eq $virtual;

		$if_ref->{ status } = &getInterfaceSystemStatus( $if_ref );

		# Any key must cotain a value or "" but can't be null
		if ( ! defined $if_ref->{ name } )    { $if_ref->{ name }    = ""; }
		if ( ! defined $if_ref->{ addr } )    { $if_ref->{ addr }    = ""; }
		if ( ! defined $if_ref->{ mask } )    { $if_ref->{ mask }    = ""; }
		if ( ! defined $if_ref->{ gateway } ) { $if_ref->{ gateway } = ""; }
		if ( ! defined $if_ref->{ status } )  { $if_ref->{ status }  = ""; }
		if ( ! defined $if_ref->{ mac } )     { $if_ref->{ mac }     = ""; }

		$interface = {
			name    => $if_ref->{ name },
			ip      => $if_ref->{ addr },
			netmask => $if_ref->{ mask },
			gateway => $if_ref->{ gateway },
			status  => $if_ref->{ status },
			mac     => $if_ref->{ mac },
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
		my $errormsg = "Virtual interface not found.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 404, body => $body } );
	}
}

sub actions_interface_nic # ( $json_obj, $nic )
{
	my $json_obj = shift;
	my $nic 	 = shift;

	my $description = "Action on nic interface";
	my $ip_v = 4;

	# validate NIC
	unless ( grep { $nic eq $_->{ name } } &getInterfaceTypeList( 'nic' ) )
	{
		# Error
		my $errormsg = "Nic interface not found";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	# reject not accepted parameters
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

	# validate action parameter
	if ( $json_obj->{ action } eq "up" )
	{
		my $if_ref = &getInterfaceConfig( $nic, $ip_v );

		# Delete routes in case that it is not a vini
		&delRoutes( "local", $if_ref ) if $if_ref;

		# Add IP
		&addIp( $if_ref ) if $if_ref;

		my $state = &upIf( { name => $nic }, 'writeconf' );

		if ( ! $state )
		{
			&applyRoutes( "local", $if_ref ) if $if_ref;

			# put all dependant interfaces up
			&setIfacesUp( $nic, "vlan" );
			&setIfacesUp( $nic, "vini" ) if $if_ref;
		}
		else
		{
			# Error
			my $errormsg = "The interface could not be set UP";
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
		my $state = &downIf( { name => $nic }, 'writeconf' );

		if ( $state )
		{
			# Error
			my $errormsg = "The interface could not be set DOWN";
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
		my $errormsg = "Action accepted values are: up or down";
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

sub actions_interface_vlan # ( $json_obj, $vlan )
{
	my $json_obj = shift;
	my $vlan     = shift;

	my $description = "Action on vlan interface";
	my $ip_v = 4;

	# validate VLAN
	unless ( grep { $vlan eq $_->{ name } } &getInterfaceTypeList( 'vlan' ) )
	{
		# Error
		my $errormsg = "VLAN interface not found";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	# reject not accepted parameters
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

	# validate action parameter
	if ( $json_obj->{action} eq "up" )
	{
		my $if_ref = &getInterfaceConfig( $vlan, $ip_v );

		# Create vlan if required if it doesn't exist
		my $exists = &ifexist( $if_ref->{ name } );
		if ( $exists eq "false" )
		{
			&createIf( $if_ref );
		}

		# Delete routes in case that it is not a vini
		&delRoutes( "local", $if_ref );

		# Add IP
		&addIp( $if_ref );

		# Check the parent's status before up the interface
		my $parent_if_name = &getParentInterfaceName( $if_ref->{ name } );
		my $parent_if_status = 'up';

		if ( $parent_if_name )
		{
			#~ &zenlog ("parent exists parent_if_name:$parent_if_name");
			my $parent_if_ref = &getSystemInterface( $parent_if_name );
			$parent_if_status = &getInterfaceSystemStatus( $parent_if_ref );
			#~ &zenlog ("parent exists parent_if_ref:$parent_if_ref parent_if_status:$parent_if_status");
		}

		# validate PARENT INTERFACE STATUS
		unless ( $parent_if_status eq 'up' )
		{
			# Error
			my $errormsg = "The interface $if_ref->{name} has a parent interface DOWN, check the interfaces status";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}

		my $state = &upIf( $if_ref, 'writeconf' );

		if ( ! $state )
		{
			&applyRoutes( "local", $if_ref );

			# put all dependant interfaces up
			&setIfacesUp( $if_ref->{ name }, "vini" );
		}
		else
		{
			# Error
			my $errormsg = "The interface could not be set UP";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}
	}
	elsif ( $json_obj->{action} eq "down" )
	{
		my $state = &downIf( { name => $vlan }, 'writeconf' );

		if ( $state )
		{
			# Error
			my $errormsg = "The interface could not be set DOWN";
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
		my $errormsg = "Action accepted values are: up or down";
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

sub actions_interface_bond # ( $json_obj, $bond )
{
	my $json_obj = shift;
	my $bond 	 = shift;

	my $description = "Action on bond interface";
	my $ip_v = 4;

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

	# validate action parameter
	if ( $json_obj->{ action } eq 'destroy' )
	{
		&delete_bond( $bond ); # doesn't return
	}
	elsif ( $json_obj->{ action } eq "up" )
	{
		my $if_ref = &getInterfaceConfig( $bond, $ip_v );

		# Delete routes in case that it is not a vini
		&delRoutes( "local", $if_ref ) if $if_ref;

		# Add IP
		&addIp( $if_ref ) if $if_ref;

		my $state = &upIf( { name => $bond }, 'writeconf' );

		if ( ! $state )
		{
			&applyRoutes( "local", $if_ref ) if $if_ref;

			# put all dependant interfaces up
			&setIfacesUp( $bond, "vlan" );
			&setIfacesUp( $bond, "vini" ) if $if_ref;
		}
		else
		{
			# Error
			my $errormsg = "The interface could not be set UP";
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
			my $errormsg = "The interface could not be set UP";
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

sub actions_interface_virtual # ( $json_obj, $virtual )
{
	my $json_obj = shift;
	my $virtual  = shift;

	my $description = "Action on virtual interface";
	my $ip_v = 4;

	# validate VLAN
	unless ( grep { $virtual eq $_->{ name } } &getInterfaceTypeList( 'virtual' ) )
	{
		# Error
		my $errormsg = "Virtual interface not found";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	# reject not accepted parameters
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

	my $if_ref = &getInterfaceConfig( $virtual, $ip_v );

	# Everything is ok
	if ( $json_obj->{ action } eq "up" )
	{
		# Add IP
		&addIp( $if_ref );

		# Check the parent's status before up the interface
		my $parent_if_name = &getParentInterfaceName( $if_ref->{name} );
		my $parent_if_status = 'up';
		if ( $parent_if_name )
		{
			#~ &zenlog ("parent exists parent_if_name:$parent_if_name");
			my $parent_if_ref = &getSystemInterface( $parent_if_name );
			$parent_if_status = &getInterfaceSystemStatus( $parent_if_ref );
			#~ &zenlog ("parent exists parent_if_ref:$parent_if_ref parent_if_status:$parent_if_status");
		}

		unless ( $parent_if_status eq 'up' )
		{
			# Error
			my $errormsg = "The interface $if_ref->{name} has a parent interface DOWN, check the interfaces status";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}

		my $state = &upIf( $if_ref, 'writeconf' );
		if ( ! $state )
		{
			&applyRoutes( "local", $if_ref );
		}
		else
		{
			# Error
			my $errormsg = "The interface could not be set UP";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}

		&runZClusterRemoteManager( 'interface', 'start', $if_ref->{ name } );
	}
	elsif ( $json_obj->{action} eq "down" )
	{
		my $state = &downIf( $if_ref, 'writeconf' );

		if ( $state )
		{
			# Error
			my $errormsg = "The interface could not be set DOWN";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}

		&runZClusterRemoteManager( 'interface', 'stop', $if_ref->{ name } );
	}
	else
	{
		# Error
		my $errormsg = "Action accepted values are: up or down";
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


sub modify_interface_nic # ( $json_obj, $nic )
{
	my $json_obj = shift;
	my $nic = shift;

	my $description = "Configure nic interface";
	my $ip_v = 4;

	# validate NIC NAME
	my $socket = IO::Socket::INET->new( Proto => 'udp' );
	my @system_interfaces = $socket->if_list;
	my $type = &getInterfaceType( $nic );

	unless ( grep( { $nic eq $_ } @system_interfaces ) && $type eq 'nic' )
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
	my $if_ref = &getInterfaceConfig( $nic, $ip_v );

	if ( $if_ref )
	{
		# Delete old IP and Netmask from system to replace it
		&delIp( $if_ref->{name}, $if_ref->{addr}, $if_ref->{mask} );

		# Remove routes if the interface has its own route table: nic and vlan
		&delRoutes( "local", $if_ref );

		$if_ref = undef;
	}

	# Setup new interface configuration structure
	$if_ref              = &getInterfaceConfig( $nic ) // &getSystemInterface( $nic );
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

	eval {
		# Add new IP, netmask and gateway
		#~ die if &addIp( $if_ref );

		# sometimes there are expected erros pending to be controlled
		&addIp( $if_ref );

		# Writing new parameters in configuration file
		&writeRoutes( $if_ref->{ name } );

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
		my $errormsg = "Errors found trying to modify interface $nic";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

sub modify_interface_vlan # ( $json_obj, $vlan )
{
	my $json_obj = shift;
	my $vlan = shift;

	my $description = "Modify VLAN interface";
	my $ip_v = 4;
	my $if_ref = &getInterfaceConfig( $vlan, $ip_v );

	# Check interface errors
	unless ( $if_ref )
	{
		# Error
		my $errormsg = "VLAN not found";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 404, body => $body });
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
		unless ( defined( $json_obj->{ ip } ) && &getValidFormat( 'IPv4_addr', $json_obj->{ ip } ) )
		{
			# Error
			my $errormsg = "IP Address $json_obj->{ip} structure is not ok.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
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

	## Check netmask errors for IPv6
	#if ( $ip_v == 6 && ( $json_obj->{netmask} !~ /^\d+$/ || $json_obj->{netmask} > 128 || $json_obj->{netmask} < 0 ) )
	#{
	#	# Error
	#	my $errormsg = "Netmask Address $json_obj->{netmask} structure is not ok. Must be numeric.";
	#	my $body = {
	#				 description => $description,
	#				 error       => "true",
	#				 message     => $errormsg
	#	};
    #
	#	&httpResponse({ code => 400, body => $body });
	#}

	# Check gateway errors
	if ( exists $json_obj->{ gateway } )
	{
		unless ( exists( $json_obj->{ gateway } ) || &getValidFormat( 'IPv4_addr', $json_obj->{ gateway } ) )
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

	# Delete old parameters
	if ( $if_ref )
	{
		# Delete old IP and Netmask from system to replace it
		&delIp( $$if_ref{name}, $$if_ref{addr}, $$if_ref{mask} );

		# Remove routes if the interface has its own route table: nic and vlan
		&delRoutes( "local", $if_ref );
	}

	$if_ref->{ addr }    = $json_obj->{ ip }      if exists $json_obj->{ ip };
	$if_ref->{ mask }    = $json_obj->{ netmask } if exists $json_obj->{ netmask };
	$if_ref->{ gateway } = $json_obj->{ gateway } if exists $json_obj->{ gateway };

	eval {
		# Add new IP, netmask and gateway
		die if &addIp( $if_ref );
		die if &writeRoutes( $if_ref->{name} );

		my $state = &upIf( $if_ref, 'writeconf' );

		if ( $state == 0 )
		{
			$if_ref->{status} = "up";
			die if &applyRoutes( "local", $if_ref );
		}

		&setInterfaceConfig( $if_ref ) or die;
	};

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
		my $errormsg = "Errors found trying to modify interface $vlan";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

sub modify_interface_virtual # ( $json_obj, $virtual )
{
	my $json_obj = shift;
	my $virtual = shift;

	my $description = "Modify virtual interface",
	my $ip_v = 4;
	my $if_ref = &getInterfaceConfig( $virtual, $ip_v );
	
	my $errormsg;
	my @allowParams = ( "ip" );

	unless ( $if_ref )
	{
		# Error
		$errormsg = "Virtual interface not found";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 404, body => $body });
	}

	if( $errormsg = &getValidOptParams( $json_obj, \@allowParams ) )
	{
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}


	# Check address errors
	unless ( defined( $json_obj->{ ip } ) && &getValidFormat( 'IPv4_addr', $json_obj->{ ip } ) )
	{
		# Error
		$errormsg = "IP Address $json_obj->{ip} structure is not ok.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	
	my $state = $if_ref->{ 'status' };
	&downIf( $if_ref ) if $state eq 'up';
	
	# No errors found
	eval {
		&runZClusterRemoteManager( 'interface', 'stop', $if_ref->{ name } );

		# Delete old IP and Netmask from system to replace it
		#~ die if &delIp( $$if_ref{name}, $$if_ref{addr}, $$if_ref{mask} ) ;

		# Set the new params
		$if_ref->{addr} = $json_obj->{ip};

		# Add new IP, netmask and gateway
		die if &addIp( $if_ref );

		if ( $state eq 'up' )
		{
			&upIf( $if_ref ) ;
			&applyRoutes( "local", $if_ref );
		}

		&setInterfaceConfig( $if_ref ) or die;
	};

	# Print params
	if ( ! $@ )
	{
		# Success
		&runZClusterRemoteManager( 'interface', 'start', $if_ref->{ name } );

		my $body = {
					 description => $description,
					 params      => $json_obj,
		};

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		# Error
		$errormsg = "Errors found trying to modify interface $virtual";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

sub modify_interface_bond # ( $json_obj, $bond )
{
	my $json_obj = shift;
	my $bond = shift;

	my $description = "Modify bond address";
	my $ip_v = 4;

	# validate BOND NAME
	my $socket = IO::Socket::INET->new( Proto => 'udp' );
	my @system_interfaces = $socket->if_list;
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

# address or interface
sub modify_interface_floating # ( $json_obj, $floating )
{
	my $json_obj = shift;
	my $interface = shift;

	my $description = "Modify floating interface";

	#~ &zenlog("modify_interface_floating interface:$interface json_obj:".Dumper $json_obj );

	if ( grep { $_ ne 'floating_ip' } keys %{$json_obj} )
	{
		# Error
		my $errormsg = "Parameter not recognized";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	unless ( keys %{ $json_obj } )
	{
		# Error
		my $errormsg = "Need to use floating_ip parameter";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	my $ip_v = 4;
	my $if_ref = &getInterfaceConfig( $interface, $ip_v );

	unless ( $if_ref )
	{
		# Error
		my $errormsg = "Floating interface not found";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	$if_ref = undef;

	if ( exists $json_obj->{ floating_ip } )
	{
		# validate ADDRESS format
		unless ( $json_obj->{ floating_ip } && &getValidFormat( 'IPv4_addr', $json_obj->{ floating_ip } ) )
		{
			# Error
			my $errormsg = "Invalid floating address format";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}

		my @interfaces = &getInterfaceTypeList( 'virtual' );
		( $if_ref ) = grep { $json_obj->{ floating_ip } eq $_->{ addr } && $_->{ parent } eq $interface } @interfaces;

		# validate ADDRESS in system
		unless ( $if_ref )
		{
			# Error
			my $errormsg = "Virtual interface with such address not found";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 404, body => $body });
		}
	}

	eval {
		my $floatfile = &getGlobalConfiguration('floatfile');
		my $float_ifaces_conf = &getConfigTiny( $floatfile );

		$float_ifaces_conf->{ _ }->{ $interface } = $if_ref->{ name };

		&setConfigTiny( $floatfile, $float_ifaces_conf ) or die;

		# refresh l4xnat rules
		&reloadL4FarmsSNAT();
		#~ &runZClusterRemoteManager( 'interface', 'float-update' );
	};

	unless ( $@ )
	{
		# Error
		my $message = "Floating interface modification done";
		my $body = {
					 description => $description,
					 success       => "true",
					 message     => $message
		};

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		# Error
		my $errormsg = "Floating interface modification failed";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

sub get_gateway
{
	my $description = "Default gateway";

	my $body = {
		description => $description,
		params      => {
			address   => &getDefaultGW(),
			interface => &getIfDefaultGW(),

		},
	};

	&httpResponse({ code => 200, body => $body });
}

sub get_interfaces_floating
{
	my $description = "List floating interfaces";

	# Interfaces
	my @output;
	my @ifaces = @{ &getSystemInterfaceList() };
	my $floatfile = &getGlobalConfiguration('floatfile');
	my $float_ifaces_conf = &getConfigTiny( $floatfile );

	for my $iface ( @ifaces )
	{
		#~ &zenlog( "getActiveInterfaceList: $iface->{ name }" );
		next unless $iface->{ ip_v } == 4;
		next if $iface->{ type } eq 'virtual';
		next unless $iface->{ addr };

		my $floating_ip = undef;

		if ( $float_ifaces_conf->{_}->{ $iface->{ name } } )
		{
			my $floating_interface = $float_ifaces_conf->{_}->{ $iface->{ name } };
			my $if_ref = &getInterfaceConfig( $floating_interface );
			$floating_ip = $if_ref->{ addr };
		}

		push @output,
		  {
			interface   => $iface->{ name },
			floating_ip => $floating_ip,
		  };

		#~ $output{ $iface->{name} } = $iface->{name} unless $output{ $iface->{name} };
	}

	my $body = {
				 description => $description,
				 params      => \@output,
	};

	&httpResponse({ code => 200, body => $body });
}

sub get_floating
{
	my $floating = shift;

	my $description = "Show floating interface";

	# Interfaces
	my $output;
	my @ifaces = @{ &getSystemInterfaceList() };
	my $floatfile = &getGlobalConfiguration('floatfile');
	my $float_ifaces_conf = &getConfigTiny( $floatfile );

	for my $iface ( @ifaces )
	{
		#~ &zenlog( "getActiveInterfaceList: $iface->{ name }" );
		next unless $iface->{ ip_v } == 4;
		next if $iface->{ type } eq 'virtual';
		next unless $iface->{ name } eq $floating;

		my $floating_ip = undef;

		unless ( $iface->{ addr } )
		{
			# Error
			my $errormsg = "This interface has no address configured";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg,
			};

			&httpResponse({ code => 400, body => $body });
		}

		$floating_ip = undef;

		if ( $float_ifaces_conf->{_}->{ $iface->{ name } } )
		{
			my $floating_interface = $float_ifaces_conf->{_}->{ $iface->{ name } };
			my $if_ref = &getInterfaceConfig( $floating_interface );
			$floating_ip = $if_ref->{ addr };
		}

		$output = {
					interface   => $iface->{ name },
					floating_ip => $floating_ip,
		};

		#~ $output{ $iface->{name} } = $iface->{name} unless $output{ $iface->{name} };
	}

	my $body = {
				 description => $description,
				 params      => $output,
	};

	&httpResponse({ code => 200, body => $body });
}

sub modify_gateway # ( $json_obj )
{
	my $json_obj = shift;

	my $description = "Modify default gateway";

	my $default_gw = &getDefaultGW();

	# verify ONLY ACCEPTED parameters received
	if ( grep { $_ !~ /^(?:address|interface)$/ } keys %$json_obj )
	{
		# Error
		my $errormsg = "Parameter received not recognized";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 400, body => $body });
	}

	# if default gateway is not configured requires address and interface
	if ( $default_gw )
	{
		# verify AT LEAST ONE parameter received
		unless ( exists $json_obj->{ address } || exists $json_obj->{ interface } )
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
	}
	else
	{
		unless ( exists $json_obj->{ address } && exists $json_obj->{ interface } )
		{
			# Error
			my $errormsg = "Gateway requires address and interface to be configured";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg,
			};

			&httpResponse({ code => 400, body => $body });
		}
	}

	# validate ADDRESS
	if ( exists $json_obj->{ address } )
	{
		unless ( defined( $json_obj->{ address } ) && &getValidFormat( 'IPv4_addr', $json_obj->{ address } ) )
		{
			# Error
			my $errormsg = "Gateway address is not valid.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}
	}

	# validate INTERFACE
	if ( exists $json_obj->{ interface } )
	{
		my $socket = IO::Socket::INET->new( Proto => 'udp' );
		my @system_interfaces = $socket->if_list;
		#~ my $type = &getInterfaceType( $nic );

		unless ( grep( { $json_obj->{ interface } eq $_ } @system_interfaces ) )
		{
			# Error
			my $errormsg = "Gateway interface not found.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 404, body => $body });
		}
	}

	my $ip_version = 4;
	my $interface = $json_obj->{ interface } // &getIfDefaultGW();
	my $address = $json_obj->{ address } // $default_gw;

	my $if_ref = getInterfaceConfig( $interface, $ip_version );

	&zenlog("applyRoutes interface:$interface address:$address if_ref:$if_ref");
	my $state = &applyRoutes( "global", $if_ref, $address );

	if ( $state == 0 )
	{
		#~ &runZClusterRemoteManager( 'gateway', 'update', $json_obj->{ interface }, ip_version );

		# Success
		my $message = "The default gateway has been changed successfully";
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
		my $errormsg = "The default gateway hasn't been changed";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 404, body => $body });
	}
}

sub delete_gateway
{
	my $description = "Remove default gateway";

	my $ip_version = 4;
	my $defaultgwif = &getIfDefaultGW();

	my $if_ref = &getInterfaceConfig( $defaultgwif, $ip_version );

	my $state = &delRoutes( "global", $if_ref );

	if ( $state == 0 )
	{
		#~ &runZClusterRemoteManager( 'gateway', 'delete', $if, $ip_version );
		my $message = "The default gateway has been deleted successfully";

		my $body = {
			description => $description,
			message => $message,
			params      => {
				address   => &getDefaultGW(),
				interface => &getIfDefaultGW(),

			},
		};

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		my $errormsg = "The default gateway hasn't been deleted";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

1;
