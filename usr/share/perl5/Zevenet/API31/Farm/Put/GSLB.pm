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

use Zevenet::API31::HTTP;

use Zevenet::Farm::Action;
use Zevenet::Farm::Base;
include 'Zevenet::Farm::GSLB::Config';

sub modify_gslb_farm    # ( $json_obj,	$farmname )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $farmname = shift;

	my $desc = "Modify GSLB farm '$farmname'";

	# Flags
	my $reload_flag  = "false";
	my $restart_flag = "false";
	my $error        = "false";
	my $changedname  = "false";
	my $status;

	# Check that the farm exists
	if ( !&getFarmExists( $farmname ) )
	{
		my $msg = "The farmname $farmname does not exist.";
		&httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	if ( my $param_msg =
		 &getValidOptParams( $json_obj, ["vip", "vport", "newfarmname"] ) )
	{
		&httpErrorResponse( code => 400, desc => $desc, msg => $param_msg );
	}

	my $reload_ipds = 0;
	if (    exists $json_obj->{ vport }
		 || exists $json_obj->{ vip }
		 || exists $json_obj->{ newfarmname } )
	{
		include 'Zevenet::IPDS::Base';
		$reload_ipds = 1;
		&runIPDSStopByFarm( $farmname );
		include 'Zevenet::Cluster';
		&runZClusterRemoteManager( 'ipds', 'stop', $farmname );
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
			my $msg = 'Cannot change the farm name while running';
			&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}

		my $newfstat;
		unless ( length $json_obj->{ newfarmname } )
		{
			my $msg = "Invalid newfarmname, can't be blank.";
			&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}

		# Check if farmname has correct characters (letters, numbers and hyphens)
		unless ( $json_obj->{ newfarmname } =~ /^[a-zA-Z0-9\-]*$/ )
		{
			my $msg = "Invalid newfarmname.";
			&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}

		if ( $json_obj->{ newfarmname } ne $farmname )
		{
			#Check if the new farm's name alredy exists
			my $newffile = &getFarmFile( $json_obj->{ newfarmname } );
			if ( $newffile != -1 )
			{
				my $msg = "The farm $json_obj->{newfarmname} already exists, try another name.";
				&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
			}

			my $oldfstat = &runFarmStop( $farmname, "true" );
			if ( $oldfstat )
			{
				my $msg = "The farm is not disabled, are you sure it's running?";
				&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
			}

			#Change farm name
			my $fnchange = &setNewFarmName( $farmname, $json_obj->{ newfarmname } );
			$changedname = "true";

			if ( $fnchange == -1 )
			{
				my $msg =
				  "The name of the farm can't be modified, delete the farm and create a new one.";
				&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
			}
			elsif ( $fnchange == -2 )
			{
				my $msg = "Invalid newfarmname, the new name can't be empty.";
				&httpErrorResponse( code => 400, desc => $desc, msg => $msg );

				#~ $newfstat = &runFarmStart( $farmname, "true" );
				if ( $newfstat != 0 )
				{
					my $msg =
					  "The farm isn't running, check if the IP address is up and the PORT is in use.";
					&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
				}
			}

			$farmname = $json_obj->{ newfarmname };

			#~ $newfstat = &runFarmStart( $farmname, "true" );
			if ( $newfstat != 0 )
			{
				my $msg =
				  "The farm isn't running, check if the IP address is up and the PORT is in use.";
				&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
			}
		}
	}

	if ( exists ( $json_obj->{ vip } ) )
	{
		# the ip must exist in some interface
		require Zevenet::Net::Interface;
		unless ( &getIpAddressExists( $json_obj->{ vip } ) )
		{
			my $msg = "The vip IP must exist in some interface.";
			&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
		unless ( length $json_obj->{ vip } )
		{
			my $msg = "Invalid vip, can't be blank.";
			&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

	if ( exists ( $json_obj->{ vport } ) )
	{
		$json_obj->{ vport } += 0;
		unless ( $json_obj->{ vport } =~ /^\d+$/ )
		{
			my $msg = "Invalid vport.";
			&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

	require Zevenet::Farm::Config;

	# Modify only vip
	if ( exists ( $json_obj->{ vip } ) && !exists ( $json_obj->{ vport } ) )
	{
		my $error = &setFarmVirtualConf( $json_obj->{ vip }, $vport, $farmname );
		if ( $error )
		{
			my $msg = "Invalid vip.";
			&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}

		$restart_flag = "true";
	}

	# Modify only vport
	if ( exists ( $json_obj->{ vport } ) && !exists ( $json_obj->{ vip } ) )
	{
		my $error = &setFarmVirtualConf( $vip, $json_obj->{ vport }, $farmname );
		if ( $error )
		{
			my $msg = "Could not set virtual port.";
			&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}

		$restart_flag = "true";
	}

	# Modify both vip & vport
	if ( exists $json_obj->{ vip } && exists $json_obj->{ vport } )
	{
		my $error =
		  &setGSLBFarmVirtualConf( $json_obj->{ vip }, $json_obj->{ vport },
								   $farmname );
		if ( $error )
		{
			my $msg = "Invalid vport or invalid vip.";
			&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}

		$restart_flag = "true";
	}

	# no error found, return successful response
	&zenlog( "Success, some parameters have been changed in farm $farmname.",
			 "info", "GSLB" );

	if ( $reload_ipds )
	{
		include 'Zevenet::IPDS::Base';
		&runIPDSStartByFarm( $farmname );
		include 'Zevenet::Cluster';
		&runZClusterRemoteManager( 'ipds', 'start', $farmname );
	}

	$json_obj->{ vport } += 0 if ( exists $json_obj->{ vport } );
	my $body = {
				 description => $desc,
				 params      => $json_obj,
	};

	if ( $changedname ne "true" )
	{
		$body->{ info } =
		  "There're changes that need to be applied, stop and start farm to apply them!";

		if ( &getFarmStatus( $farmname ) eq 'up' )
		{
			&setFarmRestart( $farmname );
			$body->{ status } = 'needed restart';
		}
	}

	&httpResponse( { code => 200, body => $body } );
}

1;
