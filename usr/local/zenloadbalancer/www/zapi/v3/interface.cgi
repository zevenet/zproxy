#!/usr/bin/perl -w

my @bond_modes_short = (
				'balance-rr',
				'active-backup',
				'balance-xor',
				'broadcast',
				'802.3ad',
				'balance-tlb',
				'balance-alb',
);

# POST Virtual Network Interface
#
# curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -d '{"name":"new2","ip":"1.1.1.3","netmask":"255.255.192.0"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/addvini/eth0
#
#####Documentation of POST VINI####
#**
#  @api {post} /addvini/<interface> Create a new virtual network interface
#  @apiGroup Interfaces
#  @apiName PostVini
#  @apiParam {String} interface  Interface name, unique ID.
#  @apiDescription Create a new virtual network interface of a given interface
#  @apiVersion 3.0.0
#
#
#
# @apiSuccess   {String}    name    The name of the virtual network interface.
# @apiSuccess	{String}	ip		IP of the virtual network interface.
#
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "New virtual network interface eth0:new2",
#   "params" : [
#      {
#         "HWaddr" : "04:01:41:01:86:01",
#         "gateway" : "",
#         "ip" : "192.168.0.150",
#         "name" : "eth0:new",
#         "netmask" : "255.255.192.0"
#      }
#   ]
#}
#
# @apiExample {curl} Example Usage:
#	curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#	 -d '{"name":"new","ip":"192.168.0.150"}'
#	https://<zenlb_server>:444/zapi/v3/zapi.cgi/addvini/eth0
#
# @apiSampleRequest off
#
#**

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
			$if_ref{ status } = "up";
			&applyRoutes( "local", $if_ref );
		}

		&setInterfaceConfig( $if_ref ) or die;
	};

	if ( !$@ )
	{
		# Success
		my $body = {
					 description => $description,
					 params      => {
								 name    => $if_ref->{ name },
								 ip      => $if_ref->{ addr },
								 netmask => $if_ref->{ mask },
								 gateway => $if_ref->{ gateway },
								 HWaddr  => $if_ref->{ mac },
					 },
		};

		&httpResponse( { code => 201, body => $body } );
	}
	else
	{
		# Error
		my $errormsg = "The $json_obj->{ name } virtual network interface can't be created";
		my $output = {
					   description => $description,
					   error       => "true",
					   message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

# POST Vlan Network Interface
#
# curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -d '{"name":"3","ip":"1.1.1.3","netmask":"255.255.192.0"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/addvlan/eth0
#
#####Documentation of POST VLAN####
#**
#  @api {post} /addvlan/<interface> Create a new vlan network interface
#  @apiGroup Interfaces
#  @apiName PostVlan
#  @apiParam {String} interface  Interface name, unique ID.
#  @apiDescription Create a new vlan network interface of a given interface
#  @apiVersion 3.0.0
#
#
#
# @apiSuccess   {String}        name                     The name of the vlan network interface.
# @apiSuccess   {String}        ip                       IP of the vlan network interface.
# @apiSuccess   {String}        netmask                  Netmask of the vlan network interface.
# @apiSuccess   {String}        gateway                  Gateway of the vlan network interface.
#
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "New vlan network interface eth0.3",
#   "params" : [
#      {
#         "HWaddr" : "04:01:41:01:86:01",
#         "gateway" : "192.168.1.0",
#         "ip" : "192.168.1.150",
#         "name" : "eth0.3",
#         "netmask" : "255.255.255.0"
#      }
#   ]
#}
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        -d '{"name":"new","ip":"192.168.1.150","netmask":"255.255.255.0",
#       "gateway":"192.168.1.0"}' https://<zenlb_server>:444/zapi/v3/zapi.cgi/addvlan/eth0
#
# @apiSampleRequest off
#
#**

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
				ip_v    => $json_obj->{ ip_v },
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
								 HWaddr  => $if_ref->{ mac },
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
	my $nic_re = &getValidFormat( 'nic_interface' );

	unless ( $json_obj->{ name } =~ /^$nic_re$/ && &ifexist($json_obj->{ name }) eq 'false' )
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
		my $body = {
					 description => $description,
					 params      => {
								 name   => $json_obj->{ name },
								 mode   => $bond_modes_short[$json_obj->{ mode }],
								 slaves => $json_obj->{ slaves },
								 status => $if_ref->{ status },
								 HWaddr => $if_ref->{ mac },
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
		$json_obj->{ slave } or die;
		&getValidFormat( 'nic_interface', $json_obj->{ slave } ) or die;
		grep ( { $json_obj->{ slave } eq $_ } &getBondAvailableSlaves() ) or die;
		die if grep ( { $json_obj->{ slave } eq $_ } @{ $bonds->{ $bond }->{ slaves } } );
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

	push @{ $bonds->{ $bond }->{ slaves } }, $json_obj->{slave};

	eval {
		die if &applyBondChange( $bonds->{ $bond }, 'writeconf' );
	};
	if ( ! $@ )
	{
		my $if_ref = getSystemInterface( $bond );

		# Success
		my $body = {
					 description => $description,
					 params      => {
								 name   => $bond,
								 mode   => $bond_modes_short[$bonds->{ $bond }->{ mode }],
								 slaves => $bonds->{ $bond }->{ slaves },
								 status => $if_ref->{ status },
								 HWaddr => $if_ref->{ mac },
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

# DELETE Virtual Network Interface
#
# curl --tlsv1 -k -X DELETE -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" https://178.62.126.152:445/zapi/v1/zapi.cgi/deleteif/eth0:new
#
#
#####Documentation of DELETE INTERFACE####
#**
#  @api {delete} /deleteif/<interface>/<ip_version> Delete a interface
#  @apiGroup Interfaces
#  @apiName DeleteIf
#  @apiParam 	{String}	 interface	Interface name, unique ID.
#  @apiParam 	{Number}	 ip_version	Stack to delete. Must be 6 for IPv6 and 4 for IPv4. In case that command ends with only the interface name, the ip version default value is IPv4.
#  @apiDescription Delete a interface, a virtual network interface or a vlan
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Delete interface eth0:new",
#   "message" : "The interface eth0:new has been deleted.",
#   "success" : "true"
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X DELETE -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        https://<zenlb_server>:444/zapi/v3/zapi.cgi/deleteif/eth0:test/6
#
# @apiSampleRequest off
#
#**

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

	&zenlog( Dumper $if_ref );

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
		my $errormsg = "The configuration for the network interface $nic can't be deleted: $@";
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
		my $message = "The bonding interface $virtual has been deleted.";
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
		my $errormsg = "The bonding interface $virtual could not be deleted";
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
		my $errormsg = "The bonding slave interface $virtual could not be removed";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 400, body => $body });
	}
}

# GET Interface
#
# curl --tlsv1 -k -X GET -H 'Content- Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" https://178.62.126.152:445/zapi/v1/zapi.cgi/interfaces
#
#####Documentation of GET INTERFACES####
#**
#  @api {get} /interfaces Get params of the interfaces
#  @apiGroup Interfaces
#  @apiName GetInterfaces
#  @apiDescription Gat all the params of the interfaces
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "List interfaces",
#   "interfaces" : [
#      {
#         "HDWaddr" : "0e:1f:c6:69:a1:97",
#         "gateway" : "192.168.101.5",
#         "ip" : "192.168.101.120",
#         "name" : "eth0",
#         "netmask" : "255.255.255.0",
#         "status" : "up"
#      },
#      {
#         "HDWaddr" : "0e:1f:c6:69:a1:97",
#         "gateway" : "",
#         "ip" : "192.168.101.122",
#         "name" : "eth0:cluster",
#         "netmask" : "255.255.255.0",
#         "status" : "up"
#      },
#      {
#         "HDWaddr" : "ee:7f:26:4c:e2:b0",
#         "gateway" : "192.168.100.5",
#         "ip" : "192.168.100.15",
#         "name" : "eth1",
#         "netmask" : "255.255.255.0",
#         "status" : "up"
#      },
#      {
#         "HDWaddr" : "ee:7f:26:4c:e2:b0",
#         "gateway" : "",
#         "ip" : "fe80:99::180",
#         "name" : "eth1",
#         "netmask" : "64",
#         "status" : "up"
#      },
#      {
#         "HDWaddr" : "0a:d0:2b:ae:61:62",
#         "gateway" : "",
#         "ip" : "192.168.101.16",
#         "name" : "eth2",
#         "netmask" : "255.255.255.0",
#         "status" : "up"
#      },
#      {
#         "HDWaddr" : "0a:d0:2b:ae:61:62",
#         "gateway" : "",
#         "ip" : "fe80::120",
#         "name" : "eth2",
#         "netmask" : "64",
#         "status" : "up"
#      },
#      {
#         "HDWaddr" : "0a:d0:2b:ae:61:62",
#         "gateway" : "192.168.12.5",
#         "ip" : "192.168.12.25",
#         "name" : "eth2.12",
#         "netmask" : "255.255.255.0",
#         "status" : "up"
#      }
#   ]
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        https://<zenlb_server>:444/zapi/v3/zapi.cgi/interfaces
#
# @apiSampleRequest off
#
#**

sub get_interfaces # ()
{
	my @output_list;

	my $description = "List interfaces";

	# Configured interfaces list
	my @interfaces = @{ &getSystemInterfaceList() };

	for my $if_ref ( @interfaces )
	{
		# Exclude IPv6
		next if $if_ref->{ ip_v } == 6 && &getGlobalConfiguration( 'ipv6_enabled' ) ne 'true';

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
			HDWaddr => $if_ref->{ mac },
			#~ ipv     => $if_ref->{ ip_v },
		  };
	}

	my $body = {
			description => $description,
			interfaces  => \@output_list,
		};

	&httpResponse({ code => 200, body => $body });
}

# GET Interface NIC
#
# curl --tlsv1 -k -X GET -H 'Content- Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" https://178.62.126.152:445/zapi/v1/zapi.cgi/interfaces
#
#####Documentation of GET INTERFACES####
#**
#  @api {get} /interfaces Get params of the interfaces
#  @apiGroup Interfaces
#  @apiName GetInterfaces
#  @apiDescription Gat all the params of the interfaces
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "List interfaces",
#   "interfaces" : [
#      {
#         "HDWaddr" : "0e:1f:c6:69:a1:97",
#         "gateway" : "192.168.101.5",
#         "ip" : "192.168.101.120",
#         "name" : "eth0",
#         "netmask" : "255.255.255.0",
#         "status" : "up"
#      },
#      {
#         "HDWaddr" : "0e:1f:c6:69:a1:97",
#         "gateway" : "",
#         "ip" : "192.168.101.122",
#         "name" : "eth0:cluster",
#         "netmask" : "255.255.255.0",
#         "status" : "up"
#      },
#      {
#         "HDWaddr" : "ee:7f:26:4c:e2:b0",
#         "gateway" : "192.168.100.5",
#         "ip" : "192.168.100.15",
#         "name" : "eth1",
#         "netmask" : "255.255.255.0",
#         "status" : "up"
#      },
#      {
#         "HDWaddr" : "ee:7f:26:4c:e2:b0",
#         "gateway" : "",
#         "ip" : "fe80:99::180",
#         "name" : "eth1",
#         "netmask" : "64",
#         "status" : "up"
#      },
#      {
#         "HDWaddr" : "0a:d0:2b:ae:61:62",
#         "gateway" : "",
#         "ip" : "192.168.101.16",
#         "name" : "eth2",
#         "netmask" : "255.255.255.0",
#         "status" : "up"
#      },
#      {
#         "HDWaddr" : "0a:d0:2b:ae:61:62",
#         "gateway" : "",
#         "ip" : "fe80::120",
#         "name" : "eth2",
#         "netmask" : "64",
#         "status" : "up"
#      },
#      {
#         "HDWaddr" : "0a:d0:2b:ae:61:62",
#         "gateway" : "192.168.12.5",
#         "ip" : "192.168.12.25",
#         "name" : "eth2.12",
#         "netmask" : "255.255.255.0",
#         "status" : "up"
#      }
#   ]
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        https://<zenlb_server>:444/zapi/v3/zapi.cgi/interfaces
#
# @apiSampleRequest off
#
#**

sub get_interfaces_nic # ()
{
	my @output_list;

	my $description = "List NIC interfaces";

	for my $if_ref ( &getInterfaceTypeList( 'nic' ) )
	{
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
			HDWaddr => $if_ref->{ mac },
			#~ ipv     => $if_ref->{ ip_v },
		  };
	}

	my $body = {
			description => $description,
			interfaces  => \@output_list,
		};

	&httpResponse({ code => 200, body => $body });
}

sub get_interfaces_vlan # ()
{
	my @output_list;

	my $description = "List VLAN interfaces";

	for my $if_ref ( &getInterfaceTypeList( 'vlan' ) )
	{
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
			HDWaddr => $if_ref->{ mac },
			#~ ipv     => $if_ref->{ ip_v },
		  };
	}

	my $body = {
			description => $description,
			interfaces  => \@output_list,
		};

	&httpResponse({ code => 200, body => $body });
}

sub get_interfaces_bond # ()
{
	my @output_list;

	my $description = "List bonding interfaces";
	my $bond_conf = &getBondConfig();

	for my $if_ref ( &getInterfaceTypeList( 'bond' ) )
	{
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
			HDWaddr => $if_ref->{ mac },

			slaves => $bond_conf->{ $if_ref->{ name } }->{ slaves },
			mode => $bond_modes_short[$bond_conf->{ $if_ref->{ name } }->{ mode }],
			#~ ipv     => $if_ref->{ ip_v },
		  };
	}

	my $body = {
			description => $description,
			interfaces  => \@output_list,
		};

	&httpResponse({ code => 200, body => $body });
}

sub get_interfaces_virtual # ()
{
	my @output_list;

	my $description = "List virtual interfaces";

	for my $if_ref ( &getInterfaceTypeList( 'virtual' ) )
	{
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
			HDWaddr => $if_ref->{ mac },
			#~ ipv     => $if_ref->{ ip_v },
		  };
	}

	my $body = {
			description => $description,
			interfaces  => \@output_list,
		};

	&httpResponse({ code => 200, body => $body });
}

# POST Interface actions
#
# curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -d '{"action":"down"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/ifaction/eth0
#
#####Documentation of POST INTERFACE ACTION####
#**
#  @api {post} /ifaction/<interface> Set an action in a interface
#  @apiGroup Interfaces
#  @apiName Postifaction
#  @apiParam {String} interface  Interface name, unique ID.
#  @apiDescription Set an action in a interface, virtual network interface or vlan
#  @apiVersion 3.0.0
#
#
#
# @apiSuccess   {String}        action                   The action that will be set in the interface. Could it be up or down.
#
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Action in interface eth0:new",
#   "params" : [
#      {
#         "action" : "down"
#      }
#   ]
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        -d '{"action":"down"}'
#       https://<zenlb_server>:444/zapi/v3/zapi.cgi/ifaction/eth0:new
#
# @apiSampleRequest off
#
#**

sub ifaction # ( $fdev )
{
	my $fdev  = shift;

	my $error = "false";

	# Check interface errors
	if ( $fdev =~ /^$/ )
	{
		# Error
		my $errormsg = "Interface name can't be empty";
		my $body = {
					 description => "Interface $fdev",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	if ( $fdev =~ /\s+/ )
	{
		# Error
		my $errormsg = "Interface name is not valid";
		my $body = {
					 description => "Interface $fdev",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	# Check input errors
	if ( $json_obj->{ action } !~ /^(up|down)$/ )
	{
		# Error
		my $errormsg = "Action value must be up or down";
		my $body = {
					 description => "Action value $json_obj->{action}",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	my $if_ref;
	my @stacks;
	for my $ip_v (4, 6)
	{
		$if_ref = &getInterfaceConfig( $fdev, $ip_v );
		
		if ($$if_ref{addr})
		{
			push @stacks, $if_ref;
		}
	}

	# Check the interface exists
	if ( !@stacks && $fdev =~ /:|\./ )
	{
		# Error
		my $errormsg = "The Network interface $fdev doesn't exist.";
		my $body = {
					 description => "Action value $json_obj->{action}",
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 400, body => $body });
	}

	# Everything is ok
	if ( $json_obj->{action} eq "up" )
	{
		# Create a hash with interface name
		my %interface;
		$interface{ name }    = $fdev;
		
		# Create vlan if required if it doesn't exist
		my $exists = &ifexist( $if_ref->{name} );
		if ( $exists eq "false" )
		{
			#Get parameters 					
			$interface{ ip_v }    = $ip_v;		
			my %if = %{ &getDevVlanVini( $interface{ name } ) };
			$interface{ dev }  	  = $if{ dev };
			$interface{ vlan }    = $if{ vlan };
			$interface{ vini }    = $if{ vini };
					
			$status = &createIf( \%interface );
		}
	
		# Delete routes in case that it is not a vini
		if ( $interface{vini} eq '' )
		{
			for my $iface (@stacks)
			{
				&delRoutes( "local", $iface );
			}
		}
		
		# Check if there are some Virtual Interfaces or Vlan with IPv6 and previous UP status to get it up.
		&setIfacesUp( $interface{name}, "vlan" );
		&setIfacesUp( $interface{name}, "vini" );
		
		# Add IP
		for my $iface (@stacks)
		{
			&addIp( $iface );
		}
		
		# Check the parent's status before up the interface
		my $parent_if_name = &getParentInterfaceName( $if_ref->{name} );
		if ( !$parent_if_name )
		{
			# &zenlog ("parent doesn't exist for $fdev");
			$parent_if_status = 'up';
		}
		else
		{
			# &zenlog ("parent exists");
			my $parent_if_ref = &getInterfaceConfig( $parent_if_name, $ip_v );
			$parent_if_status = &getInterfaceSystemStatus( $parent_if_ref, $ip_v );
		}
		
		if ( $parent_if_status eq 'up' )
		{	
			# &zenlog ("GO UP!");
			my $state = &upIf( \%interface, 'writeconf' );
			if ( $state != 0 )
			{
				$error = "true";
			}
			for my $iface (@stacks)
			{
				&applyRoutes( "local", $iface );
			}
		}
		else
		{
			# Error
			my $errormsg = "The interface $if_ref->{name} has a parent interface DOWN, check the interfaces status";
			my $body = {
						 description => "Action value $json_obj->{action}",
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}		
	} 
	elsif ( $json_obj->{action} eq "down" )
	{
		if ( $stacks[0] )
		{
			$if_ref = $stacks[0];
		}
		else # for unconfigured NICs, downIf requires only the interface name
		{
			$if_ref = { name => $fdev };
		}
		
		my $state = &downIf( $if_ref, 'writeconf' );
		
		if ( $state != 0 )
		{
			$error = "true";
		}
	}
	else
	{
		$error = "true";
	}

	if ( $error eq "false" )
	{
		# Success
		my $body = {
					 description => "Action in interface $fdev",
					 params      =>  { action => $json_obj->{ action } },
		};

		&httpResponse({ code => 201, body => $body });
	}
	else
	{
		# Error
		my $errormsg = "The action $json_obj->{action} is not set in interface $fdev";
		my $body = {
					 description => "Action in interface $fdev",
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 400, body => $body });
	}
}

# PUT Interface
#
# curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -d '{"gateway":"1.1.1.0","ip":"1.1.1.3","netmask":"255.255.192.0"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/modifyif/eth0:n1
#
#####Documentation of PUT INTERFACE####
#**
#  @api {put} /modifyif/<interface>/<ip_version> Modify a interface
#  @apiGroup Interfaces
#  @apiName PutIf
#  @apiParam {String} interface  Interface name, unique ID.
#  @apiDescription Modify a interface, vlan or a virtual network interface
#  @apiVersion 3.0.0
#
#
#
# @apiSuccess   {String}        ip                       IP of the interface.
# @apiSuccess   {String}        netmask                  Netmask of the interface.
# @apiSuccess   {String}        gateway                  Gateway of the interface. This value could not be modified in virtual network interface.
#
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Modify interface eth0:new",
#   "params" : [
#      {
#         "gateway" : "192.168.1.0"
#      },
#      {
#         "ip" : "192.168.1.160"
#      },
#      {
#         "netmask" : "255.255.255.0"
#      }
#   ]
#}
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        -d '{"ip":"192.168.1.160","netmask":"255.255.255.0",
#       "gateway":"192.168.1.0"}' https://<zenlb_server>:444/zapi/v3/zapi.cgi/modifyif/eth0:new/4
#
# @apiSampleRequest off
#
#**

sub modify_interface # ( $json_obj, $fdev )
{
	my $json_obj = shift;
	my $fdev = shift;

	my $ip_v;

	my $error = "false";

	# If $fdev contain '/' means that we have received 2 parameters, interface_name and ip_version
	if ( $fdev =~ /\// )
	{
		&zenlog("modify_interface fdev:$fdev");
		
		# Get interface_name and ip_version from $fdev
		my @ifandipv = split ( '/', $fdev );
		$fdev = $ifandipv[0];
		$ip_v = $ifandipv[1];
		
		# If $ip_v is empty, establish IPv4 like default protocol
		$ip_v = 4 if not $ip_v;
		
		if ( $ip_v != 4 && $ip_v != 6 )
		{
			# Error
			my $errormsg = "The ip version value $ip_v must be 4 or 6";
			my $body = {
						 description => "Delete interface $fdev",
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}	
	}
	
	# If ip_v is empty, default value is 4
	if ( !$ip_v ) { $ip_v = 4; }

	# Check interface errors
	if ( $fdev =~ /^$/ )
	{
		# Error
		my $errormsg = "Interface name can't be empty";
		my $body = {
					 description => "Modify interface $fdev",
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 400, body => $body });
	}

	if ( $fdev =~ /\s+/ )
	{
		# Error
		my $errormsg = "Interface name is not valid";
		my $body = {
					 description => "Modify interface $fdev",
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 400, body => $body });
	}
	
	my $if_ref = &getInterfaceConfig( $fdev, $ip_v );
	
	if ( ! $if_ref && $fdev !~ /:|\./ )
	{
		my $socket = IO::Socket::INET->new( Proto => 'udp' );
		my @system_interfaces = $socket->if_list;

		if ( scalar grep (/^$fdev$/, @system_interfaces) > 0 )
		{
			$if_ref = &getSystemInterface( $fdev );
			$$if_ref{ip_v} = $ip_v;
		}
			&zenlog("fdev:$fdev system_interfaces:@system_interfaces");
	}

	if ( ! $$if_ref{mac} )
	{
		# Error
		my $errormsg = "The stack IPv$ip_v in Network interface $fdev doesn't exist.";
		my $body = {
					 description => "Modify interface $fdev",
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 400, body => $body });
	}

	# Check address errors
	if ( ipisok( $json_obj->{ ip } ) eq "false" )
	{
		# Error
		my $errormsg = "IP Address $json_obj->{ip} structure is not ok.";
		my $body = {
					 description => "IP Address $json_obj->{ip}",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
	
	# Check netmask errors
	if ( exists ( $json_obj->{netmask} ) )
	{
		# Check netmask errors for IPv4
		if ( $ip_v == 4 
			&& ( $json_obj->{netmask} eq ''
				|| ( &ipisok( $json_obj->{netmask}, 4 ) eq "false"
					&& ( $json_obj->{netmask} !~ /^\d+$/ || $json_obj->{netmask} > 32 || $json_obj->{netmask} < 0 )
					) 
				)
			)
		{
			# Error
			my $errormsg = "Netmask Address $json_obj->{netmask} structure is not ok. Must be IPv4 structure or numeric.";
			my $body = {
			  description => "Netmask Address $json_obj->{netmask}",
			  error       => "true",
			  message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}

		# Check netmask errors for IPv6
		if ( $ip_v == 6 && ( $json_obj->{netmask} !~ /^\d+$/ || $json_obj->{netmask} > 128 || $json_obj->{netmask} < 0 ) )
		{
			# Error
			my $errormsg = "Netmask Address $json_obj->{netmask} structure is not ok. Must be numeric.";
			my $body = {
						 description => "Netmask Address $json_obj->{netmask}",
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}
	}

	# Check gateway errors
	if (    $json_obj->{ gateway } !~ /^$/
		 && &ipisok( $json_obj->{ gateway } ) eq "false" )
	{
		# Error
		my $errormsg = "Gateway Address $json_obj->{gateway} structure is not ok.";
		my $body = {
					 description => "Gateway Address $json_obj->{gateway}",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	# No errors found
	if ( $error eq "false" )
	{
		# Vlans need to be created if they don't already exist
		my $exists = &ifexist( $if_ref->{name} );
		if ( $exists eq "false" )
		{
			&createIf( $if_ref );
		}
		
		# Set the new params
		if ( exists( $json_obj->{ip} ) )
		{
			$if_ref->{addr} = $json_obj->{ip};
		}
		# If Vini is configured, only IP is the parameter editable
		if ( $if_ref->{vini} eq '' )
		{
			if ( exists( $json_obj->{netmask} ) )
			{
				$if_ref->{mask} = $json_obj->{netmask};
			}
			if ( exists( $json_obj->{gateway} ) && $name =~ /^$/ )
			{
				$if_ref->{gateway} = $json_obj->{gateway};
			}
		}

		# Delete old parameters
		my $old_iface_ref = &getInterfaceConfig( $fdev, $ip_v );

		if ( $old_iface_ref )
		{
			# Delete old IP and Netmask from system to replace it
			&delIp( $$old_iface_ref{name}, $$old_iface_ref{addr}, $$old_iface_ref{mask} );
		
			# Remove routes if the interface has its own route table: nic and vlan
			if ( $interface{vini} eq '' )
			{
				&delRoutes( "local", $old_iface_ref );
			}
		}
		
		# Add new IP, netmask and gateway
		&addIp( $if_ref );		
		my $state = &upIf( $if_ref, 'writeconf' );

		if ( $state == 0 )
		{
			$if_ref->{status} = "up";
		}

		# Writing new parameters in configuration file
		if ( $if_ref->{name} !~ /:/ )
		{
			&writeRoutes( $if_ref->{name} );
		}
		
		&setInterfaceConfig( $if_ref );
		&applyRoutes( "local", $if_ref );
	}

	# Print params
	if ( $error ne "true" )
	{
		# Success
		my $body = {
					 description => "Modify interface $if",
					 params      => $json_obj,
		};

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		# Error
		my $errormsg = "Errors found trying to modify interface $if";
		my $body = {
					 description => "Modify interface $if",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
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
	if ( exists $json_obj->{ netmask } )
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
	$if_ref              = &getSystemInterface( $nic );
	$if_ref->{ addr }    = $json_obj->{ ip };
	$if_ref->{ mask }    = $json_obj->{ netmask };
	$if_ref->{ gateway } = $json_obj->{ gateway };
	$if_ref->{ ip_v }    = 4;

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
		my $errormsg = "Errors found trying to modify interface $if";
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

	my $description => "Modify virtual interface",
	my $ip_v = 4;
	my $if_ref = &getInterfaceConfig( $virtual, $ip_v );

	unless ( $if_ref )
	{
		# Error
		my $errormsg = "Virtual interface not found";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 404, body => $body });
	}

	# Check address errors
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

	# No errors found
	eval {
		# Delete old IP and Netmask from system to replace it
		die if &delIp( $$if_ref{name}, $$if_ref{addr}, $$if_ref{mask} );

		# Set the new params
		$if_ref->{addr} = $json_obj->{ip};

		# Add new IP, netmask and gateway
		die if &addIp( $if_ref );

		my $state = &upIf( $if_ref, 'writeconf' );

		if ( $state == 0 )
		{
			$if_ref->{status} = "up";
			&applyRoutes( "local", $if_ref );
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
		my $errormsg = "Errors found trying to modify interface $if";
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

	if ( grep { !/^(?:ip|netmask|gateway)$/ } keys $json_obj )
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
	if ( exists $json_obj->{ netmask } )
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
	$if_ref              = &getSystemInterface( $bond );
	$if_ref->{ addr }    = $json_obj->{ ip } // $if_ref->{ addr };
	$if_ref->{ mask }    = $json_obj->{ netmask } // $if_ref->{ mask };
	$if_ref->{ gateway } = $json_obj->{ gateway } // $if_ref->{ gateway };
	$if_ref->{ ip_v }    = 4;

	if ( $if_ref->{ addr } xor $if_ref->{ mask } )
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

1;
