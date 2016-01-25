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

###################################
# BREADCRUMB
###################################
print "<div class=\"grid_6\"><h1>Settings :: Users Management</h1></div>\n";

####################################
# CLUSTER STATUS
####################################
&getClusterStatus();

#Variables
$zapistatus = &getZAPI( "status",  "" );
$zapikey    = &getZAPI( "keyzapi", "" );

#set admin password
if ( $action eq "changepass-admin" )
{

	if ( defined ( $pass ) && defined ( $newpass ) && defined ( $trustedpass ) )
	{

		# Empty strings
		if ( !( $pass ) )
		{
			&errormsg( "Fill in Current password field" );
		}
		elsif ( !( $newpass ) )
		{
			&errormsg( "Fill in New password field" );
		}
		elsif ( !( $trustedpass ) )
		{
			&errormsg( "Fill in Verify password field" );
		}
		elsif ( !( &checkValidUser( "root", $pass ) ) )
		{
			&errormsg( "Invalid current password" );
		}
		elsif ( !( &verifyPasswd( $newpass, $trustedpass ) ) )
		{
			&errormsg( "Invalid password verification" );
		}
		else
		{
			&changePassword( "root", $newpass, $trustedpass );
			&successmsg( "Successfully root password changed" );
		}
	}
	else
	{
		&errormsg(
			   "Please insert current password, new password and verify password fields." );
	}
}

#set random key for zapi
if ( $action eq "Save Random Key" )
{

	#$random = &setZAPIKey(64);
	&setZAPI( "randomkey", "" );
	&successmsg( "Random Key has been stablished for ZAPI" );
}

#change zapi user
if ( $action eq "Apply" )
{

	#save custome key
	if ( $zapikey ne $keyzapi )
	{
		if ( $keyzapi eq "" and $zapistatus ne "false" )
		{
			&errormsg( "The given key cannot be blank, please insert a valid key" );
		}
		elsif ( $zapikey ne $keyzapi and $keyzapi ne "" )
		{
			&setZAPI( "key", $keyzapi );
			&successmsg( "The given key has been stablished for ZAPI" );
		}
	}

	#edit-enablepass
	if ( $enablepass ne $zapistatus )
	{
		if ( $enablepass eq "true" )
		{
			&setZAPI( "enable", "" );
			&successmsg( "User zapi has been enabled" );
		}
		elsif ( $enablepass eq "" and $zapistatus eq "true" )
		{
			&setZAPI( "disable", "" );
			&successmsg( "User zapi has been disabled" );
		}
	}

	#set ZAPI user password
	if ( $newpass ne "" && $trustedpass ne "" )
	{
		if ( &verifyPasswd( $newpass, $trustedpass ) )
		{
			&changePassword( "zapi", $newpass, $trustedpass );
			&successmsg( "Successfully zapi user password changed" );
		}
		else
		{
			&errormsg( "Zapi user passwords don't match or empty" );
		}
	}
}

#
# Change Root Password
#
print "
               <div class=\"box grid_5\">
                 <div class=\"box-head\">
                       <span class=\"box-icon-24 fugue-24 user\"></span>         
                       <h2>Change root password</h2>
                 </div>
                 <div class=\"box-content\">
	";

# Print form
print "<form method=\"POST\" action=\"index.cgi\">\n
        <input type=\"hidden\" name=\"id\" value=\"3-4\">\n
		<input type=\"hidden\" name=\"action\" value=\"changepass-admin\">\n
		<div class=\"form-row\">\n
		<p class=\"form-label\"><b>Current password</b></p>\n
		<div class=\"form-item\"><input type=\"password\" name=\"pass\" class=\"fixedwidth\"></div>\n
		</div>\n
		<div class=\"form-row\">\n
		<p class=\"form-label\"><b>New password:</b></p>\n
		<div class=\"form-item\"><input type=\"password\" name=\"newpass\" class=\"fixedwidth\"></div>\n
		</div>\n
		<div class=\"form-row\">\n
		<p class=\"form-label\"><b>Verify password:</b></p>\n
		<div class=\"form-item\"><input type=\"password\" name=\"trustedpass\" class=\"fixedwidth\"></div>\n
		</div>\n
		<br>\n
		<input type=\"submit\" value=\"Apply\" name=\"action\" class=\"button normal grey\">\n
		</form>
		</div></div>
		<div class=\"clear\"></div>
	";

print "<br class=\"cl\">";

#
# Change Zapi User
#
print "<div class=\"box grid_5\">";
print " <div class=\"box-head\">";
print "		<span class=\"box-icon-24 fugue-24 user\"></span> ";
print "         <h2>Change zapi user</h2>";
print " </div>";
print "         <div class=\"box-content\">";

$zapistatus = &getZAPI( "status",  "" );
$zapikey    = &getZAPI( "keyzapi", "" );

# Enable Zapi User
print "		<div class=\"form-row\">\n";
print "         <form method=\"post\" action=\"index.cgi\">";
print "             <input type=\"hidden\" name=\"id\" value=\"3-4\">";

# print
# "                 <input type=\"hidden\" name=\"action\" value=\"edit-changezapiuser\">";
print "		<div class=\"form-row\">\n";
print "             <p class=\"form-label\"><b>Enable zapi user:</b> </p>";
if ( $zapistatus eq "true" )
{
	print
	  "<p class=\"form-label\"><input type=\"checkbox\" checked name=\"enablepass\" value=\"true\" class=\"fixedwidth\"> </p>";
}
else
{
	print
	  "<p class=\"form-label\"> <input type=\"checkbox\"  name=\"enablepass\" value=\"true\"> </p>";
}
print "		</div>";
print "                 <br><br>";

# print "                 <p class=\"form-label\">&nbsp;</p>\n";
# print "                 <div class=\"form-row\">\n";
# print
# "                 <p class=\"form-item\"><input type=\"submit\" value=\"Apply\" name=\"button\" class=\"button normal grey\"></p>";
# print "                 </div>";
print "                 <div style=\"clear:both;\"></div>";

# print "         </form>";
print "</div>";

if ( $zapistatus eq "true" )
{
	# New password
	print "			<div class=\"form-row\">\n";
	print "				<div class=\"form-row\">\n";
	print "                 <p class=\"form-label\"><b>New password:</b> </p>";
	print "                 <input type=\"hidden\" name=\"id\" value=\"3-4\">";

	# print "				<input type=\"hidden\" name=\"action\" value=\"changepass-zapi\">";
	print
	  "                 <div class=\"form-item\"><input type=\"password\"  name=\"newpass\" class=\"fixedwidth\"></div>";
	print "				</div>";
	print "             <div style=\"clear:both;\"></div>";
	print "			<div class=\"form-row\">\n";
	print "                 <p class=\"form-label\"><b>Verify password:</b> </p>";
	print
	  "                 	<p class=\"form-item\"><input type=\"password\" name=\"trustedpass\" class=\"fixedwidth\"></p>";

	# print "			</div>";
	# print "			<p class=\"form-label\">&nbsp;</p>\n";
	# print "			<div class=\"form-row\">\n";
	print "			</div>";
	print "			</div>";
	print "                 <br><br>";

	# Key
	print "		<div class=\"form-row\">\n";
	print "			<div class=\"form-row\">\n";
	print "                 <p class=\"form-label\"><b>Key:</b> </p>";
	print "                 <input type=\"hidden\" name=\"id\" value=\"3-4\">";

#print "                <input type=\"hidden\" name=\"action\" value=\"edit-randomkeyzapi\">";
	print
	  "             <div class=\"form-item\"><input type=\"text\"  name=\"keyzapi\" value=\"$zapikey\" class=\"fixedwidth\"></div>";
	print "			</div>";

	print "			<div class=\"form-row\">\n";
	print "				<p class=\"form-label\">&nbsp;</p>\n";

# print "           <p class=\"form-item\"><input type=\"submit\" value=\"Save Custom Key\" name=\"action\" class=\"button normal grey\"></p>";

	print "			</div>";
	print "			</div>";
	print "         <div style=\"clear:both;\"></div>";

	# Buttons
	# print "                 <br><br>";
	print
	  "                 <input type=\"submit\" value=\"Apply\" name=\"action\" class=\"button normal grey\">";
	print
	  "                 <input type=\"submit\" value=\"Save Random Key\" name=\"action\" class=\"button normal grey\">";
	print "             <div style=\"clear:both;\"></div>";
	print "         </form>";
}
else
{
	print
	  "                 <input type=\"submit\" value=\"Apply\" name=\"action\" class=\"button normal grey\">";
	print "         </form>";
}

print "         </div>";
print " </div>";
print "</div>";

#content 3-4 END
print "
        <br><br><br>
        </div>
    <!--Content END-->
  </div>
</div>
</div>
</div>
";

