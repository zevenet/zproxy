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

use File::stat;
use Time::localtime;

print "
  <!--- CONTENT AREA -->
  <div class=\"content container_12\">
";

####################################
# CLUSTER INFO
####################################
&getClusterInfo();

####################################
#BREADCRUMB
####################################
print "<div class=\"grid_6\"><h1>Monitoring :: Logs</h1></div>\n";

####################################
# CLUSTER STATUS
####################################
&getClusterStatus();

print "
               <div class=\"box grid_12\">
                 <div class=\"box-head\">
                       <span class=\"box-icon-24 fugue-24 magnifier\"></span>    
                       <h2>System logs</h2>
                 </div>
                 <div class=\"box-content monitoring-logs\">
       ";

# Print form
#search farm files
opendir ( DIR, $logdir );
my @files = grep ( /(.*\.log|syslog|messages)$/, readdir ( DIR ) );
closedir ( DIR );

print "<form method=\"post\" action=\"index.cgi\">";
print "<input type=\"hidden\" name=\"id\" value=\"2-3\">";

foreach my $file ( @files )
{
	print "<h6>Log: $file</h6>";
	my $filepath = "$logdir/$file";
	print
	  "<div class=\"form-row2\"><p><input type=\"radio\" name=\"filelog\" value=\"$filepath\"> ";
	my $datetime_string = ctime( stat ( $filepath )->mtime );
	print "$filepath - $datetime_string</p></div>\n";
	my @filen = split ( "\.log", $file );

	#all files with same name:
	opendir ( DIR, $logdir );
	my @filesgz = grep ( /$filen[0].*gz$/, readdir ( DIR ) );
	closedir ( DIR );
	@filesgz = sort ( @filesgz );
	foreach my $filegz ( @filesgz )
	{
		my $filepath        = "$logdir/$filegz";
		my $datetime_string = ctime( stat ( $filepath )->mtime );
		print
		  "<div class=\"form-row2\"><p><input type=\"radio\" name=\"filelog\" value=\"$filepath\"> ";
		print "$filepath - $datetime_string</p></div>";
	}
}

print "<div class=\"spacer\">&nbsp;</div>";
print
  "<p><b>Tail the last</b> <input type=\"text\" value=\"100\" name=\"nlines\" size=\"5\"> <b>lines of selected file</b> ";
print
  "<input type=\"submit\" value=\"See logs\" name=\"action\" class=\"button grey\"></p>";
print "</form>";

print "<div class=\"spacer\">&nbsp;</div>";

if ( $action eq "See logs" && $nlines !~ /^$/ && $filelog !~ /^$/ )
{
	if ( -e $filelog )
	{
		if ( $nlines =~ m/^\d+$/ )
		{
			print "<hr></hr>";
			print "<h6>Last $nlines lines from log file $filelog:</h6>";
			print "<div class=\"form-row2\">";
			my @eject;
			
			if ( $filelog =~ /gz$/ )
			{
				@eject = `$zcat $filelog | $tail -$nlines`;
			}
			else
			{
				@eject = `$tail -$nlines $filelog`;
			}
			
			foreach my $line ( @eject )
			{
				print "<p>$line</p>";
			}
			
			print "</div>\n";
			print "<div class=\"form-row2\"><form method=\"post\" action=\"index.cgi\">";
			print "<input type=\"hidden\" name=\"id\" value=\"2-3\">";
			print
			  "<input type=\"submit\" value=\"Cancel\" name=\"action\" class=\"button grey\">";
			print "</form></div>";
		}
		else
		{
			&errormsg( "The number of lines you want to tail must be a number" );
		}

	}
	else
	{
		&errormsg( "We can not find the file $filelog" );
	}
}

print "</div></div></div>";

