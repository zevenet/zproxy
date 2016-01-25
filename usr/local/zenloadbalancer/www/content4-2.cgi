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

use Tie::File;
$zlbcertfile = "$basedir/zlbcertfile.pem";

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
print "<div class=\"grid_6\"><h1>About :: Certificate Key</h1></div>\n";

####################################
# CLUSTER STATUS
####################################
&getClusterStatus();

#my $cgiurl = $ENV{SCRIPT_NAME}."?".$ENV{QUERY_STRING};

if ( $action eq "Delete ZLB Certificate Key" )
{
	unlink ( $zlbcertfile );
	&successmsg( "Certificate Key deleted..." );
}

# Print form if not a valid form
#if(!( ($pass || $newpass || $trustedpass) && check_valid_user() && verify_passwd()) ) {
##content 3-2 INI
print "<div class=\"box grid_12\">
                 <div class=\"box-head\">
                       <span class=\"box-icon-24 fugue-24 lock\"></span>         
                       <h2>Zen Load Balancer Certificate key</h2>
                 </div>
                 <div class=\"box-content certificate-key no-pad\">
		<ul class=\"table-toolbar\">
            <li><a href=\"uploadcertfile.cgi\" class=\"open-dialog\" title=\"Upload certificate\"><img src=\"img/icons/basic/up.png\" alt=\"Upload certificate\"> Upload certificate</a></li>
            <div id=\"dialog-container\" style=\"display: none;\"><iframe id=\"dialog\" width=\"350\" height=\"350\"></iframe></div>
                       <li><a href=\"index.cgi?id=$id&action=Delete ZLB Certificate Key\" title=\"Delete certificate\"><img src=\"img/icons/basic/delete.png\" alt=\"Delete certificate\"> Delete</a></li>
          </ul>
	";

#print content
print "<div class=\"padding\">";

#Information for certificate Key
my $openssl_cmd = "$openssl x509 -in $zlbcertfile -noout -text 2>/dev/null";
my @run         = `$openssl_cmd`;
foreach $line ( @run )
{
	if ( $line =~ /:$/ && $line !~ /.*\:.*\:/ )
	{
		print "<h6>$line</h6>";
	}
	else
	{
		print "<p class=\"left-margin\">$line</p>";
	}
}

print "</div></div></div>";

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
                window.location.replace('index.cgi?id=4-2');
            }
        });
        return false;
    });
});
</script>
";

