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

my $DEFAULT_DEADRATIO = 5; # FIXME: MAKE GLOBAL VARIABLE
my $DEFAULT_FAILBACK = 'disabled'; # FIXME: MAKE GLOBAL VARIABLE
my $maint_if = 'cl_maintenance';

sub get_cluster
{
	my $description = "Show the cluster configuration";

	unless ( &getZClusterStatus() )
	{
		my $body = {
					 description => $description,
					 success     => 'true',
					 message     => "There is no cluster configured on this node.",
		};

		&httpResponse( { code => 200, body => $body } );
	}

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

	my $body = {
				 description => $description,
				 params      => $cluster,
	};

	&httpResponse({ code => 200, body => $body });
}

sub modify_cluster
{
	my $json_obj = shift;

	my $description = "Modifying the cluster configuration";
	my $filecluster = &getGlobalConfiguration('filecluster');

	unless ( &getZClusterStatus() )
	{
		my $errormsg = "The cluster must be configured";
		my $body = {
					 description => $description,
					 error       => 'true',
					 message     => $errormsg,
		};

		&httpResponse({ code => 400, body => $body });
	}

	my @cl_opts = ('check_interval','failback');

	# validate CLUSTER parameters
	if ( grep { ! ( @cl_opts ~~ /^$_$/ ) } keys %$json_obj )
	{
		my $errormsg = "Cluster parameter not recognized";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	# do not allow request without parameters
	unless ( scalar keys %$json_obj )
	{
		my $errormsg = "Cluster setting requires at least one parameter";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	my $zcl_conf        = &getZClusterConfig();
	my $local_hostname  = &getHostname();
	my $remote_hostname = &getZClusterRemoteHost();
	my $changed_config;

	# validate CHECK_INTERVAL / DEADRATIO
	if ( exists $json_obj->{ check_interval } )
	{
		unless (    $json_obj->{ check_interval }
				 && &getValidFormat( 'natural_num', $json_obj->{ check_interval } ) )
		{
			my $errormsg = "Invalid check interval value";
			my $body = {
						 description => $description,
						 error      => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}

		# change deadratio
		if ( $zcl_conf->{_}->{ deadratio } != $json_obj->{ check_interval } )
		{
			$zcl_conf->{_}->{ deadratio } = $json_obj->{ check_interval };
			$changed_config = 1;
		}
	}

	# validate FAILBACK / PRIMARY
	if ( exists $json_obj->{ failback } )
	{
		unless ( &getZClusterStatus() )
		{
			my $errormsg = "Setting a primary node Error configuring the cluster";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}

		my @failback_opts = ( 'disabled', $local_hostname, $remote_hostname );

		unless( @failback_opts ~~ /^$json_obj->{ failback }$/ )
		{
			my $errormsg = "Primary node value not recognized";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}

		if ( $zcl_conf->{_}->{ primary } ne $json_obj->{ failback } )
		{
			$zcl_conf->{_}->{ primary } = $json_obj->{ failback };
			$changed_config = 1;
		}
	}

	unless ( $changed_config )
	{
		# Error
		my $errormsg = "Nothing to be changed";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	eval {
		&setZClusterConfig( $zcl_conf ) or die;

		if ( &getZClusterStatus() )
		{
			### cluster Re-configuration ###
			my $rhost = &getZClusterRemoteHost();
			my $zcluster_manager = &getGlobalConfiguration('zcluster_manager');

			&logAndRun( "scp $filecluster root\@$zcl_conf->{$rhost}->{ip}:$filecluster" );

			# reconfigure local conntrackd
			include 'Zevenet::Conntrackd';
			&setConntrackdConfig();

			# reconfigure remote conntrackd
			&zenlog(
				&runRemotely(
					"$zcluster_manager setKeepalivedConfig",
					$zcl_conf->{$rhost}->{ip}
				)
				, "info", "CLUSTER"
			);

			# reload keepalived configuration local and remotely
			my $error_code = &enableZCluster();

			&zenlog(
				&runRemotely(
					"$zcluster_manager enableZCluster",
					$zcl_conf->{$rhost}->{ip}
				)
				. "" # forcing string output
				, "info", "CLUSTER"
			);
		}
	};
	if ( ! $@ )
	{
		# Success
		my $local_hn  = &getHostname();
		my $cluster = {
						check_interval => $zcl_conf->{ _ }->{ deadratio } // $DEFAULT_DEADRATIO,
						failback       => $zcl_conf->{ _ }->{ primary }   // $local_hn,
		};

		$cluster->{ check_interval } += 0;

		my $body = {
					 description => $description,
					 params      => $cluster,
		};

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		# Error
		&zenlog( $@, "error", "CLUSTER" );

		my $errormsg = "Error configuring the cluster";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

sub set_cluster_actions
{
	my $json_obj = shift;

	my $description = "Setting cluster action";

	# validate ACTION parameter
	unless ( exists $json_obj->{ action } )
	{
		my $errormsg = "Action parameter required";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	# do not allow requests without parameters
	unless ( scalar keys %$json_obj )
	{
		my $errormsg = "Cluster actions requires at least the action parameter";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	# ACTIONS: maintenance
	if ( $json_obj->{ action } eq 'maintenance' )
	{
		my $description = "Setting maintenance mode";

		# make sure the cluster is enabled
		unless ( &getZClusterStatus() )
		{
			my $errormsg = "The cluster must be enabled";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}

		# validate parameters
		my @cl_opts = ('action','status');
		unless ( grep { @cl_opts ~~ /^(?:$_)$/ } keys %$json_obj )
		{
			my $errormsg = "Unrecognized parameter received";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}

		# Enable maintenance mode
		if ( $json_obj->{ status } eq 'enable' )
		{
			require Zevenet::Net::Interface;

			# make sure the node is not already under maintenance
			my $if_ref = getSystemInterface( $maint_if );

			if ( $if_ref->{ status } eq 'down' )
			{
				my $errormsg = "The node is already under maintenance";
				my $body = {
							 description => $description,
							 error       => "true",
							 message     => $errormsg
				};

				&httpResponse({ code => 400, body => $body });
			}

			my $ip_bin = &getGlobalConfiguration( 'ip_bin' );
			&logAndRun("$ip_bin link set $maint_if down");

			# required for no failback configuration
			if ( &getZClusterNodeStatus() eq 'backup' )
			{
				&setZClusterNodeStatus('maintenance');
			}
		}

		# Disable maintenance mode
		elsif ( $json_obj->{ status } eq 'disable' )
		{
			require Zevenet::Net::Interface;

			# make sure the node is under maintenance
			my $if_ref = getSystemInterface( $maint_if );

			if ( $if_ref->{ status } eq 'up' )
			{
				my $errormsg = "The node is not under maintenance";
				my $body = {
							 description => $description,
							 error       => "true",
							 message     => $errormsg
				};

				&httpResponse({ code => 400, body => $body });
			}

			my $ip_bin = &getGlobalConfiguration( 'ip_bin' );
			&logAndRun("$ip_bin link set $maint_if up");

			# required for no failback configuration
			&setZClusterNodeStatus('backup');
		}
		else
		{
			my $errormsg = "Status parameter not recognized";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}

		my $message = "Cluster status changed to $json_obj->{status} successfully";
		my $body = {
					 description => $description,
					 success => 'true',
					 message      => $message,
		};

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		my $errormsg = "Cluster action not recognized";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

sub disable_cluster
{
	my $description = "Disabling cluster";

	# make sure the cluster is enabled
	unless ( &getZClusterStatus() )
	{
		my $errormsg = "The cluster is already disabled";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
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
				$zcl_conf->{$rhost}->{ip}
			)
			, "info", "CLUSTER"
		);

		# 3 stop master cluster service
		&disableZCluster();
	}
	else
	{
		# 1 stop zeninotify
		&zenlog(
			&runRemotely(
				"$zenino stop",
				$zcl_conf->{$rhost}->{ip}
			)
			,"info", "CLUSTER"
		);

		# 2 stop slave zevenet
		&logAndRun( "/etc/init.d/zevenet stop >/dev/null 2>&1" );

		my $zcluster_manager = &getGlobalConfiguration('zcluster_manager');

		# 3 stop master cluster service
		&zenlog(
			&runRemotely(
				"$zcluster_manager disableZCluster",
				$zcl_conf->{$rhost}->{ip}
			)
			, "info", "CLUSTER"
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

	for my $cl_file ( $filecluster, $keepalived_conf, $znode_status_file, $conntrackd_conf ) # FIXME: Global variables
	{
		unlink $cl_file;
		&zenlog(
			&runRemotely(
				"rm $cl_file >/dev/null 2>&1",
				$zcl_conf->{$rhost}->{ip}
			)
			, "info", "CLUSTER"
		);
	}

	my $message = "Cluster disabled successfully";
	my $body = {
				 description => $description,
				 success => 'true',
				 message      => $message,
	};

	&httpResponse({ code => 200, body => $body });
}

sub enable_cluster
{
	my $json_obj = shift;

	my $description = "Enabling cluster";

	# do not allow requests without parameters
	unless ( scalar keys %$json_obj )
	{
		my $errormsg = "Cluster actions requires at least the action parameter";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	# validate parameters
	my @cl_opts = ('local_ip','remote_ip','remote_password');
	if ( grep { ! ( @cl_opts ~~ /^$_$/ ) } keys %$json_obj )
	{
		my $errormsg = "Unrecognized parameter received";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	# the cluster cannot be already enabled
	if ( &getZClusterStatus() )
	{
		my $errormsg = "The cluster is already enabled";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	# validate LOCAL IP
	require Zevenet::Net::Interface;

	my @cl_if_candidates = @{ &getSystemInterfaceList() };
	@cl_if_candidates = grep { $_->{ addr } && $_->{ type } ne 'virtual' } @cl_if_candidates;

	unless ( scalar grep { $json_obj->{ local_ip } eq $_->{ addr } } @cl_if_candidates )
	{
		my $errormsg = "Local IP address value is not valid";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	# validate REMOTE IP format
	unless ( $json_obj->{ remote_ip } && &getValidFormat( 'IPv4_addr', $json_obj->{ remote_ip } ) )
	{
		my $errormsg = "Remote IP address has invalid format";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	# validate REMOTE PASSWORD
	unless ( exists $json_obj->{ remote_password } && defined $json_obj->{ remote_password } )
	{
		my $errormsg = "A remote node password must be defined";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	eval {
		my $error = &exchangeIdKeys( $json_obj->{ remote_ip }, $json_obj->{ remote_password } );

		if ( $error )
		{
			&zenlog("Error enabling the cluster: Keys Ids exchange failed", "error", "CLUSTER");
			die;
		}

		my $zcl_conf = &getZClusterConfig();
		my $remote_hostname = &runRemotely( 'hostname', $json_obj->{ remote_ip } );
		my $local_hostname = &getHostname();

		chomp $remote_hostname;
		chomp $local_hostname;

		require Zevenet::Net::Util;

		$zcl_conf->{ _ }->{ deadratio } = $DEFAULT_DEADRATIO;
		$zcl_conf->{ _ }->{ interface } = &getInterfaceOfIp( $json_obj->{ local_ip } );
		$zcl_conf->{ _ }->{ primary }   = $DEFAULT_FAILBACK;

		if ( $local_hostname && $remote_hostname )
		{
			$zcl_conf->{ $local_hostname }->{ ip } = $json_obj->{ local_ip };
			$zcl_conf->{ $remote_hostname }->{ ip } = $json_obj->{ remote_ip };
		}

		# verify the cluster interface is the same in both nodes
		my $ip_bin = &getGlobalConfiguration('ip_bin');
		my $cl_if = $zcl_conf->{ _ }->{ interface };
		my $rm_ip = $json_obj->{ remote_ip };
		my @remote_ips = &runRemotely( "$ip_bin -o addr show $cl_if", $json_obj->{ remote_ip } );

		unless ( scalar grep( { /^\d+: $cl_if\s+inet? $rm_ip\// } @remote_ips ) )
		{
			my $msg = "Remote address does not match the cluster interface";
			&zenlog( $msg, "error", "CLUSTER" );
			die $msg;
		}

		&setZClusterConfig( $zcl_conf ) or die;


		## Starting cluster services ##

		# first synchronization
		my $configdir = &getGlobalConfiguration('configdir');
		&runSync( $configdir );

		# generate cluster config and start cluster service
		die if &enableZCluster();

		# force cluster file sync
		my $filecluster = &getGlobalConfiguration('filecluster');
		&logAndRun( "scp $filecluster root\@$zcl_conf->{$remote_hostname}->{ip}:$filecluster" );

		# local conntrackd configuration
		&setConntrackdConfig();

		my $zcluster_manager = &getGlobalConfiguration('zcluster_manager');
		my $cl_output;

		# remote conntrackd configuration
		$cl_output = &runRemotely(
			"$zcluster_manager setConntrackdConfig",
			$zcl_conf->{$remote_hostname}->{ip}
		);
		&zenlog( "rc:$? $cl_output", "info", "CLUSTER" );

		# remote keepalived configuration
		$cl_output = &runRemotely(
			"$zcluster_manager setKeepalivedConfig",
			$zcl_conf->{$remote_hostname}->{ip}
		);
		&zenlog( "rc:$? $cl_output", "info", "CLUSTER" );

		# start remote interfaces, farms and cluster
		$cl_output = &runRemotely(
			'/etc/init.d/zevenet start',
			$zcl_conf->{$remote_hostname}->{ip}
		);
		&zenlog( "rc:$? $cl_output", "info", "CLUSTER" );
	};
	if ( ! $@ )
	{
		my $message = "Cluster enabled successfully";
		my $body = {
					 description => $description,
					 success => 'true',
					 message      => $message,
		};

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		my $errormsg = "An error happened configuring the cluster: $@";
		$errormsg =~ s/ at \/.+//;
		$errormsg =~ s/\n//;
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

sub get_cluster_localhost_status
{
	my $description = "Cluster status for localhost";

	my $node = &getZClusterNodeStatusDigest();
	$node->{ name } = &getHostname();

	my $body = {
				 description => $description,
				 params      => $node,
	};

	&httpResponse({ code => 200, body => $body });
}

sub get_cluster_nodes_status
{
	my $description = "Cluster nodes status";
	my $localhost = &getHostname();
	my @cluster;

	if ( ! &getZClusterStatus() )
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

			my $ip = $cl_conf->{ $node_name }->{ ip };
			my $node = &getZClusterNodeStatusDigest( $ip );

			#~ my $if_ref = getSystemInterface( $maint_if );
			#~ if ( $if_ref->{ status } eq 'down' )

			$node->{ name } = $node_name;
			$node->{ ip } = $ip;
			$node->{ node } = ( $node_name eq $localhost ) ? 'local' : 'remote';

			push @cluster, $node;
		}
	}

	my $body = {
				 description => $description,
				 params      => \@cluster,
	};

	&httpResponse({ code => 200, body => $body });
}

1;
