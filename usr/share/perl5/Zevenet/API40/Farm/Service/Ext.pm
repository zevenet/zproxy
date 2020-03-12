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

sub modify_service_cookie_insertion
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farmname, $service, $json_obj ) = @_;

	include 'Zevenet::Farm::HTTP::Service::Ext';

	my $ci = &getHTTPServiceCookieIns( $farmname, $service );
	$ci->{ enabled } = ( $ci->{ enabled } eq 'true' ) ? 1 : 0;

	if ( exists ( $json_obj->{ cookieinsert } ) )
	{
		if ( $json_obj->{ cookieinsert } eq "true" )
		{
			$ci->{ enabled } = 1;
		}
		elsif ( $json_obj->{ cookieinsert } eq "false" )
		{
			$ci->{ enabled } = 0;
		}
	}

	if ( exists $json_obj->{ cookiename } )
	{
		$ci->{ name } = $json_obj->{ cookiename };
	}

	if ( exists $json_obj->{ cookiedomain } )
	{
		$ci->{ domain } = $json_obj->{ cookiedomain };
	}

	if ( exists $json_obj->{ cookiepath } )
	{
		$ci->{ path } = $json_obj->{ cookiepath };
	}

	if ( exists $json_obj->{ cookiettl } )
	{
		$ci->{ ttl } = $json_obj->{ cookiettl };
	}

	&setHTTPServiceCookieIns( $farmname, $service, $ci );
	return;
}

1;

