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

	my $description = "Get ssh";
	my $ssh         = &getSsh();

	&httpResponse(
			 { code => 200, body => { description => $description, params => $ssh } } );
}

#  POST /system/ssh
sub set_ssh
{
	my $json_obj    = shift;

	my $description = "Post ssh";
	my @allowParams = ( "port", "listen" );
	my $sshIp = $json_obj->{ 'listen' } if ( exists $json_obj->{ 'listen' } );
	my $errormsg = &getValidOptParams( $json_obj, \@allowParams );

	if ( !$errormsg )
	{
		if ( !&getValidFormat( "port", $json_obj->{ 'port' } ) )
		{
			$errormsg = "Port hasn't a correct format.";
		}
		else
		{
			# check if listen exists
			if ( exists $json_obj->{ 'listen' } && $json_obj->{ 'listen' } ne '*' )
			{
				my $flag;

				require Zevenet::Net::Interface;

				foreach my $iface ( @{ &getActiveInterfaceList() } )
				{
					if ( $sshIp eq $iface->{ addr } )
					{
						$flag = 1;
						if ( $iface->{ vini } ne '' )    # discard virtual interfaces
						{
							$errormsg = "Virtual interface canot be configurate as http interface.";
						}
						last;
					}
				}

				$errormsg = "Ip $json_obj->{ 'listen' } not found in system." if ( !$flag );
			}

			if ( !$errormsg )
			{
				include 'Zevenet::System::SSH';
				$errormsg = &setSsh( $json_obj );

				if ( !$errormsg )
				{
					my $dns = &getSsh();
					&httpResponse(
							 { code => 200, body => { description => $description, params => $dns } } );
				}
				else
				{
					$errormsg = "There was a error modifying ssh.";
				}
			}
		}
	}

	my $body =
	  { description => $description, error => "true", message => $errormsg };

	&httpResponse( { code => 400, body => $body } );
}

1;
