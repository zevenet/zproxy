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

use Zevenet::System;

# Get all farm stats
sub getAllFarmStats
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	require Zevenet::Farm::Core;
	require Zevenet::Farm::Base;

	my @farm_names = &getFarmNameList();
	my @farms;

	# FIXME: Verify stats are working with every type of farm

	foreach my $name ( @farm_names )
	{
		my $type = &getFarmType( $name );

		# datalink has not got stats
		next if ( $type eq 'datalink' );

		my $status      = &getFarmStatus( $name );
		my $vip         = &getFarmVip( 'vip', $name );
		my $port        = &getFarmVip( 'vipp', $name );
		my $established = 0;
		my $pending     = 0;

		require Zevenet::Farm::Action;
		$status = "needed restart" if $status eq 'up' && &getFarmRestartStatus( $name );

		if ( $status eq "up" )
		{
			require Zevenet::Net::ConnStats;
			require Zevenet::Farm::Stats;

			my $netstat = &getConntrack( "", $vip, "", "", "" );

			$pending = &getFarmSYNConns( $name, $netstat );
			$established = &getFarmEstConns( $name, $netstat );
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
sub farm_stats    # ( $farmname )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $farmname = shift;

	my $errormsg;
	my $description = "Get farm stats";

	require Zevenet::Farm::Core;

	unless ( &getFarmExists( $farmname ) )
	{
		$errormsg = "The farmname $farmname does not exist.";
		my $body =
		  { description => $description, error => "true", message => $errormsg };
		&httpResponse( { code => 404, body => $body } );
	}

	my $type = &getFarmType( $farmname );

	if ( $type eq "http" || $type eq "https" )
	{
		require Zevenet::Farm::HTTP::Stats;

		my $stats = &getHTTPFarmBackendsStats( $farmname );
		my $body = {
					 description => $description,
					 backends    => $stats->{ backends },
					 sessions    => $stats->{ sessions },
		};

		&httpResponse( { code => 200, body => $body } );
	}

	if ( $type eq "l4xnat" )
	{
		require Zevenet::Farm::L4xNAT::Stats;

		my $stats = &getL4FarmBackendsStats( $farmname );
		my $body = {
					 description => $description,
					 backends    => $stats,
		};

		&httpResponse( { code => 200, body => $body } );
	}

	if ( $type eq "gslb" )
	{
		my $gslb_stats = &eload(
								 module => 'Zevenet::Farm::GSLB::Stats',
								 func   => 'getGSLBFarmBackendsStats',
								 args   => [$farmname],
								 decode => 'true'
		);

		my $body = {
					 description => $description,
					 backends    => $gslb_stats->{ 'backends' },
					 client      => $gslb_stats->{ 'udp' },
					 server      => $gslb_stats->{ 'tcp' },
					 extended    => $gslb_stats->{ 'stats' },
		};

		&httpResponse( { code => 200, body => $body } );
	}
}

#Get Farm Stats
sub all_farms_stats    # ()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $farms = &getAllFarmStats();

	# Print Success
	my $body = {
				 description => "List all farms stats",
				 farms       => $farms,
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

# GET /stats/farms/modules
#Get a farm status resume
sub module_stats_status
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my @farms = @{ &getAllFarmStats() };
	my $lslb  = { 'total' => 0, 'up' => 0, 'down' => 0, };
	my $gslb  = { 'total' => 0, 'up' => 0, 'down' => 0, };
	my $dslb  = { 'total' => 0, 'up' => 0, 'down' => 0, };

	foreach my $farm ( @farms )
	{
		if ( $farm->{ 'profile' } =~ /(?:http|https|l4xnat)/ )
		{
			$lslb->{ 'total' }++;
			$lslb->{ 'down' }++ if ( $farm->{ 'status' } eq 'down' );
			$lslb->{ 'up' }++
			  if ( $farm->{ 'status' } eq 'up' || $farm->{ 'status' } eq 'needed restart' );
		}
		elsif ( $farm->{ 'profile' } =~ /gslb/ )
		{
			$gslb->{ 'total' }++;
			$gslb->{ 'down' }++ if ( $farm->{ 'status' } eq 'down' );
			$gslb->{ 'up' }++
			  if ( $farm->{ 'status' } eq 'up' || $farm->{ 'status' } eq 'needed restart' );
		}
		elsif ( $farm->{ 'profile' } =~ /datalink/ )
		{
			$dslb->{ 'total' }++;
			$dslb->{ 'down' }++ if ( $farm->{ 'status' } eq 'down' );
			$dslb->{ 'up' }++
			  if ( $farm->{ 'status' } eq 'up' || $farm->{ 'status' } eq 'needed restart' );
		}
	}

	# Print Success
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
	my @farms  = @{ &getAllFarmStats() };
	my @farmModule;

	foreach my $farm ( @farms )
	{
		push @farmModule, $farm
		  if ( $farm->{ 'profile' } =~ /(?:http|https|l4xnat)/ && $module eq 'lslb' );
		push @farmModule, $farm
		  if ( $farm->{ 'profile' } =~ /gslb/ && $module eq 'gslb' );
		push @farmModule, $farm
		  if ( $farm->{ 'profile' } =~ /datalink/ && $module eq 'dslb' );
	}

	# Print Success
	my $body = {
				 description => "List lslb farms stats",
				 farms       => \@farmModule,
	};
	&httpResponse( { code => 200, body => $body } );
}

#GET /stats
sub stats    # ()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	require Zevenet::Stats;
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

	# Success
	my $body = {
				 description => "System stats",
				 params      => $out
	};

	&httpResponse( { code => 200, body => $body } );
}

#GET /stats/mem
sub stats_mem    # ()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	require Zevenet::Stats;
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

	# Success
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

	# Success
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

	# Success
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

	# Success
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

	my $description = "Interfaces info";
	my @interfaces  = &getNetworkStats( 'hash' );

	my @nic  = &getInterfaceTypeList( 'nic' );
	my @bond = &getInterfaceTypeList( 'bond' );

	my @nicList;
	my @bondList;

	my @restIfaces;

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
			$iface->{ mac }     = $extrainfo->{ mac };
			$iface->{ ip }      = $extrainfo->{ addr };
			$iface->{ status }  = $extrainfo->{ status };
			$iface->{ vlan }    = &getAppendInterfaces( $iface->{ interface }, 'vlan' );
			$iface->{ virtual } = &getAppendInterfaces( $iface->{ interface }, 'virtual' );

			push @nicList, $iface;
		}

		# Fill bond interface list
		elsif ( $type eq 'bond' )
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

			$iface->{ slaves } = &getBondSlaves( $iface->{ interface } );

			push @bondList, $iface;
		}
		else
		{
			push @restIfaces, $iface;
		}

	}

	# Success
	my $body = {
				 description => $description,
				 params      => { nic => \@nicList, bond => \@bondList, }
	};
	&httpResponse( { code => 200, body => $body } );
}

#GET /stats/network
sub stats_network    # ()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	require Zevenet::Stats;

	my @interfaces = &getNetworkStats( 'hash' );

	my $output;
	$output->{ 'hostname' }   = &getHostname();
	$output->{ 'date' }       = &getDate();
	$output->{ 'interfaces' } = \@interfaces;

	# Success
	my $body = {
				 description => "Network interefaces usage",
				 params      => $output
	};

	&httpResponse( { code => 200, body => $body } );
}

1;
