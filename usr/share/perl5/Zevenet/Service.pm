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

use Zevenet::Net::Interface;

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
my $swcert    = &certcontrol();
my $enable_fg = 1;

sub getEnableFarmGuardian
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	return $enable_fg;
}

sub setSystemOptimizations
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $appliance_version = &getApplianceVersion();
	&zenlog( "Appliance version: $appliance_version", "info", "SYSTEM" );

	#### Starts node tuning ####
	require Zevenet::Farm::L4xNAT::Service;
	&loadL4FarmModules();

	&logAndRun( 'echo "22500" > /sys/module/nf_conntrack/parameters/hashsize' );

	# Set system tuning with sysctl
	my %sysctl = (
		"fs.file-max"                    => "100000",
		"kernel.threads-max"             => "120000",                # packetbl
		"kernel.pid_max"                 => "200000",                # packetbl
		"vm.max_map_count"               => "1048576",
		"vm.swappiness"                  => "10",
		"net.ipv4.conf.all.log_martians" => "0",
		"net.ipv4.ip_local_port_range"   => "1024 65535",
		"net.ipv4.tcp_max_tw_buckets"    => "2000000",
		"net.ipv4.tcp_max_syn_backlog"   => "30000",
		"net.ipv4.tcp_window_scaling"    => "1",
		"net.ipv4.tcp_timestamps"        => "0",
		"net.ipv4.tcp_rmem"              => "4096 87380 16777216",
		"net.ipv4.tcp_wmem"              => "4096 65536 16777216",
		"net.ipv4.udp_rmem_min"          => "65536",
		"net.ipv4.udp_wmem_min"          => "65536",
		"net.ipv4.tcp_low_latency"       => "1",
		"net.ipv4.tcp_tw_reuse"          => "1",

		#		"net.ipv4.tcp_tw_recycle"            => "0",
		"net.ipv4.tcp_keepalive_time"        => "512",
		"net.ipv4.tcp_fin_timeout"           => "5",
		"net.ipv4.inet_peer_maxttl"          => "5",
		"net.ipv4.tcp_keepalive_probes"      => "5",
		"net.ipv4.tcp_slow_start_after_idle" => "0",

		#"net.ipv4.netfilter.ip_conntrack_udp_timeout"        => "2",
		#"net.ipv4.netfilter.ip_conntrack_udp_timeout_stream" => "2",
		"net.netfilter.nf_conntrack_tcp_timeout_time_wait" => "2",
		"net.netfilter.nf_conntrack_max"                   => "180000",
		"net.netfilter.nf_conntrack_tcp_loose"             => "0",
		"net.core.rmem_max"                                => "16777216",
		"net.core.wmem_max"                                => "16777216",
		"net.core.rmem_default"                            => "16777216",
		"net.core.wmem_default"                            => "16777216",
		"net.core.optmem_max"                              => "40960",
		"net.ipv4.tcp_keepalive_intvl"                     => "15",
		"net.core.netdev_max_backlog"                      => "50000",
		"net.core.somaxconn"                               => "3000",
		"net.ipv4.ip_nonlocal_bind"                        => "1",
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
		$sysctl{ "net.ipv4.netfilter.ip_conntrack_udp_timeout" }             = "2";
		$sysctl{ "net.ipv4.netfilter.ip_conntrack_udp_timeout_stream" }      = "2";
	}

	#  ZVA equal or higher than 5000
	else
	{
		$sysctl{ "net.netfilter.nf_conntrack_tcp_timeout_established" } = "86400";
		$sysctl{ "net.netfilter.nf_conntrack_udp_timeout" }             = "2";
		$sysctl{ "net.netfilter.nf_conntrack_udp_timeout_stream" }      = "2";

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
	my $sysctl_errno = &logAndRun( 'sysctl -p' );
	my $sysclt_msg;

	if ( $sysctl_errno )
	{
		$sysclt_msg = "An error happenend applying sysctl policies.";
		&zenlog( $sysclt_msg, "error", "SYSTEM" );
	}
	else
	{
		$sysclt_msg = "Sysctl applied policies successfully.";
		&zenlog( $sysclt_msg, "info", "SYSTEM" );
	}

	#### End of node tuning ####
}

sub start_service
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $out_msg = "";
	my $msg     = "";

   # IMPORTANT
   # all thing in this module must be applied although the certificate will be wrong

	&zenlog( "Zevenet Service: Starting...", "info", "SYSTEM" );

	$msg = "Loading Optimizations...";
	$out_msg .= "\n* $msg";
	&zenlog( "Zevenet service: $msg", "info", "SYSTEM" );

	&setSystemOptimizations();

	$msg = "Loading Bonding configuration...";
	$out_msg .= "\n* $msg";
	&zenlog( "Zevenet service: $msg", "info", "SYSTEM" );

	include 'Zevenet::Net::Bonding';

	# bonding
	# required previous setup
	my $missing_bonding = &logAndRunCheck( 'lsmod | grep bonding' );
	if ( $missing_bonding )
	{
		&logAndRun( '/sbin/modprobe bonding' );
		my $bonding_masters_filename =
		  &getGlobalConfiguration( 'bonding_masters_filename' );
		&logAndRun( "echo -bond0 > $bonding_masters_filename" );
	}

	require Zevenet::Net::Core;

	# interface configuration
	my $bond_conf = &getBondConfig();
	for my $bond_k ( keys %{ $bond_conf } )
	{
		next if $bond_k eq '_';

		my $bond = $bond_conf->{ $bond_k };

		$out_msg .= "\n  Up bonding master $$bond{name} ";

		my $error_code = &applyBondChange( $bond );

		if ( $error_code == 0 )
		{
			$out_msg .= " \033[1;32m OK \033[0m \n";
		}
		else
		{
			$out_msg .= " \033[1;31m ERROR \033[0m \n";
		}
	}

	my $ip_bin = &getGlobalConfiguration( 'ip_bin' );
	require Zevenet::Net::Route;
	require Zevenet::Net::Util;

	# bonding adresses configuration
	foreach my $iface ( &getInterfaceTypeList( 'bond' ) )
	{
		# interfaces as eth0 for example
		if ( $$iface{ name } eq $$iface{ dev } )
		{
			use IO::Interface ':flags';

			if ( exists $$iface{ mac } )
			{
				include 'Zevenet::Net::Bonding';
				&setBondMac( $iface );
			}

			if ( $$iface{ status } eq "up" )
			{
				$out_msg .= "\n  * Starting interface $$iface{name}";
				&upIf( $iface );

				if ( exists $$iface{ addr } && length $$iface{ addr } )
				{
					$out_msg .= "\n    Ip:$$iface{addr} Netmask:$$iface{mask}";

					if ( defined $$iface{ gateway } && $$iface{ gateway } ne '' )
					{
						$out_msg .= " Gateway:$$iface{gateway}";
					}

					my $return_code = &addIp( $iface );

					if ( $return_code )
					{
						my @ip_output = `$ip_bin address show dev $$iface{name}`;
						$return_code = 0 if ( grep /$$iface{addr}/, @ip_output );
					}

					# kept in case it is required for first interface
					require Zevenet::Net::Route;
					&writeRoutes( $$iface{ name } );

					&applyRoutes( "local", $iface );

					if ( $return_code == 0 )
					{
						$out_msg .= " \033[1;32m OK \033[0m \n";
					}
					else
					{
						$out_msg .= " \033[1;31m ERROR \033[0m \n";
					}
				}

				if ( defined $$iface{ ip_v } && $$iface{ ip_v } == 4 )
				{
					require Zevenet::Net::Util;
					&sendGPing( $$iface{ name } );
				}
			}
		}
	}

	return $out_msg;
}

sub start_ipds_without_cert
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $out_msg = "";
	my $msg     = "";

	# ipds
	$msg = "Starting IPDS system...";
	$out_msg .= "* $msg\n";
	&zenlog( "Zevenet Service: $msg", "info", "IPDS" );
	include 'Zevenet::IPDS::Base';
	&runIPDSStartModule();
	return $out_msg;
}

# Warning! this function is used only from the postinst.
# to use it from another side, use: "start_modules"
sub start_modules_without_cert
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $out_msg = "";
	my $msg     = "";

	# Notifications
	$msg     = "Starting Notification...";
	$out_msg = "* $msg\n\n";
	&zenlog( "Zevenet Service: $msg", "info", "NOTIFICATIONS" );

	include 'Zevenet::Notify';
	&zlbstartNotifications();

	# rbac
	$msg = "Starting RBAC system...";
	$out_msg .= "* $msg\n\n";
	&zenlog( "Zevenet Service: $msg", "info", "RBAC" );

	include 'Zevenet::RBAC::Action';
	&initRBACModule();

	## ipds
	include 'Zevenet::IPDS::Setup';
	&initIPDSModule();

	# enable monitoring interface throughput
	#~ include 'Zevenet::Net::Throughput';
	#~ &startTHROUTask();

	return $out_msg;
}

sub start_modules
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	# do not run cluster if the certificate is not valid
	return "" if ( $swcert > 0 );

	return &start_modules_without_cert();
}

# this function syncs files with the other node before starting the cluster and
# starts the cluster services with low priority
sub enable_cluster
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	# do not run cluster if the certificate is not valid
	return "" if ( $swcert > 0 );

	my $msg;
	my $out_msg = "";

	include 'Zevenet::Cluster';

	my $zcl_configured    = &getZClusterStatus();
	my $znode_status_file = &getGlobalConfiguration( 'znode_status_file' );
	my $local_node_status;
	my $master_node;

	# end this function if the cluster is not configured
	unless ( $zcl_configured )
	{
		$out_msg = "* Cluster configuration NOT found";
		&zenlog( "Zevenet Service: $out_msg", "info", "CLUSTER" );
		return $out_msg;
	}

	$msg     = "* Configuring Cluster...";
	$out_msg = $msg;
	&zenlog( "Zevenet Service: $msg", "info", "CLUSTER" );

	# check node status if node_status_file exists
	if ( -f $znode_status_file )
	{
		$local_node_status = &getZClusterNodeStatus();
		$enable_fg         = ( $local_node_status eq 'master' );
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
		my $zcluster_manager = &getGlobalConfiguration( 'zcluster_manager' );

		&runRemotely( "$zcluster_manager sync", $remote_ip );
		&enableZCluster( 10 );

		&zenlog( "Syncing RBAC users", "info", "RBAC" );

		include 'Zevenet::RBAC::Action';
		&updateRBACAllUser();

		&zenlog( "enableZCluster returned", "info", "CLUSTER" );
	}

	# disable ip announcement if the node is not master
	if ( $local_node_status ne 'master' )
	{
		require Zevenet::Net::Interface;
		my @configured_interfaces = @{ &getConfigInterfaceList() };

		foreach my $iface ( @configured_interfaces )
		{
			next if ( !defined $$iface{ vini } || $$iface{ vini } eq '' );
			next if ( $$iface{ status } ne "up" );

			&disableInterfaceDiscovery( $iface );
		}
	}

	$msg =
	  "The nodo has been configured with the role \033[1;32m $local_node_status \033[0m";
	$out_msg .= "\n  $msg";
	&zenlog( "Zevenet Service: $msg", "info", "RBAC" );

	return $out_msg;
}

sub start_cluster
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	include 'Zevenet::Cluster';

	# do not run cluster if the certificate is not valid
	return "" if ( $swcert > 0 );

	my $zcl_configured = &getZClusterStatus();

	# end this function if the cluster is not configured
	unless ( $zcl_configured )
	{
		&zenlog( "Cluster configuration not found", "info", "CLUSTER" );
		return 0;
	}

	# start cluster
	if ( $zcl_configured )
	{
		&enableAllInterfacesDiscovery();
		&enableZCluster();

		if ( &getZClusterNodeStatus() eq 'maintenance' )
		{
			require Zevenet::Net::Interface;

			my $maint_if = 'cl_maintenance';
			my $ip_bin   = &getGlobalConfiguration( 'ip_bin' );
			my $if_ref   = &getSystemInterface( $maint_if );

			&logAndRun( "$ip_bin link set $maint_if down" );
		}
	}

	return 0;
}

sub stop_service
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	include 'Zevenet::Notify';
	include 'Zevenet::IPDS::Base';
	include 'Zevenet::Net::Throughput';
	include 'Zevenet::Cluster';

	my $out_msg = "";

	# stop all modules
	&zlbstopNotifications();
	&runIPDSStopModule();

	#~ &stopTHROUTask();

	if ( &getZClusterStatus() )
	{
		$out_msg = "Stopping ZCluster...";
		&zenlog( "$out_msg", "info", "CLUSTER" );
		my $zenino_proc = &get_zeninotify_process();

		unless ( &logAndRunCheck( $zenino_proc ) )
		{
			my $zenino = &getGlobalConfiguration( 'zenino' );
			&logAndRun( "$zenino stop" );
		}

		if ( &getZClusterRunning() )
		{
			&disableZCluster();
		}
	}

	return $out_msg;
}

sub disable_cluster
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	include 'Zevenet::Cluster';

	my $zcl_configured = &getZClusterStatus();
	&enableAllInterfacesDiscovery() if $zcl_configured;

	return 0;
}

sub service_start_farms
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	return ( $swcert > 0 );    # return 1 if the certificate is not valid
}

sub service_cert_message
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $output = "";
	my $tag    = "";
	my $msg    = "";

	if ( $swcert == 0 )
	{
		return "";
	}
	elsif ( $swcert < 0 )
	{
		$tag = "\033[1;33m Warning \033[0m";
		$msg = "The support contract is expired";
	}
	else
	{
		$tag = "\033[1;31m ERROR \033[0m";
		$msg = "No valid ZLB certificate was found, no farm started\n    ";
		$msg .= &getCertErrorMessage( $swcert );
	}

	$output = "  $tag $msg\n\n";

	return $output;
}

1;
