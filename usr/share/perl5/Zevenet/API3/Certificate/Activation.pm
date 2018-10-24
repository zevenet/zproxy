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

include 'Zevenet::Certificate';

# GET /certificates/activation
sub get_activation_certificate_info    # ()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $description   = "Activation certificate information";
	my $cert_filename = 'zlbcertfile.pem';
	my $cert_dir      = &getGlobalConfiguration( 'basedir' );

	if ( -f "$cert_dir\/$cert_filename" )
	{
		require Zevenet::Certificate;
		my @cert_info = &getCertData( $cert_filename );
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
		my $errormsg = "There is no activation certificate installed";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}
}

# DELETE /certificates/activation
sub delete_activation_certificate    # ( $cert_filename )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	require Zevenet::Certificate;

	my $description   = "Delete activation certificate";
	my $cert_filename = 'zlbcertfile.pem';

	if ( &delCert_activation( $cert_filename ) )
	{
		# Success
		my $message = "The activation certificate has been deleted";
		my $body = {
					 description => $description,
					 success     => "true",
					 message     => $message
		};

		&httpResponse( { code => 200, body => $body } );
	}
	else
	{
		my $errormsg = "An error happened deleting the activation certificate";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}
}

# POST /certificates/activation
sub upload_activation_certificate    # ()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

#
# Curl command:
#
# curl -kis --tcp-nodelay -X POST -H "ZAPI_KEY: 2bJUd" -H 'Content-Type: application/x-pem-file' https://46.101.46.14:444/zapi/v3/zapi.cgi/certificates/activation --data-binary @hostmane.pem
#

	my $upload_filehandle = shift;

	my $description = "Upload activation certificate";
	my $filename    = 'zlbcertfile.pem';

	if ( $upload_filehandle )
	{
		my $basedir = &getGlobalConfiguration( 'basedir' );

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
		include 'Zevenet::Apt';
		&setAPTRepo;
		&httpResponse( { code => 200, body => $body } );
	}
	else
	{
		&zenlog( "Error trying to upload activation certificate.", "error", "SYSTEM" );

		# Error
		my $errormsg = "Error uploading activation certificate file";

		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse( { code => 400, body => $body } );
	}
}

1;
