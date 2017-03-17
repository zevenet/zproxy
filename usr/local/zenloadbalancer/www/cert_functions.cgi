###############################################################################
#
#    Zevenet Software License
#    This file is part of the Zevenet Load Balancer software package.
#
#    Copyright (C) 2014-today ZEVENET SL, Sevilla (Spain)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

use strict;

use File::stat;
use Time::localtime;

my $openssl = &getGlobalConfiguration('openssl');

#Return all certificate files in config directory
sub getCertFiles    # ()
{
	my $configdir = &getGlobalConfiguration('configdir');

	opendir ( DIR, $configdir );
	my @files = grep ( /.*\.pem$/, readdir ( DIR ) );
	@files = grep ( !/_dh\d+\.pem$/, @files );
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
	my @eject;

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

	my $configdir = &getGlobalConfiguration('configdir');
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
	my $certdir;

	if ( 'zlbcertfile.pem' =~ /^$certname$/ )
	{
		$certdir = &getGlobalConfiguration('basedir');
	}
	else
	{
		$certdir = &getGlobalConfiguration('configdir');
	}

	# verify existance in config directory for security reasons
	opendir ( DIR, $certdir );
	my @file = grep ( /^$certname$/, readdir ( DIR ) );
	closedir ( DIR );

	my $files_removed = unlink ( "$certdir\/$file[0]" );

	&zenlog( "Error removing certificate $certdir\/$file[0]" ) if ! $files_removed;

	return $files_removed;
}

#Create CSR file
sub createCSR # ($certname, $certfqdn, $certcountry, $certstate, $certlocality, $certorganization, $certdivision, $certmail, $certkey, $certpassword)
{
	my (
		 $certname,     $certfqdn,         $certcountry,  $certstate,
		 $certlocality, $certorganization, $certdivision, $certmail,
		 $certkey,      $certpassword
	) = @_;

	my $configdir = &getGlobalConfiguration('configdir');
	my $output; 
	
	##sustituir los espacios por guiones bajos en el nombre de archivo###
	if ( $certpassword eq "" )
	{
		&zenlog(
			"Creating CSR: $openssl req -nodes -newkey rsa:$certkey -keyout $configdir/$certname.key -out $configdir/$certname.csr -batch -subj \"/C=$certcountry\/ST=$certstate/L=$certlocality/O=$certorganization/OU=$certdivision/CN=$certfqdn/emailAddress=$certmail\""
		);
		$output =
		  system ("$openssl req -nodes -newkey rsa:$certkey -keyout $configdir/$certname.key -out $configdir/$certname.csr -batch -subj \"/C=$certcountry\/ST=$certstate/L=$certlocality/O=$certorganization/OU=$certdivision/CN=$certfqdn/emailAddress=$certmail\" 2> /dev/null");
	}
	else
	{
		$output =
		  system ("$openssl req -passout pass:$certpassword -newkey rsa:$certkey -keyout $configdir/$certname.key -out $configdir/$certname.csr -batch -subj \"/C=$certcountry/ST=$certstate/L=$certlocality/O=$certorganization/OU=$certdivision/CN=$certfqdn/emailAddress=$certmail\" 2> /dev/null");
		&zenlog(
			"Creating CSR: $openssl req -passout pass:$certpassword -newkey rsa:$certkey -keyout $configdir/$certname.key -out $configdir/$certname.csr -batch -subj \"/C=$certcountry\/ST=$certstate/L=$certlocality/O=$certorganization/OU=$certdivision/CN=$certfqdn/emailAddress=$certmail\""
		);
	}
	return $output;
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

	my $configdir = &getGlobalConfiguration('configdir');
	my $filepath     = "$configdir\/$certfile";
	my @eject;

	if ( $certfile eq "zlbcertfile.pem" )
	{
		my $basedir = &getGlobalConfiguration('basedir');
		$filepath = "$basedir\/$certfile";
	}

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

	my $path    = &getGlobalConfiguration('configdir');
	my $buff    = "";
	my $pemfile = $keyfile;
	$pemfile =~ s/\.key$/\.pem/;

	my @files = ( "$path/$keyfile", "$tmpdir/$crtfile", "$tmpdir/$certautfile" );

	foreach my $file ( @files )
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
	open my $pemhandler, ">", "$path/$pemfile" or die $!;

	# Write the buffer into the output file.
	print $pemhandler $buff;

	close $pemhandler;
}

1;
