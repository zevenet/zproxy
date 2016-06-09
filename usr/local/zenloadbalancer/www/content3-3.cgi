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
use Sys::Hostname;

my $host = hostname();

print "
  <!--- CONTENT AREA -->
  <div class=\"content container_12\">
";

####################################
# CLUSTER INFO
####################################
&getClusterInfo();

###################################
#BREADCRUMB
###################################
print "<div class=\"grid_6\"><h1>Settings :: Cluster</h1></div>\n";

####################################
# CLUSTER STATUS
####################################
&getClusterStatus();

if ( $action =~ /Cancel/ )
{
	unlink ( $filecluster );
	undef ( $vipcl );
}

#action save
if (    $action eq "Save"
	 || $action eq "Save VIP"
	 || $action eq "Configure cluster type" )
{
	#create new configuration cluster file
	open FO, "> $filecluster";
	print FO "MEMBERS\:$lhost\:$lip\:$rhost\:$rip\n";
	print FO "IPCLUSTER\:$vipcl:$ifname\n";
	print FO "TYPECLUSTER\:$typecl\n";
	print FO "CABLE\:$cable\n";
	print FO "IDCLUSTER\:$idcluster\n";
	print FO "DEADRATIO\:$deadratio\n";
	close FO;
}

if ( -e $filecluster )
{
	#get cluster's members data
	@clmembers = &getClusterConfigMembers( $host, $filecluster );
	$lhost = $clmembers[0];

	if ( $clmembers[1] !~ /^$/ )
	{
		$lip = $clmembers[1];
	}

	if ( $clmembers[2] !~ /^$/ )
	{
		$rhost = $clmembers[2];
	}

	if ( $clmembers[3] !~ /^$/ )
	{
		$rip = $clmembers[3];
	}

	#get cluster's VIP data
	@clvipdata = &getClusterConfigVipInterface( $filecluster );

	if ( @clvipdata ne -1 )
	{
		$vipcl  = $clvipdata[0];
		$ifname = $clvipdata[1];
	}
	elsif ( !$vipcl =~ /^$/ )
	{
		@clvipdata = split ( ":", $vipcl );

		if ( $clvipdata[1] !~ /^$/ && $clvipdata[2] !~ /^$/ )
		{
			$ifname = "$clvipdata[1]:$clvipdata[2]";
		}

		$vipcl = $clvipdata[0];
	}

	#get cluster's type and status
	@cltypestatus = &getClusterConfigTypeStatus( $filecluster );
	if ( @cltypestatus ne -1 )
	{
		$typecl   = $cltypestatus[0];
		$clstatus = $cltypestatus[1];
	}

	#get cluster's cable link data
	$cable = &getClusterConfigCableLink( $filecluster );

	#get cluster's ID
	$idcluster = &getClusterConfigId( $filecluster );

	if ( $idcluster eq -1 )
	{
		$idcluster = 1;
	}

	#get cluster's DEADRATIO
	$deadratio = &getClusterConfigDeadratio( $filecluster );

	if ( $deadratio eq -1 )
	{
		$deadratio = 2;
	}

	#action sync cluster
	if ( $action eq "Force sync cluster from master to backup" )
	{
		open FT, ">$configdir/sync_cl";
		close FT;
		sleep ( 2 );

		unlink ( "$configdir/sync_cl" );
		&successmsg( "Cluster synced manually" );
	}

	#action Test failover
	if ( $action eq "Test failover" )
	{
		&testClusterLocalNodeFailover();
	}

	if ( $action eq "Force node as backup for maintenance" )
	{
		if ( $cable eq "Crossover cord" )
		{
			$ignoreifstate = "--ignoreifstate";
		}
		else
		{
			$ignoreifstate = "";
		}

		@rifname = split ( ":", $ifname );
		@eject = system ( "pkill -9 ucarp" );
		sleep ( 5 );

		&successmsg(
			"Demoting the node to backup for maintenance, please wait and don't stop the process"
		);
		&zenlog(
			"$ucarp $ignoreifstate -r $deadratio --interface=$rifname[0] --srcip=$lip --vhid=$idcluster --pass=secret --addr=$vipcl -k 100 --upscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-start.pl --downscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-stop.pl -B -f local6"
		);
		@eject = system (
			"$ucarp $ignoreifstate -r $deadratio --interface=$rifname[0] --srcip=$lip --vhid=$idcluster --pass=secret --addr=$vipcl -k 100 --upscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-start.pl --downscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-stop.pl -B -f local6"
		);
		sleep ( 10 );
	}

	if ( $action eq "Return node from maintenance" )
	{
		if ( $cable eq "Crossover cord" )
		{
			$ignoreifstate = "--ignoreifstate";
		}
		else
		{
			$ignoreifstate = '';
		}

		@rifname = split ( ":", $ifname );
		@eject = system ( "pkill -9 ucarp" );
		sleep ( 5 );

		&successmsg(
			"Returning the node from maintenance, please wait and don't stop the process" );

		if ( $typecl =~ /^equal$/ )
		{
			&zenlog(
				"$ucarp $ignoreifstate -r $deadratio --interface=$rifname[0] --srcip=$lip --vhid=$idcluster --pass=secret --addr=$vipcl --upscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-start.pl --downscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-stop.pl -B -f local6"
			);
			my @eject = system (
				"$ucarp $ignoreifstate -r $deadratio --interface=$rifname[0] --srcip=$lip --vhid=$idcluster --pass=secret --addr=$vipcl --upscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-start.pl --downscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-stop.pl -B -f local6"
			);
		}
		elsif ( $typecl =~ /$lhost-$rhost/ )
		{
			&zenlog(
				"$ucarp $ignoreifstate -r $deadratio --interface=$rifname[0] --srcip=$lip -P --vhid=$idcluster --pass=secret --addr=$vipcl --upscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-start.pl --downscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-stop.pl -B -f local6"
			);
			my @eject = system (
				"$ucarp $ignoreifstate -r $deadratio --interface=$rifname[0] --srcip=$lip -P --vhid=$idcluster --pass=secret --addr=$vipcl --upscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-start.pl --downscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-stop.pl -B -f local6"
			);
		}
		else
		{
			&zenlog(
				"$ucarp $ignoreifstate -r $deadratio --interface=$rifname[0] -k 50 --srcip=$lip --vhid=$idcluster --pass=secret --addr=$vipcl --upscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-start.pl --downscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-stop.pl -B -f local6"
			);
			my $eject = system (
				"$ucarp $ignoreifstate -r $deadratio --interface=$rifname[0] -k 50 --srcip=$lip --vhid=$idcluster --pass=secret --addr=$vipcl --upscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-start.pl --downscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-stop.pl -B -f local6"
			);
		}
		sleep ( 10 );
	}

	#action test rsa
	if ( $action eq "Test RSA connections" && $lhost && $rhost && $lip && $rip )
	{
		chomp ( $rip );
		$user = "root";

		@eject =
		  `$ssh -o \"ConnectTimeout=10\" -o \"StrictHostKeyChecking=no\" root\@$rip \'$pen_bin\' 2>&1 `;

		if ( $? == 0 )
		{
			&successmsg( "RSA connection from $lhost ($lip) to $rhost ($rip) is OK" );
		}
		else
		{
			&errormsg( "RSA connection from $lhost ($lip) to $rhost ($rip) not works" );
		}
	}

	#action configure connection
	if (    $action eq "Configure RSA connection between nodes"
		 && $lhost !~ /^\$/
		 && $lip !~ /^$/
		 && $rhost !~ /^$/
		 && $rip !~ /^\$/
		 && $vipcl !~ /^$/ )
	{
		chomp ( $rip );
		chomp ( $pass );

		# 1) create ssh object
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
			my $eject = $ssh->peek( 5 );

			if ( $eject =~ /yes/ )
			{
				$ssh->read_all();
				$ssh->send( "yes" );
			}

			my $sshstat = $ssh->waitfor( 'password', 10 );
			my $sshpasswrong = "false";
			&successmsg( "Request for SSH connection sent to $rhost..." );

			if ( $sshstat eq 1 )
			{
				$ssh->read_all();
				$ssh->send( $pass );
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
			else
			{
				$ssh->read_all();
				&successmsg( "Deleting previous RSA synchronization with $rhost..." );

				#There were an old RSA communication, we have to delete it
				my $eject = $ssh->exec( "rm -f /root/.ssh/authorized_keys" );
			}

			$error = "false";

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
				&successmsg( "Correct login on $rhost..." );

				#Disable command echo
				$ssh->exec( "stty raw -echo" );

				#Check if can exec commands through ssh
				my $checkcommand = "date > /dev/null";
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
				$ssh->read_all();    #There is the prompt in the input stream, we remove it
				$sshoutput[1] =~ s/^\s+//;
				$sshoutput[1] =~ s/\s+$//;

				if ( $sshoutput[1] !~ /^$/ )
				{
					&errormsg( "Login on $rhost ($rip) ok, but can not execute commands" );
					$error = "true";
				}
			}
		};
		$err_out = $@;

		if ( $err_out =~ /^$/ && $error eq "false" )
		{
			&successmsg( "Running process for configure RSA comunication" );
			&zenlog( "Deleting old RSA key on $lhost ($lip)" );
			unlink glob ( "/root/.ssh/id_rsa*" );
			&zenlog( "Creating new RSA keys on $lhost ($lip)" );
			@eject = `$sshkeygen -t rsa -f /root/.ssh/id_rsa -N \"\"`;
			open FR, "/root/.ssh/id_rsa.pub";

			while ( <FR> )
			{
				$rsa_pass = $_;
			}

			chomp ( $rsa_pass );
			close FR;

			# - now you know you're logged in - #
			# run command
			&zenlog( "Copying new RSA key from $lhost ($lip) to $rhost ($rip)" );
			my $eject = $ssh->exec(
				"rm -f /root/.ssh/authorized_keys; mkdir -p /root/.ssh/; echo $rsa_pass \>\> /root/.ssh/authorized_keys"
			);

			$ssh->read_all();    #Clean the ssh buffer
			my $rhostname = $ssh->exec( "hostname" );
			@rhostname = split ( "\ ", $rhostname );
			$rhostname = $rhostname[0];
			chomp ( $rhostname );
			@ifcl = split ( ":", $ifname );
			$ifcl = $ifcl[0];
			my $ripeth0 = $ssh->exec( "ip addr show $ifcl | grep $ifcl\$" );
			@ripeth0 = split ( "\ ", $ripeth0 );
			@ripeth0 = split ( "\/", $ripeth0[1] );
			$ripeth0 = $ripeth0[0];
			chomp ( $ripeth0 );

			$modified = "false";

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
				open FO, "> $filecluster";
				print FO "MEMBERS\:$lhost\:$lip\:$rhost\:$rip\n";
				print FO "IPCLUSTER\:$vipcl\:$ifname\n";
				print FO "CABLE\:$cable\n";
				close FO;
			}

			# closes the ssh connection
			$ssh->close();

			#connect to remote host without password
			my $user = "root";
			my $host = "$rip";
			chomp ( $rip );
			$hosts = "$user\@$rip";
			chomp ( $hosts );

			#deleting remote id_rsa key
			&zenlog( "Deleting old RSA key on $rhost" );
			ssh( $hosts, "rm -rf /root/.ssh/id_rsa*" );

			#creating new remote id_rsa key
			&zenlog( "Creating new remote RSA key on $rhost" );
			ssh( $hosts, "$sshkeygen -t rsa -f /root/.ssh/id_rsa -N \"\" &> /dev/null" );

			#copying id_rsa remote key to local
			&zenlog( "Copying new RSA key from $rhost to $lhost" );
			@eject = `$scp $hosts:/root/.ssh/id_rsa.pub /tmp/`;

			#open file
			use File::Copy;
			move( "/tmp/id_rsa.pub", "/root/.ssh/authorized_keys" );

			#open file and copy to other
			&zenlog( "Enabled RSA communication between cluster hosts" );
			&successmsg( "Enabled RSA communication between cluster hosts" );

			#run zeninotify for syncronization directories
		}
		else
		{
			&errormsg( "RSA communication with $rhost ($rip) has failed..." );
			$ssh->close();
		}
	}

	#action configure cluster ucarp
	if ( $action eq "Configure cluster type" && $typecl !~ /^$/ )
	{
		if ( $cable eq "Crossover cord" )
		{
			$ignoreifstate = "--ignoreifstate";
		}
		else
		{
			$ignoreifstate = "";
		}

		@ifname = split ( ":", $ifname );
		@eject =
		  `$ssh -o \"ConnectTimeout=10\" -o \"StrictHostKeyChecking=no\" root\@$rip \'$pen_bin\' 2>&1 `;

		if ( $? == 0 )
		{
			#remote execution
			my $ssh = Net::SSH::Expect->new(
											 host    => "$rip",
											 user    => 'root',
											 raw_pty => 1
			);

			#local execution
			$ssh->run_ssh() or die "SSH process couldn't start: $!";
			my $eject = $ssh->exec( "pkill -9 ucarp" );
			chomp ( $rip );
			$user = "root";
			my @eject = `pkill -9 ucarp`;

			#set cluster to UP on cluster file
			&setClusterStatusUp();
			&zenlog( "Sending $filecluster to $rip" );
			@eject = `$scp $filecluster root\@$rip\:$filecluster`;

			if ( $typecl =~ /^equal$/ )
			{
				&successmsg(
					"Running Zen latency Service and Zen inotify Service, please wait and don't stop the process"
				);
				&zenlog(
					"running on local: $ucarp -r $deadratio $ignoreifstate --interface=$ifname[0] --srcip=$lip --vhid=$idcluster --pass=secret --addr=$vipcl --upscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-start.pl --downscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-stop.pl -B -f local6"
				);
				my @eject = system (
					"$ucarp -r $deadratio $ignoreifstate --interface=$ifname[0] --srcip=$lip --vhid=$idcluster --pass=secret --addr=$vipcl --upscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-start.pl --downscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-stop.pl -B -f local6"
				);
				&successmsg( "Configuring $lhost, please wait and don't stop the process" );
				sleep ( 10 );
				&successmsg(
					"Local node $lhost configured, configuring $rhost, please wait and don't stop the process"
				);
				&zenlog(
					"running on remote: $ucarp -r $deadratio $ignoreifstate --interface=$ifname[0] --srcip=$rip --vhid=$idcluster --pass=secret --addr=$vipcl --upscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-start.pl --downscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-stop.pl -B -f local6"
				);
				my $eject = $ssh->exec(
					"$ucarp -r $deadratio $ignoreifstate --interface=$ifname[0] --srcip=$rip --vhid=$idcluster --pass=secret --addr=$vipcl --upscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-start.pl --downscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-stop.pl -B -f local6"
				);
				&successmsg(
					"Remote node $rhost configured, configuring cluster type, please wait and don't stop the process"
				);
				sleep ( 10 );
				&successmsg( "Cluster configured on mode $lhost or $rhost can be masters" );
				&successmsg(
					"Reload here <a href=\"index.cgi?id=$id\"><i class=\"fa fa-refresh action-icon green\" title=\"Refresh\"></i></a> to apply changes"
				);
			}

			if ( $typecl =~ /$lhost-$rhost/ )
			{
				&successmsg(
							 "Running Zen latency Service and Zen inotify Service, please wait" );
				my @eject = system (
					"$ucarp -r $deadratio $ignoreifstate --interface=$ifname[0] --srcip=$lip -P --vhid=$idcluster --pass=secret --addr=$vipcl --upscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-start.pl --downscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-stop.pl -B -f local6"
				);
				&successmsg( "Configuring $lhost, please wait and don't stop the process" );
				sleep ( 5 );
				&successmsg(
					"Local node $lhost configured, configuring $rhost, please wait and don't stop the process"
				);
				my $eject = $ssh->exec(
					"$ucarp -r $deadratio $ignoreifstate --interface=$ifname[0] -k 50 --srcip=$rip --vhid=$idcluster --pass=secret --addr=$vipcl --upscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-start.pl --downscript=/usr/local/zenloadbalancer/app/zenlatency/zenlatency-stop.pl -B -f local6"
				);
				&successmsg(
					"Remote node $rhost configured, configuring cluster type, please wait and don't stop the process"
				);
				sleep ( 10 );
				&successmsg(
					 "Cluster configured on mode $lhost master and $rhost backup automatic failover"
				);
				&successmsg(
					"Reload here <a href=\"index.cgi?id=$id\"><i class=\"fa fa-refresh action-icon green\" title=\"Refresh\"></i></a> to apply changes"
				);
			}

			if ( $typecl =~ /Disabled/ )
			{
				&successmsg(
							 "Disabling Zen latency Service and Zen inotify Service, please wait" );
				my $eject = $ssh->exec( "pkill -9f zeninotify.pl" );
				my @eject = `pkill -9f zeninotify.pl`;
				$eject = $ssh->exec( "pkill -9 ucarp" );
				@eject = `pkill -9 ucarp`;
				unlink ( $filecluster );
				$eject = $ssh->exec( "rm $filecluster" );
				$eject = $ssh->exec( "rm -f /root/.ssh/authorized_keys" );
				$eject = `rm -rf /root/.ssh/authorized_keys`;
				&successmsg( "Cluster disabled on $lhost and $rhost" );
				undef $rhost;
				undef $lhost;
				undef $vipcl;
				undef $rip;
				undef $lip;
				undef $clstatus;
			}
			$ssh->close();
		}
		else
		{
			if ( $typecl =~ /Disabled/ )
			{
				&successmsg(
							 "Disabling Zen latency Service and Zen inotify Service, please wait" );

				#remote execution
				my $ssh = Net::SSH::Expect->new(
												 host    => "$rip",
												 user    => 'root',
												 raw_pty => 1
				);

				#local execution
				$ssh->run_ssh() or die "SSH process couldn't start: $!";

				my $eject = $ssh->exec( "pkill -9f zeninotify.pl" );
				$ssh->close();
				my @eject = `pkill -9f zeninotify.pl`;
				unlink ( $filecluster );
				$eject = $ssh->exec( "rm $filecluster" );
				&successmsg( "Cluster disabled on $lhost and $rhost" );
				undef $rhost;
				undef $lhost;
				undef $vipcl;
				undef $rip;
				undef $lip;
				undef $clstatus;
			}
			else
			{
				&errormsg(
					"Error connecting between $lip and $rip, please configure the RSA connectiong first"
				);
			}
		}
	}
}

print "
               <div class=\"box grid_12\">
                 <div class=\"box-head\">
                       <span class=\"box-icon-24 fugue-24 server\"></span>       
                       <h2>Cluster configuration</h2>
                 </div>
                 <div class=\"box-content global-farm\">
        ";

#vip cluster form
#cluster information
print
  "<p><h6>Cluster status: <a href=\"index.cgi?id=$id\"><i class=\"fa fa-refresh action-icon fa-fw green\" title=\"Refresh\"></i></a></h6></p>";
print "<hr></hr>";
print "<div class=\"row\"><p>";

$error = "false";

if ( ( $rhost && $lhost && $rip && $lip && $rip && $vipcl && $clstatus ) )
{
	#zenlatency is running on local:
	my @ucarppidl = `$pidof -x ucarp`;
	print "Zen latency ";
	if ( @ucarppidl )
	{
		print "is <b>UP</b>\n";
	}
	else
	{
		print "is <b>DOWN</b>\n";
		$error = "true";
	}
	print "on <b>$lhost $lip</b>";

	print " | ";

	#zenlatency is running on remote?:
	my @ucarppidr =
	  `ssh -o \"ConnectTimeout=10\" -o \"StrictHostKeyChecking=no\" root\@$rip \"pidof -x ucarp \" 2>&1`;
	print "Zen latency ";
	if ( @ucarppidr[0] =~ /^[0-9]/ )
	{
		print "is <b>UP</b>\n";
	}
	else
	{
		print "is <b>DOWN</b>\n";
		$error = "true";
	}
	print "on <b>$rhost $rip</b>";

	if ( $error eq "false" )
	{
		print " <i class=\"fa fa-check-circle fa-fw green action-icon\"></i>";
	}
	else
	{
		print " <i class=\"fa fa-exclamation-circle fa-fw red action-icon\"></i>";
	}

	print "</p><p>";

	$vipclrun  = "false";
	$vipclrun2 = "false";
	$activecl  = "false";
	my @vipwhereis = `$ip_bin addr list`;

	if ( grep ( /$vipcl/, @vipwhereis ) )
	{
		$vipclrun = $lhost;
		print "Cluster IP <b>$vipcl</b> is active on <b>$vipclrun</b> ";
		$activecl = $lhost;
	}

	my @vipwhereis2 =
	  `ssh -o \"ConnectTimeout=10\" -o \"StrictHostKeyChecking=no\" root\@$rip \"$ip_bin addr list\" `;

	if ( grep ( /$vipcl\//, @vipwhereis2 ) )
	{
		$vipclrun2 = $rhost;
		print "Cluster is active on $vipclrun2</b>";
		$activecl = $rhost;
	}

	if (    ( $vipclrun eq "false" && $vipclrun2 eq "false" )
		 || ( $vipclrun ne "false" && $vipclrun2 ne "false" ) )
	{
		print " <i class=\"fa fa-exclamation-circle fa-fw red action-icon\"></i>";
		$activecl = "false";
		$error    = "true";
	}
	else
	{
		print " <i class=\"fa fa-check-circle fa-fw green action-icon\"></i>";
	}

	print "</p>";
	print "<p>";

	#where is zeninotify
	my @zeninopidl = `$pidof -x zeninotify.pl`;
	print "Zen Inotify is running on ";
	$zeninorun  = "false";
	$zeninorun2 = "false";
	$activeino  = "false";
	$activeino1 = "false";
	$activeino2 = "false";

	if ( @zeninopidl[0] =~ /^[0-9]/ )
	{
		print "<b>$lhost</b>\n";
		$zeninorun  = "true";
		$activeino  = $lhost;
		$activeino1 = $lhost;
	}

	my @zeninopidr =
	  `ssh -o \"ConnectTimeout=10\" -o \"StrictHostKeyChecking=no\" root\@$rip "pidof -x zeninotify.pl" `;

	if ( @zeninopidr[0] =~ /^[0-9]/ )
	{
		print "<b>$rhost</b>\n";
		$zeninorun  = "true";
		$activeino  = $rhost;
		$activeino2 = $rhost;
	}

	if ( $activeino2 ne "false" && $activeino1 ne "false" )
	{
		$zeninorun = "false";
	}

	if ( @zeninopidr[0] =~ /^[0-9]/ && @zeninopidl[0] =~ /^[0-9]/ )
	{
		$error = "true";
	}

	if (    ( $zeninorun eq "false" && $zeninorun2 eq "false" )
		 || ( $zeninorun ne "false" && $zeninorun2 ne "false" ) )
	{
		print " <i class=\"fa fa-exclamation-circle fa-fw red action-icon\"></i>";
		$activeino = "false";
		$error     = "true";
	}
	else
	{
		if ( $activeino eq $activecl )
		{
			print " <i class=\"fa fa-check-circle fa-fw green action-icon\"></i>";
		}
		else
		{
			print " <i class=\"fa fa-exclamation-circle fa-fw red action-icon\"></i>";
			$error = "true";
		}
	}
}
else
{
	print "Cluster not configured!";
	$error = "true";
}

print "</p></div>";
print "<p><h6>Global status:";

if ( $error eq "false" )
{
	print " <i class=\"fa fa-check-circle fa-fw green action-icon\"></i></h6></p>";
	print "<div class=\"row\"><p>";

	if ( &getClusterActiveNode() eq "true" )
	{
		#form form manual sync on cluster
		print "<form method=\"post\" action=\"index.cgi\">";
		print
		  "<input type=\"submit\" value=\"Force sync cluster from master to backup\" name=\"action\" class=\"button big grey\">";
		print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
		print "</form>";
		print "</p></div>";
	}
}
else
{
	print " <i class=\"fa fa-exclamation-circle fa-fw red action-icon\"></i></h6>";
}

print "<hr></hr>";
print "<div class=\"form-row\">";

my $cl_iface;

#cluster form
if ( $error eq "true" )
{
	print "<form method=\"post\" action=\"index.cgi\">";
	print
	  "<p class=\"form-label\"><b>Virtual IP for Cluster, or create new virtual IP <a href=\"index.cgi?id=3-2\">here</a>.</b> Only virtual IPs with UP status are listed.</p>";
	print
	  "<div class=\"form-item\"><select name=\"vipcl\" class=\"monospace width-initial\">\n";

	my @interfaces_available = @{ &getActiveInterfaceList() };

	foreach my $iface ( @interfaces_available )
	{
		next if $$iface{ ip_v } == 6;
		next if $$iface{ vini } eq '';

		my $selected = '';

		if ( $vipcl eq $$iface{ addr } )
		{
			$cl_iface = $iface;
			$selected = "selected=\"selected\"";
		}

		print
		  "<option value=\"$$iface{addr}:$$iface{name}\" $selected>$$iface{dev_ip_padded}</option>";
	}

	print "</select>";
	print "<input type=\"hidden\" name=\"id\" value=\"$id\"> ";
	print "</div>";
	print "<p class=\"form-label\"><b></b></p>";
	print
	  "<div class=\"form-item\"><input type=\"submit\" value=\"Save VIP\" name=\"action\" class=\"button grey\">";
	print "</div>";
	print "</form>";
	print "</div>";

	# Locate real interface for vipcl
	my $parent_if_name = $$cl_iface{ dev };
	$parent_if_name .= ".$$cl_iface{vlan}" if $$cl_iface{ vlan } ne '';

	# Locate real interface for vipcl
	foreach my $iface ( @interfaces_available )
	{
		next if $$iface{ name } ne $parent_if_name;
		next if $$iface{ ip_v } ne 4;

		$lip = $$iface{ addr };
	}

	if ( $lhost =~ /^$/ )
	{
		$lhost = hostname();
	}

	if ( $vipcl !~ /^$/ )
	{
		print "<div class=\"form-row\">";
		print "<form method=\"post\" action=\"index.cgi\">";
		print "<p class=\"form-label\"><b>Local hostname</b></p>";
		print
		  "<div class=\"form-item\"><input type=\"text\" name=\"lhost\" class=\"fixedwidth\" value=\"$lhost\" size=12> ";
		print "<span><b> $iface IP</b></span> ";
		print
		  "<input type=\"text\" name=\"lip\" class=\"fixedwidth\" value=\"$lip\" size=12>";
		print "</div>";

		print "<p class=\"form-label\"><b>Remote hostname</b></p>";
		print
		  "<div class=\"form-item\"><input type=\"text\" name=\"rhost\" class=\"fixedwidth\" value=\"$rhost\" size=12> ";
		print "<span><b> $iface IP</b></span> ";
		print
		  "<input type=\"text\" name=\"rip\" class=\"fixedwidth\" value=\"$rip\" size=12>";

		print "</div>";

		print "<p class=\"form-label\"><b>Cluster ID (1-255)</b></p>";
		print
		  "<div class=\"form-item\"><input type=\"number\" name=\"idcluster\" class=\"fixedwidth\" value=\"$idcluster\" size=12>";
		print "</div>";

		print "<p class=\"form-label\"><b>Dead ratio</b></p>";
		print
		  "<div class=\"form-item\"><input type=\"number\" name=\"deadratio\" class=\"fixedwidth\" value=\"$deadratio\" size=12>";
		print "</div>";
		print "<p class=\"form-label\"><b></b></p>";
		print
		  "<div class=\"form-item\"><input type=\"submit\" value=\"Save\" name=\"action\" class=\"button grey\">";
		print "</div>";
		print "</div>";

		print "<input type=\"hidden\" name=\"vipcl\"value=\"$vipcl\">";
		print "<input type=\"hidden\" name=\"typecl\"value=\"$typecl\">";
		print "<input type=\"hidden\" name=\"clstatus\"value=\"$clstatus\">";
		print "<input type=\"hidden\" name=\"ifname\"value=\"$ifname\">";
		print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
		print "</form>";
	}

	print "<br>";

	if (    $rhost !~ /^$/
		 && $lhost !~ /^$/
		 && $rip !~ /^$/
		 && $lip !~ /^$/
		 && $vipcl !~ /^$/ )
	{
		print "<div class=\"form-row\">";
		print "<form method=\"post\" action=\"index.cgi\">";
		print
		  "<p class=\"form-label\"><b>Remote Hostname root password.</b> This value will not be remembered.</p>";
		print
		  "<div class=\"form-item\"><input type=\"password\" name=\"pass\" class=\"fixedwidth\" value=\"\" size=12>";
		print "</div>";
		print "<p class=\"form-label\"><b></b></p>";
		print
		  "<div class=\"form-item\"><input type=\"submit\" value=\"Configure RSA connection between nodes\" name=\"action\" class=\"button big grey\">";
		print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
		print "</div>";
		print "</div>";
		print "</form>";
	}
}

if (    $rhost !~ /^$/
	 && $lhost !~ /^$/
	 && $rip !~ /^$/
	 && $lip !~ /^$/
	 && $vipcl !~ /^$/ )
{
	#form for run and stop ucarp service
	print "<form method=\"post\" action=\"index.cgi\">";
	print "<p><h6>Cluster type configuration:</h6></p>";
	print "<hr></hr>";
	print "<div class=\"row\">";
	print "<p class=\"form-label\"><b>Cluster type</b></p>";
	print "<div class=\"form-item\">";

	print "<select name=\"typecl\" class=\"fixedwidth\">\n";

	if ( $activecl eq "$lhost" || $clstatus eq "" )
	{
		if ( $typecl =~ /^$/ )
		{
			print
			  "<option value=\"Disabled\" selected=\"selected\">--Disable cluster on all hosts--</option>";
		}
		else
		{
			print "<option value=\"Disabled\">--Disable cluster on all hosts--</option>";
		}

		if ( $typecl eq "$lhost-$rhost" )
		{
			print
			  "<option value=\"$lhost-$rhost\" selected=\"selected\">$lhost master and $rhost backup automatic failback</option>";
		}
		elsif ( $typecl eq "$rhost-$lhost" )
		{
			print
			  "<option value=\"$rhost-$lhost\" selected=\"selected\">$rhost master and $lhost backup automatic failback</option>";
		}
		else
		{
			print
			  "<option value=\"$lhost-$rhost\">$lhost master and $rhost backup automatic failback</option>";
		}

		if ( $typecl =~ /^equal/ )
		{
			print
			  "<option value=\"equal\" selected=\"selected\">$lhost or $rhost can be masters</option>";
		}
		else
		{
			print "<option value=\"equal\">$lhost or $rhost can be masters</option>";
		}
	}
	else
	{
		print
		  "<option value=\"Disabled\" selected=\"selected\">--Disable cluster on all hosts--</option>";
	}

	print "</select>";
	print "</div>";

	if ( $cable eq "Crossover cord" )
	{
		$checked = "checked";
	}
	else
	{
		$checked = "";
	}

	print
	  "<p class=\"form-label\"><b>Use crossover patch cord</b></p> <div class=\"form-item\"><input type=\"checkbox\" name=\"cable\" value=\"Crossover cord\" $checked /></div>";

	print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
	print "<input type=\"hidden\" name=\"lhost\" value=\"$lhost\">";
	print "<input type=\"hidden\" name=\"rhost\" value=\"$rhost\">";
	print "<input type=\"hidden\" name=\"lip\" value=\"$lip\">";
	print "<input type=\"hidden\" name=\"rip\" value=\"$rip\">";
	print "<input type=\"hidden\" name=\"vipcl\" value=\"$vipcl\">";
	print "<input type=\"hidden\" name=\"ifname\" value=\"$ifname\">";
	print "<input type=\"hidden\" name=\"cable\" value=\"$cable\">";
	print "<input type=\"hidden\" name=\"idcluster\" value=\"$idcluster\">";
	print "<input type=\"hidden\" name=\"deadratio\" value=\"$deadratio\">";

	print "<p class=\"form-label\"><b></b></p>";
	print
	  "<div class=\"form-item\"><input type=\"submit\" value=\"Configure cluster type\" name=\"action\" class=\"button grey\">";
	print "</div>";
	print "</div>";

	if ( $clstatus !~ /^$/ )
	{
		print
		  "<input type=\"submit\" value=\"Test RSA connections\" name=\"action\" class=\"button grey\">";
	}

	if ( $activecl eq "$lhost" )
	{
		print
		  "<input type=\"submit\" value=\"Test failover\" name=\"action\" class=\"button grey\">";
	}

	if ( `ps aux | grep "ucarp" | grep "\\-k 100" | grep -v grep` )
	{
		print
		  "<input type=\"submit\" value=\"Return node from maintenance\" name=\"action\" class=\"button big grey\">";
	}
	else
	{
		print
		  "<input type=\"submit\" value=\"Force node as backup for maintenance\" name=\"action\" class=\"button big grey\">";
	}

	print "</form>";
}

if ( $vipcl !~ /^$/ && $clstatus eq "" )
{
	print "<form method=\"post\" action=\"index.cgi\">";
	print "<input type=\"hidden\" name=\"clstatus\"value=\"$clstatus\">";
	print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
	print
	  "<input type=\"submit\" value=\"Cancel\" name=\"action\" class=\"button grey\">";
	print "</form>";
}

print "</div></div></div>";
print "<br class=\"cl\" >";

print "        </div>
    <!--Content END-->
  </div>
</div>
";
