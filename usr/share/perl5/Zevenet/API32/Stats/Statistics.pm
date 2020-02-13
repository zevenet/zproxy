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

use Zevenet::System;

my $eload;
if ( eval { require Zevenet::ELoad; } )
{
	$eload = 1;
}

# GET /stats/farms/modules
#Get a farm status resume
sub module_stats_status
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	require Zevenet::API32::Stats;
	my @farms = @{ &getAllFarmStats() };
	my $lslb = {
				 'total'    => 0,
				 'up'       => 0,
				 'down'     => 0,
				 'critical' => 0,
				 'problem'  => 0,
	};
	my $gslb = {
				 'total'    => 0,
				 'up'       => 0,
				 'down'     => 0,
				 'critical' => 0,
				 'problem'  => 0,
	};
	my $dslb = {
				 'total'    => 0,
				 'up'       => 0,
				 'down'     => 0,
				 'critical' => 0,
				 'problem'  => 0,
	};

	foreach my $farm ( @farms )
	{
		if ( $farm->{ 'profile' } =~ /(?:http|https|l4xnat)/ )
		{
			$lslb->{ 'total' }++;
			if ( $farm->{ 'status' } eq 'down' )
			{
				$lslb->{ 'down' }++;
			}
			elsif ( $farm->{ 'status' } eq 'problem' )
			{
				$lslb->{ 'problem' }++;
			}
			elsif ( $farm->{ 'status' } eq 'critical' )
			{
				$lslb->{ 'critical' }++;
			}
			else
			{
				$lslb->{ 'up' }++;
			}
		}
		elsif ( $farm->{ 'profile' } eq 'gslb' )
		{
			$gslb->{ 'total' }++;
			if ( $farm->{ 'status' } eq 'down' )
			{
				$gslb->{ 'down' }++;
			}
			elsif ( $farm->{ 'status' } eq 'problem' )
			{
				$gslb->{ 'problem' }++;
			}
			elsif ( $farm->{ 'status' } eq 'critical' )
			{
				$gslb->{ 'critical' }++;
			}
			else
			{
				$gslb->{ 'up' }++;
			}
		}
		elsif ( $farm->{ 'profile' } eq 'datalink' )
		{
			$dslb->{ 'total' }++;
			if ( $farm->{ 'status' } eq 'down' )
			{
				$dslb->{ 'down' }++;
			}
			elsif ( $farm->{ 'status' } eq 'problem' )
			{
				$dslb->{ 'problem' }++;
			}
			elsif ( $farm->{ 'status' } eq 'critical' )
			{
				$dslb->{ 'critical' }++;
			}
			else
			{
				$dslb->{ 'up' }++;
			}
		}
	}

	my $body = {
				 description => "Module status",
				 params      => {
							 "lslb" => $lslb,
							 "gslb" => $gslb,
							 "dslb" => $dslb,
				 },
	};

	&httpResponse( { code => 200, body => $body } );
}

#Get lslb|gslb|dslb Farm Stats
sub module_stats    # ()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $module = shift;

	require Zevenet::API32::Stats;
	my $valid_module;

	if ( $module eq 'gslb' && $eload )
	{
		$valid_module = 1;
	}

	if ( $module eq 'lslb' || $module eq 'dslb' )
	{
		$valid_module = 1;
	}

	unless ( $valid_module )
	{
		my $desc = "List module farms stats";
		my $msg  = "Incorrect module";

		&httpErrorResponse( { code => 400, msg => $msg, desc => $desc } );
	}

	my @farms = @{ &getAllFarmStats() };
	my @farmModule;

	foreach my $farm ( @farms )
	{
		push @farmModule, $farm
		  if ( $farm->{ 'profile' } =~ /(?:https?|l4xnat)/ && $module eq 'lslb' );
		push @farmModule, $farm
		  if ( $farm->{ 'profile' } =~ /gslb/ && $module eq 'gslb' );
		push @farmModule, $farm
		  if ( $farm->{ 'profile' } =~ /datalink/ && $module eq 'dslb' );
	}

	my $body = {
				 description => "List $module farms stats",
				 farms       => \@farmModule,
	};

	&httpResponse( { code => 200, body => $body } );
}

# Get the number of farms
sub farms_number
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	require Zevenet::Farm::Core;

	my $number = scalar &getFarmNameList();
	my $body = {
				 description => "Number of farms.",
				 number      => $number,
	};

	&httpResponse( { code => 200, body => $body } );
}

#GET /stats/mem
sub stats_mem    # ()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	require Zevenet::Stats;
	require Zevenet::SystemInfo;

	my @data_mem = &getMemStats();
	my $out = {
				'hostname' => &getHostname(),
				'date'     => &getDate(),
	};

	foreach my $x ( 0 .. @data_mem - 1 )
	{
		my $name  = $data_mem[$x][0];
		my $value = $data_mem[$x][1] + 0;
		$out->{ $name } = $value;
	}

	my $body = {
				 description => "Memory usage",
				 params      => $out
	};

	&httpResponse( { code => 200, body => $body } );
}

#GET /stats/load
sub stats_load    # ()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	require Zevenet::Stats;
	require Zevenet::SystemInfo;

	my @data_load = &getLoadStats();
	my $out = {
				'hostname' => &getHostname(),
				'date'     => &getDate(),
	};

	foreach my $x ( 0 .. @data_load - 1 )
	{
		my $name = $data_load[$x][0];
		$name =~ s/ /_/;
		$name = 'Last_1' if $name eq 'Last';
		my $value = $data_load[$x][1] + 0;
		$out->{ $name } = $value;
	}

	my $body = {
				 description => "System load",
				 params      => $out
	};

	&httpResponse( { code => 200, body => $body } );
}

#GET /stats/cpu
sub stats_cpu    # ()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	require Zevenet::Stats;
	require Zevenet::SystemInfo;

	my $out = &getCPUUsageStats();

	$out->{ hostname } = &getHostname();
	$out->{ date }     = &getDate();
	$out->{ cores }    = &getCpuCores();

	my $body = {
				 description => "System CPU usage",
				 params      => $out
	};

	&httpResponse( { code => 200, body => $body } );
}

#GET /stats/system/connections
sub stats_conns
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $out = &getTotalConnections();
	my $body = {
				 description => "System connections",
				 params      => { "connections" => $out },
	};

	&httpResponse( { code => 200, body => $body } );
}

#GET /stats/network/interfaces
sub stats_network_interfaces
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	require Zevenet::Stats;
	require Zevenet::Net::Interface;

	my $desc       = "Interfaces info";
	my @interfaces = &getNetworkStats( 'hash' );
	my @nic        = &getInterfaceTypeList( 'nic' );
	my @bond;
	my @nicList;
	my @bondList;
	my @restIfaces;
	@bond = &getInterfaceTypeList( 'bond' ) if $eload;

	my $alias;
	$alias = &eload(
					 module => 'Zevenet::Alias',
					 func   => 'getAlias',
					 args   => ['interface']
	) if $eload;

	foreach my $iface ( @interfaces )
	{
		my $extrainfo;
		my $type = &getInterfaceType( $iface->{ interface } );

		# Fill nic interface list
		if ( $type eq 'nic' )
		{
			foreach my $ifaceNic ( @nic )
			{
				if ( $iface->{ interface } eq $ifaceNic->{ name } )
				{
					$extrainfo = $ifaceNic;
					last;
				}
			}

			$iface->{ alias }   = $alias->{ $iface->{ interface } } if $eload;
			$iface->{ mac }     = $extrainfo->{ mac };
			$iface->{ ip }      = $extrainfo->{ addr };
			$iface->{ status }  = $extrainfo->{ status };
			$iface->{ vlan }    = &getAppendInterfaces( $iface->{ interface }, 'vlan' );
			$iface->{ virtual } = &getAppendInterfaces( $iface->{ interface }, 'virtual' );

			push @nicList, $iface;
		}

		# Fill bond interface list
		elsif ( $type eq 'bond' && $eload )
		{
			foreach my $ifaceBond ( @bond )
			{
				if ( $iface->{ interface } eq $ifaceBond->{ name } )
				{
					$extrainfo = $ifaceBond;
					last;
				}
			}

			$iface->{ alias }   = $alias->{ $iface->{ interface } } if $eload;
			$iface->{ mac }     = $extrainfo->{ mac };
			$iface->{ ip }      = $extrainfo->{ addr };
			$iface->{ status }  = $extrainfo->{ status };
			$iface->{ vlan }    = &getAppendInterfaces( $iface->{ interface }, 'vlan' );
			$iface->{ virtual } = &getAppendInterfaces( $iface->{ interface }, 'virtual' );
			$iface->{ slaves } = &eload(
										 module => 'Zevenet::Net::Bonding',
										 func   => 'getBondSlaves',
										 args   => [$iface->{ interface }],
			);

			push @bondList, $iface;
		}
		else
		{
			push @restIfaces, $iface;
		}
	}

	my $params->{ nic } = \@nicList;
	$params->{ bond } = \@bondList if $eload;

	my $body = {
				 description => $desc,
				 params      => $params,
	};

	&httpResponse( { code => 200, body => $body } );
}

1;
