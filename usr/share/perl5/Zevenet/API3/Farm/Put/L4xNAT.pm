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

# PUT /farms/<farmname> Modify a l4xnat Farm

sub modify_l4xnat_farm    # ( $json_obj, $farmname )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $farmname = shift;

	# Flags
	my $reload_flag  = "false";
	my $restart_flag = "false";
	my $error        = "false";
	my $status;
	my $initialStatus = &getL4FarmParam( 'status', $farmname );

	include 'Zevenet::IPDS::Base';

	# flag to reset IPDS rules when the farm changes the name.
	my $farmname_old;
	my $ipds = &getIPDSfarmsRules_zapiv3( $farmname );

	# Check that the farm exists
	if ( !&getFarmExists( $farmname ) )
	{
		# Error
		my $errormsg = "The farmname $farmname does not exist.";
		my $body = {
					 description => "Modify farm",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 404, body => $body } );
	}

	&runIPDSStopByFarm( $farmname );

	# Get current vip & vport
	my $vip   = &getFarmVip( "vip",  $farmname );
	my $vport = &getFarmVip( "vipp", $farmname );

	####### Functions

	# Modify Farm's Name
	if ( exists ( $json_obj->{ newfarmname } ) )
	{
		unless ( &getL4FarmParam( 'status', $farmname ) eq 'down' )
		{
			&zenlog(
				"Error trying to modify a l4xnat farm $farmname, cannot change the farm name while running",
				"error", "LSLB"
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
				"Error trying to modify a l4xnat farm $farmname, invalid new farm name, can't be blank.",
				"error", "LSLB"
			);
		}
		else
		{
			if ( $json_obj->{ newfarmname } ne $farmname )
			{
				#Check if farmname has correct characters (letters, numbers and hyphens)
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
								"Error trying to modify a l4xnat farm $farmname, the farm $json_obj->{newfarmname} already exists, try another name.",
								"error", "LSLB"
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
							 "Error trying to modify a l4xnat farm $farmname, invalid new farm name.",
							 "error", "LSLB" );
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
				"Error trying to modify a l4xnat farm $farmname, invalid algorithm, can't be blank.",
				"error", "LSLB"
			);
		}
		if ( $json_obj->{ algorithm } =~ /^(prio)$/ )
		{
			my $desc = "Modify L4xNAT farm";
			my $msg  = "Not supported anymore.";
			&httpResponse(
						   {
							 code => 410,
							 body => { description => $desc, message => $msg, error => "true" }
						   }
			);
		}
		if ( $json_obj->{ algorithm } =~ /^leastconn|weight$/ )
		{
			$status = &setFarmAlgorithm( $json_obj->{ algorithm }, $farmname );
			if ( $status eq '-1' )
			{
				$error = "true";
				&zenlog(
					"Error trying to modify a l4xnat farm $farmname, some errors detected trying to modify the algorithm.",
					"error", "LSLB"
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
			&zenlog( "Error trying to modify a l4xnat farm $farmname, invalid algorithm.",
					 "error", "LSLB" );
		}
	}

	# Modify Persistence Mode
	if ( exists ( $json_obj->{ persistence } ) )
	{
		if ( $json_obj->{ persistence } =~ /^(?:ip|)$/ )
		{
			my $persistence = $json_obj->{ persistence };

			if ( &getL4FarmParam( 'persist', $farmname ) ne $persistence )
			{
				my $statusp = &setFarmSessionType( $persistence, $farmname, "" );
				if ( $statusp != 0 )
				{
					$error = "true";
					&zenlog(
						"Error trying to modify a l4xnat farm $farmname, some errors detected trying to modify the persistence.",
						"error", "LSLB"
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
			&zenlog( "Error trying to modify a l4xnat farm $farmname, invalid persistence.",
					 "error", "LSLB" );
		}
	}

	# Modify Protocol Type
	if ( exists ( $json_obj->{ protocol } ) )
	{
		if ( $json_obj->{ protocol } =~ /^$/ )
		{
			$error = "true";
			&zenlog(
				"Error trying to modify a l4xnat farm $farmname, invalid protocol, can't be blank.",
				"error", "LSLB"
			);
		}
		if ( $json_obj->{ protocol } =~ /^all|tcp|udp|sip|ftp|tftp$/ )
		{
			$status = &setL4FarmParam( 'proto', $json_obj->{ protocol }, $farmname );
			if ( $status != 0 )
			{
				$error = "true";
				&zenlog(
					"Error trying to modify a l4xnat farm $farmname, some errors detected trying to modify the protocol.",
					"error", "LSLB"
				);
			}
			else
			{
				if ( $json_obj->{ protocol } eq 'all' )
				{
					$json_obj->{ vport } = &getFarmVip( "vipp", $farmname );
				}
				$restart_flag = "true";
			}
		}
		else
		{
			$error = "true";
			&zenlog( "Error trying to modify a l4xnat farm $farmname, invalid protocol.",
					 "error", "LSLB" );
		}
	}

	# Modify NAT Type
	if ( exists ( $json_obj->{ nattype } ) )
	{
		if ( $json_obj->{ nattype } =~ /^$/ )
		{
			&error = "true";
			&zenlog(
				"Error trying to modify a l4xnat farm $farmname, invalid nat type, can't be blank.",
				"error", "LSLB"
			);
		}
		if ( $json_obj->{ nattype } =~ /^nat|dnat$/ )
		{
			if ( &getL4FarmParam( 'mode', $farmname ) ne $json_obj->{ nattype } )
			{
				$status = &setL4FarmParam( 'mode', $json_obj->{ nattype }, $farmname );
				if ( $status != 0 )
				{
					$error = "true";
					&zenlog(
						"Error trying to modify a l4xnat farm $farmname, some errors detected trying to modify the nat type.",
						"error", "LSLB"
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
			&zenlog( "Error trying to modify a l4xnat farm $farmname, invalid nat type.",
					 "error", "LSLB" );
		}
	}

	# Modify IP Adress Persistence Time To Limit
	if ( exists ( $json_obj->{ ttl } ) )
	{
		if ( $json_obj->{ ttl } =~ /^$/ )
		{
			$error = "true";
			&zenlog(
				 "Error trying to modify a l4xnat farm $farmname, invalid ttl, can't be blank.",
				 "error", "LSLB"
			);
		}
		elsif ( $json_obj->{ ttl } =~ /^\d+$/ )
		{
			$status = &setFarmMaxClientTime( 0, $json_obj->{ ttl }, $farmname );
			if ( $status != 0 )
			{
				$error = "true";
				&zenlog(
					"Error trying to modify a l4xnat farm $farmname, some errors detected trying to modify the ttl.",
					"error", "LSLB"
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
			&zenlog( "Error trying to modify a l4xnat farm $farmname, invalid ttl.",
					 "error", "LSLB" );
		}
	}

	# Modify only vip
	if ( exists ( $json_obj->{ vip } ) && !exists ( $json_obj->{ vport } ) )
	{
		if ( $json_obj->{ vip } =~ /^$/ )
		{
			$error = "true";
			&zenlog(
				"Error trying to modify a l4xnat farm $farmname, invalid Virtual IP, it can't be blank.",
				"error", "LSLB"
			);
		}
		elsif ( !$json_obj->{ vip } =~ /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/ )
		{
			$error = "true";
			&zenlog( "Error trying to modify a l4xnat farm $farmname, invalid Virtual IP.",
					 "error", "LSLB" );
		}
		else
		{
			$status = &setFarmVirtualConf( $json_obj->{ vip }, $vport, $farmname );
			if ( $status == -1 )
			{
				$error = "true";
				&zenlog( "Error trying to modify a l4xnat farm $farmname, invalid Virtual IP.",
						 "error", "LSLB" );
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
				"Error trying to modify a l4xnat farm $farmname, invalid Virtual port, it can't be blank.",
				"error", "LSLB"
			);
		}
		elsif ( !$json_obj->{ vport } =~ /^\d+((\:\d+)*(\,\d+)*)*$/ )
		{
			if ( $json_obj->{ vport } ne "*" )
			{
				$error = "true";
				&zenlog(
						 "Error trying to modify a l4xnat farm $farmname, invalid Virtual port.",
						 "error", "LSLB" );
			}
		}
		else
		{
			$status = &setFarmVirtualConf( $vip, $json_obj->{ vport }, $farmname );
			if ( $status == -1 )
			{
				$error = "true";
				&zenlog(
						 "Error trying to modify a l4xnat farm $farmname, invalid Virtual port.",
						 "error", "LSLB" );
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
				"Error trying to modify a l4xnat farm $farmname, invalid Virtual IP, it can't be blank.",
				"error", "LSLB"
			);
		}
		elsif ( !$json_obj->{ vip } =~ /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/ )
		{
			$error = "true";
			&zenlog( "Error trying to modify a l4xnat farm $farmname, invalid Virtual IP.",
					 "error", "LSLB" );
		}
		else
		{
			if ( exists ( $json_obj->{ vport } ) )
			{
				if ( $json_obj->{ vport } =~ /^$/ )
				{
					$error = "true";
					&zenlog(
						"Error trying to modify a l4xnat farm $farmname, invalid Virtual port, it can't be blank.",
						"error", "LSLB"
					);
				}
				elsif ( !$json_obj->{ vport } =~ /^\d+((\:\d+)*(\,\d+)*)*$/ )
				{
					if ( $json_obj->{ vport } ne "*" )
					{
						$error = "true";
						&zenlog(
								 "Error trying to modify a l4xnat farm $farmname, invalid Virtual port.",
								 "error", "LSLB" );
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
							"Error trying to modify a l4xnat farm $farmname, invalid Virtual port or invalid Virtual IP.",
							"error", "LSLB"
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
				 "info", "LSLB" );

		if ( &getL4FarmParam( 'status', $farmname ) eq 'up' )
		{
			# Reset ip rule mark when changing the farm's vip
			if ( exists $json_obj->{ vip } && $json_obj->{ vip } ne $vip )
			{
				my $farm   = &getL4FarmStruct( $farmname );
				my $ip_bin = &getGlobalConfiguration( 'ip_bin' );

				# previous vip
				my $prev_vip_if_name = &getInterfaceOfIp( $vip );
				my $prev_vip_if      = &getInterfaceConfig( $prev_vip_if_name );
				my $prev_table_if =
				  ( $prev_vip_if->{ type } eq 'virtual' )
				  ? $prev_vip_if->{ parent }
				  : $prev_vip_if->{ name };

				# new vip
				my $vip_if_name = &getInterfaceOfIp( $json_obj->{ vip } );
				my $vip_if      = &getInterfaceConfig( $vip_if_name );
				my $table_if =
				  ( $vip_if->{ type } eq 'virtual' ) ? $vip_if->{ parent } : $vip_if->{ name };

				foreach my $server ( @{ $$farm{ servers } } )
				{
					my $ip_del_cmd =
					  "$ip_bin rule add fwmark $server->{ tag } table table_$table_if";
					my $ip_add_cmd =
					  "$ip_bin rule del fwmark $server->{ tag } table table_$prev_table_if";
					&logAndRun( $ip_add_cmd );
					&logAndRun( $ip_del_cmd );
				}
			}

			&runIPDSStartByFarm( $farmname );
			include 'Zevenet::Cluster';
			&runZClusterRemoteManager( 'farm', 'restart', $farmname );
		}

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
			"Error trying to modify a l4xnat farm $farmname, it's not possible to modify the farm.",
			"error", "LSLB"
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
