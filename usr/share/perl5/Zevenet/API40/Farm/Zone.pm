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

use Zevenet::API40::HTTP;

# POST

# POST /farms/<farmname>/zones Create a new zone in a gslb Farm
sub new_farm_zone    # ( $json_obj, $farmname )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $farmname = shift;

	my $desc = "New zone";

	# Check that the farm exists
	require Zevenet::Farm::Core;

	if ( !&getFarmExists( $farmname ) )
	{
		my $msg = "The farmname $farmname does not exists.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $params = {
		"id" => {
			'valid_format' => 'zone',
			'non_blank'    => 'true',
			'required'     => 'true',
			'format_msg' =>
			  'Invalid zone name, please insert a valid value like zonename.com, zonename.net, etc.',
		},
	};

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	include 'Zevenet::Farm::GSLB::Zone';

	my $result = &setGSLBFarmNewZone( $farmname, $json_obj->{ id } );

	# check for errors adding the new zone
	if ( $result != 0 )
	{
		my $msg = "It's not possible to create the zone " . $json_obj->{ id };
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	&zenlog(
		"Success, a new zone has been created in farm $farmname with id $json_obj->{id}.",
		"info", "GSLB"
	);

	if ( &getFarmStatus( $farmname ) eq 'up' )
	{
		include 'Zevenet::Farm::GSLB::Config';
		include 'Zevenet::Cluster';

		&runGSLBFarmReload( $farmname );
		&runZClusterRemoteManager( 'farm', 'restart', $farmname );
	}

	my $body = {
				 description => "New zone " . $json_obj->{ id },
				 params      => { id => $json_obj->{ id } },
	};

	return &httpResponse( { code => 201, body => $body } );
}

# POST /farms/<farmname>/zoneresources Create a new resource of a zone in a gslb Farm
sub new_farm_zone_resource    # ( $json_obj, $farmname, $zone )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $farmname = shift;
	my $zone     = shift;

	require Zevenet::Farm::Core;
	include 'Zevenet::Farm::GSLB::Zone';

	my $desc        = "New zone resource";
	my $default_ttl = '';

	my $rdata_msg =
	  "A resource of type $json_obj->{ type } requires as RDATA a valid ";
	$rdata_msg .= "IPv4 address"
	  if ( $json_obj->{ type } eq "A" );
	$rdata_msg .= "IPv6 address"
	  if ( $json_obj->{ type } eq "AAAA" );
	$rdata_msg .= "name server"
	  if ( $json_obj->{ type } eq "NS" );
	$rdata_msg .= "format ( foo.bar.com ),"
	  if ( $json_obj->{ type } eq "CNAME" );
	$rdata_msg .= "service"
	  if ( $json_obj->{ type } eq 'DYNA' );
	$rdata_msg .= "format ( mail.example.com )"
	  if ( $json_obj->{ type } eq 'MX' );
	$rdata_msg .= "format ( 10 60 5060 host.example.com )"
	  if ( $json_obj->{ type } eq 'SRV' );
	$rdata_msg .= "format ( foo.bar.com )"
	  if ( $json_obj->{ type } eq 'PTR' );

	my $params = {
				   "rname" => {
								'valid_format' => 'resource_name',
								'non_blank'    => 'true',
								'required'     => 'true',
				   },
				   "ttl" => {
							  'valid_format' => 'resource_ttl',
				   },
				   "type" => {
							   'valid_format' => 'resource_type',
							   'values' => [qw(NS A AAAA CNAME DYNA MX SRV TXT PTR NAPTR)],
							   'required'  => 'true',
							   'non_blank' => 'true',
				   },
				   "rdata" => {
								'required'  => 'true',
								'non_blank' => 'true',
				   },
	};

	# validate FARM NAME
	if ( !&getFarmExists( $farmname ) )
	{
		my $msg = "The farmname $farmname does not exists.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	# validate FARM TYPE
	unless ( &getFarmType( $farmname ) eq 'gslb' )
	{
		my $msg = "Only GSLB profile is supported for this request.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# validate ZONE
	unless ( grep { $_ eq $zone } &getGSLBFarmZones( $farmname ) )
	{
		my $msg = "Could not find the requested zone.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	# evaluate it after of type, because this struct depend on type parameter
	unless (
		  &getValidFormat( "resource_data_$json_obj->{ type }", $json_obj->{ rdata } ) )
	{
		return &httpErrorResponse( code => 400, desc => $desc, msg => $rdata_msg );
	}

	# validate RESOURCE TTL
	$json_obj->{ ttl } = $default_ttl if !exists $json_obj->{ ttl };

	# validate RESOURCE DATA
	include 'Zevenet::Farm::GSLB::Service';

	if ( exists $json_obj->{ type } && $json_obj->{ type } eq 'DYNA' )
	{
		unless ( grep ( /^$json_obj->{ rdata }$/, &getGSLBFarmServices( $farmname ) ) )
		{
			my $msg = "The service $json_obj->{ rdata } has not been found";
			return
			  &httpErrorResponse(
								  code => 404,
								  desc => $desc,
								  msg  => $msg,
			  );
		}
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

	if ( $status == -1 )
	{
		my $msg =
		  "It's not possible to create a new resource in the zone $zone in farm $farmname.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	require Zevenet::Farm::Base;

	&zenlog(
			"Success, a new resource has been created in zone $zone in farm $farmname.",
			"info", "GSLB" );

	if ( &getFarmStatus( $farmname ) eq 'up' )
	{
		include 'Zevenet::Farm::GSLB::Config';
		include 'Zevenet::Cluster';

		&runGSLBFarmReload( $farmname );
		&runZClusterRemoteManager( 'farm', 'restart', $farmname );
	}

	$json_obj->{ ttl } = undef if !$json_obj->{ ttl };

	my $message = "Resource added";
	my $body = {
				 description => $desc,
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

	return &httpResponse( { code => 201, body => $body } );
}

# GET

#	/farms/<GSLBfarm>/zones/<zone>/resources
sub gslb_zone_resources    # ( $farmname, $zone )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $farmname = shift;
	my $zone     = shift;

	my $desc = "List zone resources";

	require Zevenet::Farm::Core;

	# validate FARM NAME
	if ( !&getFarmExists( $farmname ) )
	{
		my $msg = "Farm name not found";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	# validate FARM TYPE
	if ( &getFarmType( $farmname ) ne 'gslb' )
	{
		my $msg = "Only GSLB profile is supported for this request.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# validate ZONE
	include 'Zevenet::Farm::GSLB::Zone';

	if ( !scalar grep { $_ eq $zone } &getGSLBFarmZones( $farmname ) )
	{
		my $msg = "Could not find the requested zone.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
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

	my $body = {
				 description => $desc,
				 params      => $resources,
	};

	return &httpResponse( { code => 200, body => $body } );
}

# PUT

sub modify_zone_resource    # ( $json_obj, $farmname, $zone, $id_resource )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $json_obj, $farmname, $zone, $id_resource ) = @_;

	my $desc = "Modify zone resource";

	require Zevenet::Farm::Core;

	my $rdata_msg =
	  "A resource of type $json_obj->{ type } requires as RDATA a valid ";
	$rdata_msg .= "IPv4 address"
	  if ( $json_obj->{ type } eq "A" );
	$rdata_msg .= "IPv6 address"
	  if ( $json_obj->{ type } eq "AAAA" );
	$rdata_msg .= "name server"
	  if ( $json_obj->{ type } eq "NS" );
	$rdata_msg .= "format ( foo.bar.com ),"
	  if ( $json_obj->{ type } eq "CNAME" );
	$rdata_msg .= "service"
	  if ( $json_obj->{ type } eq 'DYNA' );
	$rdata_msg .= "format ( mail.example.com )"
	  if ( $json_obj->{ type } eq 'MX' );
	$rdata_msg .= "format ( 10 60 5060 host.example.com )"
	  if ( $json_obj->{ type } eq 'SRV' );
	$rdata_msg .= "format ( foo.bar.com )"
	  if ( $json_obj->{ type } eq 'PTR' );

	my $params = {
		"rname" => {
					 'valid_format' => 'resource_name',
					 'non_blank'    => 'true',
		},
		"ttl" => {
				   'valid_format' => 'resource_ttl',
		},
		"type" => {
			'valid_format' => 'resource_type',
			'non_blank'    => 'true',
			'values'       => [qw(NS A AAAA CNAME DYNA MX SRV TXT PTR NAPTR)],

		},
		"rdata" => {
					 'non_blank' => 'true',
		},
	};

	# validate FARM NAME
	if ( !&getFarmExists( $farmname ) )
	{
		my $msg = "The farmname $farmname does not exists.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	# validate FARM TYPE
	if ( &getFarmType( $farmname ) ne 'gslb' )
	{
		my $msg = "Only GSLB profile is supported for this request.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# validate ZONE
	include 'Zevenet::Farm::GSLB::Zone';
	unless ( grep { $_ eq $zone } &getGSLBFarmZones( $farmname ) )
	{
		my $msg = "Could not find the requested zone.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $res_aref = &getGSLBResources( $farmname, $zone );

	# read resource
	my $resource;
	my $rsc;
	my $resource_orig;
	my $i;

	for ( $i = 0 ; $i <= $#$res_aref ; $i++ )
	{
		if ( $res_aref->[$i]->{ id } eq $id_resource )
		{
			$resource      = $res_aref->[$i];
			$resource_orig = $resource;
		}
	}

	$rsc->{ rname } = $json_obj->{ rname } // $resource->{ rname };
	$rsc->{ ttl }   = $json_obj->{ ttl }   // $resource->{ ttl };
	$rsc->{ type }  = $json_obj->{ type }  // $resource->{ type };
	$rsc->{ rdata } = $json_obj->{ rdata } // $resource->{ rdata };

	# validate RESOURCE
	unless ( defined $resource )
	{
		my $msg = "Could not find the requested resource.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	# validate RESOURCE DATA
	include 'Zevenet::Farm::GSLB::Service';

	# evaluate it after of type, because this struct depend on type parameter
	if ( exists $json_obj->{ rdata } or exists $json_obj->{ type } )
	{
		unless ( &getValidFormat( "resource_data_$rsc->{ type }", $rsc->{ rdata } ) )
		{
			return &httpErrorResponse( code => 400, desc => $desc, msg => $rdata_msg );
		}

		if ( !grep ( /^$resource_orig->{ rdata }$/, &getGSLBFarmServices( $farmname ) )
			 && $resource_orig->{ type } eq "DYNA" )
		{
			my $msg = "The service $resource_orig->{ rdata } has not been found";
			return
			  &httpErrorResponse(
								  code => 404,
								  desc => $desc,
								  msg  => $msg,
			  );
		}
	}

	my $status = &setGSLBFarmZoneResource(
										   $id_resource,
										   $rsc->{ rname },
										   $rsc->{ ttl },
										   $rsc->{ type },
										   $rsc->{ rdata },
										   $farmname,
										   $zone,
	);

	if ( $status == -1 )
	{
		my $msg =
		  "It's not possible to modify the resource $id_resource in zone $zone.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}
	elsif ( $status == -2 )
	{
		my $msg = "The resource with ID $id_resource does not exist.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	&zenlog(
		"Success, some parameters have been changed in the resource $id_resource in zone $zone in farm $farmname.",
		"info", "GSLB"
	);

	my $message = "Resource modified";
	my $body = {
				 description => $desc,
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

	return &httpResponse( { code => 200, body => $body } );
}

sub modify_zones    # ( $json_obj, $farmname, $zone )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $json_obj, $farmname, $zone ) = @_;

	my $desc = "Modify zone";

	require Zevenet::Farm::Core;

	# Check that the farm exists
	if ( !&getFarmExists( $farmname ) )
	{
		my $msg = "The farmname $farmname does not exists.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $params = {
				   "defnamesv" => {
									'non_blank' => 'true',
									'required'  => 'true',
				   },
	};

	# Check allowed parameters
	my $error_msg = &checkZAPIParams( $json_obj, $params, $desc );
	return &httpErrorResponse( code => 400, desc => $desc, msg => $error_msg )
	  if ( $error_msg );

	require Zevenet::Farm::Config;

	my $status = &setFarmVS( $farmname, $zone, "ns", $json_obj->{ defnamesv } );
	if ( $status )
	{
		my $msg = "It's not possible to modify the zone $zone.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	include 'Zevenet::Farm::GSLB::Config';
	&runGSLBFarmReload( $farmname );

	&zenlog(
		 "Success, some parameters have been changed  in zone $zone in farm $farmname.",
		 "info", "GSLB"
	);

	my $body = {
				 description => $desc,
				 params      => $json_obj,
	};

	return &httpResponse( { code => 200, body => $body } );
}

# DELETE

# DELETE /farms/<farmname>/zones/<zonename> Delete a zone of a  gslb Farm
sub delete_zone    # ( $farmname, $zone )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farmname, $zone ) = @_;

	require Zevenet::Farm::Core;
	include 'Zevenet::Farm::GSLB::Zone';

	my $desc = "Delete zone";

	# Check that the farm exists
	if ( !&getFarmExists( $farmname ) )
	{
		my $msg = "The farmname $farmname does not exists.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	&setGSLBFarmDeleteZone( $farmname, $zone );

	if ( $? != 0 )
	{
		my $msg = "Zone $zone in farm $farmname hasn't been deleted.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	&zenlog( "Success, the zone $zone in farm $farmname has been deleted.",
			 "info", "GSLB" );

	require Zevenet::Farm::Base;

	if ( &getFarmStatus( $farmname ) eq 'up' )
	{
		include 'Zevenet::Farm::GSLB::Config';
		include 'Zevenet::Cluster';

		&runGSLBFarmReload( $farmname );
		&runZClusterRemoteManager( 'farm', 'restart', $farmname );
	}

	my $message = "The zone $zone in farm $farmname has been deleted.";
	my $body = {
				 description => $desc,
				 success     => "true",
				 message     => $message
	};

	return &httpResponse( { code => 200, body => $body } );
}

#  @api {delete} /farms/<farmname>/zones/<zonename>/resources/<resourceid> Delete a resource of a Zone
sub delete_zone_resource    # ( $farmname, $zone, $resource )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farmname, $zone, $resource ) = @_;

	require Zevenet::Farm::Core;

	my $desc = "Delete zone resource";

	# validate FARM NAME
	if ( !&getFarmExists( $farmname ) )
	{
		my $msg = "The farmname $farmname does not exists.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	# validate FARM TYPE
	if ( &getFarmType( $farmname ) ne 'gslb' )
	{
		my $msg = "Only GSLB profile is supported for this request.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# validate ZONE
	include 'Zevenet::Farm::GSLB::Zone';

	if ( !scalar grep { $_ eq $zone } &getGSLBFarmZones( $farmname ) )
	{
		my $msg = "Invalid zone name, please insert a valid value.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $res_aref = &getGSLBResources( $farmname, $zone );

	# validate RESOURCE
	unless ( defined $resource )
	{
		my $msg = "Could not find the requested resource.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $status = &remGSLBFarmZoneResource( $resource, $farmname, $zone );

	if ( $status == -1 )
	{
		my $msg =
		  "It's not possible to delete the resource with id $resource in the zone $zone of the farm $farmname.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	&zenlog(
		"Success, the resource $resource in zone $zone in farm $farmname has been deleted.",
		"info", "GSLB"
	);

	require Zevenet::Farm::Base;

	if ( &getFarmStatus( $farmname ) eq 'up' )
	{
		include 'Zevenet::Farm::GSLB::Config';
		include 'Zevenet::Cluster';

		&runGSLBFarmReload( $farmname );
		&runZClusterRemoteManager( 'farm', 'restart', $farmname );
	}

	my $message = "Resource removed";
	my $body = {
				 description => $desc,
				 success     => "true",
				 message     => $message,
	};

	return &httpResponse( { code => 200, body => $body } );
}

1;
