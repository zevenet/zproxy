#!/usr/bin/perl -w

use strict;

# PUT /farms/<farmname> Modify a l4xnat Farm

sub modify_l4xnat_farm # ( $json_obj, $farmname )
{
	my $json_obj = shift;
	my $farmname = shift;

	# Flags
	my $reload_flag  = "false";
	my $restart_flag = "false";
	my $error        = "false";
	my $status;
	my $initialStatus = &getFarmStatus( $farmname );
	
	# flag to reset IPDS rules when the farm changes the name.
	my $farmname_old;
	my $ipds = &getIPDSfarmsRules( $farmname );

	# Check that the farm exists
	if ( &getFarmFile( $farmname ) == -1 )
	{
		# Error
		my $errormsg = "The farmname $farmname does not exists.";
		my $body = {
					 description => "Modify farm",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	# Get current vip & vport
	my $vip   = &getFarmVip( "vip",  $farmname );
	my $vport = &getFarmVip( "vipp", $farmname );

	####### Functions

	# Modify Farm's Name
	if ( exists ( $json_obj->{ newfarmname } ) )
	{
		unless ( &getFarmStatus( $farmname ) eq 'down' )
		{
			&zenlog(
				"ZAPI error, trying to modify a l4xnat farm $farmname, cannot change the farm name while running"
			);

			my $errormsg = 'Cannot change the farm name while running';

			my $body = {
						 description => "Modify farm",
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}

		if ( $json_obj->{ newfarmname } =~ /^$/ )
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify a l4xnat farm $farmname, invalid newfarmname, can't be blank."
			);
		}
		else
		{
			if ($json_obj->{newfarmname} ne $farmname)
			{
				#Check if farmname has correct characters (letters, numbers and hyphens)
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
								"ZAPI error, trying to modify a l4xnat farm $farmname, the farm $json_obj->{newfarmname} already exists, try another name."
							);
						}
						else
						{
							#Change farm name
							my $fnchange = &setNewFarmName( $farmname, $json_obj->{ newfarmname } );
							if ( $fnchange == -1 )
							{
								$error = "true";
								&zenlog(
									"ZAPI error, trying to modify a l4xnat farm $farmname, the name of the farm can't be modified, delete the farm and create a new one."
								);
							}
							else
							{
								$restart_flag = "true";
								$farmname_old = $farmname;
								$farmname     = $json_obj->{ newfarmname };
							}
						}
					}
				}
				else
				{
					$error = "true";
					&zenlog(
						 "ZAPI error, trying to modify a l4xnat farm $farmname, invalid newfarmname." );
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
				"ZAPI error, trying to modify a l4xnat farm $farmname, invalid algorithm, can't be blank."
			);
		}
		if ( $json_obj->{ algorithm } =~ /^leastconn|weight|prio$/ )
		{
			$status = &setFarmAlgorithm( $json_obj->{ algorithm }, $farmname );
			if ( $status == -1 )
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify a l4xnat farm $farmname, some errors happened trying to modify the algorithm."
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
				   "ZAPI error, trying to modify a l4xnat farm $farmname, invalid algorithm." );
		}
	}

	# Modify Persistence Mode
	if ( exists ( $json_obj->{ persistence } ) )
	{
		if ( $json_obj->{ persistence } =~ /^(?:ip|)$/ )
		{
			my $persistence = $json_obj->{ persistence };
			$persistence = '' if $json_obj->{ persistence } eq 'none';

			if (&getFarmPersistence($farmname) ne $persistence)
			{
				my $statusp = &setFarmSessionType( $persistence, $farmname, "" );
				if ( $statusp != 0 )
				{
					$error = "true";
					&zenlog(
						"ZAPI error, trying to modify a l4xnat farm $farmname, some errors happened trying to modify the persistence."
					);
				}
				else
				{
					$restart_flag = "true";
				}
			}
		}
		else
		{
			$error = "true";
			&zenlog(
				 "ZAPI error, trying to modify a l4xnat farm $farmname, invalid persistence." );
		}
	}

	# Modify Protocol Type
	if ( exists ( $json_obj->{ protocol } ) )
	{
		if ( $json_obj->{ protocol } =~ /^$/ )
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify a l4xnat farm $farmname, invalid protocol, can't be blank."
			);
		}
		if ( $json_obj->{ protocol } =~ /^all|tcp|udp|sip|ftp|tftp$/ )
		{
			$status = &setFarmProto( $json_obj->{ protocol }, $farmname );
			if ( $status != 0 )
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify a l4xnat farm $farmname, some errors happened trying to modify the protocol."
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
					"ZAPI error, trying to modify a l4xnat farm $farmname, invalid protocol." );
		}
	}

	# Modify NAT Type
	if ( exists ( $json_obj->{ nattype } ) )
	{
		if ( $json_obj->{ nattype } =~ /^$/ )
		{
			&error = "true";
			&zenlog(
				"ZAPI error, trying to modify a l4xnat farm $farmname, invalid nattype, can't be blank."
			);
		}
		if ( $json_obj->{ nattype } =~ /^nat|dnat$/ )
		{
			if (&getFarmNatType($farmname) ne $json_obj->{nattype})
			{
				$status = &setFarmNatType( $json_obj->{ nattype }, $farmname );
				if ( $status != 0 )
				{
					$error = "true";
					&zenlog(
						"ZAPI error, trying to modify a l4xnat farm $farmname, some errors happened trying to modify the nattype."
					);
				}
				else
				{
					$restart_flag = "true";
				}
			}
		}
		else
		{
			$error = "true";
			&zenlog(
					 "ZAPI error, trying to modify a l4xnat farm $farmname, invalid nattype." );
		}
	}

	# Modify IP Adress Persistence Time To Limit
	if ( exists ( $json_obj->{ ttl } ) )
	{
		if ( $json_obj->{ ttl } =~ /^$/ )
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify a l4xnat farm $farmname, invalid ttl, can't be blank."
			);
		}
		elsif ( $json_obj->{ ttl } =~ /^\d+$/ )
		{
			$status = &setFarmMaxClientTime( 0, $json_obj->{ ttl }, $farmname );
			if ( $status != 0 )
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify a l4xnat farm $farmname, some errors happened trying to modify the ttl."
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
					  "ZAPI error, trying to modify a l4xnat farm $farmname, invalid ttl." );
		}
	}

	# Modify only vip
	if ( exists ( $json_obj->{ vip } ) && !exists ( $json_obj->{ vport } ) )
	{
		if ( $json_obj->{ vip } =~ /^$/ )
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify a l4xnat farm $farmname, invalid vip, can't be blank."
			);
		}
		elsif ( !$json_obj->{ vip } =~ /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/ )
		{
			$error = "true";
			&zenlog(
					  "ZAPI error, trying to modify a l4xnat farm $farmname, invalid vip." );
		}
		else
		{
			$status = &setFarmVirtualConf( $json_obj->{ vip }, $vport, $farmname );
			if ( $status == -1 )
			{
				$error = "true";
				&zenlog(
						  "ZAPI error, trying to modify a l4xnat farm $farmname, invalid vip." );
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
				"ZAPI error, trying to modify a l4xnat farm $farmname, invalid vport, can't be blank."
			);
		}
		elsif ( !$json_obj->{ vport } =~ /^\d+((\:\d+)*(\,\d+)*)*$/ )
		{
			if ( $json_obj->{ vport } ne "*" )
			{
				$error = "true";
				&zenlog(
						  "ZAPI error, trying to modify a l4xnat farm $farmname, invalid vport." );
			}
		}
		else
		{
			$status = &setFarmVirtualConf( $vip, $json_obj->{ vport }, $farmname );
			if ( $status == -1 )
			{
				$error = "true";
				&zenlog(
						  "ZAPI error, trying to modify a l4xnat farm $farmname, invalid vport." );
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
				"ZAPI error, trying to modify a l4xnat farm $farmname, invalid vip, can't be blank."
			);
		}
		elsif ( !$json_obj->{ vip } =~ /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/ )
		{
			$error = "true";
			&zenlog(
					  "ZAPI error, trying to modify a l4xnat farm $farmname, invalid vip." );
		}
		else
		{
			if ( exists ( $json_obj->{ vport } ) )
			{
				if ( $json_obj->{ vport } =~ /^$/ )
				{
					$error = "true";
					&zenlog(
						"ZAPI error, trying to modify a l4xnat farm $farmname, invalid vport, can't be blank."
					);
				}
				elsif ( !$json_obj->{ vport } =~ /^\d+((\:\d+)*(\,\d+)*)*$/ )
				{
					if ( $json_obj->{ vport } ne "*" )
					{
						$error = "true";
						&zenlog(
								  "ZAPI error, trying to modify a l4xnat farm $farmname, invalid vport." );
					}
				}
				else
				{
					$status =
					  &setFarmVirtualConf( $json_obj->{ vip }, $json_obj->{ vport }, $farmname );
					if ( $status == -1 )
					{
						$error = "true";
						&zenlog(
							"ZAPI error, trying to modify a l4xnat farm $farmname, invalid vport or invalid vip."
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

		if ( &getFarmStatus( $farmname ) eq 'up' )
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

			&runZClusterRemoteManager( 'farm', 'restart', $farmname );
		}

		# Success
		my $body = {
					 description => "Modify farm $farmname",
					 params      => $json_obj
		};

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		&zenlog(
			"ZAPI error, trying to modify a l4xnat farm $farmname, it's not possible to modify the farm."
		);

		# Error
		my $errormsg = "Errors found trying to modify farm $farmname";
		my $body = {
					 description => "Modify farm $farmname",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

1;
