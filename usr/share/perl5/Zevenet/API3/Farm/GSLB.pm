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

# GET /farms/GSLBFARM
sub farms_gslb # ()
{
	my @out;
	my @files = &getFarmList();

	foreach my $file ( @files )
	{
		my $name   = &getFarmName( $file );
		my $type   = &getFarmType( $name );
		next unless $type eq 'gslb';
		my $status = &getFarmStatus( $name );
		my $vip    = &getFarmVip( 'vip', $name );
		my $port   = &getFarmVip( 'vipp', $name );

		$status = "needed restart" if $status eq 'up' && ! &getFarmLock($name);

		push @out,
		  {
			farmname => $name,
			status   => $status,
			vip      => $vip,
			vport    => $port
		  };
	}

	my $body = {
				description => "List GSLB farms",
				params      => \@out,
	};

	&httpResponse({ code => 200, body => $body });
}

## Services

# POST /farms/<farmname>/services/<servicename>
sub new_gslb_farm_service    # ( $json_obj, $farmname )
{
	my $json_obj = shift;
	my $farmname = shift;

	require Zevenet::Farm::Base;
	require Zevenet::Farm::GSLB::Service;

	# check if there is a service name
	if ( $json_obj->{ id } eq '' )
	{
		&zenlog(
			"ZAPI error, trying to create a new service in farm $farmname, invalid service name."
		);

		my $errormsg = "Invalid service, please insert a valid value.";
		my $body = {
					 description => "New service " . $json_obj->{ id },
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}

	# check if there is a service algorithm
	if ( $json_obj->{ algorithm } eq '' )
	{
		&zenlog(
			"ZAPI error, trying to create a new service in farm $farmname, invalid algorithm."
		);

		my $errormsg = "Invalid algorithm, please insert a valid value.";
		my $body = {
					 description => "New service " . $json_obj->{ id },
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}

	my $status = &setGSLBFarmNewService( $farmname,
										 $json_obj->{ id },
										 $json_obj->{ algorithm } );

	# check if there was an error creating the new service
	if ( $status == -1 )
	{
		&zenlog(
			"ZAPI error, trying to create a new service in farm $farmname, it's not possible to create the service $json_obj->{id}."
		);

		my $errormsg = "It's not possible to create the service " . $json_obj->{ id };
		my $body = {
					 description => "New service " . $json_obj->{ id },
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}

	# no error found, return a succesful response
	&zenlog(
		"ZAPI success, a new service has been created in farm $farmname with id $json_obj->{id}."
	);

	my $body = {
				 description => "New service " . $json_obj->{ id },
				 params      => {
							 id        => $json_obj->{ id },
							 algorithm => $json_obj->{ algorithm }
				 },
	};

	if ( &getFarmStatus( $farmname ) eq 'up' )
	{
		require Zevenet::Farm::Action;

		&setFarmRestart( $farmname );
		$body->{ status } = 'needed restart';
	}

	&httpResponse( { code => 201, body => $body } );
}

# PUT /farms/<farmname>/services/<servicename>
sub modify_gslb_service # ( $json_obj, $farmname, $service )
{
	my ( $json_obj, $farmname, $service ) = @_;

	require Zevenet::Farm::GSLB::Config;
	require Zevenet::Farm::GSLB::FarmGuardian;

	my $output_params;
	my $description = "Modify service";

	# check deftcpport parameter is not empty
	if ( $json_obj->{ deftcpport } eq '' )
	{
		&zenlog(
			"ZAPI error, trying to modify the service $service in a farm $farmname, invalid deftcpport, can't be blank."
		);
		my $errormsg = "Invalid parameter deftcpport, can't be blank.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 400, body => $body });
	}

	# change to number format
	$json_obj->{ deftcpport } += 0;

	my $old_deftcpport = &getGSLBFarmVS ($farmname,$service, 'dpc');
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
		&zenlog(
			"ZAPI error, trying to modify the service $service in a farm $farmname, it's not possible to change the deftcpport parameter."
		);
		my $errormsg = "Could not change the deftcpport parameter.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	&runGSLBFarmReload( $farmname );

	# FIXME: Read gslb configuration instead of returning input
	$output_params = $json_obj;

	# no errors found, return succesful response
	&zenlog(
		"ZAPI success, some parameters have been changed in service $service in farm $farmname."
	);

	my $body = {
		description => "Modify service $service in farm $farmname",
		params      => $output_params,
	};

	if ( &getFarmStatus( $farmname ) eq 'up' )
	{
		require Zevenet::Farm::Action;

		&setFarmRestart( $farmname );
		$body->{ status } = 'needed restart';
		$body->{ info } = "There're changes that need to be applied, stop and start farm to apply them!";
	}

	&httpResponse({ code => 200, body => $body });
}

# DELETE /farms/<farmname>/services/<servicename>
sub delete_gslb_service # ( $farmname, $service )
{
	my ( $farmname, $service ) = @_;

	require Zevenet::Farm::Base;
	require Zevenet::Farm::GSLB::Service;

	my @services = &getGSLBFarmServices($farmname);
	my $found = 0;

	# validate SERVICE
	foreach my $farmservice (@services)
	{
		#print "service: $farmservice";
		if ($service eq $farmservice)
		{
			$found = 1;
			last;
		}
	}

	# Check if the service exists
	if ($found == 0)
	{
		my $errormsg = "Invalid service name, please insert a valid value.";
		my $body = {
					 description => "Delete service",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	my $return = &setGSLBFarmDeleteService( $farmname, $service );

	# check if the service is being used
	if ( $return == -2 )
	{
		&zenlog(
				 "ZAPI error, the service $service in farm $farmname hasn't been deleted. The service is used by a zone." );

		my $message = "The service $service in farm $farmname hasn't been deleted. The service is used by a zone.";
		my $body = {
					 description => "Delete service $service in farm $farmname.",
					 error       => "true",
					 message     => $message
		};

		&httpResponse({ code => 400, body => $body });
	}

	# check if the service could not be deleted
	if ( $return != 0 )
	{
		&zenlog(
			"ZAPI error, trying to delete the service $service in farm $farmname, the service hasn't been deleted."
		);

		my $errormsg = "Service $service in farm $farmname hasn't been deleted.";
		my $body = {
					 description => "Delete service $service in farm $farmname",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	# no error found, return succesful response
	&zenlog(
			 "ZAPI success, the service $service in farm $farmname has been deleted." );

	my $message = "The service $service in farm $farmname has been deleted.";
	my $body = {
				 description => "Delete service $service in farm $farmname.",
				 success     => "true",
				 message     => $message
	};

	if ( &getFarmStatus( $farmname ) eq 'up' )
	{
		require Zevenet::Farm::Action;

		$body->{ status } = "needed restart";
		&setFarmRestart( $farmname );
	}

	&httpResponse({ code => 200, body => $body });
}

## Backends

# POST /farms/<farmname>/services/<servicename>/backends
sub new_gslb_service_backend    # ( $json_obj, $farmname, $service )
{
	my $json_obj = shift;
	my $farmname = shift;
	my $service  = shift;

	require Zevenet::Farm::Base;
	require Zevenet::Farm::Config;
	require Zevenet::Farm::GSLB::Service;
	require Zevenet::Farm::GSLB::Backend;

	my $description = "New service backend";
	my @services_list = &getGSLBFarmServices( $farmname );

	# check if the SERVICE exists
	unless ( grep { $service eq $_ } @services_list )
	{
		my $errormsg = "Could not find the requested service.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 404, body => $body } );
	}

	my $lb = &getFarmVS( $farmname, $service, "algorithm" );

	# validate supported ALGORITHM
	unless ( $lb eq 'roundrobin' )
	{
		&zenlog(
			   "ZAPI error, this service algorithm does not support adding new backends." );

		my $errormsg = "This service algorithm does not support adding new backends.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}

	# Get an ID for the new backend
	my $id         = 1;
	my $backendsvs = &getFarmVS( $farmname, $service, "backends" );
	my @be         = split ( "\n", $backendsvs );

	foreach my $subline ( @be )
	{
		$subline =~ s/^\s+//;
		if ( $subline =~ /^$/ )
		{
			next;
		}
		$id++;
	}

	# validate IP
	unless ( &getValidFormat( 'IPv4_addr', $json_obj->{ ip } ) )
	{
		&zenlog(
			"ZAPI error, trying to create a new backend in the service $service of the farm $farmname, invalid IP."
		);

		my $errormsg = "Could not find the requested service.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}

	# Adding the backend
	my $status =
	  &setGSLBFarmNewBackend( $farmname, $service, $lb, $id, $json_obj->{ ip } );

	# check if adding the new backend failed
	if ( $status == -1 )
	{
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

	# no error found, return successful response
	&zenlog(
		"ZAPI success, a new backend has been created in farm $farmname in service $service with IP $json_obj->{ip}."
	);

	my $message = "Added backend to service successfully";
	my $body = {
				 description => $description,
				 params      => {
							 id => $id,
							 ip => $json_obj->{ ip },
				 },
				 message => $message,
	};

	if ( &getFarmStatus( $farmname ) eq 'up' )
	{
		require Zevenet::Farm::Action;

		&setFarmRestart( $farmname );
		$body->{ status } = 'needed restart';
	}

	&httpResponse( { code => 201, body => $body } );
}

# GET /farms/<name>/services/<service>/backends
sub list_gslb_service_backends
{
	my ( $farmname, $service ) = @_;

	require Zevenet::Farm::Config;
	require Zevenet::Farm::GSLB::Service;

	my $description   = "List service backends";
	my $type          = &getFarmType( $farmname );
	my @services_list = &getGSLBFarmServices( $farmname );
	my @backends;    # output

	# check if the service exists
	unless ( grep { $service eq $_ } @services_list )
	{
		my $errormsg = "The service $service does not exist.";
		my $body = {
				description => $description,
				error => "true",
				message => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	my $backends = &getFarmBackends( $farmname, $service );
	my $body = {
				 description => $description,
				 params      => $backends,
	};

	&httpResponse({ code => 200, body => $body });
}

# PUT /farms/<farmname>/services/<servicename>/backends/<backendid>
sub modify_gslb_service_backends #( $json_obj, $farmname, $service, $id_server )
{
	my ( $json_obj, $farmname, $service, $id_server ) = @_;

	require Zevenet::Farm::Action;
	require Zevenet::Farm::Config;
	require Zevenet::Farm::GSLB::Service;
	require Zevenet::Farm::GSLB::Backend;

	my $description = "Modify service backend";
	my @services = &getGSLBFarmServices( $farmname );

	# check if the SERVICE exists
	unless ( grep { $service eq $_ } @services )
	{
		my $errormsg = "Could not find the requested service.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	my $be;
	my $backend_id = $id_server;
	my $backendsvs = &getFarmVS( $farmname, $service, "backends" );
	my @be_list = split ( "\n", $backendsvs );
	my $algorithm = &getFarmVS( $farmname, $service, "algorithm" ); # convert backend_id for prio algorithm

	if ( $algorithm eq 'prio' )
	{
		$backend_id = 'primary' if $id_server == 1;
		$backend_id = 'secondary' if $id_server == 2;
	}

	# get requested backend info
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

	# check if the BACKEND exists
	if ( !$be )
	{
		my $errormsg = "Could not find a service backend with such id.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 404, body => $body });
	}

	my $lb = &getFarmVS( $farmname, $service, "algorithm" );

	# validate BACKEND ip
	if ( exists ( $json_obj->{ ip } ) )
	{
		unless ( $json_obj->{ ip } && &getValidFormat('IPv4_addr', $json_obj->{ ip } ) )
		{
			my $errormsg = "Error, trying to modify the backends in a farm $farmname, invalid IP.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg,
			};

			&zenlog( $errormsg );
			&httpResponse({ code => 400, body => $body });
		}

		$be->{ ip } = $json_obj->{ ip };
	}

	my $status =
	  &setGSLBFarmNewBackend( $farmname, $service, $lb, $backend_id, $json_obj->{ ip } );

	# check if there was an error modifying the backend
	if ( $status == -1 )
	{
		my $errormsg = "Error, trying to modify the backends in a farm $farmname, it's not possible to modify the backend with IP $json_obj->{ip} in service $service.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&zenlog( $errormsg );
		&httpResponse({ code => 400, body => $body });
	}

	# no error found, return successful response
	&setFarmRestart( $farmname );

	&zenlog(
		"ZAPI success, some parameters have been changed in the backend $id_server in service $service in farm $farmname."
	);

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

	&httpResponse({ code => 200, body => $body });
}

# DELETE /farms/<farmname>/services/<servicename>/backends/<backendid>
sub delete_gslb_service_backend # ( $farmname, $service, $id_server )
{
	my ( $farmname, $service, $id_server ) = @_;

	require Zevenet::Farm::Action;
	require Zevenet::Farm::Config;
	require Zevenet::Farm::GSLB::Service;
	require Zevenet::Farm::GSLB::Backend;

	my $description = "Delete service backend";
	my @services = &getGSLBFarmServices($farmname);

	# check if the SERVICE exists
	unless ( grep { $service eq $_ } @services )
	{
		my $errormsg = "Could not find the requested service.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	# validate ALGORITHM
	if ( &getFarmVS( $farmname, $service, "algorithm" ) eq 'prio' )
	{
		&zenlog(
			 "ZAPI error, this service algorithm does not support removing backends." );

		my $errormsg = "This service algorithm does not support removing backends.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	# check if the backend id is available
	my @backends = split ( "\n", &getFarmVS( $farmname, $service, "backends" ) );
	my $be_found = grep( /\s*$id_server\s=>\s/, @backends);

	unless ( $be_found )
	{
		my $errormsg = "Could not find the requested backend.";
		my $body = {
					description => $description,
					error       => "true",
					message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	my $status = &remFarmServiceBackend( $id_server, $farmname, $service );

	# check if there was an error removing the backend
	if ( $status == -1 )
	{
		&zenlog(
			"ZAPI error, trying to delete the backend $id_server in service $service in farm $farmname, it's not possible to delete the backend."
		);

		my $errormsg =
		  "Could not find the backend with ID $id_server of the $farmname farm.";
		my $body = {
			   description => $description,
			   error   => "true",
			   message => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	# no error found, return successful response
	&zenlog(
		"ZAPI success, the backend $id_server in service $service in farm $farmname has been deleted."
	);

	&setFarmRestart( $farmname );

	my $message = "Backend removed";
	my $body = {
				 description => $description,
				 success     => "true",
				 message     => $message,
	};

	if ( &getFarmStatus( $farmname ) eq 'up' )
	{
		$body->{ status } = "needed restart";
		&setFarmRestart( $farmname );
	}

	&httpResponse({ code => 200, body => $body });
}

## FarmGuardian

# PUT /farms/<farmname>/fg Modify the parameters of the farm guardian in a Service
sub modify_gslb_farmguardian    # ( $json_obj, $farmname )
{
	my $json_obj = shift;
	my $farmname = shift;
	my $service  = shift;

	require Zevenet::Farm::Base;
	require Zevenet::Farm::GSLB::Service;
	require Zevenet::Farm::GSLB::FarmGuardian;

	my $description = "Modify farm guardian";

	# validate exist service for gslb farms
	if ( ! grep( /^$service$/, &getGSLBFarmServices( $farmname ) ) )
	{
		my $errormsg = "Invalid service name, please insert a valid value.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};
		&httpResponse( { code => 404, body => $body } );
	}

	# check farm guardian logs are not enabled
	if ( exists ( $json_obj->{ fglog } ) )
	{
		my $errormsg = "GSLS profile do not support Farm Guardian logs.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};
		&httpResponse( { code => 400, body => $body } );
	}

	# Change check script
	if ( exists $json_obj->{ fgscript } )
	{
		if ( &setGSLBFarmGuardianParams( $farmname, $service, 'cmd', $json_obj->{ fgscript } ) == -1 )
		{
			my $errormsg = "Error, trying to modify farm guardian script in farm $farmname, service $service";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};
			&httpResponse( { code => 400, body => $body } );
		}
	}

	# local variables
	my $fgStatus = &getGSLBFarmFGStatus( $farmname, $service );
	my ( $fgTime, $fgCmd ) = &getGSLBFarmGuardianParams( $farmname, $service );

	# Change check time
	if ( exists $json_obj->{ fgtimecheck } )
	{
		if ( &setGSLBFarmGuardianParams( $farmname, $service, 'interval', $json_obj->{ fgtimecheck } ) == -1 )
		{
			my $errormsg = "Error, found trying to enable farm guardian check time in farm $farmname, service $service";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};
			&httpResponse( { code => 400, body => $body } );
		}
	}

	# check if farm guardian is being enabled or disabled
	if ( exists $json_obj->{ fgenabled } )
	{
		# enable farmguardian
		if ( $json_obj->{ fgenabled } eq 'true' && $fgStatus eq 'false' )
		{
			if ( $fgCmd )
			{
				my $errormsg = &enableGSLBFarmGuardian( $farmname, $service, 'true' );
				if ( $errormsg )
				{
					my $errormsg = "Error, trying to enable farm guardian in farm $farmname, service $service.";
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
				my $errormsg = "Error, it's necesary add a check script to enable farm guardian";
				my $body = {
							 description => $description,
							 error       => "true",
							 message     => $errormsg
				};
				&httpResponse( { code => 400, body => $body } );
			}
		}

		# disable farmguardian
		elsif ( $json_obj->{ fgenabled } eq 'false' && $fgStatus eq 'true' )
		{
			my $errormsg = &enableGSLBFarmGuardian( $farmname, $service, 'false' );

			if ( $errormsg )
			{
				my $errormsg = "ZAPI error, trying to disable farm guardian in farm $farmname, service $service";
				my $body = {
							 description => $description,
							 error       => "true",
							 message     => $errormsg
				};
				&httpResponse( { code => 400, body => $body } );
			}
		}
	}

	# no error found, return successful response
	my $errormsg = "Success, some parameters have been changed in farm guardian in farm $farmname.";
	my $body = {
				 description => $description,
				 params      => $json_obj,
				 message     => $errormsg,
	};

	if ( &getFarmStatus( $farmname ) eq 'up' )
	{
		require Zevenet::Farm::Action;

		&setFarmRestart( $farmname );
		$body->{ status } = 'needed restart';
	}

	&httpResponse( { code => 200, body => $body } );
}

1;
