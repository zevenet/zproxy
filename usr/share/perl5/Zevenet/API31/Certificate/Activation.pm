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

my $cert_path = &getGlobalConfiguration( 'zlbcertfile_path' );

require Zevenet::Certificate;
include 'Zevenet::Certificate::Activation';

# GET /certificates/activation/info
sub get_activation_certificate_info    # ()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $desc = "Activation certificate information";

	unless ( -f $cert_path )
	{
		my $msg = "There is no activation certificate installed";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $cert = &getCertActivationInfo( $cert_path );

	my $params = {
				   days_to_expire => $cert->{ days_to_expire },
				   hostname       => $cert->{ CN },
				   type           => $cert->{ type_cert },
	};
	my $body = { description => $desc, params => $params };

	return &httpResponse( { code => 200, body => $body } );
}

# GET /certificates/activation
sub get_activation_certificate    # ()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	require Zevenet::Certificate;

	my $desc = "Activation certificate";

	unless ( -f $cert_path )
	{
		my $msg = "There is no activation certificate installed";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $cert = &getCertData( $cert_path );

	return &httpResponse( { code => 200, body => $cert, type => 'text/plain' } );
}

# DELETE /certificates/activation
sub delete_activation_certificate    # ( $cert_filename )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $desc = "Delete activation certificate";

	if ( &delCert_activation() )
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
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $upload_data = shift;

	my $desc = "Upload activation certificate";

	unless ( $upload_data )
	{
		my $msg = "Error uploading activation certificate file";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
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
