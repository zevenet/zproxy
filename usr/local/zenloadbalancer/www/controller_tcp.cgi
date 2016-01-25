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

### CONTROLLER TCP/UDP FARM ###

#lateral menu
#global info for a farm
$maxtimeout   = "10000";
$maxmaxclient = "3000000";
$maxsimconn   = "32760";
$maxbackend   = "10000";

&logfile( "loading the $farmname Farm data" );
if ( $farmname =~ /^$/ )
{
	&errormsg( "Unknown farm name" );
	$action = "";
}
$ftype = &getFarmType( $farmname );
if ( $ftype ne "tcp" && $ftype ne "udp" )
{
	&errormsg( "Invalid farm type" );
	$action = "";
}

$fstate = &getFarmStatus( $farmname );
if ( $fstate eq "down" )
{
	&errormsg( "The farm $farmname is down, to edit please start it up" );
	$action = "";
}

#maintenance mode for servers
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

#Edit Global parameters
if ( $action eq "editfarm-Parameters" )
{

	#Actual Parameters
	my $actualvip   = &getFarmVip( "vip",  $farmname );
	my $actualvport = &getFarmVip( "vipp", $farmname );
	my $actuallb    = &getFarmAlgorithm( $farmname );
	if ( $actuallb == -1 )
	{
		$actuallb = "roundrobin";
	}
	my $actualpersistence = &getFarmPersistence( $farmname );
	if ( $actualpersistence == -1 )
	{
		$actualpersistence = "true";
	}
	my @client           = &getFarmMaxClientTime( $farmname );
	my $actualmaxclients = @client[0];
	chomp ( $actualmaxclients );
	my $actualtracking = @client[1];
	chomp ( $actualtracking );
	my $actualftimeout = &getFarmTimeout( $farmname );
	chomp ( $actualftimeout );
	my $actualconn_max = &getFarmMaxConn( $farmname );
	chomp ( $actualconn_max );
	my $actualnumberofservers = &getFarmMaxServers( $farmname );
	chomp ( $actualnumberofservers );
	my $actualxforw     = &getFarmXForwFor( $farmname );
	my $actualblacklist = &getFarmBlacklistTime( $farmname );
	chomp ( $actualblacklist );
	my @fgconfig        = &getFarmGuardianConf( $farmname, "" );
	my $actualfgttcheck = @fgconfig[1];
	my $actualfgscript  = @fgconfig[2];
	$actualfgscript =~ s/\n//g;
	$actualfgscript =~ s/\"/\'/g;
	my $actualfguse = @fgconfig[3];
	$actualfguse =~ s/\n//g;
	my $actualfglog = @fgconfig[4];

	#change vip and vipp
	if ( $actualvip ne $vip or $actualvport ne $vipp )
	{
		$error = 0;
		if ( &isnumber( $vipp ) eq "false" )
		{
			&errormsg( "Invalid Virtual Port $vipp value, it must be a numeric value" );
			$error = 1;
		}
		if ( &checkport( $vip, $vipp ) eq "true" )
		{
			&errormsg(
					   "Virtual Port $vipp in Virtual IP $vip is in use, select another port" );
			$error = 1;
		}
		if ( $error == 0 )
		{
			$status = &setFarmVirtualConf( $vip, $vipp, $farmname );
			if ( $status != -1 )
			{
				&runFarmStop( $farmname, "true" );
				&runFarmStart( $farmname, "true" );
				&successmsg(
					"Virtual IP and Virtual Port has been modified, the $farmname farm has been restarted"
				);
			}
			else
			{
				&errormsg(
						   "It's not possible to change the $farmname farm virtual IP and port" );
			}
		}
	}

	#change Farm's name
	if ( $farmname ne $newfarmname )
	{
		#Check if farmname has correct characters (letters, numbers and hyphens)
		my $farmnameok = &checkFarmnameOK( $newfarmname );

		#Check the farm's name change
		if ( "$newfarmname" eq "$farmname" )
		{
			&errormsg(
				"The new farm's name \"$newfarmname\" is the same as the old farm's name \"$farmname\": nothing to do"
			);
		}
		elsif ( $farmnameok ne 0 )
		{
			&errormsg( "Farm name isn't OK, only allowed numbers letters and hyphens" );

		}
		else
		{
			#Check if the new farm's name alredy exists
			$newffile = &getFarmFile( $newfarmname );
			if ( $newffile != -1 )
			{
				&errormsg( "The farm $newfarmname already exists, try another name" );
			}
			else
			{
				#Stop farm
				$oldfstat = &runFarmStop( $farmname, "true" );
				if ( $oldfstat == 0 )
				{
					&successmsg( "The Farm $farmname is now disabled" );
				}
				else
				{
					&errormsg( "The Farm $farmname is not disabled, are you sure it's running?" );
				}

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
					my $newfstat = &runFarmStart( $farmname, "true" );
					if ( $newfstat == 0 )
					{
						&successmsg( "The Farm $farmname is now running" );
					}
					else
					{
						&errormsg(
							"The Farm $farmname isn't running, check if the IP address is up and the PORT is in use"
						);
					}
				}
				else
				{
					&successmsg( "The Farm $farmname has been just renamed to $newfarmname" );
					$farmname = $newfarmname;

					#Start farm
					my $newfstat = &runFarmStart( $farmname, "true" );
					if ( $newfstat == 0 )
					{
						&successmsg( "The Farm $farmname is now running" );
					}
					else
					{
						&errormsg(
							"The Farm $farmname isn't running, check if the IP address is up and the PORT is in use"
						);
					}
				}
			}
		}
	}

	#change Timeout
	if ( $actualftimeout ne $timeout )
	{
		$error = 0;
		if ( &isnumber( $timeout ) eq "false" )
		{
			&errormsg( "Invalid timeout $timeout value, it must be a numeric value" );
			$error = 1;
		}
		if ( $timeout > $maxtimeout )
		{
			&errormsg(
					   "Invalid timeout $timeout value, the max timeout value is $maxtimeout" );
			$error = 1;
		}
		if ( $error == 0 )
		{
			$status = &setFarmTimeout( $timeout, $farmname );
			if ( $status != -1 )
			{
				&successmsg( "The timeout for $farmname farm has been modified" );
			}
			else
			{
				&errormsg( "It's not possible to change the $farmname farm timeout value" );
			}
		}
	}

	#change blacklist time
	if ( $actualblacklist ne $blacklist )
	{
		$error = 0;
		if ( &isnumber( $blacklist ) eq "false" )
		{
			&errormsg( "Invalid blacklist $blacklist value, it must be a numeric value" );
			$error = 1;
		}
		if ( $error == 0 )
		{
			$status = &setFarmBlacklistTime( $blacklist, $farmname );
			if ( $status != -1 )
			{
				&successmsg( "The blacklist time for $farmname farm is modified" );
			}
			else
			{
				&errormsg(
						   "It's not possible to change the farm $farmname blacklist time value" );
			}
		}
	}

	#change the load balance algorithm;
	if ( $actuallb ne $lb )
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

	# control client persistence
	if ( $actualpersistence eq "true" and !defined ( $persistence )
		 or defined ( $persistence ) and $actualpersistence eq "false" )
	{
		if ( defined ( $persistence ) )
		{
			$persistence = "true";
		}
		else
		{
			$persistence = "false";
		}

		if ( $persistence eq "true" )
		{
			$status = &setFarmPersistence( $persistence, $farmname );
			if ( $status != -1 )
			{
				&successmsg( "The client persistence is enabled" );
			}
			else
			{
				&errormsg(
					  "It's not possible to enable the client persistence for the farm $farmname" );
			}
		}
		else
		{
			$status = &setFarmPersistence( $persistence, $farmname );
			if ( $status != -1 )
			{
				&successmsg( "The client persistence is disabled" );
			}
			else
			{
				&errormsg(
					 "It's not possible to disable the client persistence for the farm $farmname" );
			}
		}
	}

	#change max_clients
	if ( $actualmaxclients ne $max_clients or $actualtracking ne $tracking )
	{
		$error = 0;
		if ( &isnumber( $max_clients ) eq "false" )
		{
			&errormsg( "Invalid max clients value $max_clients, it must be numeric" );
			$error = 1;
		}
		if ( $max_clients > $maxmaxclient )
		{
			&errormsg(
					 "Invalid max clients value $max_clients, the max value is $maxmaxclient" );
			$error = 1;
		}
		if ( $error == 0 )
		{
			$status = &setFarmMaxClientTime( $max_clients, $tracking, $farmname );
			if ( $status != -1 )
			{
				&runFarmStop( $farmname, "true" );
				&runFarmStart( $farmname, "true" );
				&successmsg(
					"The max number of clients has been modified, the farm $farmname has been restarted"
				);
			}
			else
			{
				&errormsg( "It's not possible to change the farm $farmname max clients" );
			}
		}
	}

	#change conn_max
	if ( $actualconn_max ne $conn_max )
	{
		$error = 0;
		if ( &isnumber( $conn_max ) eq "false" )
		{
			&errormsg( "Invalid max connections value $conn_max, it must be numeric" );
			$error = 1;
		}
		if ( $conn_max > $maxsimconn )
		{
			&errormsg(
					  "Invalid max connections value $conn_max, the max value is $maxsimconn" );
			$error = 1;
		}
		if ( $error == 0 )
		{
			$status = &setFarmMaxConn( $conn_max, $farmname );
			if ( $status != -1 )
			{
				&runFarmStop( $farmname, "true" );
				&runFarmStart( $farmname, "true" );
				&successmsg(
					"The max number of connections has been modified, the farm $farmname has been restarted"
				);
			}
			else
			{
				&errormsg( "It's not possible to change the farm $farmname max connections" );
			}
		}
	}

	#change max_servers
	if ( $actualnumberofservers ne $max_servers )
	{
		$error = 0;
		if ( &isnumber( $max_servers ) eq "false" )
		{
			&errormsg( "Invalid max servers value $max_servers, it must be numeric" );
			$error = 1;
		}
		if ( $max_servers > $maxbackend )
		{
			&errormsg(
					   "Invalid max servers value $max_servers, the max value is $maxsimconn" );
			$error = 1;
		}
		if ( $error == 0 )
		{
			$status = &setFarmMaxServers( $max_servers, $farmname );
			if ( $status != -1 )
			{
				&runFarmStop( $farmname, "true" );
				&runFarmStart( $farmname, "true" );
				&successmsg(
					"The max number of servers has been modified, the farm $farmname has been restarted"
				);
			}
			else
			{
				&errormsg( "It's not possible to change the farm $farmname max servers" );
			}
		}
	}

	#change xforwardedfor
	if ( $actualxforw eq "true" and !defined ( $xforwardedfor )
		 or defined ( $xforwardedfor ) and $actualxforw eq "false" )
	{
		if ( defined ( $xforwardedfor ) )
		{
			$xforwardedfor = "true";
		}
		else
		{
			$xforwardedfor = "false";
		}

		if ( $ftype eq "tcp" )
		{
			if ( $xforwardedfor eq "true" )
			{
				$status = &setFarmXForwFor( $xforwardedfor, $farmname );
				if ( $status != -1 )
				{
					&successmsg( "The X-Forwarded-For header is enabled" );
				}
				else
				{
					&errormsg(
						 "It's not possible to enable the X-Forwarded-For header for the farm $farmname"
					);
				}
			}
			else
			{
				$status = &setFarmXForwFor( $xforwardedfor, $farmname );
				if ( $status != -1 )
				{
					&successmsg( "The X-Forwarded-For header is disabled" );
				}
				else
				{
					&errormsg(
						"It's not possible to disable the X-Forwarded-For header for the farm $farmname"
					);
				}
			}
		}
		else
		{
			&errormsg(
				"It's not possible to use the X-Forwarded-For header for the UDP farm $farmname"
			);
		}
	}

	#change farmguardian values
	if (   !defined ( $usefarmguardian ) and $actualfguse eq "true"
		 or defined ( $usefarmguardian )  and $actualfguse eq "false"
		 or !defined ( $farmguardianlog ) and $actualfglog eq "true"
		 or defined ( $farmguardianlog )  and $actualfglog eq "false"
		 or $actualfgttcheck ne $timetocheck
		 or $actualfgscript ne $check_script )
	{
		$fguardianconf = &getFarmGuardianFile( $fname, "" );

		if ( defined ( $usefarmguardian ) )
		{
			$usefarmguardian = "true";
		}
		else
		{
			$usefarmguardian = "false";
		}

		if ( defined ( $farmguardianlog ) )
		{
			$farmguardianlog = "true";
		}
		else
		{
			$farmguardianlog = "false";
		}

		if ( &isnumber( $timetocheck ) eq "false" )
		{
			&errormsg( "Invalid period time value $timetocheck, it must be numeric" );
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
			&runFarmGuardianStop( $farmname, "" );
			&logfile(
					  "creating $farmname farmguardian configuration file in  $fguardianconf" );
			$check_script =~ s/\"/\'/g;
			$status =
			  &runFarmGuardianCreate( $farmname, $timetocheck, $check_script,
									  $usefarmguardian, $farmguardianlog, "" );
			if ( $status != -1 )
			{
				&successmsg(
							 "The FarmGuardian service for the $farmname farm has been modified" );
				if ( $usefarmguardian eq "true" )
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

#evalue the actions in the servers##
#edit server action
if ( $action eq "editfarm-saveserver" )
{
	$error = 0;
	if ( &ipisok( $rip_server ) eq "false" )
	{
		&errormsg( "Invalid real server IP value, please insert a valid value" );
		$error = 1;
	}
	if ( $rip_server =~ /^$/ || $port_server =~ /^$/ )
	{
		&errormsg( "Invalid IP address and port for a real server, it can't be blank" );
		$error = 1;
	}

	if ( $error == 0 )
	{
		$status =
		  &setFarmServer( $id_server, $rip_server, $port_server, $max_server,
						  $weight_server, $priority_server, "", $farmname );
		if ( $status != -1 )
		{
			&successmsg(
				"The real server with ip $rip_server and port $port_server for the $farmname farm has been modified"
			);
		}
		else
		{
			&errormsg(
				"It's not possible to modify the real server with ip $rip_server and port $port_server for the $farmname farm"
			);
		}
	}
}

#delete server action
if ( $action eq "editfarm-deleteserver" )
{
	$status = &runFarmServerDelete( $id_server, $farmname );
	if ( $status != -1 )
	{
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

1
