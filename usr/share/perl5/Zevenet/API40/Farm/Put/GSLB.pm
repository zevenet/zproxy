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

use Zevenet::API40::HTTP;

use Zevenet::Farm::Action;
use Zevenet::Farm::Base;
use Zevenet::Farm::Config;

include 'Zevenet::Farm::GSLB::Config';

sub modify_gslb_farm    # ( $json_obj,	$farmname )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $farmname = shift;

	my $desc = "Modify GSLB farm '$farmname'";

	my $farm_st = &getFarmStruct( $farmname );
	my $status  = $farm_st->{ status };

	# Check that the farm exists
	# it is checked in the global PUT function

	require Zevenet::Net::Interface;
	my $ip_list = &getIpAddressList();

	my $params = {
				   "newfarmname" => {
									  'valid_format' => 'farm_name',
									  'non_blank'    => 'true',
									  'exceptions'   => ['0'],
				   },
				   "vport" => {
								'interval'  => "1,65535",
								'non_blank' => 'true',
				   },
				   "vip" => {
							  'values'     => $ip_list,
							  'non_blank'  => 'true',
							  'format_msg' => 'expects an IP'
				   },
	};

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	# Extend parameter checks
	# Get current vip & vport
	my $vip   = $json_obj->{ vip }   // &getFarmVip( 'vip',  $farmname );
	my $vport = $json_obj->{ vport } // &getFarmVip( 'vipp', $farmname );

	if ( exists ( $json_obj->{ vip } ) or exists ( $json_obj->{ vport } ) )
	{
		require Zevenet::Net::Validate;
		if ( $status eq 'up' and &checkport( $vip, $vport, $farmname ) eq 'true' )
		{
			my $msg =
			  "The '$vip' ip and '$vport' port are being used for another farm. This farm should be sopped before modifying it";
			&httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
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

	# Modify Farm's Name
	if ( exists $json_obj->{ newfarmname } )
	{
		unless ( $status eq 'down' )
		{
			my $msg = 'Cannot change the farm name while running';
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}

		#Check if the new farm's name alredy exists
		if ( &getFarmExists( $json_obj->{ newfarmname } ) )
		{
			my $msg = "The farm $json_obj->{newfarmname} already exists, try another name.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}

		#Change farm name
		if ( &setNewFarmName( $farmname, $json_obj->{ newfarmname } ) )
		{
			my $msg =
			  "The name of the farm can't be modified, delete the farm and create a new one.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}

		$farmname = $json_obj->{ newfarmname };
	}

	if ( exists $json_obj->{ vip } )
	{
		# the ip must exist in some interface
		require Zevenet::Net::Interface;
		unless ( &getIpAddressExists( $json_obj->{ vip } ) )
		{
			my $msg = "The vip IP must exist in some interface.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
	}

	# Modify only vip
	if ( exists $json_obj->{ vip } or exists $json_obj->{ vport } )
	{
		my $vip   = $json_obj->{ vip }   // $farm_st->{ vip };
		my $vport = $json_obj->{ vport } // $farm_st->{ vport };

		if ( &setFarmVirtualConf( $vip, $vport, $farmname ) )
		{
			my $msg = "Could not set the virtual configuration.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
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

	if ( $status ne "down" )
	{
		$body->{ info } =
		  "There're changes that need to be applied, stop and start farm to apply them!";

		&setFarmRestart( $farmname );
		$body->{ status } = 'needed restart';
	}

	return &httpResponse( { code => 200, body => $body } );
}

1;

