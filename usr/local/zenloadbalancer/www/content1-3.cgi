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

#require
use File::stat;
use File::Basename;
use Time::localtime;
use Sys::Hostname;

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
###################################
print "<div class=\"grid_8\"><h1>Manage :: Certificates</h1></div>\n";

####################################
# CLUSTER STATUS
####################################
&getClusterStatus();

if ( $action eq "changecert" )
{
	$status = &setFarmCertificate( $certname, $farmname );
	if ( $status == 0 )
	{
		&successmsg(
			"Certificate is changed to $certname on farm $farmname, you need restart the farm to apply"
		);
		&setFarmRestart( $farmname );
	}
}

if ( $action eq "deletecert" )
{
	$status = &getFarmCertUsed( $certname );
	if ( &getFarmCertUsed( $certname ) == 0 )
	{
		&errormsg( "File can't be deleted because it's in use by a farm" );
	}
	else
	{
		&delCert( $certname );
		&successmsg( "File $file deleted" );
	}

}

if ( $action eq "Download_Cert" )
{
	&downloadCert( $certname );
}

if ( $action eq "Generate CSR" )
{
	$cert_name         = &getCleanBlanc( $cert_name );
	$cert_issuer       = &getCleanBlanc( $cert_issuer );
	$cert_fqdn         = &getCleanBlanc( $cert_fqdn );
	$cert_division     = &getCleanBlanc( $cert_division );
	$cert_organization = &getCleanBlanc( $cert_organization );
	$cert_locality     = &getCleanBlanc( $cert_locality );
	$cert_state        = &getCleanBlanc( $cert_state );
	$cert_country      = &getCleanBlanc( $cert_country );
	$cert_mail         = &getCleanBlanc( $cert_mail );
	if (    $cert_name =~ /^$/
		 || $cert_issuer =~ /^$/
		 || $cert_fqdn =~ /^$/
		 || $cert_division =~ /^$/
		 || $cert_organization =~ /^$/
		 || $cert_locality =~ /^$/
		 || $cert_state =~ /^$/
		 || $cert_country =~ /^$/
		 || $cert_mail =~ /^$/
		 || $cert_key =~ /^$/ )
	{
		&errormsg( "Fields can not be empty. Try again." );
		$action = "Show_Form";
	}
	elsif ( &checkFQDN( $cert_fqdn ) eq "false" )
	{
		&errormsg(
			"FQDN is not valid. It must be as these examples: domain.com, mail.domain.com, or *.domain.com. Try again."
		);
		$action = "Show_Form";
	}
	elsif ( $cert_name !~ /^[a-zA-Z0-9\-]*$/ )
	{
		&errormsg(
			"Certificate Name is not valid. Only letters, numbers and '-' chararter are allowed. Try again."
		);
		$action = "Show_Form";
	}
	else
	{
		&createCSR(
					$cert_name,     $cert_fqdn,     $cert_country,
					$cert_state,    $cert_locality, $cert_organization,
					$cert_division, $cert_mail,     $cert_key,
					""
		);
		&successmsg( "Cert $cert_name created" );
	}
}

my @files = &getCertFiles();

# table
print "
       <div class=\"box grid_12\">
         <div class=\"box-head\">
               <span class=\"box-icon-24 fugue-24 lock\"></span>         
               <h2>Certificates inventory</h2>
         </div>
         <div class=\"box-content no-pad\">
                 <ul class=\"table-toolbar\">";

print
  "<li><a href=\"index.cgi?id=$id&action=Show_Form\"><img src=\"img/icons/basic/plus.png\" alt=\"Create CSR\" title=\"Create CSR\">Create CSR</a></li>";

&uploadPEMCerts();

print
  "<li><a href=\"$buy_ssl\" target=\"_blank\"><img src=\"img/icons/small/cart_put.png\" alt=\"Buy SSL Certificate\" title=\"Buy SSL Certificate\">Buy SSL Certificate</a></li>";

print "</ul>
                 <table id=\"certificates-table\" class=\"display\">
                 <thead>
                       <tr>
                         <th>File</th>
                         <th>Type</th>
                         <th>Common Name</th>
                         <th>Issuer</th>
                         <th>Created on</th>
                         <th>Expire on</th>
                         <th>Actions</th>
                       </tr>
                 </thead>
                 <tbody>
";

foreach ( @files )
{
	$filepath       = "$configdir\/$_";
	$cert_type      = &getCertType( $filepath );
	$issuer         = &getCertIssuer( $filepath );
	$commonname     = &getCertCN( $filepath );
	$datecreation   = &getCertCreation( $filepath );
	$dateexpiration = &getCertExpiration( $filepath );

	print
	  "<tr><td>$_</td><td>$cert_type</td><td>$commonname</td><td>$issuer</td><td>$datecreation</td><td>$dateexpiration</td><td>";

	if ( $_ ne "zencert\.pem" )
	{
		&createMenuCert( $_ );
	}

	print "</td></tr>";
}

print "</tbody>";
print "</table>";
print "</div></div>";

# end table
if ( $action eq "View_Cert" )
{
	print "
       <div class=\"box grid_12\">
         <div class=\"box-head\">
               <span class=\"box-icon-24 fugue-24 lock\"></span>         
               <h2>View certificate $certname</h2>
         </div>
         <div class=\"box-content certificate-key\">";

	my @eject  = &getCertData( $certname );
	my $numrow = @eject;
	my $isinto = 0;
	foreach ( @eject )
	{
		if ( $_ =~ /^-----END CERTIFICATE/ )
		{

		}
		elsif ( $_ =~ /^-----BEGIN CERTIFICATE/ )
		{
			print
			  "<h6>Certificate content:<h6><textarea rows=\"23\" cols=\"68\" class=\"left-margin\" readonly>";
			$isinto = 1;
		}
		else
		{
			if ( $_ =~ /:$/ && $_ !~ /.*\:.*\:/ )
			{
				print "<h6>$_</h6>";
			}
			else
			{
				if ( $isinto == 1 )
				{
					print "$_";
				}
				else
				{
					print "<p class=\"left-margin\">$_</p>";
				}
			}

		}
	}
	print "</textarea>";
	print "         <form method=\"get\" action=\"index.cgi\">";
	print "         <input type=\"hidden\" name=\"id\" value=\"$id\">";
	print
	  "         <input type=\"submit\" value=\"Close\" name=\"button\" class=\"button grey left-margin\">";
	print "         </form>";

	print "</div></div>";
}

if ( $action eq "Show_Form" )
{

	print "
	<div class=\"box grid_12\">
		<div class=\"box-head\">
			<span class=\"box-icon-24 fugue-24 server\"></span>       
		<h2>CSR Generation</h2>
		</div>
	<div class=\"box-content global-farm no-pad\">";
	print "<form method=\"post\" action=\"index.cgi\">";
	print "<div class=\"grid_6\">\n";
	print "<div class=\"form-row\">\n";
	print
	  "<p class=\"form-label\"><b>Certificate Name.<b> Descriptive text, this name will be used in the future to identify this certificate.</p>\n";
	print
	  "<div class=\"form-item\"><input type=\"text\" value=\"$cert_name\" class=\"fixedwidth\" size=\"60\" name=\"cert_name\"></div>\n";
	print "</div>\n";
	print "<div class=\"form-row\">\n";
	print "<p class=\"form-label\"><b>Certificate Issuer</b></p>\n";
	print
	  "<div class=\"form-item\"><select name=\"cert_issuer\" class=\"fixedwidth\">\n";
	print "<option value=\"Sofintel\" >Sofintel - Starfield Tech. </option>\n";
	print "<option value=\"Others\" >Others </option>\n";
	print "</select></div>\n";
	print "</div>\n";
	print "<div class=\"form-row\">\n";
	print
	  "<p class=\"form-label\"><b>Common Name.</b> FQDN of the server. Example: domain.com, mail.domain.com, or *.domain.com.</p>\n";
	print
	  "<div class=\"form-item\"><input type=\"text\" value=\"$cert_fqdn\" class=\"fixedwidth\" size=\"60\" name=\"cert_fqdn\"></div>\n";
	print "</div>\n";
	print "<div class=\"form-row\">\n";
	print
	  "<p class=\"form-label\"><b>Division.</b> Your department; such as 'IT','Web', 'Office', etc.</p>\n";
	print
	  "<div class=\"form-item\"><input type=\"text\" value=\"$cert_division\" class=\"fixedwidth\" size=\"60\" name=\"cert_division\"></div>\n";
	print "</div>\n";
	print "<div class=\"form-row\">\n";
	print
	  "<p class=\"form-label\"><b>Organization.</b> The full legal name of your organization/company (ex.: Sofintel IT Co.)</p>\n";
	print
	  "<div class=\"form-item\"><input type=\"text\" value=\"$cert_organization\" class=\"fixedwidth\" size=\"60\" name=\"cert_organization\"></div>\n";
	print "</div>\n";
	print "</div><div class=\"grid_6\">\n";
	print "<div class=\"form-row\">\n";
	print
	  "<p class=\"form-label\"><b>Locality.</b> City where your organization is located.</p>\n";
	print
	  "<div class=\"form-item\"><input type=\"text\" value=\"$cert_locality\" class=\"fixedwidth\" size=\"60\" name=\"cert_locality\"></div>\n";
	print "</div>\n";
	print "<div class=\"form-row\">\n";
	print
	  "<p class=\"form-label\"><b>State/Province.</b> State or province where your organization is located.</p>\n";
	print
	  "<div class=\"form-item\"><input type=\"text\" value=\"$cert_state\" class=\"fixedwidth\" size=\"60\" name=\"cert_state\"></div>\n";
	print "</div>\n";
	print "<div class=\"form-row\">\n";
	print
	  "<p class=\"form-label\"><b>Country.</b> Country (two characters code, example: US) where your organization is located.</p>\n";
	print
	  "<div class=\"form-item\"><input type=\"text\" value=\"$cert_country\" class=\"fixedwidth\" size=\"2\" maxlength=\"2\" name=\"cert_country\"></div>\n";
	print "</div>\n";
	print "<div class=\"form-row\">\n";
	print "<p class=\"form-label\"><b>E-mail Address</b></p>\n";
	print
	  "<div class=\"form-item\"><input type=\"text\" value=\"$cert_mail\" class=\"fixedwidth\" size=\"60\" name=\"cert_mail\"></div>\n";
	print "</div>\n";

	print "<div class=\"form-row\">\n";
	print "<p class=\"form-label\"><b>Key size</b></p>\n";
	print
	  "<div class=\"form-item\"><select name=\"cert_key\" class=\"fixedwidth\">";
	print "<option value=\"2048\">2048 </option>";
	print "</select></div>\n";
	print "</div>\n";
	print "</div><div class=\"grid_6\">\n";
	print "<div class=\"row\">";
	print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
	print "<input type=\"hidden\" name=\"actionpost\" value=\"Generate CSR\">";
	print
	  "<input type=\"submit\" value=\"Generate CSR\" name=\"button\" class=\"button grey\"> <input type=\"submit\" value=\"Cancel\" name=\"button\" class=\"button grey\" onClick=\"location.href='index.cgi'\">";
	print "</form>";
	print "</div>";
	print "</div>";
	print "<div class=\"clear\"></div>";
	print "</div>";
	print "</div>";
}

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
                window.location.replace('index.cgi?id=1-3');
            }
        });
        return false;
    });
});
</script>

<script>
\$(document).ready(function() {
    \$('#certificates-table').DataTable( {
        \"bJQueryUI\": true,     
               \"sPaginationType\": \"full_numbers\"   
    });
} );
</script>
";

