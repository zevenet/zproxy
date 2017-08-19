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

sub modify_gslb_farm # ( $json_obj,	$farmname )
{
	my $json_obj = shift;
	my $farmname = shift;

	my $description = "Modify farm";

	# Flags
	my $reload_flag  = "false";
	my $restart_flag = "false";
	my $error        = "false";
	my $status;
	my $changedname = "false";

	# flag to reset IPDS rules when the farm changes the name.
	my $farmname_old;
	my $ipds;

	if ( eval { Zevenet::IPDS; } )
	{
		require Zevenet::IPDS::Blacklist;
		require Zevenet::IPDS::DoS;
		my $ipds = &getIPDSfarmsRules( $farmname );
	}

	my $errormsg;

	# Check that the farm exists
	if ( &getFarmFile( $farmname ) == -1 )
	{
		$errormsg = "The farmname $farmname does not exists.";
		my $body = {
					   description => $description,
					   error       => "true",
					   message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}


	if ( $errormsg = &getValidOptParams ( $json_obj, [ "vip", "vport", "newfarmname" ] ) )
	{
		# Error
		my $body = {
					   description => $description,
					   error       => "true",
					   message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

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
				"ZAPI error, trying to modify a gslb farm $farmname, cannot change the farm name while running"
			);

			my $errormsg = 'Cannot change the farm name while running';

			my $body = {
						 description => "Modify farm",
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}

		my $newfstat;
		if ( $json_obj->{ newfarmname } =~ /^$/ )
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify a gslb farm $farmname, invalid newfarmname, can't be blank."
			);
		}
		else
		{
			# Check if farmname has correct characters (letters, numbers and hyphens)
			if ( $json_obj->{ newfarmname } =~ /^[a-zA-Z0-9\-]*$/ )
			{
				if ($json_obj->{newfarmname} ne $farmname)
				{
					#Check if the new farm's name alredy exists
					my $newffile = &getFarmFile( $json_obj->{ newfarmname } );
					if ( $newffile != -1 )
					{
						$error = "true";
						&zenlog(
							"ZAPI error, trying to modify a gslb farm $farmname, the farm $json_obj->{newfarmname} already exists, try another name."
						);
					}
					else
					{
						my $oldfstat = &runFarmStop( $farmname, "true" );
						if ( $oldfstat != 0 )
						{
							$error = "true";
							&zenlog(
								"ZAPI error, trying to modify a gslb farm $farmname, the farm is not disabled, are you sure it's running?"
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
									"ZAPI error, trying to modify a gslb farm $farmname, the name of the farm can't be modified, delete the farm and create a new one."
								);
							}
							elsif ( $fnchange == -2 )
							{
								$error = "true";
								&zenlog(
									"ZAPI error, trying to modify a gslb farm $farmname, invalid newfarmname, the new name can't be empty."
								);
								#~ $newfstat = &runFarmStart( $farmname, "true" );
								if ( $newfstat != 0 )
								{
									$error = "true";
									&zenlog(
										"ZAPI error, trying to modify a gslb farm $farmname, the farm isn't running, chick if the IP address is up and the PORT is in use."
									);
								}
							}
							else
							{
								$farmname_old = $farmname; 
								$farmname = $json_obj->{ newfarmname };
								#~ $newfstat = &runFarmStart( $farmname, "true" );
								if ( $newfstat != 0 )
								{
									$error = "true";
									&zenlog(
										"ZAPI error, trying to modify a gslb farm $farmname, the farm isn't running, chick if the IP address is up and the PORT is in use."
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
				&zenlog(
						   "ZAPI error, trying to modify a gslb farm $farmname, invalid newfarmname." );
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
				"ZAPI error, trying to modify a gslb farm $farmname, invalid vip, can't be blank."
			);
		}
		elsif ( !$json_obj->{ vip } =~ /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/ )
		{
			$error = "true";
			&zenlog(
					  "ZAPI error, trying to modify a gslb farm $farmname, invalid vip." );
		}
		else
		{
			$status = &setFarmVirtualConf( $json_obj->{ vip }, $vport, $farmname );
			if ( $status == -1 )
			{
				$error = "true";
				&zenlog(
						  "ZAPI error, trying to modify a gslb farm $farmname, invalid vip." );
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
				"ZAPI error, trying to modify a gslb farm $farmname, invalid vport, can't be blank."
			);
		}
		elsif ( !$json_obj->{ vport } =~ /^\d+$/ )
		{
			$error = "true";
			&zenlog(
					  "ZAPI error, trying to modify a gslb farm $farmname, invalid vport." );
		}
		else
		{
			$json_obj->{ vport } += 0;
			$status = &setFarmVirtualConf( $vip, $json_obj->{ vport }, $farmname );
			if ( $status == -1 )
			{
				$error = "true";
				&zenlog(
						  "ZAPI error, trying to modify a gslb farm $farmname, invalid vport." );
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
				"ZAPI error, trying to modify a gslb farm $farmname, invalid vip, can't be blank."
			);
		}
		elsif ( !$json_obj->{ vip } =~ /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/ )
		{
			$error = "true";
			&zenlog(
					  "ZAPI error, trying to modify a gslb farm $farmname, invalid vip." );
		}
		else
		{
			if ( exists ( $json_obj->{ vport } ) )
			{
				if ( $json_obj->{ vport } =~ /^$/ )
				{
					$error = "true";
					&zenlog(
						"ZAPI error, trying to modify a gslb farm $farmname, invalid vport, can't be blank."
					);
				}
				elsif ( !$json_obj->{ vport } =~ /^\d+$/ )
				{
					$error = "true";
					&zenlog(
							  "ZAPI error, trying to modify a gslb farm $farmname, invalid vport." );
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
							"ZAPI error, trying to modify a gslb farm $farmname, invalid vport or invalid vip."
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
		&zenlog(
				  "ZAPI success, some parameters have been changed in farm $farmname." );

		if ( eval { Zevenet::IPDS; } )
		{
			# update the ipds rule applied to the farm
			if ( !$farmname_old )
			{
				&setBLReloadFarmRules ( $farmname );
				&setDOSReloadFarmRules ( $farmname );
			}
			# create new rules with the new farmname
			else
			{
				foreach my $list ( @{ $ipds->{ 'blacklists' } } )
				{
					&setBLRemFromFarm( $farmname_old, $list );
					&setBLApplyToFarm( $farmname, $list );
				}
				foreach my $rule ( @{ $ipds->{ 'dos' } } )
				{
					&setDOSDeleteRule( $rule, $farmname_old );
					&setDOSCreateRule( $rule, $farmname );
				}
			}
		}

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

			&httpResponse({ code => 200, body => $body });
		}
		else
		{
			# Success
			my $body = {
						 description => "Modify farm $farmname",
						 params      => $json_obj,
			};

			&httpResponse({ code => 200, body => $body });
		}
	}
	else
	{
		&zenlog(
			"ZAPI error, trying to modify a gslb farm $farmname, it's not possible to modify the farm."
		);

		# Error
		$errormsg = "Errors found trying to modify farm $farmname";
		my $body = {
					 description => "Modify farm $farmname",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

1;
