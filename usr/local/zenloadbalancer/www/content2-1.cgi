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

#########################
#BREADCRUMB
########################
print "<div class=\"grid_6\"><h1>Monitoring :: Graphs</h1></div>\n";

####################################
# CLUSTER STATUS
####################################
&getClusterStatus();

if ( $action && $action ne "Go!" )
{
	print "
               <div class=\"box grid_12\">
                 <div class=\"box-head\">
                       <span class=\"box-icon-24 fugue-24 system-monitor\"></span>       
                       <h2>Daily, weekly, monthly and yearly graphs</h2>
                 </div>
               <div class=\"box-content\">
	";

	print
	  '<center><div class="row"><h6>Daily graph:</h6></div><img src="data:image/png;base64,'
	  . &printGraph( $action, "d" )
	  . '"/></center><br><br>';
	print
	  '<center><div class="row"><h6>Weekly graph:</h6></div><img src="data:image/png;base64,'
	  . &printGraph( $action, "w" )
	  . '"/></center><br><br>';
	print
	  '<center><div class="row"><h6>Monthly graph:</h6></div><img src="data:image/png;base64,'
	  . &printGraph( $action, "m" )
	  . '"/></center><br><br>';
	print
	  '<center><div class="row"><h6>Yearly graph:</h6></div><img src="data:image/png;base64,'
	  . &printGraph( $action, "y" )
	  . '"/></center><br><br>';
	print "<form method=\"post\" action=\"index.cgi\">";
	print "<p class=\"aligncenter\">";
	print "<input type=\"hidden\" name=\"id\" value=\"2-1\">";
	print
	  "<input type=\"submit\" value=\"Return\" name=\"return\" class=\"button grey\">";
	print "</p>";
	print "</form>";
	print "</div></div>";
}
else
{
	if ( $graphtype eq "System" )
	{
		@graphselected[0] = "";
		@graphselected[1] = "selected=\"selected\"";
		@graphselected[2] = "";
		@graphselected[3] = "";
	}
	elsif ( $graphtype eq "Network" )
	{
		@graphselected[0] = "";
		@graphselected[1] = "";
		@graphselected[2] = "selected=\"selected\"";
		@graphselected[3] = "";
	}
	elsif ( $graphtype eq "Farm" )
	{
		@graphselected[0] = "";
		@graphselected[1] = "";
		@graphselected[2] = "";
		@graphselected[3] = "selected=\"selected\"";
	}
	else
	{
		@graphselected[0] = "";
		@graphselected[1] = "";
		@graphselected[2] = "";
		@graphselected[3] = "";
	}

	print "
               <div class=\"box grid_12\">
                 <div class=\"box-head\">
                       <span class=\"box-icon-24 fugue-24 system-monitor\"></span>       
                       <h2>Daily graphs</h2>
                 </div>
                 <div class=\"box-content\">
	";
	print "<form method=\"post\" action=\"index.cgi\">";
	print "<div class=\"aligncenter\">\n";
	print "<select name=\"graphtype\">\n";
	print "<option value=\"All\" @graphselected[0]>Show all Graphs</option>";
	print
	  "<option value=\"System\" @graphselected[1]>Show system type Graphs</option>";
	print
	  "<option value=\"Network\" @graphselected[2]>Show network traffic type Graphs</option>";
	print "<option value=\"Farm\" @graphselected[3]>Show farm type Graphs</option>";
	print "</select>";
	print "<input type=\"hidden\" name=\"id\" value=\"$id\"> ";
	print
	  "<input type=\"submit\" value=\"Go!\" name=\"action\" class=\"button grey\">";

	print
	  "<p align=\"center\">Click on graph to see daily, weekly, monthly and yearly graphs.</p></div>";

	print "<div class=\"onlyclear\">&nbsp;</div>";
	print "</form>";

	if ( $graphtype =~ /^$/ || $graphtype eq "All" )
	{
		@gtypes = ( System, Network, Farm );
		foreach $gtype ( @gtypes )
		{
			@graphlist = &getGraphs2Show( $gtype );
			foreach $graph ( @graphlist )
			{
				print "<form method=\"post\" action=\"index.cgi\">";
				print "<input type=\"hidden\" name=\"id\" value=\"$id\"> ";
				print "<input type=\"hidden\" name=\"action\" value=\"$graph\"> ";
				print "<center>";
				print
				  "<button type=\"submit\" class=\"noborder\" title=\"Click on graph to see daily, weekly, monthly and yearly graphs\">";
				print '<img src="data:image/png;base64,' . &printGraph( $graph, "d" ) . '"/>';
				print "</button></center><br><br>";
				print "</form>";

# print
# "<a href=\"?id=$id&action=$graph\" title=\"Click on graph to see daily, weekly, monthly and yearly graphs\"><center>";
# print '<img src="data:image/png;base64,' . &printGraph( $graph, "d" ) . '"/>';
# print "</a></center><br><br>";
			}
		}
	}
	else
	{
		@graphlist = &getGraphs2Show( $graphtype );
		foreach $graph ( @graphlist )
		{
			print "<form method=\"post\" action=\"index.cgi\">";
			print "<input type=\"hidden\" name=\"id\" value=\"$id\"> ";
			print "<input type=\"hidden\" name=\"action\" value=\"$graph\"> ";
			print "<center>";
			print
			  "<button type=\"submit\" class=\"noborder\" title=\"Click on graph to see daily, weekly, monthly and yearly graphs\">";
			print '<img src="data:image/png;base64,' . &printGraph( $graph, "d" ) . '"/>';
			print "</button></center><br><br>";
			print "</form>";

# print
# "<a href=\"?id=$id&action=$graph\" title=\"Click on graph to see daily, weekly, monthly and yearly graphs\"><center>";
# print '<img src="data:image/png;base64,' . &printGraph( $graph, "d" ) . '"/>';
# print "</a></center><br><br>";
		}
	}
	print "</div></div></div>";
}

