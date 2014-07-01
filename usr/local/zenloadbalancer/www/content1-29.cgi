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

#STATUS of a L4xNAT Farm

#if ($viewtableclients eq ""){ $viewtableclients = "no";}
#if ($viewtableconn eq ""){ $viewtableconn = "no";}

# Real Server Table
#my $args = "Nn";
my @args;
my $nattype = &getFarmNatType($farmname);
#if ($nattype eq "dnat"){
#	$args = "D$args";
#}
my $proto = &getFarmProto($farmname);
#$args = "$args -p $proto";

my @netstat = &getNetstatNat($args);
$fvip = &getFarmVip("vip",$farmname);

my @content = &getFarmBackendStatusCtl($farmname);
my @backends = &getFarmBackendsStatus($farmname,@content);

#print "content: @content<br>";
#print "backends: @backends<br>";

my $backendsize = @backends;
my $activebackends = 0;
#my $activesessions = 0;
foreach (@backends){
	my @backends_data = split(";",$_);
	if ($backends_data[3] eq "up"){
		$activebackends++;
	}
}

&refreshstats();
print "<br>";

print "<div class=\"box-header\">Real servers status<font size=1>&nbsp;&nbsp;&nbsp; $backendsize servers, $activebackends active </font></div>";
print "<div class=\"box table\"><table cellspacing=\"0\">\n";
print "<thead>\n";
print "<tr><td>Server</td><td>Address</td><td>Port(s)</td><td>Status</td><td>Pending Conns</td><td>Established Conns</td><td>Closed Conns</td><td>Weight</td>";
print "</thead>\n";
print "<tbody>";

my $index = 0;
foreach (@backends){
	my @backends_data = split(";",$_);
	$activesessions = $activesessions+$backends_data[6];
	my $ip_backend = $backends_data[0];
	my $port_backend = $backends_data[1];
	print "<tr>";
	print "<td> $index </td> ";
	print "<td> $ip_backend </td> ";
	print "<td> $port_backend </td> ";
	if ($backends_data[3] eq "maintenance"){
		print "<td><img src=\"img/icons/small/warning.png\" title=\"up\"></td> ";
	}elsif ($backends_data[3] eq "up"){
		print "<td><img src=\"img/icons/small/start.png\" title=\"up\"></td> ";
	} elsif ($backends_data[3] eq "fgDOWN"){
		print "<td><img src=\"img/icons/small/disconnect.png\" title=\"FarmGuardian down\"></td> ";	
	}else{
		print "<td><img src=\"img/icons/small/stop.png\" title=\"down\"></td> ";
	}
#	my @synnetstatback1 = &getNetstatFilter("$proto","\.\*SYN\.\*|UNREPLIED"," src=.* dst=.* .* src=$ip_backend dst=$fvip ","",@netstat);
	my @synnetstatback1 = &getNetstatFilter("$proto","","\.* SYN\.* src=\.* dst=$fvip \.* src=$ip_backend \.*","",@netstat);
	my $npend = @synnetstatback1;
#	my @synnetstatback2 = &getNetstatFilter("$proto","UNREPLIED"," src=$fvip dst=$ip_backend ","",@netstat);
#	my $npend = @synnetstatback1+@synnetstatback2;
	print "<td>$npend</td>";
	@stabnetstatback = &getNetstatFilter("$proto","","\.* ESTABLISHED src=\.* dst=$fvip \.* src=$ip_backend \.*","",@netstat);
	my $nestab = @stabnetstatback;
	print "<td>$nestab</td>";
	@timewnetstatback = &getNetstatFilter("$proto","","\.*\_WAIT src=\.* dst=$fvip \.* src=$ip_backend \.*","",@netstat);
#	@timewnetstatback = &getNetstatFilter("","","\.*WAIT \.*","",@netstat);
	my $ntimew = @timewnetstatback;
	print "<td>$ntimew</td>";
	print "<td> $backends_data[2] </td>";
	print "</tr>";
}

print "</tbody>";
print "</table>";
print "</div>";


print "<!--END MANAGE-->";

print "<div id=\"page-header\"></div>";
print "<form method=\"get\" action=\"index.cgi\">";
print "<input type=\"hidden\" value=\"1-2\" name=\"id\">";
print "<input type=\"submit\" value=\"Cancel\" name=\"action\" class=\"button small\">";
print "</form>";
print "<div id=\"page-header\"></div>";

#print "@run";
