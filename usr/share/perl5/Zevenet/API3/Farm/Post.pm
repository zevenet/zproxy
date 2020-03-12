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

use Zevenet::Net::Util;

sub new_farm    # ( $json_obj )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;

   # 3 Mandatory Parameters ( 1 mandatory for HTTP or GSBL and optional for L4xNAT )
   #
   #	- farmname
   #	- profile
   #	- vip
   #	- vport: optional for L4xNAT and not used in Datalink profile.

	my $description = "Creating farm '$json_obj->{ farmname }'";

	# validate FARM NAME
	unless (    $json_obj->{ farmname }
			 && &getValidFormat( 'farm_name', $json_obj->{ farmname } ) )
	{
		my $errormsg =
		  "Error trying to create a new farm, the farm name is required to have alphabet letters, numbers or hypens (-) only.";
		&zenlog( $errormsg, "error", "FARMS" );

		# Error
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse( { code => 400, body => $body } );
	}

	# check if FARM NAME already exists
	unless ( &getFarmType( $json_obj->{ farmname } ) == 1 )
	{
		my $errormsg =
		  "Error trying to create a new farm, the farm name already exists.";
		&zenlog( $errormsg, "error", "FARMS" );

		# Error
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse( { code => 400, body => $body } );
	}

	# Farm PROFILE validation
	if ( $json_obj->{ profile } !~ /^(:?HTTP|GSLB|L4XNAT|DATALINK)$/i )
	{
		my $errormsg =
		  "Error trying to create a new farm, the farm's profile is not supported.";
		&zenlog( $errormsg, "error", "FARMS" );

		# Error
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse( { code => 400, body => $body } );
	}

	# VIP validation
	# vip must be available
	if ( !grep { $_ eq $json_obj->{ vip } } &listallips() )
	{
		my $errormsg =
		  "Error trying to create a new farm, an available virtual IP must be set.";
		&zenlog( $errormsg, "error", "FARMS" );

		# Error
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse( { code => 400, body => $body } );
	}

   # VPORT validation
   # vport must be in range, have correct format in multiport and must not be in use
   #~ if ( $json_obj->{ vport } eq "" )
   #~ {
   #~ $vport = "*";
   #~ }
   #~ else
   #~ {
   #~ $vport = $json_obj->{ vport };
   #~ }
	if ( !&getValidPort( $json_obj->{ vport }, $json_obj->{ profile } ) )
	{
		my $errormsg =
		  "Error trying to create a new farm, the Virtual port must be an acceptable value and must be available.";
		&zenlog( $errormsg, "error", "FARMS" );

		# Error
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse( { code => 400, body => $body } );
	}

	$json_obj->{ 'interface' } = &getInterfaceOfIp( $json_obj->{ 'vip' } );

	#~ $json_obj->{ profile } = 'L4xNAT' if $json_obj->{ profile } eq 'L4XNAT';

	my $status = &runFarmCreate(
								 $json_obj->{ profile },
								 $json_obj->{ vip },
								 $json_obj->{ vport },
								 $json_obj->{ farmname },
								 $json_obj->{ interface }
	);

	if ( $status eq '-1' )
	{
		&zenlog(
			"Error trying to create a new farm $json_obj->{ farmname }, it can't be created.",
			"error", "FARMS"
		);

		# Error
		my $errormsg = "The $json_obj->{ farmname } farm can't be created";

		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse( { code => 400, body => $body } );
	}
	else
	{
		&zenlog(
				 "Success, the farm $json_obj->{ farmname } has been created successfully.",
				 "info", "FARMS" );

		# Success
		my $out_p;

		if ( $json_obj->{ profile } =~ /^DATALINK$/i )
		{
			$out_p = {
					   farmname  => $json_obj->{ farmname },
					   profile   => $json_obj->{ profile },
					   vip       => $json_obj->{ vip },
					   interface => $json_obj->{ interface },
			};
		}
		else
		{
			$out_p = {
					   farmname  => $json_obj->{ farmname },
					   profile   => $json_obj->{ profile },
					   vip       => $json_obj->{ vip },
					   vport     => $json_obj->{ vport },
					   interface => $json_obj->{ interface },
			};
		}

		my $body = {
					 description => $description,
					 params      => $out_p,
		};

		include 'Zevenet::Cluster';

		&runZClusterRemoteManager( 'farm', 'start', $json_obj->{ farmname } );

		&httpResponse( { code => 201, body => $body } );
	}
}

1;
