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

# GET /system/ssh
sub get_ssh
{
	include 'Zevenet::System::SSH';

	my $desc = "Get ssh";
	my $ssh  = &getSsh();

	return &httpResponse( { code => 200, body => { description => $desc, params => $ssh } } );
}

#  POST /system/ssh
sub set_ssh
{
	my $json_obj = shift;

	include 'Zevenet::System::SSH';

	my $desc = "Post ssh";
	my $sshIp;
	$sshIp = $json_obj->{ 'listen' } if ( exists $json_obj->{ 'listen' } );

	my @allowParams = ( "port", "listen" );
	my $param_msg = &getValidOptParams( $json_obj, \@allowParams );

	if ( $param_msg )
	{
		return &httpErrorResponse( code => 400, desc => $desc, msg => $param_msg );
	}

	if ( !&getValidFormat( "port", $json_obj->{ 'port' } ) )
	{
		my $msg = "Port hasn't a correct format.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# check if listen exists
	if ( exists $json_obj->{ 'listen' } && $json_obj->{ 'listen' } ne '*' )
	{
		require Zevenet::Net::Interface;

		my $flag;
		foreach my $iface ( @{ &getActiveInterfaceList() } )
		{
			if ( $sshIp eq $iface->{ addr } )
			{
				if ( $iface->{ type } eq 'virtual' )    # discard virtual interfaces
				{
					my $msg = "Virtual interface canot be configurate as http interface.";
					return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
				}

				$flag = 1;
				last;
			}
		}

		unless ( $flag )
		{
			my $msg = "Ip $json_obj->{ 'listen' } not found in system.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

	my $error = &setSsh( $json_obj );
	if ( $error )
	{
		my $msg = "There was a error modifying ssh.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $dns = &getSsh();
	return &httpResponse( { code => 200, body => { description => $desc, params => $dns } } );
}

1;
