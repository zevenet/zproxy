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

#~ use Zevenet::Net;
use Zevenet::System;

# Get all farm stats
sub getAllFarmStats
{
	require Zevenet::Farm::Core;
	require Zevenet::Farm::Base;

	my @files = &getFarmList();
	my @farms;

	# FIXME: Verify stats are working with every type of farm

	foreach my $file ( @files )
	{
		my $name        = &getFarmName( $file );
		my $type        = &getFarmType( $name );
		my $status      = &getFarmVipStatus( $name );
		my $vip         = &getFarmVip( 'vip', $name );
		my $port        = &getFarmVip( 'vipp', $name );
		my $established = 0;
		my $pending     = 0;

		if ( $status eq "up" )
		{
			require Zevenet::Net::ConnStats;
			require Zevenet::Farm::Stats;

			my @netstat = &getConntrack( "", $vip, "", "", "" );

			$pending = scalar &getFarmSYNConns( $name, @netstat );
			$established = scalar &getFarmEstConns( $name, @netstat );
		}

		push @farms,
		  {
			farmname    => $name,
			profile     => $type,
			status      => $status,
			vip         => $vip,
			vport       => $port,
			established => $established,
			pending     => $pending,
		  };
	}

	return \@farms;
}

#Get Farm Stats
sub farm_stats # ( $farmname )
{
	my $farmname = shift;

	require Zevenet::Farm::Core;

	my $desc = "Get farm stats";

	if ( &getFarmFile( $farmname ) == -1 )
	{
		my $msg = "The farmname $farmname does not exist.";
		&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $type = &getFarmType( $farmname );

	if ( $type eq "http" || $type eq "https" )
	{
		require Zevenet::Farm::HTTP::Stats;

		my $stats = &getHTTPFarmBackendsStats( $farmname );
		my $body = {
					 description => $desc,
					 backends    => $stats->{ backends },
					 sessions    => $stats->{ sessions },
		};

		&httpResponse({ code => 200, body => $body });
	}

	if ( $type eq "l4xnat" )
	{
		require Zevenet::Farm::L4xNAT::Stats;

		my $stats = &getL4FarmBackendsStats( $farmname );
		my $body = {
					 description => $desc,
					 backends    => $stats,
		};

		&httpResponse({ code => 200, body => $body });
	}

	if ( $type eq "gslb" )
	{
		require Zevenet::Farm::GSLB::Stats;

		my $gslb_stats = &getGSLBFarmBackendsStats( $farmname );
		my $body = {
					 description => $desc,
					 backends    => $gslb_stats->{ 'backend' },
					 client      => $gslb_stats->{ 'udp' },
					 server      => $gslb_stats->{ 'tcp' },
					 extended    => $gslb_stats->{ 'stats' },
		};

		&httpResponse({ code => 200, body => $body });
	}
}

#Get Farm Stats
sub all_farms_stats # ()
{
	my $farms = &getAllFarmStats();
	my $body = {
				 description => "List all farms stats",
				 farms       => $farms,
	};

	&httpResponse({ code => 200, body => $body });
}

# Get the number of farms
sub farms_number
{
	require Zevenet::Farm::Core;

	my $number = scalar &getFarmNameList();
	my $body = {
				 description => "Number of farms.",
				 number      => $number,
	};

	&httpResponse({ code => 200, body => $body });
}

# GET /stats/farms/modules
#Get a farm status resume 
sub module_stats_status
{
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
				 params 		=> {
					 "lslb" => $lslb,
					 "gslb" => $gslb,
					 "dslb" => $dslb,
					 },
	};

	&httpResponse({ code => 200, body => $body });
}

#Get lslb|gslb|dslb Farm Stats
sub module_stats # ()
{
	my $module = shift;

	my $valid_module;

	if ( $module eq 'gslb' && eval { require Zevenet::Farm::GSLB::Stats; } )
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

		&httpErrorResponse({ code => 400, msg => $msg, desc => $desc });
	}

	my @farms = @{ &getAllFarmStats () };
	my @farmModule;

	foreach my $farm ( @farms )
	{
		push @farmModule, $farm	if ( $farm->{ 'profile' } =~ /(?:https?|l4xnat)/ && $module eq 'lslb' );
		push @farmModule, $farm	if ( $farm->{ 'profile' } =~ /gslb/ && $module eq 'gslb' );
		push @farmModule, $farm	if ( $farm->{ 'profile' } =~ /datalink/ && $module eq 'dslb' );
	}

	my $body = {
				 description => "List $module farms stats",
				 farms       => \@farmModule,
	};

	&httpResponse({ code => 200, body => $body });
}

#GET /stats
sub stats # ()
{
	require Zevenet::Stats;
	require Zevenet::SystemInfo;

	my @data_mem  = &getMemStats();
	my @data_load = &getLoadStats();
	my @data_net  = &getNetworkStats();
	my @data_cpu  = &getCPU();

	my $out = {
				'hostname' => &getHostname(),
				'date'     => &getDate(),
	};

	foreach my $x ( 0 .. @data_mem - 1 )
	{
		my $name  = $data_mem[$x][0];
		my $value = $data_mem[$x][1] + 0;
		$out->{ memory }->{ $name } = $value;
	}

	foreach my $x ( 0 .. @data_load - 1 )
	{
		my $name  = $data_load[$x][0];
		my $value = $data_load[$x][1] + 0;

		$name =~ s/ /_/;
		$name = 'Last_1' if $name eq 'Last';
		$out->{ load }->{ $name } = $value;
	}

	foreach my $x ( 0 .. @data_cpu - 1 )
	{
		my $name  = $data_cpu[$x][0];
		my $value = $data_cpu[$x][1] + 0;

		$name =~ s/CPU//;
		$out->{ cpu }->{ $name } = $value;
	}

	$out->{ cpu }->{ cores } = &getCpuCores();

	foreach my $x ( 0 .. @data_net - 1 )
	{
		my $name;
		if ( $x % 2 == 0 )
		{
			$name = $data_net[$x][0] . ' in';
		}
		else
		{
			$name = $data_net[$x][0] . ' out';
		}
		my $value = $data_net[$x][1] + 0;
		$out->{ network }->{ $name } = $value;
	}

	my $body = {
				 description => "System stats",
				 params      => $out
	};

	&httpResponse({ code => 200, body => $body });
}

#GET /stats/mem
sub stats_mem # ()
{
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

	&httpResponse({ code => 200, body => $body });
}

#GET /stats/load
sub stats_load # ()
{
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

	&httpResponse({ code => 200, body => $body });
}

#GET /stats/cpu
sub stats_cpu # ()
{
	require Zevenet::Stats;
	require Zevenet::SystemInfo;

	my @data_cpu = &getCPU();

	my $out = {
				'hostname' => &getHostname(),
				'date'     => &getDate(),
	};

	foreach my $x ( 0 .. @data_cpu - 1 )
	{
		my $name  = $data_cpu[$x][0];
		my $value = $data_cpu[$x][1] + 0;
		( undef, $name ) = split ( 'CPU', $name );
		$out->{ $name } = $value;
	}

	$out->{ cores } = &getCpuCores();

	my $body = {
				 description => "System CPU usage",
				 params      => $out
	};

	&httpResponse({ code => 200, body => $body });
}

#GET /stats/system/connections
sub stats_conns
{
	my $out = &getTotalConnections();
	my $body = {
				 description => "System connections",
				 params      => { "connections" => $out },
	};

	&httpResponse({ code => 200, body => $body });
}

#GET /stats/network/interfaces
sub stats_network_interfaces
{
	require Zevenet::Stats;
	require Zevenet::Net::Interface;

	my $EE = eval { require Zevenet::Net::Bonding; }? 1: undef;

	my $desc       = "Interfaces info";
	my @interfaces = &getNetworkStats( 'hash' );
	my @nic        = &getInterfaceTypeList( 'nic' );
	my @bond;
	my @nicList;
	my @bondList;
	my @restIfaces;
	@bond = &getInterfaceTypeList( 'bond' ) if $EE;

	foreach my $iface ( @interfaces )
	{
		my $extrainfo;
		my $type = &getInterfaceType ( $iface->{ interface } );

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

			$iface->{ mac }     = $extrainfo->{ mac };
			$iface->{ ip }      = $extrainfo->{ addr };
			$iface->{ status }  = $extrainfo->{ status };
			$iface->{ vlan }    = &getAppendInterfaces( $iface->{ interface }, 'vlan' );
			$iface->{ virtual } = &getAppendInterfaces( $iface->{ interface }, 'virtual' );
			
			push @nicList, $iface;
		}
		
		# Fill bond interface list
		elsif ( $type eq 'bond' && $EE )
		{
			foreach my $ifaceBond ( @bond )
			{
				if ( $iface->{ interface } eq $ifaceBond->{ name } )
				{
					$extrainfo = $ifaceBond;
					last;
				}
			}

			$iface->{ mac }     = $extrainfo->{ mac };
			$iface->{ ip }      = $extrainfo->{ addr };
			$iface->{ status }  = $extrainfo->{ status };
			$iface->{ vlan }    = &getAppendInterfaces( $iface->{ interface }, 'vlan' );
			$iface->{ virtual } = &getAppendInterfaces( $iface->{ interface }, 'virtual' );
			$iface->{ slaves }  = &getBondSlaves( $iface->{ interface } );
			
			push @bondList, $iface;
		}
		else 
		{
			push @restIfaces, $iface;
		}
	}

	my $params->{ nic } = \@nicList;
	$params->{ bond } = \@bondList if $EE;

	my $body = {
				 description => $desc,
				 params      => $params,
	};

	&httpResponse({ code => 200, body => $body });
}

#GET /stats/network
sub stats_network # ()
{
	require Zevenet::Stats;
	require Zevenet::SystemInfo;

	my @interfaces = &getNetworkStats( 'hash' );
	my $output;
	$output->{ 'hostname' }   = &getHostname();
	$output->{ 'date' }       = &getDate();
	$output->{ 'interfaces' } = \@interfaces;

	my $body = {
				 description => "Network interefaces usage",
				 params      => $output
	};

	&httpResponse({ code => 200, body => $body });
}

1;
