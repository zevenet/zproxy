#!/usr/bin/perl
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

use Zevenet::System;
use Zevenet::API32::HTTP;

# GET /certificates/CERTIFICATE/info
sub get_certificate_info    # ()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $cert_filename = shift;

	require Zevenet::Certificate;

	my $desc     = "Show certificate details";
	my $cert_dir = &getGlobalConfiguration( 'certdir' );
	$cert_dir = &getGlobalConfiguration( 'basedir' )
	  if $cert_filename eq 'zlbcertfile.pem';

	if ( &getValidFormat( 'certificate', $cert_filename )
		 && -f "$cert_dir\/$cert_filename" )
	{
		my $cert = &getCertData( "$cert_dir\/$cert_filename" );

		&httpResponse( { code => 200, body => $cert, type => 'text/plain' } );
	}
	else
	{
		my $msg = "Could not get such certificate information";
		&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}
}

1;
