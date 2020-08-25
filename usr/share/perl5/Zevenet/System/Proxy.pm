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

=begin nd
Function: getProxy

	Get a object with the proxy configuration

Parameters:
	none - .

Returns:
	hash reference - It returns a hash with the http and https proxy configuration

		{
			"http_proxy" => "https://10.10.21.13:8080",
			"https_proxy" => "https://10.10.21.12:8080",
		}

=cut

sub getProxy
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );

	my $http_proxy  = &getGlobalConfiguration( 'http_proxy' )  // '';
	my $https_proxy = &getGlobalConfiguration( 'https_proxy' ) // '';

	return {
			 'http_proxy'  => $http_proxy,
			 'https_proxy' => $https_proxy,
	};
}

=begin nd
Function: setProxy

	Configure a system proxy

Parameters:
	proxy object - Port number. The object has the following struct:

		{
			"http_proxy" => "https://10.10.21.13:8080",
			"https_proxy" => "https://10.10.21.12:8080",
		}


Returns:
	Integer - 0 on succes or another value on failure

See Also:
	zapi/v3/system.cgi
=cut

sub setProxy
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $proxy_conf ) = @_;

	my $err = 0;

	foreach my $key ( 'http_proxy', 'https_proxy' )
	{
		if ( exists $proxy_conf->{ $key } )
		{
			if ( &setGlobalConfiguration( $key, $proxy_conf->{ $key } ) )
			{
				&zenlog( "Error setting '$key' with the value '$proxy_conf->{ $key }'",
						 "error", "System" );
				$err++;
			}
		}
	}

	if ( $err == 0 )
	{
		require Zevenet::Apt;
		&setAPTProxy;
	}

	return $err;
}

1;

