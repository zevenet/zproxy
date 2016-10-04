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

# GET Certificates

#####Documentation of GET Certificates####
#**
#  @api {get} /certificates Request info of all certificates
#  @apiGroup Certificates
#  @apiName GetCertificates
#  @apiDescription Get the Params of all certificates
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "List certificates",
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
#
#@apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#       -u zapi:<password>  https://<zenlb_server>:444/zapi/v3/zapi.cgi/certificates
#
#@apiSampleRequest off
#
#**

sub certificates # ()
{
	my @certificates = &getCertFiles();
	my @out;

	foreach my $certificate ( @certificates )
	{
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

# GET certificate info
sub get_certificate_info # ()
{
	my $cert_filename = shift;

	my $cert_dir = $configdir;
	$cert_dir = $basedir if $cert_filename eq 'zlbcertfile.pem';

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

# DELETE Certificate

#####Documentation of DELETE Certificate####
#**
#  @api {delete} /certificates/<certname> Delete a certificate
#  @apiGroup Certificates
#  @apiName DeleteCertificates
#  @apiParam {String} certname  Certificate name, unique ID.
#  @apiDescription Delete the certificate selected
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Delete certificate example.pem",
#   "message" : "The Certificate example.pem has been deleted.",
#   "success" : "true"
#}
#
#
#@apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X DELETE -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#       -u zapi:<password>  https://<zenlb_server>:444/zapi/v3/zapi.cgi/certificates/example.pem
#
#@apiSampleRequest off
#
#**

sub delete_certificate # ( $cert_filename )
{
	my $cert_filename = shift;

	my $status = &getFarmCertUsed( $cert_filename );

	if ( $status == 0 )
	{
		&zenlog( "ZAPI error, file can't be deleted because it's in use by a farm." );

		# Error
		my $errormsg = "File can't be deleted because it's in use by a farm";
		my $body = {
					 description => "Delete certificate",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
	else
	{
		&delCert( $cert_filename );
		&zenlog( "The certificate $cert_filename has been deleted" );
	}

	# Success
	my $message = "The Certificate $cert_filename has been deleted.";
	my $body = {
				 description => "Delete certificate $cert_filename",
				 success     => "true",
				 message     => $message
	};

	&httpResponse({ code => 200, body => $body });
}

#####Documentation of POST Add Certificates####
#**
#  @api {post} /farms/<farmname>/addcertificate Add a certificate to the SNI list of a farm
#  @apiGroup Certificates
#  @apiName AddCertificates
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiDescription Add a certificate to the available certificate list of a farm
#  @apiVersion 3.0.0
#
#
# @apiSuccess   {String}        file                The certificate name.
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Add certificate example.pem",
#   "message" : "The certificate example.pem has been added tothe SNI list of farm httptest1, you need restart the farm to apply",
#   "success" : "true"
#}
#
#
#@apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#       -u zapi:<password> -d '{"file":"example.pem"}'
#       https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/httptest/addcertificate
#
#@apiSampleRequest off
#
#**

# POST Add Farm Certificate

sub add_farmcertificate # ( $json_obj, $farmname )
{
	my $json_obj = shift;
	my $farmname = shift;

	# Check that the farm exists
	if ( &getFarmFile( $farmname ) == -1 )
	{
		# Error
		my $errormsg = "The farmname $farmname does not exists.";
		my $body = {
					 description => "Add certificate",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	if ( $json_obj->{ file } !~ /^$/ && $json_obj->{ file } =~ /^\w+\.\w{3}$/ )
	{
		$status = &setFarmCertificateSNI( $json_obj->{ file }, $farmname );
		if ( $status == 0 )
		{
			&zenlog( "ZAPI Success, trying to add a certificate to the SNI list." );

			# Success
			my $message =
			  "The certificate $json_obj->{file} has been added to the SNI list of farm $farmname, you need restart the farm to apply";

			my $body = {
						 description => "Add certificate $json_obj->{file}",
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
						 description => "Add certificate",
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}
	}
	else
	{
		&zenlog(
			"ZAPI error, trying to add a certificate to the SNI list, invalid certificate name."
		);

		# Error
		my $errormsg = "Invalid certificate name, please insert a valid value.";
		my $body = {
					 description => "Add certificate",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

#####Documentation of DELETE Certificate of a list in a farm####
#**
#  @api {delete} /farms/<farmname>/deletecertificate/<certid> Delete a certificate of the SNI list of a farm
#  @apiGroup Certificates
#  @apiName DeleteCertificateslist
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiParam {Number} certid  Certificate ID, unique ID.
#  @apiDescription Delete the certificate selected of a available certificate list in a farm
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Delete certificate 2",
#   "message" : "The Certificate 2 has been deleted.",
#   "success" : "true"
#}
#
#
#@apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X DELETE -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#       -u zapi:<password>  https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/farmhttp/deletecertificate/2
#
#@apiSampleRequest off
#
#**

# DELETE Farm Certificate

sub delete_farmcertificate # ( $farmname, $certfilename )
{
	my $farmname     = shift;
	my $certfilename = shift;

	# Check that the farm exists
	if ( &getFarmFile( $farmname ) == -1 )
	{
		# Error
		my $errormsg = "The farmname $farmname does not exists.";
		my $body = {
					 description => "Delete certificate",
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
			my $message = "The Certificate $certfilename has been deleted.";
			my $body = {
						 description => "Delete certificate $certfilename",
						 success     => "true",
						 message     => $message
			};

			&httpResponse({ code => 200, body => $body });
		}
		else
		{
			if ( $status == -1 )
			{
				&zenlog(
					"ZAPI error, trying to delete a certificate to the SNI list, it's not possible to delete the certificate."
				);

				# Error
				my $errormsg =
				  "It isn't possible to delete the selected certificate $certfilename from the SNI list";
				my $body = {
							 description => "Delete certificate",
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
							 description => "Delete certificate",
							 error       => "true",
							 message     => $errormsg
				};

				&httpResponse({ code => 400, body => $body });
			}
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
					 description => "Delete certificate",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

#####Documentation of POST Upload Certificates####
#**
#  @api {post} /certificates Upload a certificate
#  @apiGroup Certificates
#  @apiName UploadCertificates
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiDescription Upload a certificate
#  @apiVersion 3.0.0
#
#
#  @apiSuccess	{String}	fileupload	The name of the file that will be uploaded. It is important to insert the complete path of the file.
#  @apiSuccess	{String}	filename	The name that will have the file.
#
#
# @apiSuccessExample Success-Response:
# * About to connect() to 46.101.60.162 port 444 (#0)
# *   Trying 46.101.60.162...
# * TCP_NODELAY set
# * connected
# * Connected to 46.101.60.162 (46.101.60.162) port 444 (#0)
# * successfully set certificate verify locations:
# *   CAfile: none
#   CApath: /etc/ssl/certs
# * SSLv3, TLS handshake, Client hello (1):
# * SSLv3, TLS handshake, Server hello (2):
# * SSLv3, TLS handshake, CERT (11):
# * SSLv3, TLS handshake, Server key exchange (12):
# * SSLv3, TLS handshake, Server finished (14):
# * SSLv3, TLS handshake, Client key exchange (16):
# * SSLv3, TLS change cipher, Client hello (1):
# * SSLv3, TLS handshake, Finished (20):
# * SSLv3, TLS change cipher, Client hello (1):
# * SSLv3, TLS handshake, Finished (20):
# * SSL connection using ECDHE-RSA-AES256-SHA
# * Server certificate:
# *        subject: C=ES; ST=Spain; L=Spain; O=Sofintel; OU=Telecommunications; CN=Zen Load Balancer; emailAddress=zenloadbalancer-support@lists.sourceforge.net
# *        start date: 2011-01-12 14:49:03 GMT
# *        expire date: 2021-01-09 14:49:03 GMT
# *        issuer: C=ES; ST=Spain; L=Spain; O=Sofintel; OU=Telecommunications; CN=Zen Load Balancer; emailAddress=zenloadbalancer-support@lists.sourceforge.net
# *        SSL certificate verify result: self signed certificate (18), continuing anyway.
# * Server auth using Basic with user 'zapi'
# > POST /zapi/v3/zapi.cgi/certificates HTTP/1.1
# > Authorization: Basic emFwaTpONk90M2pkdUZmZjRTbkU=
# > User-Agent: curl/7.26.0
# > Host: 46.101.60.162:444
# > Accept: */*
# > ZAPI_KEY: l2ECjvrqitQZULPXbmwMV6luyooQ47SGJhn3LeX1KV6KNKa5uZfJqVVBnEJF4N2Cy
# > Content-Length: 2676
# > Expect: 100-continue
# > Content-Type: multipart/form-data; boundary=----------------------------c44e4423a51c
# >
# * HTTP 1.1 or later with persistent connection, pipelining supported
# < HTTP/1.1 100 Continue
# * additional stuff not fine transfer.c:1037: 0 0
# * additional stuff not fine transfer.c:1037: 0 0
# * additional stuff not fine transfer.c:1037: 0 0
# * additional stuff not fine transfer.c:1037: 0 0
# * HTTP 1.1 or later with persistent connection, pipelining supported
# < HTTP/1.1 200 OK
# < Transfer-Encoding: chunked
# < Date: Fri, 28 Aug 2015 08:36:46 GMT
# < Server: Cherokee/1.2.104 (UNIX)
# < Content-Type: text/html; charset=utf-8
# <
# * Connection #0 to host 46.101.60.162 left intact
# * Closing connection #0
# * SSLv3, TLS alert, Client hello (1):
#
#@apiExample {curl} Example Usage:
#       curl -v --tcp-nodelay --tlsv1 -k -X POST -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#       -u zapi:<password> -F fileupload=@newcert.pem -F filename=newcert.pem
#        https://<zenlb_server>:444/zapi/v3/zapi.cgi/certificates
#
#@apiSampleRequest off
#
#**

#upload .pem certs
sub upload_certs # ()
{

#
# Curl command:
#
# curl -v --tcp-nodelay --tlsv1 -X POST -k -H "ZAPI_KEY: 2bJUdMSHyAhsDYeHJnVHqw7kgN3lPl7gNoWyIej4gjkjpkmPDP9mAU5uUmRg4IHtT" -F fileupload=@/opt/example.pem -F filename=example.pem https://46.101.46.14:444/zapi/v3/zapi.cgi/certificates
#

	my $upload_filehandle = shift;
	my $filename = shift;

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

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		&zenlog( "ZAPI error, trying to upload a certificate." );

		# Error
		my $errormsg = "Error uploading certificate file";
		my $body = {
					 description => "Upload certificate file.",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

#upload .pem certs
sub upload_activation_certificate # ()
{

#
# Curl command:
#
# curl -v --tcp-nodelay --tlsv1 -X POST -k -H "ZAPI_KEY: 2bJUdMSHyAhsDYeHJnVHqw7kgN3lPl7gNoWyIej4gjkjpkmPDP9mAU5uUmRg4IHtT" -F certificate=@/example.pem https://46.101.46.14:444/zapi/v3/zapi.cgi/certificates/activation
#

	my $q = &getCGI();
	my $filename   = 'zlbcertfile.pem';
	my $upload_data = $q->upload( "certificate" );

	if ( <$upload_data> )
	{
		open ( my $uploadfile, '>', "$basedir/$filename" ) or die "$!";
		binmode $uploadfile;
		print { $uploadfile } <$upload_data>;
		close $uploadfile;

		&checkActivationCertificate();

		&httpResponse({ code => 200 });
	}
	else
	{
		&zenlog( "ZAPI error, trying to upload activation certificate." );

		# Error
		my $errormsg = "Error uploading activation certificate file";

		my $body = {
					   description => "Upload activation certificate file.",
					   error       => "true",
					   message     => $errormsg,
		};

		&httpResponse({ code => 400, body => $body });
	}
}

1;
