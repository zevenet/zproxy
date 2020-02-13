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

use Zevenet::Farm::Core;

# POST

sub new_farm_backend    # ( $json_obj, $farmname )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $farmname = shift;

	require Zevenet::Farm::Backend;

	# Initial parameters
	my $description = "New farm backend";

	# validate FARM NAME
	if ( !&getFarmExists( $farmname ) )
	{
		# Error
		my $errormsg = "The farmname $farmname does not exists.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 404, body => $body } );
	}

	# validate FARM TYPE
	my $type = &getFarmType( $farmname );

	if ( $type eq "l4xnat" )
	{
		require Zevenet::Net::Validate;
		require Zevenet::Farm::L4xNAT::Backend;

		my $id = &getL4FarmBackendAvailableID( $farmname );

		# validate IP
		if ( !&getValidFormat( 'IPv4_addr', $json_obj->{ ip } ) )
		{
			&zenlog(
				"Error trying to create a new backend l4xnat in farm $farmname, invalid backend IP value.",
				"error", "LSLB"
			);

			# Error
			my $errormsg = "Invalid backend IP value, please insert a valid value.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 400, body => $body } );
		}

		# validate PORT
		unless (    &isValidPortNumber( $json_obj->{ port } ) eq 'true'
				 || $json_obj->{ port } eq '' )
		{
			&zenlog(
				"Error trying to create a new backend l4xnat in farm $farmname, invalid IP address and port for a backend, ir can't be blank.",
				"error", "LSLB"
			);

			# Error
			my $errormsg = "Invalid IP address and port for a backend, it can't be blank.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 400, body => $body } );
		}

		# validate PRIORITY
		if ( $json_obj->{ priority } !~ /^\d+$/
			 && exists $json_obj->{ priority } )    # (0-9)
		{
			# Error
			my $errormsg =
			  "Invalid backend priority value, please insert a value within the range 0-9.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 400, body => $body } );
		}

		# validate WEIGHT
		if ( $json_obj->{ weight } !~ /^[1-9]\d*$/
			 && exists $json_obj->{ weight } )    # 1 or higher
		{
			# Error
			my $errormsg =
			  "Invalid backend weight value, please insert a value greater than 0.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 400, body => $body } );
		}

		#validate MAX_CONNS
		$json_obj->{ max_conns } = 0 unless exists $json_obj->{ max_conns };

		if ( $json_obj->{ max_conns } !~ /^[0-9]+$/ )    # (0 or higher)
		{
			# Error
			my $errormsg =
			  "Invalid backend connection limit value, accepted values are 0 or higher.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 400, body => $body } );
		}

		# Create backend
		my $status = &setL4FarmServer(
									   $farmname,
									   $id,
									   $json_obj->{ ip },
									   $json_obj->{ port },
									   $json_obj->{ weight },
									   $json_obj->{ priority },
									   $json_obj->{ max_conns },
		);

		if ( $status != -1 )
		{
			&zenlog(
				"Success, a new backend has been created in farm $farmname with IP $json_obj->{ip}.",
				"info", "LSLB"
			);

			$json_obj->{ port }     += 0 if $json_obj->{ port };
			$json_obj->{ weight }   += 0 if $json_obj->{ weight };
			$json_obj->{ priority } += 0 if $json_obj->{ priority };

			# Success
			my $message = "Backend added";
			my $body = {
						 description => $description,
						 params      => {
									 id        => $id,
									 ip        => $json_obj->{ ip },
									 port      => $json_obj->{ port },
									 weight    => $json_obj->{ weight },
									 priority  => $json_obj->{ priority },
									 max_conns => $json_obj->{ max_conns },
						 },
						 message => $message,
			};

			include 'Zevenet::Cluster';
			&runZClusterRemoteManager( 'farm', 'restart', $farmname );

			&httpResponse( { code => 201, body => $body } );
		}
		else
		{
			# Error
			my $errormsg =
			    "It's not possible to create the backend with ip "
			  . $json_obj->{ ip }
			  . " and port "
			  . $json_obj->{ port }
			  . " for the $farmname farm";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 400, body => $body } );
		}
	}
	elsif ( $type eq "datalink" )
	{
		# get an ID
		require Zevenet::Farm::Datalink::Backend;

		my $id = &getDatalinkFarmBackendAvailableID( $farmname );

		# validate IP
		if ( !&getValidFormat( 'IPv4_addr', $json_obj->{ ip } ) )
		{
			&zenlog(
				"Error trying to create a new backend datalink in farm $farmname, invalid backend IP value.",
				"error", "DSLB"
			);

			# Error
			my $errormsg = "Invalid backend IP value, please insert a valid value.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 400, body => $body } );
		}

		# validate INTERFACE
		require Zevenet::Net::Interface;

		my $valid_interface;

		for my $iface ( @{ &getActiveInterfaceList() } )
		{
			next if $iface->{ vini };     # discard virtual interfaces
			next if !$iface->{ addr };    # discard interfaces without address

			if ( $iface->{ name } eq $json_obj->{ interface } )
			{
				$valid_interface = 'true';
			}
		}

		if ( !$valid_interface )
		{
			&zenlog(
				"Error trying to create a new backend in the farm $farmname, invalid interface.",
				"error", "NETWORK"
			);

			my $errormsg =
			  "Invalid interface value, please insert any non-virtual interface.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg,
			};

			&httpResponse( { code => 400, body => $body } );
		}

		# validate WEIGHT
		unless (    $json_obj->{ weight } =~ &getValidFormat( 'natural_num' )
				 || $json_obj->{ weight } == undef )    # 1 or higher or undef
		{
			&zenlog(
				  "Error trying to create a new backend in the farm $farmname, invalid weight.",
				  "error", "" );

			my $errormsg = "Invalid weight value, please insert a valid weight value.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg,
			};

			&httpResponse( { code => 400, body => $body } );
		}

		# validate PRIORITY
		unless (    $json_obj->{ priority } =~ /^[1-9]$/
				 || $json_obj->{ priority } == undef )    # (1-9)
		{
			&zenlog(
				"Error trying to create a new backend in the farm $farmname, invalid priority.",
				"error", ""
			);

			my $errormsg = "Invalid priority value, please insert a valid priority value.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg,
			};

			&httpResponse( { code => 400, body => $body } );
		}

		# Create backend
		my $status = &setDatalinkFarmServer(
											 $id,
											 $json_obj->{ ip },
											 $json_obj->{ interface },
											 $json_obj->{ weight },
											 $json_obj->{ priority },
											 $farmname,
		);

		if ( $status != -1 )
		{
			&zenlog(
				"Success, a new backend has been created in farm $farmname with IP $json_obj->{ip}.",
				"info", ""
			);

			# Success
			my $message = "Backend added";
			my $weight =
			  ( $json_obj->{ weight } ne '' ) ? $json_obj->{ weight } + 0 : undef;
			my $prio =
			  ( $json_obj->{ priority } ne '' ) ? $json_obj->{ priority } + 0 : undef;

			my $body = {
						 description => $description,
						 params      => {
									 id        => $id,
									 ip        => $json_obj->{ ip },
									 interface => $json_obj->{ interface },
									 weight    => $weight,
									 priority  => $prio,
						 },
						 message => $message,
			};

			include 'Zevenet::Cluster';
			&runZClusterRemoteManager( 'farm', 'restart', $farmname );

			&httpResponse( { code => 201, body => $body } );
		}
		else
		{
			&zenlog(
				"Error trying to create a new backend datalink in farm $farmname, it's not possible to create the backend.",
				"error", "DSLB"
			);

			# Error
			my $errormsg =
			    "It's not possible to create the backend with ip "
			  . $json_obj->{ ip }
			  . " and port "
			  . $json_obj->{ port }
			  . " for the $farmname farm";

			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 400, body => $body } );
		}
	}
	else
	{
		# Error
		my $errormsg = "The $type farm profile can have backends in services only.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}
}

sub new_service_backend    # ( $json_obj, $farmname, $service )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $json_obj = shift;
	my $farmname = shift;
	my $service  = shift;

	# Initial parameters
	my $description = "New service backend";

	# Check that the farm exists
	if ( !&getFarmExists( $farmname ) )
	{
		# Error
		my $errormsg = "The farmname $farmname does not exists.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 404, body => $body } );
	}

	# validate FARM TYPE
	my $type = &getFarmType( $farmname );

	if ( $type eq "http" || $type eq "https" )
	{
		# validate SERVICE
		# Check that the provided service is configured in the farm
		require Zevenet::Farm::HTTP::Service;

		my @services = &getHTTPFarmServices( $farmname );

		my $found = 0;
		foreach my $farmservice ( @services )
		{
			if ( $service eq $farmservice )
			{
				$found = 1;
				last;
			}
		}

		if ( $found eq 0 )
		{
			# Error
			my $errormsg = "Invalid service name, please insert a valid value.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 400, body => $body } );
		}

		# get an ID
		require Zevenet::Farm::HTTP::Service;
		require Zevenet::Farm::HTTP::Backend;

		my $id = &getHTTPFarmBackendAvailableID( $farmname, $service );

		# validate IP
		unless ( defined $json_obj->{ ip }
				 && &getValidFormat( 'IPv4_addr', $json_obj->{ ip } ) )
		{
			&zenlog(
				"Error trying to create a new backend http in service $service in farm $farmname, invalid backend IP value.",
				"error", "LSLB"
			);

			# Error
			my $errormsg = "Invalid backend IP value, please insert a valid value.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 400, body => $body } );
		}

		# validate PORT
		require Zevenet::Net::Validate;
		unless ( &isValidPortNumber( $json_obj->{ port } ) eq 'true' )
		{
			&zenlog(
				"Error trying to create a new backend http in service $service in farm $farmname, invalid IP address and port for a backend, ir can't be blank.",
				"error", "LSLB"
			);

			# Error
			my $errormsg = "Invalid port for a backend.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 400, body => $body } );
		}

		# validate WEIGHT
		unless ( !defined ( $json_obj->{ weight } )
				 || $json_obj->{ weight } =~ /^[1-9]$/ )
		{
			&zenlog(
				"Error trying to create a new backend http in service $service in farm $farmname, invalid weight value for a backend, it must be 1-9.",
				"error", "LSLB"
			);

			# Error
			my $errormsg = "Invalid weight value for a backend, it must be 1-9.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 400, body => $body } );
		}

		# validate TIMEOUT
		unless ( !defined ( $json_obj->{ timeout } )
			   || ( $json_obj->{ timeout } =~ /^\d+$/ && $json_obj->{ timeout } != 0 ) )
		{
			&zenlog(
					"Error trying to modify the backends in a farm $farmname, invalid timeout.",
					"error", "" );

			# Error
			my $errormsg =
			  "Invalid timeout value for a backend, it must be empty or greater than 0.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 400, body => $body } );
		}

# First param ($id) is an empty string to let function autogenerate the id for the new backend
		require Zevenet::Farm::Backend;

		my $status = &setHTTPFarmServer(
										 "",
										 $json_obj->{ ip },
										 $json_obj->{ port },
										 $json_obj->{ weight },
										 $json_obj->{ timeout },
										 $farmname,
										 $service,
		);

		if ( $status != -1 )
		{
			&zenlog(
				"Success, a new backend has been created in farm $farmname in service $service with IP $json_obj->{ip}.",
				"info", ""
			);

			# Success
			$json_obj->{ timeout } = $json_obj->{ timeout } + 0 if $json_obj->{ timeout };

			my $message = "Added backend to service successfully";
			my $body = {
						 description => $description,
						 params      => {
									 id      => $id,
									 ip      => $json_obj->{ ip },
									 port    => $json_obj->{ port } + 0,
									 weight  => $json_obj->{ weight } + 0,
									 timeout => $json_obj->{ timeout },
						 },
						 message => $message,
			};

			require Zevenet::Farm::Base;
			if ( &getFarmStatus( $farmname ) eq 'up' )
			{
				require Zevenet::Farm::Action;
				&runFarmReload( $farmname );
			}

			&httpResponse( { code => 201, body => $body } );
		}
		else
		{
			# Error
			my $errormsg =
			    "It's not possible to create the backend with ip "
			  . $json_obj->{ ip }
			  . " and port "
			  . $json_obj->{ port }
			  . " for the $farmname farm";

			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 400, body => $body } );
		}
	}
	elsif ( $type eq "gslb" )
	{
		include 'Zevenet::Farm::GSLB::Service';
		include 'Zevenet::Farm::GSLB::Backend';

		# validate SERVICE
		{
			my @services_list = &getGSLBFarmServices( $farmname );

			unless ( grep { $service eq $_ } @services_list )
			{
				# Error
				my $errormsg = "Could not find the requested service.";
				my $body = {
							 description => $description,
							 error       => "true",
							 message     => $errormsg
				};

				&httpResponse( { code => 404, body => $body } );
			}
		}

		# Get an ID
		require Zevenet::Farm::Config;

		my $lb = &getFarmVS( $farmname, $service, "algorithm" );

		# validate ALGORITHM
		unless ( $lb eq 'roundrobin' )
		{
			&zenlog( "Error, this service algorithm does not support adding new backends.",
					 "error", "" );

			# Error
			my $errormsg = "This service algorithm does not support adding new backends.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 400, body => $body } );
		}

		# Get an ID for the new backend
		my $id = &getGSLBFarmServiceBackendAvailableID( $farmname, $service );

		# validate IP
		unless ( &getValidFormat( 'IPv4_addr', $json_obj->{ ip } ) )
		{
			&zenlog(
				"Error trying to create a new backend in the service $service of the farm $farmname, invalid IP.",
				"error", ""
			);

			# Error
			my $errormsg = "Could not find the requested service.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 400, body => $body } );
		}

		#Adding the backend
		include 'Zevenet::Farm::GSLB::Backend';

		my $status =
		  &setGSLBFarmNewBackend( $farmname, $service, $lb, $id, $json_obj->{ ip } );

		if ( $status != -1 )
		{
			&zenlog(
				"Success, a new backend has been created in farm $farmname in service $service with IP $json_obj->{ip}.",
				"info", ""
			);

			# Success
			my $message = "Added backend to service successfully";
			my $body = {
						 description => $description,
						 params      => {
									 id => $id,
									 ip => $json_obj->{ ip },
						 },
						 message => $message,
			};

			require Zevenet::Farm::Base;

			if ( &getFarmStatus( $farmname ) eq 'up' )
			{
				require Zevenet::Farm::Action;
				&setFarmRestart( $farmname );
				$body->{ status } = 'needed restart';
			}

			&httpResponse( { code => 201, body => $body } );
		}
		else
		{
			# Error
			my $errormsg =
			    "It's not possible to create the backend "
			  . $json_obj->{ ip }
			  . " for the service $service.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 400, body => $body } );
		}
	}
	else
	{
		# Error
		my $errormsg = "The $type farm profile does not support services.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}
}

# GET

#GET /farms/<name>/backends
sub backends
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my $farmname = shift;

	my $description = "List backends";

	# Check that the farm exists
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

	my $type = &getFarmType( $farmname );

	if ( $type eq 'l4xnat' )
	{
		require Zevenet::Farm::L4xNAT;
		my $l4_farm = &getL4FarmStruct( $farmname );
		my @backends;

		for my $be ( @{ $l4_farm->{ 'servers' } } )
		{
			$be->{ 'vport' } = $be->{ 'vport' } eq '' ? undef : $be->{ 'vport' } + 0;
			$be->{ 'priority' } = $be->{ 'priority' } ? $be->{ 'priority' } + 0 : undef;
			$be->{ 'weight' }   = $be->{ 'weight' }   ? $be->{ 'weight' } + 0   : undef;
			$be->{ 'max_conns' } = $be->{ 'max_conns' } + 0;

			push @backends,
			  {
				id        => $be->{ 'id' } + 0,
				ip        => $be->{ 'vip' },
				port      => $be->{ 'vport' },
				priority  => $be->{ 'priority' },
				weight    => $be->{ 'weight' },
				status    => $be->{ 'status' },
				max_conns => $be->{ 'max_conns' },
			  };
		}

		my $body = {
					 description => $description,
					 params      => \@backends,
		};

		# Success
		&httpResponse( { code => 200, body => $body } );
	}
	elsif ( $type eq 'datalink' )
	{
		require Zevenet::Farm::Datalink::Backend;
		my $backends = &getDatalinkFarmBackends( $farmname );

		my $body = {
					 description => $description,
					 params      => $backends,
		};

		&httpResponse( { code => 200, body => $body } );
	}
	else
	{
		# Error
		my $errormsg =
		  "The farm $farmname with profile $type does not support this request.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}
}

#GET /farms/<name>/services/<service>/backends
sub service_backends
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farmname, $service ) = @_;

	my $backendstatus;
	my $description = "List service backends";

	# Check that the farm exists
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

	my $type = &getFarmType( $farmname );

	if ( $type eq 'http' || $type eq 'https' )
	{
		require Zevenet::Farm::HTTP::Service;

		my $service_ref = &getHTTPServiceStruct( $farmname, $service );
		foreach my $be ( @{ $service_ref->{ backends } } )
		{
			delete ( $be->{ priority } );
		}

		# check if the requested service exists
		if ( $service_ref == -1 )
		{
			# Error
			my $errormsg = "The service $service does not exist.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 404, body => $body } );
		}

		my $body = {
					 description => $description,
					 params      => $service_ref->{ backends },
		};

		# Success
		&httpResponse( { code => 200, body => $body } );
	}
	elsif ( $type eq 'gslb' )
	{
		include 'Zevenet::Farm::GSLB::Service';
		include 'Zevenet::Farm::GSLB::Backend';

		my $desc          = "List service backends";
		my @services_list = &getGSLBFarmServices( $farmname );
		my @backends;    # output

		# check if the service exists
		unless ( grep { $service eq $_ } @services_list )
		{
			# Error
			my $errormsg = "The service $service does not exist.";
			my $body = {
						 description => $desc,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 404, body => $body } );
		}

		my $backends = &getGSLBFarmBackends( $farmname, $service );
		my $body = {
					 description => $desc,
					 params      => $backends,
		};

		&httpResponse( { code => 200, body => $body } );
	}
	else
	{
		# Error
		my $errormsg =
		  "The farm $farmname with profile $type does not support this request.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}
}

# PUT

sub modify_backends    #( $json_obj, $farmname, $id_server )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $json_obj, $farmname, $id_server ) = @_;

	my $description = "Modify backend";
	my $zapierror;

	# Check that the farm exists
	if ( !&getFarmExists( $farmname ) )
	{
		# Error
		my $errormsg = "The farmname $farmname does not exists.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse( { code => 404, body => $body } );
	}

	my $error;
	my $type = &getFarmType( $farmname );

	if ( $type eq "l4xnat" )
	{
		require Zevenet::Farm::L4xNAT::Config;

		# Params
		my $l4_farm = &getL4FarmStruct( $farmname );
		my $backend;

		for my $be ( @{ $l4_farm->{ 'servers' } } )
		{
			if ( $be->{ 'id' } eq $id_server )
			{
				$backend = $be;
			}
		}

		if ( !$backend )
		{
			# Error
			my $errormsg = "Could not find a backend with such id.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg,
			};

			&httpResponse( { code => 404, body => $body } );
		}

		if ( exists ( $json_obj->{ ip } ) )
		{
			if ( $json_obj->{ ip } && &getValidFormat( 'IPv4_addr', $json_obj->{ ip } ) )
			{
				$backend->{ vip } = $json_obj->{ ip };
			}
			else
			{
				$error = "true";
				$zapierror =
				  "Error trying to modify the backend in the farm $farmname, invalid IP.";
				&zenlog( "$zapierror", "error", "" );
			}
		}

		if ( !$error && exists ( $json_obj->{ port } ) )
		{
			if (    &isValidPortNumber( $json_obj->{ port } ) eq 'true'
				 || $json_obj->{ port } == undef )
			{
				$backend->{ vport } = $json_obj->{ port };
			}
			else
			{
				$error = "true";
				$zapierror =
				  "Error trying to modify the backend in the farm $farmname, invalid port number.";
				&zenlog( "$zapierror", "error", "" );
			}
		}

		if ( !$error && exists ( $json_obj->{ weight } ) )
		{
			if (    $json_obj->{ weight } =~ /^\d*[1-9]$/
				 || $json_obj->{ weight } == undef )    # 1 or higher
			{
				$backend->{ weight } = $json_obj->{ weight };
			}
			else
			{
				$error = "true";
				$zapierror =
				  "Error trying to modify the backends in a farm $farmname, invalid weight.";
				&zenlog( "$zapierror", "error", "" );
			}
		}

		if ( !$error && exists ( $json_obj->{ priority } ) )
		{
			if (    $json_obj->{ priority } =~ /^\d$/
				 || $json_obj->{ priority } == undef )    # (0-9)
			{
				$backend->{ priority } = $json_obj->{ priority };
			}
			else
			{
				$error = "true";
				$zapierror =
				  "Error trying to modify the backends in the farm $farmname, invalid priority.";
				&zenlog( "$zapierror", "error", "" );
			}
		}

		if ( !$error && exists ( $json_obj->{ max_conns } ) )
		{
			if ( $json_obj->{ max_conns } =~ /^\d+$/ )    # (0 or higher)
			{
				$backend->{ max_conns } = $json_obj->{ max_conns };
			}
			else
			{
				$error = "true";
				$zapierror =
				  "Error trying to modify the connection limit in the farm $farmname, invalid value.";
				&zenlog( "$zapierror", "error", "" );
			}
		}

		if ( !$error )
		{
			my $status = &setL4FarmServer(
										   $farmname,
										   $backend->{ id },
										   $backend->{ vip },
										   $backend->{ vport },
										   $backend->{ weight },
										   $backend->{ priority },
										   $backend->{ max_conns },
			);

			if ( $status == -1 )
			{
				$error = "true";
				$zapierror =
				  "Error trying to modify the backends in a farm $farmname, it's not possible to modify the backend with ip $json_obj->{ip}.";
				&zenlog( "$zapierror", "error", "" );
			}
		}
	}
	elsif ( $type eq "datalink" )
	{
		require Zevenet::Farm::Datalink::Backend;

		my $be;
		{
			my $b_ref = &getDatalinkFarmBackends( $farmname );
			$be = @{ $b_ref }[$id_server];
		}

		if ( !$be )
		{
			# Error
			my $errormsg = "Could not find a backend with such id.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg,
			};

			&httpResponse( { code => 404, body => $body } );
		}

		# Functions
		if ( exists ( $json_obj->{ ip } ) )
		{
			if ( $json_obj->{ ip } && &getValidFormat( 'IPv4_addr', $json_obj->{ ip } ) )
			{
				$be->{ ip } = $json_obj->{ ip };
			}
			else
			{
				$error = "true";
				$zapierror =
				  "Error trying to modify the backends in the farm $farmname, invalid IP.";
				&zenlog( "$zapierror", "error", "" );
			}
		}

		if ( !$error && exists ( $json_obj->{ interface } ) )
		{
			require Zevenet::Net::Interface;

			my $valid_interface;

			for my $iface ( @{ &getActiveInterfaceList() } )
			{
				next if $iface->{ vini };     # discard virtual interfaces
				next if !$iface->{ addr };    # discard interfaces without address

				if ( $iface->{ name } eq $json_obj->{ interface } )
				{
					$valid_interface = 'true';
				}
			}

			if ( $valid_interface )
			{
				$be->{ interface } = $json_obj->{ interface };
			}
			else
			{
				$error = "true";
				$zapierror =
				  "Error trying to modify the backends in the farm $farmname, invalid interface.";
				&zenlog( "$zapierror", "error", "" );
			}
		}

		if ( !$error && exists ( $json_obj->{ weight } ) )
		{
			if (    $json_obj->{ weight } =~ &getValidFormat( 'natural_num' )
				 || $json_obj->{ weight } == undef )    # 1 or higher
			{
				$be->{ weight } = $json_obj->{ weight };
			}
			else
			{
				$error = "true";
				$zapierror =
				  "Error trying to modify the backends in the farm $farmname, invalid weight.";
				&zenlog( "$zapierror", "error", "" );
			}
		}

		if ( !$error && exists ( $json_obj->{ priority } ) )
		{
			if (    $json_obj->{ priority } =~ /^[1-9]$/
				 || $json_obj->{ priority } == undef )    # (1-9)
			{
				$be->{ priority } = $json_obj->{ priority };
			}
			else
			{
				$error = "true";
				$zapierror =
				  "Error trying to modify the backends in the farm $farmname, invalid priority.";
				&zenlog( "$zapierror", "error", "" );
			}
		}

		if ( !$error )
		{
			my $status = &setFarmServer( $farmname, undef, $id_server, $be );

			if ( $status == -1 )
			{
				$error = "true";
				$zapierror =
				  "Error trying to modify the backends in the farm $farmname, it's not possible to modify the backend with IP $json_obj->{ip} and interface $json_obj->{interface}.";
				&zenlog( "$zapierror", "error", "" );
			}
		}
	}
	else
	{
		# Error
		my $errormsg = "The $type farm profile has backends only in services.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 404, body => $body } );
	}

	# Print params
	if ( !$error )
	{
		&zenlog(
			"Success, some parameters have been changed in the backend $id_server in farm $farmname.",
			"info", ""
		);

		# Success
		my $message = "Backend modified";
		my $body = {
					 description => $description,
					 params      => $json_obj,
					 message     => $message,
		};

		if ( &getFarmStatus( $farmname ) eq 'up' )
		{
			include 'Zevenet::Cluster';
			&runZClusterRemoteManager( 'farm', 'restart', $farmname );
		}

		&httpResponse( { code => 200, body => $body } );
	}
	else
	{
		&zenlog(
			"Error trying to modify the backend in the farm $farmname, it's not possible to modify the backend.",
			"error", ""
		);

		# Error
		my $errormsg = "Errors found trying to modify farm $farmname";
		if ( $zapierror )
		{
			$errormsg = $zapierror;
		}
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}
}

sub modify_service_backends    #( $json_obj, $farmname, $service, $id_server )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $json_obj, $farmname, $service, $id_server ) = @_;

	my $description = "Modify service backend";
	my $zapierror;

	# Check that the farm exists
	if ( !&getFarmExists( $farmname ) )
	{
		# Error
		my $errormsg = "The farmname $farmname does not exist.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse( { code => 404, body => $body } );
	}

	my $error;
	my $type = &getFarmType( $farmname );

	if ( $type eq "http" || $type eq "https" )
	{
		require Zevenet::Farm::HTTP::Service;
		require Zevenet::Farm::HTTP::Backend;

		# validate SERVICE
		{
			my @services = &getHTTPFarmServices( $farmname );
			my $found_service = grep { $service eq $_ } @services;

			if ( !$found_service )
			{
				# Error
				my $errormsg = "Could not find the requested service.";
				my $body = {
							 description => $description,
							 error       => "true",
							 message     => $errormsg
				};

				&httpResponse( { code => 404, body => $body } );
			}
		}

		# validate BACKEND
		my $be;
		{
			my $servers = &getHTTPFarmBackends( $farmname, $service );
			$be = @{ $servers }[$id_server];
		}

		# check if the backend was found
		if ( !$be )
		{
			# Error
			my $errormsg = "Could not find a service backend with such id.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg,
			};

			&httpResponse( { code => 404, body => $body } );
		}

		# Functions
		if ( exists ( $json_obj->{ ip } ) )
		{
			if ( $json_obj->{ ip } && &getValidFormat( 'IPv4_addr', $json_obj->{ ip } ) )
			{
				$be->{ ip } = $json_obj->{ ip };
			}
			else
			{
				$error = "true";
				$zapierror =
				  "Error trying to modify the backends in a farm $farmname, invalid IP.";
				&zenlog( "$zapierror", "error", "" );
			}
		}

		if ( !$error && exists ( $json_obj->{ port } ) )
		{
			require Zevenet::Net::Validate;

			if ( &isValidPortNumber( $json_obj->{ port } ) eq 'true' )
			{
				$be->{ port } = $json_obj->{ port };
			}
			else
			{
				$error = "true";
				$zapierror =
				  "Error trying to modify the backends in a farm $farmname, invalid port.";
				&zenlog( "$zapierror", "error", "" );
			}
		}

		if ( !$error && exists ( $json_obj->{ weight } ) )
		{
			if ( $json_obj->{ weight } =~ /^[1-9]$/ )
			{
				$be->{ weight } = $json_obj->{ weight };
			}
			else
			{
				$error = "true";
				$zapierror =
				  "Error trying to modify the backends in a farm $farmname, invalid weight.";
				&zenlog( "$zapierror", "error", "" );
			}
		}

		if ( !$error && exists ( $json_obj->{ timeout } ) )
		{
			if ( $json_obj->{ timeout } eq ''
				 || ( $json_obj->{ timeout } =~ /^\d+$/ && $json_obj->{ timeout } != 0 ) )
			{
				$be->{ timeout } = $json_obj->{ timeout };
			}
			else
			{
				$error = "true";
				$zapierror =
				  "Error trying to modify the backends in a farm $farmname, invalid timeout.";
				&zenlog( "$zapierror", "error", "" );
			}
		}

		if ( !$error )
		{
			require Zevenet::Farm::Backend;

			my $status = &setFarmServer( $farmname, $service, $id_server, $be );

			if ( $status == -1 )
			{
				$error = "true";
				$zapierror =
				  "Error trying to modify the backends in a farm $farmname, it's not possible to modify the backend with IP $json_obj->{ip} in service $service.";
				&zenlog( "$zapierror", "error", "" );
			}
			else
			{
				require Zevenet::Farm::Action;

				&runFarmReload( $farmname );
			}
		}
	}
	elsif ( $type eq "gslb" )
	{
		# validate SERVICE
		{
			include 'Zevenet::Farm::GSLB::Service';

			my @services = &getGSLBFarmServices( $farmname );
			my $found_service = grep { $service eq $_ } @services;

			if ( !$found_service )
			{
				# Error
				my $errormsg = "Could not find the requested service.";
				my $body = {
							 description => $description,
							 error       => "true",
							 message     => $errormsg
				};

				&httpResponse( { code => 404, body => $body } );
			}
		}

		# validate BACKEND
		my $be;
		my $backend_id = $id_server;
		{
			require Zevenet::Farm::Config;

			my $backendsvs = &getFarmVS( $farmname, $service, "backends" );
			my @be_list = split ( "\n", $backendsvs );

			# convert backend_id for prio algorithm
			my $algorithm = &getFarmVS( $farmname, $service, "algorithm" );
			if ( $algorithm eq 'prio' )
			{
				$backend_id = 'primary'   if $id_server == 1;
				$backend_id = 'secondary' if $id_server == 2;
			}

			foreach my $be_line ( @be_list )
			{
				$be_line =~ s/^\s+//;
				next if !$be_line;

				my @current_be = split ( " => ", $be_line );

				if ( $current_be[0] == $backend_id )
				{
					$be = {
							id       => $current_be[1],
							ip       => $current_be[3],
							port     => $current_be[5],
							timeout  => $current_be[7],
							priority => $current_be[9],
					};

					last;
				}
			}

			if ( !$be )
			{
				# Error
				my $errormsg = "Could not find a service backend with such id.";
				my $body = {
							 description => $description,
							 error       => "true",
							 message     => $errormsg,
				};

				&httpResponse( { code => 404, body => $body } );
			}
		}

		my $lb = &getFarmVS( $farmname, $service, "algorithm" );

		# Functions
		if ( exists ( $json_obj->{ ip } ) )
		{
			if ( $json_obj->{ ip } && &getValidFormat( 'IPv4_addr', $json_obj->{ ip } ) )
			{
				$be->{ ip } = $json_obj->{ ip };
			}
			else
			{
				$error = "true";
				$zapierror =
				  "Error trying to modify the backends in a farm $farmname, invalid IP.";
				&zenlog( "$zapierror", "error", "" );
			}
		}

		if ( !$error )
		{
			include 'Zevenet::Farm::GSLB::Backend';

			my $status =
			  &setGSLBFarmNewBackend( $farmname, $service, $lb, $backend_id,
									  $json_obj->{ ip } );

			if ( $status == -1 )
			{
				$error = "true";
				$zapierror =
				  "Error trying to modify the backends in a farm $farmname, it's not possible to modify the backend with IP $json_obj->{ip} in service $service.";
				&zenlog( "$zapierror", "error", "" );
			}
			else
			{
				require Zevenet::Farm::Action;
				&setFarmRestart( $farmname );
			}
		}
	}
	else
	{
		# Error
		my $errormsg = "The $type farm profile does not support services.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 404, body => $body } );
	}

	# Print params
	if ( !$error )
	{
		&zenlog(
			"Success, some parameters have been changed in the backend $id_server in service $service in farm $farmname.",
			"info", ""
		);

		# Success
		# Get farm status. If farm is down the restart is not required.
		my $body = {
					 description => $description,
					 params      => $json_obj,
					 message     => "Backend modified",
		};

		if ( &getFarmStatus( $farmname ) eq "up" )
		{
			$body->{ status } = 'needed restart';
			$body->{ info } =
			  "There're changes that need to be applied, stop and start farm to apply them!";
		}

		&httpResponse( { code => 200, body => $body } );
	}
	else
	{
		&zenlog(
			"Error trying to modify the backends in a farm $farmname, it's not possible to modify the backend.",
			"error", ""
		);

		# Error
		my $errormsg = "Errors found trying to modify farm $farmname";
		if ( $zapierror )
		{
			$errormsg = $zapierror;
		}
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}
}

# DELETE

# DELETE /farms/<farmname>/backends/<backendid> Delete a backend of a Farm
sub delete_backend    # ( $farmname, $id_server )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farmname, $id_server ) = @_;

	my $description = "Delete backend";

	# validate FARM NAME
	if ( !&getFarmExists( $farmname ) )
	{
		# Error
		my $errormsg = "The farmname $farmname does not exists.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 404, body => $body } );
	}

	# validate FARM TYPE
	my $type = &getFarmType( $farmname );
	unless ( $type eq 'l4xnat' || $type eq 'datalink' )
	{
		# Error
		my $errormsg = "The $type farm profile has backends only in services.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}

	my $exists   = 0;
	my $backends = &getFarmServers( $farmname );
	$exists = @{ $backends }[$id_server];

	if ( !$exists )
	{
		# Error
		my $errormsg = "Could not find a backend with such id.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse( { code => 404, body => $body } );
	}

	my $status = &runFarmServerDelete( $id_server, $farmname );

	if ( $status != -1 )
	{
		&zenlog( "Success, the backend $id_server in farm $farmname has been deleted.",
				 "info", "" );

		# Success
		if ( $type eq 'l4xnat' )
		{
			include 'Zevenet::Cluster';
			&runZClusterRemoteManager( 'farm', 'delete', $farmname, 'backend', $id_server );
		}
		else
		{
			include 'Zevenet::Cluster';
			&runZClusterRemoteManager( 'farm', 'restart', $farmname );
		}

#~ my $message = "The backend with ID $id_server of the $farmname farm has been deleted.";
		my $message = "Backend removed";

		my $body = {
					 description => $description,
					 success     => "true",
					 message     => $message
		};

		&httpResponse( { code => 200, body => $body } );
	}
	else
	{
		&zenlog(
			"Error trying to delete the backend $id_server in farm $farmname, it's not possible to delete the backend.",
			"error", ""
		);

		# Error
		my $errormsg =
		  "It's not possible to delete the backend with ID $id_server of the $farmname farm.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}
}

#  DELETE /farms/<farmname>/services/<servicename>/backends/<backendid> Delete a backend of a Service
sub delete_service_backend    # ( $farmname, $service, $id_server )
{
	&zenlog( __FILE__ . ":" . __LINE__ . ":" . ( caller ( 0 ) )[3] . "( @_ )",
			 "debug", "PROFILING" );
	my ( $farmname, $service, $id_server ) = @_;

	my $description = "Delete service backend";

	# validate FARM NAME
	if ( !&getFarmExists( $farmname ) )
	{
		# Error
		my $errormsg = "The farmname $farmname does not exists.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 404, body => $body } );
	}

	# validate FARM TYPE
	my $type = &getFarmType( $farmname );
	unless ( $type eq 'http' || $type eq 'https' || $type eq 'gslb' )
	{
		# Error
		my $errormsg = "The $type farm profile has backends only in services.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}

	# validate SERVICE
	{
		my @services;

		if ( $type eq "gslb" )
		{
			include 'Zevenet::Farm::GSLB::Service';
			@services = &getGSLBFarmServices( $farmname );
		}
		else
		{
			require Zevenet::Farm::HTTP::Service;
			@services = &getHTTPFarmServices( $farmname );
		}

		my $found_service = grep { $service eq $_ } @services;

		if ( !$found_service )
		{
			# Error
			my $errormsg = "Could not find the requested service.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 404, body => $body } );
		}

		# validate ALGORITHM
		require Zevenet::Farm::Config;

		if ( &getFarmVS( $farmname, $service, "algorithm" ) eq 'prio' )
		{
			&zenlog( "Error this service algorithm does not support removing backends.",
					 "error", "" );

			# Error
			my $errormsg = "This service algorithm does not support removing backends.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 400, body => $body } );
		}

		# check if the backend id is available
		my @backends = split ( "\n", &getFarmVS( $farmname, $service, "backends" ) );
		my $be_found;

		if ( $type eq "gslb" )
		{
			$be_found = grep ( /\s*$id_server\s=>\s/, @backends );
		}
		else
		{
			$be_found = grep { ( split ( " ", $_ ) )[1] == $id_server } @backends;
		}

		unless ( $be_found )
		{
			my $errormsg = "Could not find the requested backend.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 404, body => $body } );
		}
	}

	my $status;

	if ( $type eq "http" || $type eq "https" )
	{
		require Zevenet::Farm::Backend;
		$status = &runFarmServerDelete( $id_server, $farmname, $service );
	}
	if ( $type eq "gslb" )
	{
		include 'Zevenet::Farm::GSLB::Backend';
		$status = &remFarmServiceBackend( $id_server, $farmname, $service );
	}

	if ( $status != -1 )
	{
		&zenlog(
			"Success, the backend $id_server in service $service in farm $farmname has been deleted.",
			"info", ""
		);

		my $message = "Backend removed";
		my $body = {
					 description => $description,
					 success     => "true",
					 message     => $message,
		};

		if ( &getFarmStatus( $farmname ) eq 'up' )
		{
			require Zevenet::Farm::Action;
			if ( $type eq "gslb" )
			{
				$body->{ status } = "needed restart";
				&setFarmRestart( $farmname );
			}
			else
			{
				&runFarmReload( $farmname );
			}
		}

		&httpResponse( { code => 200, body => $body } );
	}
	else
	{
		&zenlog(
			"Error trying to delete the backend $id_server in service $service in farm $farmname, it's not possible to delete the backend.",
			"error", ""
		);

		# Error
		my $errormsg =
		  "Could not find the backend with ID $id_server of the $farmname farm.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 404, body => $body } );
	}
}

1;
