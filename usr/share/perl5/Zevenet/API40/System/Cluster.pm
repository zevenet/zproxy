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

use Zevenet::API40::HTTP;

include 'Zevenet::Cluster';

# disable smartmatch experimental warnings for perl >= 5.18
no if $] >= 5.018, warnings => "experimental::smartmatch";

#
##### /system/cluster
#
#GET qr{^/system/cluster$} => sub {
#       &get_cluster( @_ );
#};
#
#POST qr{^/system/cluster$} => sub {
#       &set_cluster( @_ );
#};

my $DEFAULT_DEADRATIO = 5;                  # FIXME: MAKE GLOBAL VARIABLE
my $DEFAULT_FAILBACK  = 'disabled';         # FIXME: MAKE GLOBAL VARIABLE
my $maint_if          = 'cl_maintenance';

sub get_cluster
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	require Zevenet::SystemInfo;

	my $desc      = "Show the cluster configuration";
	my $cl_status = &getZClusterStatus();
	my $body;

	if ( $cl_status )
	{
		my $zcl_conf  = &getZClusterConfig();
		my $local_hn  = &getHostname();
		my $remote_hn = &getZClusterRemoteHost();

		my $cluster = {
					check_interval => $zcl_conf->{ _ }->{ deadratio } // $DEFAULT_DEADRATIO,
					failback       => $zcl_conf->{ _ }->{ primary }   // $local_hn,
					interface      => $zcl_conf->{ _ }->{ interface },
					nodes          => [
							  {
								ip   => $zcl_conf->{ $local_hn }->{ ip },
								name => $local_hn,
								node => 'local',
							  },
							  {
								ip   => $zcl_conf->{ $remote_hn }->{ ip },
								name => $remote_hn,
								node => 'remote',
							  },
					]
		};

		$cluster->{ check_interval } += 0;

		$body = {
				  description => $desc,
				  params      => $cluster,
		};
	}
	else
	{
		$body = {
				  description => $desc,
				  success     => 'true',
				  message     => "There is no cluster configured on this node.",
		};
	}

	return &httpResponse( { code => 200, body => $body } );
}

sub modify_cluster
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;

	my $desc        = "Modifying the cluster configuration";
	my $filecluster = &getGlobalConfiguration( 'filecluster' );

	# check if there is a cluster configured
	unless ( &getZClusterStatus() )
	{
		my $msg = "The cluster must be configured";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $zcl_conf        = &getZClusterConfig();
	my $local_hostname  = &getHostname();
	my $remote_hostname = &getZClusterRemoteHost();
	my $changed_config;

	my @failback_opts = ( 'disabled', $local_hostname, $remote_hostname );
	my $params = {
				   "check_interval" => {
										 'non_blank'    => 'true',
										 'valid_format' => 'natural_num',
				   },
				   "failback" => {
								   'non_blank' => 'true',
								   'values'    => \@failback_opts,
				   },
	};

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	# validate CHECK_INTERVAL / DEADRATIO
	if ( exists $json_obj->{ check_interval } )
	{
		# change deadratio
		if ( $zcl_conf->{ _ }->{ deadratio } != $json_obj->{ check_interval } )
		{
			$zcl_conf->{ _ }->{ deadratio } = $json_obj->{ check_interval };
			$changed_config = 1;
		}
	}

	# validate FAILBACK / PRIMARY
	if ( exists $json_obj->{ failback } )
	{
		unless ( &getZClusterStatus() )
		{
			my $msg = "Setting a primary node Error configuring the cluster";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}

		if ( $zcl_conf->{ _ }->{ primary } ne $json_obj->{ failback } )
		{
			$zcl_conf->{ _ }->{ primary } = $json_obj->{ failback };
			$changed_config = 1;
		}
	}

	unless ( $changed_config )
	{
		my $msg = "Nothing to be changed";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	eval {
		&setZClusterConfig( $zcl_conf ) or die;

		if ( &getZClusterStatus() )
		{
			### cluster Re-configuration ###
			my $rhost            = &getZClusterRemoteHost();
			my $zcluster_manager = &getGlobalConfiguration( 'zcluster_manager' );

			&logAndRun( "scp $filecluster root\@$zcl_conf->{$rhost}->{ip}:$filecluster" );

			# reconfigure local conntrackd
			include 'Zevenet::Conntrackd';
			&setConntrackdConfig();

			# reconfigure remote conntrackd
			&zenlog(
					 &runRemotely(
								   "$zcluster_manager setKeepalivedConfig",
								   $zcl_conf->{ $rhost }->{ ip }
					 ),
					 "info",
					 "CLUSTER"
			);

			# reload keepalived configuration local and remotely
			my $error_code = &enableZCluster();

			&zenlog(
					 &runRemotely(
								   "$zcluster_manager enableZCluster",
								   $zcl_conf->{ $rhost }->{ ip }
					   )
					   . "",
					 "info",
					 "CLUSTER"
			);
		}
	};
	if ( $@ )
	{
		my $msg = "Error configuring the cluster";
		return
		  &httpErrorResponse(
							  code    => 400,
							  desc    => $desc,
							  msg     => $msg,
							  log_msg => $@
		  );
	}

	my $local_hn = &getHostname();
	my $cluster = {
				check_interval => $zcl_conf->{ _ }->{ deadratio } // $DEFAULT_DEADRATIO,
				failback       => $zcl_conf->{ _ }->{ primary }   // $local_hn,
	};

	$cluster->{ check_interval } += 0;

	my $body = {
				 description => $desc,
				 params      => $cluster,
	};

	return &httpResponse( { code => 200, body => $body } );
}

sub set_cluster_actions
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;

	my $desc = "Setting cluster action";

	my $params = {
				   "action" => {
								 'non_blank' => 'true',
								 'required'  => 'true',
								 'values'    => ['maintenance'],
				   },
				   "status" => {
								 'non_blank' => 'true',
								 'required'  => 'true',
								 'values'    => ['enable', 'disable'],
				   },
	};

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	# ACTIONS: maintenance
	my $desc = "Setting maintenance mode";

	# make sure the cluster is enabled
	unless ( &getZClusterStatus() )
	{
		my $msg = "The cluster must be enabled";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# Enable maintenance mode
	if ( $json_obj->{ status } eq 'enable' )
	{
		# workaround for keepalived 1.2.13
		if ( &getKeepalivedVersion() eq '1.2.13' )
		{
			my $zcluster_manager = &getGlobalConfiguration( 'zcluster_manager' );
			&logAndRun( "$zcluster_manager notify_fault" );

			my $ka_cmd = "/etc/init.d/keepalived stop >/dev/null 2>&1";
			&logAndRun( $ka_cmd );
		}
		else
		{
			require Zevenet::Net::Interface;

			# make sure the node is not already under maintenance
			my $if_ref = getSystemInterface( $maint_if );

			if ( $if_ref->{ status } eq 'down' )
			{
				my $msg = "The node is already under maintenance";
				return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
			}

			my $ip_bin = &getGlobalConfiguration( 'ip_bin' );
			&logAndRun( "$ip_bin link set $maint_if down" );

			# required for no failback configuration
			if ( &getZClusterNodeStatus() eq 'backup' )
			{
				&setZClusterNodeStatus( 'maintenance' );
			}
		}
	}

	# Disable maintenance mode
	elsif ( $json_obj->{ status } eq 'disable' )
	{
		# workaround for keepalived 1.2.13
		if ( &getKeepalivedVersion() eq '1.2.13' )
		{
			&setZClusterNodeStatus( 'backup' );

			my $zcluster_manager = &getGlobalConfiguration( 'zcluster_manager' );
			&logAndRun( "$zcluster_manager notify_backup" );

			my $ka_cmd = "/etc/init.d/keepalived start >/dev/null 2>&1";
			&logAndRun( $ka_cmd );
		}
		else
		{
			require Zevenet::Net::Interface;

			# make sure the node is under maintenance
			my $if_ref = getSystemInterface( $maint_if );

			if ( $if_ref->{ status } eq 'up' )
			{
				my $msg = "The node is not under maintenance";
				return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
			}

			my $ip_bin = &getGlobalConfiguration( 'ip_bin' );
			&logAndRun( "$ip_bin link set $maint_if up" );

			# required for no failback configuration
			&setZClusterNodeStatus( 'backup' );
		}
	}
	else
	{
		my $msg = "Status parameter not recognized";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $message = "Cluster status changed to $json_obj->{status} successfully";
	my $body = {
				 description => $desc,
				 success     => 'true',
				 message     => $message,
	};

	return &httpResponse( { code => 200, body => $body } );
}

sub disable_cluster
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $desc = "Disabling cluster";

	# make sure the cluster is enabled
	unless ( &getZClusterStatus() )
	{
		my $msg = "The cluster is already disabled";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# handle remote host when disabling cluster
	my $zcl_conf = &getZClusterConfig();
	my $rhost    = &getZClusterRemoteHost();
	my $zenino   = &getGlobalConfiguration( 'zenino' );

	### Stop cluster services ###
	if ( &getZClusterNodeStatus() eq 'master' )
	{
		# 1 stop master zeninotify
		&logAndRun( "$zenino stop" );

		# 2 stop backup node zevenet
		&zenlog(
				 &runRemotely(
							   "/etc/init.d/zevenet stop >/dev/null 2>&1",
							   $zcl_conf->{ $rhost }->{ ip }
				 ),
				 "info",
				 "CLUSTER"
		);

		# 3 stop master cluster service
		&disableZCluster();
	}
	else
	{
		# 1 stop zeninotify
		&zenlog( &runRemotely( "$zenino stop", $zcl_conf->{ $rhost }->{ ip } ),
				 "info", "CLUSTER" );

		# 2 stop slave zevenet
		&logAndRun( "/etc/init.d/zevenet stop >/dev/null 2>&1" );

		my $zcluster_manager = &getGlobalConfiguration( 'zcluster_manager' );

		# 3 stop master cluster service
		&zenlog(
				 &runRemotely(
							   "$zcluster_manager disableZCluster",
							   $zcl_conf->{ $rhost }->{ ip }
				 ),
				 "info",
				 "CLUSTER"
		);
	}

	### Remove configuration files ###
	# remove cluster configuration file
	# remove keepalived configuration file
	# remove zcluster node status file
	my $filecluster       = &getGlobalConfiguration( 'filecluster' );
	my $keepalived_conf   = &getGlobalConfiguration( 'keepalived_conf' );
	my $znode_status_file = &getGlobalConfiguration( 'znode_status_file' );
	my $conntrackd_conf   = &getGlobalConfiguration( 'conntrackd_conf' );

	for my $cl_file ( $filecluster, $keepalived_conf, $znode_status_file,
					  $conntrackd_conf )    # FIXME: Global variables
	{
		&zenlog(
				 &runRemotely(
							   "rm $cl_file >/dev/null 2>&1",
							   $zcl_conf->{ $rhost }->{ ip }
				 ),
				 "info",
				 "CLUSTER"
		);
		unlink $cl_file;
	}

	require Zevenet::SystemInfo;
	my $provider = &whereIam();
	if ( $provider eq 'aws' )
	{
		my $zcluster_manager = &getGlobalConfiguration( 'zcluster_manager' );

		include 'Zevenet::Aws';
		my $local_error = &setSshForCluster( $zcl_conf->{ $rhost }->{ ip }, 'delete' );
		my $remote_error =
		  &runRemotely( "$zcluster_manager disableSshCluster",
						$zcl_conf->{ $rhost }->{ ip } );

		if ( $local_error )
		{
			my $msg = "It is no possible destroy the local SSH configuration for cluster";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
		if ( $remote_error )
		{
			my $msg = "It is no possible destroy the remote SSH configuration for cluster";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

	my $message = "Cluster disabled successfully";
	my $body = {
				 description => $desc,
				 success     => 'true',
				 message     => $message,
	};

	return &httpResponse( { code => 200, body => $body } );
}

sub enable_cluster
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;

	my $desc = "Enabling cluster";

	my $params = {
				   "local_ip" => {
								   'valid_format' => 'IPv4_addr',
								   'non_blank'    => 'true',
								   'required'     => 'true',
				   },
				   "remote_ip" => {
									'valid_format' => 'IPv4_addr',
									'non_blank'    => 'true',
									'required'     => 'true',
				   },
				   "remote_password" => {
										  'non_blank' => 'true',
										  'required'  => 'true',
				   },
	};

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	# the cluster cannot be already enabled
	if ( &getZClusterStatus() )
	{
		my $msg = "The cluster is already enabled";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# validate LOCAL IP
	require Zevenet::Net::Interface;

	my @cl_if_candidates = @{ &getSystemInterfaceList() };
	@cl_if_candidates =
	  grep { $_->{ addr } && $_->{ type } ne 'virtual' } @cl_if_candidates;

	unless ( scalar grep { $json_obj->{ local_ip } eq $_->{ addr } }
			 @cl_if_candidates )
	{
		my $msg = "Local IP address value is not valid";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	require Zevenet::SystemInfo;
	my $provider = &whereIam();
	if ( $provider eq 'aws' )
	{
		include 'Zevenet::Aws';
		my $local_error = &setSshForCluster( $json_obj->{ remote_ip }, 'add' );
		my $remote_error =
		  &setSshRemoteForCluster(
								   $json_obj->{ remote_ip },
								   $json_obj->{ remote_password },
								   $json_obj->{ local_ip }
		  );

		if ( $local_error )
		{
			my $msg = "It is no possible to change the local SSH configuration for cluster";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
		if ( $remote_error )
		{
			my $msg =
			  "It is no possible to change the remote SSH configuration for cluster";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

	eval {
		my $error =
		  &exchangeIdKeys( $json_obj->{ remote_ip }, $json_obj->{ remote_password } );

		if ( $error )
		{
			&zenlog( "Error enabling the cluster: Keys Ids exchange failed",
					 "error", "CLUSTER" );
			die;
		}

		my $zcl_conf        = &getZClusterConfig();
		my $remote_hostname = &runRemotely( 'hostname', $json_obj->{ remote_ip } );
		my $local_hostname  = &getHostname();

		chomp $remote_hostname;
		chomp $local_hostname;

		require Zevenet::Net::Util;

		$zcl_conf->{ _ }->{ deadratio } = $DEFAULT_DEADRATIO;
		$zcl_conf->{ _ }->{ interface } = &getInterfaceOfIp( $json_obj->{ local_ip } );
		$zcl_conf->{ _ }->{ primary }   = $DEFAULT_FAILBACK;

		if ( $local_hostname && $remote_hostname )
		{
			$zcl_conf->{ $local_hostname }->{ ip }  = $json_obj->{ local_ip };
			$zcl_conf->{ $remote_hostname }->{ ip } = $json_obj->{ remote_ip };
		}

		# verify the cluster interface is the same in both nodes
		my $ip_bin = &getGlobalConfiguration( 'ip_bin' );
		my $cl_if  = $zcl_conf->{ _ }->{ interface };
		my $rm_ip  = $json_obj->{ remote_ip };
		my @remote_ips =
		  &runRemotely( "$ip_bin -o addr show $cl_if", $json_obj->{ remote_ip } );

		unless ( scalar grep ( { /^\d+: $cl_if\s+inet? $rm_ip\// } @remote_ips ) )
		{
			my $msg = "Remote address does not match with the cluster interface";
			&zenlog( $msg, "error", "CLUSTER" );
			die $msg;
		}

		&setZClusterConfig( $zcl_conf ) or die;

		## Starting cluster services ##

		# first synchronization
		my $configdir = &getGlobalConfiguration( 'configdir' );
		&runSync( $configdir );

		# generate cluster config and start cluster service
		die if &enableZCluster();

		# force cluster file sync
		my $filecluster = &getGlobalConfiguration( 'filecluster' );
		&logAndRun(
				"scp $filecluster root\@$zcl_conf->{$remote_hostname}->{ip}:$filecluster" );

		# local conntrackd configuration
		&setConntrackdConfig();

		my $zcluster_manager = &getGlobalConfiguration( 'zcluster_manager' );
		my $cl_output;

		# remote conntrackd configuration
		$cl_output = &runRemotely( "$zcluster_manager setConntrackdConfig",
								   $zcl_conf->{ $remote_hostname }->{ ip } );
		&zenlog( "rc:$? $cl_output", "info", "CLUSTER" );

		# remote keepalived configuration
		$cl_output = &runRemotely( "$zcluster_manager setKeepalivedConfig",
								   $zcl_conf->{ $remote_hostname }->{ ip } );
		&zenlog( "rc:$? $cl_output", "info", "CLUSTER" );

# start remote interfaces, farms and cluster
# bugfix: this process is executed in background, because it was blocking the call when the other node has to configure a lot of services.
		$cl_output = &runRemotely( 'nohup /etc/init.d/zevenet start > /dev/null 2>&1 &',
								   $zcl_conf->{ $remote_hostname }->{ ip } );
		&zenlog( "rc:$? $cl_output", "info", "CLUSTER" );

	};
	if ( $@ )
	{
		my $msg = "An error happened configuring the cluster.";
		return
		  &httpErrorResponse(
							  code    => 400,
							  desc    => $desc,
							  msg     => $msg,
							  log_msg => $@
		  );
	}

	my $message = "Cluster enabled successfully";
	my $body = {
				 description => $desc,
				 success     => 'true',
				 message     => $message,
	};

	return &httpResponse( { code => 200, body => $body } );
}

sub get_cluster_localhost_status
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	require Zevenet::SystemInfo;

	my $desc = "Cluster status for localhost";

	my $node = &getZClusterNodeStatusDigest();
	$node->{ name } = &getHostname();

	my $body = {
				 description => $desc,
				 params      => $node,
	};

	return &httpResponse( { code => 200, body => $body } );
}

sub get_cluster_nodes_status
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	require Zevenet::SystemInfo;

	my $desc      = "Cluster nodes status";
	my $localhost = &getHostname();
	my @cluster;

	if ( !&getZClusterStatus() )
	{
		my $node = {
					 role    => 'not configured',
					 status  => 'not configured',
					 message => 'Cluster not configured',
					 name    => $localhost,
		};
		push @cluster, $node;
	}
	else
	{
		my $cl_conf = &getZClusterConfig();

		for my $node_name ( sort keys %{ $cl_conf } )
		{
			next if $node_name eq '_';

			my $ip   = $cl_conf->{ $node_name }->{ ip };
			my $node = &getZClusterNodeStatusDigest( $ip );

			$node->{ name } = $node_name;
			$node->{ ip }   = $ip;
			$node->{ node } = ( $node_name eq $localhost ) ? 'local' : 'remote';

			push @cluster, $node;
		}
	}

	my $body = {
				 description => $desc,
				 params      => \@cluster,
	};

	return &httpResponse( { code => 200, body => $body } );
}

1;
