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
use warnings;
use Zevenet::Log;

# error codes:
#
# valid values for farms:
#swcert = -1 ==> Cert valid (>365) and it's expired
#swcert = 0 ==> OK
#
# not valid values for farms:
#swcert = 1 ==> There isn't certificate
#swcert = 2 ==> Cert isn't signed OK
#swcert = 3 ==> Cert test and it's expired
my $swcert = &certcontrol();
my $enable_fg = 1;


sub getEnableFarmGuardian
{
	return $enable_fg;
}

sub setSystemOptimizations
{
	my $appliance_version = &getApplianceVersion();
	&zenlog ("Appliance version: $appliance_version");

	#### Starts node tuning ####
	my $recent_ip_list_tot = &getGlobalConfiguration('recent_ip_list_tot');
	my $recent_ip_list_hash_size = &getGlobalConfiguration('recent_ip_list_hash_size');
	system ( '/sbin/rmmod xt_recent >/dev/null 2>&1' );
	system (
		"/sbin/modprobe xt_recent ip_list_tot=$recent_ip_list_tot ip_list_hash_size=$recent_ip_list_hash_size >/dev/null 2>&1"
	);

	system ( 'echo "22500" > /sys/module/nf_conntrack/parameters/hashsize' );

	# Set system tuning with sysctl
	my %sysctl = (
		"fs.file-max"                        => "100000",
		"kernel.threads-max"                 => "120000",                # packetbl
		"kernel.pid_max"                     => "200000",                # packetbl
		"vm.max_map_count"                   => "1048576",
		"vm.swappiness"                      => "10",
		"net.ipv4.conf.all.log_martians"     => "0",
		"net.ipv4.ip_local_port_range"       => "1024 65535",
		"net.ipv4.tcp_max_tw_buckets"        => "2000000",
		"net.ipv4.tcp_max_syn_backlog"       => "30000",
		"net.ipv4.tcp_window_scaling"        => "1",
		"net.ipv4.tcp_timestamps"            => "0",
		"net.ipv4.tcp_rmem"                  => "4096 87380 16777216",
		"net.ipv4.tcp_wmem"                  => "4096 65536 16777216",
		"net.ipv4.udp_rmem_min"              => "65536",
		"net.ipv4.udp_wmem_min"              => "65536",
		"net.ipv4.tcp_low_latency"           => "1",
		"net.ipv4.tcp_tw_reuse"              => "1",
		"net.ipv4.tcp_tw_recycle"            => "0",
		"net.ipv4.tcp_keepalive_time"        => "512",
		"net.ipv4.tcp_fin_timeout"           => "5",
		"net.ipv4.inet_peer_maxttl"          => "5",
		"net.ipv4.tcp_keepalive_probes"      => "5",
		"net.ipv4.tcp_slow_start_after_idle" => "0",
		#"net.ipv4.netfilter.ip_conntrack_udp_timeout"        => "2",
		#"net.ipv4.netfilter.ip_conntrack_udp_timeout_stream" => "2",
		"net.netfilter.nf_conntrack_tcp_timeout_time_wait"   => "2",
		"net.netfilter.nf_conntrack_max"                     => "180000",
		"net.netfilter.nf_conntrack_tcp_loose"               => "0",
		"net.core.rmem_max"                                  => "16777216",
		"net.core.wmem_max"                                  => "16777216",
		"net.core.rmem_default"                              => "16777216",
		"net.core.wmem_default"                              => "16777216",
		"net.core.optmem_max"                                => "40960",
		"net.ipv4.tcp_keepalive_intvl"                       => "15",
		"net.core.netdev_max_backlog"                        => "50000",
		"net.core.somaxconn"                                 => "3000",
		"net.ipv4.ip_nonlocal_bind"                          => "1",
	);

	# In Stretch Debian not appear "net.ipv4.netfilter.ip_conntrack*" variables
	# Debian stretch is used in Zevenet 5000
	$appliance_version =~ /[\w+] (\d)\d+/;
	$appliance_version = $1;

	#  ZVA lower than 5000
	if ( $appliance_version < 5 )
	{
		$sysctl{ "net.ipv4.netfilter.ip_conntrack_tcp_timeout_time_wait" }   = "2";
		$sysctl{ "net.ipv4.netfilter.ip_conntrack_tcp_timeout_established" } = "86400";
		$sysctl{ "net.ipv4.netfilter.ip_conntrack_udp_timeout" } = "2";
		$sysctl{ "net.ipv4.netfilter.ip_conntrack_udp_timeout_stream" } = 2;
	}
	#  ZVA equal or higher than 5000
	else
	{
		$sysctl{ "net.netfilter.nf_conntrack_tcp_timeout_established" } = "86400";
		$sysctl{ "net.netfilter.nf_conntrack_udp_timeout" }  = "2";
		$sysctl{ "net.netfilter.nf_conntrack_udp_timeout_stream" } = "2";

	}

	# apply tuning to config file
	tie my @sysctl_file, 'Tie::File', "/etc/sysctl.conf";
	@sysctl_file = grep !/^net\.ipv4\.tcp_tw_recycle/, @sysctl_file;

	foreach my $key ( sort keys %sysctl )
	{
		# escape dots for regular expression
		my $quoted_key = quotemeta ( $key );

		if ( !grep ( /^$key = $sysctl{$key}/, @sysctl_file ) )
		{
			push ( @sysctl_file, "$key = $sysctl{$key}" );
		}
		else
		{
			s/^$quoted_key .*/$key = $sysctl{$key}/ for @sysctl_file;
		}
	}

	untie @sysctl_file;

	# apply file configuration to system
	my $sysctl_errno = system ( 'sysctl -p > /dev/null' );
	my $sysclt_msg;

	if ( $sysctl_errno )
	{
		$sysclt_msg = "An error happenend applying sysctl policies.";
	}
	else
	{
		$sysclt_msg = "Sysctl applied policies successfully.";
	}

	&zenlog( $sysclt_msg );
	#### End of node tuning ####
}

sub start_service
{
	&zenlog("Zevenet Service: Starting...");

	if ( $swcert > 0 )
	{
		&printAndLog( "No valid ZLB certificate was found, no farm started\n" );
		exec ('/usr/local/zevenet/app/zbin/zevenet stop');
	}

	&zenlog("Zevenet Service: Loading Optimizations...");

	&setSystemOptimizations();

	&zenlog("Zevenet Service: Loading Bonding configuration...");

	# bonding
	if ( eval { require Zevenet::Net::Bonding; } )
	{
		# required previous setup
		my $missing_bonding = system ( 'lsmod | grep bonding >/dev/null' );
		if ( $missing_bonding )
		{
			system ( '/sbin/modprobe bonding >/dev/null 2>&1' );
			my $bonding_masters_filename = &getGlobalConfiguration('bonding_masters_filename');
			system ( "echo -bond0 > $bonding_masters_filename" );
		}

		# interface configuration
		my $bond_conf = &getBondConfig();
		for my $bond_k ( keys %{ $bond_conf } )
		{
			next if $bond_k eq '_';

			my $bond = $bond_conf->{ $bond_k };

			print "  * Up bonding master $$bond{name} ";

			my $error_code = &applyBondChange( $bond );

			if ( $error_code == 0 )
			{
				print " \033[1;32m OK \033[0m \n";
			}
			else
			{
				print " \033[1;31m ERROR \033[0m \n";
			}
		}
	}

	&zenlog("Zevenet Service: Loading Notification configuration...");

	# notifications
	if ( eval { require Zevenet::Notify; } )
	{
		&zlbstartNotifications();
	}

	&zenlog("Zevenet Service: Starting IPDS system...");

	# ipds
	if ( eval { require Zevenet::IPDS::Base; } )
	{
		&runIPDSStartModule();
	}

	return 0;
}

# this function syncs files with the other node before starting the cluster and
# starts the cluster services with low priority
sub enable_cluster
{
	# check activation certificate
	if ( $swcert > 0 )
	{
		&printAndLog( "No valid ZLB certificate was found, no farm started\n" );
		# stop zevenet service if the certificate is not valid
		# WARNING: this MUST be 'exec' and not other way of running a program
		exec ('/usr/local/zevenet/app/zbin/zevenet stop');
	}

	require Zevenet::Cluster;

	my $zcl_configured    = &getZClusterStatus();
	my $znode_status_file = &getGlobalConfiguration( 'znode_status_file' );
	my $local_node_status;
	my $master_node;

	# end this function if the cluster is not configured
	unless ( $zcl_configured )
	{
		&zenlog( "Cluster configuration not found" );
		return 0;
	}

	&zenlog( "Cluster configuration found" );

	# check node status if node_status_file exists
	if ( -f $znode_status_file )
	{
		$local_node_status = &getZClusterNodeStatus();
		$master_node       = ( $local_node_status eq 'master' );
		$enable_fg         = $master_node;
	}

	# detect master node
	# run command remotely on all nodes
	my $zcl_conf           = &getZClusterConfig();
	my $remote_ip          = $zcl_conf->{ &getZClusterRemoteHost() }->{ ip };
	my $remote_node_status = &runRemotely( "cat $znode_status_file", $remote_ip );

	# force sync with master
	if ( $remote_node_status eq 'master' )
	{
		# FIXME: use zcluster_manager function
		my $zcluster_manager = &getGlobalConfiguration('zcluster_manager');

		&runRemotely( "$zcluster_manager sync", $remote_ip );
		&enableZCluster( 10 );
		&zenlog("enableZCluster returned");
	}

	# disable ip announcement if the node is not master
	if ( $local_node_status ne 'master' )
	{
		my @configured_interfaces = @{ &getConfigInterfaceList() };

		foreach my $iface ( @configured_interfaces )
		{
			next if ( $$iface{ vini } eq '' );
			next if ( $$iface{ status } ne "up" );

			&disableInterfaceDiscovery( $iface );
		}
	}

	return 0;
}

sub start_cluster
{
	require Zevenet::Cluster;

	# check activation certificate
	if ( $swcert > 0 )
	{
		&printAndLog( "No valid ZLB certificate was found, no farm started\n" );
		# stop zevenet service if the certificate is not valid
		# WARNING: this MUST be 'exec' and not other execution
		exec ('/usr/local/zevenet/app/zbin/zevenet stop');
	}

	my $zcl_configured = &getZClusterStatus();

	# end this function if the cluster is not configured
	unless ( $zcl_configured )
	{
		&zenlog( "Cluster configuration not found" );
		return 0;
	}

	# start cluster
	if ( &getZClusterStatus() )
	{
		&enableAllInterfacesDiscovery();
		&enableZCluster();
	}

	return 0;
}

sub stop_service
{
	require Zevenet::Notify;
	require Zevenet::IPDS::Base;

	# stop all modules
	&zlbstopNotifications();
	&runIPDSStopModule();

	if ( &getZClusterStatus() )
	{
		&zenlog( "Stopping ZCluster...\n" );

		if ( `pgrep zeninotify` )
		{
			my $zenino = &getGlobalConfiguration('zenino');
			system ( "$zenino stop" );
		}

		if ( &getZClusterRunning() )
		{
			&disableZCluster();
		}
	}

	return 0;
}

sub disable_cluster
{
	require Zevenet::Cluster;

	my $zcl_configured = &getZClusterStatus();
	&enableAllInterfacesDiscovery() if $zcl_configured;

	return 0;
}

1;
