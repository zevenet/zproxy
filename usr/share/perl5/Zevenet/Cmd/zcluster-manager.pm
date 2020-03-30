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
# zcluster-manager routing_rule [stop|start] <id>
# zcluster-manager routing_table [stop|start] <table> <route_id>
# zcluster-manager routing_table [reload] <table>
#
# zcluster-manager gateway [update|delete] <interface> [4|6]
#
# zcluster-manager farm [start|stop|restart|delete|reload] <farm> [backend <backendid>]
#
# zcluster-manager fg 		[stop|start|stop] <fg>
# zcluster-manager fg_farm 	[stop|start|stop] <farm> [<service>]
#
# zcluster-manager ipds [restart]
# zcluster-manager ipds [start|stop|restart] <farm>
# zcluster-manager ipds_bl [start|stop|restart] <rule> [farm]
# zcluster-manager ipds_dos [start|stop|restart] <rule> [farm]
# zcluster-manager ipds_rbl [start|stop|restart] <rule> [farm]
# zcluster-manager ipds_waf [reload_farm|reload_rule] <rule|farm>
#
# zcluster-manager rbac_user [add|delete|modify] <user>
# zcluster-manager rbac_group [add|delete|add_user|del_user] <group> [user]
#

use strict;

use feature 'say';
use Zevenet::Log;
use Zevenet::Config;
use Zevenet::Debug;

&zenlog( "zcluster-manager args: @ARGV", 'debug', 'cluster' );

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
	require Zevenet::Nft;

	my $status = 'ok';

	if ( !&getZClusterRunning() )
	{
		say 'ko';
		exit 0;
	}

	my $node_role = &getZClusterNodeStatus();

	for my $if_ref ( &getInterfaceTypeList( 'virtual' ) )
	{
		my $if_dropped = &execNft(
								   "check",
								   "netdev cluster",
								   "cl-" . $if_ref->{ parent },
								   "$if_ref->{ addr }"
		);

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
elsif ( $object eq 'disableSshCluster' )
{
	include 'Zevenet::Aws';
	return &disableSshCluster();
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
elsif ( $object eq 'enable_ssyncd' )
{
	include 'Zevenet::Ssyncd';
	&setSsyncd( 'true' );
}
elsif ( $object eq 'disable_ssyncd' )
{
	include 'Zevenet::Ssyncd';
	&setSsyncd( 'false' );
}
elsif ( $object eq 'enable_proxyng' )
{
	include 'Zevenet::System::Global';
	&setSsyncdNG( 'true' );
	&setProxyNG( 'true' );
}
elsif ( $object eq 'disable_proxyng' )
{
	include 'Zevenet::System::Global';
	&setSsyncdNG( 'false' );
	&setProxyNG( 'false' );
}

# farm commands
if ( $object eq 'farm' )
{
	my $farm_name = shift @ARGV;
	&quit( "Missing farm name argument" ) if !$farm_name;

	my $backend = shift @ARGV // '';
	if ( $backend eq "backend" )
	{
		$backend = shift @ARGV // '';
	}

	require Zevenet::Farm::Action;

	if ( $command eq 'start' )
	{
		my $status = &_runFarmStart( $farm_name );

		# Start ipds rules
		include 'Zevenet::IPDS::Base';
		&runIPDSStartByFarm( $farm_name );

		exit $status;
	}
	elsif ( $command eq 'stop' )
	{
		# Stop ipds rules
		include 'Zevenet::IPDS::Base';
		&runIPDSStopByFarm( $farm_name );

		exit &_runFarmStop( $farm_name );
	}
	elsif ( $command eq 'restart' )
	{
		&_runFarmStop( $farm_name );
		my $status = &_runFarmStart( $farm_name );

		exit $status;
	}
	elsif ( $command eq 'reload' )
	{
		&_runFarmReload( $farm_name );
		my $status = &_runFarmReload( $farm_name );

		exit $status;
	}

	elsif ( $command eq 'delete' && $backend ne "" )
	{
		include 'Zevenet::Farm::Core';
		include 'Zevenet::Farm::Backend';
		exit &runFarmServerDelete( $backend, $farm_name );
	}
	elsif ( $command eq 'delete' )
	{
		&_runFarmStop( $farm_name );
		exit &runFarmDelete( $farm_name );
	}
	else
	{
		&quit( "Unrecognized farm command" );
	}
}

&zenlog( "checking zcluster-manager object: $object", 'debug', 'cluster' );

# zcluster-manager fg 		[stop|start|stop] <fg>
# zcluster-manager fg_farm 	[stop|start|stop] <farm> [service]
if ( $object =~ /^fg(_farm)?/ )
{
	my $module = $1;
	my ( $obj, $srv ) = @ARGV;

	#~ &zenlog ("module: $module, cmd: $command, obj: $obj");

	require Zevenet::FarmGuardian;
	if ( $module )
	{
		if ( $command eq 'start' )
		{
			&runFGFarmStart( $obj, $srv );
		}
		elsif ( $command eq 'stop' )
		{
			&runFGFarmStop( $obj, $srv );
		}
		elsif ( $command eq 'restart' )
		{
			&runFGFarmRestart( $obj, $srv );
		}
	}
	else
	{
		if ( $command eq 'start' )
		{
			&runFGStart( $obj );
		}
		elsif ( $command eq 'stop' )
		{
			&runFGStop( $obj );
		}
		elsif ( $command eq 'restart' )
		{
			&runFGRestart( $obj );
		}
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

	if ( !defined $farm_name )
	{
		include 'Zevenet::Farm::Base';
		foreach $farm_name ( &getFarmRunning() )
		{
			&runIPDSRestartByFarm( $farm_name );
		}
	}
	else
	{
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
}

#  object = ipds_(rbl|bl|dos)
if ( $object =~ /^ipds_(rbl|bl|dos|waf)/ )
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
	elsif ( $module eq 'waf' )
	{
		include 'Zevenet::IPDS::WAF::Runtime';

		# zcluster-manager ipds_waf [reload_farm|reload_rule] <rule|farm>
		if ( $command eq 'reload_rule' )
		{
			&reloadWAFByRule( $rule_name );
		}
		elsif ( $command eq 'reload_farm' )
		{
			# although the parameter is called rule, it is a farm name when the
			# command to execute is reload_farm
			&reloadWAFByFarm( $rule_name );
		}
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
	require Zevenet::Net::Interface;
	require Zevenet::Net::Core;
	require Zevenet::Net::Route;

	if ( $command eq 'float-update' )
	{
		require Zevenet::Farm::Config;
		&reloadFarmsSourceAddress();
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
		require Zevenet::Farm::Config;

		&disableInterfaceDiscovery( $if_ref );    # backup node only
		$status = &addIp( $if_ref );
		$status = &applyRoutes( "local", $if_ref ) if $status == 0;
		&reloadFarmsSourceAddress();
		exit $status;
	}
	elsif ( $command eq 'stop' )                  # flush ip
	{
		include 'Zevenet::Cluster';
		require Zevenet::Farm::Config;
		$status = &delIp( $$if_ref{ name }, $$if_ref{ addr }, $$if_ref{ mask } );
		&reloadFarmsSourceAddress();
		&enableInterfaceDiscovery( $if_ref );
		exit $status;
	}
	elsif ( $command eq 'delete' )                # remove interface stats and other
	{
		$status = &delIf( $if_name );
		exit $status;
	}
}

if ( $object =~ /^routing_(rule|table)/ )
{
	my $submod = $1;
	my ( $id, $route ) = @ARGV;
	my $err = 1;

	include 'Zevenet::Net::Routing';

	if ( $submod eq 'rule' )
	{
		my $conf = &getRoutingRulesConf( $id );
		my $act;

		if ( $command eq 'start' )
		{
			$act = 'add';
		}
		elsif ( $command eq 'stop' )
		{
			$act = 'del';
		}
		$err = &setRule( $act, $conf );
	}
	elsif ( $submod eq 'table' )
	{
		if ( $command eq 'reload' )
		{
			$id =~ s/table_//;
			$err = &reloadRoutingTable( $id );
		}
		elsif ( $command eq 'stop' )
		{
			my $conf = &getRoutingTableConf( $id, $route );
			$err = &setRoute( 'del', $conf->{ raw } );
		}
		elsif ( $command eq 'start' )
		{
			my $conf = &getRoutingTableConf( $id, $route );
			$err = &setRoute( 'add', $conf->{ raw } );
		}
	}

	exit $err;
}

if ( $object eq 'gateway' )
{
	my $iface_name = shift @ARGV;
	my $ip_version = shift @ARGV;

	require Zevenet::Net::Interface;
	require Zevenet::Net::Core;
	require Zevenet::Net::Route;

	my $status;

	if ( $command eq 'update' )
	{
		my $if_ref = getInterfaceConfig( $iface_name, $ip_version );

		exit 1 if !$if_ref;

		$status = &applyRoutes( "global", $if_ref, $if_ref->{ gateway } );
		require Zevenet::Farm::Config;
		&reloadFarmsSourceAddress();

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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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

	my $provider = &getGlobalConfiguration( 'cloud_provider' );
	if ( $provider eq "aws" )
	{
		include 'Zevenet::Aws';
		&zenlog( "Reassigning AWS virtual interfaces" );
		my $error = &reassignInterfaces();
		if ( $error )
		{
			&zenlog( "There was a problem to reassign interfaces in AWS",
					 "error", "CLUSTER" );
		}
	}

	require Zevenet::Net::Interface;
	require Zevenet::Farm::Core;
	require Zevenet::Farm::Base;
	include 'Zevenet::Ssyncd';

	# conntrackd sync
	my $primary_backup = &getGlobalConfiguration( 'primary_backup' );
	&logAndRun( "$primary_backup primary" );

	# Ssyncd
	&setSsyncdMaster();

	# flush arp rules
	&enableAllInterfacesDiscovery();

	# announce ips ( arp and neigh )
	my @configured_interfaces = @{ &getConfigInterfaceList() };

	for my $if_ref ( @configured_interfaces )
	{
		next unless $if_ref->{ type } eq 'virtual';
		&broadcastInterfaceDiscovery( $if_ref );
	}

	# start sync
	my $zenino = &getGlobalConfiguration( 'zenino' );
	{
		local %ENV = ( %ENV );
		$ENV{ _ } = $zenino;

		&logAndRunBG( "$zenino" );
	}

	# put interface as up
	my $maint_if = 'cl_maintenance';
	my $ip_bin   = &getGlobalConfiguration( 'ip_bin' );
	&logAndRun( "$ip_bin link set $maint_if up" );

	# start farmguardians
	require Zevenet::FarmGuardian;
	foreach my $fg ( &getFGList() )
	{
		&runFGStart( $fg );
	}

	&zenlog( "End of setNodeStatusMaster ###################" );

	return 0;
}

sub setNodeStatusBackup
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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
	include 'Zevenet::Cluster';

	my $zenino_proc = &get_zeninotify_process();

	# conntrackd
	my $primary_backup = &getGlobalConfiguration( 'primary_backup' );
	&logAndRun( "$primary_backup backup" );

	# Ssyncd
	&setSsyncdBackup();

	# put interface as up
	my $maint_if = 'cl_maintenance';
	my $ip_bin   = &getGlobalConfiguration( 'ip_bin' );
	&logAndRun( "$ip_bin link set $maint_if up" );

	unless ( &logAndRunCheck( $zenino_proc ) )
	{
		my $zenino = &getGlobalConfiguration( 'zenino' );

		local %ENV = ( %ENV );
		$ENV{ _ } = $zenino;

		&logAndRun( "$zenino stop &" );
	}

	# stop farmguardians
	if ( &logAndRunCheck( 'pgrep farmguardian' ) )
	{
		&logAndRun( "pkill farmguardian" );
	}

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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	&zenlog( "############### Starting setNodeStatusMaintenance" );

	include 'Zevenet::Ssyncd';
	include 'Zevenet::Cluster';
	require Zevenet::Net::Interface;

	my $zenino_proc = &get_zeninotify_process();
	my $node_status = &getZClusterNodeStatus();
	&zenlog( "Cluster ==== node_status: $node_status ===> Maintenance" );

	&zenlog( "Switching node to under maintenance" );
	&setZClusterNodeStatus( 'maintenance' );

	# put interface as down
	my $maint_if = 'cl_maintenance';
	my $ip_bin   = &getGlobalConfiguration( 'ip_bin' );
	&logAndRun( "$ip_bin link set $maint_if down" );

	# conntrackd
	my $primary_backup = &getGlobalConfiguration( 'primary_backup' );
	&logAndRun( "$primary_backup fault" );

	# Ssyncd
	&setSsyncdDisabled();

	# stop zeninotify
	unless ( &logAndRunCheck( $zenino_proc ) )
	{
		my $zenino = &getGlobalConfiguration( 'zenino' );

		local %ENV = ( %ENV );
		$ENV{ _ } = $zenino;

		&logAndRun( "$zenino stop" );
	}

	# stop farmguardian
	if ( &logAndRunCheck( 'pgrep farmguardian' ) )
	{
		&logAndRun( "pkill farmguardian" );
	}

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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $msg = shift;

	if ( $msg )
	{
		&zenlog( $msg );
		print "$msg\n";
	}

	exit 1;
}

#~ &zenlog( `grep RSS /proc/$$/status` );

1;

