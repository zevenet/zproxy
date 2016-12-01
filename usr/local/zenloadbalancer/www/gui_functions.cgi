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

#~ use strict;
#~ use warnings;

=begin nd
	Function: GUIip

	returns the GUI service ip address

	Parameters: none

	Returns:

		scalar - GUI ip address or '*' for all local addresses

=cut
sub GUIip    # ()
{
	my $gui_ip;    # output

	open my $fh, "<", "$confhttp";

	# read line matching 'server!bind!1!interface = <IP>'
	my $config_item = 'server!bind!1!interface';

	while ( my $line = <$fh> )
	{
		if ( $line =~ /$config_item/ )
		{
			( undef, $gui_ip ) = split ( "=", $line );
			last;
		}
	}

	close $fh;

	chomp ( $gui_ip );
	$gui_ip =~ s/\s//g;

	if ( &ipisok($gui_ip,4) ne "true" )
	{
		$gui_ip = "*";
	}

	return $gui_ip;
}

#function that read the https port for GUI
sub getGuiPort    # ()
{
	my $gui_port;    # output

	open my $fh, "<", "$confhttp";

	# read line matching 'server!bind!1!port = <PORT>'
	my $config_item = 'server!bind!1!port';

	while ( my $line = <$fh> )
	{
		if ( $line =~ /$config_item/ )
		{
			( undef, $gui_port ) = split ( "=", $line );
			last;
		}
	}

	#~ my @httpdconffile = <$fr>;
	close $fh;

	chomp ( $gui_port );
	$gui_port =~ s/\s//g;

	return $gui_port;
}

#function that write the https port for GUI
sub setGuiPort    # ($httpsguiport)
{
	my ( $httpsguiport ) = @_;

	$httpsguiport =~ s/\ //g;

	use Tie::File;
	tie my @array, 'Tie::File', "$confhttp";

	@array[2] = "server!bind!1!port = $httpsguiport\n";

	untie @array;
}

#function that create the menu for delete, move a service in a http[s] farm
sub createmenuservice    # ($fname,$sv,$pos)
{
	my ( $fname, $sv, $pos ) = @_;

	my $serv20   = $sv;
	my $serv     = $sv;
	my $filefarm = &getFarmFile( $fname );

	use Tie::File;
	tie @array, 'Tie::File', "$configdir/$filefarm";
	my @output = grep { /Service/ } @array;
	untie @array;

	$serv20 =~ s/\ /%20/g;

	print "
		<form method=\"post\" action=\"index.cgi\" class=\"myform\">
		<button type=\"submit\" class=\"myicons\" title=\"Delete service $serv\" onclick=\"return confirm('Are you sure you want to delete the Service $serv?')\">
			<span class=\"icon-24 fugue-24 cross-circle\"></span>
		</button>
		<input type=\"hidden\" name=\"id\" value=\"1-2\">
		<input type=\"hidden\" name=\"action\" value=\"editfarm-deleteservice\">
		<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">
		<input type=\"hidden\" name=\"service\" value=\"$serv20\">
		</form>";
}

#Refresh stats
sub refreshstats    # ()
{
	print "<form id=\"refresh_form\" method=\"post\" action=\"index.cgi\">";
	print "<p class=\"grid_12\">";
	print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
	print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
	print
	  "<input type=\"hidden\" name=\"viewtableclients\" value=\"$viewtableclients\">";
	print "<input type=\"hidden\" name=\"viewtableconn\" value=\"$viewtableconn\">";
	print
	  "<input type=\"hidden\" value=\"managefarm\" name=\"action\" class=\"button small\">";
	print "Refresh stats every: ";

	print
	  "<select id=\"farm-stats-autorefresh\" name=\"refresh\" onchange=\"javascript:jQuery('#refresh_form').submit();\">";
	print "<option value=\"Disabled\"> - </option>\n";

	( $refresh eq "10" )
	  ? print "<option value=\"10\" selected>10 seconds</option>\n"
	  : print "<option value=\"10\">10 seconds</option>\n";

	( $refresh eq "30" )
	  ? print "<option value=\"30\" selected>30 seconds</option>\n"
	  : print "<option value=\"30\">30 seconds</option>\n";

	( $refresh eq "60" )
	  ? print "<option value=\"60\" selected>60 seconds</option>\n"
	  : print "<option value=\"60\">60 seconds</option>\n";

	( $refresh eq "120" )
	  ? print "<option value=\"120\" selected>120 seconds</option>\n"
	  : print "<option value=\"120\">120 seconds</option>\n";

	print "</select> NOTE: It can overload the server.</p>";

	print "</form>";
	print "<div class=\"onlyclear\">&nbsp;</div>";

	print "
		<script type=\"text/javascript\">
		  jQuery(document).ready(function () {
			if (\$(\"#farm-stats-autorefresh\").val() != \"Disabled\") {
			  setTimeout(startRefresh, \$(\"#farm-stats-autorefresh\").val() * 1000);
			}
			function startRefresh() {  jQuery(\"#refresh_form\").submit(); }
		  });
		</script>
	";
}

#Create menu for Actions in Conns stats
sub createmenuvipstats    # ($name,$id,$status,$type)
{
	my ( $name, $id, $status, $type ) = @_;

	if ( $type eq "datalink" )
	{
		print "
		<form method=\"post\" action=\"index.cgi\" class=\"myform\">
		<button type=\"submit\" class=\"myicons\" title=\"Show interface graph for Farm $name\">
			<i class=\"fa fa-bar-chart action-icon fa-fw gray\"></i>
		</button>
		<input type=\"hidden\" name=\"id\" value=\"2-1\">
		<input type=\"hidden\" name=\"action\" value=\"${id}iface\">
		</form>";
	}
	else
	{
		print "
		<form method=\"post\" action=\"index.cgi\" class=\"myform\">
			<button type=\"submit\" class=\"myicons\" title=\"Show connection graph for Farm $name\">
				<i class=\"fa fa-bar-chart action-icon fa-fw gray\"></i>
			</button>
			<input type=\"hidden\" name=\"id\" value=\"2-1\">
			<input type=\"hidden\" name=\"action\" value=\"$name-farm\">
		</form>";
	}

	if ( $status eq "up" )
	{
		print "
		<form method=\"post\" action=\"index.cgi\" class=\"myform\">
		<button type=\"submit\" class=\"myicons\"  title=\"Show global status for $name\">
			<i class=\"fa fa-line-chart action-icon fa-fw\"></i>
		</button>
		<input type=\"hidden\" name=\"id\" value=\"1-2\">
		<input type=\"hidden\" name=\"action\" value=\"managefarm\">
		<input type=\"hidden\" name=\"farmname\" value=\"$name\">
		</form>";
	}
}

#
sub createmenuGW    # ($id,$action,$ipversion)
{
	my ( $id, $action, $ipversion ) = @_;

	# editing menu
	if ( $action =~ /editgw$ipversion/ )
	{
		# Save GW (the beginning of form is in corresponding content)
		print "
		<button type=\"submit\" class=\"myicons\" title=\"Save default GW\">
			<i class=\"fa fa-floppy-o fa-fw action-icon\"></i>
		</button>
		<input type=\"hidden\" name=\"id\" value=\"$id\">
		<input type=\"hidden\" name=\"action\" value=\"editgw$ipversion\">
		</form>";

		#Cancel
		print "
		<form method=\"post\" action=\"index.cgi\" class=\"myform\">
		<button type=\"submit\" class=\"myicons\" title=\"Cancel\">
			<i class=\"fa fa-sign-out fa-fw action-icon\"></i>
		</button>
		<input type=\"hidden\" name=\"id\" value=\"$id\">
		</form>";
	}
	else
	{    # viewing menu
		    # edit
		print "
		<form method=\"post\" action=\"index.cgi\" class=\"myform\">
		<button type=\"submit\" class=\"myicons\" title=\"Edit default GW\">
			<i class=\"fa fa-pencil-square-o action-icon fa-fw\"></i>
		</button>
		<input type=\"hidden\" name=\"id\" value=\"$id\">
		<input type=\"hidden\" name=\"action\" value=\"editgw$ipversion\">
		</form>";

		# delete
		print "
		<form method=\"post\" action=\"index.cgi\" class=\"myform\">
		<button type=\"submit\" class=\"myicons\" title=\"Delete\" onclick=\"return confirm('Are you sure you wish to delete the default gateway?')\">
			<i class=\"fa fa-times-circle action-icon fa-fw red\"></i>
		</button>
		<input type=\"hidden\" name=\"id\" value=\"$id\">
		<input type=\"hidden\" name=\"action\" value=\"deletegw$ipversion\">
		</form>";
	}
}

#function create menu for interfaces in id 3-2
sub createmenuif    # ($if_ref, $id)
{
	my ( $if_ref, $id ) = @_;

	use IO::Socket;
	use IO::Interface qw(:flags);

	my $socket = IO::Socket::INET->new( Proto => 'udp' );
	my @interfaces = $socket->if_list;

	my $guiip      = &GUIip();
	my $mgmt_iface = getInterfaceOfIp( $guiip ) if $guiip;
	my $clrip      = &getClusterRealIp();
	my $clvip      = &getClusterVirtualIp();

	#~ my $source = "";
	my $locked;

	if ( -e $filecluster )
	{
		open my $fc, "<", "$filecluster";
		my @filecl = <$fc>;
		close $fc;

		#~ &zenlog("\n @filecl");
		if ( &ipisok( $$if_ref{ addr } ) eq 'true'
			 && grep ( /$$if_ref{addr}/, @filecl ) )
		{
			$locked = "true";
		}

		if ( grep ( /$$if_ref{name}$/, @filecl ) )
		{
			$locked = "true";
		}
	}

  #~ if ( ($$iface{addr} eq $clrip || $$iface{addr} eq $clvip) && $clrip && $clvip )
	if (
		 $$if_ref{ addr }
		 && (    ( $$if_ref{ addr } eq $clrip )
			  || ( $$if_ref{ addr } eq $guiip ) )
	  )
	{
		$locked = "true";
	}

	print "<td>";

	# lock interfaces used by bonds
	for my $bond ( @{ &getBondList() } )
	{
		if ( grep ( /^$if_ref->{name}$/, @{ $bond->{ slaves } } ) )
		{
			print
			  "<i class=\"fa fa-lock action-icon fa-fw\" title=\"In use by bonding interface $bond->{name}\">";

			print "</td>";
			return;
		}
	}

	# set interface up or down
	if (    ( $$if_ref{ status } eq "up" )
		 && ( $$if_ref{ addr } ne $clrip )
		 && ( $$if_ref{ addr } ne $guiip )
		 && ( $$if_ref{ name } ne $mgmt_iface ) )
	{
		if ( not $locked )
		{
			# link set down
			print "
			<form method=\"post\" action=\"index.cgi\" class=\"myform\">
			<button type=\"submit\" class=\"myicons\" title=\"down network interface\" onclick=\"return confirm('Are you sure you wish to shutdown the interface: $$if_ref{name}?')\">
				<i class=\"fa fa-minus-circle action-icon fa-fw red\"></i>
			</button>
			<input type=\"hidden\" name=\"id\" value=\"$id\">
			<input type=\"hidden\" name=\"action\" value=\"downif\">
			<input type=\"hidden\" name=\"if\" value=\"$$if_ref{name}\">
			<input type=\"hidden\" name=\"ipv\" value=\"$$if_ref{ip_v}\">
			</form>";

			#~ $source = "system";
		}
	}
	elsif ( $$if_ref{ status } eq "down" )
	{
		if ( not $locked )
		{
			# link set up
			print "
			<form method=\"post\" action=\"index.cgi\" class=\"myform\">
			<button type=\"submit\" class=\"myicons\" title=\"up network interface\">
				<i class=\"fa fa-play-circle action-icon fa-fw green\"></i>
			</button>
			<input type=\"hidden\" name=\"id\" value=\"$id\">
			<input type=\"hidden\" name=\"action\" value=\"upif\">
			<input type=\"hidden\" name=\"if\" value=\"$$if_ref{name}\">
			<input type=\"hidden\" name=\"ipv\" value=\"$$if_ref{ip_v}\">
			</form>";

			#~ $source = "files";
		}
	}

  # edit interface
  #~ if ( ($$iface{addr} eq $clrip || $$iface{addr} eq $clvip) && $clrip && $clvip )
	if ( ( ( $$if_ref{ addr } ne $clrip ) && ( $$if_ref{ addr } ne $guiip ) )
		 || !$$if_ref{ addr } )
	{
		if ( not $locked )
		{
			# edit
			print "
				<form method=\"post\" action=\"index.cgi\" class=\"myform\">
				<button type=\"submit\" class=\"myicons\" title=\"edit network interface\">
					<i class=\"fa fa-pencil-square-o action-icon fa-fw\"></i>
				</button>
				<input type=\"hidden\" name=\"id\" value=\"$id\">
				<input type=\"hidden\" name=\"action\" value=\"editif\">
				<input type=\"hidden\" name=\"if\" value=\"$$if_ref{name}\">
				<input type=\"hidden\" name=\"status\" value=\"$$if_ref{status}\">
				<input type=\"hidden\" name=\"toif\" value=\"$$if_ref{name}\">
				<input type=\"hidden\" name=\"ipv\" value=\"$$if_ref{ip_v}\">
				</form>";
		}
	}

	# virtual interface
	if ( $$if_ref{ name } =~ /:/ )
	{
		if ( not $locked )
		{
			print "
				<form method=\"post\" action=\"index.cgi\" class=\"myform\">
				<button type=\"submit\" class=\"myicons\" title=\"delete network interface\" onclick=\"return confirm('Are you sure you wish to delete the virtual interface: $$if_ref{name}?')\">
					<i class=\"fa fa-times-circle fa-fw action-icon red\"></i>
				</button>
				<input type=\"hidden\" name=\"id\" value=\"$id\">
				<input type=\"hidden\" name=\"action\" value=\"deleteif\">
				<input type=\"hidden\" name=\"if\" value=\"$$if_ref{name}\">
				<input type=\"hidden\" name=\"ipv\" value=\"$$if_ref{ip_v}\">
				<input type=\"hidden\" name=\"ip\" value=\"$$if_ref{addr}\">
				<input type=\"hidden\" name=\"netmask\" value=\"$$if_ref{mask}\">
				</form>";
		}
	}
	else
	{
		# vlan interface
		if ( $$if_ref{ name } =~ /\./ )
		{
			if ( not $locked )
			{
				# add virtual ip
				print "
				<form method=\"post\" action=\"index.cgi\" class=\"myform\">
				<button type=\"submit\" class=\"myicons\" title=\"add virtual network interface\">
					<i class=\"fa fa-plus-circle fa-fw action-icon\"></i>
				</button>
				<input type=\"hidden\" name=\"id\" value=\"$id\">
				<input type=\"hidden\" name=\"action\" value=\"addvip\">
				<input type=\"hidden\" name=\"toif\" value=\"$$if_ref{name}\">
				<input type=\"hidden\" name=\"ipv\" value=\"$$if_ref{ip_v}\">
				</form>";

				# delete interface
				print "
				<form method=\"post\" action=\"index.cgi\" class=\"myform\">
				<button type=\"submit\" class=\"myicons\" title=\"delete network interface\" onclick=\"return confirm('Are you sure you wish to delete the physical interface: $$if_ref{name}?')\">
					<i class=\"fa fa-times-circle fa-fw action-icon red\"></i>
				</button>
				<input type=\"hidden\" name=\"id\" value=\"$id\">
				<input type=\"hidden\" name=\"action\" value=\"deleteif\">
				<input type=\"hidden\" name=\"if\" value=\"$$if_ref{name}\">
				<input type=\"hidden\" name=\"ipv\" value=\"$$if_ref{ip_v}\">
				<input type=\"hidden\" name=\"ip\" value=\"$$if_ref{addr}\">
				<input type=\"hidden\" name=\"netmask\" value=\"$$if_ref{mask}\">
				</form>";
			}
		}

		# Physical interface
		else
		{
			# add vini
			print "
				<form method=\"post\" action=\"index.cgi\" class=\"myform\">
				<button type=\"submit\" class=\"myicons\" title=\"add virtual network interface\">
					<i class=\"fa fa-plus-circle fa-fw action-icon\"></i>
				</button>
				<input type=\"hidden\" name=\"id\" value=\"$id\">
				<input type=\"hidden\" name=\"action\" value=\"addvip\">
				<input type=\"hidden\" name=\"toif\" value=\"$$if_ref{name}\">
				<input type=\"hidden\" name=\"ipv\" value=\"$$if_ref{ip_v}\">
				</form>" if &ipisok( $$if_ref{ addr } ) eq 'true';

			# add vlan
			print "
				<form method=\"post\" action=\"index.cgi\" class=\"myform\">
				<button type=\"submit\" class=\"myicons\" title=\"add vlan network interface\">
					<i class=\"fa fa-plus-circle green fa-fw action-icon\"></i>
				</button>
				<input type=\"hidden\" name=\"id\" value=\"$id\">
				<input type=\"hidden\" name=\"action\" value=\"addvlan\">
				<input type=\"hidden\" name=\"toif\" value=\"$$if_ref{name}\">
				<input type=\"hidden\" name=\"ipv\" value=\"$$if_ref{ip_v}\">
				</form>";

			if ( $$if_ref{ addr } ne '-' && not $locked )
			{
				# delete
				print "
				<form method=\"post\" action=\"index.cgi\" class=\"myform\">
				<button type=\"submit\" class=\"myicons\" title=\"delete network interface\" onclick=\"return confirm('Are you sure you wish to delete the physical interface: $$if_ref{name}?')\">
					<i class=\"fa fa-times-circle fa-fw action-icon red\"></i>
				</button>
				<input type=\"hidden\" name=\"id\" value=\"$id\">
				<input type=\"hidden\" name=\"action\" value=\"deleteif\">
				<input type=\"hidden\" name=\"if\" value=\"$$if_ref{name}\">
				<input type=\"hidden\" name=\"ipv\" value=\"$$if_ref{ip_v}\">
				<input type=\"hidden\" name=\"ip\" value=\"$$if_ref{addr}\">
				<input type=\"hidden\" name=\"netmask\" value=\"$$if_ref{mask}\">
				</form>";
			}
		}
	}

	if ( $locked )
	{
		print
		  "<i class=\"fa fa-lock action-icon fa-fw\" title=\"some actions are locked\">";
	}

	print "</td>";
}

#function that create a menu for certificates actions
sub createMenuFarmCert    # ($fname,$cname)
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
sub createmenubackup    # ($file)
{
	my $file = shift;

	# Apply
	print "
		<form method=\"post\" action=\"index.cgi\" class=\"myform\">
		<button type=\"submit\" class=\"myicons\" title=\"Apply $file backup and restart ZEVENET service\">
			<i class=\"fa fa-check-circle action-icon fa-fw green\"></i>
		</button>
		<input type=\"hidden\" name=\"id\" value=\"$id\">
		<input type=\"hidden\" name=\"action\" value=\"apply\">
		<input type=\"hidden\" name=\"file\" value=\"$file\">
		</form>";

	# Download
	print "<a href=\"downloads.cgi?filename=$file\">";
	print
	  "<i class=\"fa fa-download action-icon fa-fw\" title=\"Download $file backup\"></i>";
	print "</a>";

	# Delete
	print "
		<form method=\"post\" action=\"index.cgi\" class=\"myform\">
		<button type=\"submit\" class=\"myicons\" title=\"Delete $file backup\" onclick=\"return confirm('Are you sure you wish to delete this backup?')\">
			<i class=\"fa fa-times-circle action-icon fa-fw red\"></i>
		</button>
		<input type=\"hidden\" name=\"id\" value=\"$id\">
		<input type=\"hidden\" name=\"action\" value=\"del\">
		<input type=\"hidden\" name=\"file\" value=\"$file\">
		</form>";
}

#function that create a menu where you can enable/disable the server backend in a farm.
sub createmenubackactions    # ($id_server)
{
	my $id_server = shift;

	print
	  "<input type=\"image\" src=\"img/icons/small/server_edit.png\" title=\"Edit Real Server $id_server\" name=\"action\" value=\"editfarm-editserver\"> ";
	print
	  "<input type=\"image\" src=\"img/icons/small/server_edit.png\" title=\"Edit Real Server $id_server\" name=\"action\" value=\"editfarm-editserver\"> ";
}

# function that create a menu for configure servers in a farm
sub createmenuserversfarm    # ($actionmenu,$name,$id_server)
{
	my ( $actionmenu, $name, $id_server ) = @_;

	my $type = &getFarmType( $name );

	( $actionmenu eq "new" )
	  ? print "<td class='gray'>"
	  : print "<td>";

	my $sv20 = $sv;
	$sv20 =~ s/\ /%20/g;

	if ( $actionmenu eq "normal" )
	{
		if ( $type eq "http" || $type eq "https" )
		{
			print "
			<form method=\"post\" action=\"index.cgi\#backendlist-$sv\" class=\"myform\">
			<input type=\"hidden\" name=\"service\" value=\"$sv\">";
		}
		elsif ( $type eq "gslb" )
		{
			print "
			<form method=\"post\" action=\"index.cgi\#servicelist-$srv\" class=\"myform\">
			<input type=\"hidden\" name=\"service\" value=\"$srv\">
			<input type=\"hidden\" name=\"service_type\" value=\"service\">
			<input type=\"hidden\" name=\"lb\" value=\"$lb\">";
		}
		else
		{
			print "
			<form method=\"post\" action=\"index.cgi\#backendlist\" class=\"myform\">";
		}

		print "
		<button type=\"submit\" class=\"myicons\" title=\"Edit Real Server $id_server\">
			<i class=\"fa fa-pencil-square-o action-icon fa-fw\"></i>
		</button>";

		print "
		<input type=\"hidden\" name=\"id\" value=\"1-2\">
		<input type=\"hidden\" name=\"action\" value=\"editfarm-editserver\">
		<input type=\"hidden\" name=\"farmname\" value=\"$name\">
		<input type=\"hidden\" name=\"id_server\" value=\"$id_server\">
		</form>";

		my $maintenance = &getFarmBackendMaintenance( $name, $id_server, $sv );
		if ( $type ne "datalink" && $type ne "gslb" )
		{
			if ( $maintenance != 0 )
			{
				print "
				<form method=\"post\" action=\"index.cgi\" class=\"myform\">
				<button type=\"submit\" class=\"myicons\" title=\"Enable maintenance mode for real Server $id_server $sv\" onclick=\"return confirm('Are you sure you want to enable the  maintenance mode for server: $id_server $sv?')\">
					<i class=\"fa fa-minus-circle action-icon fa-fw red\"></i>
				</button>
				<input type=\"hidden\" name=\"id\" value=\"1-2\">
				<input type=\"hidden\" name=\"action\" value=\"editfarm-maintenance\">
				<input type=\"hidden\" name=\"farmname\" value=\"$name\">
				<input type=\"hidden\" name=\"id_server\" value=\"$id_server\">
				<input type=\"hidden\" name=\"service\" value=\"$sv\">
				</form>";
			}
			else
			{
				print "
				<form method=\"post\" action=\"index.cgi\" class=\"myform\">
				<button type=\"submit\" class=\"myicons\" title=\"Disable maintenance mode for real Server $id_server $sv\" onclick=\"return confirm('Are you sure you want to disable the  maintenance mode for server: $id_server $sv?')\">
					<i class=\"fa fa-play-circle action-icon fa-fw green\"></i>
				</button>
				<input type=\"hidden\" name=\"id\" value=\"1-2\">
				<input type=\"hidden\" name=\"action\" value=\"editfarm-nomaintenance\">
				<input type=\"hidden\" name=\"farmname\" value=\"$name\">
				<input type=\"hidden\" name=\"id_server\" value=\"$id_server\">
				<input type=\"hidden\" name=\"service\" value=\"$sv\">
				</form>";
			}
		}

		if ( $type eq "gslb" )
		{
			if ( $id_server ne "primary" && $id_server ne "secondary" )
			{
				print "
				<form method=\"post\" action=\"index.cgi\" class=\"myform\">
				<button type=\"submit\" class=\"myicons\" title=\"Delete Real Server $id_server\" onclick=\"return confirm('Are you sure you want to delete the server: $id_server?')\">
					<i class=\"fa fa-times-circle action-icon fa-fw red\"></i>
				</button>
				<input type=\"hidden\" name=\"id\" value=\"1-2\">
				<input type=\"hidden\" name=\"action\" value=\"editfarm-deleteserver\">
				<input type=\"hidden\" name=\"farmname\" value=\"$name\">
				<input type=\"hidden\" name=\"id_server\" value=\"$id_server\">
				<input type=\"hidden\" name=\"service\" value=\"$sv20\">
				<input type=\"hidden\" name=\"service_type\" value=\"$service_type\">
				</form>";
			}
		}
		else
		{
			print "
				<form method=\"post\" action=\"index.cgi\" class=\"myform\">
				<button type=\"submit\" class=\"myicons\" title=\"Delete Real Server $id_server\" onclick=\"return confirm('Are you sure you want to delete the server: $id_server?')\">
					<i class=\"fa fa-times-circle action-icon fa-fw red\"></i>
				</button>
				<input type=\"hidden\" name=\"id\" value=\"1-2\">
				<input type=\"hidden\" name=\"action\" value=\"editfarm-deleteserver\">
				<input type=\"hidden\" name=\"farmname\" value=\"$name\">
				<input type=\"hidden\" name=\"id_server\" value=\"$id_server\">";

			if ( $type eq "http" || $type eq "https" || $type eq "gslb" )
			{
				print "<input type=\"hidden\" name=\"service\" value=\"$sv20\">";
			}

			print "</form>";
		}
	}

	if ( $actionmenu eq "add" )
	{
		# Save Server (the beginning of form is in corresponding content)
		print "
		<button type=\"submit\" class=\"myicons\" title=\"Save Real Server $id_server\">
			<i class=\"fa fa-floppy-o fa-fw action-icon\"></i>
		</button>
		<input type=\"hidden\" name=\"id\" value=\"1-2\">
		<input type=\"hidden\" name=\"action\" value=\"editfarm-saveserver\">
		<input type=\"hidden\" name=\"farmname\" value=\"$name\">
		<input type=\"hidden\" name=\"id_server\" value=\"$id_server\">
		</form>";

		#Cancel
		print "
		<form method=\"post\" action=\"index.cgi\" class=\"myform\">
		<button type=\"submit\" class=\"myicons\" title=\"Cancel\">
			<i class=\"fa fa-sign-out fa-fw action-icon\"></i>
		</button>
		<input type=\"hidden\" name=\"id\" value=\"1-2\">
		<input type=\"hidden\" name=\"action\" value=\"editfarm\">
		<input type=\"hidden\" name=\"farmname\" value=\"$name\">
		<input type=\"hidden\" name=\"id_server\" value=\"$id_server\">
		</form>";
	}

	if ( $actionmenu eq "new" )
	{
		if ( $type eq "http" || $type eq "https" )
		{
			print "
			<form method=\"post\" action=\"index.cgi\#backendlist-$sv\" class=\"myform\">
			<button type=\"submit\" class=\"myicons\" title=\"Add Real Server\">
				<i class=\"fa fa-plus-circle fa-fw action-icon\"></i>
			</button>
			<input type=\"hidden\" name=\"id\" value=\"1-2\">
			<input type=\"hidden\" name=\"action\" value=\"editfarm-addserver\">
			<input type=\"hidden\" name=\"farmname\" value=\"$name\">
			<input type=\"hidden\" name=\"id_server\" value=\"$id_server\">
			<input type=\"hidden\" name=\"service\" value=\"$sv\">
			</form>";
		}
		elsif ( $type eq "gslb" )
		{
			print "
			<form method=\"post\" action=\"index.cgi\#servicelist-$srv\" class=\"myform\">
			<button type=\"submit\" class=\"myicons\" title=\"Add Real Server\">
				<i class=\"fa fa-plus-circle fa-fw action-icon\"></i>
			</button>
			<input type=\"hidden\" name=\"id\" value=\"1-2\">
			<input type=\"hidden\" name=\"action\" value=\"editfarm-addserver\">
			<input type=\"hidden\" name=\"farmname\" value=\"$name\">
			<input type=\"hidden\" name=\"id_server\" value=\"$id_server\">
			<input type=\"hidden\" name=\"service\" value=\"$srv\">
			<input type=\"hidden\" name=\"service_type\" value=\"service\">
			<input type=\"hidden\" name=\"lb\" value=\"$lb\">
			</form>";
		}
		else
		{
			print "
			<form method=\"post\" action=\"index.cgi\#backendlist\" class=\"myform\">
			<button type=\"submit\" class=\"myicons\" title=\"Add Real Server\">
				<i class=\"fa fa-plus-circle fa-fw action-icon\"></i>
			</button>
			<input type=\"hidden\" name=\"id\" value=\"1-2\">
			<input type=\"hidden\" name=\"action\" value=\"editfarm-addserver\">
			<input type=\"hidden\" name=\"farmname\" value=\"$name\">
			<input type=\"hidden\" name=\"id_server\" value=\"$id_server\">
			</form>";
		}
	}

	if ( $actionmenu eq "edit" )
	{
		# Save Server (the beginning of form is in corresponding content)
		print "
		<button type=\"submit\" class=\"myicons\" title=\"Save Real Server $id_server\">
			<i class=\"fa fa-floppy-o fa-fw action-icon\"></i>
		</button>
		<input type=\"hidden\" name=\"id\" value=\"1-2\">
		<input type=\"hidden\" name=\"action\" value=\"editfarm-saveserver\">
		<input type=\"hidden\" name=\"farmname\" value=\"$name\">
		<input type=\"hidden\" name=\"id_server\" value=\"$id_server\">
		</form>";

		#Cancel
		print "
		<form method=\"post\" action=\"index.cgi#zonelist-sofintel.com\" class=\"myform\">
		<button type=\"submit\" class=\"myicons\" title=\"Cancel\">
			<i class=\"fa fa-sign-out fa-fw action-icon\"></i>
		</button>
		<input type=\"hidden\" name=\"id\" value=\"1-2\">
		<input type=\"hidden\" name=\"action\" value=\"editfarm\">
		<input type=\"hidden\" name=\"farmname\" value=\"$name\">
		<input type=\"hidden\" name=\"id_server\" value=\"$id_server\">
		</form>";
	}

	print "</td>";
}

#function that create a menu for configure zone resources in a gslb farm
sub createmenuserversfarmz    # ($actionmenu,$name,$id_server)
{
	( $actionmenu, $name, $id_server ) = @_;

	my $type = &getFarmType( $farmname );

	( $actionmenu eq "new" )
	  ? print "<td class='gray'>"
	  : print "<td>";

	if ( $actionmenu eq "normal" )
	{
		my $zoneaux = $zone;
		$zoneaux =~ s/\./\_/g;

		print "
		<form method=\"post\" action=\"index.cgi\#zonelist-$zone\" class=\"myform\">
			<input type=\"hidden\" name=\"service\" value=\"$zone\">
			<input type=\"hidden\" name=\"service_type\" value=\"zone\">
			<button type=\"submit\" class=\"myicons\" title=\"Edit Resource $id_server\">
				<i class=\"fa fa-pencil-square-o action-icon fa-fw\"></i>
			</button>
			<input type=\"hidden\" name=\"id\" value=\"1-2\">
			<input type=\"hidden\" name=\"action\" value=\"editfarm-editserver\">
			<input type=\"hidden\" name=\"farmname\" value=\"$name\">
			<input type=\"hidden\" name=\"id_server\" value=\"$id_server\">
		</form>";

		my $sv20 = $sv;
		$sv20 =~ s/\ /%20/g;

		print "
			<form method=\"post\" action=\"index.cgi\" class=\"myform\">
				<button type=\"submit\" class=\"myicons\" title=\"Delete Resource $id_server\" onclick=\"return confirm('Are you sure you want to delete the resource: $id_server?')\">
					<i class=\"fa fa-times-circle action-icon fa-fw red\"></i>
				</button>
				<input type=\"hidden\" name=\"id\" value=\"1-2\">
				<input type=\"hidden\" name=\"action\" value=\"editfarm-deleteserver\">
				<input type=\"hidden\" name=\"farmname\" value=\"$name\">
				<input type=\"hidden\" name=\"id_server\" value=\"$id_server\">
				<input type=\"hidden\" name=\"service\" value=\"$zone\">
				<input type=\"hidden\" name=\"service_type\" value=\"zone\">
			</form>";
	}

	if ( $actionmenu eq "add" )
	{
		my $zoneaux = $zone;
		$zoneaux =~ s/\./\_/g;

		# Save Server (the beginning of form is in corresponding content)
		print "
		<button type=\"submit\" class=\"myicons\" title=\"Save Resource $id_server\">
			<i class=\"fa fa-floppy-o fa-fw action-icon\"></i>
		</button>
		<input type=\"hidden\" name=\"id\" value=\"1-2\">
		<input type=\"hidden\" name=\"action\" value=\"editfarm-saveserver\">
		<input type=\"hidden\" name=\"farmname\" value=\"$name\">
		<input type=\"hidden\" name=\"id_server\" value=\"$id_server\">
		</form>";

		#Cancel
		print "
		<form method=\"post\" action=\"index.cgi\#zonelist-$zone\" class=\"myform\">
		<button type=\"submit\" class=\"myicons\" title=\"Cancel\">
			<i class=\"fa fa-sign-out fa-fw action-icon\"></i>
		</button>
		<input type=\"hidden\" name=\"id\" value=\"1-2\">
		<input type=\"hidden\" name=\"action\" value=\"editfarm\">
		<input type=\"hidden\" name=\"farmname\" value=\"$name\">
		<input type=\"hidden\" name=\"id_server\" value=\"$id_server\">
		</form>";
	}

	if ( $actionmenu eq "new" )
	{
		print "
		<form method=\"post\" action=\"index.cgi\#zonelist-$zone\" class=\"myform\">
			<button type=\"submit\" class=\"myicons\" title=\"Add Resource\">
				<i class=\"fa fa-plus-circle fa-fw action-icon\"></i>
			</button>
			<input type=\"hidden\" name=\"id\" value=\"1-2\">
			<input type=\"hidden\" name=\"action\" value=\"editfarm-addserver\">
			<input type=\"hidden\" name=\"farmname\" value=\"$name\">
			<input type=\"hidden\" name=\"id_server\" value=\"$id_server\">
			<input type=\"hidden\" name=\"service\" value=\"$zone\">
			<input type=\"hidden\" name=\"service_type\" value=\"zone\">
		</form>";
	}

	if ( $actionmenu eq "edit" )
	{
		# Save Server (the beginning of form is in corresponding content)
		print "
		<button type=\"submit\" class=\"myicons\" title=\"Save Resource $id_server\">
			<i class=\"fa fa-floppy-o fa-fw action-icon\"></i>
		</button>
		<input type=\"hidden\" name=\"id\" value=\"1-2\">
		<input type=\"hidden\" name=\"action\" value=\"editfarm-saveserver\">
		<input type=\"hidden\" name=\"farmname\" value=\"$name\">
		<input type=\"hidden\" name=\"id_server\" value=\"$id_server\">
		</form>";

		#Cancel
		print "
		<form method=\"post\" action=\"index.cgi\#zonelist-$zone\" class=\"myform\">
		<button type=\"submit\" class=\"myicons\" title=\"Cancel\">
			<i class=\"fa fa-sign-out fa-fw action-icon\"></i>
		</button>
		<input type=\"hidden\" name=\"id\" value=\"1-2\">
		<input type=\"hidden\" name=\"action\" value=\"editfarm\">
		<input type=\"hidden\" name=\"farmname\" value=\"$name\">
		<input type=\"hidden\" name=\"id_server\" value=\"$id_server\">
		</form>";
	}
}

#function that print a OK message
sub successmsg    # ($string)
{
	my $string = shift;

	print "<div class=\"ad-notif-success grid_12 small-mg\"><p><b>SUCCESS!</b> $string</p></div>";

	&zenlog( $string );
}

#function that print a TIP message
sub tipmsg        # ($string)
{
	my $string = shift;

	print "<div class=\"ad-notif-info grid_12 small-mg ad-notif-restart\"><p><b>TIP!</b> $string</p></div>";

	&zenlog( $string );
}

#function that print a WARNING message
sub warnmsg    # ($string)
{
	my $string = shift;

	print "<div class=\"ad-notif-warn grid_12 small-mg ad-notif-restart\"><p><b>WARNING!</b> $string</p></div>";

	&zenlog( $string );
}

#function that print a ERROR message
sub errormsg    # ($string)
{
	my $string = shift;

	print "<div class=\"ad-notif-error grid_12 small-mg\"><p><b>ERROR!</b> $string</p></div>";

	&zenlog( $string );
}

1;
