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

sub modify_datalink_farm    # ( $json_obj, $farmname )
{
	&zenlog(__FILE__ . ":" . __LINE__ . ":" . (caller(0))[3] . "( @_ )", "debug", "PROFILING" );
	my $json_obj = shift;
	my $farmname = shift;

	my $reload_flag    = "false";
	my $restart_flag   = "false";
	my $initial_status = &getFarmStatus( $farmname );
	my $error          = "false";
	my $status;

	####### Functions

	# Check parameters
	foreach my $key ( keys %$json_obj )
	{
		unless ( grep { $key eq $_ } qw(newfarmname algorithm vip) )
		{
			# Error
			my $errormsg = "The parameter $key is invalid.";
			my $body = {
						 description => "Modify farm",
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 400, body => $body } );
		}
	}

	# Modify Farm's Name
	if ( exists ( $json_obj->{ newfarmname } ) )
	{
		unless ( &getFarmStatus( $farmname ) eq 'down' )
		{
			&zenlog(
				"Error trying to modify a datalink farm $farmname, cannot change the farm name while running", "error", "DSLB"
			);

			my $errormsg = 'Cannot change the farm name while running';

			my $body = {
						 description => "Modify farm",
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 400, body => $body } );
		}

		if ( $json_obj->{ newfarmname } =~ /^$/ )
		{
			$error = "true";
			&zenlog(
				"Error trying to modify a datalink farm $farmname, invalid newfarmname, can't be blank.", "error", "DSLB"
			);
		}
		else
		{
			if ( $json_obj->{ newfarmname } ne $farmname )
			{
				#Check if farmname has correct characters (letters, numbers and hyphens)
				if ( $json_obj->{ newfarmname } =~ /^[a-zA-Z0-9\-]*$/ )
				{
					#Check if the new farm's name alredy exists
					my $newffile = &getFarmFile( $json_obj->{ newfarmname } );
					if ( $newffile != -1 )
					{
						$error = "true";
						&zenlog(
							"Error trying to modify a datalink farm $farmname, the farm $json_obj->{newfarmname} already exists, try another name.", "error", "DSLB"
						);
					}
					else
					{
						#Change farm name
						my $fnchange = &setNewFarmName( $farmname, $json_obj->{ newfarmname } );
						if ( $fnchange == -1 )
						{
							&error = "true";
							&zenlog(
								"Error trying to modify a datalink farm $farmname, the name of the farm can't be modified, delete the farm and create a new one.", "error", "DSLB"
							);
						}
						else
						{
							$farmname = $json_obj->{ newfarmname };
						}
					}
				}
				else
				{
					$error = "true";
					&zenlog(
						  "Error trying to modify a datalink farm $farmname, invalid new farm name.", "error", "DSLB"
					);
				}
			}
		}
	}

	# Modify Load Balance Algorithm
	if ( exists ( $json_obj->{ algorithm } ) )
	{
		if ( $json_obj->{ algorithm } =~ /^$/ )
		{
			$error = "true";
			&zenlog(
				"Error trying to modify a datalink farm $farmname, invalid algorithm, can't be blank.", "error", "DSLB"
			);
		}
		if ( $json_obj->{ algorithm } =~ /^weight|prio$/ )
		{
			$status = &setFarmAlgorithm( $json_obj->{ algorithm }, $farmname );
			if ( $status == -1 )
			{
				$error = "true";
				&zenlog(
					"Error trying to modify a datalink farm $farmname, some errors detected trying to modify the algorithm.", "error", "DSLB"
				);
			}
			else
			{
				$restart_flag = "true";
			}
		}
		else
		{
			$error = "true";
			&zenlog(
				 "Error trying to modify a datalink farm $farmname, invalid algorithm.", "error", "DSLB" );
		}
	}

	# Modify Virtual IP and Interface
	if ( exists ( $json_obj->{ vip } ) )
	{
		if ( $json_obj->{ vip } =~ /^$/ )
		{
			$error = "true";
			&zenlog(
				"Error trying to modify a datalink farm $farmname, invalid Virtual IP, can't be blank.", "error", "DSLB"
			);
		}
		elsif ( $json_obj->{ vip } =~ /^[a-zA-Z0-9.]+/ )
		{
			my $fdev = &getInterfaceOfIp( $json_obj->{ vip } );

			if ( ! defined $json_obj->{ vip } || $json_obj->{ vip } eq "" )
			{
				$error = "true";
				&zenlog(
					"Error, trying to modify a datalink farm $farmname, invalid Virtual IP value.", "error", "DSLB"
				);
			}
			elsif ( ! defined $fdev )
			{
				$error = "true";
				&zenlog(
					"Error trying to modify a datalink farm $farmname, invalid Interface value.", "error", "DSLB"
				);
			}
			else
			{
				$status = &setFarmVirtualConf( $json_obj->{ vip }, $fdev, $farmname );
				if ( $status != -1 )
				{
					$restart_flag = "true";
				}
				else
				{
					$error = "true";
					&zenlog(
						"Error trying to modify a datalink farm $farmname, it's not possible to change the farm Virtual IP and interface.", "error", "DSLB"
					);
				}
			}
		}
		else
		{
			$error = "true";
			&zenlog(
				 "Error trying to modify a datalink farm $farmname, invalid vip.", "error", "DSLB"
			);
		}
	}

	# Restart Farm
	if ( $restart_flag eq "true" && $initial_status ne 'down' )
	{
		&runFarmStop( $farmname, "true" );
		&runFarmStart( $farmname, "true" );
		include 'Zevenet::Cluster';
		&runZClusterRemoteManager( 'farm', 'restart', $farmname );
	}

	# Check errors and print JSON
	if ( $error ne "true" )
	{
		&zenlog( "Success, some parameters have been changed in farm $farmname.", "info", "DSLB" );

		# Success
		my $body = {
					 description => "Modify farm $farmname",
					 params      => $json_obj
		};

		&httpResponse( { code => 200, body => $body } );
	}
	else
	{
		&zenlog(
			"Error trying to modify a datalink farm $farmname, it's not possible to modify the farm.", "error", "DSLB"
		);

		# Error
		my $errormsg = "Errors found trying to modify farm $farmname";
		my $body = {
					 description => "Modify farm $farmname",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}
}

1;
