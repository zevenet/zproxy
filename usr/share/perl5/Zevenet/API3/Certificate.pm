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
sub certificates    # ()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	require Zevenet::Certificate;
	my @certificates = &getCertFiles();
	my @out;

	my $cert_dh2048_re = &getValidFormat( 'cert_dh2048' );
	@certificates = grep { !/$cert_dh2048_re/ } @certificates;

	foreach my $certificate ( @certificates )
	{
		my $configdir       = &getGlobalConfiguration( 'certdir' );
		my $certificateFile = "$configdir\/$certificate";

		my $type     = &getCertType( $certificateFile );
		my $cn       = &getCertCN( $certificateFile );
		my $issuer   = &getCertIssuer( $certificateFile );
		my $creation = &getCertCreation( $certificateFile );
		chomp ( $creation );
		my $expiration = &getCertExpiration( $certificateFile );
		chomp ( $expiration );

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

	&httpResponse( { code => 200, body => $body } );
}

# GET /certificates/CERTIFICATE
sub download_certificate    # ()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $cert_filename = shift;

	my $cert_dir = &getGlobalConfiguration( 'certdir' );
	$cert_dir = &getGlobalConfiguration( 'basedir' )
	  if $cert_filename eq 'zlbcertfile.pem';

	open ( my $download_fh, '<', "$cert_dir/$cert_filename" );

	if (    $cert_filename =~ /\.(pem|csr)$/
		 && -f "$cert_dir\/$cert_filename"
		 && $download_fh )
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

		&httpResponse( { code => 400, body => $body } );
	}
}

# GET /certificates/CERTIFICATE/info
sub get_certificate_info    # ()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $cert_filename = shift;

	my $cert_dir = &getGlobalConfiguration( 'certdir' );
	$cert_dir = &getGlobalConfiguration( 'basedir' )
	  if $cert_filename eq 'zlbcertfile.pem';

	if ( $cert_filename =~ /\.(pem|csr)$/ && -f "$cert_dir\/$cert_filename" )
	{
		require Zevenet::Certificate;

		my @cert_info = &getCertData( "$cert_dir\/$cert_filename" );
		my $body;

		# Success
		foreach my $line ( @cert_info )
		{
			$body .= $line;
		}

		&httpResponse( { code => 200, body => $body, type => 'text/plain' } );
	}
	else
	{
		my $errormsg = "Could not get such certificate information";
		my $body = {
					 description => "Get Certificate Information",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}
}

# DELETE /certificates/CERTIFICATE
sub delete_certificate    # ( $cert_filename )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $cert_filename = shift;
	my $description   = "Delete certificate";
	my $errormsg;

	my $cert_dir = &getGlobalConfiguration( 'certdir' );
	$cert_dir = &getGlobalConfiguration( 'basedir' )
	  if $cert_filename eq 'zlbcertfile.pem';

	if ( !-f "$cert_dir\/$cert_filename" )
	{
		$errormsg = "Certificate file not found.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};
		&httpResponse( { code => 404, body => $body } );
	}
	else
	{
		require Zevenet::Certificate;

		my $status = &getFarmCertUsed( $cert_filename );
		if ( $status == 0 )
		{
			# Error
			$errormsg = "File can't be deleted because it's in use by a farm.";
		}
		else
		{
			&delCert( $cert_filename );

			if ( !-f "$cert_dir\/$cert_filename" )
			{
				$errormsg = "The Certificate $cert_filename has been deleted.";

				# Success
				my $body = {
							 description => $description,
							 success     => "true",
							 message     => $errormsg
				};
				&httpResponse( { code => 200, body => $body } );
			}
			else
			{
				$errormsg = "Error, deleting certificate $cert_filename.";
			}
		}
	}

	my $body = {
				 description => $description,
				 error       => "true",
				 message     => $errormsg
	};
	&httpResponse( { code => 400, body => $body } );

}

# POST /certificates (Create CSR)
sub create_csr
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;

	my $description = 'Create CSR';
	my $errormsg;

	my $configdir = &getGlobalConfiguration( 'certdir' );

	if ( -f "$configdir/$json_obj->{name}.csr" )
	{
		&zenlog( "Error $json_obj->{name} already exists.", "error", "LSLB" );

		# Error
		my $errormsg = "$json_obj->{name} already exists.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};
		&httpResponse( { code => 400, body => $body } );
	}

	require Zevenet::Certificate;

	$json_obj->{ name } = &getCleanBlanc( $json_obj->{ name } );

	#~ $json_obj->{ issuer }       = &getCleanBlanc( $json_obj->{ issuer } );
	$json_obj->{ fqdn }         = &getCleanBlanc( $json_obj->{ fqdn } );
	$json_obj->{ division }     = &getCleanBlanc( $json_obj->{ division } );
	$json_obj->{ organization } = &getCleanBlanc( $json_obj->{ organization } );
	$json_obj->{ locality }     = &getCleanBlanc( $json_obj->{ locality } );
	$json_obj->{ state }        = &getCleanBlanc( $json_obj->{ state } );
	$json_obj->{ country }      = &getCleanBlanc( $json_obj->{ country } );
	$json_obj->{ mail }         = &getCleanBlanc( $json_obj->{ mail } );

	if (
		$json_obj->{ name } =~ /^$/

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
		&zenlog( $errormsg, "error", "LSLB" );

		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}

	if ( &checkFQDN( $json_obj->{ fqdn } ) eq "false" )
	{
		$errormsg =
		  "FQDN is not valid. It must be as these examples: domain.com, mail.domain.com, or *.domain.com. Try again.";
		&zenlog( $errormsg, "error", "LSLB" );

		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}

	if ( $json_obj->{ name } !~ /^[a-zA-Z0-9\-]*$/ )
	{
		$errormsg =
		  "Certificate Name is not valid. Only letters, numbers and '-' chararter are allowed. Try again.";
		&zenlog( $errormsg, "error", "LSLB" );

		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}

	$errormsg = &createCSR(
							$json_obj->{ name },
							$json_obj->{ fqdn },
							$json_obj->{ country },
							$json_obj->{ state },
							$json_obj->{ locality },
							$json_obj->{ organization },
							$json_obj->{ division },
							$json_obj->{ mail },
							$CSR_KEY_SIZE,
							""
	);

	if ( !$errormsg )
	{
		my $message = "Certificate $json_obj->{ name } created";
		&zenlog( $message, "info", "LSLB" );

		my $body = {
					 description => $description,
					 success     => "true",
					 message     => $message
		};
		&httpResponse( { code => 200, body => $body } );
	}
	else
	{
		$errormsg = "Error creating certificate $json_obj->{ name }.";
		&zenlog( $errormsg, "error", "LSLB" );

		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};
		&httpResponse( { code => 400, body => $body } );
	}
}

# POST /certificates/CERTIFICATE (Upload PEM)
sub upload_certificate    # ()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

#
# Curl command:
#
# curl -kis -X POST -H "ZAPI_KEY: 2bJUd" --tcp-nodelay -H 'Content-Type: application/x-pem-file' https://192.168.101.20:444/zapi/v3/zapi.cgi/certificates/test.pem --data-binary @/usr/local/zevenet/config/zencert.pem
#

	my $upload_filehandle = shift;
	my $filename          = shift;

	my $description = "Upload PEM certificate";
	my $configdir   = &getGlobalConfiguration( 'certdir' );

	if ( $filename =~ /^\w.+\.pem$/ )
	{
		if ( -f "$configdir/$filename" )
		{
			# Error
			my $errormsg = "Certificate file name already exists";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 400, body => $body } );
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
					 success     => "true",
					 message     => $message
		};

		&httpResponse( { code => 200, body => $body } );
	}
	else
	{
		&zenlog( "Error trying to upload a certificate.", "error", "LSLB" );

		# Error
		my $errormsg = "Invalid certificate file name";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}
}

1;
