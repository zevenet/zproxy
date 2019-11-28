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

include 'Zevenet::System::Proxy';
include 'Zevenet::Apt';

# GET /system/proxy
sub get_proxy
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $desc = "Get proxy configuration";

	return &httpResponse(
			 { code => 200, body => { description => $desc, params => &OutProxy() } } );
}

#  POST /system/proxy
sub set_proxy
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;

	my $desc = "Configuring proxy";

	my $params = {
				   "http_proxy" => {
									 'valid_format' => 'http_proxy',
				   },
				   "https_proxy" => {
									  'valid_format' => 'http_proxy',
				   },
	};

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	if ( &setProxy( $json_obj ) )
	{
		my $msg = "There was a error modifying the proxy configuration.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# Proxy needs to be updated in apt module
	&setAPTRepo();

	return &httpResponse(
			 { code => 200, body => { description => $desc, params => &OutProxy() } } );
}

sub OutProxy
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $proxy = &getProxy();

	return {
			 "http_proxy"  => $proxy->{ 'http_proxy' },
			 "https_proxy" => $proxy->{ 'https_proxy' }
	};
}

1;
