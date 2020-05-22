#!/usr/bin/perl
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

# POST

# POST /farms/<farmname>/zones Create a new zone in a gslb Farm
sub new_farm_zone    # ( $json_obj, $farmname )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $farmname = shift;

	my $zone = $json_obj->{ id };

	# Check that the farm exists
	require Zevenet::Farm::Core;

	if ( !&getFarmExists( $farmname ) )
	{
		# Error
		my $errormsg = "The farmname $farmname does not exist.";
		my $body = {
					 description => "New zone",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 404, body => $body } );
	}

	if ( $json_obj->{ id } =~ /^$/ )
	{
		&zenlog(
				 "Error trying to create a new zone in farm $farmname, invalid zone name.",
				 "error", "GSLB" );

		# Error
		my $errormsg = "Invalid zone name, please insert a valid value.";
		my $body = {
					 description => "New zone " . $json_obj->{ id },
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}

	if ( $json_obj->{ id } !~ /.*\..*/ )
	{
		&zenlog(
			"Wrong zone name. The name has to be like zonename.com, zonename.net, etc. The zone $zone can't be created",
			"error", "GSLB"
		);

		# Error
		my $errormsg =
		  "Invalid zone name, please insert a valid value like zonename.com, zonename.net, etc. The zone $zone can't be created.";
		my $body = {
					 description => "New zone " . $json_obj->{ id },
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}

	include 'Zevenet::Farm::GSLB::Zone';

	my $result = &setGSLBFarmNewZone( $farmname, $json_obj->{ id } );
	if ( $result eq "0" )
	{
		&zenlog(
			"Success, a new zone has been created in farm $farmname with id $json_obj->{id}.",
			"info", "GSLB"
		);

		# Success
		if ( &getFarmStatus( $farmname ) eq 'up' )
		{
			include 'Zevenet::Cluster';

			&runGSLBFarmReload( $farmname );
			&runZClusterRemoteManager( 'farm', 'restart', $farmname );
		}

		my $body = {
					 description => "New zone " . $json_obj->{ id },
					 params      => { id => $json_obj->{ id } },
		};

		&httpResponse( { code => 201, body => $body } );
	}
	else
	{
		&zenlog(
			"Error trying to create a new zone in farm $farmname with id $json_obj->{id}, it's not possible to create the zone.",
			"error", "GSLB"
		);

		# Error
		my $errormsg = "It's not possible to create the zone " . $json_obj->{ id };
		my $body = {
					 description => "New zone " . $json_obj->{ id },
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}
}

# POST /farms/<farmname>/zoneresources Create a new resource of a zone in a gslb Farm
sub new_farm_zone_resource    # ( $json_obj, $farmname, $zone )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $farmname = shift;
	my $zone     = shift;

	my $description = "New zone resource";
	my $default_ttl = '';

	# validate FARM NAME
	require Zevenet::Farm::Core;

	if ( !&getFarmExists( $farmname ) )
	{
		my $errormsg = "The farmname $farmname does not exist.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 404, body => $body } );
	}

	# validate FARM TYPE
	unless ( &getFarmType( $farmname ) eq 'gslb' )
	{
		my $errormsg = "Only GSLB profile is supported for this request.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}

	# validate ZONE
	include 'Zevenet::Farm::GSLB::Zone';

	unless ( grep { $_ eq $zone } &getGSLBFarmZones( $farmname ) )
	{
		my $errormsg = "Could not find the requested zone.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 404, body => $body } );
	}

	# validate RESOURCE NAME
	unless (    $json_obj->{ rname }
			 && &getValidFormat( 'resource_name', $json_obj->{ rname } ) )
	{
		&zenlog(
			"Error trying to create a new resource in zone $zone in farm $farmname, the parameter zone resource name (rname) doesn't exist.",
			"error", "GSLB"
		);

		# Error
		my $errormsg =
		  "The parameter zone resource name (rname) doesn't exist, please insert a valid value.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}

	# validate RESOURCE TTL
	$json_obj->{ ttl } = $default_ttl if !exists $json_obj->{ ttl };

	unless (
			 $json_obj->{ ttl } eq ''
			 || (    &getValidFormat( 'resource_ttl', $json_obj->{ ttl } )
				  && $json_obj->{ ttl } != 0 )
	  )    # (1second-1year)
	{
		&zenlog(
			"Error trying to create a new resource in zone $zone in farm $farmname, the parameter time to live value (ttl) doesn't exist.",
			"error", "GSLB"
		);

		# Error
		my $errormsg =
		  "The parameter time to live value (ttl) doesn't exist, please insert a valid value.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}

	# validate RESOURCE TYPE
	unless ( &getValidFormat( 'resource_type', $json_obj->{ type } ) )
	{
		&zenlog(
			"Error trying to create a new resource in zone $zone in farm $farmname, the parameter DNS record type (type) doesn't exist.",
			"error", "GSLB"
		);

		# Error
		my $errormsg =
		  "The parameter DNS record type (type) doesn't exist, please insert a valid value.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}

	# validate RESOURCE DATA
	include 'Zevenet::Farm::GSLB::Service';

	unless (
		 !grep ( /$json_obj->{ rdata }/,
				 &getGSLBFarmServices( $farmname ) && $json_obj->{ type } eq 'DYNA' )
		 && &getValidFormat( "resource_data_$json_obj->{ type }", $json_obj->{ rdata } )
	  )
	{
		my $errormsg = "If you choose $json_obj->{ type } type, ";

		$errormsg .= "RDATA must be a valid IPv4 address,"
		  if ( $json_obj->{ type } eq "A" );
		$errormsg .= "RDATA must be a valid IPv6 address,"
		  if ( $json_obj->{ type } eq "AAAA" );
		$errormsg .= "RDATA format is not valid," if ( $json_obj->{ type } eq "NS" );
		$errormsg .= "RDATA must be a valid format ( foo.bar.com ),"
		  if ( $json_obj->{ type } eq "CNAME" );
		$errormsg .= "RDATA must be a valid service,"
		  if ( $json_obj->{ type } eq 'DYNA' );
		$errormsg .= "RDATA must be a valid format ( mail.example.com ),"
		  if ( $json_obj->{ type } eq 'MX' );
		$errormsg .= "RDATA must be a valid format ( 10 60 5060 host.example.com ),"
		  if ( $json_obj->{ type } eq 'SRV' );
		$errormsg .= "RDATA must be a valid format ( foo.bar.com ),"
		  if ( $json_obj->{ type } eq 'PTR' );

		# TXT and NAPTR input let all characters

		$errormsg .= " $json_obj->{ rname } not added to zone $zone";
		&zenlog( $errormsg, "error", "GSLB" );

		# Error
		$errormsg =
		  "The parameter zone resource server (rdata) doesn't correct format, please insert a valid value.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}

	my $status = &setGSLBFarmZoneResource(
										   "",
										   $json_obj->{ rname },
										   $json_obj->{ ttl },
										   $json_obj->{ type },
										   $json_obj->{ rdata },
										   $farmname,
										   $zone,
	);

	if ( $status != -1 )
	{
		require Zevenet::Farm::Base;

		&zenlog(
				"Success, a new resource has been created in zone $zone in farm $farmname.",
				"info", "GSLB" );

		# Success
		if ( &getFarmStatus( $farmname ) eq 'up' )
		{
			include 'Zevenet::Cluster';

			&runGSLBFarmReload( $farmname );
			&runZClusterRemoteManager( 'farm', 'restart', $farmname );
		}

		$json_obj->{ ttl } = undef if !$json_obj->{ ttl };

		my $message = "Resource added";
		my $body = {
					 description => $description,
					 params      => {
								 rname => $json_obj->{ rname },
								 zone  => $zone,
								 ttl   => $json_obj->{ ttl },
								 type  => $json_obj->{ type },
								 rdata => $json_obj->{ rdata },
					 },
					 message => $message,
		};

		include 'Zevenet::Farm::GSLB::Validate';
		my $checkConf = &getGSLBCheckConf( $farmname );

		if ( $checkConf =~ /^(.+?)\s/ )
		{
			$checkConf =
			  "The resource $1 gslb farm break the configuration. Please check the configuration";
			$body->{ params }->{ warning } = $checkConf;
		}

		&httpResponse( { code => 201, body => $body } );
	}
	else
	{
		&zenlog(
			"Error trying to create a new resource in zone $zone in farm $farmname, it's not possible to create a new resource.",
			"error", "GSLB"
		);

		# Error
		my $errormsg =
		  "It's not possible to create a new resource in the zone $zone in farm $farmname.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}
}

# GET

#	/farms/<GSLBfarm>/zones/<zone>/resources
sub gslb_zone_resources    # ( $farmname, $zone )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $farmname = shift;
	my $zone     = shift;

	my $description = "List zone resources";

	require Zevenet::Farm::Core;

	# validate FARM NAME
	if ( !&getFarmExists( $farmname ) )
	{
		# Error
		my $errormsg = "Farm name not found";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 404, body => $body } );
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

		&httpResponse( { code => 400, body => $body } );
	}

	# validate ZONE
	include 'Zevenet::Farm::GSLB::Zone';

	if ( !scalar grep { $_ eq $zone } &getGSLBFarmZones( $farmname ) )
	{
		my $errormsg = "Could not find the requested zone.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 404, body => $body } );
	}

	#
	# Zones
	#

	my $resources = &getGSLBResources( $farmname, $zone );

	for my $resource ( @{ $resources } )
	{
		$resource->{ ttl } = undef if !$resource->{ ttl };
		$resource->{ ttl } += 0 if $resource->{ ttl };
	}

	# Success
	my $body = {
				 description => $description,
				 params      => $resources,
	};

	&httpResponse( { code => 200, body => $body } );
}

# PUT

sub modify_zone_resource    # ( $json_obj, $farmname, $zone, $id_resource )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $json_obj, $farmname, $zone, $id_resource ) = @_;

	my $description = "Modify zone resource";
	my $error;

	require Zevenet::Farm::Core;

	# validate FARM NAME
	if ( !&getFarmExists( $farmname ) )
	{
		# Error
		my $errormsg = "The farmname $farmname does not exist.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 404, body => $body } );
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

		&httpResponse( { code => 400, body => $body } );
	}

	# validate ZONE
	include 'Zevenet::Farm::GSLB::Zone';
	unless ( grep { $_ eq $zone } &getGSLBFarmZones( $farmname ) )
	{
		my $errormsg = "Could not find the requested zone.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 404, body => $body } );
	}

	require Zevenet::Farm::Config;

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

		&httpResponse( { code => 404, body => $body } );
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
				"Error trying to modify the resources in a farm $farmname, invalid rname, can't be blank.",
				"error", "GSLB"
			);
		}
	}

	if ( !$error && exists ( $json_obj->{ ttl } ) )
	{
		if ( $json_obj->{ ttl } == undef
			 || (    &getValidFormat( 'resource_ttl', $json_obj->{ ttl } )
				  && $json_obj->{ ttl } ) )
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
					 "Error trying to modify the resources in a farm $farmname, invalid ttl.",
					 "error", "GSLB" );
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
					 "Error trying to modify the resources in a farm $farmname, invalid type.",
					 "error", "GSLB" );
		}
	}

	if ( !$error && exists ( $json_obj->{ rdata } ) )
	{
		$auxData = $json_obj->{ rdata };
	}

	# validate RESOURCE DATA
	unless (
		   !grep ( /$auxData/, &getGSLBFarmServices( $farmname ) && $auxType eq 'DYNA' )
		   && &getValidFormat( "resource_data_$auxType", $auxData ) )
	{
		my $errormsg = "If you choose $auxType type, ";

		$errormsg .= "RDATA must be a valid IPv4 address," if ( $auxType eq "A" );
		$errormsg .= "RDATA must be a valid IPv6 address," if ( $auxType eq "AAAA" );
		$errormsg .= "RDATA format is not valid,"          if ( $auxType eq "NS" );
		$errormsg .= "RDATA must be a valid format ( foo.bar.com ),"
		  if ( $auxType eq "CNAME" );
		$errormsg .= "RDATA must be a valid service," if ( $auxType eq 'DYNA' );
		$errormsg .= "RDATA must be a valid format ( mail.example.com ),"
		  if ( $auxType eq 'MX' );
		$errormsg .= "RDATA must be a valid format ( 10 60 5060 host.example.com ),"
		  if ( $auxType eq 'SRV' );
		$errormsg .= "RDATA must be a valid format ( foo.bar.com ),"
		  if ( $auxType eq 'PTR' );

		# TXT and NAPTR input let all characters
		&zenlog( $errormsg, "error", "GSLB" );

		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}
	else
	{
		$rsc->{ data } = $auxData;
		$rsc->{ type } = $auxType;
	}

	if ( !$error )
	{
		my $status = &setGSLBFarmZoneResource(
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
				"Error trying to modify the resources in a farm $farmname, it's not possible to modify the resource $id_resource in zone $zone.",
				"error", "GSLB"
			);
		}
		elsif ( $status == -2 )
		{
			# Error
			my $errormsg = "The resource with ID $id_resource does not exist.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 404, body => $body } );
		}
	}

	# Print params
	if ( !$error )
	{
		&zenlog(
			"Success, some parameters have been changed in the resource $id_resource in zone $zone in farm $farmname.",
			"info", "GSLB"
		);

		# Success
		my $message = "Resource modified";
		my $body = {
					 description => $description,
					 success     => "true",
					 params      => $json_obj,
					 message     => $message,
		};

		include 'Zevenet::Farm::GSLB::Validate';

		my $checkConf = &getGSLBCheckConf( $farmname );
		if ( $checkConf )
		{
			$body->{ warning } = $checkConf;
		}

		&httpResponse( { code => 200, body => $body } );
	}
	else
	{
		&zenlog(
			"Error trying to modify the resources in a farm $farmname, it's not possible to modify the resource.",
			"error", "GSLB"
		);

		# Error
		my $errormsg = "Errors found trying to modify farm $farmname";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}
}

sub modify_zones    # ( $json_obj, $farmname, $zone )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $json_obj, $farmname, $zone ) = @_;

	my $error;

	require Zevenet::Farm::Core;

	# Check that the farm exists
	if ( !&getFarmExists( $farmname ) )
	{
		# Error
		my $errormsg = "The farmname $farmname does not exist.";
		my $body = {
					 description => "Modify zone",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 404, body => $body } );
	}

	$error = "false";

	# Functions
	if ( $json_obj->{ defnamesv } =~ /^$/ )
	{
		$error = "true";
		&zenlog(
			"Error trying to modify the zones in a farm $farmname, invalid defnamesv, can't be blank.",
			"error", "GSLB"
		);
	}

	if ( $error eq "false" )
	{
		require Zevenet::Farm::Config;

		&setFarmVS( $farmname, $zone, "ns", $json_obj->{ defnamesv } );
		if ( $? eq 0 )
		{
			include 'Zevenet::Farm::GSLB::Config';
			&runGSLBFarmReload( $farmname );
		}
		else
		{
			$error = "true";
			&zenlog(
				"Error trying to modify the zones in a farm $farmname, it's not possible to modify the zone $zone.",
				"error", "GSLB"
			);
		}
	}

	# Print params
	if ( $error ne "true" )
	{
		&zenlog(
			 "Success, some parameters have been changed  in zone $zone in farm $farmname.",
			 "info", "GSLB"
		);

		# Success
		my $body = {
					 description => "Modify zone $zone in farm $farmname",
					 params      => $json_obj,
		};

		&httpResponse( { code => 200, body => $body } );
	}
	else
	{
		&zenlog(
			"Error trying to modify the zones in a farm $farmname, it's not possible to modify the zone $zone.",
			"error", "GSLB"
		);

		# Error
		my $errormsg = "Errors found trying to modify farm $farmname";
		my $body = {
					 description => "Modify zone $zone in farm $farmname",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}
}

# DELETE

# DELETE /farms/<farmname>/zones/<zonename> Delete a zone of a  gslb Farm
sub delete_zone    # ( $farmname, $zone )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farmname, $zone ) = @_;

	require Zevenet::Farm::Core;

	# Check that the farm exists
	if ( !&getFarmExists( $farmname ) )
	{
		# Error
		my $errormsg = "The farmname $farmname does not exist.";
		my $body = {
					 description => "Delete zone",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 404, body => $body } );
	}

	include 'Zevenet::Farm::GSLB::Zone';

	&setGSLBFarmDeleteZone( $farmname, $zone );

	if ( $? eq 0 )
	{
		&zenlog( "Success, the zone $zone in farm $farmname has been deleted.",
				 "info", "GSLB" );

		# Success
		require Zevenet::Farm::Base;

		if ( &getFarmStatus( $farmname ) eq 'up' )
		{
			include 'Zevenet::Cluster';

			&runGSLBFarmReload( $farmname );
			&runZClusterRemoteManager( 'farm', 'restart', $farmname );
		}

		my $message = "The zone $zone in farm $farmname has been deleted.";
		my $body = {
					 description => "Delete zone $zone in farm $farmname.",
					 success     => "true",
					 message     => $message
		};

		&httpResponse( { code => 200, body => $body } );
	}
	else
	{
		&zenlog(
			"Error trying to delete the zone $zone in farm $farmname, the zone hasn't been deleted.",
			"error", "GSLB"
		);

		# Error
		my $errormsg = "Zone $zone in farm $farmname hasn't been deleted.";
		my $body = {
					 description => "Delete zone $zone in farm $farmname",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}
}

#  @api {delete} /farms/<farmname>/zones/<zonename>/resources/<resourceid> Delete a resource of a Zone
sub delete_zone_resource    # ( $farmname, $zone, $resource )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farmname, $zone, $resource ) = @_;

	my $description = "Delete zone resource";

	require Zevenet::Farm::Core;

	# validate FARM NAME
	if ( !&getFarmExists( $farmname ) )
	{
		# Error
		my $errormsg = "The farmname $farmname does not exist.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 404, body => $body } );
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

		&httpResponse( { code => 400, body => $body } );
	}

	# validate ZONE
	include 'Zevenet::Farm::GSLB::Zone';

	if ( !scalar grep { $_ eq $zone } &getGSLBFarmZones( $farmname ) )
	{
		&zenlog(
			"Error trying to delete the resource $resource in zone $zone in farm $farmname, invalid zone name.",
			"error", "GSLB"
		);

		# Error
		my $errormsg = "Invalid zone name, please insert a valid value.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 404, body => $body } );
	}

	require Zevenet::Farm::Config;

	my $backendsvs = &getFarmVS( $farmname, $zone, "resources" );
	my @be = split ( "\n", $backendsvs );
	my ( $resource_line ) = grep { /;index_$resource$/ } @be;

	# validate RESOURCE
	if ( !$resource_line )
	{
		&zenlog(
			"Error trying to delete the resource $resource in zone $zone in farm $farmname, invalid resource id.",
			"error", "GSLB"
		);

		# Error
		my $errormsg = "Invalid resource id, please insert a valid value.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 404, body => $body } );
	}

	my $status = &remGSLBFarmZoneResource( $resource, $farmname, $zone );

	if ( $status != -1 )
	{
		&zenlog(
			"Success, the resource $resource in zone $zone in farm $farmname has been deleted.",
			"info", "GSLB"
		);

		# Success
		require Zevenet::Farm::Base;

		if ( &getFarmStatus( $farmname ) eq 'up' )
		{
			include 'Zevenet::Cluster';

			&runGSLBFarmReload( $farmname );
			&runZClusterRemoteManager( 'farm', 'restart', $farmname );
		}

#~ my $message = "The resource with id $resource in the zone $zone of the farm $farmnamehas been deleted.";
		my $message = "Resource removed";
		my $body = {
					 description => $description,
					 success     => "true",
					 message     => $message,
		};

		&httpResponse( { code => 200, body => $body } );
	}
	else
	{
		&zenlog(
			"Error trying to delete the resource $resource in zone $zone in farm $farmname, it's not possible to delete the resource.",
			"error", "GSLB"
		);

		# Error
		my $errormsg =
		  "It's not possible to delete the resource with id $resource in the zone $zone of the farm $farmname.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse( { code => 400, body => $body } );
	}
}

1;
