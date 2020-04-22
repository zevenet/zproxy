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

my $cert_path = &getGlobalConfiguration( 'zlbcertfile_path' );

# GET /certificates/activation
sub get_activation_certificate_info    # ()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $description = "Activation certificate information";

	if ( -f $cert_path )
	{
		require Zevenet::Certificate;
		my $cert = &getCertData( $cert_path );

		&httpResponse( { code => 200, body => $cert, type => 'text/plain' } );
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

	my $description = "Delete activation certificate";

	if ( !&delCert_activation() )
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

	my $upload_data = shift;

	my $desc = "Upload activation certificate";

	unless ( $upload_data )
	{
		my $msg = "Error uploading activation certificate file";
		return
		  &httpResponse(
					   {
						 code => 400,
						 body => { description => $desc, message => $msg, error => "true" }
					   }
		  );
	}

	my $errmsg = &uploadCertActivation( $upload_data );
	if ( $errmsg )
	{
		return
		  &httpErrorResponse(
							  code => 400,
							  desc => $desc,
							  msg  => $errmsg
		  );
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
