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

### VIEW L4xNAT FARM ###

#global info for a farm
print "
    <div class=\"box container_12 grid_12\">
      <div class=\"box-head\">
           <span class=\"box-icon-24 fugue-24 globe\"></span>    
        <h2>Edit $farmname Farm global parameters</h2>
      </div>
      <div class=\"box-content global-farm\">
";

print "<div class=\"grid_6\">\n";

#
# Change farm's name form
#
print "<div class=\"form-row\">\n";
print "<p class=\"form-label\"><b>Farm's name.</b></p>";
print "<form method=\"post\" action=\"index.cgi\">";

print "<input type=\"hidden\" name=\"action\" value=\"editfarm-Parameters\">";
print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
print
  "<div class=\"form-item\"><input type=\"text\" class=\"fixedwidth\" value=\"$farmname\" size=\"25\" name=\"newfarmname\"> ";

print "</div>\n";

print "</div>\n";

#####Virtual IP and virtual port
print "<div class=\"form-row\">\n";
print
  "<p class=\"form-label\"><b>Farm Virtual IP and Virtual port(s).</b>Specify a single port, several ports (i.e 80,8080), port range (i.e. 21:23) or all ports with '*'. Also a combination of them should work.</p>";
$vip   = &getFarmVip( "vip",  $farmname );
$vport = &getFarmVip( "vipp", $farmname );
@listinterfaces = &listallips();
$clrip          = &getClusterRealIp();
my $disabled = "";

if ( $farmprotocol eq "all" )
{
	$disabled = "disabled";
}

print
  "<div class=\"form-item\"><select name=\"vip\" class=\"fixedwidth-medium\">";
foreach $ip ( @listinterfaces )
{
	if ( $ip !~ $clrip )
	{
		if ( $vip eq $ip )
		{
			print "<option value=\"$ip\" selected=\"selected\">$ip</option>";
		}
		else
		{
			print "<option value=\"$ip\">$ip</option>";
		}
	}
}
print "</select> ";
print
  " <input type=\"text\" class=\"fixedwidth-small\" value=\"$vport\" size=\"20\" name=\"vipp\" $disabled>";
if ( $disabled ne "" )
{
	print "<input type=\"hidden\" name=\"vipp\" value=\"$vport\">";
}

print "</div>\n";
print "</div>\n";

print "<br><br><br>";

#
# Load Balance Algorithm
#
print "<div class=\"form-row\">\n";
print "<p class=\"form-label\"><b>Load Balance Algorithm.</b></p>";
$lbalg = &getFarmAlgorithm( $farmname );
if ( $lbalg == -1 )
{
	$lbalg = "weight";
}

print "<div class=\"form-item\"><select name=\"lb\" class=\"fixedwidth\">";
if ( $lbalg eq "weight" )
{
	print
	  "<option value=\"weight\" selected=\"selected\">Weight: connection linear dispatching by weight</option>";
}
else
{
	print
	  "<option value=\"weight\">Weight: connection linear dispatching by weight</option>";
}
if ( $lbalg eq "prio" )
{
	print
	  "<option value=\"prio\" selected=\"selected\">Priority: connections always to the most prio available</option>";
}
else
{
	print
	  "<option value=\"prio\" >Priority: connections always to the most prio available</option>";
}
if ( $lbalg eq "leastconn" )
{
	print
	  "<option value=\"leastconn\" selected=\"selected\">Least Connections: connections to the least open conns available</option>";
}
else
{
	print
	  "<option value=\"leastconn\" >Least Connections: connections to the least open conns available</option>";
}

print "</select> ";
print "</div>\n";
print "</div>\n";

print "</div><div class=\"grid_6\">\n";

#
# Type session
#
print "<div class=\"form-row\">\n";
print "<p class=\"form-label\"><b>Persistence mode.</b></p>";
$session = &getFarmSessionType( $farmname );
if ( $session == -1 )
{
	$session = "none";
}

print "<div class=\"form-item\"><select name=\"session\" class=\"fixedwidth\">";
print "<option value=\"none\">no persistence</option>";
if ( $session eq "ip" )
{
	print "<option value=\"ip\" selected=\"selected\">IP: client address</option>";
}
else
{
	print "<option value=\"ip\" >IP: client address</option>";
}
print "</select> ";
print "</div>\n";
print "</div>\n";

if ( $session ne "none" )
{
	#
	# Session TTL
	#
	print "<div class=\"form-row\">\n";
	print
	  "<p class=\"form-label\"><b>Source IP Address Persistence time to limit.</b> In seconds, only for IP persistence.</p>";
	my @ttl = &getFarmMaxClientTime( $farmname );

	print
	  "<div class=\"form-item\"><input type=\"number\" class=\"fixedwidth\" value=\"@ttl[0]\" size=\"4\" name=\"sessttl\"> ";

	print "</div>\n";
	print "</div>\n";
}

#
# Protocol
#
print "<div class=\"form-row\">\n";
print "<p class=\"form-label\"><b>Protocol type.</b></p>";
my $farmprotocol = &getFarmProto( $farmname );
if ( $farmprotocol == -1 )
{
	$farmprotocol = "all";
}

print
  "<div class=\"form-item\"><select name=\"farmprotocol\" class=\"fixedwidth\">";

if ( $farmprotocol eq "all" )
{
	print "<option value=\"all\" selected=\"selected\">ALL</option>";
}
else
{
	print "<option value=\"all\">ALL</option>";
}
if ( $farmprotocol eq "tcp" )
{
	print "<option value=\"tcp\" selected=\"selected\">TCP</option>";
}
else
{
	print "<option value=\"tcp\">TCP</option>";
}
if ( $farmprotocol eq "udp" )
{
	print "<option value=\"udp\" selected=\"selected\">UDP</option>";
}
else
{
	print "<option value=\"udp\">UDP</option>";
}
if ( $farmprotocol eq "sip" )
{
	print "<option value=\"sip\" selected=\"selected\">SIP</option>";
}
else
{
	print "<option value=\"sip\">SIP</option>";
}
if ( $farmprotocol eq "ftp" )
{
	print "<option value=\"ftp\" selected=\"selected\">FTP</option>";
}
else
{
	print "<option value=\"ftp\">FTP</option>";
}
if ( $farmprotocol eq "tftp" )
{
	print "<option value=\"tftp\" selected=\"selected\">TFTP</option>";
}
else
{
	print "<option value=\"tftp\">TFTP</option>";
}
print "</select> ";
print "</div>\n";
print "</div>\n";

#
# NAT type
#
print "<div class=\"form-row\">\n";
print "<p class=\"form-label\"><b>NAT type.</b></p>";
my $nattype = &getFarmNatType( $farmname );
if ( $nattype == -1 )
{
	$nattype = "nat";
}
my $seldisabled = "";

print
  "<div class=\"form-item\"><select $seldisabled name=\"nattype\" class=\"fixedwidth\">";
if ( $nattype eq "nat" )
{
	print "<option value=\"nat\" selected=\"selected\">NAT</option>";
}
else
{
	print "<option value=\"nat\">NAT</option>";
}
if ( $nattype eq "dnat" )
{
	print "<option value=\"dnat\" selected=\"selected\">DNAT</option>";
}
else
{
	print "<option value=\"dnat\">DNAT</option>";
}

print "</select> ";
print "</div>\n";
print "</div>\n";

print "</div><div class=\"grid_12\">\n";
print "<br><br>";
print "<h6>Farm Guardian</h6>\n";
print "<hr></hr>";
print "</div><div class=\"grid_6\">\n";    #div grid 6 l

#
# Use farmguardian
#
# open farmguardian file to view config.
@fgconfig  = &getFarmGuardianConf( $farmname, "" );
$fgttcheck = $fgconfig[1];
$fgscript  = $fgconfig[2];
$fgscript =~ s/\n//g;
$fgscript =~ s/\"/\'/g;
$fguse = $fgconfig[3];
$fguse =~ s/\n//g;
$fglog = $fgconfig[4];
if ( !$fgttcheck && $fguse eq 'true' ) { $fgttcheck = 5; }

# Enable FG
print "<div class=\"form-row\">\n";
print
  "<p class=\"form-label\"><b>Use FarmGuardian to check Backend Servers</b></p>";

print "<div class=\"form-item mycheckbox\">";

if ( $fguse eq 'true' )
{
	print "<input type=\"checkbox\" checked name=\"usefarmguardian\">";
}
else
{
	print "<input type=\"checkbox\" name=\"usefarmguardian\"> ";
}
print "</div>\n";
print "</div>\n";
print "<br>";

# Enable FG logs
print "<div class=\"form-row\">\n";
print "<p class=\"form-label\"><b>Enable farmguardian logs</b></p>";
print "<div class=\"form-item mycheckbox\">";

if ( $fglog eq "true" )
{
	print "<input type=\"checkbox\" checked name=\"farmguardianlog\"> ";
}
else
{
	print "<input type=\"checkbox\" name=\"farmguardianlog\"> ";
}

print "</div>\n";
print "</div>\n";

print "</div>\n";                    #close div grid 6 l
print "<div class=\"grid_6\">\n";    #div grid 6 r

# Check interval
print "<div class=\"form-row\">\n";
print
  "<p class=\"form-label\"><b>Check interval.</b> Time between checks in seconds.</p>";
print
  "<div class=\"form-item\"><input type=\"number\" class=\"fixedwidth\" value=\"$fgttcheck\" size=\"1\" name=\"timetocheck\"> ";
print "</div>\n";
print "</div>\n";

# Command to check
print "<div class=\"form-row\">\n";
print "<p class=\"form-label\"><b>Command to check</b></p>";
print
  "<div class=\"form-item\"><input type=\"text\" class=\"fixedwidth\" value=\"$fgscript\" size=\"60\" name=\"check_script\"> ";
print "</div>\n";
print "</div>\n";
print "<br>";

print "</div>\n";    #close div grid 6 r
print "<div class=\"clear\"></div>";
print
  " <input type=\"submit\" value=\"Modify\" name=\"buttom\" class=\"button grey\"> ";
print "</form>\n";
print "</div></div>\n";

####end form for global parameters

##paint the server configuration
my @run = &getFarmServers( $farmname );

print "
<div class=\"box grid_12\">
  <a name=\"backendlist\"></a>
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
print "		<th>Port</th>";
print "		<th>Weight</th>";
print "		<th>Priority</th>";
print "		<th>Actions</th>";
print "    </tr>";
print "    </thead>";
print "	   <tbody>";

$id_serverchange = $id_server;
my $sindex     = 0;
my $rowcounter = 1;
foreach $l_servers ( @run )
{
	my @l_serv = split ( "\;", $l_servers );

	$isrs = "true";
	if ( $action eq "editfarm-editserver" && $id_serverchange eq $l_serv[0] )
	{
		#This form ends in createmenuserverfarm
		print "<form method=\"post\" action=\"index.cgi\" class=\"myform\">";
		print "<tr class=\"selected\">";

		#id server
		print "<td>$l_serv[0]</td>";
		print "<input type=\"hidden\" name=\"id_server\" value=\"$l_serv[0]\">";

		#real server ip
		print
		  "<td><input type=\"text\" size=\"12\" name=\"rip_server\" value=\"$l_serv[1]\"> </td>";

		#local interface
		print
		  "<td><input type=\"text\" size=\"12\" name=\"port_server\" value=\"$l_serv[2]\" $disabled> </td>";

		#Weight
		print
		  "<td><input type=\"number\" size=\"4\" name=\"weight_server\" min=\"1\" value=\"$l_serv[4]\"> </td>";

		#Priority
		print
		  "<td><input type=\"number\" size=\"4\" name=\"priority_server\" min=\"0\" max=\"9\" value=\"$l_serv[5]\"> </td>";
		&createmenuserversfarm( "edit", $farmname, $l_serv[0] );
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
		print "<td>$l_serv[0]</td>";
		print "<td>$l_serv[1]</td>";
		print "<td>$l_serv[2]</td>";
		print "<td>$l_serv[4]</td>";
		print "<td>$l_serv[5]</td>";
		&createmenuserversfarm( "normal", $farmname, $l_serv[0] );
	}
	print "</tr>";
	$sindex++;
}

## New backend form
if ( $action eq "editfarm-addserver" )
{
	$action = "editfarm";
	$isrs   = "true";

	#This form ends in createmenuserverfarm
	print "<form method=\"post\" class=\"myform\" action=\"index.cgi\">";
	print "<tr class=\"selected\">";

	#id server
	print "<td>$sindex</td>";

	#real server ip
	print
	  "<td><input type=\"text\" size=\"14\" name=\"rip_server\" value=\"\"> </td>";

	# port only editable if the farm isnt multiport
	print
	  "<td><input type=\"text\" size=\"12\" name=\"port_server\" value=\"$l_serv[2]\" $disabled> </td>";

	#Weight
	print
	  "<td><input type=\"number\" size=\"6\" name=\"weight_server\" min=\"1\" value=\"\"></td>";

	#Priority
	print
	  "<td><input type=\"number\" size=\"6\" name=\"priority_server\" min=\"0\" max=\"9\" value=\"\"> </td>";
	&createmenuserversfarm( "add", $farmname, $sindex );
	print "</tr>";
}

print "<tr>";
print "<td  class='gray' colspan=\"5\"></td>";
&createmenuserversfarm( "new", $farmname, "" );
print "</tr>";

print "</tbody>";
print "</table>";
print "</div>";
print "</div>";
