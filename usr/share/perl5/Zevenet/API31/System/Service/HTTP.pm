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

use Zevenet::API31::HTTP;

use Zevenet::Net::Interface;
include 'Zevenet::System::HTTP';

# GET /system/http
sub get_http
{
	&zenlog(__FILE__ . ":" . __LINE__ . ":" . (caller(0))[3] . "( @_ )", "debug", "PROFILING" );
	my $desc              = "Get http";
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
		$http->{ 'ip' } = '*' ;
	}
	else
	{
		$http->{ 'ip' } = $interface->{ 'ip' };
	}
	$http->{ 'port' } = &getHttpServerPort;

	&httpResponse(
			{ code => 200, body => { description => $desc, params => $http } } );
}

# POST /system/http
sub set_http
{
	&zenlog(__FILE__ . ":" . __LINE__ . ":" . (caller(0))[3] . "( @_ )", "debug", "PROFILING" );
	my $json_obj = shift;

	my $desc = "Post http";
	my $httpIp;
	$httpIp = $json_obj->{ 'ip' } if ( exists $json_obj->{ 'ip' } );

	my @allowParams = ( "ip", "port" );
	my $param_msg = &getValidOptParams( $json_obj, \@allowParams );

	if ( $param_msg )
	{
		&httpErrorResponse( code => 400, desc => $desc, msg => $param_msg );
	}

	if ( !&getValidFormat( "port", $json_obj->{ 'port' } ) )
	{
		my $msg = "Port hasn't a correct format.";
		&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	if ( exists $json_obj->{ 'ip' } && $json_obj->{ 'ip' } ne '*' )
	{
		my $flag;

		foreach my $iface ( @{ &getActiveInterfaceList() } )
		{
			next unless $httpIp eq $iface->{ addr };

			if ( $iface->{ type } eq 'virtual' )    # discard virtual interfaces
			{
				my $msg = "Virtual interface canot be configurate as http interface.";
				&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
			}

			$flag = 1;
			last;
		}

		unless ( $flag )
		{
			my $msg = "Ip not found in system.";
			&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

	&setHttpServerPort( $json_obj->{ 'port' } ) if ( exists $json_obj->{ 'port' } );
	&setHttpServerIp( $httpIp ) if ( exists $json_obj->{ 'ip' } );
	&logAndRunBG( "/etc/init.d/cherokee restart" );

	my $body = { description => $desc, params => $json_obj };

	&httpResponse( { code => 200, body => $body } );
}

1;
