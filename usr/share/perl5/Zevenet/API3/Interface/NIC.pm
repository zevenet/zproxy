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

sub modify_interface_nic # ( $json_obj, $nic )
{
	my $json_obj = shift;
	my $nic = shift;

	my $description = "Configure nic interface";
	my $ip_v = 4;

	# validate NIC NAME
	my @system_interfaces = &getInterfaceList();
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

		# sometimes there are expected errors pending to be controlled
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


1;
