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
use File::Basename;
use Time::localtime;
use Sys::Hostname;
my $host = hostname();

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
print "<div class=\"grid_6\"><h1>Settings :: Backup</h1></div>\n";

####################################
# CLUSTER STATUS
####################################
&getClusterStatus();

if ( $action eq "apply" )
{
	&successmsg(
		"Backup will be decompressed and Zen Load Balancer will be restarted, Zen Cluster node could switch..."
	);
	my @eject = `$tar -xvzf $backupdir$file -C /`;
	&logfile( "Restoring backup $backupdir$file" );
	&logfile( "unpacking files: @eject" );
	my @eject = `/etc/init.d/zenloadbalancer restart 2> /dev/null`;
	if ( $? == 0 )
	{
		&successmsg( "Backup applied and Zen Load Balancer restarted..." );
	}
	else
	{
		&errormsg( "Problem restarting Zen Load Balancer service" );
	}

}

if ( $action eq "Create Backup" )
{
	if ( $name !~ /^$/ )
	{
		$name =~ s/\ //g;
		my @eject = `$zenbackup $name -c 2> /dev/null`;
		&successmsg( "Local system backup created <b>backup-$name.tar.gz</b>" );
	}

}

if ( $action eq "del" )
{
	$filepath = "$backupdir$file";
	if ( -e $filepath )
	{
		unlink ( $filepath );
		&successmsg( "Deleted backup file <b>$file</b>" );

	}
	else
	{
		&errormsg( "File <b>$file</b> not found" );
	}

}

#if ($action eq "Upload Backup")
#	{
#$CGI::POST_MAX = 1024 * 5000;
#my $query = new CGI;
#my $safe_filename_characters = "a-zA-Z0-9_.-";
#my $upload_dir = "$backupdir";
#my $filex = $query->param("file");
#my $upload_filehandle = $query->upload("fileName");
#
#open ( UPLOADFILE, ">$backupdir$file" ) or die "$!";
#binmode UPLOADFILE;
#
#while ( <$upload_filehandle> )
#{
# print UPLOADFILE;
#}
#
#close UPLOADFILE;
#	}

print "
               <div class=\"box grid_6\">
                 <div class=\"box-head\">
                       <span class=\"box-icon-24 fugue-24 plus\"></span>         
                       <h2>Create backup</h2>
                 </div>
                 <div class=\"box-content global-farm\">
       ";

print "<form method=\"post\" action=\"index.cgi\">";
print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
print "<div class=\"form-row\">\n";
print "<p class=\"form-label\"><b>Description name</b></p>\n";
print
  "<div class=\"form-item\"><input type=\"text\" name=\"name\" value=\"$lhost\" class=\"fixedwidth\"> <input type=\"submit\" value=\"Create Backup\" name=\"action\" class=\"button grey\"></div>\n";
print "</div>\n";
print "</form>";

print "</div></div>";
print "<div class=\"clear\"></div>";

#table
print "
               <div class=\"box grid_12\">
                 <div class=\"box-head\">
                       <span class=\"box-icon-24 fugue-24 disk-black\"></span>   
                       <h2>Backups table</h2>
                 </div>
                 <div class=\"box-content no-pad\">
                 <ul class=\"table-toolbar\">
            <li>";

&upload();

print "</li>
          </ul>
       ";

print "<table id=\"backups-table\" class=\"display\">";
print "<thead>";

print "<tr>";
print "<th>Description name</th>";
print "<th>Date</th>";
print "<th>Host</th>";
print "<th>Action</th>";
print "</tr>";
print "</thead>";
print "<tbody>";

opendir ( DIR, "$backupdir" );
@files = grep ( /^backup.*/, readdir ( DIR ) );
closedir ( DIR );

foreach $file ( @files )
{
	print "<tr>";
	$filepath = "$backupdir$file";
	chomp ( $filepath );

	#print "filepath: $filepath";
	$datetime_string = ctime( stat ( $filepath )->mtime );
	print "<td>$file</td>";
	print "<td>$datetime_string</td>";
	print "<td>$host</td>";
	print "<td>";
	&createmenubackup( $file );
	print "</td>";
	print "</tr>";
}

print "</tbody>";
print "</table>";
print "</div></div>";

print "
<script>
\$(document).ready(function () {
    \$(\".open-dialog\").click(function () {
        \$(\"#dialog\").attr('src', \$(this).attr(\"href\"));
        \$(\"#dialog-container\").dialog({
            width: 350,
            height: 350,
            modal: true,
            close: function () {
                window.location.replace('index.cgi?id=3-5');
            }
        });
        return false;
    });
});
</script>

<script>
\$(document).ready(function() {
    \$('#backups-table').DataTable( {
        \"bJQueryUI\": true,     
        \"sPaginationType\": \"full_numbers\",
		\"aLengthMenu\": [
			[10, 25, 50, 100, 200, -1],
			[10, 25, 50, 100, 200, \"All\"]
		],
		\"iDisplayLength\": 10
    });
} );
</script>
";

