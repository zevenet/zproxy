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

my $ssyncd_enabled = &getGlobalConfiguration('ssyncd_enabled');

# farm up
sub setSsyncdFarmUp
{
	my ( $farm_name ) = @_;

	return 0 if $ssyncd_enabled eq 'false';

	my $ssyncdctl_bin = &getGlobalConfiguration( 'ssyncdctl_bin' );
	my $type          = &getFarmType( $farm_name );

	if ( $type eq 'l4xnat' )
	{
		require Zevenet::Farm::Base;
		my $farms_started = &getNumberOfFarmTypeRunning( 'l4xnat' );

		if ( $farms_started )
		{
			return system( "$ssyncdctl_bin start recent >/dev/null" );
		}
	}
	elsif ( $type =~ /^https?$/ )
	{
		return system( "$ssyncdctl_bin start http $farm_name >/dev/null" );
	}

	return undef;
}


# farm down
sub setSsyncdFarmDown
{
	my ( $farm_name ) = @_;

	return 0 if $ssyncd_enabled eq 'false';

	my $ssyncdctl_bin = &getGlobalConfiguration( 'ssyncdctl_bin' );
	my $type          = &getFarmType( $farm_name );

	if ( $type eq 'l4xnat' )
	{
		require Zevenet::Farm::Base;
		my $farms_started = &getNumberOfFarmTypeRunning( 'l4xnat' );

		if ( $farms_started <= 1 )
		{
			return system( "$ssyncdctl_bin stop recent >/dev/null" );
		}
	}
	elsif ( $type =~ /^https?$/ )
	{
		return system( "$ssyncdctl_bin stop http $farm_name >/dev/null" );
	}

	return undef;
}

#~ sub disable_ssyncd
sub setSsyncdDisabled
{
	my $ssyncdctl_bin = &getGlobalConfiguration( 'ssyncdctl_bin' );

	# /ssyncdctl quit --> Exit ssyncd process
	my $ssync_cmd = "$ssyncdctl_bin quit";
	my $error;

	system( "$ssync_cmd >/dev/null" ) if `pgrep ssyncd`;

	if ( `pgrep ssyncd` )
	{
		system("pkill ssyncd");
		&zenlog("ssyncd found still running and was killed", "info", "CLUSTER");
	}

	return $error;
}

sub setSsyncdBackup
{
	&zenlog("/// Starting setSsyncdBackup", "info", "CLUSTER");

	return 0 if $ssyncd_enabled eq 'false';

	my $ssyncd_bin    = &getGlobalConfiguration( 'ssyncd_bin' );
	my $ssyncd_port   = &getGlobalConfiguration( 'ssyncd_port' );
	my $ssyncdctl_bin = &getGlobalConfiguration( 'ssyncdctl_bin' );

	if ( `pgrep ssyncd` )
	{
		# check mode
		# ./ssyncdctl show mode --> master|backup
		my $ssync_cmd = "$ssyncdctl_bin show mode";
		chomp( my ( $mode ) = `$ssync_cmd` );

		if ( $mode eq 'backup' )
		{
			&zenlog("Ssyncd already in backup mode", "info", "CLUSTER");

			# end function if already in backup mode
			return 0;
		}
		else
		{
			&zenlog("Ssyncd current mode: $mode", "info", "CLUSTER");
		}

		&setSsyncdDisabled();
	}

	my $cl_conf          = &getZClusterConfig();
	my $remote_node_name = &getZClusterRemoteHost();
	my $remote_node_ip   = $cl_conf->{ $remote_node_name }{ ip };

	# Start Backup mode:
	# ./ssyncd -d -B -p 9999 -a 172.16.1.1 --> start backup node and connect to master 172.16.1.1:9999

	my $error = system( "$ssyncd_bin -d -B -p $ssyncd_port -a $remote_node_ip" );

	return $error;
}

sub setSsyncdMaster
{
	return 0 if $ssyncd_enabled eq 'false';

	my $ssyncd_bin    = &getGlobalConfiguration( 'ssyncd_bin' );
	my $ssyncd_port   = &getGlobalConfiguration( 'ssyncd_port' );
	my $ssyncdctl_bin = &getGlobalConfiguration( 'ssyncdctl_bin' );
	my $ssync_cmd;

	if ( `pgrep ssyncd` )
	{
		# check mode
		# ./ssyncdctl show mode --> master|slave
		$ssync_cmd = "$ssyncdctl_bin show mode";
		chomp( my ( $mode ) = `$ssync_cmd` );

		if ( $mode eq 'master' )
		{
			&zenlog("Ssyncd already in master mode", "info", "CLUSTER");

			# end function if already in master mode
			return 0;
		}
		else
		{
			&zenlog("Ssyncd current mode: $mode", "info", "CLUSTER");
		}

		# Before changing to master mode:
		# ./ssyncdctl write http   --> Write http sessions data to pound
		# ./ssyncdctl write recent --> Write recent data to recent module
		my $error;

		$ssync_cmd = "$ssyncdctl_bin write http";
		my $error = system( "$ssync_cmd" );
		&zenlog("setSsyncdMaster ssyncd write http: $error > cmd: $ssync_cmd", "error", "CLUSTER") if $error;

		$ssync_cmd = "$ssyncdctl_bin write recent";
		my $error = system( "$ssync_cmd" );
		&zenlog("setSsyncdMaster ssyncd write recent: $error > cmd: $ssync_cmd", "error", "CLUSTER") if $error;

		&setSsyncdDisabled();
	}

	# Start Master mode:
	# ./ssyncd -d -M -p 9999 --> start master node

	$ssync_cmd = "$ssyncd_bin -d -M -p $ssyncd_port";
	my $error = system( "$ssync_cmd" );
	&zenlog("/// ssyncd as master: $error > cmd: $ssync_cmd", "info", "CLUSTER");

	# ./ssyncdctl start http <farm>
	# ./ssyncdctl start recent

	sleep 1;

	for my $farm ( &getFarmNameList() )
	{
		my $type = &getFarmType( $farm );
		next if $type !~ /^(?:https?|l4xnat)$/;

		my $status = &getFarmStatus( $farm );
		next if $status ne 'up';

		if ( $type eq 'l4xnat' )
		{
			my $error = &setSsyncdFarmUp( $farm );
		}
		else # http
		{
			my $error = &setSsyncdFarmUp( $farm );
		}
	}
}

sub setSsyncRestart
{
	my $status = &getZClusterNodeStatus();

	&setSsyncdDisabled();

	if ( $status eq "master" )
	{
		setSsyncdMaster();
	}
	elsif ( $status eq "backup" )
	{
		setSsyncdBackup();
	}
}

1;
