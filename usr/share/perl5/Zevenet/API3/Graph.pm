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

use Zevenet::RRD;

# Supported graphs periods
my $graph_period = {
					 'daily'   => 'd',
					 'weekly'  => 'w',
					 'monthly' => 'm',
					 'yearly'  => 'y',
};

#GET disk
sub possible_graphs    #()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my @farms = grep ( s/-farm//, &getGraphs2Show( "Farm" ) );
	my @net   = grep ( s/iface//, &getGraphs2Show( "Network" ) );
	my @sys = ( "cpu", "load", "ram", "swap" );

	# Get mount point of disks
	require Zevenet::Stats;
	my @mount_points;
	my $partitions = &getDiskPartitionsInfo();
	for my $key ( keys %{ $partitions } )
	{
		# mount point : root/mount_point
		push ( @mount_points, "root$partitions->{ $key }->{ mount_point }" );
	}
	@mount_points = sort @mount_points;
	push @sys, { disks => \@mount_points };

	# Success
	my $body = {
		description =>
		  "These are the possible graphs, you'll be able to access to the daily, weekly, monthly or yearly graph",
		system     => \@sys,
		interfaces => \@net,
		farms      => \@farms
	};

	&httpResponse( { code => 200, body => $body } );
}

# GET all system graphs
sub get_all_sys_graphs    #()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	# System values
	my @graphlist = &getGraphs2Show( "System" );

	my @sys = ( "cpu", "load", "ram", "swap" );

	# Get mount point of disks
	require Zevenet::Stats;
	my @mount_points;
	my $partitions = &getDiskPartitionsInfo();
	for my $key ( keys %{ $partitions } )
	{
		# mount point : root/mount_point
		push ( @mount_points, "root$partitions->{ $key }->{ mount_point }" );
	}
	@mount_points = sort @mount_points;
	push @sys, { disk => \@mount_points };

	my $body = {
		description =>
		  "These are the possible system graphs, you'll be able to access to the daily, weekly, monthly or yearly graph",
		system => \@sys
	};
	&httpResponse( { code => 200, body => $body } );
}

# GET system graphs
sub get_sys_graphs    #()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $key         = shift;
	my $description = "Get $key graphs";

	$key = 'mem'   if ( $key eq 'ram' );
	$key = 'memsw' if ( $key eq 'swap' );

	# Print Graph Function
	my @output;
	my $graph = &printGraph( $key, 'd' )->{ img };
	push @output, { frequency => 'daily', graph => $graph };
	$graph = &printGraph( $key, 'w' )->{ img };
	push @output, { frequency => 'weekly', graph => $graph };
	$graph = &printGraph( $key, 'm' )->{ img };
	push @output, { frequency => 'monthly', graph => $graph };
	$graph = &printGraph( $key, 'y' )->{ img };
	push @output, { frequency => 'yearly', graph => $graph };

	my $body = { description => $description, graphs => \@output };
	&httpResponse( { code => 200, body => $body } );
}

# GET frequency system graphs
sub get_frec_sys_graphs    #()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $key         = shift;
	my $frequency   = shift;
	my $description = "Get $frequency $key graphs";

	$key = 'mem'   if ( $key eq 'ram' );
	$key = 'memsw' if ( $key eq 'swap' );

	# take initial idenfiticative letter
	$frequency = $1 if ( $frequency =~ /^(\w)/ );

	# Print Graph Function
	my @output;
	my $graph = &printGraph( $key, $frequency )->{ img };

	my $body = { description => $description, graphs => $graph };
	&httpResponse( { code => 200, body => $body } );
}

# GET all interface graphs
sub get_all_iface_graphs    #()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my @iface = grep ( s/iface//, &getGraphs2Show( "Network" ) );
	my $body = {
		description =>
		  "These are the possible interface graphs, you'll be able to access to the daily, weekly, monthly or yearly graph",
		interfaces => \@iface
	};
	&httpResponse( { code => 200, body => $body } );
}

# GET interface graphs
sub get_iface_graphs    #()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $iface       = shift;
	my $description = "Get interface graphs";
	my $errormsg;

	# validate NIC NAME
	require Zevenet::Net::Interface;
	my @system_interfaces = &getInterfaceList();

	if ( !grep ( /^$iface$/, @system_interfaces ) )
	{
		# Error
		my $errormsg = "Nic interface not found.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 404, body => $body } );
	}

	# graph for this farm doesn't exist
	elsif ( !grep ( /${iface}iface/, &getGraphs2Show( "Network" ) ) )
	{
		$errormsg = "There is no rrd files yet.";
	}
	else
	{
		# Print Graph Function
		my @output;
		my $graph = &printGraph( "${iface}iface", 'd' )->{ img };
		push @output, { frequency => 'daily', graph => $graph };
		$graph = &printGraph( "${iface}iface", 'w' )->{ img };
		push @output, { frequency => 'weekly', graph => $graph };
		$graph = &printGraph( "${iface}iface", 'm' )->{ img };
		push @output, { frequency => 'monthly', graph => $graph };
		$graph = &printGraph( "${iface}iface", 'y' )->{ img };
		push @output, { frequency => 'yearly', graph => $graph };

		my $body = { description => $description, graphs => \@output };
		&httpResponse( { code => 200, body => $body } );
	}

	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 400, body => $body } );
}

# GET frequency interface graphs
sub get_frec_iface_graphs    #()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $iface       = shift;
	my $frequency   = shift;
	my $description = "Get interface graphs";
	my $errormsg;

	# validate NIC NAME
	require Zevenet::Net::Interface;
	my @system_interfaces = &getInterfaceList();

	if ( !grep ( /^$iface$/, @system_interfaces ) )
	{
		# Error
		my $errormsg = "Nic interface not found.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 404, body => $body } );
	}
	elsif ( !grep ( /${iface}iface/, &getGraphs2Show( "Network" ) ) )
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

		# Print Graph Function
		my $graph = &printGraph( "${iface}iface", $frequency )->{ img };
		my $body = { description => $description, graph => $graph };
		&httpResponse( { code => 200, body => $body } );
	}

	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 400, body => $body } );
}

# GET all farm graphs
sub get_all_farm_graphs    #()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my @farms = grep ( s/-farm//, &getGraphs2Show( "Farm" ) );
	my $body = {
		description =>
		  "These are the possible farm graphs, you'll be able to access to the daily, weekly, monthly or yearly graph",
		farms => \@farms
	};
	&httpResponse( { code => 200, body => $body } );
}

# GET farm graphs
sub get_farm_graphs    #()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $farmName    = shift;
	my $description = "Get farm graphs";
	my $errormsg;

	require Zevenet::Farm::Core;

	# this farm doesn't exist
	if ( !&getFarmExists( $farmName ) )
	{
		$errormsg = "$farmName doesn't exist.";
		my $body =
		  { description => $description, error => "true", message => $errormsg, };
		&httpResponse( { code => 404, body => $body } );
	}

	# graph for this farm doesn't exist
	elsif ( !grep ( /$farmName-farm/, &getGraphs2Show( "Farm" ) ) )
	{
		$errormsg = "There is no rrd files yet.";
	}
	else
	{
		# Print Graph Function
		my @output;
		my $graph = &printGraph( "$farmName-farm", 'd' )->{ img };
		push @output, { frequency => 'daily', graph => $graph };
		$graph = &printGraph( "$farmName-farm", 'w' )->{ img };
		push @output, { frequency => 'weekly', graph => $graph };
		$graph = &printGraph( "$farmName-farm", 'm' )->{ img };
		push @output, { frequency => 'monthly', graph => $graph };
		$graph = &printGraph( "$farmName-farm", 'y' )->{ img };
		push @output, { frequency => 'yearly', graph => $graph };

		my $body = { description => $description, graphs => \@output };
		&httpResponse( { code => 200, body => $body } );
	}

	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 400, body => $body } );
}

# GET frequency farm graphs
sub get_frec_farm_graphs    #()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $farmName    = shift;
	my $frequency   = shift;
	my $description = "Get farm graphs";
	my $errormsg;

	require Zevenet::Farm::Core;

	# this farm doesn't exist
	if ( !&getFarmExists( $farmName ) )
	{
		$errormsg = "$farmName doesn't exist.";
		my $body =
		  { description => $description, error => "true", message => $errormsg, };
		&httpResponse( { code => 404, body => $body } );
	}

	# graph for this farm doesn't exist
	elsif ( !grep ( /$farmName-farm/, &getGraphs2Show( "Farm" ) ) )
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

		# Print Graph Function
		my $graph = &printGraph( "$farmName-farm", $frequency )->{ img };
		my $body = { description => $description, graph => $graph };
		&httpResponse( { code => 200, body => $body } );
	}

	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 400, body => $body } );
}

#GET mount points list
sub list_disks    #()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	require Zevenet::Stats;

	my @mount_points;
	my $partitions = &getDiskPartitionsInfo();

	for my $key ( keys %{ $partitions } )
	{
		# mount point : root/mount_point
		push ( @mount_points, "root$partitions->{ $key }->{ mount_point }" );
	}

	@mount_points = sort @mount_points;

	my $body = {
				 description => "List disk partitions",
				 params      => \@mount_points,
	};

	&httpResponse( { code => 200, body => $body } );
}

#GET disk graphs for all periods
sub graphs_disk_mount_point_all    #()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $mount_point = shift;

	$mount_point =~ s/^root[\/]?/\//;

	require Zevenet::Stats;
	my $description = "Disk partition usage graphs";
	my $parts       = &getDiskPartitionsInfo();

	my ( $part_key ) =
	  grep { $parts->{ $_ }->{ mount_point } eq $mount_point } keys %{ $parts };

	unless ( $part_key )
	{
		# Error
		my $errormsg = "Mount point not found";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 404, body => $body } );
	}

	my $dev_id = $parts->{ $part_key }->{ rrd_id };

	# Success
	my @graphs = (
				   {
					  frequency => 'daily',
					  graph     => &printGraph( $dev_id, 'd' )->{ img }
				   },
				   {
					  frequency => 'weekly',
					  graph     => &printGraph( $dev_id, 'w' )->{ img }
				   },
				   {
					  frequency => 'monthly',
					  graph     => &printGraph( $dev_id, 'm' )->{ img }
				   },
				   {
					  frequency => 'yearly',
					  graph     => &printGraph( $dev_id, 'y' )->{ img }
				   },
	);

	my $body = {
				 description => $description,
				 graphs      => \@graphs,
	};

	&httpResponse( { code => 200, body => $body } );
}

#GET disk graph for a single period
sub graph_disk_mount_point_freq    #()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $mount_point = shift;
	my $frequency   = shift;

	$mount_point =~ s/^root[\/]?/\//;

	require Zevenet::Stats;
	my $description = "Disk partition usage graph";
	my $parts       = &getDiskPartitionsInfo();

	my ( $part_key ) =
	  grep { $parts->{ $_ }->{ mount_point } eq $mount_point } keys %{ $parts };

	unless ( $part_key )
	{
		# Error
		my $errormsg = "Mount point not found";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 404, body => $body } );
	}

	my $dev_id = $parts->{ $part_key }->{ rrd_id };
	my $freq   = $graph_period->{ $frequency };

	# Success
	my $body = {
				 description => $description,
				 frequency   => $frequency,
				 graph       => &printGraph( $dev_id, $freq )->{ img },
	};

	&httpResponse( { code => 200, body => $body } );
}

1;
