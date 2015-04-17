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


print "
    <!--Content INI-->
        <div id=\"page-content\">

                <!--Content Header INI-->
                        <h2>Manage::Global View</h2>
                <!--Content Header END-->";

	#&help("1");
#graph
use GD::3DBarGrapher qw(creategraph);
&logfile("loading default view");

#memory values
my @data_mem = &getMemStats();

#memory graph
$description = "img/graphs/graphmem.jpg";

&graphs($description,@data_mem);

#load values
my @data_load = &getLoadStats();

#load graph
$description = "img/graphs/graphload.jpg";

&graphs($description,@data_load);

#network interfaces
my @data_net = &getNetworkStats();
#network graph
$description = "img/graphs/graphnet.jpg";
&graphs($description,@data_net);
#

####################################
# ZLB COMMERCIAL INFORMATION
####################################

my $systemuuid = `/usr/sbin/dmidecode | grep UUID | awk '{print \$2}'`;
chomp($systemuuid); 
print "<div class=\"box-header\">Zen Load Balancer Professional Products &amp; Services</div>";
print " <div class=\"box table\">
	<table class=\"commerce\">
	<thead>";
print "		<tr>";
print "			<td>Professional Services</td><td>Professional Products</td>";
print "				<td>News</td>";
print "		</tr>";
print "</thead>";
print "<tbody>";
print "		<tr>";

print "			<td><div id=\"support\"></div></td>
			<td><div id=\"products\"></div></td>
			<td><div id=\"news\"></div></td>";
print "		</tr>";
print "</tbody>"; 	
print "</table></div>";
print "<br>";

####################################
# GLOBAL FARMS INFORMATION
####################################

print "<div class=\"box-header\">Global farms information</div>";
print "	<div class=\"box table\"> 
	<table>
	<thead>";
	#if ($temp){print "<td style=\"border: 0px\">Tempherature: <b>$temp</b></td>";}

	my @netstat = &getNetstatNat();
	my @nets= &getNetstatFilter("","ESTABLISHED","","",@netstat);
	push (@nets, &getNetstatFilter("udp","[^UNREPLIED]","","",@netstat));
	my $conn_max = @nets;

	@files = &getFarmList();

	print "<tr>";
	print "<td>Farm</td><td>Profile</td>";
	print "<td>%CPU</td><td>%MEM</b></td><td>Total connections on system</td>";
	print "</tr>";
	print "</thead>";
	print "<tbody>";
	foreach $file(@files){
		print "<tr>";
		$farmname = &getFarmName($file);
		my $type = &getFarmType($farmname);
		if ($type !~ /datalink/ && $type !~ /l4xnat/){
			$pid = &getFarmPid($farmname);
			chomp($pid);
		}
		else{
			$pid = "-";
		}
		my @eject;
		$pc = "-";
		if ($pid ne "-" && $pid ne "-1"){
			@eject = `top -p $pid -b -n 1`;
			$line = @eject[7];
			@line = split (" ",$line);
			if ($type =~ /http/){
				$pid2 = $pid + 1;
				@eject = `top -p $pid2 -b -n 1`;
				$line2 = @eject[7];
				@line2 = split (" ",$line2);
				@line[8] += @line2[8];
				@line[9] += @line2[9];
			}
		}
		else{
			@line[8]="-";
			@line[9]="-";
		}
		print "<td>$farmname</td><td>$type</td>";
		print "<td>@line[8]</td><td>@line[9]</td>";

		#if ($pid ne "-"){
			@conns=&getFarmEstConns($farmname,@netstat);
			$global_conns=@conns;
			$pc;
			if ($conn_max != 0){
				$pc = 100*$global_conns/$conn_max;
			} else {
				$pc = 0;
			}
			$pc = sprintf('%.0f', $pc);
			$vbar = 149*$pc/100;
			print "<td>";
			&progressbar("img/graphs/bar$farmname.png",$vbar);
			print "<img src=\"img/graphs/bar$farmname.png\">";
			print " $global_conns ($pc%)";
			print "</td>";
		#} else {
		#	print "<td>-</td>";
		#}
		print "</tr>";
	}

	print "</tbody></table></div>";
	print "<br>";

####################################
# MEM INFORMATION
####################################


print "<div class=\"box-header\">Memory (mb)</div>";
print " <div class=\"box table\">
        <table>
        <thead>";
print "<tr><td>$data_mem[0][0]</td><td>$data_mem[1][0]</td><td>$data_mem[2][0]</td><td>$data_mem[3][0]</td><td>$data_mem[4][0]</td><td>$data_mem[5][0]</td><td>$data_mem[6][0]</td><td>$data_mem[7][0]</td>    </tr>";
print "</thead>";


print "<tbody>";

print "<tr><td>$data_mem[0][1]</td><td>$data_mem[1][1]</td><td>$data_mem[2][1]</td><td>$data_mem[3][1]</td><td>$data_mem[4][1]</td><td>$data_mem[5][1]</td><td>$data_mem[6][1]</td><td>$data_mem[7][1]</td>    </tr>";
print "<tr style=\"background:none\;\"><td colspan=\"8\" style=\"text-align:center;\"><img src=\"img/graphs/graphmem.jpg\">  </tr>";

print "</tbody>";
print "</table>";
print "</div>";

print "<div class=\"box-header\">Load</div>";
print " <div class=\"box table\">
        <table>
        <thead>";
print "<tr><td colspan=3>Load last minute</td><td colspan=2>Load Last 5 minutes</td><td colspan=3>Load Last 15 minutes</td></tr>";
print "</thead>";
print "<tbody>";
print "<tr><td colspan=3>$data_load[0][1]</td><td colspan=2>$data_load[1][1]</td><td colspan=3>$data_load[2][1]</td></tr>";
print "<tr style=\"background:none;\"><td colspan=8 style=\"text-align:center;\"><img src=\"img/graphs/graphload.jpg\"></td></tr>";
print "</tbody>";

print "</table>";
print "</div>";

####################################
# NETWORK TRAFFIC INFORMATION
####################################


print "\n";
print "<div class=\"box-header\">Network traffic interfaces (mb) from ". &uptime ."</div>";
print " <div class=\"box table\">
        <table>
        <thead>";
print "<tr><td>Interface</td><td>Input</td><td>Output</td></tr>";
print "</thead>";
print "<tbody>";
my $indice = @data_net;
for my $i ( 0 .. @data_net-2 ){
                print "<tr>";
		print "<td>$data_net[$i][0]</td><td>$data_net[$i][1]</td><td>$data_net[$i+1][1]</td>\n";
                print "</tr>";
        }

print "<tr style=\"background:none;\"><td colspan=3 style=\"text-align:center;\"><img src=\"img/graphs/graphnet.jpg\"></td></tr>";

print "</tbody>";
print "</table>";
print "</div>";

print "<br class=\"cl\" ></div>\n";


print "<script src=\"https://code.jquery.com/jquery-latest.pack.js\"></script>
<script>
\$(document).ready(function(){
  var container0 = \$('#support');
  var container1 = \$('#products');
  var container2 = \$('#news');
  var fixedsupport = '<a href=\"http://www.zenloadbalancer.com/support-programs/?zlb_gui\" target=\"_blank\"><i class=\"fa fa-support fa-2x\"></i>&nbsp;&nbsp;Get Support for Zen Community and Enterprise Edition</a><br><a href=\"https://www.sofintel.net/support?zlb_gui\" target=\"_blank\"><i class=\"fa fa-users fa-2x\"></i>&nbsp;&nbsp;Already have Professional Support? Open a Support Request here</a><br>';
  var fixedproducts = '<a href=\"http://www.zenloadbalancer.com/products/?zlb_gui\" target=\"_blank\"><i class=\"fa fa-tasks fa-2x\"></i>&nbsp;&nbsp;Get more from Zen with Enterprise Edition Appliances</a><br><a href=\"http://ecommerce.sofintel.net/ssl/ssl-certificate.aspx\" target=\"_blank\"><i class=\"fa fa-certificate fa-2x\"></i>&nbsp;&nbsp;Get your best Zen-Ready SSL Certificates at the best price *</a><br><br><font size=1>&nbsp;&nbsp;&nbsp;* We are a Starfield Technologies supplier&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</font><<img src=\"/img/img_verified_logo.gif\" title=\"Verified by Starfield Technologies\">';
  var fixednews = 'ZLB News<br><a href=\"http://www.zenloadbalancer.com/news/?zlb_gui\" target=\"_blank\"><i class=\"fa fa-info-circle fa-2x\"></i>&nbsp;&nbsp;Visit the news page on our WEB site</a><br>';
  var url = '$url';
  window.connect = 'false';
  \$.getJSON(url + '?callback=?&uuid=$systemuuid',
     function(data){
	window.connect = 'true';
	if(data.results[0] == ''){
            	container0.html(fixedsupport);
	} 
	else{
		container0.html(data.results[0]);
	}
	if(data.results[1] == ''){
            	container1.html(fixedproducts);
	} 
	else{
		container1.html(data.results[1]);
	}
	if(data.results[2] == ''){
            	container2.html(fixednews);
	} 
	else{
		container2.html(data.results[2]);
	}
     }
  );
  if(window.connect == 'false'){
    container0.html(fixedsupport);
    container1.html(fixedproducts);
    container2.html(fixednews);
  }
});
</script>";
