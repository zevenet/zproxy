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

#get ip GUI
sub GUIip    # ()
{
	open FO, "<$confhttp";
	@file  = <FO>;
	$guiip = @file[0];
	@guiip = split ( "=", $guiip );
	chomp ( @guiip );
	@guiip[1] =~ s/\ //g;
	return @guiip[1];

}

#function that read the https port for GUI
sub getGuiPort    # ($minihttpdconf)
{
	( $minihttpdconf ) = @_;
	open FR, "<$minihttpdconf";
	@minihttpdconffile = <FR>;
	my @guiportline = split ( "=", @minihttpdconffile[1] );
	close FR;
	return @guiportline[1];
}

#function that write the https port for GUI
sub setGuiPort    # ($httpsguiport,$minihttpdconf)
{
	( $httpsguiport, $minihttpdconf ) = @_;
	$httpsguiport =~ s/\ //g;
	use Tie::File;
	tie @array, 'Tie::File', "$minihttpdconf";
	@array[1] = "port=$httpsguiport\n";
	untie @array;
}

#function that create the menu for delete, move a service in a http[s] farm
sub createmenuservice    # ($fname,$sv,$pos)
{
	my ( $fname, $sv, $pos ) = @_;

	my $serv20        = $sv;
	my $serv          = $sv;
	my $farm_filename = &getFarmFile( $fname );

	use Tie::File;
	tie @array, 'Tie::File', "$configdir/$farm_filename";
	my @output = grep { /Service/ } @array;
	untie @array;

	$serv20 =~ s/\ /%20/g;
	print
	  "<a href=index.cgi?id=1-2&action=editfarm-deleteservice&service=$serv20&farmname=$farmname><img src=\"img/icons/small/cross_octagon.png \" title=\"Delete service $svice\" onclick=\"return confirm('Are you sure you want to delete the Service $serv?')\" ></a> ";

}

#Refresh stats
sub refreshstats    # ()
{
	print "<form method=\"get\" action=\"index.cgi\">";
	print
	  "<b>Refresh stats every</b><input type=\"hidden\" name=\"id\" value=\"$id\">";
	print "<select name=\"refresh\" onchange=\"this.form.submit()\">";
	print "<option value=\"Disabled\"> - </option>\n";
	if ( $refresh eq "10" )
	{
		print "<option value=\"10\" selected>10</option>\n";
	}
	else
	{
		print "<option value=\"10\">10</option>\n";
	}
	if ( $refresh eq "30" )
	{
		print "<option value=\"30\" selected>30</option>\n";
	}
	else
	{
		print "<option value=\"30\">30</option>\n";
	}
	if ( $refresh eq "60" )
	{
		print "<option value=\"60\" selected>60</option>\n";
	}
	else
	{
		print "<option value=\"60\">60</option>\n";
	}
	if ( $refresh eq "120" )
	{
		print "<option value=\"120\" selected>120</option>\n";
	}
	else
	{
		print "<option value=\"120\">120</option>\n";
	}

	print
	  "</select> <b>secs</b>, <font size=1>It can overload the zen server</font>";

	print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
	print
	  "<input type=\"hidden\" name=\"viewtableclients\" value=\"$viewtableclients\">";
	print "<input type=\"hidden\" name=\"viewtableconn\" value=\"$viewtableconn\">";
	print
	  "<input type=\"hidden\" value=\"managefarm\" name=\"action\" class=\"button small\">";

#print "<input type=\"submit\" value=\"Submit\" name=\"button\" class=\"button small\">";
	print "</form>";
}

#Create menu for Actions in Conns stats
sub createmenuvipstats($name,$id,$status,$type)
{
	my ( $name, $id, $status, $type ) = @_;

	print "<a href=\"index.cgi?id=2-1&action=$name-farm\" \">";
	print "<img "
	  . "src=\"img/icons/small/chart_bar.png\" "
	  . "title=\"Show connection graphs for Farm $name\">";
	print "</a> ";

	if ( $status eq "up" && $type ne "gslb" )
	{
		print "<a href=\"index.cgi?id=1-2&action=managefarm&farmname=$name\">";
		print "<img "
		  . "src=\"img/icons/small/connect.png\" "
		  . "title=\"View $name backends status\">";
		print "</a> ";
	}
}

#function that create the menu for manage the vips in Farm Table
sub createmenuvip($name,$id,$status)
{
	my ( $name, $id, $status ) = @_;

	if ( $status eq "up" )
	{
		print "<a "
		  . "href=\"index.cgi?id=$id&action=stopfarm&farmname=$name\" "
		  . "onclick=\"return confirm('Are you sure you want to stop the farm: $name?')\">";

		print
		  "<img src=\"img/icons/small/farm_delete.png\" title=\"Stop the $name Farm\">";
		print "</a> ";

		print "<a href=\"index.cgi?id=$id&action=editfarm&farmname=$name\">";
		print
		  "<img src=\"img/icons/small/farm_edit.png\" title=\"Edit the $name Farm\">";
		print "</a> ";
	}
	else
	{
		print "<a href=\"index.cgi?id=$id&action=startfarm&farmname=$name\">";
		print
		  "<img src=\"img/icons/small/farm_up.png\" title=\"Start the $name Farm\">";
		print "</a> ";
	}
	print "<a "
	  . "href=\"index.cgi?id=$id&action=deletefarm&farmname=$name\" "
	  . "onclick=\"return confirm('Are you sure you wish to delete the farm: $name?')\">";
	print
	  "<img src=\"img/icons/small/farm_cancel.png\" title=\"Delete the $name Farm\">";
	print "</a> ";
}

#
sub createmenuGW($id,$action)
{
	my ( $id, $action ) = @_;

	if ( $action =~ /editgw/ )
	{
		print "<input " . "type=\"hidden\" " . "name=\"action\" " . "value=\"editgw\">";
		print "<input "
		  . "type=\"image\" "
		  . "src=\"img/icons/small/disk.png\" "
		  . "onclick=\"submit();\" "
		  . "name=\"action\" "
		  . "type=\"submit\" "
		  . "value=\"editgw\" "
		  . "title=\"save "
		  . "default gw\">";

		print "<a href=\"index.cgi?id=$id\">";
		print "<img src=\"img/icons/small/arrow_left.png\" title=\"cancel operation\">";
		print "</a> ";
	}
	else
	{
		print "<a href=\"index.cgi?id=$id&action=editgw\">";
		print "<img "
		  . "src=\"img/icons/small/pencil.png\" "
		  . "title=\"edit "
		  . "default GW\"/>";
		print "</a>";
		print "&nbsp";
		print "<a "
		  . "href=\"index.cgi?id=$id&action=deletegw\" "
		  . "onclick=\"return confirm('Are you sure you wish to delete the default gateway?')\">";
		print "<img "
		  . "src=\"img/icons/small/delete.png\" "
		  . "title=\"delete default GW\"/>";
		print "</a> ";
	}
}

#function create menu for interfaces in id 3-2
sub createmenuif($if, $id, $configured, $state)
{
	my ( $if, $id, $configured, $state ) = @_;

	use IO::Socket;
	use IO::Interface qw(:flags);

	my $s = IO::Socket::INET->new( Proto => 'udp' );
	my @interfaces = $s->if_list;

	$clrip = &getClusterRealIp();
	$guiip = &GUIip();
	$clvip = &getClusterVirtualIp();

	print "<td>";
	$ip     = $s->if_addr( $if );
	$source = "";
	$locked = "false";

	if ( -e $filecluster )
	{
		open FC, "<$filecluster";
		@filecl = <FC>;
		if ( grep ( /$ip/, @filecl ) && $ip !~ /^$/ )
		{
			$locked = "true";
		}
		if ( grep ( /$if$/, @filecl ) )
		{
			$locked = "true";
		}
	}
	if ( $ip !~ /^$/ && ( ( $ip eq $clrip ) || ( $ip eq $guiip ) ) )
	{
		$locked = "true";
	}

	if ( ( $status eq "up" ) && ( $ip ne $clrip ) && ( $ip ne $guiip ) )
	{
		if ( $locked eq "false" )
		{
			print "<a "
			  . "href=\"index.cgi?id=$id&action=downif&if=$if\" "
			  . "onclick=\"return confirm('Are you sure you wish to shutdown the interface: $if?')\">";

			print "<img "
			  . "src=\"img/icons/small/plugin_stop.png\" "
			  . "title=\"down network interface\">";

			print "</a> ";
			$source = "system";
		}
	}
	else
	{
		if ( $status eq "down" )
		{
			if ( $locked eq "false" )
			{
				print "<a href=\"index.cgi?id=$id&action=upif&if=$if\">";
				print
				  "<img src=\"img/icons/small/plugin_upn.png\" title=\"up network interface\">";
				print "</a> ";
				$source = "files";
			}
		}
	}

	if ( ( ( $ip ne $clrip ) && ( $ip ne $guiip ) ) || !$ip )
	{
		if ( $locked eq "false" )
		{
			print
			  "<a href=\"index.cgi?id=$id&action=editif&if=$if&toif=$if&source=$source&status=$status\">";
			print
			  "<img src=\"img/icons/small/plugin_edit.png\" title=\"edit network interface\">";
			print "</a> ";
		}
	}

	if ( $if =~ /\:/ )
	{
		#virtual interface
		if ( $locked eq "false" )
		{
			print
			  "<a href=\"index.cgi?id=$id&action=deleteif&if=$if\" onclick=\"return confirm('Are you sure you wish to delete the virtual interface: $if?')\">";
			print
			  "<img src=\"img/icons/small/plugin_delete.png\" title=\"delete network interface\">";
			print "</a> ";
		}
	}
	else
	{
		# Physical interface
		if ( $if =~ /\./ )
		{
			if ( $locked eq "false" )
			{
				print
				  "<a href=\"index.cgi?id=$id&action=addvip&toif=$if\"><img src=\"img/icons/small/pluginv_add.png\" title=\"add virtual network interface\"></a> ";
				print
				  "<a href=\"index.cgi?id=$id&action=deleteif&if=$if\" onclick=\"return confirm('Are you sure you wish to delete the physical interface: $if?')\"><img src=\"img/icons/small/plugin_delete.png\" title=\"delete network interface\"></a> ";
			}
		}
		else
		{
			print
			  "<a href=\"index.cgi?id=$id&action=addvip&toif=$if\"><img src=\"img/icons/small/pluginv_add.png\" title=\"add virtual network interface\"></a> ";
			print
			  "<a href=\"index.cgi?id=$id&action=addvlan&toif=$if\"><img src=\"img/icons/small/plugin_add.png\" title=\"add vlan network interface\"></a> ";
			if ( $locked eq "false" )
			{
				print
				  "<a href=\"index.cgi?id=$id&action=deleteif&if=$if\" onclick=\"return confirm('Are you sure you wish to delete the physical interface: $if?')\"><img src=\"img/icons/small/plugin_delete.png\" title=\"delete network interface\"></a> ";
			}
		}
	}

	if ( $locked eq "true" )
	{
		print "&nbsp&nbsp&nbsp&nbsp";
		print
		  "<img src=\"img/icons/small/lock.png\" title=\"some actions are locked\">";
	}

	print "</td>";
}

#function that create a menu for certificates actions
sub createMenuFarmCert($fname,$cname)
{
	my ( $fname, $cname ) = @_;

	print "<input type=\"hidden\" name=\"action\" value=\"changecert\">";
	print "<input "
	  . "type=\"image\" "
	  . "src=\"img/icons/small/accept2.png\" "
	  . "title=\"Change Certificate $certname on farm $farmane\" "
	  . "name=\"action\" "
	  . "value=\"changecert\"> ";
}

#function that create a menu for backup actions
sub createmenubackup($file)
{
	my ( $file ) = @_;

	print "<a href=\"index.cgi?id=$id&action=apply&file=$file\">";
	print
	  "<img src=\"img/icons/small/accept2.png\"  title=\"Apply $file backup and restart Zen Load Balancer service\">";
	print "</a>";

	print "<a href=\"downloads.cgi?filename=$file\">";
	print
	  "<img src=\"img/icons/small/arrow_down.png\"  title=\"Download $file backup\">";
	print "</a>";

	print
	  "<a href=\"index.cgi?id=$id&action=del&file=$file\" onclick=\"return confirm('Are you sure you wish to delete this backup?')\">";
	print
	  "<img src=\"img/icons/small/cross_octagon.png\" title=\"Delete $file backup\">";
	print "</a>";
}

#function that create a menu where you can enable/disable the server backend in a farm.
sub createmenubackactions($id_server)
{
	my ( $id_server ) = @_;

	print
	  "<input type=\"image\" src=\"img/icons/small/server_edit.png\" title=\"Edit Real Server $id_server\" name=\"action\" value=\"editfarm-editserver\"> ";
	print
	  "<input type=\"image\" src=\"img/icons/small/server_edit.png\" title=\"Edit Real Server $id_server\" name=\"action\" value=\"editfarm-editserver\"> ";
}

#function that create a menu for configure servers in a farm
sub createmenuserversfarm($action,$name,$id_server)
{
	my ( $actionmenu, $name, $id_server ) = @_;
	my $type = &getFarmType( $name );

	print "<td>";
	if ( $actionmenu eq "normal" )
	{
		print "<input type=\"hidden\" name=\"action\" value=\"editfarm-editserver\">";
		print
		  "<input type=\"image\" src=\"img/icons/small/server_edit.png\" title=\"Edit Real Server $id_server\" name=\"action\" value=\"editfarm-editserver\">";

		my $maintenance = &getFarmBackendMaintenance( $name, $id_server, $sv );
		if ( $type ne "datalink" && $type ne "l4xnat" && $type ne "gslb" )
		{
			if ( $maintenance ne "0" )
			{
				print
				  "<a href=index.cgi?action=editfarm-maintenance&id=1-2&farmname=$name&id_server=$id_server&service=$sv "
				  . "title=\"Enable  maintenance mode for real Server $id_server $sv\" "
				  . "onclick=\"return confirm('Are you sure you want to enable the  maintenance mode for server: $id_server $sv?')\">";
				print "<img src=\"img/icons/small/server_maintenance.png\">";
				print "</a>";
			}
			else
			{
				print
				  "<a href=index.cgi?action=editfarm-nomaintenance&id=1-2&farmname=$name&id_server=$id_server&service=$sv "
				  . "title=\"Disable maintenance mode for real Server $id_server $sv\" "
				  . "onclick=\"return confirm('Are you sure you want to disable the maintenance mode for server: $id_server $sv?')\">";
				print "<img src=\"img/icons/small/server_ok.png\">";
				print "</a>";
			}
		}

		my $sv20 = $sv;
		$sv20 =~ s/\ /%20/g;

		if ( $type eq "gslb" )
		{
			if ( $id_server ne "primary" && $id_server ne "secondary" )
			{
				print
				  "<a href=index.cgi?action=editfarm-deleteserver&id=1-2&farmname=$name&id_server=$id_server&service=$sv20&service_type=$service_type "
				  . "title=\"Delete Real Server $id_server\" "
				  . "onclick=\"return confirm('Are you sure you want to delete the server: $id_server?')\">";
				print "<img src=\"img/icons/small/server_delete.png\">";
				print "</a>";
			}
		}
		else
		{
			print
			  "<a href=index.cgi?action=editfarm-deleteserver&id=1-2&farmname=$name&id_server=$id_server&service=$sv20 "
			  . "title=\"Delete Real Server $id_server\" "
			  . "onclick=\"return confirm('Are you sure you want to delete the server: $id_server?')\">";
			print "<img src=\"img/icons/small/server_delete.png\">";
			print "</a>";
		}
	}

	if ( $actionmenu eq "add" )
	{
		print "<input type=\"hidden\" name=\"action\" value=\"editfarm-saveserver\">";
		print "<input "
		  . "type=\"image\" "
		  . "src=\"img/icons/small/server_save.png\" "
		  . "title=\"Save Real Server $id_server\" "
		  . "name=\"action\" value=\"editfarm-saveserver\">";

		print "<a href=\"index.cgi?id=1-2&action=editfarm&farmname=$farmname\">";
		print "<img src=\"img/icons/small/server_out.png\">";
		print "</a>";
	}

	if ( $actionmenu eq "new" )
	{
		print "<input type=\"hidden\" name=\"action\" value=\"editfarm-addserver\">";
		print "<input "
		  . "type=\"image\" "
		  . "src=\"img/icons/small/server_add.png\" "
		  . "title=\"Add Real Server\" "
		  . "name=\"action\" "
		  . "value=\"editfarm-addserver\"> ";
	}

	if ( $actionmenu eq "edit" )
	{
		print "<input type=\"hidden\" name=\"action\" value=\"editfarm-saveserver\">";
		print "<input "
		  . "type=\"image\" src=\"img/icons/small/server_save.png\" "
		  . "title=\"Save Real Server $id_server\" "
		  . "name=\"action\" value=\"editfarm-saveserver\"> ";

		print "<a href=\"index.cgi?id=1-2&action=editfarm&farmname=$farmname\">";
		print "<img src=\"img/icons/small/server_out.png\">";
		print "</a>";
	}

	print "</td>";
}

#function that print a OK message
sub successmsg($string)
{
	my ( $string ) = @_;

	print "<div class=\"notification success\">";
	print "<span class=\"strong\">SUCCESS!</span>";
	print " $string.";
	print "</div>";
	&logfile( $string );
}

#function that print a TIP message
sub tipmsg($string)
{
	my ( $string ) = @_;

	print "<div class=\"notification tip\">";
	print "<span class=\"strong\">TIP!</span>";
	print " $string. Restart HERE! ";
	print "<a href='index.cgi?id=$id&farmname=$farmname&action=editfarm-restart'>";
	print "<img src='img/icons/small/arrow_refresh.png' title='restart'>";
	print "</a>";
	print "</div>";
	&logfile( $string );
}

#function that print a WARNING message
sub warnmsg($string)
{
	my ( $string ) = @_;

	print "<div class=\"notification warning\">";
	print "<span class=\"strong\">WARNING!</span>";
	print " $string.";
	print "</div>";

	&logfile( $string );
}

#function that print a ERROR message
sub errormsg($string)
{
	my ( $string ) = @_;

	print "<div class=\"notification error\">";
	print "<span class=\"strong\">ERROR!</span>";
	print " $string.";
	print "</div>";

	&logfile( $string );
}

#function that create the menu for manage the vips in HTTP Farm Table
sub createmenuviph    # ($name,$pid,$fproto)
{
	( $name, $id, $farmprotocol ) = @_;

	if ( $pid =~ /^[1-9]/ )
	{
		print
		  "<a href=\"index.cgi?id=$id&action=stopfarm&farmname=$name\" onclick=\"return confirm('Are you sure you want to stop the farm: $name?')\"><img src=\"img/icons/small/farm_delete.png\" title=\"Stop the $name Farm\"></a> ";
		print
		  "<a href=\"index.cgi?id=$id&action=editfarm&farmname=$name\"><img src=\"img/icons/small/farm_edit.png\" title=\"Edit the $name Farm\"></a> ";
	}
	else
	{
		print
		  "<a href=\"index.cgi?id=$id&action=startfarm&farmname=$name\"><img src=\"img/icons/small/farm_up.png\" title=\"Start the $name Farm\"></a> ";
	}
	print
	  "<a href=\"index.cgi?id=$id&action=deletefarm&farmname=$name\"><img src=\"img/icons/small/farm_cancel.png\" title=\"Delete the $name Farm\" onclick=\"return confirm('Are you sure you want to delete the farm: $name?')\"></a> ";

}

#
#no remove this
1
