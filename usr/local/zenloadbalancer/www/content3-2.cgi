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

use IO::Socket;
use IO::Interface qw(:flags);
use Tie::File;
use Net::Netmask;
use Data::Dumper;
$Data::Dumper::Sortkeys = 1;

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
print "<div class=\"grid_6\"><h1>Settings :: Interfaces</h1></div>\n";

####################################
# CLUSTER STATUS
####################################
&getClusterStatus();

my $socket = IO::Socket::INET->new( Proto => 'udp' );
my @system_interfaces = $socket->if_list;

my %interface;

# temporal scope to initialize %interface
{
	if ( $action eq "addvip2" || $action eq "addvlan2" )
	{
		$if = $toif . $if;
	}

	$interface{ name }    = $if;
	$interface{ addr }    = $newip;
	$interface{ mask }    = $netmask;
	$interface{ gateway } = $gwaddr;
	$interface{ ip_v }    = $ipv;

	my %if = %{ &getDevVlanVini( $interface{ name } ) };

	$interface{ dev }  = $if{ dev };
	$interface{ vlan } = $if{ vlan };
	$interface{ vini } = $if{ vini };

	my $if_flags = $socket->if_flags( $interface{ name } );

	$interface{ status } = ( $if_flags & IFF_UP ) ? "up" : "down";
	$interface{ mac } = $socket->if_hwaddr( $interface{ dev } );
}

chomp %interface;

#~ &zenlog("interface ".Dumper \%interface);

# action edit interface
if ( $action eq "editif" )
{
	require "./content3-21.cgi";
}

# action Save & Up!
elsif (    $action eq "Save & Up!"
		|| $action eq "addvip2"
		|| $action eq "addvlan2" )
{
	$swaddif = "true";

	# check all possible errors
	# check if the interface is empty
	if ( $interface{ name } =~ /^$/ )
	{
		&errormsg( "Interface name can not be empty" );
		$swaddif = "false";
	}

	if ( $interface{ name } =~ /\s+/ )
	{
		&errormsg( "Interface name is not valid" );
		$swaddif = "false";
	}

	if ( $action eq "addvlan2" && &isnumber( $interface{ vlan } ) eq "false" )
	{
		&errormsg( "Invalid vlan tag value, it must be a numeric value" );
		$swaddif = "false";
	}

	if ( $action eq "addvip2" )
	{
		my $if_ref = &getInterfaceConfig( $interface{ name }, 4 );
		$if_ref = &getInterfaceConfig( $interface{ name }, 6 ) if !if_ref;

		if ( $if_ref )
		{
			&errormsg( "Network interface $interface{name} already exists." );
			$swaddif = "false";
		}
	}

	if ( $action eq "addvlan2" )
	{
		my $if_ref = &getInterfaceConfig( $interface{ name }, $interface{ ip_v } );
<<<<<<< HEAD

		if ( $if_ref )
		{
			&errormsg( "Network interface $interface{name} already exists." );
			$swaddif = "false";
		}
	}

	# check if the new newip is correct
	if ( &ipisok( $interface{ addr } ) eq "false" )
	{
		&errormsg( "IP Address $interface{addr} structure is not ok" );
		$swaddif = "false";
	}

	# check if the new newip is correct, check version ip
	if ( $interface{ ip_v } != &ipversion( $interface{ addr } ) )
	{
		&zenlog( "interface{ ip_v }:$interface{ ip_v } ipversion:"
				  . &ipversion( $interface{ addr } ) );

		if ( $interface{ ip_v } == 4 )
		{
			&errormsg(
				  "IP Address $interface{ addr } structure is not ok, must be an IPv4 structure"
			);
		}
		elsif ( $interface{ ip_v } == 6 )
		{
			&errormsg(
				  "IP Address $interface{ addr } structure is not ok, must be an IPv6 structure"
			);
		}
		$swaddif = "false";
	}

	# check if the new netmask for IPv6 is correct
	if (
		 $interface{ ip_v } == 6
		 && (    $interface{ mask } !~ /^\d+$/
			  || $interface{ mask } > 128
			  || $interface{ mask } < 0 )
	  )
	{
		&errormsg(
			"Netmask address $interface{mask} structure is not ok. Must be numeric [0-128]."
		);
		$swaddif = "false";
	}

	# check if the new gateway is correct, if empty don't worry
	if ( $interface{ gateway } && &ipisok( $interface{ gateway } ) eq "false" )
	{
		&errormsg( "Gateway address $interface{gateway} structure is not ok" );
		$swaddif = "false";
	}

	# end check, if all is ok
	if ( $swaddif eq "true" )
	{
		# vlans need to be created if they don't already exist
		my $exists = &ifexist( $interface{ name } );

		if ( $exists eq "false" )
		{
			&createIf( \%interface );    # create vlan if needed
		}

		my $old_iface_ref =
		  &getInterfaceConfig( $interface{ name }, $interface{ ip_v } );

		if ( $old_iface_ref )
		{
			# Delete old IP and Netmask
			if ( $action eq "Save & Up!" )
			{
				# delete interface from system to be able to repace it
				&delIp(
						$$old_iface_ref{ name },
						$$old_iface_ref{ addr },
						$$old_iface_ref{ mask }
				);
			}

			# Remove routes if the interface has its own route table: nic and vlan)
			if ( $interface{ vini } eq '' )
			{
				&delRoutes( "local", $old_iface_ref );
			}
		}

		&addIp( \%interface );

		my $state = &upIf( \%interface, 'writeconf' );

		if ( $state == 0 )
		{
			$interface{ status } = "up";
			&successmsg( "Network interface $interface{name} is now UP" );
		}

		# Writing new parameters in configuration file
		if ( $interface{ name } !~ /:/ )
		{
			&writeRoutes( $interface{ name } );
		}

		&setInterfaceConfig( \%interface );
		&applyRoutes( "local", \%interface );

		&successmsg( "All is ok, saved $interface{name} interface config file" );
	}
	else
	{
		&errormsg( "A problem detected configuring $interface{name} interface" );
	}
}

# action adddvip2 if ok add if not ok error and set variables
elsif ( $action eq "deleteif" )
{
	if ( $interface{ name } && $interface{ ip_v } )
	{
		my %interface =
		  %{ &getInterfaceConfig( $interface{ name }, $interface{ ip_v } ) };
		my $hasvini = 0;
		my $is_eth  = 0;

		# remove child vinis if any
		if ( $interface{ vini } eq '' )
		{
			my @configured_interfaces = @{ &getConfigInterfaceList() };
			foreach my $iface ( @configured_interfaces )
			{
				next if $iface->{ name } !~ /$interface{name}:/;

				&delRoutes( "local", $iface );
				&downIf( $iface, 'writeconf' );
				&delIf( $iface );
				$hasvini = 1;
			}

			&zenlog(
				  "All the Virtual Network interfaces of $interface{name} have been deleted." );
		}

		&delRoutes( "local", \%interface );

# If $if is a network interface (eth0, eth1...), don't shut down before delete the interface.
		if ( $interface{ vlan } eq '' && $interface{ vini } eq '' )
		{
			$is_eth = 1;
		}
		else    # vlan, vini
		{
			&downIf( \%interface, 'writeconf' );
		}

		&delIf( \%interface );

		# Success messages
		if ( $hasvini == 0 )
		{
			if ( $is_eth == 0 )
			{
				&successmsg( "Interface $interface{name} is now DELETED and DOWN" );
			}
			else
			{
				&successmsg( "Interface $interface{name} is now DELETED" );
			}
		}
		else
		{
			&successmsg(
				"Interface $interface{name} and its Virtual Network Interfaces are now DELETED and DOWN"
			);
		}
	}
	else
	{
		&errormsg( "The interface is not detected" );
	}
}
elsif ( $action eq "upif" )
{
	if ( $interface{ name } )
	{
		my $error = "false";
		my @stacks;

		for my $ip_v ( 4, 6 )
		{
			$if_ref = &getInterfaceConfig( $interface{ name }, $ip_v );

			if ( $$if_ref{ addr } )
			{
				#~ &zenlog("stacks:$$if_ref{addr}");
				push @stacks, $if_ref;
			}
		}

		# create vlan if required
		my $exists = &ifexist( $interface{ name } );
		if ( $exists eq "false" && !$interface{ vini } )
		{
			&createIf( \%interface );
		}

		# FIXME: Check IPv6 compatibility
		# open config file to get the interface parameters
		tie my @array, 'Tie::File', "$configdir/if_$if\_conf", recsep => ':';

		# check if the ip is already in use
		my @activeips = &listallips();

		if ( $interface{ vini } eq '' )
		{
			for my $iface ( @stacks )
			{
				&delRoutes( "local", $iface );
			}
		}

# Check if there are some Virtual Interfaces or Vlan with IPv6 and previous UP status to get it up.
		&setIfacesUp( $interface{ name }, "vlan" );
		&setIfacesUp( $interface{ name }, "vini" );

		for my $iface ( @stacks )
		{
			&addIp( $iface );
		}

		my $if_status;
		my $parent_if_name = &getParentInterfaceName( $interface{ name } );

		if ( !$parent_if_name )
		{
			$parent_if_status = 'up';
		}
		else
		{
			my $parent_if_ref = &getInterfaceConfig( $parent_if_name, $interface{ ip_v } );
			$parent_if_status =
			  &getInterfaceSystemStatus( $parent_if_ref, $interface{ ip_v } );
		}

		# FIXME: bug-prove this condition
		if ( $parent_if_status eq 'up' && $error eq "false" )
		{

			my $state = &upIf( \%interface, 'writeconf' );

			if ( $state == 0 )
			{
				&successmsg( "Network interface $interface{name} is now UP" );
			}
			else
			{
				&errormsg(
						"Interface $interface{name} is not UP, bad configuration or duplicate ip" );
			}

			for my $iface ( @stacks )
			{
				&applyRoutes( "local", $iface );
			}
		}
		else
		{
			&errormsg(
				  "$interface{name} has a parent interface DOWN, check the interfaces status" );
		}
	}
	else
	{
		&errormsg( "The interface is not detected" );
	}
}
elsif ( $action eq "downif" )
{
	my $if_ref = &getInterfaceConfig( $interface{ name }, $interface{ ip_v } );

	if ( ! $if_ref )
	{
		my @interfaces = @{ &getSystemInterfaceList() };

		for my $iface ( @interfaces )
		{
			if ( $iface->{ name } eq $interface{ name } && $iface->{ ip_v } == 4)
			{
				$if_ref = $iface;
				last;
			}
		}
	}
		
	my $state = &downIf( $if_ref, 'writeconf' );

	if ( $state == 0 )
	{
		&successmsg( "Interface $interface{name} is now DOWN" );
	}
	else
	{
		&errormsg(
			"Interface $interface{name} is not DOWN, check if any Farms is running over this interface"
		);
	}
}

# default gateway
elsif ( $action =~ /editgw/ )
{
	if ( $gwaddr !~ /^$/ )
	{
		my $ip_version =
		    ( $action =~ /6/ ) ? 6
		  : ( $action =~ /4/ ) ? 4
		  :                      '';
		my $if_ref = getInterfaceConfig( $if, $ip_version );

		&zenlog( "if:$if ip_version:$ip_version gwaddr:$gwaddr" );

		my $state = &applyRoutes( "global", $if_ref, $gwaddr );

		# TODO write def gw in file
		# action variable must be reset to show the page in normal view mode
		$action = "";

		if ( $state == 0 )
		{
			&successmsg( "The default gateway has been changed successfully" );
		}
		else
		{
			&errormsg( "The default gateway hasn't been changed" );
		}
	}
}
elsif ( $action =~ /deletegw/ )
{
	my $ip_version =
	    ( $action =~ /6/ ) ? 6
	  : ( $action =~ /4/ ) ? 4
	  :                      '';
	my $if_ref = getInterfaceConfig( $defaultgwif6, $ip_version );

	&zenlog( "defaultgwif6:$defaultgwif6 ip_version:$ip_version gwaddr:$gwaddr" );

	my $state = &delRoutes( "global", $if_ref );

	# action variable must be reset to show the page in normal view mode
	$action = "";

	if ( $state == 0 )
	{
		&successmsg( "The default gateway has been deleted successfully" );
	}
	else
	{
		&errormsg( "The default gateway hasn't been deleted" );
	}
}

# Calculate cluster and GUI ips
$guiip = &GUIip();
$clrip = &getClusterRealIp();
$clvip = &getClusterVirtualIp();

my @interfaces = @{ &getSystemInterfaceList() };

print "
               <div class=\"box grid_12\">
                 <div class=\"box-head\">
                       <span class=\"box-icon-24 fugue-24 server\"></span>       
                       <h2>Interfaces table</h2>
                 </div>
                 <div class=\"box-content no-pad\">";
print "<table id=\"interfaces-table\" class=\"display\">";
print "<thead>";
print "<tr>";
print "<th>Name</th>";
#~ print "<th>IPv</th>";
print "<th>Addr</th>";
print "<th>HWaddr</th>";
print "<th>Netmask/Bitmask</th>";
print "<th>Gateway</th>";
print "<th>Status</th>";
print "<th>Actions</th>";
print "</tr>";
print "</thead>";
print "<tbody>";

if ( $action eq "addvip" || $action eq "addvlan" )
{
	my $i = 0;

	for my $if ( @interfaces )
	{
		if ( $$if{ name } eq $toif && $$if{ ip_v } eq $interface{ ip_v } )
		{
			$i++;    # next to current position

			my $if_separator =
			    ( $action eq "addvip" )  ? ':'
			  : ( $action eq "addvlan" ) ? '.'
			  :                            '';
			my $iface = {
						  name     => "$$if{name}${if_separator}",
						  ip_v     => $$if{ ip_v },
						  mac      => $$if{ mac },
						  edit_row => 'true',
			};

			if ( $action eq "addvip" )
			{
				$$iface{ mask }    = $$if{ mask };
				$$iface{ gateway } = $$if{ gateway };
			}

			splice @interfaces, $i, 0, $iface;
		}

		$i++;
	}
}

for my $iface ( @interfaces )
{
	# Only IPv4
	next if $$iface{ip_v} == 6;
	
	my $cluster_icon = '';
	if (    ( $$iface{ addr } eq $clrip || $$iface{ addr } eq $clvip )
		 && $clrip
		 && $clvip )
	{
		$cluster_icon =
		  "&nbsp;&nbsp;<i class=\"fa fa-database action-icon fa-fw\" title=\"The cluster service interface has to be changed or disabled before to be able to modify this interface\"></i>";
	}

	my $gui_icon = '';
	if ( $$iface{ addr } eq $guiip && $guiip )
	{
		$gui_icon =
		  "&nbsp;&nbsp;<i class=\"fa fa-home action-icon fa-fw\" title=\"The GUI service interface has to be changed before to be able to modify this interface\"></i>";
	}

	# row selection
	my $selected = '';
	if (    ( $action eq "editif" )
		 && ( $$iface{ name } eq $toif )
		 && ( $$iface{ ip_v } ) == $interface{ ip_v } )
	{
		$selected = "class=\"selected\"";
	}

	# Datalink interface
	my ( $non_virtual_if ) = split ( ":", $$iface{ name } );
	my $uplink = &uplinkUsed( $non_virtual_if );
	my $gateway = $$iface{ gateway } // "-";
	$$iface{ addr } = "-" if not $$iface{ addr };
	$$iface{ mask } = "-" if not $$iface{ mask };

	if ( $uplink eq "true" )
	{
		$gateway =
		  "&nbsp;&nbsp;<i class=\"fa fa-lock action-icon fa-fw\" title=\"A datalink farm is locking the gateway of this interface\">";
	}

	# status
	my $status_icon =
	  ( $$iface{ status } eq "up" )
	  ? "src=\"img/icons/small/start.png\" title=\"up\""
	  : "src=\"img/icons/small/stop.png\" title=\"down\"";

	# link
	my $link_icon = '';
	if ( $$iface{ link } eq "off" )
	{
		$link_icon =
		  "&nbsp;&nbsp;<img src=\"img/icons/small/disconnect.png\" title=\"No link\">";
	}

	if ( $$iface{ edit_row } )
	{
		print "<tr $selected>";
		print "<form method=\"post\" action=\"index.cgi\" class=\"myform\">";
		print
		  "<td>$$iface{name}<input type=\"text\" maxlength=\"10\" size=\"10\" name=\"if\" value=\"\"></td>";
		#~ print "<td><center>IPv$$iface{ip_v}</center></td>";
		print "<td><input type=\"text\" name=\"newip\" size=\"14\"></td>";

		print
		  "<input type=\"hidden\" name=\"ipv\" value=\"$$iface{ip_v}\" size=\"14\">";
		print "<input type=\"hidden\" name=\"id\" value=\"3-2\">";
		print "<input type=\"hidden\" name=\"toif\" value=\"$$iface{name}\">";
		print "<input type=\"hidden\" name=\"status\" value=\"$$iface{status}\">";

		print "<td><center>$$iface{mac}</center></td>";

		if ( $action eq "addvip" )
		{
			print "<td><center>$$iface{mask}</center></td>";
			print "<td class=\"aligncenter\">$gateway</td>";
			print
			  "<input type=\"hidden\" name=\"netmask\" value=\"$$iface{mask}\" size=\"14\">";
		}
		elsif ( $action eq "addvlan" )
		{
			print "<td><input type=\"text\" size=\"16\" name=\"netmask\" value=\"\" ></td>";
			print "<td><input type=\"text\" size=\"16\" name=\"gwaddr\" value=\"\" ></td>";
		}

		print "<td class=\"aligncenter\">Adding</td>";
		print "<input type=\"hidden\" name=\"action\" value=\"${action}2\">";
		print "<td>";

		# edit row menu
		if ( $action eq "addvip" )
		{
			print "
			<button type=\"submit\" class=\"myicons\" title=\"save virtual interface\">
				<i class=\"fa fa-floppy-o fa-fw action-icon\"></i>
			</button>
			</form>";
		}
		elsif ( $action eq "addvlan" )
		{
			print "
			<button type=\"submit\" class=\"myicons\" title=\"save vlan interface\">
				<i class=\"fa fa-floppy-o fa-fw action-icon\"></i>
			</button>
			</form>";
		}

		# cancel edit row
		print "
		<form method=\"post\" action=\"index.cgi\" class=\"myform\">
			<button type=\"submit\" class=\"myicons\" title=\"cancel operation\">
				<i class=\"fa fa-sign-out fa-fw action-icon\"></i>
			</button>
			<input type=\"hidden\" name=\"id\" value=\"$id\">
		</form>";
		print "</td>";
		print "</tr>";
	}
	else
	{
		print "<tr $selected>";
		print "<td>$$iface{name} $cluster_icon $gui_icon</td>";
		#~ print "<td><center>IPv$$iface{ip_v}</center></td>";
		print "<td><center>$$iface{addr}</center></td>";
		print "<td><center>$$iface{mac}</center></td>";
		print "<td><center>$$iface{mask}</center></td>";
		print "<td class=\"aligncenter\">$gateway</td>";
		print "<td class=\"aligncenter\"><img $status_icon>$link_icon</td>";
		&createmenuif( $iface, $id );    # $iface is a reference here
	}

	print "</tr>";
}

print "</tbody>";
print "</table>";
print "</div></div>";

#### Default GW section

print "
               <div class=\"box grid_12\">
                 <div class=\"box-head\">
                       <span class=\"box-icon-24 fugue-24 home\"></span>         
                       <h2>Default gateway</h2>
                 </div>
                 <div class=\"box-content no-pad\">
";

my %available_interfaces;

if ( $action =~ /editgw/ )
{
	for my $iface ( @interfaces )
	{
		my $flags = $socket->if_flags( $$iface{ name } );

		if ( ( $$iface{ name } !~ /^lo|sit|.*\:.*/ ) && ( $flags & IFF_RUNNING ) )
		{
			$available_interfaces{ $$iface{ name } } = "";
		}
	}
}

print "<table class=\"display\">";
print "<thead>";
print "<tr>";
print "<th>Addr</th>";
print "<th>Interface</th>";
#~ print "<th>IPv</th>";
print "<th>Actions</th>";
print "</tr>";
print "</thead>";
print "<tbody>";

# IPv4 default gateway
if ( $action =~ /editgw4/ )
{
	print
	  "<form name=\"gatewayform\" method=\"post\" action=\"index.cgi\" class=\"myform\">";

	print "<tr class=\"selected\"><td>";
	print "<input type=\"text\" size=\"14\" name=\"gwaddr\" value=\"";
	print &getDefaultGW();
	print "\">";
	print "</td><td>";
	print "<select name=\"if\">";

	my $gw = &getIfDefaultGW();
	if ( $gw )
	{
		$available_interfaces{ $gw } = 'selected';
	}
	else
	{
		my ( $first_if ) = sort keys %available_interfaces;
		$available_interfaces{ $first_if } = 'selected';
	}

	for my $if ( sort keys %available_interfaces )
	{
		print "<option value=\"$if\" $available_interfaces{$if}>$if</option>";
	}

	print "</select>";
	#~ print "</td><td>";
	#~ print "IPv4";
}
else
{
	print "<tr><td>";
	print &getDefaultGW();
	print "</td><td>";
	print &getIfDefaultGW();
	#~ print "</td><td>";
	#~ print "IPv4";
}
print "</td><td>";
&createmenuGW( $id, $action, 4 );
print "</td></tr>";

#~ # IPv6 default gateway
#~ if ( $action =~ /editgw6/ )
#~ {
	#~ print
	  #~ "<form name=\"gatewayform\" method=\"post\" action=\"index.cgi\" class=\"myform\">";
	#~ print "<tr class=\"selected\"><td>";
	#~ print "<input type=\"text\" size=\"14\" name=\"gwaddr\" value=\"";
	#~ print &getIPv6DefaultGW();
	#~ print "\">";
	#~ print "</td><td>";
	#~ print "<select name=\"if\">";
#~ 
	#~ my $gw = &getIPv6IfDefaultGW();
	#~ if ( $gw )
	#~ {
		#~ $available_interfaces{ $gw } = 'selected';
	#~ }
	#~ else
	#~ {
		#~ my ( $first_if ) = sort keys %available_interfaces;
		#~ $available_interfaces{ $first_if } = 'selected';
	#~ }
#~ 
	#~ for my $if ( sort keys %available_interfaces )
	#~ {
		#~ print "<option value=\"$if\" $available_interfaces{$if}>$if</option>";
	#~ }
#~ 
	#~ print "</select>";
	#~ print "</td><td>";
	#~ print "IPv6";
#~ }
#~ else
#~ {
	#~ print "<tr><td>";
	#~ print &getIPv6DefaultGW();
	#~ print "</td><td>";
	#~ print &getIPv6IfDefaultGW();
	#~ print "</td><td>";
	#~ print "IPv6";
#~ }
#~ print "</td><td>";
#~ &createmenuGW( $id, $action, 6 );
#~ print "</td></tr>";

print "</tbody>";
print "</table>";
print "</div></div>";

print "
<script>
\$(document).ready(function() {
    \$('#interfaces-table').DataTable( {
        \"bJQueryUI\": true,     
        \"sPaginationType\": \"full_numbers\",
		\"aLengthMenu\": [
			[10, 25, 50, 100, 200, -1],
			[10, 25, 50, 100, 200, \"All\"]
		],
		\"iDisplayLength\": 25
    });
} );
</script>
";

1;
