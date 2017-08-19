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
		my $errormsg = "IP Address is not valid.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	require Zevenet::Net::Validate;
	$json_obj->{ ip_v } = ipversion( $json_obj->{ ip } );

	# validate PARENT
	# virtual interfaces require a configured parent interface
	my $parent_exist = &ifexist( $json_obj->{ parent } );
	unless ( $parent_exist eq "true" && &getInterfaceConfig( $json_obj->{ parent }, $json_obj->{ ip_v } ) )
	{
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
		my $errormsg = "Network interface $json_obj->{ name } already exists.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	# Check new IP address is not in use
	require Zevenet::Net::Util;

	my @activeips = &listallips();

	for my $ip ( @activeips )
	{
		if ( $ip eq $json_obj->{ ip } )
		{
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

	require Zevenet::Net::Core;
	require Zevenet::Net::Route;

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
		if ( eval { require Zevenet::Cluster; } )
		{
			&runZClusterRemoteManager( 'interface', 'start', $if_ref->{ name } );
		}

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
		my $errormsg = "The $json_obj->{ name } virtual network interface can't be created";
		my $body = {
					   description => $description,
					   error       => "true",
					   message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

sub delete_interface_virtual # ( $virtual )
{
	my $virtual = shift;

	require Zevenet::Net::Interface;

	my $description = "Delete virtual interface";
	my $ip_v = 4;
	my $if_ref = &getInterfaceConfig( $virtual, $ip_v );

	if ( !$if_ref )
	{
		my $errormsg = "The virtual interface $virtual doesn't exist.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 400, body => $body });
	}

	require Zevenet::Net::Route;
	require Zevenet::Net::Core;

	eval {
		die if &delRoutes( "local", $if_ref );
		die if &downIf( $if_ref, 'writeconf' );
		die if &delIf( $if_ref );
	};

	if ( ! $@ )
	{
		if ( eval { require Zevenet::Cluster; } )
		{
			&runZClusterRemoteManager( 'interface', 'stop', $if_ref->{ name } );
			&runZClusterRemoteManager( 'interface', 'delete', $if_ref->{ name } );
		}

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
		my $errormsg = "The virtual interface $virtual can't be deleted";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 400, body => $body });
	}
}

sub get_virtual_list # ()
{
	require Zevenet::Net::Interface;

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

	require Zevenet::Net::Interface;

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
		my $errormsg = "Virtual interface not found.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 404, body => $body } );
	}
}

sub actions_interface_virtual # ( $json_obj, $virtual )
{
	my $json_obj = shift;
	my $virtual  = shift;

	require Zevenet::Net::Interface;

	my $description = "Action on virtual interface";
	my $ip_v = 4;

	# validate VLAN
	unless ( grep { $virtual eq $_->{ name } } &getInterfaceTypeList( 'virtual' ) )
	{
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
		my $errormsg = "Only the parameter 'action' is accepted";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	my $if_ref = &getInterfaceConfig( $virtual, $ip_v );

	if ( $json_obj->{ action } eq "up" )
	{
		require Zevenet::Net::Core;

		# Add IP
		&addIp( $if_ref );

		# Check the parent's status before up the interface
		my $parent_if_name = &getParentInterfaceName( $if_ref->{name} );
		my $parent_if_status = 'up';

		if ( $parent_if_name )
		{
			my $parent_if_ref = &getSystemInterface( $parent_if_name );
			$parent_if_status = &getInterfaceSystemStatus( $parent_if_ref );
		}

		unless ( $parent_if_status eq 'up' )
		{
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
			require Zevenet::Net::Route;
			&applyRoutes( "local", $if_ref );
		}
		else
		{
			my $errormsg = "The interface could not be set UP";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}

		if ( eval { require Zevenet::Cluster; } )
		{
			&runZClusterRemoteManager( 'interface', 'start', $if_ref->{ name } );
		}
	}
	elsif ( $json_obj->{action} eq "down" )
	{
		require Zevenet::Net::Core;

		my $state = &downIf( $if_ref, 'writeconf' );

		if ( $state )
		{
			my $errormsg = "The interface could not be set DOWN";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}

		if ( eval { require Zevenet::Cluster; } )
		{
			&runZClusterRemoteManager( 'interface', 'stop', $if_ref->{ name } );
		}
	}
	else
	{
		my $errormsg = "Action accepted values are: up or down";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	my $body = {
				 description => $description,
				 params      =>  { action => $json_obj->{ action } },
	};

	&httpResponse({ code => 200, body => $body });
}

sub modify_interface_virtual # ( $json_obj, $virtual )
{
	my $json_obj = shift;
	my $virtual  = shift;

	require Zevenet::Net::Interface;

	my $description = "Modify virtual interface",
	my $ip_v = 4;
	my $if_ref = &getInterfaceConfig( $virtual, $ip_v );
	
	my $errormsg;
	my @allowParams = ( "ip" );

	unless ( $if_ref )
	{
		$errormsg = "Virtual interface not found";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 404, body => $body });
	}

	if ( $errormsg = &getValidOptParams( $json_obj, \@allowParams ) )
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
		$errormsg = "IP Address $json_obj->{ip} structure is not ok.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	require Zevenet::Net::Core;

	my $state = $if_ref->{ 'status' };
	&downIf( $if_ref ) if $state eq 'up';

	if ( eval { require Zevenet::Cluster; } )
	{
		&runZClusterRemoteManager( 'interface', 'stop', $if_ref->{ name } );
	}

	eval {
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

	if ( ! $@ )
	{
		if ( eval { require Zevenet::Cluster; } )
		{
			&runZClusterRemoteManager( 'interface', 'start', $if_ref->{ name } );
		}

		my $body = {
					 description => $description,
					 params      => $json_obj,
		};

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		$errormsg = "Errors found trying to modify interface $virtual";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

1;
