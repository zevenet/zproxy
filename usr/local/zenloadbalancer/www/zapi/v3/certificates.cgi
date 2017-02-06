#!/usr/bin/perl -w

##############################################################################
#
#     This file is part of the Zen Load Balancer Enterprise Edition software
#     package.
#
#     Copyright (C) 2014 SOFINTEL IT ENGINEERING SL, Sevilla (Spain)
#
#     This file cannot be distributed, released in public domain and/or for
#     commercial purposes.
#
###############################################################################

my $CSR_KEY_SIZE = 2048;

#**
# @apiDefine Request Request
#**

#**
# @apiDefine RequestParams Request parameters
#**

#**
# @apiDefine ResponseParams Response parameters
#**

#**
# @apiDefine Response Response
#**

#**
# @apiDefine ResponseHeader Response Headers
#**

#**
# @apiDefine RequestHeader Request Headers
#**

#**
# @apiDefine URI URI variables
#**

#**
# @apiDefine RequestPostData Request Post Data
#**

# GET /certificates
sub certificates # ()
{
	my @certificates = &getCertFiles();
	my @out;

	my $cert_dh2048_re = &getValidFormat('cert_dh2048');
	@certificates = grep {! /$cert_dh2048_re/ } @certificates;

	foreach my $certificate ( @certificates )
	{
		my $configdir = &getGlobalConfiguration('configdir');
		my $certificateFile = "$configdir\/$certificate";

		my $type       = &getCertType( $certificateFile );
		my $cn         = &getCertCN( $certificateFile );
		my $issuer     = &getCertIssuer( $certificateFile );
		my $creation   = &getCertCreation( $certificateFile );
		chomp($creation);
		my $expiration = &getCertExpiration( $certificateFile );
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

	# Success
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
		# Error
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

	my $cert_dir = &getGlobalConfiguration('configdir');
	$cert_dir = &getGlobalConfiguration('basedir') if $cert_filename eq 'zlbcertfile.pem';

	if ( $cert_filename =~ /\.(pem|csr)$/ && -f "$cert_dir\/$cert_filename" )
	{
		my @cert_info = &getCertData( $cert_filename );
		my $body;

		# Success
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

# GET /certificates/activation
sub get_activation_certificate_info # ()
{
	my $description = "Activation certificate information";
	my $cert_filename = 'zlbcertfile.pem';
	my $cert_dir = &getGlobalConfiguration('basedir');

	if ( -f "$cert_dir\/$cert_filename" )
	{
		my @cert_info = &getCertData( $cert_filename );
		my $body;

		# Success
		foreach my $line ( @cert_info )
		{
			$body .= $line;
		}

		&httpResponse({ code => 200, body => $body, type => 'text/plain' });
	}
	else
	{
		my $errormsg = "There is no activation certificate installed";
		my $body = {
					 description => $description,
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

	my $description = "Delete certificate";
	my $status = &getFarmCertUsed( $cert_filename );

	if ( $status == 0 )
	{
		&zenlog( "ZAPI error, file can't be deleted because it's in use by a farm." );

		# Error
		my $errormsg = "File can't be deleted because it's in use by a farm";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	my $message = "The Certificate $cert_filename has been deleted";

	&delCert( $cert_filename );
	&zenlog( $message );

	# Success
	my $body = {
				 description => $description,
				 success     => "true",
				 message     => $message
	};

	&httpResponse({ code => 200, body => $body });
}

# DELETE /certificates/activation
sub delete_activation_certificate # ( $cert_filename )
{
	my $description = "Delete activation certificate";
	my $cert_filename = 'zlbcertfile.pem';

	if ( &delCert( $cert_filename ) )
	{
		# Success
		my $message = "The activation certificate has been deleted";
		my $body = {
					 description => $description,
					 success     => "true",
					 message     => $message
		};

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		my $errormsg = "An error happened deleting the activation certificate";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

# POST /farms/FARM/certificates (Add certificate to farm)
sub add_farm_certificate # ( $json_obj, $farmname )
{
	my $json_obj = shift;
	my $farmname = shift;

	my $description = "Add certificate";

	# Check that the farm exists
	if ( &getFarmFile( $farmname ) == -1 )
	{
		# Error
		my $errormsg = "Farm not found";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	my $configdir = &getGlobalConfiguration('configdir');
	my $cert_pem_re = &getValidFormat('cert_pem');

	unless ( -f $configdir . "/" . $json_obj->{ file }
			 && &getValidFormat( 'cert_pem', $json_obj->{ file } ) )
	{
		&zenlog(
			"ZAPI error, trying to add a certificate to the SNI list, invalid certificate name."
		);

		# Error
		my $errormsg = "Invalid certificate name, please insert a valid value.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	# FIXME: Show error if the certificate is already in the list

	my $status = &setFarmCertificateSNI( $json_obj->{ file }, $farmname );

	if ( $status == 0 )
	{
		&zenlog( "ZAPI Success, trying to add a certificate to the SNI list." );

		# Success
		my $message =
		  "The certificate $json_obj->{file} has been added to the SNI list of farm $farmname, you need restart the farm to apply";

		my $body = {
					 description => $description,
					 success     => "true",
					 message     => $message
		};

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		&zenlog(
			"ZAPI error, trying to add a certificate to the SNI list, it's not possible to add the certificate."
		);

		# Error
		my $errormsg =
		  "It's not possible to add the certificate with name $json_obj->{file} for the $farmname farm";

		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
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
		# Error
		my $errormsg = "The farmname $farmname does not exists";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	if ( $certfilename !~ /^$/ && $certfilename =~ /^[\w\.-_]+$/ )
	{
		$status = &setFarmDeleteCertNameSNI( $certfilename, $farmname );

		if ( $status == 0 )
		{
			&zenlog( "ZAPI Success, trying to delete a certificate to the SNI list." );

			# Success
			my $message = "The Certificate $certfilename has been deleted";
			my $body = {
						 description => $description,
						 success     => "true",
						 message     => $message
			};

			&httpResponse({ code => 200, body => $body });
		}

		if ( $status == -1 )
		{
			&zenlog(
				"ZAPI error, trying to delete a certificate to the SNI list, it's not possible to delete the certificate."
			);

			# Error
			my $errormsg =
			  "It isn't possible to delete the selected certificate $certfilename from the SNI list";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}

		if ( $status == 1 )
		{
			&zenlog(
				"ZAPI error, trying to delete a certificate to the SNI list, it's not possible to delete all certificates, at least one is required for HTTPS."
			);

			# Error
			my $errormsg =
			  "It isn't possible to delete all certificates, at least one is required for HTTPS profiles";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}
	}
	else
	{
		&zenlog(
			"ZAPI error, trying to delete a certificate to the SNI list, invalid certificate id."
		);

		# Error
		my $errormsg = "Invalid certificate id, please insert a valid value.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

# POST /certificates (Create CSR)
sub create_csr
{
	my $json_obj = shift;

	my $description = 'Create CSR';
	my $errormsg;

	my $configdir = &getGlobalConfiguration('configdir');

	if ( -f "$configdir/$json_obj->{name}.csr" )
	{
		&zenlog( "ZAPI error, $json->{ name} already exists."	);
		# Error
		my $errormsg = "$json->{ name} already exists.";
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
		&zenlog( $message );
		
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

#
# Curl command:
#
# curl -kis -X POST -H "ZAPI_KEY: 2bJUd" --tcp-nodelay -H 'Content-Type: application/x-pem-file' https://192.168.101.20:444/zapi/v3/zapi.cgi/certificates/test.pem --data-binary @/usr/local/zenloadbalancer/config/zencert.pem
#

	my $upload_filehandle = shift;
	my $filename = shift;

	my $description = "Upload PEM certificate";
	my $configdir = &getGlobalConfiguration('configdir');

	if ( $filename =~ /^\w.+\.pem$/ && ! -f "$configdir/$filename" )
	{
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

		# Error
		my $errormsg = "Error uploading certificate file";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

# POST /certificates/activation
sub upload_activation_certificate # ()
{

#
# Curl command:
#
# curl -kis --tcp-nodelay -X POST -H "ZAPI_KEY: 2bJUd" -H 'Content-Type: application/x-pem-file' https://46.101.46.14:444/zapi/v3/zapi.cgi/certificates/activation --data-binary @hostmane.pem
#

	my $upload_filehandle = shift;

	my $description = "Upload activation certificate";
	my $filename = 'zlbcertfile.pem';

	if ( $upload_filehandle )
	{
		my $basedir = &getGlobalConfiguration('basedir');

		open ( my $cert_filehandle, '>', "$basedir/$filename" ) or die "$!";
		binmode $cert_filehandle;
		print { $cert_filehandle } $upload_filehandle;
		close $cert_filehandle;

		&checkActivationCertificate();

		my $message = "Activation certificate uploaded";
		my $body = {
					 description => $description,
					 success     => "true",
					 message     => $message
		};

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		&zenlog( "ZAPI error, trying to upload activation certificate." );

		# Error
		my $errormsg = "Error uploading activation certificate file";

		my $body = {
					   description => $description,
					   error       => "true",
					   message     => $errormsg,
		};

		&httpResponse({ code => 400, body => $body });
	}
}

1;
