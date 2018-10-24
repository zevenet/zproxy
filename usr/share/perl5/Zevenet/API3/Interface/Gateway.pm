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

sub get_gateway
{
	&zenlog(__FILE__ . ":" . __LINE__ . ":" . (caller(0))[3] . "( @_ )", "debug", "PROFILING" );
	require Zevenet::Net::Route;

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

sub modify_gateway # ( $json_obj )
{
	&zenlog(__FILE__ . ":" . __LINE__ . ":" . (caller(0))[3] . "( @_ )", "debug", "PROFILING" );
	my $json_obj = shift;

	require Zevenet::Net::Route;

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
		require Zevenet::Net::Interface;

		my @system_interfaces = &getInterfaceList();
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

	require Zevenet::Net::Interface;
	my $if_ref = getInterfaceConfig( $interface, $ip_version );

	&zenlog("applyRoutes interface:$interface address:$address if_ref:$if_ref", "info", "NETWORK");
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
	&zenlog(__FILE__ . ":" . __LINE__ . ":" . (caller(0))[3] . "( @_ )", "debug", "PROFILING" );
	require Zevenet::Net::Route;
	require Zevenet::Net::Interface;

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
