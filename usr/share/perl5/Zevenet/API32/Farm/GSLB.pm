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

use Zevenet::Farm::Core;

# GET /farms/modules/gslb
sub farms_gslb    # ()
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	require Zevenet::Farm::Base;

	my @out;
	my @files = &getFarmList();

	foreach my $file ( @files )
	{
		my $name = &getFarmName( $file );
		my $type = &getFarmType( $name );
		next unless $type eq 'gslb';
		my $status = &getFarmVipStatus( $name );
		my $vip    = &getFarmVip( 'vip', $name );
		my $port   = &getFarmVip( 'vipp', $name );

		require Zevenet::Farm::Action;
		$status = "needed restart"
		  if $status ne 'down' && &getFarmRestartStatus( $name );

		push @out,
		  {
			farmname => $name,
			status   => $status,
			vip      => $vip,
			vport    => $port
		  };
	}

	include 'Zevenet::RBAC::Group::Core';
	@out = @{ &getRBACUserSet( 'farms', \@out ) };

	my $body = {
				 description => "List GSLB farms",
				 params      => \@out,
	};

	return &httpResponse( { code => 200, body => $body } );
}

## Services

# POST /farms/<farmname>/services/<servicename>
sub new_gslb_farm_service    # ( $json_obj, $farmname )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $farmname = shift;

	require Zevenet::Farm::Base;
	include 'Zevenet::Farm::GSLB::Service';

	my $desc = "New service";

	# check if there is a service name
	if ( !&getValidFormat( 'gslb_service', $json_obj->{ id } ) )
	{
		my $msg = "Error, the service name has a invalid format.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# check if there is a service algorithm
	if ( $json_obj->{ algorithm } eq '' )
	{
		my $msg = "Invalid algorithm, please insert a valid value.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $status = &setGSLBFarmNewService( $farmname,
										 $json_obj->{ id },
										 $json_obj->{ algorithm } );

	# check if there was an error creating the new service
	if ( $status == -1 )
	{
		my $msg = "It's not possible to create the service " . $json_obj->{ id };
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# no error found, return a succesful response
	&zenlog(
		"Success, a new service has been created in farm $farmname with id $json_obj->{id}.",
		"info", "GSLB"
	);

	my $body = {
				 description => "New service " . $json_obj->{ id },
				 params      => {
							 id        => $json_obj->{ id },
							 algorithm => $json_obj->{ algorithm }
				 },
	};

	if ( &getFarmStatus( $farmname ) ne 'down' )
	{
		require Zevenet::Farm::Action;

		&setFarmRestart( $farmname );
		$body->{ status } = 'needed restart';
	}

	return &httpResponse( { code => 201, body => $body } );
}

# PUT /farms/<farmname>/services/<servicename>
sub modify_gslb_service    # ( $json_obj, $farmname, $service )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $json_obj, $farmname, $service ) = @_;

	include 'Zevenet::Farm::GSLB::Config';
	include 'Zevenet::Farm::GSLB::FarmGuardian';
	include 'Zevenet::Farm::GSLB::Service';
	require Zevenet::Farm::Config;
	require Zevenet::Farm::Base;

	my $output_params;
	my $desc = "Modify service";

	# check deftcpport parameter is not empty
	if ( $json_obj->{ deftcpport } eq '' )
	{
		my $msg = "Invalid deftcpport value, can't be blank.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# change to number format
	$json_obj->{ deftcpport } += 0;

	my $old_deftcpport = &getGSLBFarmVS( $farmname, $service, 'dpc' );
	&setFarmVS( $farmname, $service, "dpc", $json_obj->{ deftcpport } );

	# Update farmguardian
	my ( $fgTime, $fgScript ) = &getGSLBFarmGuardianParams( $farmname, $service );
	my $error;

	# Changing farm guardian port check
	if ( $fgScript =~ s/-p $old_deftcpport/-p $json_obj->{ deftcpport }/ )
	{
		$error = &setGSLBFarmGuardianParams( $farmname, $service, 'cmd', $fgScript );
	}

	# check if setting FG params failed
	if ( $error )
	{
		my $msg = "Could not change the deftcpport parameter.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	&runGSLBFarmReload( $farmname );

	# FIXME: Read gslb configuration instead of returning input
	$output_params = $json_obj;

	# no errors found, return succesful response
	&zenlog(
		"Success, some parameters have been changed in service $service in farm $farmname.",
		"info", "GSLB"
	);

	my $body = {
				 description => "Modify service $service in farm $farmname",
				 params      => $output_params,
	};

	if ( &getFarmStatus( $farmname ) ne 'down' )
	{
		require Zevenet::Farm::Action;

		&setFarmRestart( $farmname );
		$body->{ status } = 'needed restart';
		$body->{ info } =
		  "There're changes that need to be applied, stop and start farm to apply them!";
	}

	return &httpResponse( { code => 200, body => $body } );
}

# DELETE /farms/<farmname>/services/<servicename>
sub delete_gslb_service    # ( $farmname, $service )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farmname, $service ) = @_;

	require Zevenet::Farm::Base;
	include 'Zevenet::Farm::GSLB::Service';

	my $desc     = "Delete service in GSLB farm";
	my @services = &getGSLBFarmServices( $farmname );
	my $found    = 0;

	# validate SERVICE
	foreach my $farmservice ( @services )
	{
		#print "service: $farmservice";
		if ( $service eq $farmservice )
		{
			$found = 1;
			last;
		}
	}

	# Check if the service exists
	unless ( $found )
	{
		my $msg = "Invalid service name, please insert a valid value.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	my $error = &setGSLBFarmDeleteService( $farmname, $service );

	# check if the service is being used
	if ( $error == -2 )
	{
		my $msg =
		  "The service $service in farm $farmname hasn't been deleted. The service is used by a zone.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# check if the service could not be deleted
	if ( $error )
	{
		my $msg = "Service $service in farm $farmname hasn't been deleted.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# no error found, return succesful response
	&zenlog( "Success, the service $service in farm $farmname has been deleted.",
			 "info", "GSLB" );

	my $msg = "The service $service in farm $farmname has been deleted.";
	my $body = {
				 description => "Delete service $service in farm $farmname.",
				 success     => "true",
				 message     => $msg,
	};

	if ( &getFarmStatus( $farmname ) ne 'down' )
	{
		require Zevenet::Farm::Action;

		$body->{ status } = "needed restart";
		&setFarmRestart( $farmname );
	}

	return &httpResponse( { code => 200, body => $body } );
}

## Backends

# POST /farms/<farmname>/services/<servicename>/backends
sub new_gslb_service_backend    # ( $json_obj, $farmname, $service )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $farmname = shift;
	my $service  = shift;

	require Zevenet::Net::Validate;
	require Zevenet::Farm::Base;
	require Zevenet::Farm::Config;
	include 'Zevenet::Farm::GSLB::Service';
	include 'Zevenet::Farm::GSLB::Backend';

	my $desc          = "New service backend";
	my @services_list = &getGSLBFarmServices( $farmname );

	# check if the SERVICE exists
	unless ( grep { $service eq $_ } @services_list )
	{
		my $msg = "Could not find the requested service.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $lb = &getFarmVS( $farmname, $service, "algorithm" );

	# validate supported ALGORITHM
	unless ( $lb eq 'roundrobin' )
	{
		my $msg = "This service algorithm does not support adding new backends.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# Get an ID for the new backend
	my $id = &getGSLBFarmServiceBackendAvailableID( $farmname, $service );

	# validate IP
	unless ( &getValidFormat( 'ip_addr', $json_obj->{ ip } ) )
	{
		my $msg = "Invalid IP address.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# Get a backend IP
	my @be = @{ &getGSLBFarmBackends( $farmname, $service ) };

	my $be_ip = 0;
	$be_ip = $be[0]->{ ip } if @be && exists $be[0]->{ ip };

	# match ip stack version
	unless ( !@be || &ipversion( $json_obj->{ ip } ) eq &ipversion( $be_ip ) )
	{
		my $msg = "Invalid IP version.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# Adding the backend
	my $status =
	  &setGSLBFarmNewBackend( $farmname, $service, $lb, $id, $json_obj->{ ip } );

	# check if adding the new backend failed
	if ( $status == -1 )
	{
		my $msg =
		  "It's not possible to create the backend $json_obj->{ ip } for the service $service.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# no error found, return successful response
	&zenlog(
		"Success, a new backend has been created in farm $farmname in service $service with IP $json_obj->{ip}.",
		"info", "GSLB"
	);

	my $message = "Added backend to service successfully";
	my $body = {
				 description => $desc,
				 params      => {
							 id => $id,
							 ip => $json_obj->{ ip },
				 },
				 message => $message,
	};

	if ( &getFarmStatus( $farmname ) ne 'down' )
	{
		require Zevenet::Farm::Action;

		&setFarmRestart( $farmname );
		$body->{ status } = 'needed restart';
	}

	return &httpResponse( { code => 201, body => $body } );
}

# GET /farms/<name>/services/<service>/backends
sub list_gslb_service_backends
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farmname, $service ) = @_;

	require Zevenet::Farm::Config;
	include 'Zevenet::Farm::GSLB::Service';

	my $desc          = "List service backends";
	my $type          = &getFarmType( $farmname );
	my @services_list = &getGSLBFarmServices( $farmname );
	my @backends;    # output

	# check if the service exists
	unless ( grep { $service eq $_ } @services_list )
	{
		my $msg = "The service $service does not exist.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $backends = &eload(
						   module => 'Zevenet::Farm::GSLB::Backend',
						   func   => 'getGSLBFarmBackends',
						   args   => [$farmname, $service],
	);
	my $body = {
				 description => $desc,
				 params      => $backends,
	};

	return &httpResponse( { code => 200, body => $body } );
}

# PUT /farms/<farmname>/services/<servicename>/backends/<backendid>
sub modify_gslb_service_backends #( $json_obj, $farmname, $service, $id_server )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $json_obj, $farmname, $service, $id_server ) = @_;

	require Zevenet::Farm::Action;
	require Zevenet::Farm::Config;
	include 'Zevenet::Farm::GSLB::Service';
	include 'Zevenet::Farm::GSLB::Backend';

	my $desc     = "Modify service backend";
	my @services = &getGSLBFarmServices( $farmname );

	# check if the SERVICE exists
	unless ( grep { $service eq $_ } @services )
	{
		my $msg = "Could not find the requested service.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	# get requested backend info
	my $be_aref = &getGSLBFarmBackends( $farmname, $service );
	my $be = $be_aref->[$id_server - 1];

	# check if the BACKEND exists
	if ( !$be )
	{
		my $msg = "Could not find a service backend with such id.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $lb = &getFarmVS( $farmname, $service, "algorithm" );

	# validate BACKEND ip
	if ( exists ( $json_obj->{ ip } ) )
	{
		unless (    $json_obj->{ ip }
				 && &getValidFormat( 'ip_addr', $json_obj->{ ip } ) )
		{
			my $msg = "Invalid IP address.";
			return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
		}

		$be->{ ip } = $json_obj->{ ip };
	}

	my $status =
	  &setGSLBFarmNewBackend( $farmname, $service, $lb, $id_server,
							  $json_obj->{ ip } );

	# check if there was an error modifying the backend
	if ( $status == -1 )
	{
		my $msg =
		  "It's not possible to modify the backend with IP $json_obj->{ip} in service $service.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# no error found, return successful response
	&setFarmRestart( $farmname );

	&zenlog(
		"Success, some parameters have been changed in the backend $id_server in service $service in farm $farmname.",
		"info", "GSLB"
	);

	# Check IP stack version
	require Zevenet::Net::Validate;

	my $service_stack;
	my $ipv_mismatch;

	my $be_aref = &getGSLBFarmBackends( $farmname, $service );

	# check every backend ip version
	foreach my $be ( @{ $be_aref } )
	{
		my $current_stack = &ipversion( $be->{ ip } );

		if ( !$service_stack )
		{
			$service_stack = $current_stack;
		}
		else
		{
			$ipv_mismatch = $current_stack ne $service_stack;
		}

		last if $ipv_mismatch;
	}

	# Get farm status. If farm is down the restart is not required.
	my $msg = "Backend modified";
	$msg .= ". IPv4 and IPv6 addresses on the same service are not supported."
	  if $ipv_mismatch;

	my $body = {
				 description => $desc,
				 params      => $json_obj,
				 message     => $msg,
	};

	if ( &getFarmStatus( $farmname ) ne 'down' )
	{
		$body->{ status } = 'needed restart';
		$body->{ info } =
		  "There're changes that need to be applied, stop and start farm to apply them!";
	}

	return &httpResponse( { code => 200, body => $body } );
}

# DELETE /farms/<farmname>/services/<servicename>/backends/<backendid>
sub delete_gslb_service_backend    # ( $farmname, $service, $id_server )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farmname, $service, $id_server ) = @_;

	require Zevenet::Farm::Action;
	require Zevenet::Farm::Config;
	include 'Zevenet::Farm::GSLB::Service';
	include 'Zevenet::Farm::GSLB::Backend';

	my $desc     = "Delete service backend";
	my @services = &getGSLBFarmServices( $farmname );

	# check if the SERVICE exists
	unless ( grep { $service eq $_ } @services )
	{
		my $msg = "Could not find the requested service.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	# validate ALGORITHM
	if ( &getFarmVS( $farmname, $service, "algorithm" ) eq 'prio' )
	{
		my $msg = "This service algorithm does not support removing backends.";
		return &httpErrorResponse( code => 400, desc => $desc, msg => $msg );
	}

	# check if the backend id is available
	my $be_aref = &getGSLBFarmBackends( $farmname, $service );

	require Zevenet::Farm::Backend;
	my $be_found = &getFarmServer( $be_aref, $id_server );

	unless ( $be_found )
	{
		my $msg = "Could not find the requested backend.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	# the farm has to have one backend at least
	if ( @{ $be_aref } < 2 )
	{
		my $msg = "The service has to have one backend at least.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	my $status = &remFarmServiceBackend( $id_server, $farmname, $service );

	# check if there was an error removing the backend
	if ( $status == -1 )
	{
		&zenlog( "It's not possible to delete the backend.", "warning", "GSLB" );

		my $msg =
		  "Could not find the backend with ID $id_server of the $farmname farm.";
		return &httpErrorResponse( code => 404, desc => $desc, msg => $msg );
	}

	# no error found, return successful response
	&zenlog(
		"Success, the backend $id_server in service $service in farm $farmname has been deleted.",
		"info", "GSLB"
	);

	&setFarmRestart( $farmname );

	my $message = "Backend removed";
	my $body = {
				 description => $desc,
				 success     => "true",
				 message     => $message,
	};

	if ( &getFarmStatus( $farmname ) ne 'down' )
	{
		$body->{ status } = "needed restart";
		&setFarmRestart( $farmname );
	}

	return &httpResponse( { code => 200, body => $body } );
}

1;
