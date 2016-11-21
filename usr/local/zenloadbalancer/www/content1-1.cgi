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
  <!--- CONTENT AREA -->
  <div class=\"content container_12\">
";

####################################
# CLUSTER INFO
####################################
&getClusterInfo();

####################################
# BREADCRUMB
####################################
print "<div class=\"grid_6\"><h1>Manage :: Global views</h1></div>";

####################################
# CLUSTER STATUS
####################################
&getClusterStatus();

#graph
use GD::3DBarGrapher qw(creategraph);

#memory values
my @data_mem = &getMemStats();

#memory graph
$description = "img/graphs/graphmem.jpg";

&graphs( $description, @data_mem );

#load values
my @data_load = &getLoadStats();

#load graph
$description = "img/graphs/graphload.jpg";

&graphs( $description, @data_load );

#network interfaces
my @data_net = &getNetworkStats();

#network graph
$description = "img/graphs/graphnet.jpg";
&graphs( $description, @data_net );

#

####################################
# ZLB COMMERCIAL INFORMATION
####################################

my $systemuuid = `/usr/sbin/dmidecode | grep UUID | awk '{print \$2}'`;
chomp ( $systemuuid );
print "
    <div class=\"box grid_12\">
      <div class=\"box-head\">
           <span class=\"box-icon-24 fugue-24 globe\"></span>
        <h2>ZEVENET Professional Products &amp; Services</h2>
      </div>
      <div class=\"box-content no-pad\">
         <table class=\"display\">
          <thead>
            <tr>
              <th width=\"33%\">Professional Services</th>
              <th width=\"33%\">Professional Products</th>
              <th width=\"33%\">News</th>
            </tr>
          </thead>
          <tbody>
             <tr>
              <td><div id=\"support\"></div></td>
              <td><div id=\"products\"></div></td>
              <td><div id=\"news\"></div></td>
            </tr>
           </tbody>
         </table>
      </div>
    </div>
";

####################################
# GLOBAL FARMS INFORMATION
####################################

print "
       <div class=\"box grid_12\">
           <span class=\"box-icon-24 fugue-24 counter\"></span>
         <div class=\"box-head\">
        <h2>Global Farms information</h2>
      </div>
      <div class=\"box-content no-pad\">
               <table id=\"global-farms-information-table\" class=\"display\">
          <thead>
            <tr>
              <th>Farm</th>
              <th>Profile</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
";

my @files = &getFarmList();

my $rowCounter = 1;
foreach $file ( @files )
{

	if ( $rowCounter % 2 eq 0 )
	{
		print "<tr class=\"even gradeA\">";
	}
	else
	{
		print "<tr class=\"odd gradeA\">";
	}
	$rowCounter++;

	$farmname = &getFarmName( $file );
	my $type = &getFarmType( $farmname );
	if ( $type !~ /datalink/ && $type !~ /l4xnat/ )
	{
		$pid = &getFarmPid( $farmname );
		chomp ( $pid );
	}
	else
	{
		$pid = "-";
	}
	my @eject;
	$pc = "-";
	print "<td>$farmname</td><td>$type</td>";

	$status = &getFarmStatus( $farmname );
	if ( $status ne "up" )
	{
		print
		  "<td class=\"aligncenter\"><img src=\"img/icons/small/stop.png\" title=\"down\"></td>";
	}
	else
	{
		print
		  "<td class=\"aligncenter\"><img src=\"img/icons/small/start.png\" title=\"up\"></td>";
	}

	print "</tr>";
}

print "</tbody></table></div></div><div class=\"clear\"></div>";

####################################
# MEM INFORMATION
####################################

print " <div class=\"box grid_4\">
         <div class=\"box-head\">
           <span class=\"box-icon-24 fugue-24 system-monitor\"></span>
        <h2>Mem information (mb)</h2>
      </div>
      <div class=\"box-content no-pad\" style=\"min-height: 0px; display: block;\">
               <table class=\"display\">
          <thead>
            <tr>
              <th>$data_mem[0][0]</th>
              <!--<th>$data_mem[1][0]</th>-->
              <th>$data_mem[2][0]</th>
              <th>$data_mem[3][0]</th>
              <th>$data_mem[4][0]</th>
                         <th>$data_mem[5][0]</th>
                         <!--<th>$data_mem[6][0]</th>-->
                         <th>$data_mem[7][0]</th>
            </tr>
          </thead>
          <tbody>
";

print
  "<tr><td class=\"aligncenter\">$data_mem[0][1]</td><!--<td class=\"aligncenter\">$data_mem[1][1]</td>--><td class=\"aligncenter\">$data_mem[2][1]</td><td class=\"aligncenter\">$data_mem[3][1]</td><td class=\"aligncenter\">$data_mem[4][1]</td><td class=\"aligncenter\">$data_mem[5][1]</td><!--<td class=\"aligncenter\">$data_mem[6][1]</td>--><td class=\"aligncenter\">$data_mem[7][1]</td>    </tr>";

print "</tbody></table>
	<p class=\"aligncenter\"><img class=\"graph\" src=\"img/graphs/graphmem.jpg\"></p>
	</div></div>";

####################################
# LOAD INFORMATION
####################################

print "
       <div class=\"box grid_4\">
         <div class=\"box-head\">
           <span class=\"box-icon-24 fugue-24 system-monitor\"></span>
        <h2>Load information</h2>
      </div>
      <div class=\"box-content no-pad\" style=\"min-height: 0px; display: block;\">
               <table class=\"display\">
          <thead>
            <tr>
              <th>Load last minute</th>
              <th>Load Last 5 minutes</th>
              <th>Load Last 15 minutes</th>
            </tr>
          </thead>
";

print "<tbody>
	<tr><td class=\"aligncenter\">$data_load[0][1]</td><td class=\"aligncenter\">$data_load[1][1]</td><td class=\"aligncenter\">$data_load[2][1]</td></tr>
	</tbody></table>
	<p class=\"aligncenter\"><img class=\"graph\" src=\"img/graphs/graphload.jpg\"></p>
	</div></div>";

####################################
# NETWORK TRAFFIC INFORMATION
####################################
print "
       <div class=\"box grid_4\">
         <div class=\"box-head\">
           <span class=\"box-icon-24 fugue-24 system-monitor\"></span>
        <h2>Network traffic interfaces (mb)</h2>
      </div>
      <div class=\"box-content no-pad\" style=\"min-height: 0px; display: block;\">
               <table class=\"display\">
          <thead>
            <tr>
              <th>Interface</th>
              <th>Input</th>
              <th>Output</th>
            </tr>
          </thead>
          <tbody>
";

my $indice = @data_net;
for ( my $i = 0 ; $i < $indice - 1 ; $i = $i + 2 )
{
	my @ifname = split ( ' ', $data_net[$i][0] );
	print "<tr>
		<td class=\"aligncenter\">$ifname[0]</td><td class=\"aligncenter\">$data_net[$i][1]</td><td class=\"aligncenter\">$data_net[$i+1][1]</td>\n
		</tr>";
}

print "</tbody></table>
	<p class=\"aligncenter\"><img class=\"graph\" src=\"img/graphs/graphnet.jpg\"></p>
	</div>
	</div>";

print "<br class=\"cl\" ></div>";

print "
<script>
\$(document).ready(function(){
  var container0 = \$('#support');
  var container1 = \$('#products');
  var container2 = \$('#news');
  var fixedsupport = '<a href=\"http://www.zenloadbalancer.com/support-programs/?zlb_gui\" target=\"_blank\"><i class=\"fa fa-support fa-2x\"></i>&nbsp;&nbsp;Get Support for Zen Community and Enterprise Edition</a><br><a href=\"https://www.sofintel.net/support?zlb_gui\" target=\"_blank\"><i class=\"fa fa-users fa-2x\"></i>&nbsp;&nbsp;Already have Professional Support? Open a Support Request here</a><br>';
  var fixedproducts = '<a href=\"http://www.zenloadbalancer.com/products/?zlb_gui\" target=\"_blank\"><i class=\"fa fa-tasks fa-2x\"></i>&nbsp;&nbsp;Get more from Zen with Enterprise Edition Appliances</a><br><a href=\"http://ecommerce.sofintel.net/ssl/ssl-certificate.aspx\" target=\"_blank\"><i class=\"fa fa-certificate fa-2x\"></i>&nbsp;&nbsp;Get your best Zen-Ready SSL Certificates at the best price *</a><br><br><font size=1>&nbsp;&nbsp;&nbsp;* We are a Starfield Technologies supplier&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</font><img src=\"/img/img_verified_logo.gif\" title=\"Verified by Starfield Technologies\">';
  var fixednews = 'ZLB News<br><a href=\"http://www.zenloadbalancer.com/news/?zlb_gui\" target=\"_blank\"><i class=\"fa fa-info-circle fa-2x\"></i>&nbsp;&nbsp;Visit the news page on our WEB site</a><br>';
  var url = '$url';
  window.connect = 'false';
  \$.getJSON(url + '?callback=?&key=$key&host=$hostname&ver=$version',
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

print "
<script>
\$(document).ready(function() {
    \$('#global-farms-information-table').DataTable( {
        \"bJQueryUI\": true,     
        \"sPaginationType\": \"full_numbers\",
		\"aLengthMenu\": [
			[10, 25, 50, 100, 200, -1],
			[10, 25, 50, 100, 200, \"All\"]
		],
		\"iDisplayLength\": 10
    });
} );
</script>";
