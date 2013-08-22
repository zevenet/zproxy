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



#lateral menu
#print "
#<div id=\"page-wrapper\">
#  <div class=\"page\">
#";
#require "menu.cgi";

print "
    <!--Content INI-->
        <div id=\"page-content\">

                <!--Content Header INI-->
                        <h2>Monitoring::Graphs</h2>
                <!--Content Header END-->
";



#opendir(DIR, "$basedir$img_dir");
#@files = grep(/\_d.png$/,readdir(DIR));
#closedir(DIR);


if ($action && $action ne "Select Graph type"){
	print " <div class=\"container_12\">
          <div class=\"grid_12\">
          <div class=\"box-header\"> Graphs daily, weekly, monthly yearly </div>
          <div class=\"box stats\">
	";
	print '<center><img src="data:image/png;base64,'.&printGraph($action,"d").'"/></center><br><br>';
	print '<center><img src="data:image/png;base64,'.&printGraph($action,"w").'"/></center><br><br>';
	print '<center><img src="data:image/png;base64,'.&printGraph($action,"m").'"/></center><br><br>';
	print '<center><img src="data:image/png;base64,'.&printGraph($action,"y").'"/></center><br><br>';

	print "</div></div></div>";
        print "<form method=\"get\" action=\"index.cgi\">";
        print "<input type=\"hidden\" name=\"id\" value=\"2-1\">";
        print "<input type=\"submit\" value=\"Return\" name=\"return\" class=\"button small\">";
        print "</form>";
}
else{
	if ($graphtype eq "System"){
		@graphselected[0] = "";
		@graphselected[1] = "selected=\"selected\"";
		@graphselected[2] = "";
		@graphselected[3] = "";
	}
	elsif ($graphtype eq "Network"){
		@graphselected[0] = "";
		@graphselected[1] = "";
		@graphselected[2] = "selected=\"selected\"";
		@graphselected[3] = "";
	}
	elsif ($graphtype eq "Farm"){
		@graphselected[0] = "";
		@graphselected[1] = "";
		@graphselected[2] = "";
		@graphselected[3] = "selected=\"selected\"";
	}
	else{
		@graphselected[0] = "";
		@graphselected[1] = "";
		@graphselected[2] = "";
		@graphselected[3] = "";
	}
	print " <div class=\"container_12\">
          <div class=\"grid_12\">
          <div class=\"box-header\"> $graphtype Graphs daily </div>
          <div class=\"box stats\">
	";
	print "<form method=\"get\" action=\"index.cgi\">";
	print "<b>Select the type of Graphs to show</b>";
	print "<br>";	
	print "<select name=\"graphtype\">\n";
	print "<option value=\"All\" @graphselected[0]>Show all Graphs</option>";
	print "<option value=\"System\" @graphselected[1]>Show system type Graphs</option>";
	print "<option value=\"Network\" @graphselected[2]>Show network traffic type Graphs</option>";
	print "<option value=\"Farm\" @graphselected[3]>Show farm type Graphs</option>";
	print "</select>";
	print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
	print "<br>";	
	print "<br>";	
	print "<input type=\"submit\" value=\"Select Graph type\" name=\"action\" class=\"button small\">";
	print "</form>";
	print "<br>";
	if ($graphtype =~ /^$/ || $graphtype eq "All"){
		@gtypes=(System,Network,Farm);
		foreach $gtype(@gtypes){
			@graphlist = &getGraphs2Show($gtype);
			foreach $graph(@graphlist){
				print "<a href=\"?id=$id&action=$graph\"><center><img src=\"img/icons/small/zoom_in.png\" title=\"More info\"></a>";
				print '<img src="data:image/png;base64,'.&printGraph($graph,"d").'"/>';
				print "</center><br><br>";
			}
		}
	}
	else{
		@graphlist = &getGraphs2Show($graphtype);
		foreach $graph(@graphlist){
			print "<a href=\"?id=$id&action=$graph\"><center><img src=\"img/icons/small/zoom_in.png\" title=\"More info\"></a>";
			#print "<img src=\"img/graphs/$graph\"></center><br><br>";
			print '<img src="data:image/png;base64,'.&printGraph($graph,"d").'"/>';
			print "</center><br><br>";
		}
	}
	print "</div></div></div>";
}

print "<br class=\"cl\" >";

print "        </div>
    <!--Content END-->
  </div>
</div>
";
