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

# GET /interfaces Get params of the interfaces
sub get_interfaces # ()
{
	my @output_list;

	my $description = "List interfaces";

	# Configured interfaces list
	require Zevenet::Net::Interface;
	my @interfaces = @{ &getSystemInterfaceList() };
	
	# get cluster interface
	include 'Zevenet::Cluster';
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

1;
