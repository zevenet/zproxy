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

#STATUS of a HTTP(S) farm

if ($viewtableclients eq ""){ $viewtableclients = "no";}
#if ($viewtableconn eq ""){ $viewtableconn = "no";}

# Real Server Table
my @netstat = &getNetstat("atnp");
$fvip = &getFarmVip("vip",$farmname);
$fpid = &getFarmPid($farmname);
# Pound second process
$fpid = $fpid+1;

my @content = &getFarmBackendStatusCtl($farmname);
my @backends = &getFarmBackendsStatus($farmname,@content);

my $backendsize = @backends;
my $activebackends = 0;
my $activesessions = 0;
foreach (@backends){
	my @backends_data = split("\t",$_);
	if ($backends_data[3] eq "up"){
		$activebackends++;
	}
}

print "<div class=\"box-header\">Real servers status<font size=1>&nbsp;&nbsp;&nbsp; $backendsize servers, $activebackends active </font></div>";
print "<div class=\"box table\"><table cellspacing=\"0\">\n";
print "<thead>\n";
print "<tr><td>Server</td><td>Address</td><td>Port</td><td>Status</td><td>Pending Conns</td><td>Established Conns</td><td>Closed Conns</td><td>Sessions</td><td>Weight</td>";
print "</thead>\n";
print "<tbody>";

foreach (@backends){
	my @backends_data = split("\t",$_);
	$activesessions = $activesessions+$backends_data[6];
	print "<tr>";
	print "<td> $backends_data[0] </td> ";
	print "<td> $backends_data[1] </td> ";
	print "<td> $backends_data[2] </td> ";
	if ($backends_data[3] eq "maintenance"){
		print "<td><img src=\"img/icons/small/warning.png\" title=\"up\"></td> ";
	}elsif ($backends_data[3] eq "up"){
		print "<td><img src=\"img/icons/small/start.png\" title=\"up\"></td> ";
	}else{
		print "<td><img src=\"img/icons/small/stop.png\" title=\"down\"></td> ";
	}
	$ip_backend = $backends_data[1];
	$port_backend= $backends_data[2];
	@synnetstatback = &getNetstatFilter("tcp","\.\*SYN\.\*","$ip_backend\:$port_backend",$fpid,@netstat);
	$npend = @synnetstatback;
	print "<td>$npend</td>";
	@stabnetstatback = &getNetstatFilter("tcp","ESTABLISHED","$ip_backend\:$port_backend",$fpid,@netstat);
	$nestab = @stabnetstatback;
	print "<td>$nestab</td>";
	@timewnetstatback = &getNetstatFilter("tcp","\.\*\_WAIT\.\*","$ip_backend\:$port_backend",$fpid,@netstat);
	$ntimew = @timewnetstatback;
	print "<td>$ntimew</td>";
	print "<td> $backends_data[6] </td> ";
	print "<td> $backends_data[5] </td>";
	print "</tr>";
}

print "</tbody>";
print "</table>";
print "</div>";


# Client Sessions Table
print "<div class=\"box-header\">";

if ($viewtableclients eq "yes"){
	print "<a href=\"index.cgi?id=1-2&action=managefarm&farmname=$farmname&viewtableclients=no\" title=\"Minimize\"><img src=\"img/icons/small/bullet_toggle_minus.png\"></a>";
} else {
	print "<a href=\"index.cgi?id=1-2&action=managefarm&farmname=$farmname&viewtableclients=yes\" title=\"Maximize\"><img src=\"img/icons/small/bullet_toggle_plus.png\"></a>";
}

print "Client sessions status<font size=1>&nbsp;&nbsp;&nbsp; $activesessions active sessions</font></div>\n";

if ($viewtableclients eq "yes"){
	my @sessions = &getFarmBackendsClientsList($farmname,@content);

	print "<div class=\"box table\"><table cellspacing=\"0\">\n";
	print "<thead>\n";
	print "<tr><td>Client</td><td>Session ID</td><td>Server</td>";
	print "</thead>\n";
	print "<tbody>";

	foreach (@sessions){
		my @sessions_data = split("\t",$_);
		print "<tr>";
		print "<td> $sessions_data[0] </td> ";
		print "<td> $sessions_data[1] </td> ";
		print "<td> $sessions_data[2] </td> ";
		print "</tr>";
	}

	print "</tbody>";
	print "</table>";
	print "</div>";
}

print "<!--END MANAGE-->";

print "<div id=\"page-header\"></div>";
print "<form method=\"get\" action=\"index.cgi\">";
print "<input type=\"hidden\" value=\"1-2\" name=\"id\">";
print "<input type=\"submit\" value=\"Cancel\" name=\"action\" class=\"button small\">";
print "</form>";
print "<div id=\"page-header\"></div>";

#print "@run";
