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
	require Zevenet::Net::Validate;
	my $parent_exist = &ifexist($json_obj->{ parent });
	unless ( $parent_exist eq "true" || $parent_exist eq "created" )
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
	require Zevenet::Net::Util;
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
	if ( $json_obj->{ ip_v } == 4 && ($json_obj->{ netmask } == undef || ! &getValidFormat( 'IPv4_mask', $json_obj->{ netmask } )) )
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

	$if_ref = {
				name    => $json_obj->{ name },
				dev     => $json_obj->{ parent },
				status  => "up",
				vlan    => $json_obj->{ tag },
				addr    => $json_obj->{ ip },
				mask    => $json_obj->{ netmask },
				gateway => $json_obj->{ gateway } // '',
				ip_v    => &ipversion( $json_obj->{ ip } ),
				mac     => $socket->if_hwaddr( $json_obj->{ parent } ),
	};

	# No errors
	require Zevenet::Net::Core;
	require Zevenet::Net::Route;
	require Zevenet::Net::Interface;
	eval {
		&zenlog("new_vlan: $if_ref->{name}");
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

sub delete_interface_vlan # ( $vlan )
{
	my $vlan = shift;

	my $description = "Delete VLAN interface";
	my $ip_v = 4;
	require Zevenet::Net::Interface;
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

	require Zevenet::Net::Core;
	require Zevenet::Net::Route;
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

sub get_vlan_list # ()
{
	my @output_list;

	my $description = "List VLAN interfaces";

	# get cluster interface
	include 'Zevenet::Cluster';
	my $zcl_conf  = &getZClusterConfig();
	my $cluster_if = $zcl_conf->{ _ }->{ interface };
	
	require Zevenet::Net::Interface;
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

	require Zevenet::Net::Interface;
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

sub actions_interface_vlan # ( $json_obj, $vlan )
{
	my $json_obj = shift;
	my $vlan     = shift;

	require Zevenet::Net::Interface;

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
		require Zevenet::Net::Validate;
		require Zevenet::Net::Route;
		require Zevenet::Net::Core;

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
			require Zevenet::Net::Util;
			&setIfacesUp( $if_ref->{ name }, "vini" );
		}
		else
		{
			# Error
			my $errormsg = "The interface $if_ref->{ name } could not be set UP";
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
		require Zevenet::Net::Core;

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

sub modify_interface_vlan # ( $json_obj, $vlan )
{
	my $json_obj = shift;
	my $vlan = shift;

	require Zevenet::Net::Interface;

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
		require Zevenet::Net::Core;
		require Zevenet::Net::Route;

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


1;
