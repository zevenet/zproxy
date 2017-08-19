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

sub move_services
{
	my ( $json_obj, $farmname, $service ) = @_;

	require Zevenet::Farm::HTTP::Service;

	my @services = &getHTTPFarmServices( $farmname );
	my $services_num = scalar @services;
	my $description = "Move service";
	my $moveservice;
	my $errormsg;

	# validate FARM NAME
	if ( &getFarmFile( $farmname ) == -1 ) {
		# Error
		$errormsg = "The farmname $farmname does not exists.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}
	elsif ( ! grep ( /^$service$/, @services ) )
	{
		$errormsg = "$service not found.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};
		&httpResponse({ code => 404, body => $body });
	}

	# Move services
	else
	{
		$errormsg = &getValidOptParams( $json_obj, ["position"] );

		if ( !$errormsg )
		{
			if ( !&getValidFormat( 'service_position', $json_obj->{ 'position' } ) )
			{
				$errormsg = "Error in service position format.";
			}
			else
			{
				my $srv_position = &getFarmVSI( $farmname, $service );
				if ( $srv_position == $json_obj->{ 'position' } )
				{
					$errormsg = "The service already is in required position.";
				}
				elsif ( $services_num <= $json_obj->{ 'position' } )
				{
					$errormsg = "The required position is bigger than number of services.";
				}

				# select action
				elsif ( $srv_position > $json_obj->{ 'position' } )
				{
					$moveservice = "up";
				}
				else
				{
					$moveservice = "down";
				}

				if ( !$errormsg )
				{
					# stopping farm
					require Zevenet::Farm::Base;

					my $farm_status = &getFarmStatus( $farmname );
					if ( $farm_status eq 'up' )
					{
						if ( &runFarmStop( $farmname, "true" ) != 0 )
						{
							$errormsg = "Error stopping the farm.";
						}
						else
						{
							&zenlog( "Farm stopped successful." );
						}
					}

					if ( !$errormsg )
					{
						# move service until required position
						while ( $srv_position != $json_obj->{ 'position' } )
						{
							#change configuration file
							&moveServiceFarmStatus( $farmname, $moveservice, $service );
							&moveService( $farmname, $moveservice, $service );

							$srv_position = &getFarmVSI( $farmname, $service );
						}

						# start farm if his status was up
						if ( $farm_status eq 'up' )
						{
							if ( &runFarmStart( $farmname, "true" ) == 0 )
							{
								&setHTTPFarmBackendStatus( $farmname );

								require Zevenet::Cluster;
								&runZClusterRemoteManager( 'farm', 'restart', $farmname );

								&zenlog( "$service was moved successful." );
							}
							else
							{
								$errormsg = "The $farmname farm hasn't been restarted";
							}
						}

						my $body =
						  { description => $description, params => $json_obj, message => $errormsg, };
						&httpResponse( { code => 200, body => $body } );
					}
				}
			}
		}
	}

	my $body =
	  { description => $description, error => "true", message => $errormsg };
	&httpResponse( { code => 400, body => $body } );
}

1;
