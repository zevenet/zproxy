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

# Check RBAC permissions
include 'Zevenet::Certificate';
require Zevenet::User;

# GET /certificates/activation/info
sub get_activation_certificate_info    # ()
{
	require Zevenet::Certificate;

	my $desc          = "Activation certificate information";
	my $cert_filename = 'zlbcertfile.pem';
	my $cert_dir      = &getGlobalConfiguration( 'basedir' );

	unless ( -f "$cert_dir\/$cert_filename" )
	{
		my $msg = "There is no activation certificate installed";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $cert    = &getCertInfo( $cert_filename, $cert_dir );
	my $c_type  = 'temporal';
	my $support = 'N/A';

	if ( $cert->{ key } =~ m/-/ )
	{
		my $c_days = (
			 &getDateEpoc( $cert->{ expiration } ) - &getDateEpoc( $cert->{ creation } ) ) /
		  86400;
		$c_type = ( $c_days > 364 ) ? 'permanent' : 'temporal';
	}
	else
	{
		my $cert_type = $cert->{ type_cert };
		$c_type = ( $cert_type eq 'DE' ) ? 'permanent' : 'temporal';
		my $c_days = (
			 &getDateEpoc( $cert->{ expiration } ) - &getDateEpoc( $cert->{ creation } ) ) /
		  86400;

		if ( $c_type eq 'permanent' )
		{
			if   ( $c_days < 1 ) { $support = 'false'; }
			else                 { $support = 'true' }
		}
	}

	my $params = {
				   days_to_expire  => &getCertDaysToExpire( $cert->{ expiration } ),
				   hostname        => $cert->{ CN },
				   type            => $c_type,
				   certificate_key => $cert->{ key },
				   host_key        => &keycert(),
				   support         => $support
	};
	my $body = { description => $desc, params => $params };

	return &httpResponse( { code => 200, body => $body, type => 'text/plain' } );
}

# GET /certificates/activation
sub get_activation_certificate    # ()
{
	require Zevenet::Certificate;

	my $desc          = "Activation certificate";
	my $cert_filename = 'zlbcertfile.pem';
	my $cert_dir      = &getGlobalConfiguration( 'basedir' );

	unless ( -f "$cert_dir\/$cert_filename" )
	{
		my $msg = "There is no activation certificate installed";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my @cert_info = &getCertData( $cert_filename );
	my $body      = "@cert_info";

	return &httpResponse( { code => 200, body => $body, type => 'text/plain' } );
}

# DELETE /certificates/activation
sub delete_activation_certificate    # ( $cert_filename )
{
	require Zevenet::Certificate;

	my $desc = "Delete activation certificate";

	unless ( &delCert_activation() )
	{
		my $msg = "An error happened deleting the activation certificate";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $msg = "The activation certificate has been deleted";
	my $body = {
				 description => $desc,
				 success     => "true",
				 message     => $msg,
	};

	return &httpResponse( { code => 200, body => $body } );
}

# POST /certificates/activation
#
# Curl command:
#
# curl -kis --tcp-nodelay -X POST -H "ZAPI_KEY: 2bJUd" -H 'Content-Type: application/x-pem-file' https://1.2.3.4:444/zapi/v3/zapi.cgi/certificates/activation --data-binary @hostmane.pem
sub upload_activation_certificate    # ()
{
	my $upload_filehandle = shift;

	my $desc        = "Upload activation certificate";
	my $tmpFilename = 'zlbcertfile.tmp.pem';
	my $filename    = 'zlbcertfile.pem';

	unless ( $upload_filehandle )
	{
		my $msg = "Error uploading activation certificate file";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $basedir = &getGlobalConfiguration( 'basedir' );

	open ( my $cert_filehandle, '>', "$basedir/$tmpFilename" ) or die "$!";
	binmode $cert_filehandle;
	print { $cert_filehandle } $upload_filehandle;
	close $cert_filehandle;

	my $response = &checkActivationCertificate( "$tmpFilename" );

	# A hash reference will be returned for non valid activation certificates
	if ( ref $response )
	{
		# Delete the tmp certificate file
		&zenlog(
				 "The cerfile is incorrect, removing uploaded temporary certificate file",
				 "debug", "certificate" );
		unless ( unlink "$basedir/$tmpFilename" )
		{
			my $msg = "Error deleting new invalid activation certificate file";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
		my $msg =
		  "The certificate file isn't signed by the Zevenet Certificate Authority, please request a new one";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}
	else
	{
		&zenlog(
			   "The certfile is correct, moving the uploaded certificate to the right path",
			   "debug", "certificate" );
		rename ( "$basedir/$tmpFilename", "$basedir/$filename" );
	}

	my $msg = "Activation certificate uploaded";
	my $body = {
				 description => $desc,
				 success     => "true",
				 message     => $msg,
	};

	return &httpResponse( { code => 200, body => $body } );
}

1;
