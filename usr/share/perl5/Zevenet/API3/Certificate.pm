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

my $CSR_KEY_SIZE = 2048;

# GET /certificates
sub certificates # ()
{
	require Zevenet::Certificate;

	my @out;
	my @certificates   = &getCertFiles();
	my $cert_dh2048_re = &getValidFormat( 'cert_dh2048' );
	@certificates = grep { !/$cert_dh2048_re/ } @certificates;

	foreach my $certificate ( @certificates )
	{
		my $configdir       = &getGlobalConfiguration( 'configdir' );
		my $certificateFile = "$configdir\/$certificate";

		my $type       = &getCertType( $certificateFile );
		my $cn         = &getCertCN( $certificateFile );
		my $issuer     = &getCertIssuer( $certificateFile );
		my $creation   = &getCertCreation( $certificateFile );
		my $expiration = &getCertExpiration( $certificateFile );

		chomp($creation);
		chomp($expiration);

		push @out,
		  {
			"file"       => "$certificate",
			"type"       => "$type",
			"CN"         => "$cn",
			"issuer"     => "$issuer",
			"creation"   => "$creation",
			"expiration" => "$expiration"
		  };
	}

	my $body = {
				 description => "List certificates",
				 params      => \@out,
	};

	&httpResponse({ code => 200, body => $body });
}

# GET /certificates/CERTIFICATE
sub download_certificate # ()
{
	my $cert_filename = shift;

	my $cert_dir = &getGlobalConfiguration('configdir');
	$cert_dir = &getGlobalConfiguration('basedir') if $cert_filename eq 'zlbcertfile.pem';

	open ( my $download_fh, '<', "$cert_dir/$cert_filename" );

	if ( $cert_filename =~ /\.(pem|csr)$/ && -f "$cert_dir\/$cert_filename" && $download_fh )
	{
		my $cgi = &getCGI();
		print $cgi->header(
						  -type            => 'application/x-download',
						  -attachment      => $cert_filename,
						  'Content-length' => -s "$cert_dir/$cert_filename",
		);

		binmode $download_fh;
		print while <$download_fh>;
		close $download_fh;
		exit;
	}
	else
	{
		my $errormsg = "Could not send such certificate";
		my $body = {
					 description => "Download certificate",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

# GET /certificates/CERTIFICATE/info
sub get_certificate_info # ()
{
	my $cert_filename = shift;

	require Zevenet::Certificate;

	my $cert_dir = &getGlobalConfiguration('configdir');
	$cert_dir = &getGlobalConfiguration('basedir') if $cert_filename eq 'zlbcertfile.pem';

	if ( &getValidFormat( 'certificate', $cert_filename ) && -f "$cert_dir\/$cert_filename" )
	{
		my @cert_info = &getCertData( $cert_filename );
		my $body;

		foreach my $line ( @cert_info )
		{
			$body .= $line;
		}

		&httpResponse({ code => 200, body => $body, type => 'text/plain' });
	}
	else
	{
		my $errormsg = "Could not get such certificate information";
		my $body = {
					 description => "Get Certificate Information",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

# DELETE /certificates/CERTIFICATE
sub delete_certificate # ( $cert_filename )
{
	my $cert_filename = shift;

	require Zevenet::Certificate;

	my $description = "Delete certificate";
	my $cert_dir    = &getGlobalConfiguration( 'configdir' );

	$cert_dir = &getGlobalConfiguration('basedir') if $cert_filename eq 'zlbcertfile.pem';

	# check is the certificate file exists
	if ( ! -f "$cert_dir\/$cert_filename" )
	{
		my $errormsg = "Certificate file not found.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};
		&httpResponse({ code => 404, body => $body });
	}

	my $status = &getFarmCertUsed( $cert_filename );

	# check is the certificate is being used
	if ( $status == 0 )
	{
		my $errormsg = "File can't be deleted because it's in use by a farm.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};
		&httpResponse({ code => 400, body => $body });
	}

	&delCert( $cert_filename );
	
	# check if the certificate exists
	if ( -f "$cert_dir\/$cert_filename" )
	{
		my $errormsg = "Error deleting certificate $cert_filename.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};
		&httpResponse({ code => 400, body => $body });
	}

	# no errors found, make a succesful response
	my $errormsg = "The Certificate $cert_filename has been deleted.";
	my $body = {
				 description => $description,
				 success     => "true",
				 message     => $errormsg
	};

	&httpResponse({ code => 200, body => $body });
}

# POST /farms/FARM/certificates (Add certificate to farm)
sub add_farm_certificate # ( $json_obj, $farmname )
{
	my $json_obj = shift;
	my $farmname = shift;

	my $description = "Add certificate";

	# Check if the farm exists
	if ( &getFarmFile( $farmname ) == -1 )
	{
		my $errormsg = "Farm not found";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	my $configdir   = &getGlobalConfiguration( 'configdir' );
	my $cert_pem_re = &getValidFormat( 'cert_pem' );

	# check certificate validation
	# FIXME: Show error if the certificate is already in the list
	unless ( -f $configdir . "/" . $json_obj->{ file }
			 && &getValidFormat( 'cert_pem', $json_obj->{ file } ) )
	{
		&zenlog(
			"ZAPI error, trying to add a certificate to the SNI list, invalid certificate name."
		);

		my $errormsg = "Invalid certificate name, please insert a valid value.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	if ( grep ( /^ $json_obj->{ file }$/, &getFarmCertificatesSNI( $farmname ) ) )
	{
		# Error
		my $errormsg = "The certificate already exists in the farm.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	my $status = &setFarmCertificateSNI( $json_obj->{ file }, $farmname );

	# check for error setting the certificate
	if ( $status != 0 )
	{
		&zenlog(
			"ZAPI error, trying to add a certificate to the SNI list, it's not possible to add the certificate."
		);

		my $errormsg =
		  "It's not possible to add the certificate with name $json_obj->{file} for the $farmname farm";

		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	# no errors found setting the certificate, return succesful response
	&zenlog( "ZAPI Success, trying to add a certificate to the SNI list." );

	my $message =
	  "The certificate $json_obj->{file} has been added to the SNI list of farm $farmname, you need restart the farm to apply";

	my $body = {
				 description => $description,
				 success     => "true",
				 message     => $message
	};

	if ( &getFarmStatus( $farmname ) eq 'up' )
	{
		&setFarmRestart( $farmname );
		$body->{ status } = 'needed restart';
	}

	&httpResponse({ code => 200, body => $body });
}

# DELETE /farms/FARM/certificates/CERTIFICATE
sub delete_farm_certificate # ( $farmname, $certfilename )
{
	my $farmname     = shift;
	my $certfilename = shift;

	my $description = "Delete farm certificate";

	# Check that the farm exists
	if ( &getFarmFile( $farmname ) == -1 )
	{
		my $errormsg = "The farmname $farmname does not exists";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	# Check if this certificate is set in the farm
	if ( !grep ( /^$certfilename$/, &getFarmCertificatesSNI( $farmname ) ) )
	{
		# Error
		my $errormsg = "The certificate does not exist in the farm.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}


	if ( &getValidFormat ( 'certificate', $certfilename ) )
	{
		&zenlog(
			"ZAPI error, trying to delete a certificate to the SNI list, invalid certificate id."
		);

		my $errormsg = "Invalid certificate id, please insert a valid value.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	my $status = &setFarmDeleteCertNameSNI( $certfilename, $farmname );

	# check if there was any error removing the certificate from the list.
	if ( $status == -1 )
	{
		&zenlog(
			"ZAPI error, trying to delete a certificate to the SNI list, it's not possible to delete the certificate."
		);

		my $errormsg =
		  "It isn't possible to delete the selected certificate $certfilename from the SNI list";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	# check if tried to remove last certificate in list, not allowed
	if ( $status == 1 )
	{
		&zenlog(
			"ZAPI error, trying to delete a certificate to the SNI list, it's not possible to delete all certificates, at least one is required for HTTPS."
		);

		my $errormsg =
		  "It isn't possible to delete all certificates, at least one is required for HTTPS profiles";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	# no errors found removing the certificate from farm, return succesful response
	&zenlog( "ZAPI Success, trying to delete a certificate to the SNI list." );

	my $message = "The Certificate $certfilename has been deleted";
	my $body = {
				 description => $description,
				 success     => "true",
				 message     => $message
	};

	if ( &getFarmStatus( $farmname ) eq 'up' )
	{
		&setFarmRestart( $farmname );
		$body->{ status } = 'needed restart';
	}

	&httpResponse({ code => 200, body => $body });
}

# POST /certificates (Create CSR)
sub create_csr
{
	my $json_obj = shift;

	require Zevenet::Certificate;

	my $description = 'Create CSR';
	my $errormsg;

	my $configdir = &getGlobalConfiguration('configdir');

	if ( -f "$configdir/$json_obj->{name}.csr" )
	{
		&zenlog( "ZAPI error, $json_obj->{name} already exists." );

		my $errormsg = "$json_obj->{name} already exists.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};
		&httpResponse({ code => 400, body => $body });
	}

	$json_obj->{ name }         = &getCleanBlanc( $json_obj->{ name } );
	#~ $json_obj->{ issuer }       = &getCleanBlanc( $json_obj->{ issuer } );
	$json_obj->{ fqdn }         = &getCleanBlanc( $json_obj->{ fqdn } );
	$json_obj->{ division }     = &getCleanBlanc( $json_obj->{ division } );
	$json_obj->{ organization } = &getCleanBlanc( $json_obj->{ organization } );
	$json_obj->{ locality }     = &getCleanBlanc( $json_obj->{ locality } );
	$json_obj->{ state }        = &getCleanBlanc( $json_obj->{ state } );
	$json_obj->{ country }      = &getCleanBlanc( $json_obj->{ country } );
	$json_obj->{ mail }         = &getCleanBlanc( $json_obj->{ mail } );

	if (    $json_obj->{ name } =~ /^$/
		 #~ || $json_obj->{ issuer } =~ /^$/
		 || $json_obj->{ fqdn } =~ /^$/
		 || $json_obj->{ division } =~ /^$/
		 || $json_obj->{ organization } =~ /^$/
		 || $json_obj->{ locality } =~ /^$/
		 || $json_obj->{ state } =~ /^$/
		 || $json_obj->{ country } =~ /^$/
		 || $json_obj->{ mail } =~ /^$/
		 #~ || $json_obj->{ key } =~ /^$/
		 )
	{
		$errormsg = "Fields can not be empty. Try again.";
		&zenlog( $errormsg );

		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	if ( &checkFQDN( $json_obj->{ fqdn } ) eq "false" )
	{
		$errormsg = "FQDN is not valid. It must be as these examples: domain.com, mail.domain.com, or *.domain.com. Try again.";
		&zenlog( $errormsg );

		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	if ( $json_obj->{ name } !~ /^[a-zA-Z0-9\-]*$/ )
	{
		$errormsg = "Certificate Name is not valid. Only letters, numbers and '-' chararter are allowed. Try again.";
		&zenlog( $errormsg );

		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	$errormsg = &createCSR(
				$json_obj->{ name },     $json_obj->{ fqdn },     $json_obj->{ country },
				$json_obj->{ state },    $json_obj->{ locality }, $json_obj->{ organization },
				$json_obj->{ division }, $json_obj->{ mail },     $CSR_KEY_SIZE,
				""
	);

	if ( !$errormsg )
	{
		my $message = "Certificate $json_obj->{ name } created";
		&zenlog( $message );
		
		my $body = {
					description => $description,
					success     => "true",
					message     => $message
		};
		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		$errormsg = "Error, creating certificate $json_obj->{ name }.";
		&zenlog( $errormsg );
		
		my $body = {
					description => $description,
					error     => "true",
					message     => $errormsg
		};
		&httpResponse({ code => 400, body => $body });
	}
}

# POST /certificates/CERTIFICATE (Upload PEM)
sub upload_certificate # ()
{
	my $upload_filehandle = shift;
	my $filename          = shift;

	my $description = "Upload PEM certificate";
	my $configdir = &getGlobalConfiguration('configdir');

	if ( &getValidFormat( 'certificate', $filename) )
	{
		$filename =~ s/[\(\)\@ ]//g;
		if ( -f "$configdir/$filename" )
		{
			# Error
			my $errormsg = "Certificate file name already exists";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}

		if ( $filename =~ /\\/ )
		{
			my @filen = split ( /\\/, $filename );
			$filename = $filen[-1];
		}

		open ( my $cert_filehandle, '>', "$configdir/$filename" ) or die "$!";
		print $cert_filehandle $upload_filehandle;
		close $cert_filehandle;

		my $message = "Certificate uploaded";
		my $body = {
					 description => $description,
					 success       => "true",
					 message     => $message
		};

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		&zenlog( "ZAPI error, trying to upload a certificate." );

		my $errormsg = "Invalid certificate file name";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	# check if the certificate filename already exists
	if ( -f "$configdir/$filename" )
	{
		my $errormsg = "Certificate file name already exists";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	if ( $filename =~ /\\/ )
	{
		my @filen = split ( /\\/, $filename );
		$filename = $filen[-1];
	}

	open ( my $cert_filehandle, '>', "$configdir/$filename" ) or die "$!";
	print $cert_filehandle $upload_filehandle;
	close $cert_filehandle;

	# no errors found, return sucessful response
	my $message = "Certificate uploaded";
	my $body = {
				 description => $description,
				 success       => "true",
				 message     => $message
	};

	&httpResponse({ code => 200, body => $body });
}

1;
