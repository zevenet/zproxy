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

### CONTROLLER DATALINK FARM ###

#Edit Global Parameters

#Actual Parameters
my $actuallb = &getFarmAlgorithm( $farmname );

if ( $actuallb == -1 )
{
	$actuallb = "weight";
}

my $actualvip   = &getFarmVip( "vip",  $farmname );
my $actualvport = &getFarmVip( "vipp", $farmname );
my ( $fdev, $vip ) = split ( " ", $vip );

if ( $vip ne '' )
{
	#change vip and vipp
	if ( $actualvip ne $vip )
	{
		$error = 0;

		if ( $fdev eq "" )
		{
			&errormsg( "Invalid Interface value" );
			$error = 1;
		}
		if ( $vip eq "" )
		{
			&errormsg( "Invalid Virtual IP value" );
			$error = 1;
		}
		if ( $error == 0 )
		{
			$status = &setFarmVirtualConf( $vip, $fdev, $farmname );
			if ( $status != -1 )
			{
				&successmsg(
					"Virtual IP and Interface has been modified, the $farmname farm has been restarted"
				);
			}
			else
			{
				&errormsg(
						"It's not possible to change the $farmname farm virtual IP and interface" );
			}
		}
	}
}

if ( $newfarmname ne "" )
{
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
					&successmsg( "The Farm $farmname has been just renamed to $newfarmname." );
					$farmname = $newfarmname;
				}
			}
		}
	}
}

if ( defined ( $lb ) )
{
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
}

#}

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
	if ( $rip_server =~ /^$/ || $if =~ /^$/ )
	{
		&errormsg(
			 "Invalid IP address and network interface for a real server, it can't be blank"
		);
		$error = 1;
	}
	if ( $priority_server ne ""
		 && ( $priority_server <= 0 || $priority_server >= 10 ) )
	{
		&errormsg( "Invalid priority value for real server" );
		$error = 1;
	}
	if ( $weight_server ne ""
		 && ( $weight_server <= 0 || $weight_server >= 10000 ) )
	{
		&errormsg( "Invalid weight value for real server" );
		$error = 1;
	}

	if ( $error == 0 )
	{
		$status =
		  &setFarmServer( $id_server, $rip_server, $if, "", $weight_server,
						  $priority_server, "", $farmname );

		if ( $status != -1 )
		{
			&successmsg(
				"The real server with ip $rip_server and local interface $if for the $farmname farm has been modified"
			);
		}
		else
		{
			&errormsg(
				"It's not possible to modify the real server with ip $rip_server and interface $if for the $farmname farm"
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

1;
