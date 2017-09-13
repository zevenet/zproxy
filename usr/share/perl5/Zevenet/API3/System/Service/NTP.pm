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

# GET /system/ntp
sub get_ntp
{
	my $description = "Get ntp";
	my $ntp         = &getGlobalConfiguration( 'ntp' );

	&httpResponse(
			 { code => 200, body => { description => $description, params => { "server" => $ntp } } } );
}

#  POST /system/ntp
sub set_ntp
{
	my $json_obj    = shift;
	my $description = "Post ntp";
	my $errormsg;
	my @allowParams = ( "server" );

	$errormsg = &getValidOptParams( $json_obj, \@allowParams );
	if ( !$errormsg )
	{
		if ( !&getValidFormat( "ntp", $json_obj->{ 'server' } ) )
		{
			$errormsg = "NTP hasn't a correct format.";
		}
		else
		{
			$errormsg = &setGlobalConfiguration( 'ntp', $json_obj->{ 'server' } );

			if ( !$errormsg )
			{
				my $ntp = &getGlobalConfiguration( 'ntp' );
				&httpResponse(
						 { code => 200, body => { description => $description, params => $ntp } } );
			}
			else
			{
				$errormsg = "There was a error modifying ntp.";
			}
		}
	}
	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 400, body => $body } );
}

1;
