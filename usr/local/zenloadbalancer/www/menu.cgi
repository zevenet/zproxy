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



print "

<div class=\"menu\">
<link rel=\"stylesheet\" href=\"css/menu_style.css\" type=\"text/css\" />

		<ul>
			<li><a href=\"#\" id=\"current\"><img src=\"../img/icons/small/images.png\"> Manage</a>
				<ul>
					<li><a href=\"index.cgi?id=1-1\"><img src=\"../img/icons/small/find.png\"> Global View</a></li>
					<li><a href=\"index.cgi?id=1-2\"><img src=\"../img/icons/small/farm.png\"> Farms</a></li>
					<li><a href=\"index.cgi?id=1-3\"><img src=\"../img/icons/small/rosette.png\"> Certificates</a></li>
			   	</ul>
		  	</li>
			<li><a href=\"#\" id=\"current\"><img src=\"../img/icons/small/find.png\"> Monitoring</a>
				<ul>
					<li><a href=\"index.cgi?id=2-1\"><img src=\"../img/icons/small/chart_bar.png\"> Graphs</a></li>
					<li><a href=\"index.cgi?id=2-2\"><img src=\"../img/icons/small/page_lightning.png\"> Logs</a></li>
				</ul>
			
			</li>
			<li><a href=\"#\" id=\"current\"><img src=\"../img/icons/small/table_multiple.png\"> Settings</a>
                		<ul>
                			<li><a href=\"index.cgi?id=3-1\"><img src=\"../img/icons/small/application_edit.png\"> Server</a></li>
                			<li><a href=\"index.cgi?id=3-2\"><img src=\"../img/icons/small/plugin.png\"> Interfaces</a></li>
                			<li><a href=\"index.cgi?id=3-3\"><img src=\"../img/icons/small/databases.png\"> Cluster</a></li>
                			<li><a href=\"index.cgi?id=3-4\"><img src=\"../img/icons/small/user.png\"> Change Password</a></li>
                			<li><a href=\"index.cgi?id=3-5\"><img src=\"../img/icons/small/drive_disk.png\"> Backup</a></li>
                		</ul>
          		</li>
			<li><a href=\"#\"><img src=\"../img/icons/small/comment.png\"> About</a>
				<ul>
                			<li><a href=\"index.cgi?id=4-1\"><img src=\"../img/icons/small/page_2.png\"> License</a></li>


				</ul>
			</li>
		</ul>
</div>
";
