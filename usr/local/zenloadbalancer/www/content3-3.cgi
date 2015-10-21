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

use Sys::Hostname;

print '<!--Content INI-->';
print '<div id="page-content">';

# cluster virtual "ip interface" pair is divided
# this happens when Save VIP button is pressed
if ( $vipcl =~ ' ' )
{
	( $vipcl, $ifname ) = split ( ' ', $vipcl );

}

if ( $action eq "Cancel" )
{
	unlink ( $filecluster );
	undef ( $vipcl );
}

if (    $action eq "Save"
	 || $action eq "Save VIP"
	 || $action eq "Configure cluster type" )
{
	setClusterConfig(
					  $lhost, $lip,       $rhost,  $rip,
					  $vipcl, $ifname,    $typecl, $clstatus,
					  $cable, $idcluster, $deadratio
	);
}

if ( -e $filecluster )    # get configuration from file
{
	(
	   $lhost,  $lip,      $rhost, $rip,       $vipcl, $ifname,
	   $typecl, $clstatus, $cable, $idcluster, $deadratio
	) = &getClusterConfig();
}

#action sync cluster
if ( $action eq "Force sync cluster from master to backup" )
{
	&setClusterSyncForced();
	&successmsg( "Cluster synced manually" );
}

#~ #action Test failover
if ( $action eq "Test failover" )
{
	&testClusterLocalNodeFailover();
}

if ( $action eq "Force node as backup for maintenance" )
{
	&setClusterNodeOnMaintenance( $cable, $ifname,    $deadratio,
								  $lip,   $idcluster, $vipcl );
}

if ( $action eq "Return node from maintenance" )
{
	&successmsg(
		  "Returning the node from maintenance, please wait and not stop the process" );
	&setClusterNodeOffMaintenance( $cable, $ifname,    $deadratio,
								   $lip,   $idcluster, $vipcl, $typecl );
	sleep ( 10 );
}

#~ #action test rsa
if ( $action eq "Test RSA connections" && $lhost && $rhost && $lip && $rip )
{
	if ( &testClusterRsaConnectionsWithIp( $rip ) == 0 )
	{
		&successmsg( "RSA connection from $lhost ($lip) to $rhost ($rip) successful" );
	}
	else
	{
		&errormsg( "RSA connection from $lhost ($lip) to $rhost ($rip) failed" );
	}
}

if ( $action eq "Configure RSA connection between nodes" )
{
	&setClusterRsaConnection( $lhost, $rhost, $lip, $rip, $pass );
	undef $typecl if !&isClusterConfigured();
}

#action configure cluster ucarp
if ( $action eq "Configure cluster type" )
{
	( $typecl, $lip, $rip, $ifname, $cable, $deadratio, $idcluster, $vipcl ) =
	  &setClusterType( $typecl, $lip, $rip, $ifname, $cable, $deadratio,
					   $idcluster, $vipcl );

	if ( $typecl =~ /Disabled/ )
	{
		undef $rhost;
		undef $lhost;
		undef $vipcl;
		undef $rip;
		undef $lip;
		undef $clstatus;
	}
}

############################## Content 3-3 #####################################
print '<!--Content Header INI-->';
print '<h2>Settings::Cluster</h2>';
print '<!--Content Header END-->';

print "<div class=\"container_12\">";
print "<div class=\"grid_12\">";
print "<div class=\"box-header\"> Cluster configuration </div>";
print "<div class=\"box stats\">";

### show Cluster status ###
my $refresh_link =
  qq{<a href="index.cgi?id=$id"><img src="img/icons/small/arrow_refresh.png" title="Refresh"></a>};

print "<b>Cluster status $refresh_link: </b>";

# Show Cluster status
# this function prints html
( $rhost, $lhost, $rip, $lip, $vipcl, $clstatus, $error ) =
  showCluserStatus( $rhost, $lhost, $rip, $lip, $vipcl, $clstatus, $error );
print "<div id=\"page-header\"></div>";

### show Global status ###
print "<b>Global status:</b>";

# aka: is zeninotify running?
if ( &isClusterLocalNodeActive() )
{
	print " <img src=\"/img/icons/small/accept.png\">";
	print "<br><br>";

	# force cluster sync
	print "<form method=\"get\" action=\"index.cgi\">";
	print
	  "<input type=\"submit\" value=\"Force sync cluster from master to backup\" name=\"action\" class=\"button small\">";
	print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
	print "</form>";
}
else
{
	print " <img src=\"/img/icons/small/exclamation.png\">";
}
print "<br>";
print "<div id=\"page-header\"></div>";

## 1st step for Cluster configuration form
# Virtual IP for Cluster, or create new virtual
print "<form method=\"get\" action=\"index.cgi\">";
print
  "<b>Virtual IP for Cluster, or create new virtual <a href=\"index.cgi?id=3-2\">here</a>.";
print "</b>";
print "<font size=\"1\">*Virtual ips with status up are listed only</font>";
print "<br>";
print "<select name=\"vipcl\">\n";    # <-- $vipcl

foreach $interface_file ( &getVirtualInterfaceFilenameList() )
{
	@data = &getInterfaceConfiguration( $interface_file );

	# example: @data = (eth0,0,192.168.101.240,255.255.255.0,up,,)
	# $data[0] = physical network interface
	# $data[1] = virtual network interface
	# $data[2] = ip
	if ( $vipcl eq $data[2] )
	{
		print
		  "<option value=\"$data[2] $data[0]:$data[1]\" selected=\"selected\">$data[0]:$data[1] $data[2]</option>";
	}
	else
	{
		print
		  "<option value=\"$data[2] $data[0]:$data[1]\">$data[0]:$data[1] $data[2]</option>";
	}
}
print "</select>";
print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
print "<input type=\"hidden\" name=\"ifname\" value=\"$ifname\">";
print "<br>";
print "<br>";
print
  "<input type=\"submit\" value=\"Save VIP\" name=\"action\" class=\"button small\">";
print "</form>";
print "<br>";

#locate real interface for vipcl
# iface only used to show physical network device on gui
( $iface, $lip ) = &getClusterLocalIPandInterface( $vipcl );

$lhost = hostname() if !defined $lhost;

## 2nd step for Cluster configuration form
# Local hostname with ip and Remote hostname with ip
if ( -e $filecluster )
{
	print "<form method=\"get\" action=\"index.cgi\">";
	print "<b>Local hostname.</b>";
	print "<br>";
	print " <input type=\"text\" name=\"lhost\" value=\"$lhost\" size=12>";
	print "<b> $iface IP</b>";
	print " <input type=\"text\" name=\"lip\" value=\"$lip\" size=12>";
	print "<br>";
	print "<br>";

	print "<b>Remote hostname.</b>";
	print "<br>";
	print " <input type=\"text\" name=\"rhost\" value=\"$rhost\" size=12>";
	print "<b> $iface IP</b>";
	print " <input type=\"text\" name=\"rip\" value=\"$rip\" size=12>";
	print "<br>";
	print "<br>";

	print "<b>Cluster ID (1-255).</b>";
	print "<br>";
	print " <input type=\"text\" name=\"idcluster\" value=\"$idcluster\" size=12>";
	print "<br>";
	print "<br>";

	print "<b>Dead ratio.</b>";
	print "<br>";
	print " <input type=\"text\" name=\"deadratio\" value=\"$deadratio\" size=12>";
	print "<br>";
	print "<br>";

	print "<input type=\"hidden\" name=\"vipcl\"value=\"$vipcl\">";
	print "<input type=\"hidden\" name=\"typecl\"value=\"$typecl\">";
	print "<input type=\"hidden\" name=\"clstatus\"value=\"$clstatus\">";
	print "<input type=\"hidden\" name=\"ifname\"value=\"$ifname\">";
	print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
	print
	  "<input type=\"submit\" value=\"Save\" name=\"action\" class=\"button small\">";

	print "</form>";
}
print "<br>";

## 3rd step for Cluster configuration form ##
# Remote Hostname root password
if ( &areClusterNodesDefined() )
{
	print "<form method=\"post\" action=\"index.cgi\">";
	print
	  "<b>Remote Hostname root password.</b><font size=\"1\">*This value will no be remembered</font>";
	print "<br>";
	print "<input type=\"password\" name=\"pass\"value=\"\" size=12>";
	print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
	print '<br><br>';
	print
	  "<input type=\"submit\" value=\"Configure RSA connection between nodes\" name=\"actionpost\" class=\"button small\">";
	print "</form>";
	print "<br>";
}

## 4th step for Cluster configuration form ##
# Cluster type
if ( &areClusterNodesDefined() )
{
	#form for run and stop ucarp service
	print "<form method=\"get\" action=\"index.cgi\">";
	print "<b>Cluster type: </b>";

	print "<select name=\"typecl\">\n";

	if ( $typecl eq 'Disabled' || $typecl eq '' )
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

	if ( $typecl eq 'equal' )
	{
		print
		  "<option value=\"equal\" selected=\"selected\">$lhost or $rhost can be masters</option>";
	}
	else
	{
		print "<option value=\"equal\">$lhost or $rhost can be masters</option>";
	}

	print "</select>";
	print "<br>";
	print "<br>";

	# initialize $cable => $checked
	$checked = ( $cable eq "Crossover cord" )	?	'checked'
												:	'';

	print
	  "<input type=\"checkbox\" name=\"cable\" value=\"Crossover cord\" $checked />&nbsp;Use crossover patch cord";
	print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
	print "<input type=\"hidden\" name=\"lhost\" value=\"$lhost\">";
	print "<input type=\"hidden\" name=\"rhost\" value=\"$rhost\">";
	print "<input type=\"hidden\" name=\"lip\" value=\"$lip\">";
	print "<input type=\"hidden\" name=\"rip\" value=\"$rip\">";
	print "<input type=\"hidden\" name=\"vipcl\" value=\"$vipcl\">";
	print "<input type=\"hidden\" name=\"ifname\" value=\"$ifname\">";
	print "<input type=\"hidden\" name=\"clstatus\" value=\"$clstatus\">";
	print "<input type=\"hidden\" name=\"cable\" value=\"$cable\">";
	print "<input type=\"hidden\" name=\"idcluster\" value=\"$idcluster\">";
	print "<input type=\"hidden\" name=\"deadratio\" value=\"$deadratio\">";
	print "<br>";
	print "<br>";
	print
	  "<input type=\"submit\" value=\"Configure cluster type\" name=\"action\" class=\"button small\">";

	if ( $clstatus !~ /^$/ )    # Test RSA connections
	{
		print
		  "<input type=\"submit\" value=\"Test RSA connections\" name=\"action\" class=\"button small\">";
	}

	if ( $activecl eq $lhost )    # Test failover
	{
		print
		  "<input type=\"submit\" value=\"Test failover\" name=\"action\" class=\"button small\">";
	}

	if ( &isClusterNodeInMaintenanceMode() )    # Return node from maintenance
	{
		print
		  "<input type=\"submit\" value=\"Return node from maintenance\" name=\"action\" class=\"button small\">";
	}
	else
	{
		print
		  "<input type=\"submit\" value=\"Force node as backup for maintenance\" name=\"action\" class=\"button small\">";
	}

	print "</form>";
	print "<br>";
}

if ( -e $filecluster && !&isClusterConfigured() )
{
	print "<form method=\"get\" action=\"index.cgi\">";
	print "<input type=\"hidden\" name=\"clstatus\"value=\"$clstatus\">";
	print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
	print
	  "<input type=\"submit\" value=\"Cancel\" name=\"action\" class=\"button small\">";
	print "</form>";
}

print "</div></div></div>";
print "<br class=\"cl\" >";

print "</div>";
print "<!--Content END-->";
print "</div>";
print "</div>";
