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

my $basedir      = "/usr/local/zenloadbalancer/www";
my $modules_path = "$basedir/Modules";

print "
  <!--- CONTENT AREA -->
  <div class=\"content container_12\">
";

####################################
# CLUSTER INFO
####################################
&getClusterInfo();

# $action = plugin name
my $idModule = &plugins::getIdModule($id);
my $idSubModule = &plugins::getIdSubModule($id);
my $errMsg;


if ( $action =~ /^edit-/ )
{
	$errMsg = &plugins::triggerPlugin( $idModule, "control$idSubModule" );
	# report successful message
	if ( $errMsg =~ /^0-/ )
	{
		$errMsg =~ s/^0-//;
		&successmsg( $errMsg );
	}
	# no report message
	elsif ( $errMsg eq "" ) {} 
	# report error message
	else
	{
		$errMsg =~ s/^\d+-//;
		&errormsg( $errMsg );
	}
}


###############################
#BREADCRUMB
############################
print "<div class=\"grid_6\"><h1>$idModule :: $idSubModule</h1></div>\n";

####################################
# CLUSTER STATUS
####################################
&getClusterStatus();

##########################################
# DO STUFF
##########################################

my $content = &plugins::triggerPlugin( $idModule, "content$idSubModule" );
print "$content";
print "</div>";

print "<div><br><br><br></div>";
1;
