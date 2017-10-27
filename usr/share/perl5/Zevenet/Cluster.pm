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

#~ use Zevenet::Conntrackd;

my $maint_if = 'cl_maintenance';

=begin nd
Function: getZClusterLocalIp

	Get the IP address of the local node in the cluster.

Parameters:
	none - .

Returns:
	string - IP address.

See Also:
	<getZClusterNodeStatusInfo>
=cut
sub getZClusterLocalIp
{
	return undef if ! &getZClusterStatus();
	
	my $zcl_conf = getZClusterConfig();

	return $zcl_conf->{ &getHostname() }->{ ip };
}

=begin nd
Function: getZClusterStatus

	Get if the cluster is configured.

Parameters:
	none - .

Returns:
	boolean - TRUE if the cluster is configured, or FALSE otherwise.

See Also:
	<getZClusterLocalIp>, <setDOSSshBruteForceRule>

	zapi/v3/cluster.cgi, cluster_status.pl, zevenet

	NOT USED: <getClusterInfo>,

=cut
sub getZClusterStatus
{
	# case filecuster does not exist
	return undef if ! -f &getGlobalConfiguration('filecluster');

	my $zcl_conf = &getZClusterConfig();

	# $zcl_conf->{_} global section
	# $zcl_conf->{*} node section
	# 1 global section + 2 nodes section

	return keys %{ $zcl_conf } > 2;
}

=begin nd
Function: getZClusterConfig

	Get cluster configuration hash.

Parameters:
	none - .

Returns:
	undef  - On failure.
	scalar - Hash reference on success.

See Also:
	<getZClusterLocalIp>, <getZClusterStatus>, <setKeepalivedConfig>, <getZClusterRemoteHost>, <parallel_run>, <runSync>, <runZClusterRemoteManager>, <getZCusterStatusInfo>

	<setConntrackdConfig>, <setDOSSshBruteForceRule>

	zapi/v3/interface.cgi, zapi/v3/cluster.cgi, zeninotify.pl, cluster_status.pl, zevenet
=cut
sub getZClusterConfig
{
	require Config::Tiny;
	require Zevenet::Config;

	my $filecluster = &getGlobalConfiguration('filecluster');

	if ( ! -f $filecluster )
	{
		open my $zcl_file, '>', $filecluster;

		if ( ! $zcl_file )
		{
			&zenlog("Could not create file $filecluster: $!");
			return undef;
		}

		close $zcl_file;
	}
	
	my $config = Config::Tiny->read( $filecluster );

	# returns object on success or undef on error.
	return $config;
}

=begin nd
Function: setZClusterConfig

	Store cluster configuration.

Parameters:
	config - Reference to hash with cluster configuration.

Returns:
	none - .

See Also:
	zapi/v3/cluster.cgi
=cut
sub setZClusterConfig
{
	my $config = shift;

	# returns true on success or undef on error,
	return $config->write( &getGlobalConfiguration('filecluster') );
}

=begin nd
Function: getZClusterRunning

	Get if the cluster controller is running in localhost.

Parameters:
	none - .

Returns:
	boolean - TRUE if the cluster is running, or FALSE otherwise.

See Also:
	<enableZCluster>, <runZClusterRemoteManager>, <getZCusterStatusInfo>

	zcluster-manager, zevenet
=cut
sub getZClusterRunning
{
	return ( system( "pgrep keepalived >/dev/null" ) == 0 );
}

=begin nd
Function: enableZCluster

	Start the cluster controller, keepalived, and conntrackd.

	Also adds the cluster mantenance interface.

Parameters:
	prio - Sets a non-default priority to start the cluster controller. Used only when starting the node on an already running cluster.

Returns:
	integer - ERRNO or return code starting the cluster controller.

See Also:
	zapi/v3/cluster.cgi, zcluster-manager, zevenet
=cut
sub enableZCluster
{
	my $prio = shift;

	#~ my $zcl_conf = &getZClusterConfig();

	my $error_code = &setKeepalivedConfig( $prio );

	if ( $error_code )
	{
		&zenlog("An error happened setting vrrp configuration");
		return 1;
	}

	require Zevenet::Net::Interface;

	# create dummy interface
	unless ( &getSystemInterface( $maint_if ) )
	{
		my $ip_bin = &getGlobalConfiguration('ip_bin');

		&zenlog("Starting cluster maintenance interface");

		# create the interface and put it up
		my $ip_cmd = "$ip_bin link add name $maint_if type dummy";
		&logAndRun( $ip_cmd );

		if ( &getSystemInterface( 'dummy0' ) )
		{
			# remove interface auto-created loading dummy-interface module
			my $ip_cmd = "$ip_bin link delete dummy0 type dummy";
			&logAndRun( $ip_cmd );
		}

		$ip_cmd = "$ip_bin link set $maint_if up";
		&logAndRun( $ip_cmd );
	}

	# start or reload keepalived
	if ( &getZClusterRunning() )
	{
		&zenlog("Reloading keepalived service");

		#~ my $ka_cmd = "/etc/init.d/keepalived reload >/dev/null 2>&1";
		my $ka_cmd = "/etc/init.d/keepalived reload";
		$error_code = &logAndRun( $ka_cmd );

		&zenlog("Reloading keepalived service output: $error_code");
	}
	else
	{
		&zenlog("Starting keepalived service");

		# WARNING: Sometimes keepalived needs to be stopped before it can be started
		my $ka_cmd = "/etc/init.d/keepalived stop >/dev/null 2>&1";
		#~ my $ka_cmd = "/etc/init.d/keepalived stop";
		$error_code = &logAndRun( $ka_cmd );

		$ka_cmd = "/etc/init.d/keepalived start >/dev/null 2>&1";
		#~ $ka_cmd = "/etc/init.d/keepalived start";
		$error_code = &logAndRun( $ka_cmd );

		if ( &pgrep( "keepalived" ) )
		{
			&zenlog("Error starting Keepalived service");
			return 1;
		}
	}

	# conntrackd
	require Zevenet::Conntrackd;
	unless ( -f &getGlobalConfiguration('conntrackd_conf') )
	{
		&setConntrackdConfig();
	}

	if ( &getConntrackdRunning() )
	{
		&stopConntrackd();
	}

	&startConntrackd();

	return $error_code;
}

=begin nd
Function: disableZCluster

	Stops the cluster controller, keepalived, and conntrackd.

	Also removes the cluster mantenance interface.

Parameters:
	none - .

Returns:
	integer - ERRNO or return code stopping the cluster controller.

See Also:
	zapi/v3/cluster.cgi, zcluster-manager, zevenet
=cut
sub disableZCluster
{
	my $error_code = system("/etc/init.d/keepalived stop >/dev/null 2>&1");

	require Zevenet::Net::Interface;
	require Zevenet::Conntrackd;
	require Zevenet::Ssyncd;

	# conntrackd
	if ( &getConntrackdRunning() )
	{
		&stopConntrackd();
	}

	# ssyncd
	&setSsyncdDisabled();

	# remove dummy interface
	if ( &getSystemInterface( $maint_if ) )
	{
		&zenlog("Removing cluster maintenance interface");

		my $ip_bin = &getGlobalConfiguration('ip_bin');

		# create the interface and put it up
		my $ip_cmd = "$ip_bin link delete $maint_if type dummy";
		&logAndRun( $ip_cmd );
	}

	# Remove cluster exception not to block traffic from the other node of cluster
	&setZClusterIptablesException( "delete" );

	return $error_code;
}

=begin nd
Function: setKeepalivedConfig

	Apply to keepalive configuration file the settings in the cluster.

Parameters:
	prio - Sets a non-default priority.

Returns:
	none - .

See Also:
	<enableZCluster>, zcluster-manager
=cut
sub setKeepalivedConfig
{
	my $prio = shift;

	require Zevenet::SystemInfo;

	&zenlog("Setting keepalived configuration file");
	
	my $zcl_conf = &getZClusterConfig();
	my $keepalived_conf = &getGlobalConfiguration('keepalived_conf');

	open my $ka_file, '>', $keepalived_conf;

	if ( ! $ka_file )
	{
		&zenlog("Could not open file $keepalived_conf: $!");
		return 1;
	}

	my $localhost = &getHostname();
	my $remotehost = &getZClusterRemoteHost();
	my $priority;

	if ( $prio )
	{
		$priority = $prio;
	}
	else
	{
		$priority = ( $zcl_conf->{_}->{ primary } eq $localhost )? 120: 50;
	}

	my $ka_conf = "! Zen Load Balancer configuration file for keepalived

vrrp_instance ZCluster {
\tinterface $zcl_conf->{_}->{interface}
\tvirtual_router_id 1
\tpriority $priority
\tadvert_int $zcl_conf->{_}->{deadratio}
\tgarp_master_delay 1

\ttrack_interface {
\t\t$maint_if
\t}
\t#authentication {	#}

\tunicast_src_ip $zcl_conf->{$localhost}->{ip}
\tunicast_peer {
\t\t$zcl_conf->{$remotehost}->{ip}
\t}

\tnotify_master	\"/usr/local/zevenet/app/zbin/zcluster-manager notify_master\"
\tnotify_backup	\"/usr/local/zevenet/app/zbin/zcluster-manager notify_backup\"
\tnotify_fault	\"/usr/local/zevenet/app/zbin/zcluster-manager notify_fault\"
\tnotify		\"/usr/local/zevenet/app/zbin/zcluster-manager\"
}

";

	print { $ka_file } "$ka_conf";

    # notify scripts and alerts are optional
    #
    # filenames of scripts to run on transitions
    # can be unquoted (if just filename)
    # or quoted (if it has parameters)
    # to MASTER transition
    #~ notify_master /path/to_master.sh
    #
    # to BACKUP transition
    #~ notify_backup /path/to_backup.sh
    #
    # FAULT transition
    #~ notify_fault "/path/fault.sh VG_1"
	#
    # for ANY state transition.
    # "notify" script is called AFTER the
    # notify_* script(s) and is executed
    # with 3 arguments provided by Keepalived
    # (so don't include parameters in the notify line).
    # arguments
    # $1 = "GROUP"|"INSTANCE"
    # $2 = name of the group or instance
    # $3 = target state of transition
    #     ("MASTER"|"BACKUP"|"FAULT")

	close $ka_file;

	return 0;
}

=begin nd
Function: getZClusterRemoteHost

	Get the hostname of the remote node.

Parameters:
	none - .

Returns:
	string - Remote node hostname.

See Also:
	<setConntrackdConfig>,<setKeepalivedConfig>, <runZClusterRemoteManager>, <getZCusterStatusInfo>, <setDOSSshBruteForceRule>, <getZClusterNodeStatusInfo>

	zapi/v3/cluster.cgi, cluster_status.pl, zevenet
=cut
sub getZClusterRemoteHost
{
	require Zevenet::SystemInfo;

	my $zcl_conf = &getZClusterConfig();
	my $hostname = &getHostname();
	my @hosts = keys %{ $zcl_conf };
	my $remotehost;

	for my $zcl_key ( keys %{ $zcl_conf } )
	{
		next if $zcl_key eq '_';
		next if $zcl_key eq $hostname;

		$remotehost = $zcl_key;
		last;
	}

	return $remotehost;
}

=begin nd
Function: parallel_run

	NOT USED (yet?). Run a command on every node of the cluster via ssh.

	WARNING: Requires the command 'parallel-ssh'.

Parameters:
	cmd - Command to run.

Returns:
	Returns the output of the command parallel-ssh.

Bugs:
	NOT USED (yet?).
=cut
#sub parallel_run # `output` ( $cmd )
#{
#	my $cmd = shift;
#
#	my %config = %{ &getZClusterConfig() };
#	my $host_list;
#
#	for my $key ( keys %config )
#	{
#		next if $key eq '_';
#		#~ &zenlog("key:$key");
#
#		my $host = $config{$key}{ip};
#
#		#~ &zenlog("host:$host");
#
#		$host_list .= "-H $host ";
#	}
#
#	#~ &zenlog("host_list:$host_list");
#
#	#~ $output = `parallel-ssh $host_list '$cmd'`;
#	#~ &zenlog("parallel_run output:$output");
#	#~ return $output;
#
#	return `parallel-ssh $host_list '$cmd'`;
#}

################################# SSH-KEY #################################

=begin nd
Function: generateIdKey

	Generate private and public RSA keys. Used in the process of cluster configuration if required.

Parameters:
	none - .

Returns:
	integer - ERRNO or return code generating the keys.

See Also:
	<exchangeIdKeys>
=cut
sub generateIdKey # $rc ()
{
	my $key_path = &getGlobalConfiguration('key_path');
	my $keygen_cmd = &getGlobalConfiguration('keygen_cmd');

	if ( ! -e $key_path )
	{
		mkdir $key_path;
	}

	my $gen_output = `$keygen_cmd 2>&1`;
	my $error_code = $?;

	if ( $error_code != 0 )
	{
		&zenlog("An error happened generating the RSA id key: $gen_output");
	}

	return $error_code;
}

=begin nd
Function: copyIdKey

	Send the local public RSA key to the indicated remote node.

Parameters:
	ip_address - Remote node cluster ip address.
	password - Remote node root password.

Returns:
	integer - ERRNO or return code copying the public key to the remote node.

See Also:
	<exchangeIdKeys>
=cut
sub copyIdKey # $rc ( $ip_addr, $pass )
{
	my $ip_address = shift;
	my $password   = shift;

	my $safe_password = quotemeta( $password );

	my $copyId_cmd = "HOME=\"/root\" /usr/local/zevenet/app/zbin/ssh-copy-id.sh $safe_password root\@$ip_address";

	my $copy_output = `$copyId_cmd`; # WARNING: Do not redirect stderr to stdout
	my $error_code = $?;

	if ( $error_code != 0 )
	{
		&zenlog("An error happened copying the Id key to the host $ip_address: $copy_output");
	}

	return $error_code;
}

=begin nd
Function: exchangeIdKeys

	This procedure exchanges plublic RSA keys between two nodes. Also generates the RSA keys if required.

Parameters:
	ip_address - Remote node cluster ip address.
	password - Remote node root password.

Returns:
	0 - On success.
	1 - On failure.

See Also:
	zapi/v3/cluster.cgi
=cut
sub exchangeIdKeys # $bool ( $ip_addr, $pass )
{
	my $ip_address = shift;
	my $password   = shift;

	my $key_path = &getGlobalConfiguration( 'key_path' );
	my $key_id   = &getGlobalConfiguration( 'key_id' );

	#### Check for local key ID ####

	# 1) generate id key if it doesn't exist
	if ( ! -e "$key_path/$key_id" )
	{
		my $return_code = &generateIdKey();

		if ( $return_code || ! -f "$key_path/$key_id" )
		{
			&zenlog("Key ID $key_path/$key_id does not exist, aborting.");
			return 1;
		}
	}

	# 2) install the key in the remote node
	my $error_code = &copyIdKey( $ip_address, $password );

	return 1 if ( $error_code != 0 );

	#### Check for remote key ID ####

	# 1) generate id key in remote node if it doesn't exist
	&runRemotely("ls $key_path/$key_id 2>/dev/null", $ip_address );
	$error_code = $?;

	if ( $error_code != 0 )
	{
		my $keygen_cmd = &getGlobalConfiguration('keygen_cmd');
		$keygen_cmd =~ s/'/"/g; # change included quotes for remote execution

		my $gen_output = &runRemotely("$keygen_cmd 2>&1", $ip_address);
		my $error_code = $?;

		if ( $error_code != 0 )
		{
			&zenlog("An error happened generating the RSA id key remotely: $gen_output");
			return 1;
		}
	}

	# 2) install remote key in the localhost
	my $key_id_pub = &runRemotely("cat $key_path/$key_id.pub 2>&1", $ip_address );
	$error_code = $?;

	if ( $error_code != 0 )
	{
		&zenlog("An error happened getting the remote public key: $key_id_pub");
		return 1;
	}

	my $auth_keys_path = "$key_path/authorized_keys";
	open my $auth_keys, '<', $auth_keys_path;

	my $found_key = grep /$key_id_pub/, $auth_keys;
	close $auth_keys;

	if ( ! $found_key )
	{
		open my $auth_keys, '>>', $auth_keys_path;

		return 1 if ( ! $auth_keys );

		print $auth_keys $key_id_pub;
		close $auth_keys;
	}

	# ended successfully
	return 0;
}

=begin nd
Function: runRemotely

	Run a command on a remote host via ssh.

Parameters:
	cmd - Command to be run.
	ip_address - Remote ip addtress.
	port - SSH port. Optional. (Default: 22)

Returns:
	Returns remote command output.

See Also:
	<exchangeIdKeys>, <checkZClusterInterfaces>, <runZClusterRemoteManager>, <getZCusterStatusInfo>, 

	zapi/v3/cluster.cgi
=cut
sub runRemotely # `output` ( $cmd, $ip_addr [, $port ] )
{
	my $cmd        = shift;
	my $ip_address = shift;
	my $port       = shift // '22';

	my $ssh_options = '';
	$ssh_options .= '-o "ConnectTimeout=2" '; # ssh-connect timeout
	$ssh_options .= '-o "StrictHostKeyChecking=no" ';

	# log the command to be run
	my $ssh     = &getGlobalConfiguration( 'ssh' );
	my $ssh_cmd = "$ssh $ssh_options root\@$ip_address '$cmd'";

	&zenlog("Running remotely: \@$ip_address: $cmd") if &debug();
	&zenlog("Running: $ssh_cmd") if &debug() > 2;

	# capture output and return it
	return `$ssh_cmd 2>/dev/null`;
}

=begin nd
Function: zsync

	Synchronize a local directory with a remote node.

	The synchronization is made with rsync, via ssh.

Parameters:
	args - Hash reference.

	Hash keys:

	path    - Path to be synchronized.
	ip_addr - Remote node IP address.
	exclude - Files or directories to be excluded. Optional.
	include - Files or directories to be included. Optional.

	Input format example:

	$args = {
		path    => '/dir/',
		ip_addr => '10.0.0.20',
		exclude => [ '/dir/foo',      '/dir/*.cgi',  ... ],	# optional
		include => [ '/dir/foo/test', '/dir/A*.cgi', ... ],	# optional
	};

Returns:
	integer - ERRNO or return code of synchronization process.

See Also:
	<runSync>
=cut
sub zsync
{
	my $args = shift;

	if ( ref $args ne 'HASH' )
	{
		&zenlog( ( caller )[3] . ": Invalid hash reference.");
		die;
	}

	#~ &zenlog( "running zsync with $args->{ip_addr} for $args->{path}" );

	my $exclude = '';
	for my $pattern ( @{ $args->{exclude} } )
	{
		#~ &zenlog( "exclude:$pattern" );
		$exclude .= "--exclude=\"$pattern\" ";
	}
	
	my $include = '';
	for my $pattern ( @{ $args->{include} } )
	{
		#~ &zenlog( "include:$pattern" );
		$include .= "--include=\"$pattern\" ";
	}

	#~ my $zenrsync = "$zenrsync --dry-run";

	my $user = 'root';
	my $host = $args->{ip_addr};
	my $path = $args->{path};

	my $src = "$path";
	$src .= '/' if -d $path;
	my $dest = "$user\@$host:$path";

	my $rsync = &getGlobalConfiguration('rsync');
	my $zenrsync = &getGlobalConfiguration('zenrsync');
	my $rsync_cmd = "$rsync $zenrsync $include $exclude $src $dest";

	&zenlog( "Running: $rsync_cmd" );
	my $rsync_output = `$rsync_cmd`;
	my $error_code = $?;

	#~ &zenlog_thread("$rsync_output");

	if ( $error_code )
	{
		&zenlog_thread( $rsync_output );
	}

	return $error_code;
}

=begin nd
Function: runSync

	Sync a path with the remote node.

Parameters:
	src_path - Path to be synchronized.

Returns:
	none - .

See Also:
	zapi/v3/cluster.cgi, zeninotify.pl, zcluster-manager
=cut
sub runSync
{
	my $src_path = shift;

	#~ &zenlog("starting runSync");

	require Zevenet::SystemInfo;

	#~ my @excluded_paths = @_;
	my @excluded_files = (
		"lost+found",
		"global.conf",
		"if_*_conf",
		"zencert-c.key",
		"zencert.pem",
		"zlb-start",
		"zlb-stop",
	);

	my $cl_conf = &getZClusterConfig(); # cluster configuration hash
	#~ my $local_ip = &iponif( $cl_conf->{_}->{interface} );

	if ( ! $cl_conf )
	{
		&zenlog( "Cluster configuration not found. Aborting sync." );
		return 1;
	}

	my @args;
	for my $key ( keys %{ $cl_conf } )
	{
		next if $key eq '_';
		next if $key eq &getHostname();
		#~ next if $cl_conf->{$key}->{ip} eq $local_ip;

		#~ &zenlog("runSync key:$key");

		#~ &zenlog("Element:$element");
		#~ &zenlog("Adding $cl_conf->{$element}->{ip}");

		my %arg = (
			exclude => \@excluded_files,
			include => [ "if_*:*_conf" ],
			#~ exclude => [ '*' ],
			#~ include => [ "$target" ],
			ip_addr => $cl_conf->{$key}->{ip},
			path => $src_path,
		);

		#~ &zenlog("Element:$element ($cl_conf->{$element}->{ip})");
		#~ &zenlog("Adding $cl_conf->{$element}->{ip}");
		push( @args, \%arg );
		#~ &zenlog( Dumper \%arg );
	}

	# WARNING: as a temporal workaround run zsync once
	#          since there is only one more node.
	&zsync( $args[0] );

	#~ # run in parallel
	#~ my $r_list = &runParallel( \&zsync, \@args );

	#~ for my $rc ( @{ $r_list } )
	#~ {
		#~ &zenlog("Return[$rc->{tid}] $rc->{ret_val}");
		
		#~ if ( $rc->{ret_val} )
		#~ {
			#~ &zenlog( "An error happened syncing with $rc->{arg}->{ip_addr}");
		#~ }
	#~ }
}

=begin nd
Function: getZClusterNodeStatus

	Get the status of the local node in the cluster.

Parameters:
	none - .

Returns:
	undef  - There is no status file of the local node.
	string - Local node status. master, backup or maintenance.

See Also:
	<getClusterInfo>, <runZClusterRemoteManager>, <getZCusterStatusInfo>, <getZClusterNodeStatusInfo>

	zapi/v3/cluster.cgi, zcluster-manager, zevenet
=cut
sub getZClusterNodeStatus
{
	require Zevenet::Config;

	my $znode_status_file = &getGlobalConfiguration('znode_status_file');
	open my $znode_status, '<', $znode_status_file;

	if ( ! $znode_status )
	{
		#~ &zenlog( "Could not open file $znode_status_file: $!" );
		return undef;
	}

	my $status = <$znode_status>;
	chomp $status;

	return $status;
}

=begin nd
Function: setZClusterNodeStatus

	Store the status of the local node.

Parameters:
	node_status - New node status: master, backup or maintenance.

Returns:
	0 - On success.
	1 - On failure.

See Also:
	zapi/v3/cluster.cgi, zcluster-manager
=cut
sub setZClusterNodeStatus
{
	my $node_status = shift;

	if ( $node_status !~ /^(master|backup|maintenance)$/ )
	{
		&zenlog("\"$node_status\" is not an accepted node status");
		return 1;
	}

	my $znode_status_file = &getGlobalConfiguration('znode_status_file');
	open my $znode_status, '>', $znode_status_file;

	if ( ! $znode_status )
	{
		&zenlog( "Could not open file $znode_status_file: $!" );
		return 1;
	}

	print { $znode_status } "$node_status\n";

	close $znode_status;

	return 0;
}

=begin nd
Function: disableInterfaceDiscovery

	Disable interface broadcast discovery, ARP or NDP (Neighbour Discovery Protocol).

Parameters:
	iface - Virtual interface name.

Returns:
	0 - On success.
	1 - On failure.

See Also:
	zcluster-manager, zevenet
=cut
sub disableInterfaceDiscovery
{
	my $iface = shift;

	if ( $iface->{ ip_v } == 4 )
	{
		my $arptables = &getGlobalConfiguration('arptables');
		return &logAndRun( "$arptables -A INPUT -d $iface->{ addr } -j DROP" );
	}
	elsif ( $iface->{ ip_v } == 6 )
	{
		&zenlog("WARNING: disableInterfaceDiscovery pending for IPv6");
		return 0;
	}
	else
	{
		&zenlog("IP version not supported");
		return 1;
	}
}

=begin nd
Function: enableInterfaceDiscovery

	Enable interface broadcast discovery, ARP or NDP (Neighbour Discovery Protocol).

Parameters:
	iface - Virtual interface name.

Returns:
	0 - On success.
	1 - On failure.

See Also:
	zcluster-manager
=cut
sub enableInterfaceDiscovery
{
	my $iface = shift;

	if ( $iface->{ ip_v } == 4 )
	{
		my $arptables = &getGlobalConfiguration('arptables');
		return &logAndRun( "$arptables -D INPUT -d $iface->{ addr } -j DROP" );
	}
	elsif ( $iface->{ ip_v } == 6 )
	{
		&zenlog("WARNING: enableInterfaceDiscovery pending for IPv6");
		return 0;
	}
	else
	{
		&zenlog("IP version not supported");
		return 1;
	}
}

=begin nd
Function: enableAllInterfacesDiscovery

	Enable interface broadcast discovery for all interfaces, ARP or NDP (Neighbour Discovery Protocol).

Parameters:
	none - .

Returns:
	integer - 0 on success, or failure otherwise.

See Also:
	zcluster-manager, zevenet
=cut
sub enableAllInterfacesDiscovery
{
	# IPv4
	my $arptables = &getGlobalConfiguration('arptables');
	my $rc = &logAndRun( "$arptables -F" );

	# IPv6
	&zenlog("WARNING: enableInterfaceDiscovery pending for IPv6");

	return $rc;
}

=begin nd
Function: broadcastInterfaceDiscovery

	Advertise interface to be discovered.

Parameters:
	iface - Interface name.

Returns:
	0 - On success.
	1 - On failure.

See Also:
	zcluster-manager
=cut
sub broadcastInterfaceDiscovery
{
	my $iface = shift;

	&zenlog("Sending GArping for $iface->{ name }: $iface->{ addr }");

	if ( $iface->{ ip_v } == 4 )
	{
		require Zevenet::Net::Util;

		# arping
		&sendGArp( $iface->{ name }, $iface->{ addr } );
	}
	elsif ( $iface->{ ip_v } == 6 )
	{
		&zenlog("WARNING: broadcastInterfaceDiscovery pending for IPv6");
	}
	else
	{
		&zenlog("IP version not supported");
		return 1;
	}

	return 0;
}

=begin nd
Function: runZClusterRemoteManager

	Run zcluster-manager on remote node.

Parameters:
	object - Can be: farm | interface | ipds.

		Or a supported function like:

		enableZCluster, disableZCluster, setKeepalivedConfig, setConntrackdConfig, getZClusterRunning, getZClusterNodeStatus, getConntrackdRunning, getZClusterArpStatus, sync, notify_master, notify_backup, notify_fault, gateway.

	command - A supported command.

		Supported commands for object 'farm': start | stop | restart | delete.
		Supported commands for object 'ipds': restart_bl | restart_dos.
		Supported commands for object 'interface': start | stop | delete | float-update.

	arguments - Arguments are used to indicate an instance:

		With the object farm: the farm name.
		With the object interface: the interface name.

Returns:
	integer - 0 on success, or failure otherwise.

See Also:
	Unsed in:

	zapi/v3/put.cgi,
	zapi/v3/interface.cgi,
	zapi/v3/farm_actions.cgi,
	zapi/v3/put_l4.cgi,
	zapi/v3/post_gslb.cgi,
	zapi/v3/delete_gslb.cgi,
	zapi/v3/ipds.cgi,
	zapi/v3/post.cgi,
	zapi/v3/put_datalink.cgi,
	zapi/v3/delete.cgi
=cut
sub runZClusterRemoteManager
{
	my $object = shift;
	my $command = shift;
	my @arguments = shift;

	# zcluster: start farm in remote node
	if ( &getZClusterRunning() && &getZClusterNodeStatus() eq 'master' )
	{
		my $zcl_conf = &getZClusterConfig();
		my $remote_hostname = &getZClusterRemoteHost();
		my $zcluster_manager = &getGlobalConfiguration('zcluster_manager');

		# start remote interfaces, farms and cluster
		my $cl_output = &runRemotely(
			"$zcluster_manager $object $command @arguments",
			$zcl_conf->{$remote_hostname}->{ip}
		);

		my $rc = $?;
		my $msg = "rc:$rc";
		$msg .= " $cl_output" if $rc;

		&zenlog( $msg );

		return $rc;
	}

	return 0;
}

=begin nd
Function: pgrep

	Check if a command is running.

Parameters:
	cmd - Command to be checked.

Returns:
	integer - 0 on success, or failure otherwise.

See Also:
	<getZClusterNodeStatusInfo>, <enableZCluster>
=cut
sub pgrep
{
	my $cmd = shift;

	# return_code
	my $rc = system("/usr/bin/pgrep $cmd >/dev/null");

	#~ &zenlog("$cmd not found running") if $rc && &debug();

	return $rc;
}

=begin nd
Function: getZClusterNodeStatusInfo

	Get node role and cluster services status.

Parameters:
	ip - Remote IP address for a remote host, or undef for localhost.

Returns:
	scalar - Hash reference.

	Hash reference example:

	$node = {
		ka   => 'value',
		zi   => 'value',
		ct   => 'value',
		role => 'value'
	}

See Also:
	<getZClusterLocalhostStatusDigest>, <getZClusterNodeStatusDigest>, cluster_status.pl
=cut
sub getZClusterNodeStatusInfo
{
	my $ip = shift; # IP for remote host, or undef for local host

	my $node; # output
	my $ssyncd_enabled = &getGlobalConfiguration('ssyncd_enabled');
	my $ssyncdctl_bin = &getGlobalConfiguration('ssyncdctl_bin');

	if ( ! defined( $ip ) || $ip eq &getZClusterLocalIp() )
	{
		$node->{ ka } = pgrep('keepalived');
		$node->{ zi } = pgrep('zeninotify.pl');
		$node->{ ct } = pgrep('conntrackd');

		chomp( ( $node->{ sy } ) = `$ssyncdctl_bin show mode` ) if $ssyncd_enabled eq 'true';

		$node->{ role } = &getZClusterNodeStatus();
	}
	else
	{
		&runRemotely("pgrep keepalived", $ip );
		$node->{ ka } = $?;

		&runRemotely("pgrep zeninotify.pl", $ip );
		$node->{ zi } = $?;

		&runRemotely("pgrep conntrackd", $ip );
		$node->{ ct } = $?;

		chomp( ( $node->{ sy } ) = &runRemotely("$ssyncdctl_bin show mode", $ip ) ) if $ssyncd_enabled eq 'true';

		my $zcluster_manager = &getGlobalConfiguration('zcluster_manager');

		$node->{ role } = &runRemotely("$zcluster_manager getZClusterNodeStatus", $ip );
		chomp $node->{ role };
	}

	return $node;
}

=begin nd
Function: getZClusterNodeStatusDigest

	Get a comprehensible information about the state of a cluster node.

Parameters:
	ip - Remote IP address for a remote host, or undef for localhost.

Returns:
	scalar - Hash reference.

	Hash reference example:

	$node = {
		role    => 'value',
		status  => 'value',
		message => 'value',
	}


	Role values:
		master | backup | maintenance | unreachable | error

	Status values:
		ok | failure | unreachable | error

	Messages:
		'Node online and active'
		'Node online and passive'
		'Node in maintenance mode'
		'Services not running: '
		'Failed services: ...'
		'Node unreachable'
		'error'

See Also:
	<getZClusterLocalhostStatusDigest>, zapi/v3/cluster.cgi
=cut
sub getZClusterNodeStatusDigest
{
	my $ip = shift; # IP for remote host, or undef for local host

	my $ssyncd_enabled = &getGlobalConfiguration( 'ssyncd_enabled' );
	my $n              = &getZClusterNodeStatusInfo( $ip );
	my $node->{ role } = $n->{ role };

	if ( $node->{ role } eq 'master' )
	{
		my $ssync_ok = $ssyncd_enabled eq 'false' || $n->{ sy } eq 'master';

		if ( !$n->{ ka } && !$n->{ zi } && !$n->{ ct } && $ssync_ok )
		{
			$node->{ status }  = 'ok';
			$node->{ message } = 'Node online and active';
		}
		else
		{
			$node->{ status }  = 'failure';
			$node->{ message } = 'Failed services: ';
			my @services;
			push ( @services, 'keepalived' )    if $n->{ ka };
			push ( @services, 'zeninotify.pl' ) if $n->{ zi };
			push ( @services, 'conntrackd' )    if $n->{ ct };
			push ( @services, 'ssyncd' )        unless $ssync_ok;
			$node->{ message } .= join ', ', @services;
		}
	}
	elsif ( $node->{ role } eq 'backup' )
	{
		my $ssync_ok = $ssyncd_enabled eq 'false' || $n->{ sy } eq 'backup';

		if ( !$n->{ ka } && $n->{ zi } && !$n->{ ct } && $ssync_ok )
		{
			$node->{ status } = 'ok';
			$node->{ message } = 'Node online and passive';
		}
		else
		{
			$node->{ status }  = 'failure';
			$node->{ message } = 'Failed services: ';
			my @services;
			push ( @services, 'keepalived' )    if $n->{ ka };
			push ( @services, 'zeninotify.pl' ) if !$n->{ zi };
			push ( @services, 'conntrackd' )    if $n->{ ct };
			push ( @services, 'ssyncd' )        unless $ssync_ok;
			$node->{ message } .= join ', ', @services;
		}
	}
	elsif ( $node->{ role } eq 'maintenance' )
	{
		my $ssync_ok = $ssyncd_enabled eq 'false' || $n->{ sy } eq 'error';

		if ( !$n->{ ka } || $n->{ zi } || !$n->{ ct } || $ssync_ok )
		{
			$node->{ status }  = 'ok';
			$node->{ message } = 'Node in maintenance mode';
		}
		else
		{
			$node->{ status }  = 'failure';
			$node->{ message } = 'Services not running: ';
			my @services;
			push ( @services, 'keepalived' )    if $n->{ ka };
			push ( @services, 'zeninotify.pl' ) if !$n->{ zi };
			push ( @services, 'conntrackd' )    if $n->{ ct };
			push ( @services, 'ssyncd' )        unless $ssync_ok;
			$node->{ message } .= join ', ', @services;
		}
	}
	elsif ( $node->{ role } eq '' )
	{
		$node->{ role }    = 'unreachable';
		$node->{ status }  = 'unreachable';
		$node->{ message } = 'Node unreachable';
	}
	else
	{
		$node->{ role }    = 'error';
		$node->{ status }  = 'error';
		$node->{ message } = 'error';
	}

	return $node;
}

=begin nd
Function: setZClusterIptablesException

	Add a list of iptable rules  to never block traffic from/to the other node of cluster

Parameters:
	Action - The available actions are "insert", insert rules in the first position of the iptables chains;
	or "delete", delete the iptables rules.

Returns:
	Integer - It is the error code, 0 on success or other value on failure.

See Also:
	zapi/v3/cluster.cgi, zenloadbalancer
=cut

sub setZClusterIptablesException
{
	my $option = shift;

	# return if the node is not in a cluster
	return 0 unless &getZClusterStatus();

	require Zevenet::Netfilter;
	require Zevenet::Conntrackd;
	require Zevenet::IPDS::Core;

	my $error;
	my $action;
	
	if ( $option eq "insert" )
	{
		$action = "-I";
	}
	elsif ( $option eq "delete" )
	{
		$action = "-D" ;
	}
	else
	{
		return -1;
	 }
	
	my $config    = &getZClusterConfig();
	my $remote_hn = &getZClusterRemoteHost();
	my $ipremote  = $config->{ $remote_hn }->{ ip };
	my $iptables  = &getGlobalConfiguration( 'iptables' );
	my $ipt_args  = '-j ACCEPT -m comment --comment "cluster_exception"';
	my $chain = &getIPDSChain( 'whitelist' );

	# Avoid blacklist rules and rbl rules
	my $cmd = "$iptables $action $chain -t raw -s $ipremote $ipt_args";
	$error = &iptSystem( $cmd );
	
	return -1 if $error;

	# Avoid the dos rules
	$cmd = "$iptables $action $chain -t mangle -s $ipremote $ipt_args";
	$error = &iptSystem( $cmd );
	
	return $error;
}

sub zClusterFarmUp
{
	my ( $farm_name ) = @_;

	my $ssyncd_enabled = &getGlobalConfiguration( 'ssyncd_enabled' );

	if ( $ssyncd_enabled eq 'true' )
	{
		require Zevenet::Ssyncd;
		&setSsyncdFarmUp( $farm_name );
	}

	return 0;
}

sub zClusterFarmDown
{
	my ( $farm_name ) = @_;

	my $ssyncd_enabled = &getGlobalConfiguration( 'ssyncd_enabled' );

	if ( $ssyncd_enabled eq 'true' )
	{
		require Zevenet::Ssyncd;
		&setSsyncdFarmDown( $farm_name );
	}

	return 0;
}

sub getKeepalivedVersion
{
	my ( $line ) = `keepalived -v 2>&1`;
	my ( $version ) = $line =~ / v([1-9]+\.[1-9]+\.[1-9]+)/;

	return $version;
}

1;
