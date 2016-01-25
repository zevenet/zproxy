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

use Tie::File;

print "
  <!--- CONTENT AREA -->
  <div class=\"content container_12\">
";

####################################
# CLUSTER INFO
####################################
&getClusterInfo();

##################################
# BREADCRUMB
##################################
print "<div class=\"grid_6\"><h1>About :: License</h1></div>\n";

###################################
# CLUSTER STATUS
###################################
&getClusterStatus();

print "
               <div class=\"box grid_12\">
                 <div class=\"box-head\">
                       <span class=\"box-icon-24 fugue-24 document-text\"></span>        
                       <h2>Zen Load Balancer license</h2>
                 </div>
                 <div class=\"box-content\">
       ";

#print content
print "<div class=\"aligncenter\">";
print "<form method=\"post\" action=\"index.cgi\">";

#print "<input type=\"hidden\" name=\"id\" value=\"$id\"
print
  "<textarea  name=\"license\" cols=\"85\" rows=\"20\" align=\"center\" readonly>";
open FR, "/usr/local/zenloadbalancer/license.txt";
while ( <FR> )
{
	print "$_";
}
close FR;
print "</textarea></div>";
print
  "<div class=\"aligncenter\"><p><b>*If you use this program, you accept the GNU/LGPL license</b></p></div>";

print "</form>";
print "</div>";
print "</div>";
print "</div>";
print "</div>";

