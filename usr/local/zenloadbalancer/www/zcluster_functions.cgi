###############################################################################
#
#     Zen Load Balancer Software License
#     This file is part of the Zen Load Balancer software package.
#
#     Copyright (C) 2014 SOFINTEL IT ENGINEERING SL, Sevilla (Spain)
#
#     This library is free software; you can redistribute it and/or modify it
#     under the terms of the GNU Lesser General Public License as published
#     by the Free Software Foundation; either version 2.1 of the License, or
#     (at your option) any later version.
#
#     This library is distributed in the hope that it will be useful, but
#     WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
#     General Public License for more details.
#
#     You should have received a copy of the GNU Lesser General Public License
#     along with this library; if not, write to the Free Software Foundation,
#     Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
###############################################################################

require "/usr/local/zenloadbalancer/www/thread_functions.cgi";
require "/usr/local/zenloadbalancer/www/conntrackd_functions.cgi";

sub getClusterInfo
{
	my $cluster_msg  = "Not configured";
	my $cluster_icon = "fa-cog yellow";

	if ( &getZClusterStatus() )
	{
		$cluster_msg = &getZClusterNodeStatus();
		
		if ( $cluster_msg eq 'master' )
		{
			$cluster_icon = "fa-cog green";
		}
		elsif ( $cluster_msg eq 'maintenance' )
		{
			$cluster_icon = "fa-cog red";
		}
		elsif ( $cluster_msg eq 'backup' )
		{
			$cluster_icon = "fa-cog green";
		}

		$cluster_msg = ucfirst $cluster_msg;
	}

	return ( $cluster_msg, $cluster_icon );
}

sub getClusterStatus
{
	my ( $cluster_msg, $cluster_icon ) = &getClusterInfo();
	
	if ( $cluster_msg eq "Not configured" )
	{
		print
		  "<div class=\"grid_6\"><p class=\"cluster\"><a href=\"http://www.zenloadbalancer.com/eliminate-a-single-point-of-failure/\" target=\"_blank\"><i class=\"fa fa-fw $cluster_icon action-icon\" title=\"How to eliminate this single point of failure\"></i></a> Cluster status: $cluster_msg</p></div>";
		print "<div class=\"clear\"></div>";
	}
	else
	{
		print
		  "<div class=\"grid_6\"><p class=\"cluster\"><i class=\"fa fa-fw $cluster_icon action-icon\"></i> Cluster status: $cluster_msg</p></div>";
		print "<div class=\"clear\"></div>";
	}
}

sub getZClusterLocalIp
{
	return undef if ! &getZClusterStatus();
	
	my $zcl_conf = getZClusterConfig();

	return $zcl_conf->{ &getHostname() }->{ ip };
}

################################################################################

sub getZClusterStatus
{
	# case filecuster does not exist
	return undef if ! -f &getGlobalConfiguration('filecluster');
	
	my $zcl_conf = &getZClusterConfig();

	# $zcl_conf->{_} global section
	# $zcl_conf->{*} node section
	# 1 global section + 2 nodes section
	return ( scalar( keys %{ $zcl_conf } ) > 2  );
}

sub getZClusterConfig
{
	use Config::Tiny;
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

sub setZClusterConfig
{
	my $config = shift;

	# returns true on success or undef on error,
	return $config->write( &getGlobalConfiguration('filecluster') );
}

sub getZClusterRunning
{
	return ( system( "pgrep keepalived >/dev/null" ) == 0 );
}

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

	# start or reload keepalived
	if ( &getZClusterRunning() )
	{
		&zenlog("Reloading keepalived service");
		$error_code = system("/etc/init.d/keepalived reload >/dev/null 2>&1");
	}
	else
	{
		&zenlog("Starting keepalived service");
		$error_code = system("/etc/init.d/keepalived start >/dev/null 2>&1");
	}

	# conntrackd
	if ( -f $conntrackd_conf )
	{
		if ( &getConntrackdRunning() )
		{
			&stopConntrackd();
		}

		&startConntrackd();
	}

	return $error_code;
}

sub disableZCluster
{
	my $error_code = system("/etc/init.d/keepalived stop >/dev/null 2>&1");

	# conntrackd
	if ( &getConntrackdRunning() )
	{
		&stopConntrackd();
	}

	return $error_code;
}

sub setKeepalivedConfig
{
	my $prio = shift;

	&zenlog("Setting keepalived configuration file");
	
	my $zcl_conf = &getZClusterConfig();

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

#~ \tdebug 2

	my $ka_conf = "! Zen Load Balancer configuration file for keepalived

vrrp_instance ZCluster {
\tinterface $zcl_conf->{_}->{interface}
\tvirtual_router_id 1
\tpriority $priority
\tadvert_int $zcl_conf->{_}->{deadratio}
\tgarp_master_delay 1

\t#track_interface { #eth0 #eth1	#}
\t#authentication {	#}

\tunicast_src_ip $zcl_conf->{$localhost}->{ip}
\tunicast_peer {
\t\t$zcl_conf->{$remotehost}->{ip}
\t}

\tnotify_master	\"/usr/local/zenloadbalancer/app/zbin/zcluster-manager notify_master\"
\tnotify_backup	\"/usr/local/zenloadbalancer/app/zbin/zcluster-manager notify_backup\"
\tnotify_fault	\"/usr/local/zenloadbalancer/app/zbin/zcluster-manager notify_fault\"
\tnotify		\"/usr/local/zenloadbalancer/app/zbin/zcluster-manager\"
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

sub getZClusterRemoteHost
{
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

sub parallel_run # `output` ( $cmd )
{
	my $cmd = shift;
	
	my %config = %{ &getZClusterConfig() };
	my $host_list;

	for my $key ( keys %config )
	{
		next if $key eq '_';
		#~ &zenlog("key:$key");

		my $host = $config{$key}{ip};
		
		#~ &zenlog("host:$host");
		
		$host_list .= "-H $host ";
	}
	
	#~ &zenlog("host_list:$host_list");

	#~ $output = `parallel-ssh $host_list '$cmd'`;
	#~ &zenlog("parallel_run output:$output");
	#~ return $output;

	return `parallel-ssh $host_list '$cmd'`;
}

#sub getMasterNode # $ip_addr ()
#{
	#my @sucess_lines = grep /SUCCESS/, &parallel_run( 'ls /etc/MASTER' );
	
	##~ &zenlog("getMasterNode1:@sucess_lines");

	## take from the first line, the forth element
	## sample: [1] 11:46:11 [SUCCESS] 192.168.101.12
	#my $ip_address = ( split / /, $sucess_lines[0] )[3];
	#chomp $ip_address;

	##~ &zenlog("getMasterNode2 ip_address:$ip_address<");
	
	#return $ip_address;
#}

################################# SSH-KEY #################################

sub generateIdKey # $rc ()
{
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

sub copyIdKey # $rc ( $ip_addr, $pass )
{
	my $ip_address = shift;
	my $password = shift;
	
	my $copyId_cmd = "/usr/local/zenloadbalancer/app/zbin/ssh-copy-id.sh $password root@$ip_address";

	my $copy_output = `$copyId_cmd`;
	my $error_code = $?;

	if ( $error_code != 0 )
	{
		&zenlog("An error happened copying the Id key to the host $ip_address: $copy_output");
	}

	return $error_code;
}

sub exchangeIdKeys # $bool ( $ip_addr, $pass )
{
	my $ip_address = shift;
	my $password = shift; 

	# generate id key if it doesn't exist
	if ( ! -e "$key_path/$key_id" )
	{
		my $return_code = &generateIdKey();

		return 1 if ( $return_code != 0 );
	}

	# install the key in the remote node
	my $error_code = &copyIdKey( $ip_address, $password );

	return 1 if ( $error_code != 0 );

	# Reload remote sshd??
	
	# Now we can run commands remotely

	# generate id key in remote node if it doesn't exist
	&runRemotely("ls $key_path/$key_id", $ip_address );
	$error_code = $?;
	
	if ( $error_code != 0 )
	{
		my $gen_output = &runRemotely("$keygen_cmd 2>&1", $ip_address);
		my $error_code = $?;

		if ( $error_code != 0 )
		{
			&zenlog("An error happened generating the RSA id key remotely: $gen_output");
			return 1;
		}
	}
	
	# install remote key in the localhost
	my $local_if = &getInterfaceConfig('eth0', 4); # FIXME: choose the cluster interface
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

	return 0;
}

sub runRemotely # `output` ( $cmd, $ip_addr [, $port ] )
{
	my $cmd = shift;
	my $ip_address = shift;
	my $port = shift // '22';

	my $ssh_options = '';
	$ssh_options .= '-o "ConnectTimeout=10" ';
	$ssh_options .= '-o "StrictHostKeyChecking=no" ';

	# log the command to be run
	my $ssh = &getGlobalConfiguration('ssh');
	my $ssh_cmd = "$ssh $ssh_options root\@$ip_address '$cmd'";
	&zenlog("Running remotely: \@$ip_address: $cmd");
	&zenlog("Running remotely: $ssh_cmd");

	# capture output and return it
	return `$ssh_cmd`;
}

sub checkZClusterInterfaces # @inmatched_ifaces ( $cl_conf, $nodeIP )
{
	my $cl_conf = shift;
	my $nodeIP = shift;

	use NetAddr::IP;

	my @unmatched_ifaces; 

	for my $if_name ( values %{ $cl_conf->{interfaceList} } )
	{
		my $iface = &getInterfaceConfig( $if_name, 4 );

		# get local data
		my $local_addr = new NetAddr::IP ( $iface->{addr}, $iface->{mask} );

		# get remote data
		my @output_line = &runRemotely( "ifconfig $if_name", $nodeIP );

		# strip ipv4
		my ( $output_line ) = grep /inet addr/, @output_line; # get line
		my @line_words = split( /\s+/, $output_line );	# divide into words

		# get ip and mask parts
		my ( $remote_ip ) = grep( /addr/, @line_words );
		my ( $remote_mask ) = grep( /Mask/, @line_words );
		
		# remove attached tags
		my ( undef, $remote_ip ) = split( 'addr:', $remote_ip );
		my ( undef, $remote_mask ) = split( 'Mask:', $remote_mask );
		
		#~ print "remote_ip:$remote_ip\n";
		#~ print "remote_mask:$remote_mask\n";

		my $remote_addr = new NetAddr::IP ( $remote_ip, $remote_mask );
		#~ print "remote_network:$remote_addr->network()\n";

		if ( $local_addr->network() ne $remote_addr->network() )
		{
			#~ print "$if_name network did not match.";
			push @unmatched_ifaces, $if_name;
		}
	}

	return @unmatched_ifaces;
}

# rsync function
sub zsync
{
#	input format example:
#
#	$args = {
#		exclude => [ '/dir/foo',      '/dir/*.cgi',  ... ],	# optional
#		include => [ '/dir/foo/test', '/dir/A*.cgi', ... ],	# optional
#		ip_addr => '10.0.0.20',
#		path    => '/dir/',
#	};
	
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

sub runSync
{
	my $src_path = shift;

	#~ &zenlog("starting runSync");

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

	# run in parallel
	my $r_list = &runParallel( \&zsync, \@args );

	#~ my $return_code = 0;
	for my $rc ( @{ $r_list } )
	{
		#~ my $tid = $rc->{tid}->tid();
		&zenlog("Return[$rc->{tid}] $rc->{ret_val}");
		
		if ( $rc->{ret_val} )
		{
			&zenlog( "An error happened syncing with $rc->{arg}->{ip_addr}");
			#~ $return_code++;
		}
	}
}

sub getZClusterNodeStatus
{
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

sub setZClusterNodeStatus
{
	my $node_status = shift;

	if ( $node_status !~ /^(master|backup)$/ )
	{
		&zenlog("\"$node_status\" is not an accepted node status");
		return 1;
	}
	
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

sub disableInterfaceDiscovery
{
	my $iface = shift;

	if ( $iface->{ ip_v } == 4 )
	{
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

sub enableInterfaceDiscovery
{
	my $iface = shift;

	if ( $iface->{ ip_v } == 4 )
	{
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

sub enableAllInterfacesDiscovery
{
	# IPv4
	my $rc = &logAndRun( "$arptables -F" );

	# IPv6
	&zenlog("WARNING: enableInterfaceDiscovery pending for IPv6");

	return $rc;
}

sub broadcastInterfaceDiscovery
{
	my $iface = shift;

	&zenlog("Sending GArping for $iface->{ name }: $iface->{ addr }");

	if ( $iface->{ ip_v } == 4 )
	{
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

		# start remote interfaces, farms and cluster
		my $cl_output = &runRemotely(
			"$zcluster_manager $object $command @arguments",
			$zcl_conf->{$remote_hostname}->{ip}
		);

		&zenlog( "rc:$? $cl_output" );

		return $?;
	}

	return 0;
}

sub getZCusterStatusInfo
{
	my $status;

	# check zcluster configuration
	if ( ! -f &getGlobalConfiguration('filecluster') )
	{
		$status->{ cl_conf } = 'ko';
		return $status;
	}
	
	my $zcl_conf = &getZClusterConfig();
	my $localhost = &getHostname();
	my $remotehost = &getZClusterRemoteHost();

	$status->{ localhost } = $localhost;
	$status->{ remotehost } = $remotehost;

	### Localhost ###

	# check local keepalived
	if ( &getZClusterRunning() )
	{
		$status->{ $localhost }->{ keepalived } = 'ok';
	}
	else
	{
		$status->{ $localhost }->{ keepalived } = 'ko';
	}

	# check local node role
	if ( $status->{ $localhost }->{ keepalived } eq 'ok' )
	{
		$status->{ $localhost }->{ node_role } = &getZClusterNodeStatus();
	}

	# check local zeninotify
	if ( $status->{ $localhost }->{ keepalived } eq 'ok' )
	{
		my $zenino_procs_found = `pgrep zeninotify | wc -l`;
		chomp $zenino_procs_found;

		if ( $status->{ $localhost }->{ node_role } eq 'master' && $zenino_procs_found == 1 )
		{
			$status->{ $localhost }->{ zeninotify } = 'ok';
		}
		elsif ( $status->{ $localhost }->{ node_role } eq 'backup' && $zenino_procs_found == 0 )
		{
			$status->{ $localhost }->{ zeninotify } = 'ok';
		}
		else
		{
			$status->{ $localhost }->{ zeninotify } = 'ko';
		}
	}
	else
	{
		$status->{ $localhost }->{ zeninotify } = 'ko';
	}
	
	# check local conntrackd
	if ( &getConntrackdRunning() )
	{
		$status->{ $localhost }->{ conntrackd } = 'ok';
	}
	else
	{
		$status->{ $localhost }->{ conntrackd } = 'ko';
	}

	# check local arp/neighbour
	my @arptables_lines = `arptables -L INPUT`;

	for my $if_ref ( &getInterfaceList() )
	{
		next if $if_ref->{ vini } eq ''; # only virtual ips

		if ( $status->{ $localhost }->{ node_role } ne 'master' && @arptables_lines !~ /^-j DROP -d $if_ref->{ addr } $/ )
		{
			$status->{ $localhost }->{ arp } = 'ko';
			last;
		}
		elsif ( $status->{ $localhost }->{ node_role } eq 'master' && @arptables_lines =~ /^-j DROP -d $if_ref->{ addr } $/ )
		{
			$status->{ $localhost }->{ arp } = 'ko';
			last;
		}
	}

	if ( $status->{ $localhost }->{ arp } ne 'ko' )
	{
		$status->{ $localhost }->{ arp } = 'ok';
	}

	# check local floating ips
	# FIXME

	### Remotehost ###

	# check remote keepalived
	if ( &runRemotely( "$zcluster_manager getZClusterRunning", $zcl_conf->{$remotehost}->{ip} ) == 1 )
	{
		$status->{ $remotehost }->{ keepalived } = 'ok';
	}
	else
	{
		$status->{ $remotehost }->{ keepalived } = 'ko';
	}

	# check remote node role
	if ( $status->{ $remotehost }->{ keepalived } eq 'ok' )
	{
		$status->{ $remotehost }->{ node_role } = &runRemotely( "$zcluster_manager getZClusterNodeStatus", $zcl_conf->{$remotehost}->{ip} );
		chomp $status->{ $remotehost }->{ node_role };
	}

	# check remote zeninotify
	if ( $status->{ $remotehost }->{ keepalived } eq 'ok' )
	{
		my $zenino_procs_found = &runRemotely( "pgrep zeninotify | wc -l", $zcl_conf->{$remotehost}->{ip} );
		chomp $zenino_procs_found;

		if ( $status->{ $remotehost }->{ node_role } eq 'master' && $zenino_procs_found == 1 )
		{
			$status->{ $remotehost }->{ zeninotify } = 'ok';
		}
		elsif ( $status->{ $remotehost }->{ node_role } eq 'backup' && $zenino_procs_found == 0 )
		{
			$status->{ $remotehost }->{ zeninotify } = 'ok';
		}
		else
		{
			$status->{ $remotehost }->{ zeninotify } = 'ko';
		}
	}
	else
	{
		$status->{ $remotehost }->{ zeninotify } = 'ko';
	}
	
	# check remote conntrackd
	if ( &runRemotely( "$zcluster_manager getConntrackdRunning", $zcl_conf->{$remotehost}->{ip} ) == 1 )
	{
		$status->{ $remotehost }->{ conntrackd } = 'ok';
	}
	else
	{
		$status->{ $remotehost }->{ conntrackd } = 'ko';
	}

	# check remote arp/neighbour
	$status->{ $remotehost }->{ arp } = &runRemotely( "$zcluster_manager getZClusterArpStatus", $zcl_conf->{$remotehost}->{ip} );
	chomp $status->{ $remotehost }->{ arp };

	# check remote floating ips
	# FIXME

	return $status;
}

1;
