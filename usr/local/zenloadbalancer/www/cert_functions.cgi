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

#Return all certificate files in config directory
sub getCertFiles    # ()
{
	opendir ( DIR, $configdir );
	my @files = grep ( /.*\.pem$/, readdir ( DIR ) );
	closedir ( DIR );

	opendir ( DIR, $configdir );
	push ( @files, grep ( /.*\.csr$/, readdir ( DIR ) ) );
	closedir ( DIR );

	return @files;
}

#Delete all blancs from the beginning and from the end of a variable.
sub getCleanBlanc    # ($vartoclean)
{
	my ( $vartoclean ) = @_;

	$vartoclean =~ s/^\s+//;
	$vartoclean =~ s/\s+$//;

	return $vartoclean;
}

#Return the type of a certificate file
sub getCertType      # ($certfile)
{
	my ( $certfile ) = @_;
	my $certtype = "none";

	if ( $certfile =~ /\.pem/ || $certfile =~ /\.crt/ )
	{
		$certtype = "Certificate";
	}
	elsif ( $certfile =~ /\.csr/ )
	{
		$certtype = "CSR";
	}

	return $certtype;
}

#Return the Common Name of a certificate file
sub getCertCN    # ($certfile)
{
	my ( $certfile ) = @_;
	my $certcn = "";

	if ( &getCertType( $certfile ) eq "Certificate" )
	{
		@eject  = `$openssl x509 -noout -in $certfile -text | grep Subject:`;
		@eject  = split ( /CN=/, $eject[0] );
		@eject  = split ( /\/emailAddress=/, $eject[1] );
		$certcn = $eject[0];
	}
	else
	{
		@eject  = `$openssl req -noout -in $certfile -text | grep Subject:`;
		@eject  = split ( /CN=/, $eject[0] );
		@eject  = split ( /\/emailAddress=/, $eject[1] );
		$certcn = $eject[0];
	}

	$certcn = &getCleanBlanc( $certcn );

	return $certcn;
}

#Return the Issuer Common Name of a certificate file
sub getCertIssuer    # ($certfile)
{
	my ( $certfile ) = @_;
	my $certissu = "";

	if ( &getCertType( $certfile ) eq "Certificate" )
	{
		my @eject = `$openssl x509 -noout -in $certfile -text | grep Issuer:`;
		@eject = split ( /CN=/,             $eject[0] );
		@eject = split ( /\/emailAddress=/, $eject[1] );
		$certissu = $eject[0];
	}
	else
	{
		$certissu = "NA";
	}

	$certissu = &getCleanBlanc( $certissu );

	return $certissu;
}

#Return the creation date of a certificate file
sub getCertCreation    # ($certfile)
{
	my ( $certfile ) = @_;

	#~ use File::stat;
	#~ use Time::localtime;

	my $datecreation = "";

	if ( &getCertType( $certfile ) eq "Certificate" )
	{
		my @eject = `$openssl x509 -noout -in $certfile -dates`;
		my @datefrom = split ( /=/, $eject[0] );
		$datecreation = $datefrom[1];
	}
	else
	{
		my @eject = split ( / /, gmtime ( stat ( $certfile )->mtime ) );
		splice ( @eject, 0, 1 );
		push ( @eject, "GMT" );
		$datecreation = join ( ' ', @eject );
	}

	return $datecreation;
}

#Return the expiration date of a certificate file
sub getCertExpiration    # ($certfile)
{
	my ( $certfile ) = @_;
	my $dateexpiration = "";

	if ( &getCertType( $certfile ) eq "Certificate" )
	{
		my @eject = `$openssl x509 -noout -in $certfile -dates`;
		my @dateto = split ( /=/, $eject[1] );
		$dateexpiration = $dateto[1];
	}
	else
	{
		$dateexpiration = "NA";
	}

	return $dateexpiration;
}

# content 1-3 certificate-https
sub getFarmCertUsed    #($cfile)
{
	my ( $cfile ) = @_;

	my @farms  = &getFarmsByType( "https" );
	my $output = -1;

	for ( @farms )
	{
		my $fname         = $_;
		my $farm_filename = &getFarmFile( $fname );
		use File::Grep qw( fgrep fmap fdo );
		if ( fgrep { /Cert \"$configdir\/$cfile\"/ } "$configdir/$farm_filename" )
		{
			$output = 0;
		}
	}

	return $output;
}

#Check if a fqdn is valid
sub checkFQDN    # ($certfqdn)
{
	my ( $certfqdn ) = @_;
	my $valid = "true";

	if ( $certfqdn =~ /^http:/ )
	{
		$valid = "false";
	}
	if ( $certfqdn =~ /^\./ )
	{
		$valid = "false";
	}
	if ( $certfqdn =~ /\.$/ )
	{
		$valid = "false";
	}
	if ( $certfqdn =~ /\// )
	{
		$valid = "false";
	}

	return $valid;
}

sub delCert    # ($certname)
{
	my ( $certname ) = @_;

	# escaping special caracters
	$certname = quotemeta $certname;

	# verify existance in config directory for security reasons
	opendir ( DIR, $configdir );
	my @file = grep ( /^$certname$/, readdir ( DIR ) );
	closedir ( DIR );

	unlink ( "$configdir\/$file[0]" )
	  or &logfile( "Error removing certificate $configdir\/$file[0]" );
}

#Create CSR file
sub createCSR # ($certname, $certfqdn, $certcountry, $certstate, $certlocality, $certorganization, $certdivision, $certmail, $certkey, $certpassword)
{
	my (
		 $certname,     $certfqdn,         $certcountry,  $certstate,
		 $certlocality, $certorganization, $certdivision, $certmail,
		 $certkey,      $certpassword
	) = @_;

	##sustituir los espacios por guiones bajos en el nombre de archivo###
	if ( $certpassword eq "" )
	{
		&logfile(
			"Creating CSR: $openssl req -nodes -newkey rsa:$certkey -keyout $configdir/$certname.key -out $configdir/$certname.csr -batch -subj \"/C=$certcountry\/ST=$certstate/L=$certlocality/O=$certorganization/OU=$certdivision/CN=$certfqdn/emailAddress=$certmail\""
		);
		my @opensslout =
		  `$openssl req -nodes -newkey rsa:$certkey -keyout $configdir/$certname.key -out $configdir/$certname.csr -batch -subj "/C=$certcountry\/ST=$certstate/L=$certlocality/O=$certorganization/OU=$certdivision/CN=$certfqdn/emailAddress=$certmail" 2> /dev/null`;
	}
	else
	{
		my @opensslout =
		  `$openssl req -passout pass:$certpassword -newkey rsa:$certkey -keyout $configdir/$certname.key -out  $configdir/$certname.csr -batch -subj "/C=$certcountry/ST=$certstate/L=$certlocality/O=$certorganization/OU=$certdivision/CN=$certfqdn/emailAddress=$certmail" 2> /dev/null`;
		&logfile(
			"Creating CSR: $openssl req -passout pass:$certpassword -newkey rsa:$certkey -keyout $configdir/$certname.key -out $configdir/$certname.csr -batch -subj \"/C=$certcountry\/ST=$certstate/L=$certlocality/O=$certorganization/OU=$certdivision/CN=$certfqdn/emailAddress=$certmail\""
		);
	}
}

#function that creates a menu to manage a certificate
sub createMenuCert    # ($certfile)
{
	my ( $certfile ) = @_;

	my $certtype = &getCertType( $certfile );

	if ( $certtype eq "CSR" )
	{
		&uploadCertFromCSR( $certfile );
	}

	print "<p>";

	# delete
	print "
		<form method=\"post\" action=\"index.cgi\" class=\"myform\">
		<button type=\"submit\" class=\"myicons\" title=\"Delete $certtype $certfile\" onclick=\"return confirm('Are you sure you want to delete the certificate: $certfile?')\">
			<i class=\"fa fa-times-circle action-icon fa-fw red\"></i>
		</button>
		<input type=\"hidden\" name=\"id\" value=\"$id\">
		<input type=\"hidden\" name=\"action\" value=\"deletecert\">
		<input type=\"hidden\" name=\"certname\" value=\"$certfile\">
		</form>";

	# view
	print "
		<form method=\"post\" action=\"index.cgi\" class=\"myform\">
		<button type=\"submit\" class=\"myicons\" title=\"View $certtype $certfile content\">
			<i class=\"fa fa-search action-icon fa-fw\"></i>
		</button>
		<input type=\"hidden\" name=\"id\" value=\"$id\">
		<input type=\"hidden\" name=\"action\" value=\"View_Cert\">
		<input type=\"hidden\" name=\"certname\" value=\"$certfile\">
		</form>";

	# download
	print
	  "<a href=\"downloadcerts.cgi?certname=$certfile\" target=\"_blank\" title=\"Download $certtype $certfile\"><i class=\"fa fa-download action-icon fa-fw\"></i></a>";
	print "</p>";
}

sub uploadCertFromCSR    # ($certfile)
{
	my ( $certfile ) = @_;

	print "<script language=\"javascript\">
	                var popupWindow = null;
	                function positionedPopup(url,winName,w,h,t,l,scroll)
	                {
	                settings ='height='+h+',width='+w+',top='+t+',left='+l+',scrollbars='+scroll+',resizable'
	                popupWindow = window.open(url,winName,settings)
	                }
	        </script>";

	print
	  "<a href=\"uploadcertsfromcsr.cgi?certname=$certfile\" title=\"Upload certificate for CSR $certfile\" onclick=\"positionedPopup(this.href,'myWindow','500','300','100','200','yes');return false\"><i class=\"fa fa-upload action-icon fa-fw green\"></i></a> ";
}

sub uploadPEMCerts    # ($certfile)
{
	my ( $certfile ) = @_;

	print
	  "<li><a href=\"uploadcerts.cgi\" class=\"open-dialog\"><img src=\"img/icons/basic/up.png\" alt=\"Upload cert\" title=\"Upload cert\">Upload Certificate </a></li>";
	print
	  "<div id=\"dialog-container\" style=\"display: none;\"><iframe id=\"dialog\" width=\"350\" height=\"350\"></iframe></div>";
}

sub downloadCert      # ($certfile)
{
	my ( $certfile ) = @_;

	print "<script language=\"javascript\">
	                var popupWindow = null;
	                function positionedPopup(url,winName,w,h,t,l,scroll)
	                {
	                settings ='height='+h+',width='+w+',top='+t+',left='+l+',scrollbars='+scroll+',resizable'
	                popupWindow = window.open(url,winName,settings)
	                }
	        </script>";

	#print the information icon with the popup with info.
	print
	  "<a href=\"downloadcerts.cgi?certname=$certfile\" onclick=\"positionedPopup(this.href,'myWindow','500','300','100','200','yes');return false\"><img src='img/icons/small/page_white_put.png' title=\"Download $certfile\"></a> ";
}

sub getCertData    # ($certfile)
{
	my ( $certfile ) = @_;
	my $filepath     = "$configdir\/$certfile";
	my @eject        = ( "" );

	if ( &getCertType( $filepath ) eq "Certificate" )
	{
		@eject = `$openssl x509 -in $filepath -text`;
	}
	else
	{
		@eject = `$openssl req -in $filepath -text`;
	}

	return @eject;
}

sub createPemFromKeyCRT    # ($keyfile,$crtfile,$certautfile,$tmpdir)
{
	my ( $keyfile, $crtfile, $certautfile, $tmpdir ) = @_;

	my $path    = $configdir;
	my $buff    = "";
	my $pemfile = $keyfile;
	$pemfile =~ s/\.key$/\.pem/;

	@files = ( "$path/$keyfile", "$tmpdir/$crtfile", "$tmpdir/$certautfile" );

	foreach $file ( @files )
	{
		# Open key files
		open FILE, "<", $file or die $!;

	  # Now get every line in the file, and attach it to the full ‘buffer’ variable.
		while ( my $line = <FILE> )
		{
			$buff .= $line;
		}

		# Close this particular file.
		close FILE;
	}
	open $pemhandler, ">", "$path/$pemfile" or die $!;

	# Write the buffer into the output file.
	print $pemhandler $buff;

	close $pemhandler;
}

# do not remove this
1;

