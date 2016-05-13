###############################################################################
#
#     Zen Load Balancer Software License
#     This file is part of the Zen Load Balancer software package.
#
#     Copyright (C) 2014 SOFINTEL IT ENGINEERING SL, Sevilla (Spain)
#
#     This library is free software; you can redistribute it and/or modify it
#     under the terms of the GNU Lesser General Public License as published
#     by the Free Software Foundation; either version 2.1 of the License, or
#     (at your option) any later version.
#
#     This library is distributed in the hope that it will be useful, but
#     WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
#     General Public License for more details.
#
#     You should have received a copy of the GNU Lesser General Public License
#     along with this library; if not, write to the Free Software Foundation,
#     Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
###############################################################################

### CONTROLLER L4xNAT FARM ###

# maintenance mode for servers
if ( $action eq "editfarm-maintenance" )
{
	&setFarmBackendMaintenance( $farmname, $id_server );
	if ( $? eq 0 )
	{
		&successmsg( "Enabled maintenance mode for backend $id_server" );
	}
}

#disable maintenance mode for servers
if ( $action eq "editfarm-nomaintenance" )
{
	&setFarmBackendNoMaintenance( $farmname, $id_server );
	if ( $? eq 0 )
	{
		&successmsg( "Disabled maintenance mode for backend" );
	}
}

#Edit Global Parameters
if ( $action eq "editfarm-Parameters" )
{
	#Actual Parameters
	#read configuration values
	my $actualvip   = &getFarmVip( "vip",  $farmname );
	my $actualvport = &getFarmVip( "vipp", $farmname );

	my $actualsession = &getFarmSessionType( $farmname );
	if ( $actualsession == -1 )
	{
		$actualsession = "none";
	}

	my $actuallbalg = &getFarmAlgorithm( $farmname );
	if ( $actuallbalg == -1 )
	{
		$actuallbalg = "weight";
	}

	my $actualnattype = &getFarmNatType( $farmname );
	if ( $actualnattype == -1 )
	{
		$actualnattype = "nat";
	}

	my $actualfarmprotocol = &getFarmProto( $farmname );
	if ( $actualfarmprotocol == -1 )
	{
		$actualfarmprotocol = "all";
	}

	my @actualttl       = &getFarmMaxClientTime( $farmname );
	my $actualttl       = $actualttl[0];
	my @fgconfig        = &getFarmGuardianConf( $farmname, "" );
	my $actualfgttcheck = $fgconfig[1];
	my $actualfgscript  = $fgconfig[2];
	$actualfgscript =~ s/\n//g;
	$actualfgscript =~ s/\"/\'/g;
	my $actualfguse = $fgconfig[3];
	$actualfguse =~ s/\n//g;
	my $actualfglog = $fgconfig[4];

	#change Farm's name
	if ( $farmname ne $newfarmname )
	{
		#Check if farmname has correct characters (letters, numbers and hyphens)
		if ( &checkFarmnameOK( $newfarmname ) )
		{
			&errormsg( "Farm name isn't OK, only allowed numbers letters and hyphens" );
		}
		else
		{
			#Check if the new farm's name alredy exists
			if ( &getFarmFile( $newfarmname ) != -1 )
			{
				&errormsg( "The farm $newfarmname already exists, try another name" );
			}
			else
			{
				#Change farm name
				$fnchange = &setNewFarmName( $farmname, $newfarmname );

				if ( $fnchange == -1 )
				{
					&errormsg(
						"The name of the Farm $farmname can't be modified, delete the farm and create a new one."
					);
				}
				elsif ( $fnchange == -2 )
				{
					&errormsg(
						 "The name of the Farm $farmname can't be modified, the new name can't be empty"
					);
				}
				else
				{
					&successmsg( "The Farm $farmname has been renamed to $newfarmname." );
					$farmname = $newfarmname;
				}
			}
		}
	}

	#change vip and vport
	if ( $actualvip ne $vip or $actualvport ne $vipp )
	{
		my $fproto = &getFarmProto( $farmname );
		if ( $fproto ne "all" && &ismport( $vipp ) eq "false" )
		{
			&errormsg(
					   "Invalid Virtual Port $vipp value, it must be a valid multiport value" );
			$error = 1;
		}

		if ( &validL4ExtPort( $fproto ) != 0 )
		{
			&errormsg(
				"Virtual Port $vipp is not valid for the $fproto protocol, use a simple port or ',' separated for several ports"
			);
		}
		if ( $error == 0 )
		{
			$status = &setFarmVirtualConf( $vip, $vipp, $farmname );
			if ( $status != -1 )
			{
				&successmsg(
						   "Virtual IP and Virtual Port has been modified for the farm $farmname" );
			}
			else
			{
				&errormsg(
						   "It's not possible to change the $farmname farm virtual IP and port" );
			}
		}
	}

	#persistence mode
	if ( $actualsession ne $session )
	{
		$status = &setFarmSessionType( $session, $farmname );
		if ( $status == 0 )
		{

			&successmsg( "The session type for $farmname farm has been modified" );
		}
		else
		{
			&errormsg( "It's not possible to change the $farmname farm session type" );
		}
	}

	#change the load balance algorithm;
	if ( $actuallbalg ne $lb )
	{
		$error = 0;
		if ( $lb =~ /^$/ )
		{
			&errormsg( "Invalid algorithm value" );
			$error = 1;
		}
		if ( $error == 0 )
		{
			$status = &setFarmAlgorithm( $lb, $farmname );
			if ( $status != -1 )
			{
				&successmsg( "The algorithm for $farmname Farm is modified" );
			}
			else
			{
				&errormsg( "It's not possible to change the farm $farmname algorithm" );
			}
		}
	}

	#nat type
	if ( $actualnattype ne $nattype )
	{
		$status = &setFarmNatType( $nattype, $farmname );
		if ( $status == 0 )
		{
			&successmsg( "The NAT type for $farmname farm has been modified" );
		}
		else
		{
			&errormsg( "It's not possible to change the $farmname farm NAT type" );
		}
	}

	#proto type
	if ( $actualfarmprotocol ne $farmprotocol )
	{
		$status = &setFarmProto( $farmprotocol, $farmname );
		if ( $status == 0 )
		{
			&successmsg( "The protocol type for $farmname farm has been modified" );
		}
		else
		{
			&errormsg( "It's not possible to change the $farmname farm protocol type" );
		}
	}

	#TTL
	if ( $actualttl ne $sessttl && $sessttl ne "" )
	{

		$error = 0;

		if ( &isnumber( $sessttl ) eq "false" )
		{
			&errormsg(
					   "Invalid client timeout $sessttl value, it must be a numeric value" );
			$error = 1;
		}

		if ( $error == 0 )
		{
			$status = &setFarmMaxClientTime( 0, $sessttl, $farmname );

			if ( $status == 0 )
			{
				&successmsg( "The sessions TTL for $farmname farm has been modified" );
			}

			else
			{
				&errormsg( "It's not possible to change the $farmname farm sessions TTL" );
			}
		}
	}

	#change farmguardian values
	if (    ( !defined ( $usefarmguardian ) and $actualfguse eq "true" )
		 or ( defined ( $usefarmguardian )  and $actualfguse eq "false" )
		 or ( defined ( $usefarmguardian )  and $actualfguse eq "" )
		 or ( !defined ( $farmguardianlog ) and $actualfglog eq "true" )
		 or ( defined ( $farmguardianlog )  and $actualfglog eq "false" )
		 or ( defined ( $farmguardianlog )  and $actualfglog eq "" )
		 or ( $actualfgttcheck ne $timetocheck )
		 or ( $actualfgscript ne $check_script ) )
	{
		$fguardianconf = &getFarmGuardianFile( $farmname, "" );

		$usefarmguardian =
		  defined ( $usefarmguardian )
		  ? "true"
		  : "false";

		$farmguardianlog =
		  defined ( $farmguardianlog )
		  ? "true"
		  : "false";

		if ( &isnumber( $timetocheck ) eq "false" )
		{
			&errormsg( "Invalid check interval value $timetocheck, it must be numeric" );
		}
		elsif ( ( !defined ( $check_script ) or $check_script eq '' )
				&& $usefarmguardian eq 'true' )
		{
			&warnmsg( "To enable FarmGardian a command to check must be defined" );
		}
		else
		{
			$status = -1;
			$usefarmguardian =~ s/\n//g;
			&runFarmGuardianStop( $farmname, "" )
			  if ( &getFarmStatus( $farmname ) eq 'up' );
			&logfile(
					  "creating $farmname farmguardian configuration file in $fguardianconf" )
			  if !-f "$configdir/$fguardianconf";
			$check_script =~ s/\"/\'/g;
			$status =
			  &runFarmGuardianCreate( $farmname, $timetocheck, $check_script,
									  $usefarmguardian, $farmguardianlog, "" );
			if ( $status != -1 )
			{
				&successmsg(
							 "The FarmGuardian service for the $farmname farm has been modified" );
							 
				if ( $usefarmguardian eq "true" && &getFarmStatus( $farmname ) eq 'up' )
				{
					$status = &runFarmGuardianStart( $farmname, "" );
					if ( $status != -1 )
					{
						&successmsg(
									 "The FarmGuardian service for the $farmname farm has been started" );
					}
					else
					{
						&errormsg(
							"An error ocurred while starting the FarmGuardian service for the $farmname farm"
						);
					}
				}
			}
			else
			{
				&errormsg(
					"It's not possible to create the FarmGuardian configuration file for the $farmname farm"
				);
			}
		}
	}
}

#restart farm
if ( $action eq "editfarm-restart" )
{
	&runFarmStop( $farmname, "true" );
	&sendL4ConfChange( $farmname );
	$status = &runFarmStart( $farmname, "true" );

	#$status = &runL4FarmRestart($farmname, "true", "cold");
	if ( $status == 0 )
	{
		&successmsg( "The $farmname farm has been restarted" );
	}
	else
	{
		&errormsg( "The $farmname farm hasn't been restarted" );
	}
}

#delete server
if ( $action eq "editfarm-deleteserver" )
{
	$status = &runFarmServerDelete( $id_server, $farmname );
	if ( $status != -1 )
	{
		#&runL4FarmRestart($farmname, "false", "hot");
		&successmsg(
			  "The real server with ID $id_server of the $farmname farm has been deleted" );
	}
	else
	{
		&errormsg(
			"It's not possible to delete the real server with ID $id_server of the $farmname farm"
		);
	}
}

#save server
if ( $action eq "editfarm-saveserver" )
{
	# Get IP Version of current farm
	my $current_vip = &getFarmVip( "vip", $farmname );
	my $ipv = &ipversion( $current_vip );

	# Check if rip_server has a correct IP value (IPv4 or IPv6)
	$error = 0;
	if ( &ipisok( $rip_server ) eq "false" || $rip_server =~ /^$/ )
	{
		&errormsg(
			 "Invalid real server IP value, please insert a valid value with $ipv structure"
		);
		$error = 1;
	}

	# Check if rip_server structure is IPv4 or IPv6
	if ( $ipv ne &ipversion( $rip_server ) && $error == 0 )
	{
		&errormsg(
				  "IP Address $rip_server structure is not ok, must be an $ipv structure" );
		$error = 1;
	}

	if ( &checkmport( $port_server ) eq "true" )
	{
		my $port = &getFarmVip( "vipp", $farmname );
		if ( $port_server == $port || $port_server =~ /\*/ )
		{
			$port_server = "";
		}
		else
		{
			&errormsg(
				"Invalid multiple ports for backend, please insert a single port number or blank"
			);
			$error = 1;
		}
	}

	# weight can be from
	if ( $weight_server =~ /^$/ )
	{
		$weight_server = 1;    # default
	}
	elsif ( $weight_server eq "0" )
	{
		&errormsg(
				 "Invalid real server weight value, please insert a value greater than 0" );
		$error = 1;
	}
	elsif ( $weight_server < 1 )
	{
		&errormsg(
				 "Invalid real server weight value, please insert a value greater than 0" );
		$error = 1;
	}

	# priority can be from 0 to 9
	if ( $priority_server =~ /^$/ )
	{
		$priority_server = 1;    # default
	}
	elsif ( $priority_server < 0 )
	{
		&errormsg(
			"Invalid real server priority value, please insert a value greater than or equal to 0"
		);
		$error = 1;
	}
	elsif ( $priority_server > 9 )
	{
		&errormsg(
			"Invalid real server priority value, please insert a value less than or equal to 9"
		);
		$error = 1;
	}

	if ( $error == 0 )
	{
		$status = &setFarmServer(
								  $id_server,      $rip_server,    $port_server,
								  $max_server,     $weight_server, $priority_server,
								  $timeout_server, $farmname
		);
		if ( $status != -1 )
		{

			&successmsg(
				"The real server with ID $id_server and IP $rip_server of the $farmname farm has been modified"
			);
		}
		else
		{
			&errormsg(
				"It's not possible to modify the real server with ID $id_server and IP $rip_server of the $farmname farm"
			);
		}
	}
}

#check if the farm need a restart
#if (-e "/tmp/$farmname.lock"){
#	&tipmsg("There're changes that need to be applied, stop and start farm to apply them!");
#}

1;
