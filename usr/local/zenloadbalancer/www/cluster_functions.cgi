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

use Net::SSH qw(ssh sshopen2);
use Net::SSH::Expect;

#get real ip from cluster on this host
sub getClusterRealIp
{
	open FR, "<$filecluster";
	my $lmembers = <FR>;
	close FR;

	my @lmembers = split ( ":", $lmembers );
	chomp ( @lmembers );

	my $lhost = $lmembers[1];
	my $lip   = $lmembers[2];
	my $rhost = $lmembers[3];
	my $rip   = $lmembers[4];

	use Sys::Hostname;
	return ( hostname() eq $lhost )
	  ? $lip
	  : $rip;
}

# deprecating clrip function name in favor of getClusterRealIp
#~ sub clrip
#~ {
#~ return &getClusterRemoteIp();
#~ }

# set cluster status as Up on cluster configuration file
sub setClusterStatusUp
{
	use Tie::File;

	tie @contents, 'Tie::File', "$filecluster";

	for ( @contents )
	{
		if ( $_ =~ /^TYPECLUSTER/ )
		{
			@clline = split ( ":", $_ );
			$_ = "$clline[0]:$clline[1]:UP";
		}
	}

	untie @contents;
}

# deprecating clstatusUP function name in favor of setClusterStatusUp
#~ sub clstatusUP
#~ {
#~ return &();
#~ }

#get cluster virtual ip
sub getClusterVirtualIp
{
	open FR, "<$filecluster";
	@clfile = <FR>;
	close FR;

	$lcluster = $clfile[1];
	chomp ( $lcluster );
	@lcluster = split ( ":", $lcluster );
	return $lcluster[1];
}

# deprecating clvip function name in favor of getClusterVirtualIp
#~ sub clvip
#~ {
#~ return &getClusterVirtualIp();
#~ }

#is zeninotify running?
sub isClusterLocalNodeActive
{
	# returns boolean
	return `$pidof -x zeninotify.pl` != 0;
}

#get cluster's members from config file
sub getClusterConfigMembers
{
	use Sys::Hostname;

	my $members_line = -1;
	my $cl_lhost;    # cluster local host
	my $cl_lip;      # cluster local ip
	my $cl_rhost;    # cluster remote host
	my $cl_rip;      # cluster remote ip

	# get MEMBERS line from cluster configuration file
	# Example:
	# MEMBERS:hostname1:ip1:hostname2:ip2
	open FR, "$filecluster";
	foreach ( <FR> )
	{
		if ( $_ =~ /^MEMBERS/ )
		{
			chomp ( $members_line = $_ );
			last;
		}
	}
	close FR;

	#split members line
	( $cl_lhost, $cl_lip, $cl_rhost, $cl_rip ) =
	  ( split ( ":", $members_line ) )[1 .. 4];

	if ( $cl_rhost eq hostname() )
	{
		( $cl_rhost, $cl_rip, $cl_lhost, $cl_lip ) =
		  ( $cl_lhost, $cl_lip, $cl_rhost, $cl_rip );
	}

	return ( $cl_lhost, $cl_lip, $cl_rhost, $cl_rip );
}

#get data of cluster's Virtual IP
sub getClusterConfigVipInterface
{
	my $cluster_ip_line;

	# get IPCLUSTER line from cluster configuration file
	# Example:
	# IPCLUSTER:10.0.0.10:eth0:0
	open FR, "$filecluster";
	foreach ( <FR> )
	{
		if ( $_ =~ /^IPCLUSTER/ )
		{
			chomp ( $cluster_ip_line = $_ );
			last;
		}
	}
	close FR;

	# split ip and device info
	my @cl_VIPdata = split ( ":", $cluster_ip_line );

	# ( ip, virtual interface)
	return ( $cl_VIPdata[1], $cl_VIPdata[2] . ":" . $cl_VIPdata[3] );
}

#get cluster type and cluster status
sub getClusterConfigTypeStatus
{
	my $line;

	# pick line TYPECLUSTER from cluster configuration line
	# Examples:
	# TYPECLUSTER:hostname1-hostname2:UP
	# TYPECLUSTER:equal:UP
	open FR, "$filecluster";
	foreach ( <FR> )
	{
		if ( $_ =~ /^TYPECLUSTER/ )
		{
			chomp ( $line = $_ );
			last;
		}
	}
	close FR;

	return ( split ( ":", $line ) )[1 .. 2];
}

#get cluster cable link
sub getClusterConfigCableLink
{
	my $output = -1;
	my $line   = -1;

	# get CABLE line from cluster config file
	open FR, "$filecluster";
	foreach ( <FR> )
	{
		if ( $_ =~ /^CABLE/ )
		{
			chomp ( $line = $_ );
			last;
		}
	}
	close FR;

	return ( split ( ":", $line ) )[1];
}

# get cluster ID. In use???
sub getClusterConfigId
{
	my $line;

	open FR, "$filecluster";

	foreach ( <FR> )
	{
		if ( $_ =~ /^IDCLUSTER/ )
		{
			chomp ( $line = $_ );
			last;
		}
	}
	close FR;

	return ( split ( ":", $line ) )[1];
}

#get cluster DEADRATIO
sub getClusterConfigDeadratio
{
	my $line;

	open FR, "$filecluster";
	foreach ( <FR> )
	{
		if ( $_ =~ /^DEADRATIO/ )
		{
			chomp ( $line = $_ );
			last;
		}
	}
	close FR;

	return ( split ( ":", $line ) )[1];
}

# force local node failover. Test failover
sub testClusterLocalNodeFailover
{
	my $piducarp = `pidof ucarp`;
	return system ( "kill -SIGUSR2 $piducarp" );
}

# deprecating setLocalNodeForceFail function name in favor of testClusterLocalNodeFailover
#~ sub setLocalNodeForceFail
#~ {
#~ return &testClusterLocalNodeFailover();
#~ }

sub isUcarpRunningLocally
{
	return `$pidof -x ucarp`;
}

sub isUcarpRunningOn
{
	my ( $rip ) = @_;
	return
	  `ssh -o \"ConnectTimeout=10\" -o \"StrictHostKeyChecking=no\" root\@$rip \"pidof -x ucarp \" 2>&1`;
}

# save cluser configuration
sub setClusterConfig
{
	my (
		 $local_host,  $local_ip,          $remote_host,  $remote_ip,
		 $cluster_vip, $cluster_vip_iface, $cluster_type, $cluster_status,
		 $cable,       $cluster_id,        $deadratio
	) = @_;

	#create new configuration cluster file
	open FO, "> $filecluster";
	print FO "MEMBERS\:$local_host\:$local_ip\:$remote_host\:$remote_ip\n";
	print FO "IPCLUSTER\:$cluster_vip\:$cluster_vip_iface\n";
	print FO "TYPECLUSTER\:$cluster_type\:$cluster_status\n";
	print FO "CABLE\:$cable\n";
	print FO "IDCLUSTER\:$cluster_id\n";
	print FO "DEADRATIO\:$deadratio\n";
	close FO;
}

# might be used in a non cluster
sub getInterfaceConfiguration
{
	my ( $iface_configfile ) = @_;

	my @data;

	open IFACE_FILE, "$configdir\/$iface_configfile";

	# actually, only one line
	while ( <IFACE_FILE> )
	{
		chomp ( @data = split ( ":", $_ ) );
		last;
	}
	close IFACE_FILE;

	return @data;
}

sub getClusterLocalIPandInterface
{
	my ( $vipcl ) = @_;

	# take the physical part of the virtual interface
	my ( $iface ) = split ':', &getInterfaceOfIp( $vipcl );
	my $lip = &iponif( $iface );

	# if vipcl is not locally available, node in slave mode
	if ( !defined ( $iface ) )
	{
		$lip   = ( &getClusterConfigMembers() )[1];
		$iface = &getInterfaceOfIp( $lip );
	}

	return ( $iface, $lip );
}

sub showCluserStatus
{
	my ( $rhost, $lhost, $rip, $lip, $vipcl, $clstatus ) = @_;

	if ( &areClusterNodesDefined() && $clstatus )
	{
		print "<br>";
		&showZenLatencyStatus();
		print "<br>";
		getClusterActiveNode();
		print "<br>";
		&showZenInotifyStatus();
	}
	else
	{
		print "Cluster not configured!";
	}

	return ( $rhost, $lhost, $rip, $lip, $vipcl, $clstatus );
}

sub showZenLatencyStatus
{
	my ( $lhost, $lip, $rhost, $rip ) = getClusterConfigMembers();

	#zenlatency is running on local:
	my $local_ucarp = &isUcarpRunningLocally();

	print "Zen latency on <b>$lhost</b> is ";
	print $local_ucarp
	  ? "<b>UP</b>\n"
	  : "<b>DOWN</b>\n";

	print ' | ';

	#zenlatency is running on remote?:
	my $remote_ucarp = &isUcarpRunningOn( $rip );

	print "Zen latency on <b>$rhost</b> is ";
	print $remote_ucarp
	  ? "<b>UP</b>\n"
	  : "<b>DOWN</b>\n";

	print $local_ucarp && $remote_ucarp
	  ? " <img src=\"/img/icons/small/accept.png\">"
	  : " <img src=\"/img/icons/small/exclamation.png\">";
}

sub getClusterActiveNode
{
	my $active_node = 'false';

	my ( $lhost, undef, $rhost, $rip, $vipcl ) = ( &getClusterConfig() )[0 .. 4];

#( $lhost, $lip, $rhost, $rip, $vipcl, $ifname, $typecl, $clstatus, $cable, $idcluster, $deadratio )

	#~ my @vipwhereis = `$ip_bin addr list`;
	my @vipwhereis2 =
	  `ssh -o \"ConnectTimeout=10\" -o \"StrictHostKeyChecking=no\" root\@$rip \"$ip_bin addr list\" 2>&1`;

	print "Cluster VIP <b>$vipcl</b> is active on ";

	# look for cluster vip in current ip addresses
	#~ if ( grep ( /$vipcl/, @vipwhereis ) )
	if ( grep ( /$vipcl/, `$ip_bin addr list` ) )
	{
		print "<b>$lhost</b> ";
		$active_node = $lhost;
	}

	if ( grep ( /$vipcl/, @vipwhereis2 ) )
	{
		print ' and ' if $active_node ne 'false';
		print "<b>$rhost</b>";
		$active_node .= $rhost;
	}

	print $active_node eq 'false'
	  ? " <img src=\"/img/icons/small/exclamation.png\">"
	  : " <img src=\"/img/icons/small/accept.png\">";

	return $active_node;
}

sub showZenInotifyStatus
{
	my ( $lhost, undef, $rhost, $rip ) = getClusterConfigMembers();
	my $activeino = 'false';

	my $local_zeninotify_pid = `$pidof -x zeninotify.pl`;
	my $remote_zeninotify_pid =
	  `ssh -o \"ConnectTimeout=10\" -o \"StrictHostKeyChecking=no\" root\@$rip "pidof -x zeninotify.pl" 2>&1`;

	print "Synchronization by Zen Inotify is ";

	if ( $local_zeninotify_pid && !$remote_zeninotify_pid )
	{
		print "running on <b>$lhost</b>\n";
		print " <img src=\"/img/icons/small/accept.png\">";
	}
	elsif ( $remote_zeninotify_pid && !$local_zeninotify_pid )
	{
		print "running on <b>$rhost</b>\n";
		print " <img src=\"/img/icons/small/accept.png\">";
	}
	else
	{
		if ( $local_zeninotify_pid && $remote_zeninotify_pid )
		{
			print "running on <b>$lhost</b> and <b>$rhost</b>";
		}
		else
		{
			print "not running on this cluster. ";
		}
		print " <img src=\"/img/icons/small/exclamation.png\">";
	}
}

sub isClusterNodeInMaintenanceMode
{
	return `ps aux | grep "ucarp" | grep "\\-k 100" | grep -v grep`;
}

# returns cluster configuration values from configuration file
sub getClusterConfig
{
	### 1. Get local and remote hostname and ip from configfile ###
	my ( $lhost, $lip, $rhost, $rip ) = &getClusterConfigMembers();

	### 2. Get cluster's VIP data ###
	my ( $vipcl, $ifname ) = &getClusterConfigVipInterface();

	### 3. Get cluster's type and status ###
	my ( $typecl, $clstatus ) = &getClusterConfigTypeStatus();

	# if $clstatus is empty: defaulting to -1
	#~ $clstatus = $clstatus // 'DOWN';

	### 4. Get cluster's cable link data ###
	# if function's return is empty: defaulting to -1
	my $cable = &getClusterConfigCableLink() // -1;

	### 5. Get cluster's ID ###
	# if function's return is empty: defaulting to 1
	my $idcluster = &getClusterConfigId() // 1;

	### 6. Get cluster's Deadratio ###
	# if function's return is empty: defaulting to 10
	my $deadratio = &getClusterConfigDeadratio() // 10;

	return (
			 $lhost,  $lip,      $rhost, $rip,       $vipcl, $ifname,
			 $typecl, $clstatus, $cable, $idcluster, $deadratio
	);
}

# Force sync cluster from master to backup
sub setClusterSyncForced
{
	open FT, ">$configdir/sync_cl";
	close FT;
	sleep ( 2 );
	unlink ( "$configdir/sync_cl" );
}

sub setClusterNodeOnMaintenance
{
	my ( $cable, $ifname, $deadratio, $lip, $idcluster, $vipcl ) = @_;

	my $return_code;

	#~ $ignoreifstate = ( $cable eq "Crossover cord" ) ? "--ignoreifstate"
	#~ : "";

	if ( $cable eq "Crossover cord" )
	{
		$ignoreifstate = "--ignoreifstate";
	}
	else
	{
		$ignoreifstate = "";
	}

	@rifname = split ( ":", $ifname );

	&successmsg(
		"Demoting the node to backup for maintenance, please wait and don't stop the process"
	);

	@eject = system ( "pkill -9 ucarp" );
	sleep ( 5 );

	my $ucarp_command =
	    "$ucarp "
	  . "$ignoreifstate "
	  . "-r $deadratio "
	  . "--interface=$rifname[0] "
	  . "--srcip=$lip "
	  . "--vhid=$idcluster "
	  . "--pass=secret "
	  . "--addr=$vipcl "
	  . "-k 100 "
	  . "--upscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-start.pl "
	  . "--downscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-stop.pl "
	  . "-B "
	  . "-f local6";
	&logfile( $ucarp_command );
	system ( $ucarp_command );
	$return_code = $?;

	sleep ( 10 );

	return $return_code;
}

sub setClusterNodeOffMaintenance
{
	my ( $cable, $ifname, $deadratio, $lip, $idcluster, $vipcl, $typecl ) = @_;

	my $return_code;
	my ( $rifname ) = split ( ":", $ifname );
	my $ignoreifstate =
	  ( $cable eq "Crossover cord" )
	  ? "--ignoreifstate"
	  : "";

	system ( "pkill -9 ucarp" ) and sleep ( 5 );

	if ( $typecl =~ /^equal$/ )
	{
		my $ucarp_command =
		    "$ucarp "
		  . "$ignoreifstate "
		  . "-r $deadratio "
		  . "--interface=$rifname "
		  . "--srcip=$lip "
		  . "--vhid=$idcluster "
		  . "--pass=secret "
		  . "--addr=$vipcl "
		  . "--upscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-start.pl "
		  . "--downscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-stop.pl "
		  . "-B "
		  . "-f local6";
		&logfile( $ucarp_command );
		system ( $ucarp_command );
		$return_code = $?;
	}
	elsif ( $typecl =~ /$lhost-$rhost/ )
	{
		my $ucarp_command =
		    "$ucarp "
		  . "$ignoreifstate "
		  . "-r $deadratio "
		  . "--interface=$rifname "
		  . "--srcip=$lip " . "-P "
		  . "--vhid=$idcluster "
		  . "--pass=secret "
		  . "--addr=$vipcl "
		  . "--upscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-start.pl "
		  . "--downscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-stop.pl "
		  . "-B "
		  . "-f local6";
		&logfile( $ucarp_command );
		system ( $ucarp_command );
		$return_code = $?;
	}
	else    # M-B Backup node
	{
		my $ucarp_command =
		    "$ucarp "
		  . "$ignoreifstate "
		  . "-r $deadratio "
		  . "--interface=$rifname "
		  . "-k 50 "
		  . "--srcip=$lip "
		  . "--vhid=$idcluster "
		  . "--pass=secret "
		  . "--addr=$vipcl "
		  . "--upscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-start.pl "
		  . "--downscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-stop.pl "
		  . "-B "
		  . "-f local6";
		&logfile( $ucarp_command );
		system ( $ucarp_command );
		$return_code = $?;
	}

	return $return_code;
}

sub setClusterRsaConnection
{
	my ( $lhost, $rhost, $lip, $rip, $pass, $vipcl, $cable ) = @_;

	my $error = "false";

	# 1) create ssh object, introducing credentials
	my $ssh = Net::SSH::Expect->new(
									 host                         => "$rip",
									 user                         => 'root',
									 password                     => "$pass",
									 raw_pty                      => 1,
									 restart_timeout_upon_receive => 1
	);

	eval {
		# 2) logon to the SSH server using those credentials.
		# test the login output to make sure we had success
		$ssh->run_ssh() or die "SSH process couldn't start: $!";

		# test connection
		#$ssh->peek( 5 );

		if ( $ssh->peek( 5 ) =~ /yes/ )
		{
			$ssh->read_all();
			$ssh->send( "yes" );
		}

		my $sshpasswrong = "false";

		# look for 'password' string
		my $sshstat = $ssh->waitfor( 'password', 10 );

		# if password was found
		if ( $sshstat eq 1 )
		{
			$ssh->read_all();
			$ssh->send( $pass );

			# look for 'password' string
			$sshstat = $ssh->waitfor( 'password', 10 );

			if ( $sshstat eq 1 )
			{
				$ssh->read_all();
				$sshpasswrong = "true";
			}
			else
			{
				$ssh->read_all();
			}
		}

		# 'password' was never found
		else
		{
			$ssh->read_all();

			#There was an old RSA communication, we have to delete it
			$ssh->exec( "rm -f /root/.ssh/authorized_keys" );
		}

		# if password was found
		if ( $sshstat eq 1 )
		{
			if ( $sshpasswrong eq "true" )
			{
				&errormsg(
						  "Login on $rhost ($rip) has failed, wrong password could be a cause..." );
			}
			else
			{
				&errormsg(
					"Login on $rhost ($rip) has failed, timeout on ssh connection could be a cause..."
				);
			}
			$error = "true";
		}
		else
		{
			#Check if can exec commands through ssh
			my $checkcommand = "date > null";
			$ssh->send( $checkcommand );    # using send() instead of exec()

			my $line;
			my $ind = 0;
			my @sshoutput;
			while ( defined ( $line = $ssh->read_line() ) )
			{
				@sshoutput[$ind] = $line;
				$ind++;
			}

			#The first line is the command echoed
			#The second line is stderr output
			$ssh->read_all();    # The prompt is in the input stream, skip it

			# if there was output after the test command is an error message,
			# so there is a problem to be catched
			if ( defined $sshoutput[1] )
			{
				$sshoutput[1] =~ s/^\s+//;
				$sshoutput[1] =~ s/\s+$//;

				if ( $sshoutput[1] !~ /^$/ )
				{
					&errormsg( "Login on $rhost ($rip) ok, but can not execute commands" );
					$error = "true";
				}
			}
		}
	};

	# check eval error ($@) and error string values
	if ( $@ =~ /^$/ && $error eq "false" )

	  #~ if ( $error eq "false" )
	{
		&successmsg( "Running process for configure RSA comunication" );

		&logfile( "Deleting old RSA key on $lhost ($lip)" );
		unlink glob ( "/root/.ssh/id_rsa*" );

		&logfile( "Creating new RSA keys on $lhost ($lip)" );

		# includes -q for quiet
		system ( qq{$sshkeygen -q -t rsa -f /root/.ssh/id_rsa -N ""} );

		open FR, "/root/.ssh/id_rsa.pub"
		  or warn "$0: open /root/.ssh/id_rsa.pub: $!";
		chomp ( $rsa_pass = <FR> );
		close FR;

		# - now you know you're logged in - #
		# run command
		&logfile( "Copying new RSA key from $lhost ($lip) to $rhost ($rip)" );
		my $eject = $ssh->exec(
			"rm -f /root/.ssh/authorized_keys; mkdir -p /root/.ssh/; echo $rsa_pass \>\> /root/.ssh/authorized_keys"
		);

		$ssh->read_all();    #Clean the ssh buffer

		my $rhostname = $ssh->exec( "hostname" );
		$rhostname = ( split ( "\ ", $rhostname ) )[1];
		chomp ( $rhostname );

		@ifcl = split ( ":", $ifname );
		$ifcl = $ifcl[0];

		my $ripeth0 = $ssh->exec( "ip addr show $ifcl | grep $ifcl\$" );

		my @ripeth0 = split ( "\ ", $ripeth0 );
		@ripeth0 = split ( "\/", $ripeth0[8] );
		$ripeth0 = $ripeth0[0];
		chomp ( $ripeth0 );

		my $modified = "false";

		if ( $rhostname ne $rhost )
		{
			$rhost = $rhostname;
			&errormsg( "Remote hostname is not OK, modified to $rhostname" );
			$modified = "true";
		}

		if ( $ripeth0 ne $rip )
		{
			$rip = $ripeth0;
			&errormsg( "Remote ip on eth0 is not OK, modified to $ripeth0" );
			$modified = "true";
		}

		if ( $modified eq "true" )
		{
			open $fo, ">", "$filecluster";
			print $fo "MEMBERS\:$lhost\:$lip\:$rhost\:$rip\n";
			print $fo "IPCLUSTER\:$vipcl\:$ifname\n";
			print $fo "CABLE\:$cable\n";
			close $fo;
		}

		#connect to remote host without password
		my $userNhost = qq{root\@$rip};

		#deleting remote id_rsa key
		&logfile( "Deleting old RSA key on $rhost" );
		ssh( $userNhost, "rm -rf /root/.ssh/id_rsa*" );

		#creating new remote id_rsa key
		&logfile( "Creating new remote RSA key on $rhost" );
		ssh( $userNhost,
			 "$sshkeygen -t rsa -f /root/.ssh/id_rsa -N \"\" &> /dev/null" );

		#copying id_rsa remote key to local
		&logfile( "Copying new RSA key from $rhost to $lhost" );
		@eject = `$scp $userNhost:/root/.ssh/id_rsa.pub /tmp/`;

		#open file
		use File::Copy;
		move( "/tmp/id_rsa.pub", "/root/.ssh/authorized_keys" );

		#open file and copy to other
		&logfile( "Enabled RSA communication between cluster hosts" );
		&successmsg( "Enabled RSA communication between cluster hosts" );

		#run zeninotify for syncronization directories
	}
	else
	{
		&errormsg( "RSA communication with $rhost ($rip) has failed..." );
	}

	$ssh->close();
}

# setup rsa connections with remote host
sub testClusterRsaConnectionsWithIp
{
	my ( $rip ) = @_;

	system (
		"$ssh -o \"ConnectTimeout=10\" -o \"StrictHostKeyChecking=no\" root\@$rip \'$pen_bin\' >/dev/null 2>&1"
	);

	return $?;
}

#  set a cluster type
sub setClusterType
{
	my ( $typecl, $lip, $rip, $ifname, $cable, $deadratio, $idcluster, $vipcl ) =
	  @_;

	my $ignoreifstate =
	  ( $cable eq "Crossover cord" )
	  ? "--ignoreifstate"
	  : "";

	# taking only the physical interface, ignoring the virtual part of the device
	( $ifname ) = split ( ":", $ifname );

	# test if ssh connection to cluster remote host is already configured
	system (
		qq{$ssh -o "ConnectTimeout=10" -o "StrictHostKeyChecking=no" root\@$rip '$pen_bin' >/dev/null 2>&1}
	);

	# if ssh and cluster already configured
	if ( $? == 0 )
	{
		# create ssh object with credentials
		my $ssh = Net::SSH::Expect->new(
										 host    => $rip,
										 user    => 'root',
										 raw_pty => 1
		);

		# open ssh connection
		$ssh->run_ssh() or die "SSH process couldn't start: $!";

		# stop remote and local execution of ucarp
		$ssh->exec( "pkill -9 ucarp" );
		system ( "pkill -9 ucarp" );

		# set cluster status as UP on the configuration file
		&setClusterStatusUp();

		# send configuration file to remote cluster host
		&logfile( "Sending $filecluster to $rip" );
		system ( qq{$scp $filecluster root\@$rip:$filecluster} );

		if ( $typecl =~ /^equal$/ )
		{
			&successmsg(
				"Running Zen latency Service and Zen inotify Service, please wait and not stop the process"
			);

			# run local and remute ucarp processes
			&setClusterTypeEqual( $deadratio, $ignoreifstate, $ifname, $lip, $rip,
								  $idcluster, $vipcl, $ssh );

			# show gui messages
			&successmsg( "Cluster configured on mode $lhost or $rhost can be masters" );
			&successmsg(
				"Reload here <a href=\"index.cgi?id=$id\"><img src=\"img/icons/small/arrow_refresh.png\"></a> to apply changes"
			);
		}
		elsif ( $typecl =~ /$lhost-$rhost/ )
		{
			&successmsg(
						 "Running Zen latency Service and Zen inotify Service, please wait" );

			# run local and remute ucarp processes
			&setClusterTypePreferedMaster( $deadratio, $ignoreifstate, $ifname, $lip, $rip,
										   $idcluster, $vipcl, $ssh );

			# show gui messages
			&successmsg(
				 "Cluster configured on mode $lhost master and $rhost backup automatic failover"
			);
			&successmsg(
				"Reload here <a href=\"index.cgi?id=$id\"><img src=\"img/icons/small/arrow_refresh.png\"></a> to apply changes"
			);
		}
		elsif ( $typecl =~ /Disabled/ )
		{
			&successmsg(
						 "Disabling Zen latency Service and Zen inotify Service, please wait" );

			# disable services and remove cluster configuration
			&setClusterDisabledAndRemoved( $ssh );

			&successmsg( "Cluster disabled on $lhost and $rhost" );
		}

		# close ssh connection to cluster remote host
		$ssh->close();
	}

	# if ssh and cluster configuration was not successfull
	else
	{
		# cluser in configuration process is disabled/removed
		if ( $typecl =~ /Disabled/ )
		{
			&successmsg(
						 "Disabling Zen latency Service and Zen inotify Service, please wait" );

			# create ssh object
			my $ssh = Net::SSH::Expect->new(
											 host    => "$rip",
											 user    => 'root',
											 raw_pty => 1
			);

			# open ssh connection
			$ssh->run_ssh() or die "SSH process couldn't start: $!";

			# disable zen inotify and remove cluster configuration
			&setClusterDisabledAndRemoved( $ssh );

			# close ssh connection
			$ssh->close();

			&successmsg( "Cluster disabled on $lhost and $rhost" );
		}
		else
		{
			&errormsg(
				"Error connecting between $lip and $rip, please configure the RSA connectiong first"
			);

	  # leave cluster type without configuration because rsa configuration is required first
	  # to keep a correct cluster configuration
			undef ( $typecl );
		}
	}

	return ( $typecl, $lip, $rip, $ifname, $cable, $deadratio, $idcluster, $vipcl );
}

# set cluster type as equal preference for master node
sub setClusterTypeEqual
{
	my ( $deadratio, $ignoreifstate, $ifname, $lip, $rip, $idcluster, $vipcl, $ssh )
	  = @_;

	# run ucarp locally
	my $ucarp_local_command =
	    "$ucarp "
	  . "-r $deadratio "
	  . "$ignoreifstate "
	  . "--interface=$ifname "
	  . "--srcip=$lip "
	  . "--vhid=$idcluster "
	  . "--pass=secret "
	  . "--addr=$vipcl "
	  . "--upscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-start.pl "
	  . "--downscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-stop.pl "
	  . "-B "
	  . "-f local6";

	&logfile( "running on local: $ucarp_local_command" );
	system ( $ucarp_local_command );
	sleep ( 10 );

	# run ucarp remotely
	my $ucarp_remote_command =
	    "$ucarp "
	  . "-r $deadratio "
	  . "$ignoreifstate "
	  . "--interface=$ifname "
	  . "--srcip=$rip "
	  . "--vhid=$idcluster "
	  . "--pass=secret "
	  . "--addr=$vipcl "
	  . "--upscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-start.pl "
	  . "--downscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-stop.pl "
	  . "-B "
	  . "-f local6";

	&logfile( "running on remote: $ucarp_remote_command" );
	$ssh->exec( $ucarp_remote_command );
	sleep ( 10 );

	return;
}

# set cluster type as prefered localhost for master node
sub setClusterTypePreferedMaster
{
	my ( $deadratio, $ignoreifstate, $ifname, $lip, $rip, $idcluster, $vipcl, $ssh )
	  = @_;

	# run ucarp locally
	my $ucarp_local_command =
	    "$ucarp "
	  . "-r $deadratio "
	  . "$ignoreifstate "
	  . "--interface=$ifname "
	  . "--srcip=$lip " . "-P "
	  . "--vhid=$idcluster "
	  . "--pass=secret "
	  . "--addr=$vipcl "
	  . "--upscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-start.pl "
	  . "--downscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-stop.pl "
	  . "-B "
	  . "-f local6";

	&logfile( "running on local: $ucarp_local_command" );
	system ( $ucarp_local_command );
	sleep ( 5 );

	# run ucarp remotely
	my $ucarp_remote_command =
	    "$ucarp "
	  . "-r $deadratio "
	  . "$ignoreifstate "
	  . "--interface=$ifname "
	  . "-k 50 "
	  . "--srcip=$rip "
	  . "--vhid=$idcluster "
	  . "--pass=secret "
	  . "--addr=$vipcl "
	  . "--upscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-start.pl "
	  . "--downscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-stop.pl "
	  . "-B "
	  . "-f local6";

	&logfile( "running on remote: $ucarp_remote_command" );
	$ssh->exec( $ucarp_remote_command );
	sleep ( 10 );

	return;
}

#
sub setClusterDisabledAndRemoved
{
	my ( $ssh ) = @_;

	# stop cluster zen ninotify
	$ssh->exec( 'pkill -9f zeninotify.pl' );
	system ( 'pkill -9f zeninotify.pl' );

	# stop cluster ucarp
	# ucarp is not running if the cluster is not fully configured
	$ssh->exec( 'pkill -9 ucarp' );
	system ( 'pkill -9 ucarp' );

	# remove cluster configuration file
	$ssh->exec( "rm $filecluster" );
	unlink ( $filecluster );

	# remove ssh RSA keys
	# the RSA key files do not exit if not configured
	$ssh->exec( 'rm -f  /root/.ssh/authorized_keys' );
	system ( 'rm -rf /root/.ssh/authorized_keys' );
}

# check if all configuration parameters are defined and not empty
sub isClusterConfigured
{
	# check if all the cluster parameters are defined
	foreach $parameter ( &getClusterConfig() )
	{
		# return a false value if a cluster variable is not defined or has no value
		return 0 if ( !defined $parameter || $parameter eq '' );
	}

	# returns a true value if no parameter is undefined
	return 1;
}

# check if both nodes are defined and no parameter is empty
sub areClusterNodesDefined
{
	# check if all the cluster nodes parameters are defined
	foreach $parameter ( &getClusterConfigMembers() )
	{
		# if any parameter is not defined return a false value
		return 0 if ( !defined $parameter || $parameter eq '' );
	}

	# if all parameters ar defined return a true value
	return 1;
}

###HTML cluster INFO ### from ee branch
sub getClusterInfo()
{
	open FR, "<$filecluster";
	@file         = <FR>;
	$cluster_msg  = "Not configured";
	$cluster_icon = "fa-cog yellow";

	if ( -e $filecluster && ( grep ( /UP/, @file ) ) )
	{
		if ( &activenode() eq "true" )
		{

			#print "Cluster: <b>this node is master</b>";
			$cluster_msg  = "Master";
			$cluster_icon = "fa-cog green";
		}
		elsif ( `ps aux | grep "ucarp" | grep "\\-k 100" | grep -v grep` )
		{

			#print "Cluster: <b>this node is on maintenance</b>";
			$cluster_msg  = "Maintenance";
			$cluster_icon = "fa-cog red";
		}
		else
		{

			#print "Cluster: <b>this node is backup</b>";
			$cluster_msg  = "Backup";
			$cluster_icon = "fa-cog green";
		}
	}

}

###HTML Cluster status icons ### from ee branch
sub getClusterStatus()
{
	if ( $cluster_msg eq "Not configured" )
	{
		print
		  "<div class=\"grid_4\"><p class=\"cluster\"><a href=\"http://www.zenloadbalancer.com/eliminate-a-single-point-of-failure/\" target=\"_blank\"><i class=\"fa fa-fw $cluster_icon action-icon\" title=\"How to eliminate this single point of failure\"></i></a> Cluster status: $cluster_msg</p></div>";
		print "<div class=\"clear\"></div>";
	}
	else
	{
		print
		  "<div class=\"grid_4\"><p class=\"cluster\"><i class=\"fa fa-fw $cluster_icon action-icon\"></i> Cluster status: $cluster_msg</p></div>";
		print "<div class=\"clear\"></div>";
	}
}

# do not remove this
1;

