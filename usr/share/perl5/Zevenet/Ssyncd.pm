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

require Zevenet::Farm::Core;

# my $ssyncd_enabled = 'true';
# my $ssyncd_bin     = '/usr/local/zevenet/app/ssyncd/bin/ssyncd';
# my $ssyncdctl_bin  = '/usr/local/zevenet/app/ssyncd/bin/ssyncdctl';
# my $ssyncd_port    = 9999;

my $ssyncd_enabled = &getGlobalConfiguration( 'ssyncd_enabled' );

# farm up
sub setSsyncdFarmUp
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farm_name ) = @_;

	return 0 if !&getSsyncdRunning();

	my $ssyncdctl_bin = &getGlobalConfiguration( 'ssyncdctl_bin' );
	my $type          = &getFarmType( $farm_name );

	if ( $type eq 'l4xnat' )
	{
		require Zevenet::Farm::Base;
		my $farms_started = &getNumberOfFarmTypeRunning( 'l4xnat' );

		if ( $farms_started )
		{
			&zenlog( "Registering l4xnat farm $farm_name in ssyncd", "info", "cluster" );
			return &logAndRun( "$ssyncdctl_bin start nft $farm_name" );
		}
	}
	elsif ( $type =~ /^https?$/ )
	{
		&zenlog( "Registering http farm $farm_name in ssyncd", "info", "cluster" );
		return &logAndRun( "$ssyncdctl_bin start http $farm_name" );
	}

	return;
}

# farm down
sub setSsyncdFarmDown
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farm_name ) = @_;

	return 0 if !&getSsyncdRunning();

	my $ssyncdctl_bin = &getGlobalConfiguration( 'ssyncdctl_bin' );
	my $type          = &getFarmType( $farm_name );

	if ( $type eq 'l4xnat' )
	{
		require Zevenet::Farm::Base;
		my $farms_started = &getNumberOfFarmTypeRunning( 'l4xnat' );

		if ( $farms_started <= 1 )
		{
			&zenlog( "Unregistering l4xnat farm $farm_name in ssyncd", "info", "cluster" );
			return &logAndRun( "$ssyncdctl_bin stop nft $farm_name" );
		}
	}
	elsif ( $type =~ /^https?$/ )
	{
		&zenlog( "Unregistering http farm $farm_name in ssyncd", "info", "cluster" );
		return &logAndRun( "$ssyncdctl_bin stop http $farm_name" );
	}

	return;
}

#~ sub disable_ssyncd
sub setSsyncdDisabled
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $ssyncdctl_bin = &getGlobalConfiguration( 'ssyncdctl_bin' );

	# /ssyncdctl quit --> Exit ssyncd process
	my $ssync_cmd = "$ssyncdctl_bin quit";
	my $error;

	&logAndRun( "$ssync_cmd" ) if ( &getSsyncdRunning() );

	if ( &getSsyncdRunning() )
	{
		&logAndRun( "pkill ssyncd" );
		&zenlog( "ssyncd found still running and was killed", "info", "CLUSTER" );
	}

	return $error;
}

=begin nd
Function: getSsyncdRunning

	Check if the ssyncd process is running in the system

Parameters:
	none -.

Returns:
	Integer - It returns 0 if the process is not running, or another value if it is running

=cut

sub getSsyncdRunning
{
	my $pgrep = &getGlobalConfiguration( "pgrep" );
	my $err   = &logAndRunCheck( "$pgrep ssyncd" );
	return !$err;
}

sub setSsyncdBackup
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	&zenlog( "/// Starting setSsyncdBackup", "info", "CLUSTER" );

	return 0 if $ssyncd_enabled eq 'false';

	my $ssyncd_bin    = &getGlobalConfiguration( 'ssyncd_bin' );
	my $ssyncd_port   = &getGlobalConfiguration( 'ssyncd_port' );
	my $ssyncdctl_bin = &getGlobalConfiguration( 'ssyncdctl_bin' );

	if ( &getSsyncdRunning() )
	{
		# check mode
		# ./ssyncdctl show mode --> master|backup
		my $ssync_cmd = "$ssyncdctl_bin show mode";
		my $mode      = &logAndGet( $ssync_cmd );

		if ( $mode eq 'backup' )
		{
			&zenlog( "Ssyncd already in backup mode", "info", "CLUSTER" );

			# end function if already in backup mode
			return 0;
		}
		else
		{
			&zenlog( "Ssyncd current mode: $mode", "info", "CLUSTER" );
		}

		&setSsyncdDisabled();
	}

	my $cl_conf          = &getZClusterConfig();
	my $remote_node_name = &getZClusterRemoteHost();
	my $remote_node_ip   = $cl_conf->{ $remote_node_name }{ ip };

# Start Backup mode:
# ./ssyncd -d -B -p 9999 -a 172.16.1.1 --> start backup node and connect to master 172.16.1.1:9999

	my $error =
	  &logAndRun( "$ssyncd_bin -d -B -p $ssyncd_port -a $remote_node_ip" );

	return $error;
}

sub setSsyncdMaster
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	return 0 if $ssyncd_enabled eq 'false';

	my $ssyncd_bin    = &getGlobalConfiguration( 'ssyncd_bin' );
	my $ssyncd_port   = &getGlobalConfiguration( 'ssyncd_port' );
	my $ssyncdctl_bin = &getGlobalConfiguration( 'ssyncdctl_bin' );
	my $ssync_cmd;

	if ( &getSsyncdRunning() )
	{
		# check mode
		# ./ssyncdctl show mode --> master|slave
		$ssync_cmd = "$ssyncdctl_bin show mode";
		my $mode = &logAndGet( $ssync_cmd );

		if ( $mode eq 'master' )
		{
			&zenlog( "Ssyncd already in master mode", "info", "CLUSTER" );

			# end function if already in master mode
			return 0;
		}
		else
		{
			&zenlog( "Ssyncd current mode: $mode", "info", "CLUSTER" );
		}

		# Before changing to master mode:
		# ./ssyncdctl write http   --> Write http sessions data to l7 proxy
		# ./ssyncdctl write nft --> Write nft data to nftables
		my $error;

		$ssync_cmd = "$ssyncdctl_bin write http";
		$error     = &logAndRun( "$ssync_cmd" );
		&zenlog( "setSsyncdMaster ssyncd write http: $error > cmd: $ssync_cmd",
				 "error", "CLUSTER" )
		  if $error;

		$ssync_cmd = "$ssyncdctl_bin write nft";
		$error     = &logAndRun( "$ssync_cmd" );
		&zenlog( "setSsyncdMaster ssyncd write nft: $error > cmd: $ssync_cmd",
				 "error", "CLUSTER" )
		  if $error;

		&setSsyncdDisabled();
	}

	# Start Master mode:
	# ./ssyncd -d -M -p 9999 --> start master node

	$ssync_cmd = "$ssyncd_bin -d -M -p $ssyncd_port";
	my $error = &logAndRun( "$ssync_cmd" );
	&zenlog( "/// ssyncd as master: $error > cmd: $ssync_cmd", "info", "CLUSTER" );

	# ./ssyncdctl start http <farm>
	# ./ssyncdctl start nft <farm>

	sleep 1;

	for my $farm ( &getFarmNameList() )
	{
		my $type = &getFarmType( $farm );
		next if $type !~ /^(?:https?|l4xnat)$/;

		my $status = &getFarmStatus( $farm );
		next if $status ne 'up';

		my $error = &setSsyncdFarmUp( $farm );
	}
}

sub setSsyncd
{
	my $enable = shift;
	&setGlobalConfiguration( 'ssyncd_enabled', $enable );

	if ( $enable eq 'false' )
	{
		&setSsyncdDisabled();
	}
	elsif ( $enable eq 'true' )
	{
		include 'Zevenet::Cluster';
		my $node_role = &getZClusterNodeStatus();
		if ( $node_role eq 'master' )
		{
			&setSsyncdMaster();
		}
		elsif ( $node_role eq 'backup' )
		{
			&setSsyncdBackup();
		}
	}
	else
	{
		&zenlog( "The value '$enable' for the parameter 'ssyncd' is not valid.",
				 "error", "ssyncd" );
		return 1;
	}
	return 0;
}
1;
