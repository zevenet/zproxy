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

### VIEW GSLB FARM ###

#global info for a farm
print "
    <div class=\"box container_12 grid_12\">
      <div class=\"box-head\">
           <span class=\"box-icon-24 fugue-24 globe\"></span>    
        <h2>Edit $farmname Farm global parameters</h2>
      </div>
      <div class=\"box-content grid-demo-12 global-farm\">
";

#Change farm's name form
print "<div class=\"form-row\">\n
	<p class=\"form-label\"><b>Farm's name.</b> Service will be restarted.</p>
	<form method=\"post\" action=\"index.cgi\">
	<input type=\"hidden\" name=\"action\" value=\"editfarm-Parameters\">
	<input type=\"hidden\" name=\"id\" value=\"$id\">
	<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
print
  "<div class=\"form-item\"><input type=\"text\" value=\"$farmname\" size=\"25\" name=\"newfarmname\" class=\"fixedwidth\"> </div>";
print "</div>\n";

#Change virtual IP and virtual Port
print "<div class=\"form-row\">\n";
print "<p class=\"form-label\"><b>Farm Virtual IP and Virtual port</b></p>";
$vip   = &getFarmVip( "vip",  $farmname );
$vport = &getFarmVip( "vipp", $farmname );

# @listinterfaces = &listallips();
my @interfaces_available = @{ &getActiveInterfaceList() };

my $clrip = &getZClusterLocalIp();

#~ my @nvips = &getListActiveIps();
print
  "<div class=\"form-item\"><select name=\"vip\" class=\"fixedwidth monospace\">\n";
print "<option value=\"\">-Select One-</option>\n";

for my $iface ( @interfaces_available )
{
	next if $$iface{ addr } eq $clrip;

	my $selected = '';

	if ( $$iface{ addr } eq $vip )
	{
		$selected = "selected=\"selected\"";
	}

	print
	  "<option value=\"$$iface{addr}\" $selected>$$iface{dev_ip_padded}</option>\n";
}

print
  " <input type=\"number\" value=\"$vport\" size=\"4\" name=\"vipp\" class=\"fixedwidth\">";
print "</div>\n";
print "<div class=\"clear\"></div>";
print "<br>";
print
  " <input type=\"submit\" value=\"Modify\" name=\"buttom\" class=\"button grey\"></div>";
print "</form>\n";
print "</div></div>\n";

#Add SERVICES
print "
    <div class=\"box grid_6\">
      <div class=\"box-head\">
           <span class=\"box-icon-24 fugue-24 plus\"></span>     
        <h2>Add service</h2>
      </div>
      <div class=\"box-content global-farm\">
";
print "<div class=\"form-row\">\n";
print
  "<p class=\"form-label\"><b>Add service and algorithm.</b> Manage services and backends.</p>";
print "<form method=\"post\" action=\"index.cgi\">";
print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
print "<input type=\"hidden\" name=\"action\" value=\"editfarm-addservice\">";
print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
print "<input type=\"hidden\" name=\"service_type\" value=\"service\">";
print
  "<div class=\"form-item\"><input type=\"text\" value=\"\" size=\"25\" name=\"service\" class=\"fixedwidth\">";
print
  " <select name=\"lb\" class=\"fixedwidth\"><option value=\"roundrobin\" selected=\"selected\">Round Robin: equal sharing</option><option value=\"prio\">Priority: connections always to the most prio available</option></select>";

print "</div>\n";
print "</div>";
print
  " <input type=\"submit\" value=\"Add\" name=\"buttom\" class=\"button grey\"></div>";
print "</form>\n";
print "</div>";
print "<div class=\"clear\"></div>";

####end form for global parameters

# SERVICES
my $id_serverr = $id_server;

# Manage every service
my @services = &getGSLBFarmServices( $farmname );
foreach $srv ( @services )
{
	my $lb = &getFarmVS( $farmname, $srv, "algorithm" );
	print "<div class=\"box grid_12\">\n";
	print "<a name=\"servicelist-$srv\"></a>\n";
	print "<div class=\"box-head\">\n";
	print "<span class=\"box-icon-24 fugue-24 monitor\"></span>\n";
	print "<h2 style=\"float: left; padding-left: 0px; padding-right: 0px;\">";
	print "
			<form method=\"post\" action=\"index.cgi\">
			<button type=\"submit\" class=\"myicons\" title=\"Delete service $srv\" onclick=\"return confirm('Are you sure you want to delete the Service $srv?')\">
			<span class=\"icon-24 fugue-24 cross-circle\"></span>
			</button>
			<input type=\"hidden\" name=\"id\" value=\"1-2\">
			<input type=\"hidden\" name=\"action\" value=\"editfarm-deleteservice\">
			<input type=\"hidden\" name=\"service_type\" value=\"service\">
			<input type=\"hidden\" name=\"service\" value=\"$srv\">
			<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">
			</form>";
	print "</h2><h2>";
	print " Service \"$srv\" with ";

	if ( $lb eq "roundrobin" )
	{
		print "Round Robin";
	}
	else
	{
		if ( $lb eq "prio" )
		{
			print "Priority";
		}
		else
		{
			print "Unknown";
		}
	}
	print " algorithm</h2></div>";

	print "<div class=\"box-content global-farm\">";

	# Default port health check
	my $dpc = &getFarmVS( $farmname, $srv, "dpc" );
	print "<div class=\"form-row\">\n";
	print "<form method=\"post\" action=\"index.cgi\">";
	print
	  "<p class=\"form-label\"><b>Default TCP port health check.</b> Empty value disabled.</p>";
	print "<input type=\"hidden\" name=\"action\" value=\"editfarm-dpc\">";
	print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
	print "<input type=\"hidden\" name=\"service\" value=\"$srv\">";
	print "<input type=\"hidden\" name=\"service_type\" value=\"service\">";
	print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
	print
	  "<div class=\"form-item\"><input type=\"number\" size=\"20\" name=\"dpc\" class=\"fixedwidth\" value=\"$dpc\"> ";
	print
	  "<input type=\"submit\" value=\"Modify\" name=\"buttom\" class=\"button grey\">";
	print "</form>";
	print "</div>\n";
	print "</div></div></div>";
	print "
			<div class=\"box grid_12\">
				<div class=\"box-head\">
					<span class=\"box-icon-24 fugue-24 server\"></span>       
					<h2>Backends for service '$srv'</h2>
				</div>
				<div class=\"box-content no-pad\">
				<table class=\"display\">";

	# Maximize button
	print
	  "<thead><tr><th>ID</th><th>IP Address</th><th>Actions</th></tr></thead><tbody>";
	my $backendsvs = &getFarmVS( $farmname, $srv, "backends" );
	my @be = split ( "\n", $backendsvs );
	foreach $subline ( @be )
	{
		$subline =~ s/^\s+//;
		if ( $subline =~ /^$/ )
		{
			next;
		}

		my @subbe = split ( " => ", $subline );

		if (    $id_serverr eq "@subbe[0]"
			 && $service eq "$srv"
			 && $action eq "editfarm-editserver" )
		{
			print "<form method=\"post\" class=\"myform\" action=\"index.cgi\">"
			  ;    #This form ends in createmenuserverfarm
			print "<tr class=\"selected\">";

			print "<td>$subbe[0]</td>";

			print
			  "<td><input type=\"text\" size=\"20\"  name=\"rip_server\" value=\"@subbe[1]\"></td>";
			print "<input type=\"hidden\" name=\"service\" value=\"$service\">";
			print "<input type=\"hidden\" name=\"lb\" value=\"$lb\">";
			print "<input type=\"hidden\" name=\"service_type\" value=\"service\">";
			$sv = $srv;
			&createmenuserversfarm( "edit", $farmname, $id_serverr );
			print "</tr>";

		}
		else
		{
			print "<td>$subbe[0]</td><td>$subbe[1]</td>";
			$sv = $srv;
			&createmenuserversfarm( "normal", $farmname, @subbe[0] );
			print "</tr>";

		}
	}

	# New backend form
	if ( $action eq "editfarm-addserver" && $service eq "$srv" )
	{
		print "<a name=\"servicelist-$srv\"></a>\n\n";
		my $id_srv = "";
		print "<form method=\"post\" class=\"myform\" action=\"index.cgi\">"
		  ;    #This form ends in createmenuserverfarm
		print "<tr class=\"selected\">";
		if ( $lb eq "prio" )
		{
			print "<td><select name=\"id_server\" disabled>";
			if ( @be == 0 )
			{
				print "<option value=\"primary\" selected=\"selected\">primary</option>";
				print "<option value=\"secondary\">secondary</option>";
				$id_srv = "primary";
			}
			else
			{
				print "<option value=\"primary\" >primary</option>";
				print "<option value=\"secondary\" selected=\"selected\">secondary</option>";
				$id_srv = "secondary";
			}
			print "</select></td>";
		}
		else
		{
			print "<td>-</td>";
		}
		print
		  "<td><input type=\"text\" size=\"20\" name=\"rip_server\" value=\"\"></td>";
		$sv = $srv;

		print "<input type=\"hidden\" name=\"service\" value=\"$service\">";
		print "<input type=\"hidden\" name=\"lb\" value=\"$lb\">";
		print "<input type=\"hidden\" name=\"id_server\" value=\"$id_srv\">";
		print "<input type=\"hidden\" name=\"service_type\" value=\"service\">";

		&createmenuserversfarm( "add", $farmname, @l_serv[0] );

		print "</tr>";
	}

	# add backend button
	if ( !( $lb eq "prio" && @be > 2 ) )
	{
		print "<tr><td class='gray' colspan=\"2\"></td>";

		&createmenuserversfarm( "new", $farmname, "" );

		print "</tr>";
	}
	print "</tbody></table>";
	print "</div>";

	print "</div>";
}

#Add ZONES
print "
    <div class=\"box grid_6\">
      <div class=\"box-head\">
           <span class=\"box-icon-24 fugue-24 plus\"></span>     
        <h2>Add zone</h2>
      </div>
      <div class=\"box-content global-farm\">
";
print "<div class=\"form-row\">\n";
print "<p class=\"form-label\"><b>Add zone.</b> Manage DNS zones.</p>";
print "<form method=\"post\" action=\"index.cgi\">";
print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
print "<input type=\"hidden\" name=\"action\" value=\"editfarm-addservice\">";
print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
print "<input type=\"hidden\" name=\"service_type\" value=\"zone\">";
print
  "<div class=\"form-item\"><input type=\"text\" value=\"\" size=\"25\" name=\"zone\" class=\"fixedwidth\"> ";

print "</div>\n";
print "</div>";
print
  "<input type=\"submit\" value=\"Add\" name=\"buttom\" class=\"button grey\"></div>";
print "</form>\n";

print "</div>";

print "<div class=\"clear\"></div>";

# ZONES

my @zones   = &getFarmZones( $farmname );
my $first   = 0;
my $vserver = 0;
my $pos     = 0;
foreach $zone ( @zones )
{

	$pos++;
	$first = 1;
	print "<div class=\"box grid_12\">\n";
	print "<div class=\"box-head\">\n";
	print "<span class=\"box-icon-24 fugue-24 monitor\"></span>\n";
	print "<h2 style=\"float: left; padding-left: 0px; padding-right: 0px;\">";
	print "
			<form method=\"post\" action=\"index.cgi\">
			<button type=\"submit\" class=\"myicons\" title=\"Delete zone $zone\" onclick=\"return confirm('Are you sure you want to delete the Zone $zone?')\">
			<span class=\"icon-24 fugue-24 cross-circle\"></span>
			</button>
			<input type=\"hidden\" name=\"id\" value=\"1-2\">
			<input type=\"hidden\" name=\"action\" value=\"editfarm-deleteservice\">
			<input type=\"hidden\" name=\"service_type\" value=\"zone\">
			<input type=\"hidden\" name=\"service\" value=\"$zone\">
			<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">
			</form>
	";
	print "</h2>";

	# Anchor
	print "<a name=\"zonelist-$zone\"></a>";

	print "<h2> Zone \"$zone\"</h2></div>";

	#Maximize button
	print "<div class=\"box-content global-farm\">";

	# Default name server
	my $ns = &getFarmVS( $farmname, $zone, "ns" );
	print "<form method=\"post\" action=\"index.cgi\">";
	print "<div class=\"form-row\">\n";
	print
	  "<p class=\"form-label\"><b>Default Name Server.</b> Empty value disabled.</p>";
	print "<input type=\"hidden\" name=\"action\" value=\"editfarm-ns\">";
	print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
	print "<input type=\"hidden\" name=\"service\" value=\"$zone\">";
	print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
	print "<input type=\"hidden\" name=\"service_type\" value=\"zone\">";
	print
	  "<div class=\"form-item\"><input type=\"text\" size=\"20\" class=\"fixedwidth\" name=\"ns\" value=\"$ns\"> ";
	print
	  "<input type=\"submit\" value=\"Modify\" name=\"buttom\" class=\"button grey\"></div>";
	print "</form>";
	print "</div>";
	print "</div>";
	print "</div>";

	print "
	
		<div class=\"box grid_12\">
		<div class=\"box-head\">   
			<span class=\"box-icon-24 fugue-24 server\"></span>    
			<h2>Resources for zone \"$zone\"</h2>
		</div>
		<div class=\"box-content no-pad\">
			<ul class=\"table-toolbar\">
				<li>
					<form method=\"post\" action=\"index.cgi\#zonelist-$zone\">
						<button type=\"submit\" class=\"noborder\">
						<img src=\"img/icons/basic/plus.png\" alt=\"Add\"> Add Resource</button>
									
						<input type=\"hidden\" name=\"id\" value=\"1-2\">
						<input type=\"hidden\" name=\"action\" value=\"editfarm-addserver\">
						<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">
						<input type=\"hidden\" name=\"id_server\" value=\"$l_serv[0]\">
						<input type=\"hidden\" name=\"service\" value=\"$zone\">
						<input type=\"hidden\" name=\"service_type\" value=\"zone\">						
					</form>
				</li>
			</ul>
			<table class=\"dns-table display\">
	";

	print
	  "<thead><tr><th>Resource Name</th><th>TTL</th><th>Type</th><th>RData</th><th>Actions</th></tr></thead>
	  <tbody>";

	# New backend form
	# if ( ( $action =~ /editfarm-addserver/ || $action =~ /editfarm-saveserver/ )
	if ( $action =~ /editfarm-addserver/ && $service eq $zone )
	{
		my $zoneaux = $zone;
		$zoneaour =~ s/\./\_/g;

		print "<tr class=\"selected\">";

		print "<form method=\"post\" class=\"myform\" action=\"index.cgi\">"
		  ;    #This form ends in createmenuserverfarm

		print
		  "<td><input type=\"text\" size=\"30\" name=\"resource_server\" value=\"$resource_server\"> </td>";
		print
		  "<td><input type=\"number\" size=\"10\" name=\"ttl_server\" value=\"$ttl_server\"> </td>";

		# print "<td><select name=\"type_server\" onchange=\"this.form.submit()\">";
		print
		  "<td><select class=\"resource-type\" name=\"type_server\" onchange=\"chRTypeAdd(this)\">";

		if ( $type_server eq "NS" )
		{
			print "<option value=\"NS\" selected=\"selected\">NS</option>";
		}
		else { print "<option value=\"NS\">NS</option>"; }

		if ( $type_server eq "A" )
		{
			print "<option value=\"A\" selected=\"selected\">A</option>";
		}
		else { print "<option value=\"A\">A</option>"; }

		if ( $type_server eq "AAAA" )
		{
			print "<option value=\"AAAA\" selected=\"selected\">AAAA</option>";
		}
		else { print "<option value=\"AAAA\">AAAA</option>"; }

		if ( $type_server eq "CNAME" )
		{
			print "<option value=\"CNAME\" selected=\"selected\">CNAME</option>";
		}
		else { print "<option value=\"CNAME\">CNAME</option>"; }

		if ( $type_server eq "DYNA" )
		{
			print "<option value=\"DYNA\" selected=\"selected\">DYNA</option>";
		}
		else { print "<option value=\"DYNA\">DYNA</option>"; }

		if ( $type_server eq "MX" )
		{
			print "<option value=\"MX\" selected=\"selected\">MX</option>";
		}
		else { print "<option value=\"MX\">MX</option>"; }

		if ( $type_server eq "SRV" )
		{
			print "<option value=\"SRV\" selected=\"selected\">SRV</option>";
		}
		else { print "<option value=\"SRV\">SRV</option>"; }

		if ( $type_server eq "TXT" )
		{
			print "<option value=\"TXT\" selected=\"selected\">TXT</option>";
		}
		else { print "<option value=\"TXT\">TXT</option>"; }

		if ( $type_server eq "PTR" )
		{
			print "<option value=\"PTR\" selected=\"selected\">PTR</option>";
		}
		else { print "<option value=\"PTR\">PTR</option>"; }

		if ( $type_server eq "NAPTR" )
		{
			print "<option value=\"NAPTR\" selected=\"selected\">NAPTR</option>";
		}
		else { print "<option value=\"NAPTR\">NAPTR</option>"; }

		print "</select></td>";

		print "<td>";

		if ( $rdata_server ne "" ) { $rdata = $rdata_server; }

		if ( $type_server ne "DYNA" )
		{
			print "
				<select name=\"rdata_server\" id=\"resourcerdata-select\" disabled=\"\" style=\"display: none;\"> ";
		}
		else
		{
			print "
				<select name=\"rdata_server\" id=\"resourcerdata-select\"> ";
		}

		foreach $sr ( @services )
		{
			my @srv = split ( ".cfg", $sr );
			my $srr = @srv[0];
			print "<option value=\"$srr\" ";
			if ( $rdata eq $srr ) { print " selected=\"selected\" "; }
			print ">$srr</option>";
		}
		print "</select>";

		my $rdataPrint = $rdata;
		$rdataPrint =~ s/\"/&quot;/g;

		if ( $type_server ne "DYNA" )
		{
			print
			  "<input type=\"text\" name=\"rdata_server\" id=\"resourcerdata-input\" size=\"50\" value=\"$rdataPrint\" 
						style=\"display: block;\">";
		}
		else
		{
			print
			  "<input type=\"text\" name=\"rdata_server\" id=\"resourcerdata-input\" size=\"50\" value=\"$rdataPrint\" 
						style=\"display: none;\">";
		}

		print "</td>";

		print "<input type=\"hidden\" name=\"service\" value=\"$zone\">";
		print "<input type=\"hidden\" name=\"service_type\" value=\"zone\">";
		&createmenuserversfarmz( "add", $farmname, @l_serv[0] );

		print "</tr>";

	}

	my $backendsvs = &getFarmVS( $farmname, $zone, "resources" );

	my @be = split ( "\n", $backendsvs );

	foreach $subline ( @be )
	{
		if ( $subline =~ /^$/ )
		{
			next;
		}

		my @subbe  = split ( "\;", $subline );
		my @subbe1 = split ( "\t", @subbe[0] );
		my @subbe2 = split ( "\_", @subbe[1] );    # index '#'
		my $ztype  = $subbe1[1];
		my $la_resource = $subbe1[0];
		my $la_ttl      = $subbe1[1];

		if ( $resource_server ne "" ) { $la_resource = $resource_server; }
		if ( $ttl_server ne "" )      { $la_ttl      = $ttl_server; }

		if (    $id_serverr eq "$subbe2[1]"
			 && $service eq "$zone"
			 && $action eq "editfarm-editserver" )
		{
			#
			# Edit server
			#
			my $zoneaux = $zone;
			$zoneaux =~ s/\./\_/g;

			print "<tr class=\"selected\">";

			print "<form method=\"post\"  class=\"myform\" action=\"index.cgi\">"
			  ;    #This form ends in createmenuserverfarm

			print
			  "<td><input type=\"text\" size=\"30\"  name=\"resource_server\" value=\"$la_resource\"> </td>";
			if (    $subbe1[1] ne "NS"
				 && $subbe1[1] ne "A"
				 && $subbe1[1] ne "AAAA"
				 && $subbe1[1] ne "CNAME"
				 && $subbe1[1] ne "DYNA"
				 && $subbe1[1] ne "DYNC"
				 && $subbe1[1] ne "MX"
				 && $subbe1[1] ne "SRV"
				 && $subbe1[1] ne "TXT"
				 && $subbe1[1] ne "PTR"
				 && $subbe1[1] ne "NAPTR" )
			{
				print
				  "<td><input type=\"number\" size=\"10\" name=\"ttl_server\" value=\"$la_ttl\"> </td>";
				$ztype = $subbe1[2];
			}
			else
			{
				print
				  "<td><input type=\"number\" size=\"10\" name=\"ttl_server\" value=\"\"></td>";
			}
			my $la_type = $ztype;
			if ( $type_server ne "" ) { $la_type = $type_server; }
			print
			  "<td><select id=\"resource-type\" name=\"type_server\" onchange=\"chRType(this)\">";

			if ( $la_type eq "NS" )
			{
				print "<option value=\"NS\" selected=\"selected\">NS</option>";
			}
			else { print "<option value=\"NS\">NS</option>"; }

			if ( $la_type eq "A" )
			{
				print "<option value=\"A\" selected=\"selected\">A</option>";
			}
			else { print "<option value=\"A\">A</option>"; }

			if ( $la_type eq "AAAA" )
			{
				print "<option value=\"AAAA\" selected=\"selected\">AAAA</option>";
			}
			else { print "<option value=\"AAAA\">AAAA</option>"; }

			if ( $la_type eq "CNAME" )
			{
				print "<option value=\"CNAME\" selected=\"selected\">CNAME</option>";
			}
			else { print "<option value=\"CNAME\">CNAME</option>"; }

			if ( $la_type eq "DYNA" )
			{
				print "<option value=\"DYNA\" selected=\"selected\">DYNA</option>";
			}
			else { print "<option value=\"DYNA\">DYNA</option>"; }

			if ( $la_type eq "MX" )
			{
				print "<option value=\"MX\" selected=\"selected\">MX</option>";
			}
			else { print "<option value=\"MX\">MX</option>"; }

			if ( $la_type eq "SRV" )
			{
				print "<option value=\"SRV\" selected=\"selected\">SRV</option>";
			}
			else { print "<option value=\"SRV\">SRV</option>"; }

			if ( $la_type eq "TXT" )
			{
				print "<option value=\"TXT\" selected=\"selected\">TXT</option>";
			}
			else { print "<option value=\"TXT\">TXT</option>"; }

			if ( $la_type eq "PTR" )
			{
				print "<option value=\"PTR\" selected=\"selected\">PTR</option>";
			}
			else { print "<option value=\"PTR\">PTR</option>"; }

			if ( $la_type eq "NAPTR" )
			{
				print "<option value=\"NAPTR\" selected=\"selected\">NAPTR</option>";
			}
			else { print "<option value=\"NAPTR\">NAPTR</option>"; }

			print "</select></td>";

			print "<td>";

			my $rdata = "";
			if ( @subbe1 == 3 )
			{
				$rdata = $subbe1[2];
			}
			elsif ( @subbe1 == 4 )
			{
				$rdata = $subbe1[3];
			}
			elsif ( @subbe1 == 5 )
			{
				$rdata = $subbe1[4];
			}
			chop ( $rdata );

			if ( $rdata_server ne "" ) { $rdata = $rdata_server; }

			if ( $la_type ne "DYNA" )
			{
				print "
					<select name=\"rdata_server\" id=\"resourcerdata-select\" disabled=\"\" style=\"display: none;\"> ";
			}
			else
			{
				print "
					<select name=\"rdata_server\" id=\"resourcerdata-select\"> ";
			}

			foreach $sr ( @services )
			{
				my @srv = split ( ".cfg", $sr );
				my $srr = @srv[0];
				print "<option value=\"$srr\" ";
				if ( $rdata eq $srr ) { print " selected=\"selected\" "; }
				print ">$srr</option>";
			}
			print "</select>";

			my $rdataPrint = $rdata;
			$rdataPrint =~ s/\"/&quot;/g;

			if ( $la_type ne "DYNA" )
			{
				print
				  "<input type=\"text\" name=\"rdata_server\" id=\"resourcerdata-input\" size=\"50\" value=\"$rdataPrint\" 
							style=\"display: block;\">";
			}
			else
			{
				print "
					<select name=\"rdata_server\" id=\"resourcerdata-select\"> ";
			}

			foreach $sr ( @services )
			{
				my @srv = split ( ".cfg", $sr );
				my $srr = @srv[0];
				print "<option value=\"$srr\" ";
				if ( $rdata eq $srr ) { print " selected=\"selected\" "; }
				print ">$srr</option>";
			}
			print "</select>";

			my $rdataPrint = $rdata;
			$rdataPrint =~ s/\"/&quot;/g;

			if ( $la_type ne "DYNA" )
			{
				print
				  "<input type=\"text\" name=\"rdata_server\" id=\"resourcerdata-input\" size=\"50\" value=\"$rdataPrint\" 
							style=\"display: none;\">";
			}

			print "</td>";

			$nserv = $subbe2[1];

			print "<input type=\"hidden\" name=\"service\" value=\"$zone\">";
			print "<input type=\"hidden\" name=\"service_type\" value=\"zone\">";

			&createmenuserversfarmz( "edit", $farmname, $nserv );

			print "</tr>";
		}
		else
		{
			#
			# Not editing server
			#

			my $zoneaux = $zone;
			$zoneaux =~ s/\./\_/g;

# "<form method=\"get\" name=\"zone_${zoneaux}_resource_${subbe2[1]}\" action=\"index.cgi\#zonelist-$zone\">";
			print "<td>$subbe1[0]</td>";
			if (    $subbe1[1] ne "NS"
				 && $subbe1[1] ne "A"
				 && $subbe1[1] ne "AAA"
				 && $subbe1[1] ne "CNAME"
				 && $subbe1[1] ne "DYNA"
				 && $subbe1[1] ne "DYNC"
				 && $subbe1[1] ne "MX"
				 && $subbe1[1] ne "SRV"
				 && $subbe1[1] ne "TXT"
				 && $subbe1[1] ne "PTR"
				 && $subbe1[1] ne "NAPTR" )
			{
				print "<td>$subbe1[1]</td>";
				$ztype = $subbe1[2];
			}
			else
			{
				print "<td></td>";
			}

			print "<td>$ztype</td>";
			if ( @subbe1 == 3 )
			{
				print "<td>$subbe1[2]</td>";
			}
			elsif ( @subbe1 == 4 )
			{
				print "<td>$subbe1[3]</td>";
			}
			elsif ( @subbe1 == 5 )
			{
				print "<td>$subbe1[4]</td>";
			}

			$nserv = $subbe2[1];
			$sv    = $zone;
			&createmenuserversfarmz( "normal", $farmname, $nserv );
			print "</tr>";
		}
	}

	print "</tbody></table>";
	print "</div>";

	print "</div>";
}

#end table

#################################################################
#BACKENDS:
##################################################################

print "
 <script type=\"text/javascript\">
  function chRType(oSelect)
  {
    oSelect.form.action.value=\"editfarm-editserver\";
    oSelect.form.submit();
  }
  function chRTypeAdd(oSelect)
  {
    oSelect.form.action.value=\"editfarm-addserver\";
    oSelect.form.submit();
  }
  </script>
  ";

print "
<script>
	\$(document).ready(function() {
    \$('.dns-table').DataTable( {
        \"bJQueryUI\": true,     
        \"sPaginationType\": \"full_numbers\",
		\"aLengthMenu\": [
			[10, 25, 50, 100, 200, -1],
			[10, 25, 50, 100, 200, \"All\"]
		],
		\"iDisplayLength\": 10,
        \"aaSorting\": []
    });
} );
</script>
";

print "
<script>
jQuery(document).ready(function () {
	\$(\"#resource-type\").change(function() {
		if (\$(this).val() == \"DYNA\") {
			\$(\"#resourcerdata-input\").hide().prop(\"disabled\", \"true\");
			\$(\"#resourcerdata-select\").show().prop(\"disabled\", \"false\");
		} else {
			\$(\"#resourcerdata-input\").show().prop(\"disabled\", \"false\");
			\$(\"#resourcerdata-select\").hide().prop(\"disabled\", \"true\");
		}
	});
});
</script>
";

1;

