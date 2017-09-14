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

# GET /certificates/activation
sub get_activation_certificate_info # ()
{
	require Zevenet::Certificate;

	my $desc          = "Activation certificate information";
	my $cert_filename = 'zlbcertfile.pem';
	my $cert_dir      = &getGlobalConfiguration( 'basedir' );

	unless ( -f "$cert_dir\/$cert_filename" )
	{
		my $msg = "There is no activation certificate installed";
		&httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my @cert_info = &getCertData( $cert_filename );
	my $body = "@cert_info";

	&httpResponse({ code => 200, body => $body, type => 'text/plain' });
}

# DELETE /certificates/activation
sub delete_activation_certificate # ( $cert_filename )
{
	require Zevenet::Certificate;

	my $desc          = "Delete activation certificate";
	my $cert_filename = 'zlbcertfile.pem';

	unless ( &delCert( $cert_filename ) )
	{
		my $msg = "An error happened deleting the activation certificate";
		&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $msg = "The activation certificate has been deleted";
	my $body = {
				 description => $desc,
				 success     => "true",
				 message     => $msg,
	};

	&httpResponse({ code => 200, body => $body });
}

# POST /certificates/activation
#
# Curl command:
#
# curl -kis --tcp-nodelay -X POST -H "ZAPI_KEY: 2bJUd" -H 'Content-Type: application/x-pem-file' https://1.2.3.4:444/zapi/v3/zapi.cgi/certificates/activation --data-binary @hostmane.pem
sub upload_activation_certificate # ()
{
	my $upload_filehandle = shift;

	my $desc = "Upload activation certificate";
	my $filename = 'zlbcertfile.pem';

	unless ( $upload_filehandle )
	{
		my $msg = "Error uploading activation certificate file";
		&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $basedir = &getGlobalConfiguration('basedir');

	open ( my $cert_filehandle, '>', "$basedir/$filename" ) or die "$!";
	binmode $cert_filehandle;
	print { $cert_filehandle } $upload_filehandle;
	close $cert_filehandle;

	&checkActivationCertificate();

	my $msg = "Activation certificate uploaded";
	my $body = {
				 description => $desc,
				 success     => "true",
				 message     => $msg,
	};

	&httpResponse({ code => 200, body => $body });
}

1;
