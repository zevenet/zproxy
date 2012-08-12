#This cgi is part of Zen Load Balancer, is a Web GUI integrated with binary systems that
#create Highly Effective Bandwidth Managemen
#Copyright (C) 2010  Emilio Campos Martin / Laura Garcia Liebana
#
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You can read license.txt file for more information.

#Created by Emilio Campos Martin
#File that create the Zen Load Balancer GUI

### EDIT L4xNAT FARM ###

if ($farmname =~ /^$/){
	&errormsg("Unknown farm name");
	$action = "";
}

$ftype = &getFarmType($farmname);
if ($ftype ne "l4txnat" && $ftype ne "l4uxnat"){
	&errormsg("Invalid farm type");
	$action = "";
}

$fstate = &getFarmStatus($farmname);
if ($fstate eq "down"){
	&errormsg("The farm $farmname is down, to edit please start it up");
	$action = "";
}

#maintenance mode for servers
#if ($action eq "editfarm-maintenance"){
#        &setFarmBackendMaintenance($farmname,$id_server);
#        if ($? eq 0){
#                &successmsg("Enabled maintenance mode for backend $id_server");
#        }
#}

#disable maintenance mode for servers
#if ($action eq "editfarm-nomaintenance"){
#        &setFarmBackendNoMaintenance($farmname,$id_server);
#        if ($? eq 0){
#                &successmsg("Disabled maintenance mode for backend");
#        }
#}

#change Farm's name
if ($action eq "editfarm-Name"){

        #Check if farmname has correct characters (letters, numbers and hyphens)
        my $farmnameok = &checkFarmnameOK($newfarmname);
        #Check the farm's name change
        if ("$newfarmname" eq "$farmname"){
                &errormsg("The new farm's name \"$newfarmname\" is the same as the old farm's name \"$farmname\": nothing to do");
        }elsif ($farmnameok ne 0){
                &errormsg("Farm name isn't OK, only allowed numbers letters and hyphens");
	} else {
		#Check if the new farm's name alredy exists
		$newffile = &getFarmFile($newfarmname);
		if ($newffile != -1){
			&errormsg("The farm $newfarmname already exists, try another name");
		} else {
			#Change farm name
			$fnchange = &setNewFarmName($farmname,$newfarmname);
			if ($fnchange != -1){
				&successmsg("The Farm $farmname is now renamed to $newfarmname, restart the farm to apply the changes.");
				$farmname=$newfarmname;
			} else {
				&errormsg("The name of the Farm $farmname can't be modified, delete the farm and create a new one.");
			}
		}
	}
}

if ($action eq "editfarm-changevipvipp"){
        if ( &ismport($vipp) eq "false"){
                &errormsg("Invalid Virtual Port $vipp value, it must be a valid multiport value");
                $error = 1;
        }
#        if (&checkport($vip,$vipp) eq "true"){
#                &errormsg("Virtual Port $vipp in Virtual IP $vip is in use, select another port");
#                $error = 1;
#        }
        if ($error == 0){
                $status = &setFarmVirtualConf($vip,$vipp,$farmname);
                if ($status != -1){
#                	&setFarmRestart($farmname);
			&runFarmStop($farmname,"false");
			&runFarmStart($farmname,"false");
                        &successmsg("Virtual IP and Virtual Port has been modified, the $farmname farm need be restarted");
                } else {
                        &errormsg("It's not possible to change the $farmname farm virtual IP and port");
                }
        }
}


if ($action eq "editfarm-restart"){
	&runFarmStop($farmname,"true");
	$status = &runFarmStart($farmname,"true");
	if ($status == 0){
		&successmsg("The $farmname farm has been restarted");
	} else {
		&errormsg("The $farmname farm hasn't been restarted");
	}
}


#delete server
if ($action eq "editfarm-deleteserver"){
	$status = &runFarmServerDelete($id_server,$farmname);
	if ($status != -1){
#		&setFarmRestart($farmname);
		&runFarmStop($farmname,"false");
		&runFarmStart($farmname,"false");
		&successmsg("The real server with ID $id_server of the $farmname farm has been deleted");
	} else {
		&errormsg("It's not possible to delete the real server with ID $id_server of the $farmname farm");
	}
}

#save server
if ($action eq "editfarm-saveserver"){
	$error = 0;
	if (&ipisok($rip_server) eq "false" || $rip_server =~ /^$/){
		&errormsg("Invalid real server IP value, please insert a valid value");
		$error = 1;
	}
	#if ($port_server =~ /^$/) {
	#	&errormsg("Invalid port for real server, it can't be blank");
	#	$error = 1;
	#}
	if (&checkmport($port_server) eq "true") {
		my $port = &getFarmVip("vipp",$fname);
		if ($port_server == $port){
			$port_server = "";
		} else {
			&errormsg("Invalid multiple ports for backend, please insert a single port number or blank");
			$error = 1;
		}
	}

        if ($error == 0){
		$status = &setFarmServer($id_server,$rip_server,$port_server,$max_server,$weight_server,$priority_server,$timeout_server,$farmname);
		if ($status != -1){
#			&setFarmRestart($farmname);
			&runFarmStop($farmname,"false");
			&runFarmStart($farmname,"false");
			&successmsg("The real server with ID $id_server and IP $rip_server of the $farmname farm has been modified");
		} else {
			&errormsg("It's not possible to modify the real server with ID $id_server and IP $rip_server of the $farmname farm");
		}
	}
}

#session type
if ($action eq "editfarm-typesession"){
	$status = &setFarmSessionType($session,$farmname);
	if ($status == 0){
#		&setFarmRestart($farmname);
		&runFarmStop($farmname,"false");
		&runFarmStart($farmname,"false");
		&successmsg("The session type for $farmname farm has been modified");
	} else {
		&errormsg("It's not possible to change the $farmname farm session type");
	}
}

#change the load balance algorithm;
if ($action eq "editfarm-algorithm"){
	$error = 0;
	if ($lb =~ /^$/){
		&errormsg("Invalid algorithm value");
		$error = 1;
	}
	if ($error == 0){
		$status = &setFarmAlgorithm($lb,$farmname);
		if ($status != -1){
#			$action="editfarm";
			&runFarmStop($farmname,"false");
			&runFarmStart($farmname,"false");
			&successmsg("The algorithm for $farmname Farm is modified");
		} else {
			&errormsg("It's not possible to change the farm $farmname algorithm");
		}
	}
}

#nat type
if ($action eq "editfarm-nattype"){
	$status = &setFarmNatType($nattype,$farmname);
	if ($status == 0){
		&runFarmStop($farmname,"false");
		&runFarmStart($farmname,"false");
		&successmsg("The NAT type for $farmname farm has been modified");
	} else {
		&errormsg("It's not possible to change the $farmname farm NAT type");
	}
}

#TTL
if ($action eq "editfarm-TTL"){
	$error = 0;
	if (&isnumber($param) eq "false"){
		&errormsg("Invalid client timeout $param value, it must be a numeric value");
		$error = 1;
	}
	if ($error == 0){
		$status = &setFarmMaxClientTime(0,$param,$farmname);
		if ($status == 0){
			&setFarmRestart($farmname);
			&successmsg("The sessions TTL for $farmname farm has been modified");
		} else {
			&errormsg("It's not possible to change the $farmname farm sessions TTL");
		}
	}
}

#check if the farm need a restart
#if (-e "/tmp/$farmname.lock"){
#	&tipmsg("There're changes that need to be applied, stop and start farm to apply them!");
#}

#global info for a farm
print "<div class=\"container_12\">";
print "<div class=\"grid_12\">";

#paint a form to the global configuration
print "<div class=\"box-header\">Edit $farmname Farm global parameters</div>";
print "<div class=\"box stats\">";
print "<div class=\"row\">";

#print "<div style=\"float:left;\">";

#Change farm's name form
print "<b>Farm's name</b><font size=1> *service will be restarted</font><b>.</b><br>";
print "<form method=\"get\" action=\"index.cgi\">";
print "<input type=\"hidden\" name=\"action\" value=\"editfarm-Name\">";
print "<input type=\"text\" value=\"$farmname\" size=\"25\" name=\"newfarmname\">";
print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
print "<input type=\"hidden\" name=\"done\" value=\"yes\">";
print "<input type=\"hidden\" name=\"id_server\" value=\"@l_serv[0]\">";
print "<input type=\"submit\" value=\"Modify\" name=\"buttom\" class=\"button small\"></form>";
print "<br>";

#type session
print "<b>NAT type </b><font size=\"1\">*the service will be restarted</font><b>.</b>";
my $nattype = &getFarmNatType($farmname);
if ($nattype == -1){
	$nattype = "dnat";
}
print "<form method=\"get\" action=\"index.cgi\">";
print "<input type=\"hidden\" name=\"action\" value=\"editfarm-nattype\">";
print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
print "<select  name=\"nattype\">";
if ($nattype eq "nat"){	
	print "<option value=\"nat\" selected=\"selected\">NAT</option>";
} else {
	print "<option value=\"nat\">NAT</option>";
}
if ($nattype eq "dnat"){
	print "<option value=\"dnat\" selected=\"selected\">DNAT</option>";
} else {
	print "<option value=\"dnat\">DNAT</option>";
}
#if ($nattype eq "snat"){
#	print "<option value=\"snat\" selected=\"selected\">SNAT</option>";
#} else {
#	print "<option value=\"snat\">SNAT</option>";
#}
print "</select>";
print "<input type=\"submit\" value=\"Modify\" name=\"buttom\" class=\"button small\"></form>";
print "<br>";

#print "<b>Backend response timeout secs.<br>";
#$timeout = &getFarmTimeout($farmname);
#print "<form method=\"get\" action=\"index.cgi\">";
#print "<input type=\"hidden\" name=\"action\" value=\"editfarm-Timeout-http\">";
#print "<input type=\"text\" value=\"$timeout\" size=\"4\" name=\"param\">";
#print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
#print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
#print "<input type=\"submit\" value=\"Modify\" name=\"buttom\" class=\"button small\"></form>";
#print "<br>";

#Timeout for client
#print "<b>Timeout request from clients.</b>";
#$client = &getFarmClientTimeout($farmname);
#print "<form method=\"get\" action=\"index.cgi\">";
#print "<input type=\"hidden\" name=\"action\" value=\"editfarm-Client\">";
#print "<input type=\"text\" value=\"$client\" size=\"4\" name=\"param\">";
#print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
#print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
#print "<input type=\"submit\" value=\"Modify\" name=\"buttom\" class=\"button small\"></form>";

#algorithm
#print "<b>Load Balance Algorithm.</b>";
#$lbalg = &getFarmAlgorithm($farmname);
#if ($lbalg == -1){
#	$lbalg = "weight";
#}
#print "<form method=\"get\" action=\"index.cgi\">";
#print "<input type=\"hidden\" name=\"action\" value=\"editfarm-algorithm\">";
#print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
#print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
#print "<select  name=\"lb\">";
#if ($lbalg eq "weight"){
#	print "<option value=\"weight\" selected=\"selected\">Weight: connection linear dispatching by weight</option>";
#} else {
#	print "<option value=\"weight\">Weight: connection linear dispatching by weight</option>";
#}
##if ($lbalg eq "prio"){	
##	print "<option value=\"prio\" disabled >Priority: connections always to the most prio avaliable</option>";
##} else {
#	print "<option value=\"prio\" disabled >Priority: connections always to the most prio avaliable</option>";
##}
#print "</select>";
#print "<input type=\"submit\" value=\"Modify\" name=\"buttom\" class=\"button small\"></form>";
#print "<br>";

#type session
print "<b>Persistence mode </b><font size=\"1\">*the service will be restarted</font><b>.</b>";
$session = &getFarmSessionType($farmname);
if ($session == -1){
	$session = "none";
}
print "<form method=\"get\" action=\"index.cgi\">";
print "<input type=\"hidden\" name=\"action\" value=\"editfarm-typesession\">";
print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
print "<select  name=\"session\">";
print "<option value=\"none\">no persistence</option>";
if ($session eq "ip"){	
	print "<option value=\"ip\" selected=\"selected\">IP persistence</option>";
} else {
	print "<option value=\"ip\" >IP persistence</option>";
}
#if ($session eq "connection"){
#	print "<option value=\"connection\" selected=\"selected\">CONNECTION persistence</option>";
#} else {
#	print "<option value=\"connection\">CONNECTION persistence</option>";
#}
print "</select>";
print "<input type=\"submit\" value=\"Modify\" name=\"buttom\" class=\"button small\"></form>";
print "<br>";

#print "<b>Frequency to check resurrected backends.</b>";
#$alive = &getFarmBlacklistTime($farmname);
#print "<form method=\"get\" action=\"index.cgi\">";
#print "<input type=\"hidden\" name=\"action\" value=\"editfarm-Alive\">";
#print "<input type=\"text\" value=\"$alive\" size=\"4\" name=\"param\">";
#print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
#print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
#print "<input type=\"submit\" value=\"Modify\" name=\"buttom\" class=\"button small\"></form>";
#print "<br>";

#session TTL
#if ($session ne "nothing" && $session){
print "<b>Source IP Address Persistence time to limit </b><font size=\"1\">*in seconds, only for IP persistence</font><b>.</b>";
@ttl = &getFarmMaxClientTime($farmname);
print "<form method=\"get\" action=\"index.cgi\">";
print "<input type=\"hidden\" name=\"action\" value=\"editfarm-TTL\">";
print "<input type=\"text\" value=\"@ttl[0]\" size=\"4\" name=\"param\">";
print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
print "<input type=\"submit\" value=\"Modify\" name=\"buttom\" class=\"button small\"></form>";
#}


print "<br>";
print "<b>Farm Virtual IP and Virtual port(s) </b><font size=\"1\">*the service will be restarted</font><b>.</b>";
$vip = &getFarmVip("vip",$farmname);
$vport = &getFarmVip("vipp",$farmname);
print "<br>";
@listinterfaces = &listallips();
$clrip = &clrip();
print "<form method=\"get\" action=\"index.cgi\">";
print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
print "<input type=\"hidden\" name=\"action\" value=\"editfarm-changevipvipp\">";
print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
print "<select name=\"vip\">";
foreach $ip(@listinterfaces){
	if ($ip !~ $clrip){
		if ($vip eq $ip){
			print "<option value=\"$ip\" selected=\"selected\">$ip</option>";
		} else {
			print "<option value=\"$ip\">$ip</option>";
		}
	}
}
print "</select>";
print " <input type=\"text\" value=\"$vport\" size=\"20\" name=\"vipp\">";
print "&nbsp;<img src=\"img/icons/small/help.png\" title=\"Specify a port, several ports between `,', ports range between `:', or all ports with `*'. Also a combination of them should work.\"</img>&nbsp;";
print "<input type=\"submit\" value=\"Modify\" name=\"buttom\" class=\"button small\"></form>";


#print "</div><div style=\"align:right; margin-left: 50%; \">";


#print "</div>";
#print "</td></tr></table>";

####end form for global parameters

print "</div><br>";
print "</div>";
print "<div id=\"page-header\"></div>";

##paint the server configuration
my @run = &getFarmServers($farmname);

print "<a name=\"backendlist\"></a>";

print "<div class=\"box-header\">Edit real IP servers configuration </div>";
print "<div class=\"box table\">";
print "  <table cellspacing=\"0\">";
print "    <thead>";
print "    <tr>";
print "		<td>Server</td>";
print "		<td>Address</td>";
print "		<td>Port</td>";
print "		<td>Weight</td>";
#print "		<td>Priority</td>";
print "		<td>Actions</td>";
print "    </tr>";
print "    </thead>";
print "	   <tbody>";

$id_serverchange = $id_server;
my $sindex = 0;
#my @laifaces = &listActiveInterfaces();
foreach $l_servers(@run){
	my @l_serv = split("\;",$l_servers);
#	if (@l_serv[2] ne "0.0.0.0"){
		$isrs="true";
		if ($action eq "editfarm-editserver" && $id_serverchange eq @l_serv[0]){
			print "<form method=\"get\" action=\"index.cgi\#backendlist\">";
			print "<tr class=\"selected\">";
			#id server 
			print "<td>@l_serv[0]</td>";
			print "<input type=\"hidden\" name=\"id_server\" value=\"@l_serv[0]\">";
			#real server ip
			print "<td><input type=\"text\" size=\"12\"  name=\"rip_server\" value=\"@l_serv[1]\"> </td>";
			#local interface
			if (@l_serv[2] eq ""){
				print "<td><input type=\"text\" size=\"12\"  name=\"port_server\" value=\"$vport\"></td>";
			} else {
        			print "<td><input type=\"text\" size=\"12\"  name=\"port_server\" value=\"@l_serv[2]\"> </td>";
			}
			#Weight
			print "<td><input type=\"text\" size=\"4\"  name=\"weight_server\" value=\"@l_serv[4]\"> </td>";
			#Priority
			#print "<td><input type=\"text\" size=\"4\"  name=\"priority_server\" value=\"@l_serv[5]\"> </td>";
			&createmenuserversfarm("edit",$farmname,@l_serv[0]);
		} else {
			print "<form method=\"get\" action=\"index.cgi\#backendlist\">";
			print "<tr>";
			print "<td>@l_serv[0]</td>";
			print "<td>@l_serv[1]</td>";
			if (@l_serv[2] eq ""){
				print "<td>$vport</td>";
			} else {
        			print "<td>@l_serv[2]</td>";
			}
			print "<td>@l_serv[4]</td>";
			#print "<td>@l_serv[5]</td>";
			&createmenuserversfarm("normal",$farmname,@l_serv[0]);
		}
		print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
		print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
		print "<input type=\"hidden\" name=\"id_server\" value=\"@l_serv[0]\">";
		print "</form>";
		print "</tr>";
		$sindex = @l_serv[0];
#	}
}

## New backend form
$sindex = $sindex +1;
if ($action eq "editfarm-addserver"){
	$action ="editfarm";
	$isrs="true";
	print "<form method=\"get\" action=\"index.cgi\#backendlist\">";
        print "<tr class=\"selected\">";
        #id server
        print "<td>$sindex</td>";
        print "<input type=\"hidden\" name=\"id_server\" value=\"$sindex\">";
        #real server ip
        print "<td><input type=\"text\" size=\"12\"  name=\"rip_server\" value=\"\"> </td>";
	# port only editable if the farm isnt multiport
	if (@l_serv[2] eq ""){
		print "<td><input type=\"text\" size=\"12\"  name=\"port_server\" value=\"$vport\" ></td>";
	} else {
        	print "<td><input type=\"text\" size=\"12\"  name=\"port_server\" value=\"@l_serv[2]\"> </td>";
	}
        #Weight
        print "<td><input type=\"text\" size=\"4\"  name=\"weight_server\" value=\"\"></td>";
	#Priority
	#print "<td><input type=\"text\" size=\"4\"  name=\"priority_server\" value=\"\"> </td>";
	&createmenuserversfarm("add",$farmname,$sindex);
	print "<input type=\"hidden\" name=\"id\" value=\"$id\">";	
        print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
       	print "<input type=\"hidden\" name=\"id_server\" value=\"$sindex\">";
       	print "</form>";
       	print "</tr>";
}

print "<tr>";
print "<td  colspan=\"4\"></td>";
print "<form method=\"get\" action=\"index.cgi\#backendlist\">";
&createmenuserversfarm("new",$farmname,"");
print "<input type=\"hidden\" name=\"id\" value=\"$id\">";	
print "<input type=\"hidden\" name=\"farmname\" value=\"$farmname\">";
print "<input type=\"hidden\" name=\"id_server\" value=\"\">";
print "</form>";
print "</tr>";

print "</tbody>";
print "</table>";
print "</div>";
print "</div>";

print "<div id=\"page-header\"></div>";
print "<input type=\"submit\" value=\"Cancel\" name=\"action\" class=\"button small\">";
print "<div id=\"page-header\"></div>";
print "</form>";
print "</div>";

