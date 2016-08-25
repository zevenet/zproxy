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

use Data::Dumper;

use threads;
require "/usr/local/zenloadbalancer/www/thread_functions.cgi";

print "
<!--- CONTENT AREA -->
<div class=\"content container_12\">
";

###################################
# BREADCRUMB
###################################
print "
<div class=\"grid_6\">
	<h1>Settings :: ZCluster</h1>
</div>
";

#~ print "
#~ <div class=\"box grid_12\">
#~ 
	#~ <div class=\"box-head\">
		#~ <span class=\"box-icon-24 fugue-24 plus\"></span>
		#~ <h2>Cluster settings</h2>
	#~ </div>
#~ ";

####################################
# CLUSTER STATUS
####################################
&getClusterStatus();

my $zcl_conf = &getZClusterConfig();

if ( ! -f $floatfile )
{
	&tipsimplemsg("To get a stateful cluster configure first the Floating IP addresses in Settings > Interfaces");
}
else
{
	my $float_ifaces_conf = &getConfigTiny( $floatfile );

	for my $if_name ( keys $float_ifaces_conf->{_} )
	{
		if ( $float_ifaces_conf->{_}->{ $if_name } eq '' )
		{
			&warnmsg("Some interface does not have configured a floating IP, the cluster may not be stateful");
			last;
		}
	}
}

if ( $action eq "Save" )
{
	my $changed_config;
	my $error;

	if ( $deadratio != $zcl_conf->{_}->{deadratio} )
	{
		# verify new deadratio value
		my $error;
		$error = ( $deadratio < 0 || &isnumber( $deadratio ) ne 'true' );

		if ( ! $error )
		{
			$zcl_conf->{_}->{deadratio} = $deadratio;
			$changed_config = 1;
		}
	}

	if ( $interface ne $zcl_conf->{_}->{interface} || ! $zcl_conf->{_}->{interface} )
	{
		&zenlog( "interface $interface" );
		# verify new interface value
		my $error;
		my $iface;
		for my $if_ref ( @{ &getConfigInterfaceList() } )
		{
			#~ &zenlog( "interface $if_ref->{name}" );
			$iface = $if_ref if $if_ref->{name} eq $interface;
		}

		&zenlog( Dumper $iface );
		$error = ( ! $iface || defined $iface->{vini} );

		if ( ! $error )
		{
			$zcl_conf->{_}->{interface} = $interface;
			$changed_config = 1;
		}
	}

	# prefered primary node
	if ( $primary && $primary ne $zcl_conf->{_}->{primary} )
	{
		&zenlog( "primary $primary" );
		# verify new failback value
		my $error;
		my @primary_opts = ( 'any' );
		for my $zcl_key ( keys %{ $zcl_conf } )
		{
			next if $zcl_key eq '_';
			push @primary_opts, $zcl_key;
		}
		$error = ( grep( /^$primary$/, @primary_opts ) != 1 );

		if ( ! $error )
		{
			$zcl_conf->{_}->{primary} = $primary;
			$changed_config = 1;
		}
	}
	elsif ( ! $primary )
	{
		$zcl_conf->{_}->{primary} = &getHostname();
		$changed_config = 1;
	}

	$error = &setZClusterConfig( $zcl_conf ) if $changed_config;

	if ( ! &getZClusterStatus() )
	{
		### Initial cluster configuration ###

		## Setting-up nodes keys exchange ##
		
		# verify ip and pass
		my $error_code;
		my $ipv = &ipversion( $rip );
		$error_code = ( $ipv != 4 && $ipv != 6 );
		
		# exchange keys
		$error_code = &exchangeIdKeys( $rip, $pass ) if ! $error_code;

		## Finish cluster configuration file ##

		# get hostnames
		my $remote_hostname = &runRemotely( 'hostname', $rip ) if ! $error_code;
		my $local_hostname = &getHostname();

		chomp $remote_hostname;
		chomp $local_hostname;
		
		if ( ( ! $error_code ) && $remote_hostname && $local_hostname )
		{
			$zcl_conf->{ $local_hostname }->{ ip } = &iponif( $interface );
			$zcl_conf->{ $remote_hostname }->{ ip } = $rip;
		}

		if ( ! $error_code && &setZClusterConfig( $zcl_conf ) )
		{
			## Start cluster services ##

			# first synchronization
			&runSync( $configdir );

			# generate cluster config and start cluster service
			my $error_code = &enableZCluster();

			# force cluster file sync
			system( "scp $filecluster root\@$zcl_conf->{$remote_hostname}->{ip}:$filecluster" );

			# local conntrackd configuration
			&setConntrackdConfig();

			# remote conntrackd configuration
			my $cl_output = &runRemotely(
				"$zcluster_manager setKeepalivedConfig",
				$zcl_conf->{$remote_hostname}->{ip}
			);
			&zenlog( "rc:$? $cl_output" );

			# start remote interfaces, farms and cluster
			my $cl_output = &runRemotely(
				'/etc/init.d/zenloadbalancer start',
				$zcl_conf->{$remote_hostname}->{ip}
			);
			&zenlog( "rc:$? $cl_output" );
		}
		else
		{
			&errormsg("An error happened enabling the cluster");
		}
	}
	elsif ( $changed_config )
	{
		### cluster Re-configuration ###
		my $rhost = &getZClusterRemoteHost();
		
		system( "scp $filecluster root\@$zcl_conf->{$rhost}->{ip}:$filecluster" );

		# reconfigure local conntrackd
		&setConntrackdConfig();

		# reconfigure remote conntrackd
		&zenlog(
			&runRemotely(
				"$zcluster_manager setKeepalivedConfig",
				$zcl_conf->{$rhost}->{ip}
			)
		);

		# reload keepalived configuration local and remotely
		$error_code = &enableZCluster();
		
		&zenlog(
			&runRemotely(
				"$zcluster_manager enableZCluster",
				$zcl_conf->{$rhost}->{ip}
			)
		);
	}
}
elsif ( $action eq 'Disable cluster' )
{
	# handle remote host when disabling cluster
	my $rhost = &getZClusterRemoteHost();

	### Stop cluster services ###
	if ( &getZClusterNodeStatus() eq 'master' )
	{
		# 1 stop master zeninotify
		system( "$zenino stop" );

		# 2 stop backup node zenloadbalancer
		&zenlog(
			&runRemotely(
				"/etc/init.d/zenloadbalancer stop >/dev/null 2>&1",
				$zcl_conf->{$rhost}->{ip}
			)
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
		);

		# 2 stop slave zenloadbalancer
		system( "/etc/init.d/zenloadbalancer stop >/dev/null 2>&1" );
		
		# 3 stop master cluster service
		&zenlog(
			&runRemotely(
				"$zcluster_manager disableZCluster",
				$zcl_conf->{$rhost}->{ip}
			)
		);
	}
	
	### Remove configuration files ###
	# remove cluster configuration file
	# remove keepalived configuration file
	# remove zcluster node status file
	for my $cl_file ( $filecluster, $keepalived_conf, $znode_status_file, $conntrackd_conf )
	{
		unlink $cl_file;
		&zenlog(
			&runRemotely(
				"rm $cl_file >/dev/null 2>&1",
				$zcl_conf->{$rhost}->{ip}
			)
		);
	}

	# reset zcluster configuration
	$zcl_conf = undef;
}

######## End of Controller ########

# Cluster interface
my @interfaces_available = @{ &getActiveInterfaceList() };
my $cl_iface_options = "<option value=\"\" selected>Choose an interface</option>\n";

foreach my $iface ( @interfaces_available )
{
	next if $$iface{ vini } ne '';

	my $selected = '';

	if ( $zcl_conf->{_}->{interface} eq $$iface{ name } )
	{
		$selected = "selected";
	}

	$cl_iface_options .=
	  "<option value=\"$$iface{name}\" $selected>$$iface{dev_ip_padded}</option>\n";
}

# primary_server_options
my $primary_server_options = '';

if ( &getZClusterStatus() )
{
	my $selected_any;
	$selected_any = ( $zcl_conf->{_}->{ primary } eq 'any' )? 'selected': '';
	$primary_server_options = "<option value=\"any\" $selected_any>Any</option>\n";
	
	for my $zcl_key ( sort keys %{ $zcl_conf } )
	{
		next if ( $zcl_key eq '_' );

		my $selected = ( $zcl_key eq $zcl_conf->{_}->{ primary } )? 'selected': '';
		
		$primary_server_options .=
			"<option value=\"$zcl_key\" $selected>$zcl_key</option>\n";
	}
}

# HA interfaces
my @ha_avail;
for my $iface ( @interfaces_available )
{
	next if defined $iface->{vini};
	push ( @ha_avail, $iface ) if grep ( /^$iface->{name}$/, values %{ $zcl_conf->{interfaceList} } ) == 0;
}

# set default deadratio value
$zcl_conf->{_}->{ deadratio } = 1 if ! $zcl_conf;

######## Content ########

if ( &getZClusterStatus() )
{
	my $cl_info = &getZCusterStatusInfo();
	my $lhost = $cl_info->{localhost};
	my $rhost = $cl_info->{remotehost};
	
	my $img_stop = "<img src=\"img/icons/small/stop.png\" title=\"Down\">";
	my $img_start = "<img src=\"img/icons/small/start.png\" title=\"Up\">";

	## Box: Cluster settings
	print "
	<div class=\"box grid_12\">

		<div class=\"box-head\">
			<span class=\"box-icon-24 fugue-24 plus\"></span>
			<h2>Cluster status</h2>
		</div>
	";

	# Box content
	print "
		<div class=\"box-content global-farm\">
			<form method=\"post\" action=\"index.cgi\">
				<input type=\"hidden\" name=\"id\" value=\"$id\">
	";

	for my $host ( $cl_info->{localhost}, $cl_info->{remotehost} )
	{
		my $img = $img_start;
		my $msg; # = ucfirst $cl_info->{ $host }->{ node_role };

		if ( $cl_info->{ $host }->{ keepalived } eq 'ko' )
		{
			$img = $img_stop;
			$msg = "Cluster service not running";
		}
		elsif ( $cl_info->{ $host }->{ node_role } !~ /^(master|backup)$/ )
		{
			$img = $img_stop;
			$msg = "Cluster node with incorrect status";
		}
		elsif ( $cl_info->{ $host }->{ zeninotify } eq 'ko' )
		{
			$img = $img_stop;
			$msg = "Cluster synchronization error";
		}
		elsif ( $cl_info->{ $host }->{ arp } eq 'ko' )
		{
			$img = $img_stop;
			$msg = "Cluster ip announcement error";
		}
		elsif ( $cl_info->{ $host }->{ conntrackd } eq 'ko' )
		{
			$img = $img_stop;
			$msg = "Cluster state replication system error";
		}
		else
		{
			$msg = ucfirst $cl_info->{ $host }->{ node_role };
		}

		# Localhost node
		print "
					<div class=\"form-row\">
						<p class=\"form-label\">
							<b>$host</b>: $img $msg
						</p>
					</div>
		";
	}

	# Testing output
	#~ $Data::Dumper::Sortkeys = 1;
	#~ 
	#~ my $string = Dumper( $cl_info );
	#~ $string =~ s/\n/<br>/g;
	#~ $string =~ s/ /&nbsp/g;
	#~ 
	#~ # Test Row
	#~ print "
				#~ <div class=\"form-row\">
					#~ <p class=\"form-label\">
						#~ <b>$string</b>
					#~ </p>
				#~ </div>
	#~ ";

	# Button
	print "
				<br><br>
				<input type=\"submit\" value=\"Refresh\" name=\"action\" class=\"button grey\">
	";

	# Close form
	print "
			</form>
	";

	# Close box
	print "
		</div>
	</div>
	";
}

## Box: Cluster settings
print "
<div class=\"box grid_12\">

	<div class=\"box-head\">
		<span class=\"box-icon-24 fugue-24 plus\"></span>
		<h2>Cluster settings</h2>
	</div>
";

# Box content
print "
	<div class=\"box-content global-farm\">
		<form method=\"post\" action=\"index.cgi\">
			<input type=\"hidden\" name=\"id\" value=\"$id\">
";

# Row Health check interval
print "
			<div class=\"form-row\">
				<p class=\"form-label\">
					<b>Health check interval</b>
				</p>
				<div class=\"form-item\">
					<input type=\"number\" name=\"deadratio\" value=\"$zcl_conf->{_}->{deadratio}\" class=\"fixedwidth\">
				</div>
			</div>
";

# Row Cluster interface
print "
			<div class=\"form-row\">
				<p class=\"form-label\">
					<b>Cluster interface</b>
				</p>
				<div class=\"form-item\">
					<select name=\"interface\" class=\"fixedwidth monospace\">
						$cl_iface_options
					</select>
				</div>
			</div>
";

# Row Primary server
print "
			<div class=\"form-row\">
				<p class=\"form-label\">
					<b>Primary server</b>
				</p>
				<div class=\"form-item\">
					<select name=\"primary\" class=\"fixedwidth\">
						$primary_server_options
					</select>
				</div>
			</div>
" if &getZClusterStatus();

# Row Second node IP
print "
			<div class=\"form-row\">
				<p class=\"form-label\">
					<b>Second node IP</b>
				</p>
				<div class=\"form-item\">
					<input type=\"text\" name=\"rip\" value=\"\" class=\"fixedwidth\">
				</div>
			</div>
" if ! &getZClusterStatus();

# Row Second node password
print "
			<div class=\"form-row\">
				<p class=\"form-label\">
					<b>Second node password</b>
				</p>
				<div class=\"form-item\">
					<input type=\"text\" name=\"pass\" value=\"\" class=\"fixedwidth\">
				</div>
			</div>
" if ! &getZClusterStatus();

# Button
print "
			<br>
			<input type=\"submit\" value=\"Save\" name=\"action\" class=\"button grey\">
";

# Button
print "
			<input type=\"submit\" value=\"Disable cluster\" name=\"action\" class=\"button grey\">
" if &getZClusterStatus();

# Close form
print "
		</form>
";

# Close box
print "
	</div>
</div>
";

# Clear
print "<div class=\"clear\">";
print "</div>";

# Close content area
print "</div>";

print "
<script>
\$(document).ready(function () {
    \$(\".open-dialog\").click(function () {
        \$(\"#dialog\").attr('src', \$(this).attr(\"href\"));
        \$(\"#dialog-container\").dialog({
            width: 350,
            height: 350,
            modal: true,
            close: function () {
                window.location.replace('index.cgi?id=3-5');
            }
        });
        return false;
    });
});
</script>

<script>
\$(document).ready(function() {
    \$('#backups-table').DataTable( {
        \"bJQueryUI\": true,     
        \"sPaginationType\": \"full_numbers\",
		\"aLengthMenu\": [
			[10, 25, 50, 100, 200, -1],
			[10, 25, 50, 100, 200, \"All\"]
		],
		\"iDisplayLength\": 10
    });
} );
</script>
";
