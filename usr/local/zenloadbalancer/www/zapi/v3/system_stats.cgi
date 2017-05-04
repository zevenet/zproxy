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

require "/usr/local/zenloadbalancer/www/system_functions.cgi";
require "/usr/local/zenloadbalancer/www/rrd_functions.cgi";
require "/usr/local/zenloadbalancer/www/networking_functions_ext.cgi";

# Supported graphs periods
my $graph_period = {
					 'daily'   => 'd',
					 'weekly'  => 'w',
					 'monthly' => 'm',
					 'yearly'  => 'y',
};

# Get all farm stats
sub getAllFarmStats
{
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

#GET disk
sub possible_graphs	#()
{
	my @farms = grep ( s/-farm//, &getGraphs2Show( "Farm" ) );
	my @net = grep ( s/iface//, &getGraphs2Show( "Network" ) );
	my @sys = ( "cpu", "load", "ram", "swap" );
	
	# Get mount point of disks
	my @mount_points;
	my $partitions = &getDiskPartitionsInfo();
	for my $key ( keys %{ $partitions } )
	{
		# mount point : root/mount_point
		push( @mount_points, "root$partitions->{ $key }->{ mount_point }" );
	}
	@mount_points = sort @mount_points;
	push @sys, { disks => \@mount_points };

	# Success
	my $body = {
		description =>
		  "These are the possible graphs, you`ll be able to access to the daily, weekly, monthly or yearly graph",
		system  => \@sys,
		interfaces => \@net,
		farms    => \@farms
	};

	&httpResponse({ code => 200, body => $body });
}

# GET all system graphs
sub get_all_sys_graphs	 #()
{
	# System values
	my @graphlist = &getGraphs2Show( "System" );
	
	my @sys = ( "cpu", "load", "ram", "swap" );
	
	# Get mount point of disks
	my @mount_points;
	my $partitions = &getDiskPartitionsInfo();
	for my $key ( keys %{ $partitions } )
	{
		# mount point : root/mount_point
		push( @mount_points, "root$partitions->{ $key }->{ mount_point }" );
	}
	@mount_points = sort @mount_points;
	push @sys, { disk => \@mount_points };

	my $body = {
		description =>
		  "These are the possible system graphs, you`ll be able to access to the daily, weekly, monthly or yearly graph", 
		  system    => \@sys
	};
	&httpResponse({ code => 200, body => $body });
}

# GET system graphs
sub get_sys_graphs	#()
{
	my $key = shift;
	my $description = "Get $key graphs";

	$key = 'mem' if ( $key eq 'ram' );
	$key = 'memsw' if ( $key eq 'swap' );

	# Print Graph Function
	my @output;
	my $graph = &printGraph( $key, 'd' );
	push @output, { frequency => 'daily', graph => $graph };
	$graph = &printGraph( $key, 'w' );
	push @output, { frequency => 'weekly', graph => $graph };
	$graph = &printGraph( $key, 'm' );
	push @output, { frequency => 'monthly', graph => $graph };
	$graph = &printGraph( $key, 'y' );
	push @output, { frequency => 'yearly', graph => $graph };

	my $body = { description => $description, graphs => \@output };
	&httpResponse({ code => 200, body => $body });
}

# GET frequency system graphs
sub get_frec_sys_graphs	#()
{	
	my $key = shift;
	my $frequency = shift;
	my $description = "Get $frequency $key graphs";

	$key = 'mem' if ( $key eq 'ram' );
	$key = 'memsw' if ( $key eq 'swap' );

	 # take initial idenfiticative letter 
	$frequency = $1  if ( $frequency =~ /^(\w)/ );

	# Print Graph Function
	my @output;
	my $graph = &printGraph( $key, $frequency );

	my $body = { description => $description, graphs => $graph };
	&httpResponse({ code => 200, body => $body });
}

# GET all interface graphs
sub get_all_iface_graphs	#()
{
	my @iface = grep ( s/iface//, &getGraphs2Show( "Network" ) );
	my $body = {
		description =>
		  "These are the possible interface graphs, you`ll be able to access to the daily, weekly, monthly or yearly graph",
		  interfaces    => \@iface
	};
	&httpResponse({ code => 200, body => $body });
}

# GET interface graphs
sub get_iface_graphs	#()
{
	my $iface = shift;
	my $description = "Get interface graphs";
	my $errormsg;
	# validate NIC NAME
	my @system_interfaces = &getInterfaceList();

	if ( ! grep( /^$iface$/, @system_interfaces ) )
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
	# graph for this farm doesn't exist
	elsif ( ! grep ( /${iface}iface/, &getGraphs2Show( "Network" ) ) )
	{
		$errormsg = "There is no rrd files yet.";
	}
	else
	{
		# Print Success
		&zenlog( "ZAPI success, trying to get graphs." );
		
		# Print Graph Function
		my @output;
		my $graph = &printGraph( "${iface}iface", 'd' );
		push @output, { frequency => 'daily', graph => $graph };
		$graph = &printGraph( "${iface}iface", 'w' );
		push @output, { frequency => 'weekly', graph => $graph };
		$graph = &printGraph( "${iface}iface", 'm' );
		push @output, { frequency => 'monthly', graph => $graph };
		$graph = &printGraph( "${iface}iface", 'y' );
		push @output, { frequency => 'yearly', graph => $graph };

		my $body = { description => $description, graphs => \@output };
		&httpResponse({ code => 200, body => $body });
	}
	
	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 400, body => $body } );
}

# GET frequency interface graphs
sub get_frec_iface_graphs	#()
{
	my $iface = shift;
	my $frequency = shift;
	my $description = "Get interface graphs";
	my $errormsg;
	# validate NIC NAME
	my @system_interfaces = &getInterfaceList();

	if ( ! grep( /^$iface$/, @system_interfaces ) )
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
	elsif ( ! grep ( /${iface}iface/, &getGraphs2Show( "Network" ) ) )
	{
		$errormsg = "There is no rrd files yet.";
	}
	else
	{
		if ( $frequency =~ /^daily|weekly|monthly|yearly$/ )
		{
			if ( $frequency eq "daily" )   { $frequency = "d"; }
			if ( $frequency eq "weekly" )  { $frequency = "w"; }
			if ( $frequency eq "monthly" ) { $frequency = "m"; }
			if ( $frequency eq "yearly" )  { $frequency = "y"; }
		}
		# Print Success
		&zenlog( "ZAPI success, trying to get graphs." );
		
		# Print Graph Function
		my $graph = &printGraph( "${iface}iface", $frequency );				
		my $body = { description => $description, graph => $graph };
		&httpResponse({ code => 200, body => $body });
	}
	
	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 400, body => $body } );
}

# GET all farm graphs
sub get_all_farm_graphs	#()
{
	my @farms = grep ( s/-farm//, &getGraphs2Show( "Farm" ) );
	my $body = {
		description =>
		  "These are the possible farm graphs, you`ll be able to access to the daily, weekly, monthly or yearly graph", 
		  farms    => \@farms
	};
	&httpResponse({ code => 200, body => $body });
}

# GET farm graphs
sub get_farm_graphs	#()
{
	my $farmName = shift;
	my $description = "Get farm graphs";
	my $errormsg;

	# this farm doesn't exist
	if ( &getFarmFile( $farmName ) == -1 )
	{
		$errormsg = "$farmName doesn't exist.";
		my $body = { description => $description, error => "true", message => $errormsg, };
		&httpResponse( { code => 404, body => $body } );
	}	
	# graph for this farm doesn't exist
	elsif ( ! grep ( /$farmName-farm/, &getGraphs2Show( "Farm" ) ) )
	{
		$errormsg = "There is no rrd files yet.";
	}
	else
	{
		# Print Success
		&zenlog( "ZAPI success, trying to get graphs." );
		
		# Print Graph Function
		my @output;
		my $graph = &printGraph( "$farmName-farm", 'd' );
		push @output, { frequency => 'daily', graph => $graph };
		$graph = &printGraph( "$farmName-farm", 'w' );
		push @output, { frequency => 'weekly', graph => $graph };
		$graph = &printGraph( "$farmName-farm", 'm' );
		push @output, { frequency => 'monthly', graph => $graph };
		$graph = &printGraph( "$farmName-farm", 'y' );
		push @output, { frequency => 'yearly', graph => $graph };

		my $body = { description => $description, graphs => \@output };
		&httpResponse({ code => 200, body => $body });
	}
	
	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 400, body => $body } );
}

# GET frequency farm graphs
sub get_frec_farm_graphs	#()
{
	my $farmName = shift;
	my $frequency = shift;
	my $description = "Get farm graphs";
	my $errormsg;

	# this farm doesn't exist
	if ( &getFarmFile( $farmName ) == -1 )
	{
		$errormsg = "$farmName doesn't exist.";
		my $body = { description => $description, error => "true", message => $errormsg, };
		&httpResponse( { code => 404, body => $body } );
	}	
	# graph for this farm doesn't exist
	elsif ( ! grep ( /$farmName-farm/, &getGraphs2Show( "Farm" ) ) )
	{
		$errormsg = "There is no rrd files yet.";
	}
	else
	{
		if ( $frequency =~ /^daily|weekly|monthly|yearly$/ )
		{
			if ( $frequency eq "daily" )   { $frequency = "d"; }
			if ( $frequency eq "weekly" )  { $frequency = "w"; }
			if ( $frequency eq "monthly" ) { $frequency = "m"; }
			if ( $frequency eq "yearly" )  { $frequency = "y"; }
		}
		# Print Success
		&zenlog( "ZAPI success, trying to get graphs." );
		
		# Print Graph Function
		my $graph = &printGraph( "$farmName-farm", $frequency );				
		my $body = { description => $description, graph => $graph };
		&httpResponse({ code => 200, body => $body });
	}
	
	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 400, body => $body } );
}

#GET mount points list
sub list_disks	#()
{
	my @mount_points;
	my $partitions = &getDiskPartitionsInfo();

	for my $key ( keys %{ $partitions } )
	{
		# mount point : root/mount_point
		push( @mount_points, "root$partitions->{ $key }->{ mount_point }" );
	}

	@mount_points = sort @mount_points;

	my $body = {
		description => "List disk partitions",
		params => \@mount_points,
	};

	&httpResponse({ code => 200, body => $body });
}

#GET disk graphs for all periods
sub graphs_disk_mount_point_all	#()
{
	my $mount_point = shift;

	$mount_point =~ s/^root[\/]?/\//;

	my $description = "Disk partition usage graphs";
	my $parts = &getDiskPartitionsInfo();

	my ( $part_key ) = grep { $parts->{ $_ }->{ mount_point } eq $mount_point } keys %{ $parts };

	unless ( $part_key )
	{
		# Error
		my $errormsg = "Mount point not found";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	my $dev_id = $parts->{ $part_key }->{ rrd_id };

	# Success
	my @graphs = (
				   { frequency => 'daily',   graph => &printGraph( $dev_id, 'd' ) },
				   { frequency => 'weekly',  graph => &printGraph( $dev_id, 'w' ) },
				   { frequency => 'monthly', graph => &printGraph( $dev_id, 'm' ) },
				   { frequency => 'yearly',  graph => &printGraph( $dev_id, 'y' ) },
	);

	my $body = {
				 description => $description,
				 graphs      => \@graphs,
	};

	&httpResponse({ code => 200, body => $body });
}

#GET disk graph for a single period
sub graph_disk_mount_point_freq	#()
{
	my $mount_point = shift;
	my $frequency = shift;

	$mount_point =~ s/^root[\/]?/\//;

	my $description = "Disk partition usage graph";
	my $parts = &getDiskPartitionsInfo();

	my ( $part_key ) = grep { $parts->{ $_ }->{ mount_point } eq $mount_point } keys %{ $parts };

	unless ( $part_key )
	{
		# Error
		my $errormsg = "Mount point not found";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	my $dev_id = $parts->{ $part_key }->{ rrd_id };
	my $freq = $graph_period->{ $frequency };

	# Success
	my $body = {
				 description => $description,
				 frequency      => $frequency,
				 graph      => &printGraph( $dev_id, $freq ),
	};

	&httpResponse({ code => 200, body => $body });
}

#Get Farm Stats
sub farm_stats # ( $farmname )
{
	my $farmname = shift;

	my $errormsg;
	my $description = "Get farm stats";

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

		# Real Server Table, from content1-25.cgi
		my @netstat;
		my $fvip = &getFarmVip( "vip", $farmname );
		my $fpid = &getFarmChildPid( $farmname );

		my @content = &getFarmBackendStatusCtl( $farmname );
		my @backends = &getFarmBackendsStatus( $farmname, @content );

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

			@netstat = &getConntrack( "$fvip", $ip_backend, "", "", "tcp" );
			my @synnetstatback =
			&getBackendSYNConns( $farmname, $ip_backend, $port_backend, @netstat );
			my $npend = @synnetstatback; 

			if ( $backends_data[3] == -1 )
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
		my @backends = &getFarmBackendsStatus( $farmname, @content );

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
		my $out_rss;
		my $gslb_stats = &getGSLBGdnsdStats( $farmname );
		my @backendStats;
		my @services = &getGSLBFarmServices( $farmname );

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
