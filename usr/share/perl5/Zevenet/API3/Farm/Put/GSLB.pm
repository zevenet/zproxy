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

sub modify_gslb_farm    # ( $json_obj,	$farmname )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $farmname = shift;

	my $description = "Modify farm";

	# Flags
	my $reload_flag  = "false";
	my $restart_flag = "false";
	my $error        = "false";
	my $status;
	my $changedname = "false";

	include 'Zevenet::IPDS::Base';

	# flag to reset IPDS rules when the farm changes the name.
	my $farmname_old;
	my $ipds = &getIPDSfarmsRules_zapiv3( $farmname );

	my $errormsg;

	# Check that the farm exists
	if ( !&getFarmExists( $farmname ) )
	{
		# Error
		$errormsg = "The farmname $farmname does not exist.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 404, body => $body } );
	}

	if ( $errormsg =
		 &getValidOptParams( $json_obj, ["vip", "vport", "newfarmname"] ) )
	{
		# Error
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}

	&runIPDSStopByFarm( $farmname );

	# Get current vip & vport
	my $vip   = &getFarmVip( "vip",  $farmname );
	my $vport = &getFarmVip( "vipp", $farmname );

	######## Functions

	# Modify Farm's Name
	if ( exists ( $json_obj->{ newfarmname } ) )
	{
		unless ( &getFarmStatus( $farmname ) eq 'down' )
		{
			&zenlog(
				"Error trying to modify a gslb farm $farmname, cannot change the farm name while it is running",
				"error", "GSLB"
			);

			my $errormsg = 'Cannot change the farm name while running';

			my $body = {
						 description => "Modify farm",
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 400, body => $body } );
		}

		my $newfstat;
		if ( $json_obj->{ newfarmname } =~ /^$/ )
		{
			$error = "true";
			&zenlog(
				"Error trying to modify a gslb farm $farmname, invalid new farm name, can't be blank.",
				"error", "GSLB"
			);
		}
		else
		{
			# Check if farmname has correct characters (letters, numbers and hyphens)
			if ( $json_obj->{ newfarmname } =~ /^[a-zA-Z0-9\-]*$/ )
			{
				if ( $json_obj->{ newfarmname } ne $farmname )
				{
					#Check if the new farm's name alredy exists
					my $newffile = &getFarmFile( $json_obj->{ newfarmname } );
					if ( $newffile != -1 )
					{
						$error = "true";
						&zenlog(
							"Error trying to modify a gslb farm $farmname, the farm $json_obj->{newfarmname} already exists, try another name.",
							"error", "GSLB"
						);
					}
					else
					{
						my $oldfstat = &runFarmStop( $farmname, "true" );
						if ( $oldfstat != 0 )
						{
							$error = "true";
							&zenlog(
								"Error trying to modify a gslb farm $farmname, the farm is not disabled, are you sure it's running?",
								"error", "GSLB"
							);
						}
						else
						{
							#Change farm name
							my $fnchange = &setNewFarmName( $farmname, $json_obj->{ newfarmname } );
							$changedname = "true";

							if ( $fnchange == -1 )
							{
								&error = "true";
								&zenlog(
									"Error trying to modify a gslb farm $farmname, the name of the farm can't be modified, delete the farm and create a new one.",
									"error", "GSLB"
								);
							}
							elsif ( $fnchange == -2 )
							{
								$error = "true";
								&zenlog(
									"Error trying to modify a gslb farm $farmname, invalid new farm name, the new name can't be empty.",
									"error", "GSLB"
								);

								#~ $newfstat = &runFarmStart( $farmname, "true" );
								if ( $newfstat != 0 )
								{
									$error = "true";
									&zenlog(
										"Error trying to modify a gslb farm $farmname, the farm isn't running, check if the IP address is up and the PORT is in use.",
										"error", "GSLB"
									);
								}
							}
							else
							{
								$farmname_old = $farmname;
								$farmname     = $json_obj->{ newfarmname };

								#~ $newfstat = &runFarmStart( $farmname, "true" );
								if ( $newfstat != 0 )
								{
									$error = "true";
									&zenlog(
										"Error trying to modify a gslb farm $farmname, the farm isn't running, check if the IP address is up and the PORT is in use.",
										"error", "GSLB"
									);
								}
							}
						}
					}
				}
			}
			else
			{
				$error = "true";
				&zenlog( "Error trying to modify a gslb farm $farmname, invalid new farm name.",
						 "error", "GSLB" );
			}
		}
	}

	# Modify only vip
	if ( exists ( $json_obj->{ vip } ) && !exists ( $json_obj->{ vport } ) )
	{
		if ( $json_obj->{ vip } =~ /^$/ )
		{
			$error = "true";
			&zenlog(
				"Error trying to modify a gslb farm $farmname, invalid Virtual IP, can't be blank.",
				"error", "GSLB"
			);
		}
		elsif ( !$json_obj->{ vip } =~ /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/ )
		{
			$error = "true";
			&zenlog( "Error trying to modify a gslb farm $farmname, invalid Virtual IP.",
					 "error", "GSLB" );
		}
		else
		{
			$status = &setFarmVirtualConf( $json_obj->{ vip }, $vport, $farmname );
			if ( $status == -1 )
			{
				$error = "true";
				&zenlog( "Error trying to modify a gslb farm $farmname, invalid Virtual IP.",
						 "error", "GSLB" );
			}
			else
			{
				$restart_flag = "true";
			}
		}
	}

	# Modify only vport
	if ( exists ( $json_obj->{ vport } ) && !exists ( $json_obj->{ vip } ) )
	{
		if ( $json_obj->{ vport } =~ /^$/ )
		{
			$error = "true";
			&zenlog(
				"Error trying to modify a gslb farm $farmname, invalid Virtual port, can't be blank.",
				"error", "GSLB"
			);
		}
		elsif ( !$json_obj->{ vport } =~ /^\d+$/ )
		{
			$error = "true";
			&zenlog( "Error trying to modify a gslb farm $farmname, invalid Virtual port.",
					 "error", "GSLB" );
		}
		else
		{
			$json_obj->{ vport } += 0;
			$status = &setFarmVirtualConf( $vip, $json_obj->{ vport }, $farmname );
			if ( $status == -1 )
			{
				$error = "true";
				&zenlog( "Error trying to modify a gslb farm $farmname, invalid Virtual port.",
						 "error", "GSLB" );
			}
			else
			{
				$restart_flag = "true";
			}
		}
	}

	# Modify both vip & vport
	if ( exists ( $json_obj->{ vip } ) && exists ( $json_obj->{ vport } ) )
	{
		if ( $json_obj->{ vip } =~ /^$/ )
		{
			$error = "true";
			&zenlog(
				"Error trying to modify a gslb farm $farmname, invalid Virtual IP, can't be blank.",
				"error", "GSLB"
			);
		}
		elsif ( !$json_obj->{ vip } =~ /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/ )
		{
			$error = "true";
			&zenlog( "Error trying to modify a gslb farm $farmname, invalid Virtual IP.",
					 "error", "GSLB" );
		}
		else
		{
			if ( exists ( $json_obj->{ vport } ) )
			{
				if ( $json_obj->{ vport } =~ /^$/ )
				{
					$error = "true";
					&zenlog(
						"Error trying to modify a gslb farm $farmname, invalid Virtual port, can't be blank.",
						"error", "GSLB"
					);
				}
				elsif ( !$json_obj->{ vport } =~ /^\d+$/ )
				{
					$error = "true";
					&zenlog( "Error trying to modify a gslb farm $farmname, invalid Virtual port.",
							 "error", "GSLB" );
				}
				else
				{
					$json_obj->{ vport } += 0;
					$status =
					  &setFarmVirtualConf( $json_obj->{ vip }, $json_obj->{ vport }, $farmname );
					if ( $status == -1 )
					{
						$error = "true";
						&zenlog(
							"Error trying to modify a gslb farm $farmname, invalid Virtual port or invalid Virtual IP.",
							"error", "GSLB"
						);
					}
					else
					{
						$restart_flag = "true";
					}
				}
			}
		}
	}

	# Check errors and print JSON
	if ( $error ne "true" )
	{
		&zenlog( "Success, some parameters have been changed in farm $farmname.",
				 "error", "GSLB" );

		&runIPDSStartByFarm( $farmname );

		if ( $changedname ne "true" )
		{
			# Success
			my $body = {
				description => "Modify farm $farmname",
				params      => $json_obj,
				info =>
				  "There're changes that need to be applied, stop and start farm to apply them!"
			};

			if ( &getFarmStatus( $farmname ) eq 'up' )
			{
				&setFarmRestart( $farmname );
				$body->{ status } = 'needed restart';
			}

			&httpResponse( { code => 200, body => $body } );
		}
		else
		{
			# Success
			my $body = {
						 description => "Modify farm $farmname",
						 params      => $json_obj,
			};

			&httpResponse( { code => 200, body => $body } );
		}
	}
	else
	{
		&zenlog(
			"Error trying to modify a gslb farm $farmname, it's not possible to modify the farm.",
			"error", "GSLB"
		);

		# Error
		$errormsg = "Errors found trying to modify farm $farmname";
		my $body = {
					 description => "Modify farm $farmname",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}
}

# Get all IPDS rules applied to a farm
sub getIPDSfarmsRules_zapiv3
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $farmName = shift;

	require Config::Tiny;

	my $rules;
	my $fileHandle;
	my @dosRules        = ();
	my @blacklistsRules = ();
	my @rblRules        = ();

	my $dosConf        = &getGlobalConfiguration( 'dosConf' );
	my $blacklistsConf = &getGlobalConfiguration( 'blacklistsConf' );
	my $rblPath        = &getGlobalConfiguration( 'configdir' ) . "/ipds/rbl";
	my $rblConf        = "$rblPath/rbl.conf";

	if ( -e $dosConf )
	{
		$fileHandle = Config::Tiny->read( $dosConf );
		foreach my $key ( keys %{ $fileHandle } )
		{
			if ( defined $fileHandle->{ $key }->{ 'farms' }
				 && $fileHandle->{ $key }->{ 'farms' } =~ /( |^)$farmName( |$)/ )
			{
				push @dosRules, $key;
			}
		}
	}

	if ( -e $blacklistsConf )
	{
		$fileHandle = Config::Tiny->read( $blacklistsConf );
		foreach my $key ( keys %{ $fileHandle } )
		{
			if ( defined $fileHandle->{ $key }->{ 'farms' }
				 && $fileHandle->{ $key }->{ 'farms' } =~ /( |^)$farmName( |$)/ )
			{
				push @blacklistsRules, $key;
			}
		}
	}

	if ( -e $rblConf )
	{
		$fileHandle = Config::Tiny->read( $rblConf );
		foreach my $key ( keys %{ $fileHandle } )
		{
			if ( defined $fileHandle->{ $key }->{ 'farms' }
				 && $fileHandle->{ $key }->{ 'farms' } =~ /( |^)$farmName( |$)/ )
			{
				push @rblRules, $key;
			}
		}
	}

	$rules =
	  { dos => \@dosRules, blacklists => \@blacklistsRules, rbl => \@rblRules };
	return $rules;
}

1;
