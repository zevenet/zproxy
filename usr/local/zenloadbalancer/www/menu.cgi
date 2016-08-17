###############################################################################
###############################################################################
#
#     Zen Load Balancer Software License
#     This file is part of the Zen Load Balancer software package.
#
#     Copyright (C) 2014 SOFINTEL IT ENGINEERING SL, based in Sevilla (Spain)
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

use Sys::Hostname;

my $host     = hostname();
my $now      = ctime();
my $username = username();

if (    $id eq "2-1"
	 || $id eq "2-2"
	 || $id eq "2-3"
	 || ( $id eq "1-2" && $action eq "managefarm" ) )
{
	$manageiconclass     = "";
	$monitoringiconclass = "active";
	$settingsiconclass   = "";
	$abouticonclass      = "";
}
elsif (    $id eq "3-1"
		|| $id eq "3-2"
		|| $id eq "3-3"
		|| $id eq "3-4"
		|| $id eq "3-5" )
{
	$manageiconclass     = "";
	$monitoringiconclass = "";
	$settingsiconclass   = "active";
	$abouticonclass      = "";
}

elsif (    $id eq ""
		|| $id eq "1-1"
		|| $id eq "1-2"
		|| $id eq "1-3" && $action ne "managefarm" )
{
	$manageiconclass     = "active";
	$monitoringiconclass = "";
	$settingsiconclass   = "";
	$abouticonclass      = "";
}

elsif (    $id eq "4-1"
		|| $id eq "4-2" )
{
	$manageiconclass     = "";
	$monitoringiconclass = "";
	$settingsiconclass   = "";
	$abouticonclass      = "active";
}
else
{
	$manageiconclass     = "";
	$monitoringiconclass = "";
	$settingsiconclass   = "";
	$abouticonclass      = "";
}

my $pluginsmenulist =
  ${ &plugins::getPluginsMenuList( ) };

print "
  <div class=\"top-bar\">
    <ul id=\"nav\">
      <li id=\"user-panel\">
        <img src=\"img/nav/usr-avatar.png\" id=\"usr-avatar\" alt=\"Zen Load Balancer user\" />
        <div id=\"usr-info\">
          <p id=\"usr-name\">Welcome back, $username. <a href=\"index.cgi?action=logout\">Log out</a></p>
		  <p id=\"usr-host\">Host: $host, Version: $version</p>
		  <p id=\"usr-date\">Date: $now</p>
        </div>
      </li>
      <li>
        <ul id=\"top-nav\">
          <li class=\"nav-item\">
            <a href=\"#\"><i class=\"fa fa-cogs $manageiconclass\"></i><p>Manage</p></a>
		    <ul class=\"sub-nav\">
				<li><a href=\"index.cgi?id=1-1\">Global View</a></li>
				<li><a href=\"index.cgi?id=1-2\">Farms</a></li>
				<li><a href=\"index.cgi?id=1-3\">Certificates</a></li>
            </ul>
          </li>
          <li class=\"nav-item\">
            <a href=\"#\"><i class=\"fa fa-dashboard $monitoringiconclass\"></i><p>Monitoring</p></a>
		    <ul class=\"sub-nav\">
              <li><a href=\"index.cgi?id=2-1\">Graphs</a></li>
              <li><a href=\"index.cgi?id=2-2\">Conns stats</a></li>
              <li><a href=\"index.cgi?id=2-3\">Logs</a></li>
            </ul>
          </li>
          <li class=\"nav-item\">
            <a href=\"#\"><i class=\"fa fa-sliders $settingsiconclass\"></i><p>Settings</p></a>
		    <ul class=\"sub-nav\">
              <li><a href=\"index.cgi?id=3-1\">Server</a></li>
              <li><a href=\"index.cgi?id=3-2\">Interfaces</a></li>
		  	<li><a href=\"index.cgi?id=3-3\">Cluster</a></li>
		  	<li><a href=\"index.cgi?id=3-4\">Users</a></li>
		  	<li><a href=\"index.cgi?id=3-5\">Backup</a></li>
            </ul>
          </li>
          $pluginsmenulist
          <li class=\"nav-item\">
			<a href=\"#\"><i class=\"fa fa-life-buoy $abouticonclass\"></i><p>About</p></a>
			<ul class=\"sub-nav\">
			<li>
				<form action=\"index.cgi\" method=post name=\"changepage41\"> 
					<input type=\"hidden\" name=\"id\" value=\"4-1\"/> 					
					<a href=\"javascript:document.changepage41.submit()\">License</a>
				</form>				
			</li>
			<li>
				<form action=\"index.cgi\" method=post name=\"changepage42\"> 
					<input type=\"hidden\" name=\"id\" value=\"4-2\"/> 					
					<a href=\"javascript:document.changepage42.submit()\">Certificate Key</a>
				</form>				
			</li>	
			</ul>
			</li>
        </ul>
      </li>
    </ul>
  </div>
  ";

print "
	<script type=\"text/javascript\">
	function submitform()
	{
	  document.myform.submit();
	}
	</script>
";

1;
