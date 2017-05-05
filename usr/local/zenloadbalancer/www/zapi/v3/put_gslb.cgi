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
	my $ipds = &getIPDSfarmsRules( $farmname );
	my $errormsg;

	# Check that the farm exists
	if ( &getFarmFile( $farmname ) == -1 )
	{
		# Error
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
								"ZAPI error, trying to modify a gslb farm $farmname,the farm is not disabled, are you sure it's running?"
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


sub modify_zone_resource # ( $json_obj, $farmname, $zone, $id_resource )
{
	my ( $json_obj, $farmname, $zone, $id_resource ) = @_;

	my $description = "Modify zone resource";
	my $error;

	# validate FARM NAME
	if ( &getFarmFile( $farmname ) == -1 )
	{
		# Error
		my $errormsg = "The farmname $farmname does not exists.";
		my $body = {
					   description => $description,
					   error       => "true",
					   message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	# validate FARM TYPE
	if ( &getFarmType( $farmname ) ne 'gslb' )
	{
		my $errormsg = "Only GSLB profile is supported for this request.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	# validate ZONE
	unless ( grep { $_ eq $zone } &getFarmZones( $farmname ) )
	{
		my $errormsg = "Could not find the requested zone.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	my $backendsvs = &getFarmVS( $farmname, $zone, "resources" );
	my @be = split ( "\n", $backendsvs );
	my ( $resource_line ) = grep { /;index_$id_resource$/ } @be;

	# validate RESOURCE
	unless ( $resource_line )
	{
		my $errormsg = "Could not find the requested resource.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	# read resource
	my $rsc;

	( $rsc->{ name }, $rsc->{ ttl }, $rsc->{ type }, $rsc->{ data }, $rsc->{ id } )
	  = split ( /(?:\t| ;index_)/, $resource_line );

	# Functions
	if ( exists ( $json_obj->{ rname } ) )
	{
		if ( &getValidFormat( 'resource_name', $json_obj->{ rname } ) )
		{
			$rsc->{ name } = $json_obj->{ rname };
		}
		else
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify the resources in a farm $farmname, invalid rname, can't be blank."
			);
		}
	}

	if ( !$error && exists ( $json_obj->{ ttl } ) )
	{
		if ( $json_obj->{ ttl } == undef || ( &getValidFormat( 'resource_ttl', $json_obj->{ ttl } ) && $json_obj->{ ttl } ) )
		{
			if ( $json_obj->{ ttl } == undef )
			{
				$rsc->{ ttl } = '';
			}
			else
			{
				$rsc->{ ttl } = $json_obj->{ ttl };
			}
		}
		else
		{
			$error = "true";
			&zenlog(
				  "ZAPI error, trying to modify the resources in a farm $farmname, invalid ttl."
			);
		}
	}


	my $auxType = $rsc->{ type };
	my $auxData = $rsc->{ data };

	if ( !$error && exists ( $json_obj->{ type } ) )
	{
		if ( &getValidFormat( 'resource_type', $json_obj->{ type } ) )
		{
			$auxType = $json_obj->{ type };
		}
		else
		{
			$error = "true";
			&zenlog(
				 "ZAPI error, trying to modify the resources in a farm $farmname, invalid type."
			);
		}
	}

	if ( !$error && exists ( $json_obj->{ rdata } ) )
	{
		$auxData = $json_obj->{ rdata };
	}
	
	# validate RESOURCE DATA
	unless ( ! grep ( /$auxData/, &getGSLBFarmServices ( $farmname ) && $auxType eq 'DYNA' ) && 
						&getValidFormat( "resource_data_$auxType", $auxData ) )
	{
		my $errormsg = "If you choose $auxType type, ";
		
		$errormsg .= "RDATA must be a valid IPv4 address," 		if ($auxType eq "A" ); 
		$errormsg .= "RDATA must be a valid IPv6 address,"		if ($auxType eq "AAAA" ); 
		$errormsg .= "RDATA format is not valid,"						if ($auxType eq "NS" ); 
		$errormsg .= "RDATA must be a valid format ( foo.bar.com ),"		if ($auxType eq "CNAME" );
		$errormsg .= "RDATA must be a valid service,"									if ( $auxType eq 'DYNA' ); 
		$errormsg .= "RDATA must be a valid format ( mail.example.com ),"		if ( $auxType eq 'MX' ); 
		$errormsg .= "RDATA must be a valid format ( 10 60 5060 host.example.com ),"		if ( $auxType eq 'SRV' ); 
		$errormsg .= "RDATA must be a valid format ( foo.bar.com ),"			if ( $auxType eq 'PTR' ); 
		# TXT and NAPTR input let all characters
		
		&zenlog( $errormsg );

		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
	else
	{
		$rsc->{ data } = $auxData;
		$rsc->{ type } =  $auxType;
	}
	
	if ( !$error )
	{
		my $status = &setFarmZoneResource(
										   $id_resource,
										   $rsc->{ name },
										   $rsc->{ ttl },
										   $rsc->{ type },
										   $rsc->{ data },
										   $farmname,
										   $zone,
		);

		if ( $status == -1 )
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify the resources in a farm $farmname, it's not possible to modify the resource $id_resource in zone $zone."
			);
		}
		elsif ($status == -2)
		{
			# Error
			my $errormsg = "The resource with ID $id_resource does not exist.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 404, body => $body });
		}
	}

	# Print params
	if ( !$error )
	{
		&zenlog(
			"ZAPI success, some parameters have been changed in the resource $id_resource in zone $zone in farm $farmname."
		);

		# Success
		my $message = "Resource modified";
		my $body = {
					 description => $description,
					 success       => "true",
					 params       => $json_obj,
					 message      => $message,
		};
		
		my $checkConf = &getGSLBCheckConf  ( $farmname );
		if( $checkConf )
		{	
			$body->{ warning }  =  $checkConf;
		}

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		&zenlog(
			"ZAPI error, trying to modify the resources in a farm $farmname, it's not possible to modify the resource."
		);

		# Error
		my $errormsg = "Errors found trying to modify farm $farmname";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}


sub modify_zones # ( $json_obj, $farmname, $zone )
{
	my ( $json_obj, $farmname, $zone ) = @_;

	my $error;
	if ( $farmname =~ /^$/ )
	{
		&zenlog(
			"ZAPI error, trying to modify the zones in a farm $farmname, invalid farmname, can't be blank."
		);

		# Error
		my $errormsg = "Invalid farm name, please insert a valid value.";
		my $body = {
					 description => "Modify zone",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
	
	# Check that the farm exists
	if ( &getFarmFile( $farmname ) == -1 ) {
		# Error
		my $errormsg = "The farmname $farmname does not exists.";
		my $body = {
					 description => "Modify zone",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	$error = "false";

	# Functions
	if ( $json_obj->{ defnamesv } =~ /^$/ )
	{
		$error = "true";
		&zenlog(
			"ZAPI error, trying to modify the zones in a farm $farmname, invalid defnamesv, can't be blank."
		);
	}

	if ( $error eq "false" )
	{
		&setFarmVS( $farmname, $zone, "ns", $json_obj->{ defnamesv } );
		if ( $? eq 0 )
		{
			&runFarmReload( $farmname );
		}
		else
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify the zones in a farm $farmname, it's not possible to modify the zone $zone."
			);
		}
	}

	# Print params
	if ( $error ne "true" )
	{
		&zenlog(
			"ZAPI success, some parameters have been changed  in zone $zone in farm $farmname."
		);

		# Success
		my $body = {
					 description => "Modify zone $zone in farm $farmname",
					 params      => $json_obj,
		};

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		&zenlog(
			"ZAPI error, trying to modify the zones in a farm $farmname, it's not possible to modify the zone $zone."
		);

		# Error
		my $errormsg = "Errors found trying to modify farm $farmname";
		my $body = {
					 description => "Modify zone $zone in farm $farmname",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

1;
