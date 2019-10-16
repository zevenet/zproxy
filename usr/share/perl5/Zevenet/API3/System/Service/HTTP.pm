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

use Zevenet::Net::Interface;
include 'Zevenet::System::HTTP';

# GET /system/http
sub get_http
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $description       = "Get http";
	my $httpIp            = &getHttpServerIp();
	my $allInterfaces_aux = &getActiveInterfaceList();
	my @interfaces;
	my $interface;

	# add all interfaces
	push @interfaces, { 'dev' => '*', 'ip' => '*' };

	foreach my $iface ( @{ $allInterfaces_aux } )
	{
		push @interfaces, { 'dev' => $iface->{ 'dev' }, 'ip' => $iface->{ 'addr' } };
		if ( $iface->{ 'addr' } eq $httpIp )
		{
			$interface = { 'dev' => $iface->{ 'dev' }, 'ip' => $iface->{ 'addr' } };
		}
	}

	my $http;

	# http is enabled in all interfaces
	if ( !$interface )
	{
		$http->{ 'ip' } = '*';
	}
	else
	{
		$http->{ 'ip' } = $interface->{ 'ip' };
	}
	$http->{ 'port' } = &getHttpServerPort;

	&httpResponse(
			{ code => 200, body => { description => $description, params => $http } } );
}

# POST /system/http
sub set_http
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;

	my $description = "Post http";
	my @allowParams = ( "ip", "port" );
	my $httpIp;
	$httpIp = $json_obj->{ 'ip' } if ( exists $json_obj->{ 'ip' } );
	my $errormsg = &getValidOptParams( $json_obj, \@allowParams );

	if ( !$errormsg )
	{
		if ( !&getValidFormat( "port", $json_obj->{ 'port' } ) )
		{
			$errormsg = "Port hasn't a correct format.";
		}
		else
		{
			if ( exists $json_obj->{ 'ip' } )
			{
				if ( $json_obj->{ 'ip' } ne '*' )
				{
					my $flag;

					foreach my $iface ( @{ &getActiveInterfaceList() } )
					{
						if ( $httpIp eq $iface->{ addr } )
						{
							$flag = 1;
							if ( $iface->{ vini } ne '' )    # discard virtual interfaces
							{
								$errormsg = "Virtual interface canot be configurate as http interface.";
							}
							last;
						}
					}
					$errormsg = "Ip not found in system." if ( !$flag );
				}
			}
			if ( !$errormsg )
			{
				&setHttpServerPort( $json_obj->{ 'port' } ) if ( exists $json_obj->{ 'port' } );
				&setHttpServerIp( $httpIp ) if ( exists $json_obj->{ 'ip' } );
				&logAndRunBG( "/etc/init.d/cherokee restart" );

				&httpResponse(
					{ code => 200, body => { description => $description, params => $json_obj } } );
			}
		}
	}

	my $body =
	  { description => $description, error => "true", message => $errormsg };

	&httpResponse( { code => 400, body => $body } );
}

1;
