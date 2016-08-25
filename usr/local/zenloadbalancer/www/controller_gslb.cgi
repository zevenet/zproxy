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

### CONTROLLER GSLB FARM ###

my $farm_config_changed = 0;

#Farm restart
if ( $action eq "editfarm-restart" )
{
	&runFarmStop( $farmname, "true" );
	my $status = &runFarmStart( $farmname, "true" );
	
	if ( $status == 0 )
	{
		$farm_config_changed = 1;
		&successmsg( "The $farmname farm has been restarted" );
	}
	else
	{
		&errormsg( "The $farmname farm hasn't been restarted" );
	}
}

#Change health check port for a service
if ( $action eq "editfarm-dpc" )
{
	if ( $service =~ /^$/ )
	{
		&errormsg( "Invalid service, please select a valid value" );
		$error = 1;
	}
	elsif ( $farmname =~ /^$/ )
	{
		&errormsg( "Invalid farm name, please select a valid value" );
		$error = 1;
	}
	elsif ( $dpc =~ /^$/ )
	{
		&errormsg( "Invalid default port health check, please select a valid value" );
		$error = 1;
	}
	elsif ( $error == 0 )
	{
		my $status = &setFarmVS( $farmname, $service, "dpc", $dpc );
		if ( $status == 0 )
		{
			$farm_config_changed = 1;
			&successmsg(
				"The default port health check for the service $service has been successfully changed"
			);
			&setFarmRestart( $farmname );

			#&runFarmReload($farmname);
		}
		else
		{
			&errormsg(
					   "The default port health check for the service $service has failed" );
		}
	}
}

if ( $action eq "editfarm-ns" )
{
	if ( $service =~ /^$/ )
	{
		&errormsg( "Invalid zone, please select a valid value" );
		$error = 1;
	}
	elsif ( $farmname =~ /^$/ )
	{
		&errormsg( "Invalid farm name, please select a valid value" );
		$error = 1;
	}
	elsif ( $ns =~ /^$/ )
	{
		&errormsg( "Invalid name server, please select a valid value" );
		$error = 1;
	}
	elsif ( $error == 0 )
	{
		my $status = &setFarmVS( $farmname, $service, "ns", $ns );
		if ( $status == 0 )
		{
			$farm_config_changed = 1;
			&successmsg(
						"The name server for the zone $service has been successfully changed" );
			&runFarmReload( $farmname );
		}
		else
		{
			&errormsg( "The name server for the zone $service has failed" );
		}
	}
}

#editfarm delete service
if ( $action eq "editfarm-deleteservice" )
{
	if ( $service_type =~ /^$/ )
	{
		&errormsg( "Invalid service type, please select a valid value" );
		$error = 1;
	}
	elsif ( $error == 0 )
	{
		if ( $service_type eq "zone" )
		{
			my $status = &setGSLBFarmDeleteZone( $farmname, $service );
			if ( $status == 0 )
			{
				&successmsg( "Deleted zone $service in farm $farmname" );
				&runFarmReload( $farmname );
			}
		}
		else
		{
			if ( $service_type eq "service" )
			{
				my $rc = &setGSLBFarmDeleteService( $farmname, $service );

				# rc = return code
				if ( $rc == 0 )
				{
					$farm_config_changed = 1;
					&successmsg( "Deleted service $service in farm $farmname" );
					&setFarmRestart( $farmname );
				}
				elsif ( $rc == -1 )
				{
					&errormsg( "Service not found" );
				}
				elsif ( $rc == -2 )
				{
					&errormsg( "Unable to remove a service in use by any zone" );
				}
			}
		}
	}
}

#Edit Global Parameters
if ( $action eq "editfarm-Parameters" )
{

	#Actual Parameters
	my $actualvip   = &getFarmVip( "vip",  $farmname );
	my $actualvport = &getFarmVip( "vipp", $farmname );

	#change Farm's name
	if ( $farmname ne $newfarmname )
	{
		#Check if farmname has correct characters (letters, numbers and hyphens)
		my $farmnameok = &checkFarmnameOK( $newfarmname );

		#Check the farm's name change
		if ( "$newfarmname" eq "$farmname" )
		{
			&errormsg(
				"The new farm's name \"$newfarmname\" is the same as the old farm's name \"$farmname\". Nothing to do"
			);
		}
		elsif ( $farmnameok ne 0 )
		{
			&errormsg(
					   "Farm name is not valid, only allowed numbers, letters and hyphens" );
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
				# zcluster: stop farm in remote node
				&runZClusterRemoteManager( 'farm', 'stop', $farmname );

				#Change farm name
				$fnchange = &setNewFarmName( $farmname, $newfarmname );

				# zcluster: start farm in remote node
				&runZClusterRemoteManager( 'farm', 'start', $farmname ) if $fnchange;

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
					$farm_config_changed = 1;
					&successmsg( "The Farm $farmname has been just renamed to $newfarmname." );
					$farmname = $newfarmname;
				}
			}
		}
		$action = "editfarm";
	}

	if ( $actualvip ne $vip or $actualvport ne $vipp )
	{
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
				$farm_config_changed = 1;
				&successmsg(
					"Virtual IP and Virtual Port has been modified, the $farmname farm need be restarted"
				);
				&setFarmRestart( $farmname );
			}
			else
			{
				&errormsg(
						   "It's not possible to change the $farmname farm virtual IP and port" );
			}
		}
	}
}

#delete server
if ( $action eq "editfarm-deleteserver" )
{
	$error = 0;
	if ( $service =~ /^$/ )
	{
		&errormsg( "Invalid $service_type, please insert a valid value" );
		$error = 1;
	}
	if ( $id_server =~ /^$/ )
	{
		&errormsg( "Invalid id server, please insert a valid value" );
		$error = 1;
	}
	if ( $farmname =~ /^$/ )
	{
		&errormsg( "Invalid farmname, please insert a valid value" );
		$error = 1;
	}
	if ( $service_type eq "zone" )
	{
		if ( $error == 0 )
		{
			$status = &remFarmZoneResource( $id_server, $farmname, $service );
			if ( $status != -1 )
			{
				$farm_config_changed = 1;
				&runFarmReload( $farmname );
				&successmsg(
						  "The resource with ID $id_server in the zone $service has been deleted" );
			}
			else
			{
				&errormsg(
					"It's not possible to delete the resource server with ID $id_server in the zone $service"
				);
			}
		}
		$service_type = "zone";
	}
	else
	{
		if ( $error == 0 )
		{
			$status = &remFarmServiceBackend( $id_server, $farmname, $service );

			if ( $status != -1 )
			{
				if ( $status == -2 )
				{
					&errormsg(
						"You need at least one bakcend in the service. It's not possible to delete the backend."
					);
				}
				else
				{
					$farm_config_changed = 1;
					&successmsg(
							"The backend with ID $id_server in the service $service has been deleted" );
					&setFarmRestart( $farmname );
				}
			}
			else
			{
				&errormsg(
					"It's not possible to delete the backend with ID $id_server in the service $service"
				);
			}
		}
		$service_type = "service";
	}
}

#save server
if ( $action eq "editfarm-saveserver" )
{
	$error = 0;
	my $forbittenName=0;

	if ( $service_type eq "zone" )
	{
		if ( $service =~ /^$/ )
		{
			&errormsg( "Invalid zone, please insert a valid value" );
			$error = 1;
		}
		
		
		# let character exceptions in resource name for PTR and SRV types
		if ( $type_server eq 'SRV' || $type_server eq 'PTR' || $type_server eq 'NAPTR') 
		{
			if( $resource_server !~ /^[\@a-zA-Z1-9\-_\.]*$/ )
			{
				&errormsg(
					"Invalid resource name, please for this farm insert a valid value \(only letters, numbers '-', '_' and '.' character are allowed\)"
				);
				$error = 1;
			}
		}
		else
		{
			if ( $resource_server !~ /^[\@a-zA-Z1-9\-]*$/ )
			{
				&errormsg(
					"Invalid resource name, please insert a valid value \(only letters, numbers and '-' character are allowed\)"
				);
				$error = 1;
			}
		}
		if ( $resource_server =~ /^$/ )
		{
			&errormsg( "Invalid resource server, please insert a valid value" );
			$error = 1;
		}
		
		if ( $rdata_server =~ /^$/ )
		{
			&errormsg( "Invalid RData, please insert a valid value" );
			$error = 1;
		}
		if ( $error == 0 )
		{
			if ( ( $type_server eq "A" ) && &ipversion( $rdata_server ) != 4 )
			{
				&errormsg(
					"If you choose A type, RDATA must be a valid IPv4 address, $resource_server not modified for the zone $service"
				);
			}
			elsif ( ( $type_server eq "AAAA" ) && &ipversion( $rdata_server ) != 6 )
			{
				&errormsg(
					"If you choose AAAA type, RDATA must be a valid IPv6 address, $resource_server not modified for the zone $service"
				);
			}
			else
			{
				$status =
				  &setFarmZoneResource( $id_server, $resource_server, $ttl_server,
										$type_server, $rdata_server, $farmname, $service );

				if ( $status != -1 )
				{
					$farm_config_changed = 1;
					&runFarmReload( $farmname );
					&successmsg(
							"The resource name $resource_server for the zone $zone has been modified" );
				}
				else
				{
					&errormsg(
						"It's not possible to modify the resource name $resource_server for the zone $zone"
					);
				}
			}
		}
	}
	else
	{
		if ( $service =~ /^$/ )
		{
			&errormsg( "Invalid service, please insert a valid value" );
			$error = 1;
		}
		if ( $error == 0 )
		{
			$status =
			  &setGSLBFarmNewBackend( $farmname, $service, $lb, $id_server, $rip_server );

			if ( $status != -1 )
			{
				$farm_config_changed = 1;
				&successmsg(
							 "The backend $rip_server for the service $service has been modified" );
				&setFarmRestart( $farmname );
			}
			else
			{
				&errormsg(
					  "It's not possible to modify the backend $rip_server for the service $service"
				);
			}
		}
	}
}

if ( $action eq "editfarm-addservice" )
{
	if ( $service_type eq "zone" )
	{
		if ( $zone !~ /.*\..*/ )
		{
			&errormsg(
				"Wrong zone name. The name has to be like zonename.com, zonename.net, etc. The zone $zone can't be created"
			);
		}
		else
		{
			my $result = &setGSLBFarmNewZone( $farmname, $zone );

			if ( $result == 0 )
			{
				$farm_config_changed = 1;
				&setFarmRestart( $farmname );
				&successmsg( "Zone $zone has been added to the farm" );
			}
			else
			{
				&errormsg( "The zone $zone can't be created" );
			}
		}
	}
	else
	{
		if ( $service_type eq "service" )
		{
			if ( $service !~ /^[a-zA-Z1-9\-]*$/ )
			{
				&errormsg(
					"Invalid service name, please insert a valid value \(only letters, numbers and '-' character are allowed\)"
				);
				$error = 1;
			}
			if ( $service =~ /^$/ )
			{
				&errormsg( "Invalid service, please insert a valid value" );
				$error = 1;
			}
			if ( $farmname =~ /^$/ )
			{
				&errormsg( "Invalid farm name, please insert a valid value" );
				$error = 1;
			}
			if ( $lb =~ /^$/ )
			{
				&errormsg( "Invalid algorithm, please insert a valid value" );
				$error = 1;
			}
			if ( $error == 0 )
			{
				$status = &setGSLBFarmNewService( $farmname, $service, $lb );
				if ( $status != -1 )
				{
					$farm_config_changed = 1;
					&successmsg( "The service $service has been successfully created" );
					&setFarmRestart( $farmname );
				}
				else
				{
					&errormsg( "It's not possible to create the service $service" );
				}
			}
		}
	}
}

#$service=$farmname;
#check if the farm need a restart
if ( -e "/tmp/$farmname.lock" )
{
	&tipmsg(
		  "There're changes that need to be applied, stop and start farm to apply them!"
	);
}

# zcluster: apply remote changes
if ( $farm_config_changed && &getFarmStatus( $farmname ) eq 'up' )
{
	# zcluster: restart farm in remote node
	&runZClusterRemoteManager( 'farm', 'restart', $farmname );
}

1;
