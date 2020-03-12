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

use Zevenet::API40::HTTP;

use Zevenet::Net::Interface;
include 'Zevenet::System::HTTP';

# GET /system/http
sub get_http
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
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
		$http->{ 'ip' } = '*';
	}
	else
	{
		$http->{ 'ip' } = $interface->{ 'ip' };
	}
	$http->{ 'port' } = &getHttpServerPort();

	return &httpResponse(
				   { code => 200, body => { description => $desc, params => $http } } );
}

# POST /system/http
sub set_http
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;

	my $desc = "Post http";
	my $httpIp;
	$httpIp = $json_obj->{ 'ip' } if ( exists $json_obj->{ 'ip' } );

	my $params = {
		"ip" => {
			'non_blank'    => 'true',
			'valid_format' => 'ssh_listen',

		},
		"port" => {
					'valid_format' => 'port',
					'non_blank'    => 'true',
		},
		"force" => {
					 'values'    => ["true", "false"],
					 'non_blank' => 'true',
		},
	};

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	if ( exists $json_obj->{ 'ip' } && $json_obj->{ 'ip' } ne '*' )
	{
		my $flag;

		foreach my $iface ( @{ &getActiveInterfaceList() } )
		{
			next unless $httpIp eq $iface->{ addr };

			if ( $iface->{ type } eq 'virtual' )    # discard virtual interfaces
			{
				my $msg = "Virtual interface cannot be configurate as http interface.";
				return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
			}

			$flag = 1;
			last;
		}

		unless ( $flag )
		{
			my $msg = "Ip not found in system.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

	unless ( exists $json_obj->{ force } and $json_obj->{ force } eq 'true' )
	{
		my $msg =
		  "The web server will be restarted and won't be accessible from its current IP anymore. "
		  . "The load balancer GUI will be accesible from $json_obj->{ip} when the restart is over. "
		  . "If you agree, execute again sending the parameter 'force'";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	&setHttpServerPort( $json_obj->{ 'port' } ) if ( exists $json_obj->{ 'port' } );
	&setHttpServerIp( $httpIp ) if ( exists $json_obj->{ 'ip' } );

	include 'Zevenet::System::HTTP';
	return
	  &httpErrorResponse(
				  code => 400,
				  desc => $desc,
				  msg => "An error has occurred while trying to restart the HTTP Server"
	  ) if ( &restartHttpServer() );

	my $body = { description => $desc, params => $json_obj };

	return &httpResponse( { code => 200, body => $body } );
}

1;

