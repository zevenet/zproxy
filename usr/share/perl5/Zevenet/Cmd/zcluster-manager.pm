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

## zcluster-manager 1.0
#
# Usage:
#
# zcluster-manager enableZCluster
# zcluster-manager disableZCluster
# zcluster-manager setKeepalivedConfig
# zcluster-manager setConntrackdConfig
# zcluster-manager getZClusterRunning
# zcluster-manager getZClusterNodeStatus
# zcluster-manager getConntrackdRunning
# zcluster-manager getZClusterArpStatus
# zcluster-manager sync
# zcluster-manager notify_master
# zcluster-manager notify_backup
# zcluster-manager notify_fault
#
# zcluster-manager interface float-update
# zcluster-manager interface [start|stop|delete] <interface> [4|6]
#
# zcluster-manager gateway [update|delete] <interface> [4|6]
#
# zcluster-manager farm [start|stop|restart|delete] <farm>
#
# zcluster-manager ipds [start|stop|restart] <farm>
# zcluster-manager ipds_bl [start|stop|restart] <rule> [farm]
# zcluster-manager ipds_dos [start|stop|restart] <rule> [farm]
# zcluster-manager ipds_rbl [start|stop|restart] <rule> [farm]
#
# zcluster-manager rbac_user [add|delete|modify] <user>
# zcluster-manager rbac_group [add|delete|add_user|del_user] <group> [user]
#

use strict;
use warnings;
use feature 'say';
use Zevenet::Log;
use Zevenet::Config;
use Zevenet::Debug;

#~ my $primary_backup = "/usr/share/doc/conntrackd/examples/sync/primary-backup.sh";

#&zenlog( "ARGV:@ARGV" ) if &debug();
&zenlog( "ARGV:@ARGV:" );

my $object  = shift @ARGV // '';
my $command = shift @ARGV // '';

if ( !grep { $object eq $_ } ( qw(interface gateway farm ipds) ) )
{
	if ( $object =~ /Conntrackd/ )
	{
		include 'Zevenet::Conntrackd';
	}
	else
	{
		include 'Zevenet::Cluster';
	}
}

#~ if ( $object eq 'node' )
#~ {
if ( $object eq 'enableZCluster' )
{
	exit &enableZCluster();
}
elsif ( $object eq 'disableZCluster' )
{
	exit &disableZCluster();
}
elsif ( $object eq 'setKeepalivedConfig' )
{
	exit &setKeepalivedConfig();
}
elsif ( $object eq 'setConntrackdConfig' )
{
	exit &setConntrackdConfig();
}
elsif ( $object eq 'getZClusterRunning' )
{
	#~ say &getZClusterRunning();
	say ( ( &getZClusterRunning() ) ? '1' : '0' );

	#~ say ( &getZClusterRunning() )? 'true': 'false';
	exit 0;
}
elsif ( $object eq 'getZClusterNodeStatus' )
{
	say &getZClusterNodeStatus();
	exit 0;
}
elsif ( $object eq 'getConntrackdRunning' )
{
	#~ say &getConntrackdRunning();
	say ( ( &getConntrackdRunning() ) ? '1' : '0' );
	exit 0;
}
elsif ( $object eq 'getZClusterArpStatus' )
{
	require Zevenet::Net::Interface;

	my $status = 'ok';

	if ( !&getZClusterRunning() )
	{
		say 'ko';
		exit 0;
	}

	my $node_role       = &getZClusterNodeStatus();
	my @arptables_lines = `arptables -L INPUT`;

	for my $if_ref ( &getInterfaceTypeList( 'virtual' ) )
	{
		my $if_dropped =
		  grep { $_ =~ /^-j DROP -d $if_ref->{ addr } $/ } @arptables_lines;

		if ( $node_role ne 'master' && !$if_dropped )
		{
			$status = 'ko';
			last;
		}
		elsif ( $node_role eq 'master' && $if_dropped )
		{
			$status = 'ko';
			last;
		}
	}

	say $status;
	exit 0;
}
elsif ( $object eq 'sync' )
{
	my $configdir = &getGlobalConfiguration( 'configdir' );
	my $rttables  = &getGlobalConfiguration( 'rttables' );

	&zenlog( "Syncing $configdir" );
	&runSync( $configdir );

	&zenlog( "Syncing $rttables" );
	&runSync( $rttables );
}
elsif ( $object eq 'notify_master' )
{
	exit &setNodeStatusMaster();
}
elsif ( $object eq 'notify_backup' )
{
	exit &setNodeStatusBackup();
}
elsif ( $object eq 'notify_fault' )
{
	exit &setNodeStatusMaintenance();
}

#~ }

# farm commands
if ( $object eq 'farm' )
{
	require Zevenet::Farm::Action;

	if ( $command eq 'start' )
	{
		my $farm_name = shift @ARGV;
		&quit( "Missing farm name argument" ) if !$farm_name;

		my $status = &_runFarmStart( $farm_name );

		# Start ipds rules
		include 'Zevenet::IPDS::Base';
		&runIPDSStartByFarm( $farm_name );

		exit $status;
	}
	elsif ( $command eq 'stop' )
	{
		my $farm_name = shift @ARGV;
		&quit( "Missing farm name argument" ) if !$farm_name;

		# Stop ipds rules
		include 'Zevenet::IPDS::Base';
		&runIPDSStopByFarm( $farm_name );

		exit &_runFarmStop( $farm_name );
	}
	elsif ( $command eq 'restart' )
	{
		my $farm_name = shift @ARGV;
		&quit( "Missing farm name argument" ) if !$farm_name;

		&_runFarmStop( $farm_name );
		my $status = &_runFarmStart( $farm_name );

		exit $status;
	}
	elsif ( $command eq 'delete' )
	{
		my $farm_name = shift @ARGV;
		&quit( "Missing farm name argument" ) if !$farm_name;

		exit &runFarmDelete( $farm_name );
	}
	else
	{
		&quit( "Unrecognized farm command" );
	}
}

# zcluster-manager rbac_user [add|delete|modify] <user>
# zcluster-manager rbac_group [add|delete|add_user|del_user] <group> [user]
if ( $object =~ /^rbac_(user|group)/ )
{
	my $module = $1;
	if ( $module eq "user" )
	{
		include 'Zevenet::RBAC::User::Action';
		my ( $user ) = @ARGV;
		&updateRBACUser( $user, $command );
	}
	if ( $module eq "group" )
	{
		include 'Zevenet::RBAC::Group::Action';
		my ( $group, $user ) = @ARGV;
		&updateRBACGroup( $group, $command, $user );
	}

}

# ipds commands
#  object = ipds
if ( $object eq "ipds" )
{
	include 'Zevenet::IPDS::Base';
	my $farm_name = shift @ARGV;

	# stop DOS rules
	if ( $command eq "stop" )
	{
		&runIPDSStopByFarm( $farm_name );
	}

	# start DOS rules
	elsif ( $command eq "start" )
	{
		&runIPDSStartByFarm( $farm_name );
	}

	# reload DOS rules
	else
	{
		&runIPDSRestartByFarm( $farm_name );
	}
}

#  object = ipds_(rbl|bl|dos)
if ( $object =~ /^ipds_(rbl|bl|dos)/ )
{
	my $module    = $1;
	my $rule_name = shift @ARGV;
	my $farm_name = shift @ARGV;

	if ( $module eq 'bl' )
	{
		include 'Zevenet::IPDS::Blacklist::Actions';

		if ( $farm_name )
		{
			# stop BL rules
			if ( $command eq "stop" )
			{
				&runBLStop( $rule_name, $farm_name );
			}

			# start BL rules
			elsif ( $command eq "start" )
			{
				&runBLStart( $rule_name, $farm_name );
			}

			# reload BL rules
			else
			{
				&runBLRestart( $rule_name, $farm_name );
			}
		}
		else
		{
			# stop BL rules
			if ( $command eq "stop" )
			{
				&runBLStopByRule( $rule_name );
			}

			# start BL rules
			elsif ( $command eq "start" )
			{
				&runBLStartByRule( $rule_name );
			}

			# reload BL rules
			else
			{
				&runBLRestartByRule( $rule_name );
			}
		}

		exit 0;
	}
	elsif ( $module eq 'dos' )
	{
		include 'Zevenet::IPDS::DoS::Actions';

		if ( $farm_name )
		{
			# stop DOS rules
			if ( $command eq "stop" )
			{
				&runDOSStop( $rule_name, $farm_name );
			}

			# start DOS rules
			elsif ( $command eq "start" )
			{
				&runDOSStart( $rule_name, $farm_name );
			}

			# reload DOS rules
			else
			{
				&runDOSRestart( $rule_name, $farm_name );
			}
		}
		else
		{
			# stop DOS rules
			if ( $command eq "stop" )
			{
				&runDOSStopByRule( $rule_name );
			}

			# start DOS rules
			elsif ( $command eq "start" )
			{
				&runDOSStartByRule( $rule_name );
			}

			# reload DOS rules
			else
			{
				&runDOSRestartByRule( $rule_name );
			}
		}

		exit 0;
	}
	elsif ( $module eq 'rbl' )
	{
		include 'Zevenet::IPDS::RBL::Actions';

		if ( $farm_name )
		{
			# stop RBL rules
			if ( $command eq "stop" )
			{
				&runRBLStop( $rule_name, $farm_name );
			}

			# start RBL rules
			elsif ( $command eq "start" )
			{
				&runRBLStart( $rule_name, $farm_name );
			}

			# reload RBL rules
			else
			{
				&runRBLRestart( $rule_name, $farm_name );
			}
		}
		else
		{
			# stop RBL rules
			if ( $command eq "stop" )
			{
				&runRBLStopByRule( $rule_name );
			}

			# start RBL rules
			elsif ( $command eq "start" )
			{
				&runRBLStartByRule( $rule_name );
			}

			# reload RBL rules
			else
			{
				&runRBLRestartByRule( $rule_name );
			}
		}

		exit 0;
	}

	else
	{
		&quit( "Unrecognized ipds command" );
	}
}

# interface commands
# WARNING: only virtual interfaces are handled
if ( $object eq 'interface' )
{
	require Zevenet::Net;

	if ( $command eq 'float-update' )
	{
		require Zevenet::Farm::L4xNAT::Config;
		include 'Zevenet::Cluster';

		&reloadL4FarmsSNAT();
		exit 0;
	}

	# common interface initial tasks
	my $if_name = shift @ARGV;      # virtual interface name
	my $ip_v = shift @ARGV // 4;    # ip version: 4 or 6 (default: 4)

	# must have an interface argument
	&quit( "Interface action not defined." ) if !$if_name;
	&quit( "Only virtual interfaces are supported." )
	  if $if_name !~ /.+:.+/;       # only accept virtual interfaces

	my $if_ref = &getInterfaceConfig( $if_name, $ip_v );

	exit 1 if !$if_ref;

	my $status;

	# define different interface actions

	# configures ip
	if ( $command eq 'start' )
	{
		include 'Zevenet::Cluster';
		require Zevenet::Farm::L4xNAT::Config;

		&disableInterfaceDiscovery( $if_ref );    # backup node only
		$status = &addIp( $if_ref );
		$status = &applyRoutes( "local", $if_ref ) if $status == 0;
		&reloadL4FarmsSNAT();
		exit $status;
	}
	elsif ( $command eq 'stop' )                  # flush ip
	{
		include 'Zevenet::Cluster';
		require Zevenet::Farm::L4xNAT::Config;

		$status = &delIp( $$if_ref{ name }, $$if_ref{ addr }, $$if_ref{ mask } );
		&reloadL4FarmsSNAT();
		&enableInterfaceDiscovery( $if_ref );
		exit $status;
	}
	elsif ( $command eq 'delete' )                # remove interface stats and other
	{
		$status = &delIf( $if_name );
		exit $status;
	}
}

if ( $object eq 'gateway' )
{
	my $iface_name = shift @ARGV;
	my $ip_version = shift @ARGV;

	require Zevenet::Net;

	my $status;

	if ( $command eq 'update' )
	{
		my $if_ref = getInterfaceConfig( $iface_name, $ip_version );

		exit 1 if !$if_ref;

		$status = &applyRoutes( "global", $if_ref, $if_ref->{ gateway } );
		&reloadL4FarmsSNAT();

		exit $status;
	}
	elsif ( $command eq 'delete' )    # remove interface stats and other
	{
		my $defaultgwif = &getGlobalConfiguration( 'defaultgwif' );
		my $if_ref = getInterfaceConfig( $defaultgwif, $ip_version );

		exit 1 if !$if_ref;

		$status = &delRoutes( "global", $if_ref );
		exit $status;
	}
}

sub setNodeStatusMaster
{
	&zenlog( "############# Starting setNodeStatusMaster" );

	my $node_status = &getZClusterNodeStatus();
	&zenlog( "Cluster ==== node_status: $node_status ===> Master" );

	if ( &getZClusterNodeStatus() eq 'master' )
	{
		&zenlog( "Node is already master" );
		return 0;
	}

	&zenlog( "Switching node to master" );
	&setZClusterNodeStatus( 'master' );

	require Zevenet::Net::Interface;
	require Zevenet::Farm::Core;
	require Zevenet::Farm::Base;
	include 'Zevenet::Ssyncd';

	# conntrackd sync
	my $primary_backup = &getGlobalConfiguration( 'primary_backup' );
	system ( "$primary_backup primary" );

	# Ssyncd
	&setSsyncdMaster();

	# flush arp rules
	my $rc = &enableAllInterfacesDiscovery();

	# announce ips ( arp and neigh )
	my @configured_interfaces = @{ &getConfigInterfaceList() };

	for my $if_ref ( @configured_interfaces )
	{
		next unless $if_ref->{ type } eq 'virtual';
		&broadcastInterfaceDiscovery( $if_ref );
	}

	# start sync
	my $zenino = &getGlobalConfiguration( 'zenino' );
	system ( "$zenino &" );

	# start farmguardians
	my @farmsf = &getFarmList();

	foreach my $ffile ( @farmsf )
	{
		my $farmname = &getFarmName( $ffile );
		my $bstatus  = &getFarmBootStatus( $farmname );

		if ( $bstatus eq "up" )
		{
			require Zevenet::FarmGuardian;

			#~ print "  * Starting Farm $farmname:";
			#~ $status = &_runFarmStart( $farmname, "false" );

			#farmguardian configured and up?
			my $fgstatus = &getFarmGuardianStatus( $farmname );

			if ( ( $bstatus eq 'up' ) && ( $fgstatus == 1 ) )
			{
				my $error_code = &runFarmGuardianStart( $farmname, "" );
				if ( $error_code )
				{
					&zenlog( "Some error happened starting farmguardian for farm $farmname" );
				}
			}
		}
	}

	&zenlog( "End of setNodeStatusMaster ###################" );

	return 0;
}

sub setNodeStatusBackup
{
	&zenlog( "############### Starting setNodeStatusBackup" );

	my $node_status = &getZClusterNodeStatus();
	&zenlog( "Cluster ==== node_status: $node_status ===> Backup" );

	if ( $node_status eq 'maintenance' )
	{
		&zenlog( "Node on maintenance mode. Setting maintenance mode instead" );
		&setNodeStatusMaintenance();

		return 0;
	}
	elsif ( $node_status eq 'backup' )
	{
		# FIXME: Deprecate this condition if it is not required.
		&zenlog( "Node is already backup" );

		#~ return 0;
	}
	else
	{
		&zenlog( "Switching node to backup" );
		&setZClusterNodeStatus( 'backup' );
	}

	require Zevenet::Net::Interface;
	include 'Zevenet::Ssyncd';

	# conntrackd
	my $primary_backup = &getGlobalConfiguration( 'primary_backup' );
	system ( "$primary_backup backup >/dev/null" );

	# Ssyncd
	&setSsyncdBackup();

	my $zenino = &getGlobalConfiguration( 'zenino' );
	system ( "$zenino stop &" ) unless system ( 'pgrep zeninotify >/dev/null' );

	# stop farmguardians
	my $pids = `pgrep farmguardian`;
	$pids =~ s/\n/ /g;
	system ( "kill $pids" ) if $pids;

	# block/disable ip announces ( arp and neigh )
	my @configured_interfaces = @{ &getConfigInterfaceList() };

	for my $if_ref ( @configured_interfaces )
	{
		next unless $if_ref->{ type } eq 'virtual';
		&disableInterfaceDiscovery( $if_ref );
	}

	&zenlog( "End of setNodeStatusBackup ####################" );

	return 0;
}

sub setNodeStatusMaintenance
{
	&zenlog( "############### Starting setNodeStatusMaintenance" );

	include 'Zevenet::Ssyncd';
	require Zevenet::Net::Interface;

	my $node_status = &getZClusterNodeStatus();
	&zenlog( "Cluster ==== node_status: $node_status ===> Maintenance" );

	&zenlog( "Switching node to under maintenance" );
	&setZClusterNodeStatus( 'maintenance' );

	# conntrackd
	my $primary_backup = &getGlobalConfiguration( 'primary_backup' );
	system ( "$primary_backup fault" );

	# Ssyncd
	&setSsyncdDisabled();

	# stop zeninotify
	my $zenino = &getGlobalConfiguration( 'zenino' );
	system ( "$zenino stop" );

	# stop farmguardian
	system ( "pkill farmguardian" );

	# block/disable ip announces ( arp and neigh )
	my @configured_interfaces = @{ &getConfigInterfaceList() };
	for my $if_ref ( @configured_interfaces )
	{
		next if $if_ref->{ vini } eq '';
		&disableInterfaceDiscovery( $if_ref );
	}

	&zenlog( "End of setNodeStatusMaintenance ################" );

	return 0;
}

sub quit
{
	my $msg = shift;

	if ( $msg )
	{
		&zenlog( $msg );
		print "$msg\n";
	}

	exit 1;
}

#~ &zenlog( `grep RSS /proc/$$/status` );
