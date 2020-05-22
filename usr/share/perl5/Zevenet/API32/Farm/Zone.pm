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

use Zevenet::API32::HTTP;

# POST

# POST /farms/<farmname>/zones Create a new zone in a gslb Farm
sub new_farm_zone    # ( $json_obj, $farmname )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $farmname = shift;

	my $desc = "New zone";
	my $zone = $json_obj->{ id };

	# Check that the farm exists
	require Zevenet::Farm::Core;

	if ( !&getFarmExists( $farmname ) )
	{
		my $msg = "The farmname $farmname does not exist.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	if ( !&getValidFormat( 'zone', $json_obj->{ id } ) )
	{
		&zenlog(
			"Wrong zone name. The name has to be like zonename.com, zonename.net, etc. The zone $zone can't be created",
			"error", "GSLB"
		);

		my $msg =
		  "Invalid zone name, please insert a valid value like zonename.com, zonename.net, etc. The zone $zone can't be created.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

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

	# validate FARM NAME
	if ( !&getFarmExists( $farmname ) )
	{
		my $msg = "The farmname $farmname does not exist.";
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

	# validate RESOURCE NAME
	unless (    $json_obj->{ rname }
			 && &getValidFormat( 'resource_name', $json_obj->{ rname } ) )
	{
		my $msg =
		  "The parameter zone resource name (rname) doesn't exist, please insert a valid value.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# validate RESOURCE TTL
	$json_obj->{ ttl } = $default_ttl if !exists $json_obj->{ ttl };

	unless (
			 $json_obj->{ ttl } eq ''
			 || (    &getValidFormat( 'resource_ttl', $json_obj->{ ttl } )
				  && $json_obj->{ ttl } != 0 )
	  )    # (1second-1year)
	{
		my $msg =
		  "The parameter time to live value (ttl) doesn't exist, please insert a valid value.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# validate RESOURCE TYPE
	unless ( &getValidFormat( 'resource_type', $json_obj->{ type } ) )
	{
		my $msg =
		  "The parameter DNS record type (type) doesn't exist, please insert a valid value.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# validate RESOURCE DATA
	include 'Zevenet::Farm::GSLB::Service';

	unless (
		 !grep ( /$json_obj->{ rdata }/,
				 &getGSLBFarmServices( $farmname ) && $json_obj->{ type } eq 'DYNA' )
		 && &getValidFormat( "resource_data_$json_obj->{ type }", $json_obj->{ rdata } )
	  )
	{
		my $log_msg = "If you choose $json_obj->{ type } type, ";
		$log_msg .= "RDATA must be a valid IPv4 address,"
		  if ( $json_obj->{ type } eq "A" );
		$log_msg .= "RDATA must be a valid IPv6 address,"
		  if ( $json_obj->{ type } eq "AAAA" );
		$log_msg .= "RDATA format is not valid," if ( $json_obj->{ type } eq "NS" );
		$log_msg .= "RDATA must be a valid format ( foo.bar.com ),"
		  if ( $json_obj->{ type } eq "CNAME" );
		$log_msg .= "RDATA must be a valid service,"
		  if ( $json_obj->{ type } eq 'DYNA' );
		$log_msg .= "RDATA must be a valid format ( mail.example.com ),"
		  if ( $json_obj->{ type } eq 'MX' );
		$log_msg .= "RDATA must be a valid format ( 10 60 5060 host.example.com ),"
		  if ( $json_obj->{ type } eq 'SRV' );
		$log_msg .= "RDATA must be a valid format ( foo.bar.com ),"
		  if ( $json_obj->{ type } eq 'PTR' );

		# TXT and NAPTR input let all characters
		$log_msg .= " $json_obj->{ rname } not added to zone $zone";

		my $msg =
		  "The parameter zone resource server (rdata) doesn't correct format, please insert a valid value.";
		return
		  &httpErrorResponse(
							  code    => 400,
							  desc    => $desc,
							  msg     => $msg,
							  log_msg => $log_msg
		  );
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
	my $error;

	require Zevenet::Farm::Core;

	# validate FARM NAME
	if ( !&getFarmExists( $farmname ) )
	{
		my $msg = "The farmname $farmname does not exist.";
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

	# validate RESOURCE
	unless ( defined $res_aref->[$id_resource] )
	{
		my $msg = "Could not find the requested resource.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	# read resource
	my $resource = $res_aref->[$id_resource];
	my $rsc = {
				name => $resource->{ rname },
				ttl  => $resource->{ ttl },
				type => $resource->{ type },
				data => $resource->{ rdata },
				id   => $resource->{ id },
	};

	# Functions
	if ( exists ( $json_obj->{ rname } ) )
	{
		if ( !&getValidFormat( 'resource_name', $json_obj->{ rname } ) )
		{
			my $msg = "Invalid rname.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}

		$rsc->{ name } = $json_obj->{ rname };
	}

	if ( exists ( $json_obj->{ ttl } ) )
	{
		unless ( !defined $json_obj->{ ttl }
				 || (    &getValidFormat( 'resource_ttl', $json_obj->{ ttl } )
					  && $json_obj->{ ttl } ) )
		{
			my $msg = "Invalid ttl.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}

		$rsc->{ ttl } = $json_obj->{ ttl } // '';
	}

	my $auxType = $rsc->{ type };
	my $auxData = $rsc->{ data };

	if ( exists ( $json_obj->{ type } ) )
	{
		unless ( &getValidFormat( 'resource_type', $json_obj->{ type } ) )
		{
			my $msg = "Invalid type.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}

		$auxType = $json_obj->{ type };
	}

	if ( exists ( $json_obj->{ rdata } ) )
	{
		$auxData = $json_obj->{ rdata };
	}

	# validate RESOURCE DATA
	include 'Zevenet::Farm::GSLB::Service';

	unless (
		   !grep ( /$auxData/, &getGSLBFarmServices( $farmname ) && $auxType eq 'DYNA' )
		   && &getValidFormat( "resource_data_$auxType", $auxData ) )
	{
		my $msg = "If you choose $auxType type, ";
		$msg .= "RDATA must be a valid IPv4 address," if ( $auxType eq "A" );
		$msg .= "RDATA must be a valid IPv6 address," if ( $auxType eq "AAAA" );
		$msg .= "RDATA format is not valid,"          if ( $auxType eq "NS" );
		$msg .= "RDATA must be a valid format ( foo.bar.com ),"
		  if ( $auxType eq "CNAME" );
		$msg .= "RDATA must be a valid service," if ( $auxType eq 'DYNA' );
		$msg .= "RDATA must be a valid format ( mail.example.com ),"
		  if ( $auxType eq 'MX' );
		$msg .= "RDATA must be a valid format ( 10 60 5060 host.example.com ),"
		  if ( $auxType eq 'SRV' );
		$msg .= "RDATA must be a valid format ( foo.bar.com ),"
		  if ( $auxType eq 'PTR' );

		# TXT and NAPTR input let all characters

		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
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
			my $msg =
			  "It's not possible to modify the resource $id_resource in zone $zone.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}
		elsif ( $status == -2 )
		{
			my $msg = "The resource with ID $id_resource does not exist.";
			return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
		}
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
	my $error;

	require Zevenet::Farm::Core;

	# Check that the farm exists
	if ( !&getFarmExists( $farmname ) )
	{
		my $msg = "The farmname $farmname does not exist.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	$error = "false";

	# Functions
	if ( $json_obj->{ defnamesv } =~ /^$/ )
	{
		my $msg = "Invalid defnamesv, can't be blank.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	if ( $error eq "false" )
	{
		require Zevenet::Farm::Config;

		my $status = &setFarmVS( $farmname, $zone, "ns", $json_obj->{ defnamesv } );
		if ( $status )
		{
			my $msg = "It's not possible to modify the zone $zone.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}

		include 'Zevenet::Farm::GSLB::Config';
		&runGSLBFarmReload( $farmname );
	}

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
		my $msg = "The farmname $farmname does not exist.";
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
		my $msg = "The farmname $farmname does not exist.";
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
	unless ( defined $res_aref->[$resource] )
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
