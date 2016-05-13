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

### VIEW TCP/UDP FARM ###

##########################################
# EDIT FARM GLOBAL PARAMETERS
##########################################

&warnmsg( "This profile is deprecated, use L4xNAT instead" );

print "
    <div class=\"box container_12 grid_12\">
      <div class=\"box-head\">
           <span class=\"box-icon-24 fugue-24 globe\"></span>    
        <h2>Edit $farmname Farm global parameters</h2>
      </div>
      <div class=\"box-content grid-demo-12 global-farm\">
";

print "<div class=\"grid_6\">\n";

##########################################
# CHANGE FARM'S NAME FORM
##########################################

print "<div class=\"form-row\">\n";

print "<form method=\"post\" action=\"index.cgi\">\n";
print "<input type=\"hidden\" name=\"action\" value=\"editfarm-Parameters\">\n";
print "<input type=\"hidden\" name=\"id\" value=\"$id\">\n";
print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">\n";

print
  "<p class=\"form-label\"><b>Farm's name.</b> Service will be restarted.</p>\n";
print
  "<div class=\"form-item\"><input type=\"text\" class=\"fixedwidth\" value=\"$farmname\" size=\"25\" name=\"newfarmname\"></div>\n";

print "</div>\n";

##########################################
# CHANGE IP OR PORT FOR VIP
##########################################

$vip   = &getFarmVip( "vip",  $farmname );
$vport = &getFarmVip( "vipp", $farmname );

#~ @listinterfaces = &listallips();
$clrip = &getClusterRealIp();
$guiip = &GUIip();

my @interfaces_available = @{ &getActiveInterfaceList() };

print "<div class=\"form-row\">\n";
print
  "<p class=\"form-label\"><b>Farm Virtual IP.</b> Service will be restarted.</p>\n";
print "<div class=\"form-item\">\n";
print "<select name=\"vip\" class=\"fixedwidth monospace\">";

for my $iface ( @interfaces_available )
{
	next if $$iface{ ip_v } ne 4;

	if ( $$iface{ addr } ne $clrip && $$iface{ addr } ne $guiip )
	{
		my $selected = '';

		if ( $$iface{ addr } eq $vip )
		{
			$selected = "selected=\"selected\"";
		}

		print
		  "<option value=\"$$iface{addr}\" $selected>$$iface{dev_ip_padded}</option>\n";
	}
}

print "</select>\n";
print "</div>\n";
print "</div>\n";

print "<div class=\"form-row\">\n";
print
  "<p class=\"form-label\"><b>Farm Virtual port.</b> Service will be restarted.</p>\n";
print
  "<div class=\"form-item\"> <input type=\"number\" class=\"fixedwidth\" value=\"$vport\" size=\"4\" name=\"vipp\">\n";
print "</div>\n";
print "</div>\n";

##########################################
# LOAD BALANCE ALGORITHM
##########################################

$lb = &getFarmAlgorithm( $farmname );
if ( $lb == -1 )
{
	$lb = "roundrobin";
}

$roundrobin = "Round Robin: equal sharing";
$hash       = "Hash: sticky client";
$weight     = "Weight: connection linear dispatching by weight";
$priority   = "Priority: connections to the highest priority available";
print "<div class=\"form-row\">";

print "<p class=\"form-label\"><b>Load Balance Algorithm</b></p>\n";
print "<div class=\"form-item\">\n";

print "<select name=\"lb\" class=\"fixedwidth\">\n";
if ( $lb eq "roundrobin" )
{
	print
	  "<option value=\"roundrobin\" selected=\"selected\">$roundrobin</option>\n";
}
else
{
	print "<option value=\"roundrobin\">$roundrobin</option>\n";
}
if ( $lb eq "hash" )
{
	print "<option value=\"hash\" selected=\"selected\">$hash</option>\n";
}
else
{
	print "<option value=\"hash\">$hash</option>\n";
}
if ( $lb eq "weight" )
{
	print "<option value=\"weight\" selected=\"selected\">$weight</option>\n";
}
else
{
	print "<option value=\"weight\">$weight</option>\n";
}
if ( $lb eq "prio" )
{
	print "<option value=\"prio\" selected=\"selected\">$priority</option>\n";
}
else
{
	print "<option value=\"prio\">$priority</option>\n";
}
print "</select>\n";
print "</div>\n";
print "</div>\n";

##########################################
# BACKEND RESPONSE TIMEOUT
##########################################

$ftimeout = &getFarmTimeout( $farmname );
if ( $ftimeout == -1 )
{
	$ftimeout = 4;
}
else
{
	chomp ( $ftimeout );
}

print "<div class=\"form-row\">\n";
print
  "<p class=\"form-label\"><b>Backend response timeout.</b> In seconds.</p>\n";
print
  "<div class=\"form-item\"><input type=\"number\" class=\"fixedwidth\" value=\"$ftimeout\" size=\"4\" name=\"timeout\">\n";
print "</div>\n";
print "</div>\n";

##########################################
# BLACKLISTED TIME PARAMETER
##########################################

$blacklist = &getFarmBlacklistTime( $farmname );
if ( $blacklist == -1 )
{
	if ( $ftype eq "udp" )
	{
		$blacklist = 3;
	}
	else
	{
		$blacklist = 30;
	}
}

chomp ( $blacklist );
print "<div class=\"form-row\">\n";
print
  "<p class=\"form-label\"><b>Frequency to check resurrected backends.</b> In seconds.</p>\n";

print
  "<div class=\"form-item\"><input type=\"number\" class=\"fixedwidth\" value=\"$blacklist\" size=\"4\" name=\"blacklist\"></div>\n";

print "</div>\n";

print "</div><div class=\"grid_6\">";

##########################################
# ENABLE CLIENT PERSISTENCE
##########################################

if ( $ftype eq "tcp" )
{
	$persistence = &getFarmPersistence( $farmname );
	if ( $persistence == -1 )
	{
		$persistence = "true";
	}
	print "<div class=\"form-row\">\n";

	print
	  "<p class=\"form-label\"><b>Enable client ip address persistence through memory</b></p>\n";
	print "<div class=\"form-item mycheckbox\">\n";

	if ( $persistence eq "true" )
	{
		print "<input type=\"checkbox\" checked name=\"persistence\">\n";
	}
	else
	{
		print "<input type=\"checkbox\" name=\"persistence\">\n";
	}

	print "</div>\n";
	print "</div>\n";

	##########################################
	# CLIENTS_MAX VALUE
	##########################################

	@client = &getFarmMaxClientTime( $farmname );
	print "<div class=\"form-row\">\n";
	if ( @client == -1 )
	{
		$maxclients = 256;
		$tracking   = 10;
	}
	else
	{
		$maxclients = @client[0];
		chomp ( $maxclients );
		$tracking = @client[1];
		chomp ( $tracking );
	}
	print
	  "<p class=\"form-label\"><b>Max number of clients memorized in the farm.</b> Service will be restarted</p>\n";

	print "<div class=\"form-item\">\n";
	print
	  "<input type=\"number\" class=\"fixedwidth\" value=\"$maxclients\" size=\"4\" name=\"max_clients\">\n";

	print "</div>\n";
	print "</div>\n";

	print "<div class=\"form-row\">\n";
	print
	  "<p class=\"form-label\"><b>Client-time(sec, 0=always).</b> Service will be restarted.</p>\n";
	print "<div class=\"form-item\">\n";
	print
	  "<input type=\"number\" class=\"fixedwidth\" value=\"$tracking\" size=\"4\" name=\"tracking\">\n";
	print "</div>\n";
	print "</div>\n";
}

##########################################
# MAX NUMBER OF SIMULTANEOUS CONNECTIONS
##########################################

$conn_max = &getFarmMaxConn( $farmname );
if ( $conn_max == -1 )
{
	$conn_max = 512;
}
else
{
	chomp ( $conn_max );
}

print "<div class=\"form-row\">\n";
print
  "<p class=\"form-label\"><b>Max number of simultaneous connections.</b> Service will be restarted.</p>\n";
print
  "<div class=\"form-item\"><input type=\"number\" class=\"fixedwidth\" value=\"$conn_max\" name=\"conn_max\">\n";
print "</div>\n";
print "</div>\n";

##########################################
# MAX NUMBER OF REAL IP SERVERS
##########################################

$numberofservers = &getFarmMaxServers( $farmname );
if ( $numberofservers == -1 )
{
	$numberofservers = 16;
}
else
{
	chomp ( $numberofservers );
}

print "<div class=\"form-row\">\n";
print
  "<p class=\"form-label\"><b>Max number of real ip servers.</b> Service will be restarted.</p>\n";
print
  "<div class=\"form-item\"><input type=\"number\" class=\"fixedwidth\" value=\"$numberofservers\" size=\"4\" name=\"max_servers\">\n";
print "</div>\n";
print "</div>\n";

if ( $ftype eq "tcp" )
{

	##########################################
	# X-FORWARDED-FOR HEADER PARAMETER
	##########################################

	$xforw = &getFarmXForwFor( $farmname );
	if ( $xforw == -1 )
	{
		$xforw = "false";
	}
	print "<div class=\"form-row\">\n";
	print
	  "<p class=\"form-label\"><b>Add X-Forwarded-For header to http requests</b></p>\n";
	print "<div class=\"form-item mycheckbox\">\n";

	if ( $xforw eq "false" )
	{
		print "<input type=\"checkbox\" name=\"xforwardedfor\">";
	}
	else
	{
		print "<input type=\"checkbox\" checked name=\"xforwardedfor\">";
	}
	print "</div>\n";
	print "</div>\n";
}

##########################################
# FARMGUARDIAN
##########################################

if ( $ftype eq "tcp" )
{
	print "</div><div class=\"grid_12\">\n";
	print "<br><br>";
	print "<h6>Farm Guardian</h6>\n";
	print "<hr></hr>";
	print "</div><div class=\"grid_6\">\n";    #div grid 6 l

	#open farmguardian file to view config.
	@fgconfig  = &getFarmGuardianConf( $farmname, "" );
	$fgttcheck = @fgconfig[1];
	$fgscript  = @fgconfig[2];
	$fgscript =~ s/\n//g;
	$fgscript =~ s/\"/\'/g;
	$fguse = @fgconfig[3];
	$fguse =~ s/\n//g;
	$fglog = @fgconfig[4];

	if ( !$fgttcheck )
	{
		$fgttcheck = 5;
	}
	else
	{
		chomp ( $fgttcheck );
	}

	# Enable FG
	print "<div class=\"form-row\">\n";
	print
	  "<p class=\"form-label\"><b>Use FarmGuardian to check Backend Servers</b></p>\n";
	print "<div class=\"form-item mycheckbox\">\n";

	if ( $fguse eq "true" )
	{
		print "<input type=\"checkbox\" checked name=\"usefarmguardian\">\n";
	}
	else
	{
		print "<input type=\"checkbox\" name=\"usefarmguardian\">\n";
	}
	print "</div>\n";
	print "</div>\n";
	print "<br>";

	# Enable FG logs
	print "<div class=\"form-row\">\n";
	print "<p class=\"form-label\"><b>Enable farmguardian logs</b></p>\n";
	print "<div class=\"form-item mycheckbox\">\n";

	if ( $fglog eq "true" )
	{
		print "<input type=\"checkbox\" checked name=\"farmguardianlog\">\n";
	}
	else
	{
		print "<input type=\"checkbox\" name=\"farmguardianlog\">\n";
	}
	print "</div>\n";
	print "</div>\n";

	print "</div><div class=\"grid_6\">\n";    #div grid 6 r

	# Check interval
	print "<div class=\"form-row\">\n";
	print
	  "<p class=\"form-label\"><b>Check interval.</b> Time between checks in seconds.</p>\n";
	print
	  "<div class=\"form-item\"> <input type=\"number\" class=\"fixedwidth\" value=\"$fgttcheck\" size=\"1\" name=\"timetocheck\">\n";
	print "</div>\n";
	print "</div>\n";

	# Command to check
	print "<div class=\"form-row\">\n";
	print "<p class=\"form-label\"><b>Command to check</b></p>\n";
	print
	  "<div class=\"form-item\"> <input type=\"text\" class=\"fixedwidth\" value=\"$fgscript\" size=\"60\" name=\"check_script\">\n";
	print "</div>\n";
	print "</div>\n";
	print "<br>";
}

print "</div>\n";    #close div
print "<div class=\"clear\"></div>\n";
print
  "<input type=\"submit\" value=\"Modify\" name=\"buttom\" class=\"button grey\">";
print "</form>\n";
print "</div>\n";
print "</div>\n";

####end form for global parameters

##paint the server configuration
my @run = &getFarmServers( $farmname );

print "
      <div class=\"box grid_12\">
        <div class=\"box-head\">
             <span class=\"box-icon-24 fugue-24 server\"></span>         
          <h2>Edit real IP servers configuration</h2>
        </div>
        <div class=\"box-content no-pad\">
                 <table class=\"display\">
            <thead>
              <tr>
                <th>Server</th>
                <th>Address</th>
                <th>Port</th>
                <th>Max connections</th>
                <th>Weight</th>
                               <th>Priority</th>
                               <th>Actions</th>
              </tr>
            </thead>
            <tbody>
";
print "<a name=\"backendlist\"></a>";

$id_serverchange = $id_server;
my $rowcounter = 1;
foreach $l_servers ( @run )
{
	my @l_serv = split ( "\ ", $l_servers );
	if ( @l_serv[2] ne "0.0.0.0" )
	{
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
			  "<td><input type=\"text\" size=\"12\"  name=\"rip_server\" value=\"@l_serv[2]\"> </td>";

			#port
			print
			  "<td><input type=\"number\" size=\"4\"  name=\"port_server\" value=\"@l_serv[4]\"> </td>";

			#max connections
			print
			  "<td><input type=\"number\" size=\"4\"  name=\"max_server\" value=\"@l_serv[8]\"> </td>";

			#Weight
			print
			  "<td><input type=\"number\" size=\"4\"  name=\"weight_server\" value=\"@l_serv[12]\"> </td>";

			#Priority
			print
			  "<td><input type=\"number\" size=\"4\"  name=\"priority_server\" value=\"@l_serv[14]\"> </td>";

			&createmenuserversfarm( "edit", $farmname, @l_serv[0] );
		}
		else
		{
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
			print "<td>@l_serv[2]</td>";
			print "<td>@l_serv[4]</td>";
			print "<td>@l_serv[8]</td>";
			print "<td>@l_serv[12]</td>";
			print "<td>@l_serv[14]</td>";
			&createmenuserversfarm( "normal", $farmname, @l_serv[0] );
			my $maintenance = &getFarmBackendMaintenance( $farmname, @l_serv[0] );
		}
		print "</tr>";
	}

	if ( @l_serv[2] eq "0.0.0.0" && $action eq "editfarm-addserver" )
	{
		$action = "editfarm";
		$isrs   = "true";
		print "<form method=\"post\" class=\"myform\" action=\"index.cgi\">"
		  ;    #This form ends in createmenuserverfarm
		print "<tr class=\"selected\">";

		#id server
		print "<td>@l_serv[0]</td>";
		print "<input type=\"hidden\" name=\"id_server\" value=\"@l_serv[0]\">";

		#real server ip
		print
		  "<td><input type=\"text\" size=\"12\"  name=\"rip_server\" value=\"\"> </td>";

		#port
		print
		  "<td><input type=\"number\" size=\"4\"  name=\"port_server\" value=\"\"> </td>";

		#max connections
		print
		  "<td><input type=\"number\" size=\"4\"  name=\"max_server\" value=\"\"> </td>";

		#Weight
		print
		  "<td><input type=\"number\" size=\"4\"  name=\"weight_server\" value=\"\"> </td>";

		#Priority
		print
		  "<td><input type=\"number\" size=\"4\"  name=\"priority_server\" value=\"\"> </td>";

		&createmenuserversfarm( "add", $farmname, @l_serv[0] );

		print "</tr>";
	}
}

print "<tr>";
print "<td class='gray' colspan=\"6\"></td>";

&createmenuserversfarm( "new", $farmname, @l_serv[0] );

print "</tr>";

print "</tbody>";
print "</table>";
print "</div>";
print "</div>";

1;
