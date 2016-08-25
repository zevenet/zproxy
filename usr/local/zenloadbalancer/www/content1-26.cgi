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

### VIEW DATALINK FARM ###

#paint a form to the global configuration

print "
    <div class=\"box container_12 grid_12\">
      <div class=\"box-head\">
           <span class=\"box-icon-24 fugue-24 globe\"></span>    
        <h2>Edit $farmname Farm global parameters</h2>
      </div>
      <div class=\"box-content global-farm\">
";

print "<div class=\"grid_12\">\n";

#
# Change farm's name form
#

print "<div class=\"form-row\">\n";
print "<p class=\"form-label\"><b>Farm's name</b></p>\n";
print "<form method=\"post\" action=\"index.cgi\">\n";
print "<input type=\"hidden\" name=\"action\" value=\"editfarm-Parameters\">\n";
print "<input type=\"hidden\" name=\"id\" value=\"$id\">\n";
print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">\n";
print
  "<div class=\"form-item\"><input type=\"text\" class=\"fixedwidth\" value=\"$farmname\" size=\"25\" name=\"newfarmname\"> \n";
print "</div>\n";
print "</div>\n";

#
# Change ip or port for VIP
#

my $vip   = &getFarmVip( "vip",  $farmname );
my $vport = &getFarmVip( "vipp", $farmname );
print "<div class=\"form-row\">\n";
print
  "<p class=\"form-label\"><b>Farm Virtual IP and Interface.</b> Service will be restarted.</p>";

$clrip = &getZClusterLocalIp();
$guiip = &GUIip();

my @interfaces_available = @{ &getActiveInterfaceList() };

print
  "<div class=\"form-item\"><select name=\"vip\" class=\"fixedwidth monospace\">\n";
print "<option value=\"\">-Select One-</option>\n";
for my $iface ( @interfaces_available )
{
	next if $$iface{ vini } ne '';
	next if $$iface{ addr } eq $clrip;

	my $selected = '';

	if ( $$iface{ addr } eq $vip )
	{
		$selected = "selected=\"selected\"";
	}

	print
	  "<option value=\"$$iface{name} $$iface{addr}\" $selected>$$iface{dev_ip_padded}</option>\n";
}

print "</select> ";
print "</div>\n</div>\n";

#
# Load balance algoritm
#

my $lb = &getFarmAlgorithm( $farmname );
if ( $lb == -1 )
{
	$lb = "weight";
}
my $weight   = "Weight: connection dispatching by weight";
my $priority = "Priority: connections to the highest priority available";

print "<div class=\"form-row\">\n";
print "<p class=\"form-label\"><b>Load Balance Algorithm</b></p>";
print "<div class=\"form-item\"><select name=\"lb\" class=\"fixedwidth\">";
if ( $lb eq "weight" )
{
	print "<option value=\"weight\" selected=\"selected\">$weight</option>";
}
else
{
	print "<option value=\"weight\">$weight</option>";
}
if ( $lb eq "prio" )
{
	print "<option value=\"prio\" selected=\"selected\">$priority</option>";
}
else
{
	print "<option value=\"prio\">$priority</option>";
}
print "</select> ";
print "</div>";
print "</div>\n";
print "</div>\n";

print "<div class=\"clear\"></div>";
print "<br>";
print
  "<input type=\"submit\" value=\"Modify\" name=\"buttom\" class=\"button grey\">";
print "</form>\n";
print "</div></div>\n";

####end form for global parameters

##paint the server configuration
my @run = &getFarmServers( $farmname );

print "<a name=\"backendlist\"></a>";

print "
<div class=\"box grid_12\">
  <div class=\"box-head\">
       <span class=\"box-icon-24 fugue-24 server\"></span>       
       <h2>Edit real IP servers configuration</h2>
  </div>
  <div class=\"box-content no-pad\">
         <table class=\"display\">";
print "    <thead>";
print "    <tr>";
print "		<th>Server</th>";
print "		<th>Address</th>";
print "		<th>Local Interface</th>";
print "		<th>Weight</th>";
print "		<th>Priority</th>";
print "		<th>Actions</th>";
print "    </tr>";
print "    </thead>";
print "	   <tbody>";

$id_serverchange = $id_server;
my $sindex     = 0;
my @laifaces   = &listActiveInterfaces( "phvlan" );
my $rowcounter = 1;
foreach $l_servers ( @run )
{
	my @l_serv = split ( "\;", $l_servers );

	$isrs = "true";
	if ( $action eq "editfarm-editserver" && $id_serverchange eq @l_serv[0] )
	{
		print "<form method=\"post\" class=\"myform\" action=\"index.cgi\">"
		  ;    #This form ends in createmenuserverfarm
		print "<tr class=\"selected\">";

		#id server
		print "<td>@l_serv[0]</td>";
		print "<input type=\"hidden\" name=\"id_server\" value=\"@l_serv[0]\">";

		#real server ip
		print
		  "<td><input type=\"text\" size=\"12\"  name=\"rip_server\" value=\"@l_serv[1]\"> </td>";

		#local interface
		print "<td>";
		print "<select name=\"if\">";
		foreach $iface ( @laifaces )
		{
			if ( @l_serv[2] eq $iface )
			{
				print "<option value=\"$iface\" selected=\"selected\">$iface</option>";
			}
			else
			{
				print "<option value=\"$iface\">$iface</option>";
			}
		}
		print "</select>";
		print "</td>";

		#Weight
		print
		  "<td><input type=\"number\" size=\"4\"  name=\"weight_server\" value=\"@l_serv[3]\"> </td>";

		#Priority
		print
		  "<td><input type=\"number\" size=\"4\"  name=\"priority_server\" value=\"@l_serv[4]\"> </td>";
		&createmenuserversfarm( "edit", $farmname, @l_serv[0] );
	}
	else
	{
# print
# "<form method=\"get\" name=\"service_${srv}_backend_${l_serv[0]}\" action=\"index.cgi\#backendlist\">";
		if ( $rowcounter % 2 == 0 )
		{
			print "<tr class=\"even\">";
		}
		else
		{
			print "<tr class=\"odd\">";
		}
		$rowcounter++;

		print "<td>@l_serv[0]</td>";
		print "<td>@l_serv[1]</td>";
		print "<td>@l_serv[2]</td>";
		print "<td>@l_serv[3]</td>";
		print "<td>@l_serv[4]</td>";
		&createmenuserversfarm( "normal", $farmname, @l_serv[0] );
	}

	# print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
	# print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
	# print "<input type=\"hidden\" name=\"id_server\" value=\"@l_serv[0]\">";
	# print "</form>";
	print "</tr>";
	$sindex = @l_serv[0];

}

## New backend form
$sindex = $sindex + 1;
if ( $action eq "editfarm-addserver" )
{
	$action = "editfarm";
	$isrs   = "true";
	print "<form method=\"post\" class=\"myform\" action=\"index.cgi\">"
	  ;    #This form ends in createmenuserverfarm
	print "<tr class=\"selected\">";

	#id server
	print "<td>$sindex</td>";
	print "<input type=\"hidden\" name=\"id_server\" value=\"$sindex\">";

	#real server ip
	print
	  "<td><input type=\"text\" size=\"12\"  name=\"rip_server\" value=\"\"> </td>";

	#local interface
	print "<td>";
	print "<select name=\"if\">";
	my $first = "true";
	foreach $iface ( @laifaces )
	{
		if ( $first eq "true" )
		{
			print "<option value=\"$iface\" selected=\"selected\">$iface</option>";
			$first = "false";
		}
		else
		{
			print "<option value=\"$iface\">$iface</option>";
		}
	}
	print "</select>";
	print "</td>";

	#Weight
	print
	  "<td><input type=\"number\" size=\"4\"  name=\"weight_server\" value=\"\"></td>";

	#Priority
	print
	  "<td><input type=\"number\" size=\"4\"  name=\"priority_server\" value=\"\"> </td>";

	&createmenuserversfarm( "add", $farmname, $sindex );

	# print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
	# print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
	# print "<input type=\"hidden\" name=\"id_server\" value=\"$sindex\">";
	# print "</form>";
	print "</tr>";
}

print "<tr>";
print "<td  class='gray' colspan=\"5\"></td>";

# print
# "<form method=\"get\" name=\"backendlist\" action=\"index.cgi\#backendlist\">";
&createmenuserversfarm( "new", $farmname, "" );

# print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
# print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
# print "<input type=\"hidden\" name=\"id_server\" value=\"\">";
# print "</form>";
print "</tr>";

print "</tbody>";
print "</table>";

print "</div>\n</div>\n";

1;
