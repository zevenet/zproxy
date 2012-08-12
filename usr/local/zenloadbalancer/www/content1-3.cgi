#require
use File::stat;
use File::Basename;
use Time::localtime;
use Sys::Hostname;
#my $query = new CGI;


print "
    <!--Content INI-->
        <div id=\"page-content\">

                <!--Content Header INI-->
                        <h2>Manage::Certificates</h2>
                <!--Content Header END-->";

###
#table
#list all certs
#opendir(DIR, $configdir);
#@files = grep(/.*\.pem$/,readdir(DIR));
#closedir(DIR);
if ($action eq "changecert")
	{
	$status = &setFarmCertificate($certname,$farmname);
	if ($status == 0)
		{
		&successmsg("Certificate is changed to $certname on farm $farmname, you need restart the farm to apply");
		&setFarmRestart($farmname);
		}
	}

if ($action eq "deletecert")
	{
	$status = &getFarmCertUsed($certname);
	if (&getFarmCertUsed($certname) == 0)
		{
		&errormsg("File can't be deleted because it's in use by a farm");
		}
	else
		{
		unlink ("$configdir\/$certname");
		&successmsg("File $file deleted");	
		}
#obtain https certificates
	}

opendir(DIR, $configdir);
@files = grep(/.*\.pem$/,readdir(DIR));
closedir(DIR);



#print "<div class=\"box-header\">Certificates for HTTPS farms </div>";
#print "<div class=\"box table\">";
#print "<table cellspacing=\"0\">";
#print "<thead>";
#print "<tr>";
#print "<td>Farm name</td><td>Certificate</td><td>Actions</td>";
#print "</tr>";
#print "</thead>";
#
#
#print "<tbody>";
#my @httpsfarms = &getFarmsByType("https");
#foreach (@httpsfarms)
#	{
#	print "<form method=\"get\" action=\"index.cgi\">";
#	print "<input type=\"hidden\" name=\"id\" value=\"$id\">";
#	print "<input type=\"hidden\" name=\"farmname\" value=\"$_\">";
#	$certname = &getFarmCertificate($_);
#	print "<tr>";
#	print "<td>$_</td> <td>";
#	print "<select  name=\"certname\">";
#	foreach $file(@files)
#		{
#		if ($certname eq $file)
#			{
#			print "<option value=\"$file\" selected=\"selected\">$file</option>";
#			}
#		else
#			{
#			print "<option value=\"$file\">$file</option>";
#			}
#		}
#	print "</td>";
#	print "</select>";
#	print  "<td>";
#	&createMenuFarmCert($_,$certname);
#	print   "</td>";	
#	print "</tr>\n";
#	print "</form>\n";
#	}	
#
#
#print "</tbody>";
#print "</table>";
#
#print "</div>";
#end table


#
#table
print "<div class=\"box-header\">Certificates inventory </div>";
print "<div class=\"box table\">";
print "<table cellspacing=\"0\">";
print "<thead>";
print "<tr>";
print "<td>Certificate</td><td>Issuer</td><td>Created on</td><td>Expire on</td><td>Actions</td>";
print "</tr>";
print "</thead>";


print "<tbody>";
foreach (@files)
	{
	$filepath = "$configdir\/$_";
	my @eject = `$openssl x509 -noout -in $filepath -issuer`;
	$issuer = @eject[0];
	$issuer =~ s/issuer= //;
	my @eject = `$openssl x509 -noout -in $filepath  -dates`;
	my @datefrom = split(/=/,@eject[0]);
	my @dateto = split(/=/,@eject[1]);
	$datecreation = @datefrom[1];
	$dateexpiration = @dateto[1];
	
	print "<tr><td>$_</td><td>$issuer</td><td>$datecreation</td><td>$dateexpiration</td><td>";
	if ($_ ne  "zencert\.pem")
		{
		print "<a href=\"index.cgi?id=$id&action=deletecert&certname=$_ \"><img src=\"img/icons/small/cross_octagon.png\" title=\"Delete $_ certificate\" onclick=\"return confirm('Are you sure you want to delete the certificate: $_?')\"></a>"
		}

	print "</td></tr>";
	}

print "<tr><td colspan=4></td><td>\n\n";

&uploadcerts();

print "</td></tr>";


#print "<tr><td colspan=2></td><td><a href=\"index.cgi?id=$id&action=uploadcert\"><img src=\"img/icons/small/arrow_up.png\" title=\"Upload new certificate\"></a></td></tr>";
print "</tbody>";
print "</table>";

print "</div>";
#end table



print "</div><!--Content END-->";


