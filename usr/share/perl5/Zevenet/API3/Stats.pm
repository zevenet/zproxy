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
		my $name   = &getFarmName( $file );
		my $type   = &getFarmType( $name );
		my $status = &getFarmStatus( $name );
		my $vip    = &getFarmVip( 'vip', $name );
		my $port   = &getFarmVip( 'vipp', $name );
		my $established = 0;
		my $pending     = 0;
		$status = "needed restart" if $status eq 'up' && ! &getFarmLock($name);

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

	my $errormsg;
	my $description = "Get farm stats";

	require Zevenet::Farm::Core;

	if ( &getFarmFile( $farmname ) == -1 )
	{
		$errormsg = "The farmname $farmname does not exist.";
		my $body = { description => $description, error  => "true", message => $errormsg };
		&httpResponse( { code => 404, body => $body } );		
	}

	my $type = &getFarmType( $farmname );

	if ( $type eq "http" || $type eq "https" )
	{
		my @out_rss;
		my @out_css;
		my @netstat;

		require Zevenet::Farm::Base;

		my $fvip = &getFarmVip( "vip", $farmname );
		my $fpid = &getFarmChildPid( $farmname );

		require Zevenet::Farm::Backend;

		my @content = &getFarmBackendStatusCtl( $farmname );
		my @backends = &getFarmBackendsStatus_old( $farmname, @content );

		# List of services
		my @a_service;
		my $sv;

		foreach ( @content )
		{
			if ( $_ =~ /Service/ )
			{
				my @l = split ( "\ ", $_ );
				$sv = $l[2];
				$sv =~ s/"//g;
				chomp ( $sv );
				push ( @a_service, $sv );
			}
		}

		# List of backends
		my $backendsize    = @backends;
		my $activebackends = 0;
		my $activesessions = 0;

		foreach ( @backends )
		{
			my @backends_data = split ( "\t", $_ );
			if ( $backends_data[3] eq "up" )
			{
				$activebackends++;
			}
		}

		my $i = -1;

		foreach ( @backends )
		{
			my @backends_data = split ( "\t", $_ );
			$activesessions = $activesessions + $backends_data[6];
			if ( $backends_data[0] == 0 )
			{
				$i++;
			}
			my $ip_backend   = $backends_data[1];
			my $port_backend = $backends_data[2];

			require Zevenet::Net::ConnStats;
			require Zevenet::Farm::Stats;

			@netstat = &getConntrack( "$fvip", $ip_backend, "", "", "tcp" );
			my @synnetstatback =
			&getBackendSYNConns( $farmname, $ip_backend, $port_backend, @netstat );
			my $npend = @synnetstatback; 

			if ( $backends_data[3] == -1 || $backends_data[3] eq "fgDOWN" )
			{
				$backends_data[3] = "down";
			}

			push @out_rss,
			  {
				service     => $a_service[$i],
				id          => $backends_data[0]+0,
				ip          => $backends_data[1],
				port        => $backends_data[2]+0,
				status      => $backends_data[3],
				pending     => $npend,
				established => $backends_data[7]+0,
			  };
		}

		# Client Session Table
		my @sessions = &getFarmBackendsClientsList( $farmname, @content );
		my $t_sessions = $#sessions + 1;

		foreach ( @sessions )
		{
			my @sessions_data = split ( "\t", $_ );

			push @out_css,
			  {
				service => $sessions_data[0],
				client  => $sessions_data[1],
				session => $sessions_data[2],
				id      => $sessions_data[3]
			  };
		}

		# Print Success
		my $body = {
					description         => "List farm stats",
					backends => \@out_rss,
					sessions => \@out_css,
		};

		&httpResponse({ code => 200, body => $body });
	}

	if ( $type eq "l4xnat" )
	{
		require Zevenet::Farm::L4xNAT::Config;

		# Parameters
		my @out_rss;

		my @args;
		my $nattype = &getFarmNatType( $farmname );
		my $proto   = &getFarmProto( $farmname );

		if ( $proto eq "all" )
		{
			$proto = "";
		}

		# my @netstat = &getNetstatNat($args);
		my $fvip     = &getFarmVip( "vip", $farmname );
		my @content  = &getFarmBackendStatusCtl( $farmname );
		#~ chomp @content;
		my @backends = &getFarmBackendsStatus_old( $farmname, @content );

		# List of backends
		my $backendsize    = @backends;
		my $activebackends = 0;
		
		foreach ( @backends )
		{
			my @backends_data = split ( ";", $_ );
			if ( $backends_data[4] eq "up" )
			{
				$activebackends++;
			}
		}

		my $index = 0;

		foreach ( @backends )
		{
			my @backends_data = split ( ";", $_ );
			chomp @backends_data;
			my $ip_backend   = $backends_data[0];
			my $port_backend = $backends_data[1];

			# Pending Conns
			my @netstat = &getConntrack( "", $fvip, $ip_backend, "", "" );

			my $established = scalar &getBackendEstConns( $farmname, $ip_backend, $port_backend, @netstat );
			
			my $pending = 0;
			if ( $proto ne "udp" )
			{
				$pending = scalar &getBackendSYNConns( $farmname, $ip_backend, $port_backend, @netstat );
			}

			if ( $backends_data[4] == -1 )
			{
				$backends_data[4] = "down";
			}

			push @out_rss,
			  {
				id          => $index,
				ip          => $ip_backend,
				port        => $port_backend,
				status      => $backends_data[4],
				pending     => $pending,
				established => $established,
			  };

			$index = $index + 1;
		}

		# Print Success
		my $body = {
					description       => "List farm stats",
					backends => \@out_rss,
		};

		&httpResponse({ code => 200, body => $body });
	}

	if ( $type eq "gslb" )
	{
		require Zevenet::Farm::GSLB::Stats;
		require Zevenet::Farm::GSLB::Service;

		my $out_rss;
		my $gslb_stats = &getGSLBGdnsdStats( $farmname );
		my @backendStats;
		my @services = &getGSLBFarmServices( $farmname );

		require Zevenet::Farm::Config;

		foreach my $srv ( @services )
		{
			# Default port health check
			my $port       = &getFarmVS( $farmname, $srv, "dpc" );
			my $lb         = &getFarmVS( $farmname, $srv, "algorithm" );
			my $backendsvs = &getFarmVS( $farmname, $srv, "backends" );
			my @be = split ( "\n", $backendsvs );
			my $out_b = [];

			#
			# Backends
			#

			foreach my $subline ( @be )
			{
				$subline =~ s/^\s+//;

				if ($subline =~ /^$/)
				{
					next;
				}

				# ID and IP
				my @subbe = split(" => ",$subline);
				my $id = $subbe[0];
				my $addr = $subbe[1];
				my $status;

				# look for backend status in stats
				foreach my $st_srv ( @{ $gslb_stats->{ 'services' } } )
				{
					if ( $st_srv->{ 'service' } =~ /^$addr\/[\w]+$port$/ )
					{
						$status = $st_srv->{ 'real_state' };
						last;
					}
				}

				$id =~ s/^primary$/1/;
				$id =~ s/^secondary$/2/;
				$status = lc $status if defined $status;

				push @backendStats,
				  {
					id      => $id + 0,
					ip      => $addr,
					service => $srv,
					port    => $port + 0,
					status  => $status
				  };
			}
		}

		# Print Success
		my $body = {
					 description => "List farm stats",
					 backends    => \@backendStats,
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

	# Print Success
	my $body = {
				 description       => "List all farms stats",
				 farms => $farms,
	};

	&httpResponse({ code => 200, body => $body });
}

# Get the number of farms
sub farms_number
{
	require Zevenet::Farm::Ext;
	my $number =  scalar &getFarmNameList();

	# Print Success
	my $body = {
				 description       => "Number of farms.",
				 number => $number,
	};

	&httpResponse({ code => 200, body => $body });
}

# GET /stats/farms/modules
#Get a farm status resume 
sub module_stats_status
{
	my @farms = @{ &getAllFarmStats () };
	my $lslb = { 'total' => 0, 'up' => 0, 'down' => 0, };
	my $gslb = { 'total' => 0, 'up' => 0, 'down' => 0, };
	my $dslb = { 'total' => 0, 'up' => 0, 'down' => 0, };

	foreach my $farm ( @farms )
	{
		if ( $farm->{ 'profile' } =~ /(?:http|https|l4xnat)/ )
		{
			$lslb->{ 'total' } ++;
			$lslb->{ 'down' } ++ 	if ( $farm->{ 'status' } eq 'down' );
			$lslb->{ 'up' } ++ 		if ( $farm->{ 'status' } eq 'up' || $farm->{ 'status' } eq 'needed restart' );
		}
		elsif ( $farm->{ 'profile' } =~ /gslb/ )
		{
			$gslb->{ 'total' } ++;
			$gslb->{ 'down' } ++ 	if ( $farm->{ 'status' } eq 'down' );
			$gslb->{ 'up' } ++ 		if ( $farm->{ 'status' } eq 'up' || $farm->{ 'status' } eq 'needed restart' );
		}
		elsif ( $farm->{ 'profile' } =~ /datalink/ )
		{
			$dslb->{ 'total' } ++;
			$dslb->{ 'down' } ++ 	if ( $farm->{ 'status' } eq 'down' );
			$dslb->{ 'up' } ++ 		if ( $farm->{ 'status' } eq 'up' || $farm->{ 'status' } eq 'needed restart' );
		}
	}
	
	# Print Success
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
	my @farms = @{ &getAllFarmStats () };
	my @farmModule;

	foreach my $farm ( @farms )
	{
		push @farmModule, $farm	if ( $farm->{ 'profile' } =~ /(?:http|https|l4xnat)/ && $module eq 'lslb' );
		push @farmModule, $farm	if ( $farm->{ 'profile' } =~ /gslb/ && $module eq 'gslb' );
		push @farmModule, $farm	if ( $farm->{ 'profile' } =~ /datalink/ && $module eq 'dslb' );
	}
	
	# Print Success
	my $body = {
				 description       => "List lslb farms stats", farms => \@farmModule,
	};
	&httpResponse({ code => 200, body => $body });
}

#GET /stats
sub stats # ()
{
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

	&httpResponse({ code => 200, body => $body });
}

#GET /stats/mem
sub stats_mem # ()
{
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

	&httpResponse({ code => 200, body => $body });
}

#GET /stats/load
sub stats_load # ()
{
	require Zevenet::Stats;
	my @data_load = &getLoadStats();

	my $out = {
		'hostname' => &getHostname(),
		'date'     => &getDate(),
	};

	foreach my $x ( 0 .. @data_load - 1 )
	{
		my $name  = $data_load[$x][0];
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

	&httpResponse({ code => 200, body => $body });
}

#GET /stats/cpu
sub stats_cpu # ()
{
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
		(undef, $name) = split( 'CPU', $name );
		$out->{ $name } = $value;
	}

	$out->{ cores } = &getCpuCores();

	# Success
	my $body = {
				 description => "System CPU usage",
				 params      => $out
	};

	&httpResponse({ code => 200, body => $body });
}

#GET /stats/system/connections
sub stats_conns
{
	# Success
	my $out = &getTotalConnections ();
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

	my $description = "Interfaces info";
	my @interfaces = &getNetworkStats( 'hash' );
	
	my @nic = &getInterfaceTypeList( 'nic' );
	my @bond = &getInterfaceTypeList( 'bond' );
	
	my @nicList;
	my @bondList;
	
	my @restIfaces;

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
			$iface->{ mac }	= $extrainfo->{ mac };
			$iface->{ ip } 		= $extrainfo->{ addr };
			$iface->{ status } = $extrainfo->{ status };
			$iface->{ vlan } = &getAppendInterfaces ( $iface->{ interface }, 'vlan' );
			$iface->{ virtual } = &getAppendInterfaces ( $iface->{ interface }, 'virtual' );
			
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
			$iface->{ mac }	= $extrainfo->{ mac };
			$iface->{ ip } 		= $extrainfo->{ addr };
			$iface->{ status } = $extrainfo->{ status };
			$iface->{ vlan } = &getAppendInterfaces ( $iface->{ interface }, 'vlan' );
			$iface->{ virtual } = &getAppendInterfaces ( $iface->{ interface }, 'virtual' );
			
			$iface->{ slaves } = &getBondSlaves ( $iface->{ interface } );
			
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
	&httpResponse({ code => 200, body => $body });
}

#GET /stats/network
sub stats_network # ()
{
	require Zevenet::Stats;

	my @interfaces = &getNetworkStats( 'hash' );

	my $output;
	$output->{ 'hostname'} = &getHostname();
	$output->{ 'date' } 		= &getDate();
	$output->{ 'interfaces' } = \@interfaces;

	# Success
	my $body = {
				 description => "Network interefaces usage",
				 params      => $output
	};

	&httpResponse({ code => 200, body => $body });
}

1;
