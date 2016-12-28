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

#**
# @apiDefine CertObj Certificate Object
#**

#**
#  @api {get} /certificates List all Certificates
#  @apiGroup Certificates
#  @apiName GetCertificates
#
#  @apiVersion 3.0.0
#  @apiDescription List all CSR and PEM certificates installed, which can be used with HTTPS farms.
#
#  The response will be a JSON object with a key set to params. The value of this will be an array of certificate objects, each of which contain the key attributes below.
#
# @apiExample {curl} Request example:
# curl -k -X GET -H "ZAPI_KEY: <ZAPI_KEY_STRING>" https://<zenlb_server>:444/zapi/v3/zapi.cgi/certificates
#
# @apiSuccess (ResponseParams) {Object[]} params List of certificate objects.
#
# @apiSuccess (CertObj) {String} CN Domain common name.
# @apiSuccess (CertObj) {String} creation Creation date.
# @apiSuccess (CertObj) {String} expiration Expiration date.
# @apiSuccess (CertObj) {String} file Filename of the certificate.
# @apiSuccess (CertObj) {String} issuer Certified Authority signing the certificate.
# @apiSuccess (CertObj) {String} type CSR or Certificate.
#
# @apiSuccessExample Response example:
#{
#   "description" : "List all certificates",
#   "params" : [
#      {
#         "CN" : "Zen Load Balancer",
#         "creation" : "Jan 12 14:49:03 2011 GMT",
#         "expiration" : "Jan  9 14:49:03 2021 GMT",
#         "file" : "zencert.pem",
#         "issuer" : "Zen Load Balancer",
#         "type" : "Certificate"
#      }
#   ]
#}
#
#@apiSampleRequest off
#
#**

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

#**
#  @api {get} /certificates/<file> Download Certificate
#  @apiGroup Certificates
#  @apiName DownloadCertificate
#
#  @apiVersion 3.0.0
#  @apiDescription Download a certificate installed on the load balancer, using the file name in the request to identify it.
#
#  The response will include the headers indicated below with information about the file. The body of the response will be the content of the file.
#
# @apiExample {curl} Request example:
# curl -k -X GET -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
# https://<zenlb_server>:444/zapi/v3/zapi.cgi/certificates/example.pem
#
# @apiHeader (Uri) {String} file Certificate file name as shown in the certificate list.
#
# @apiHeader (ResponseHeader) {String} Content-Disposition Includes the certificate file name.
# @apiHeader (ResponseHeader) {String} Content-Type Includes MIME type <code>application/x-download</code> to download the file. 
# @apiHeader (ResponseHeader) {Number} Content-Length Size of the body in bytes.
#
# @apiHeaderExample Response Headers
# HTTP/1.1 200 OK
# Date: Thu, 22 Dec 2016 09:27:47 GMT
# Content-Disposition: attachment; filename="example.pem"
# Content-Type: application/x-download; charset=ISO-8859-1
# Content-Length: 2359
#
# @apiSampleRequest off
#
#**

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

#**
#  @api {get} /certificates/<file>/info Show Certificate details
#  @apiGroup Certificates
#  @apiName CertificateDetails
#
#  @apiVersion 3.0.0
#  @apiDescription Show all the information included in the certificate, including signatures.
#
# @apiExample {curl} Request example:
# curl -k -X GET -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
# https://<zenlb_server>:444/zapi/v3/zapi.cgi/certificates/example.pem/info
#
# @apiHeader (URI) {String} file Certificate file name as shown in the certificate list.
#
# @apiSuccessExample Response example:
# Certificate:
#     Data:
#         Version: 3 (0x2)
#         Serial Number: 14346016480403539444 (0xc71749fb005a45f4)
#     Signature Algorithm: sha1WithRSAEncryption
#         Issuer: C=ES, ST=Spain, L=Spain, O=Sofintel, OU=Telecommunications, CN=Zen Load Balancer/emailAddress=zenloadbalancer-support@lists.sourceforge.net
#         Validity
#             Not Before: Jan 12 14:49:03 2011 GMT
#             Not After : Jan  9 14:49:03 2021 GMT
#         Subject: C=ES, ST=Spain, L=Spain, O=Sofintel, OU=Telecommunications, CN=Zen Load Balancer/emailAddress=zenloadbalancer-support@lists.sourceforge.net
#         Subject Public Key Info:
#             Public Key Algorithm: rsaEncryption
#                 Public-Key: (1024 bit)
#                 Modulus:
# ...
#
# @apiSampleRequest off
#
#**

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

#**
# @api {get} /certificates/activation Show activation Certificate details
# @apiGroup Certificates
# @apiName ActivationCertificateDetails
#
# @apiVersion 3.0.0
# @apiDescription Show all the information included in the activation certificate, including signatures.
#
# @apiExample {curl} Request example:
# curl -k -X GET -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
# https://<zenlb_server>:444/zapi/v3/zapi.cgi/certificates/activation
#
# @apiSampleRequest off
#
#**

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

#####Documentation of DELETE Certificate####
#**
# @api {delete} /certificates/<file> Delete a Certificate
# @apiGroup Certificates
# @apiName DeleteCertificate
#
# @apiVersion 3.0.0
# @apiDescription Deletes a certificate by file name in the load balancer.
#
# @apiExample {curl} Request example:
# curl -k -X DELETE -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
# https://<zenlb_server>:444/zapi/v3/zapi.cgi/certificates/example.pem
#
# @apiHeader (URI) {String} file Certificate file name, unique ID.
#
# @apiSuccessExample Response example:
# {
#    "description" : "Delete certificate",
#    "message" : "The Certificate example.pem has been deleted.",
#    "success" : "true"
# }
#
# @apiSampleRequest off
#
#**

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

#**
# @api {delete} /certificates/activation Delete the activation Certificate
# @apiGroup Certificates
# @apiName DeleteActivationCertificate
#
# @apiVersion 3.0.0
# @apiDescription Deletes the activation certificate installed in the load balancer.
#
# @apiExample {curl} Request example:
# curl -k -X DELETE -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
# https://<zenlb_server>:444/zapi/v3/zapi.cgi/certificates/activation
#
# @apiSuccessExample Response example:
# {
#    "description" : "Delete activation certificate",
#    "message" : "The activation certificate has been deleted",
#    "success" : "true"
# }
#
# @apiSampleRequest off
#
#**

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

#####Documentation of POST Add Certificates####
#**
# @api {post} /farms/<farmname>/certificates Add a Certificate to a farm
# @apiGroup Certificates
# @apiName AddFarmCertificate
#
# @apiVersion 3.0.0
# @apiDescription Include an installed PEM Certificate to the SNI list or <code>certlist</code> array of an HTTP farm with an HTTPS listener.
#
# @apiExample {curl} Request example:
# curl -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
# -d '{"file":"example.pem"}' https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/httpFarm/addcertificate
#
# @apiHeader (URI) {String} farmname Farm name, unique ID. Must be an HTTP farm with HTTPS listener configured.
#
# @apiSuccess (RequestParams) {String} file PEM Certificate file name.
#
# @apiSuccessExample Response example:
# {
#    "description" : "Add certificate",
#    "message" : "The certificate example.pem has been added to the SNI list of farm httpFarm, you need restart the farm to apply",
#    "success" : "true"
# }
#
#@apiSampleRequest off
#
#**

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

#####Documentation of DELETE Certificate of a list in a farm####
#**
# @api {delete} /farms/<farmname>/certificates/<file> Delete a Certificate from a farm
# @apiGroup Certificates
# @apiName DeleteFarmCertificate
#
# @apiVersion 3.0.0
# @apiDescription Delete the certificate with the selected file name from the certlist of an HTTP farm with HTTPS listener.
#
# @apiExample {curl} Request example:
# curl -k -X DELETE -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
# https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/MyHttpFarm/certificates/example.pem
#
# @apiHeader (URI) {String} farmname  Farm name, unique ID.
# @apiHeader (URI) {Number} file  Certificate file name in such farm.
#
# @apiSuccessExample Response example:
# {
#    "description" : "Delete farm certificate",
#    "message" : "The Certificate example.pem has been deleted.",
#    "success" : "true"
# }
#
# @apiSampleRequest off
#
#**

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

#**
# @api {post} /certificates Create a CSR certificate
# @apiGroup Certificates
# @apiName CreateCsrCertificate
#
# @apiVersion 3.0.0
# @apiDescription Create a CSR Certificate
#
# @apiExample {curl} Request example:
# curl -k -X POST -H "ZAPI_KEY: <ZAPI_KEY_STRING>" -H 'Content-Type: application/json'
# -d '{"name":"NewCSR","fqdn":"host.domain.com","division":"IT","organization":"Example Corp.",
# "locality":"Madrid","state":"Madrid","country":"Spain","mail":"info@domain.com"}'
# https://<zenlb_server>:444/zapi/v3/zapi.cgi/certificates
#
# @apiParam (RequestParams) {String} name		Certificate Name. Descriptive text, this name will be used to identify this certificate.
# @apiParam (RequestParams) {String} fqdn		Common Name or FQDN of the server. Example: domain.com, mail.domain.com, or *.domain.com.
# @apiParam (RequestParams) {String} division	Division or department name.
# @apiParam (RequestParams) {String} organization	Organization name.
# @apiParam (RequestParams) {String} locality	City where your organization is located.
# @apiParam (RequestParams) {String} state		State or Province.
# @apiParam (RequestParams) {String} country	Country.
# @apiParam (RequestParams) {String} mail		Contact e-mail address.
#
# @apiSuccessExample Response example:
# {
#    "description" : "Create CSR",
#    "message" : "Certificate NewCSR created",
#    "success" : "true"
# }

#
#@apiSampleRequest off
#
#**

sub create_csr
{
	my $json_obj = shift;

	my $description = 'Create CSR';

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
		my $errormsg = "Fields can not be empty. Try again.";
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
		my $errormsg = "FQDN is not valid. It must be as these examples: domain.com, mail.domain.com, or *.domain.com. Try again.";
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
		my $errormsg = "Certificate Name is not valid. Only letters, numbers and '-' chararter are allowed. Try again.";
		&zenlog( $errormsg );

		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	&createCSR(
				$json_obj->{ name },     $json_obj->{ fqdn },     $json_obj->{ country },
				$json_obj->{ state },    $json_obj->{ locality }, $json_obj->{ organization },
				$json_obj->{ division }, $json_obj->{ mail },     $CSR_KEY_SIZE,
				""
	);

	my $message = "Certificate $json_obj->{ name } created";
	&zenlog( $message );

	my $body = {
				 description => $description,
				 success     => "true",
				 message     => $message
	};

	&httpResponse({ code => 200, body => $body });
}

# POST /certificates/CERTIFICATE (Upload PEM)

#####Documentation of POST Upload Certificates####
#**
# @api {post} /certificates/<file> Upload a Certificate
# @apiGroup Certificates
# @apiName UploadCertificate
#
# @apiVersion 3.0.0
# @apiDescription Upload a PEM certificate for HTTP farms with HTTPS listener.
#
# Requires the parameter <code>--tcp-nodelay</code>, and <code>--data-binary</code> to upload the file in binary mode.
#
# @apiExample {curl} Request example:
# curl -k -X POST -H "ZAPI_KEY: <ZAPI_KEY_STRING>" -H 'Content-Type: text/plain'
# --tcp-nodelay --data-binary @/path/to/example.pem
# https://<zenlb_server>:444/zapi/v3/zapi.cgi/certificates/example.pem
#
# @apiParam (URI) {String} file File name to be given to the Certificate in the load balancer, unique ID.
#
# @apiSuccessExample Response example:
# {
#    "description" : "Upload PEM certificate",
#    "message" : "Certificate uploaded",
#    "success" : "true"
# }
#
# @apiSampleRequest off
#
#**

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

#**
# @api {post} /certificates/activation Upload an activation Certificate
# @apiGroup Certificates
# @apiName UploadActivationCertificate
#
# @apiVersion 3.0.0
# @apiDescription Upload an activation certificate with PEM format.
#
# @apiExample {curl} Request example
# curl -k -X POST -H "ZAPI_KEY: <ZAPI_KEY_STRING>" -H 'Content-Type: text/plain'
# --tcp-nodelay --data-binary @/path/to/example.pem
# https://<zenlb_server>:444/zapi/v3/zapi.cgi/certificates/activation
#
# @apiSuccessExample Response example:
# {
#    "description" : "Upload activation certificate",
#    "message" : "Activation certificate uploaded",
#    "success" : "true"
# }
#
#@apiSampleRequest off
#
#**

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
