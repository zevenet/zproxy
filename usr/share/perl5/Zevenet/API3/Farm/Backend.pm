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
	my $json_obj = shift;
	my $farmname = shift;

	require Zevenet::Farm::Backend;

	# Initial parameters
	my $description = "New farm backend";

	# validate FARM NAME
	if ( &getFarmFile( $farmname ) == -1 )
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
		# Get ID of the new backend
		my $id  = 0;
		my @run = &getFarmServers( $farmname );

		if ( @run > 0 )
		{
			foreach my $l_servers ( @run )
			{
				my @l_serv = split ( ";", $l_servers );
				if ( $l_serv[1] ne "0.0.0.0" )
				{
					if ( $l_serv[0] > $id )
					{
						$id = $l_serv[0];
					}
				}
			}

			if ( $id >= 0 )
			{
				$id++;
			}
		}

		# validate IP
		if ( !&getValidFormat( 'IPv4_addr', $json_obj->{ ip } ) )
		{
			&zenlog(
				"ZAPI error, trying to create a new backend l4xnat in farm $farmname, invalid backend IP value."
			);

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
		unless (    &isValidPortNumber( $json_obj->{ port } ) eq 'true'
				 || $json_obj->{ port } eq '' )
		{
			&zenlog(
				"ZAPI error, trying to create a new backend l4xnat in farm $farmname, invalid IP address and port for a backend, ir can't be blank."
			);

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

		if ( $json_obj->{ max_conns } !~ /^[0-9]+$/ ) # (0 or higher)
		{
			my $errormsg =
			  "Invalid backend connection limit value, accepted values are 0 or higher.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 400, body => $body } );
		}


####### Create backend

		my $status = &setFarmServer(
									 $id,                   $json_obj->{ ip },
									 $json_obj->{ port },   $json_obj->{ max_conns },
									 $json_obj->{ weight }, $json_obj->{ priority },
									 "",                    $farmname
		);

		if ( $status != -1 )
		{
			&zenlog(
				"ZAPI success, a new backend has been created in farm $farmname with IP $json_obj->{ip}."
			);

			$json_obj->{ port }     += 0 if $json_obj->{ port };
			$json_obj->{ weight }   += 0 if $json_obj->{ weight };
			$json_obj->{ priority } += 0 if $json_obj->{ priority };

			# Success
			my $message = "Backend added";
			my $body = {
						 description => $description,
						 params      => {
									 id       => $id,
									 ip       => $json_obj->{ ip },
									 port     => $json_obj->{ port },
									 weight   => $json_obj->{ weight },
									 priority => $json_obj->{ priority },
									 max_conns => $json_obj->{ max_conns },
						 },
						 message => $message,
			};

			if ( eval { require Zevenet::Cluster; } )
			{
				&runZClusterRemoteManager( 'farm', 'restart', $farmname );
			}

			&httpResponse( { code => 201, body => $body } );
		}
		else
		{
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
		my $id  = 0;
		my @run = &getFarmServers( $farmname );
		if ( @run > 0 )
		{
			foreach my $l_servers ( @run )
			{
				my @l_serv = split ( ";", $l_servers );
				if ( $l_serv[1] ne "0.0.0.0" )
				{
					if ( $l_serv[0] > $id )
					{
						$id = $l_serv[0];
					}
				}
			}

			if ( $id >= 0 )
			{
				$id++;
			}
		}

		# validate IP
		if ( !&getValidFormat( 'IPv4_addr', $json_obj->{ ip } ) )
		{
			&zenlog(
				"ZAPI error, trying to create a new backend datalink in farm $farmname, invalid backend IP value."
			);

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
				"ZAPI error, trying to create a new backend in the farm $farmname, invalid interface."
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
				"ZAPI error, trying to create a new backend in the farm $farmname, invalid weight."
			);

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
				"ZAPI error, trying to create a new backend in the farm $farmname, invalid priority."
			);

			my $errormsg = "Invalid priority value, please insert a valid priority value.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg,
			};

			&httpResponse( { code => 400, body => $body } );
		}

####### Create backend

		my $status = &setFarmServer(
									 $id,                      $json_obj->{ ip },
									 $json_obj->{ interface }, "",
									 $json_obj->{ weight },    $json_obj->{ priority },
									 "",                       $farmname
		);

		if ( $status != -1 )
		{
			&zenlog(
				"ZAPI success, a new backend has been created in farm $farmname with IP $json_obj->{ip}."
			);

			my $message = "Backend added";
			my $body = {
				description => $description,
				params      => {
					  id        => $id,
					  ip        => $json_obj->{ ip },
					  interface => $json_obj->{ interface },
					  weight => ( $json_obj->{ weight } ne '' ) ? $json_obj->{ weight } + 0 : undef,
					  priority => ( $json_obj->{ priority } ne '' )
					  ? $json_obj->{ priority } + 0
					  : undef,
				},
				message => $message,
			};

			if ( eval { require Zevenet::Cluster; } )
			{
				&runZClusterRemoteManager( 'farm', 'restart', $farmname );
			}

			&httpResponse( { code => 201, body => $body } );
		}
		else
		{
			&zenlog(
				"ZAPI error, trying to create a new backend datalink in farm $farmname, it's not possible to create the backend."
			);

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
	my $json_obj = shift;
	my $farmname = shift;
	my $service  = shift;

	# Initial parameters
	my $description = "New service backend";

	# Check that the farm exists
	if ( &getFarmFile( $farmname ) == -1 )
	{
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

	if ( $type eq "gslb" && eval { require Zevenet::API3::Farm::GSLB; } )
	{
		&new_gslb_service_backend( $json_obj, $farmname, $service );
	}
	elsif ( $type !~ /(?:https?)/ )
	{
		my $errormsg = "The $type farm profile does not support services.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}

	# HTTP
	require Zevenet::Net::Validate;
	require Zevenet::Farm::Base;
	require Zevenet::Farm::Config;
	require Zevenet::Farm::Backend;
	require Zevenet::Farm::HTTP::Service;

	# validate SERVICE
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

	# Check if the provided service is configured in the farm
	if ( $found eq 0 )
	{
		my $errormsg = "Invalid service name, please insert a valid value.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}

	# get an ID for the new backend
	my $backendsvs = &getFarmVS( $farmname, $service, "backends" );
	my @be = split ( "\n", $backendsvs );
	my $id;

	foreach my $subl ( @be )
	{
		my @subbe = split ( ' ', $subl );
		$id = $subbe[1] + 1;
	}

	$id = 0 if $id eq '';

	# validate IP
	unless ( defined $json_obj->{ ip }
			 && &getValidFormat( 'IPv4_addr', $json_obj->{ ip } ) )
	{
		&zenlog(
			"ZAPI error, trying to create a new backend http in service $service in farm $farmname, invalid backend IP value."
		);

		my $errormsg = "Invalid backend IP value, please insert a valid value.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}

	# validate PORT
	unless ( &isValidPortNumber( $json_obj->{ port } ) eq 'true' )
	{
		&zenlog(
			"ZAPI error, trying to create a new backend http in service $service in farm $farmname, invalid IP address and port for a backend, ir can't be blank."
		);

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
			"ZAPI error, trying to create a new backend http in service $service in farm $farmname, invalid weight value for a backend, it must be 1-9."
		);

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
			"ZAPI error, trying to modify the backends in a farm $farmname, invalid timeout."
		);

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
	my $status = &setFarmServer(
								 "",                     $json_obj->{ ip },
								 $json_obj->{ port },    "",
								 "",                     $json_obj->{ weight },
								 $json_obj->{ timeout }, $farmname,
								 $service,
	);

	# check if there was an error adding a new backend
	if ( $status == -1 )
	{
		my $errormsg =
		    "It's not possible to create the backend with ip "
		  . $json_obj->{ ip }
		  . " and port "
		  . $json_obj->{ port }
		  . " for the $farmname farm";

		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse( { code => 400, body => $body } );
	}

	# no error found, return successful response
	&zenlog(
		"ZAPI success, a new backend has been created in farm $farmname in service $service with IP $json_obj->{ip}."
	);

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

	if ( &getFarmStatus( $farmname ) eq 'up' )
	{
		require Zevenet::Farm::Action;

		&setFarmRestart( $farmname );
		$body->{ status } = 'needed restart';
	}

	&httpResponse( { code => 201, body => $body } );
}

# GET

#GET /farms/<name>/backends
sub backends
{
	my $farmname = shift;

	my $description = "List backends";

	# Check that the farm exists
	if ( &getFarmFile( $farmname ) == -1 )
	{
		my $errormsg = "The farmname $farmname does not exist.";
		my $body = {
				description => $description,
				error => "true",
				message => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	my $type = &getFarmType( $farmname );

	if ( $type eq 'l4xnat' )
	{
		require Zevenet::Farm::Config;
		my $backends = &getFarmBackends( $farmname );

		my $body = {
					description => $description,
					params      => $backends,
		};

		&httpResponse({ code => 200, body => $body });
	}
	elsif ( $type eq 'datalink' )
	{
		require Zevenet::Farm::Config;
		my $backends = &getFarmBackends( $farmname );

		my $body = {
					 description => $description,
					 params      => $backends,
		};

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		my $errormsg = "The farm $farmname with profile $type does not support this request.";
		my $body = {
				description => $description,
				error => "true",
				message => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

#GET /farms/<name>/services/<service>/backends
sub service_backends
{
	my ( $farmname, $service ) = @_;

	my $description = "List service backends";
	my $backendstatus;

	# Check that the farm exists
	if ( &getFarmFile( $farmname ) eq '-1' )
	{
		my $errormsg = "The farmname $farmname does not exist.";
		my $body = {
				description => $description,
				error => "true",
				message => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	my $type = &getFarmType( $farmname );

	if ( $type eq 'gslb' && eval { require Zevenet::API3::Farm::GSLB; } )
	{
		&list_gslb_service_backends( $farmname, $service );
	}
	if ( $type !~ /(?:https?)/ )
	{
		my $errormsg = "The farm profile $type does not support this request.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	# HTTP
	require Zevenet::Farm::Config;
	require Zevenet::Farm::Backend::Maintenance;

	my @services_list = split ' ', &getFarmVS( $farmname );

	# check if the requested service exists
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

	my @be = split ( "\n", &getFarmVS( $farmname, $service, "backends" ) );
	my @backends;

	# populate output array
	foreach my $subl ( @be )
	{
		my @subbe       = split ( ' ', $subl );
		my $id          = $subbe[1] + 0;
		my $maintenance = &getFarmBackendMaintenance( $farmname, $id, $service );

		if ( $maintenance != 0 )
		{
			$backendstatus = "up";
		}
		else
		{
			$backendstatus = "maintenance";
		}

		my $ip   = $subbe[3];
		my $port = $subbe[5] + 0;
		my $tout = $subbe[7];
		my $prio = $subbe[9];

		$tout = $tout eq '-' ? undef: $tout+0;
		$prio = $prio eq '-' ? undef: $prio+0;

		push @backends,
		  {
			id      => $id,
			status  => $backendstatus,
			ip      => $ip,
			port    => $port,
			timeout => $tout,
			weight  => $prio,
		  };
	}

	my $body = {
				description => $description,
				params      => \@backends,
	};

	&httpResponse({ code => 200, body => $body });
}

# PUT

sub modify_backends #( $json_obj, $farmname, $id_server )
{
	my ( $json_obj, $farmname, $id_server ) = @_;

	my $description = "Modify backend";
	my $zapierror;

	# Check that the farm exists
	if ( &getFarmFile( $farmname ) == -1 )
	{
		my $errormsg = "The farmname $farmname does not exists.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 404, body => $body });
	}

	my $error;
	my $type = &getFarmType( $farmname );

	if ( $type eq "l4xnat" )
	{
		require Zevenet::Farm::L4xNAT::Config;

		# Params
		my $l4_farm = &getL4FarmStruct( $farmname );
		my $backend;

		for my $be ( @{ $l4_farm->{'servers'} } )
		{
			if ( $be->{'id'} eq $id_server )
			{
				$backend = $be;
			}
		}

		if ( ! $backend )
		{
			my $errormsg = "Could not find a backend with such id.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg,
			};

			&httpResponse({ code => 404, body => $body });
		}

		if ( exists ( $json_obj->{ ip } ) )
		{
			if ( $json_obj->{ ip } && &getValidFormat('IPv4_addr', $json_obj->{ ip } ) )
			{
				$backend->{ vip } = $json_obj->{ ip };
			}
			else
			{
				$error = "true";
				$zapierror = "Error, trying to modify the backend in the farm $farmname, invalid IP.";
				&zenlog( "Zapi $zapierror" );
			}
		}

		if ( !$error && exists ( $json_obj->{ port } ) )
		{
			if ( &isValidPortNumber( $json_obj->{ port } ) eq 'true' || $json_obj->{ port } == undef )
			{
				$backend->{ vport } = $json_obj->{ port };
			}
			else
			{
				$error = "true";
				$zapierror = "Error, trying to modify the backend in the farm $farmname, invalid port number.";
				&zenlog( "Zapi $zapierror" );
			}
		}

		if ( !$error && exists ( $json_obj->{ weight } ) )
		{
			if ( $json_obj->{ weight } =~ /^\d*[1-9]$/ || $json_obj->{ weight } == undef ) # 1 or higher
			{
				$backend->{ weight } = $json_obj->{ weight };
			}
			else
			{
				$error = "true";
				$zapierror = "Error, trying to modify the backends in a farm $farmname, invalid weight.";
				&zenlog( "Zapi $zapierror" );
			}
		}

		if ( !$error && exists ( $json_obj->{ priority } ) )
		{
			if ( $json_obj->{ priority } =~ /^\d$/ || $json_obj->{ priority } == undef ) # (0-9)
			{
				$backend->{ priority } = $json_obj->{ priority };
			}
			else
			{
				$error = "true";
				$zapierror = "Error, trying to modify the backends in the farm $farmname, invalid priority.";
				&zenlog( "Zapi $zapierror" );
			}
		}

		if ( !$error && exists ( $json_obj->{ max_conns } ) )
		{
			if ( $json_obj->{ max_conns } =~ /^\d+$/ ) # (0 or higher)
			{
				$backend->{ max_conns } = $json_obj->{ max_conns };
			}
			else
			{
				$error = "true";
				$zapierror = "Error, trying to modify the connection limit in the farm $farmname, invalid value.";
				&zenlog( "Zapi $zapierror" );
			}
		}

		if ( !$error )
		{
			my $status = &setL4FarmServer(
										   $backend->{ id },
										   $backend->{ vip },
										   $backend->{ vport },
										   $backend->{ weight },
										   $backend->{ priority },
										   $farmname,
										   $backend->{ max_conns },
			);

			if ( $status == -1 )
			{
				$error = "true";
				$zapierror = "Error, trying to modify the backends in a farm $farmname, it's not possible to modify the backend with ip $json_obj->{ip}.";
				&zenlog( "Zapi $zapierror" );
			}
		}
	}
	elsif ( $type eq "datalink" )
	{
		require Zevenet::Farm::Backend;

		my @run = &getFarmServers( $farmname );
		my $serv_values = $run[$id_server];
		my $be;

		if ( ! $serv_values )
		{
			my $errormsg = "Could not find a backend with such id.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg,
			};

			&httpResponse({ code => 404, body => $body });
		}

		( undef, $be->{ip}, $be->{interface}, $be->{weight}, $be->{priority}, $be->{status} ) = split ( ";", $serv_values );

		# Functions
		if ( exists ( $json_obj->{ ip } ) )
		{
			if ( $json_obj->{ ip } && &getValidFormat('IPv4_addr', $json_obj->{ ip } ) )
			{
				$be->{ ip } = $json_obj->{ ip };
			}
			else
			{
				$error = "true";
				$zapierror = "Error, trying to modify the backends in the farm $farmname, invalid IP.";
				&zenlog( "Zapi $zapierror" );
			}
		}

		if ( !$error && exists ( $json_obj->{ interface } ) )
		{
			require Zevenet::Net::Interface;

			my $valid_interface;

			for my $iface ( @{ &getActiveInterfaceList() } )
			{
				next if $iface->{ vini }; # discard virtual interfaces
				next if !$iface->{ addr }; # discard interfaces without address

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
				$zapierror = "Error, trying to modify the backends in the farm $farmname, invalid interface.";
				&zenlog( "Zapi $zapierror" );
			}
		}

		if ( !$error && exists ( $json_obj->{ weight } ) )
		{
			if ( $json_obj->{ weight } =~ &getValidFormat('natural_num') || $json_obj->{ weight } == undef ) # 1 or higher
			{
				$be->{ weight } = $json_obj->{ weight };
			}
			else
			{
				$error = "true";
				$zapierror = "Error, trying to modify the backends in the farm $farmname, invalid weight.";
				&zenlog( "Zapi $zapierror" );
			}
		}

		if ( !$error && exists ( $json_obj->{ priority } ) )
		{
			if ( $json_obj->{ priority } =~ /^[1-9]$/ || $json_obj->{ priority } == undef ) # (1-9)
			{
				$be->{ priority } = $json_obj->{ priority };
			}
			else
			{
				$error = "true";
				$zapierror = "Error, trying to modify the backends in the farm $farmname, invalid priority.";
				&zenlog( "Zapi $zapierror" );
			}
		}

		if ( !$error )
		{
			my $status =
			  &setFarmServer( $id_server,
							  $be->{ ip },
							  $be->{ interface },
							  "",
							  $be->{ weight },
							  $be->{ priority },
							  "", $farmname );
			if ( $status == -1 )
			{
				$error = "true";
				$zapierror = "Error, trying to modify the backends in the farm $farmname, it's not possible to modify the backend with IP $json_obj->{ip} and interface $json_obj->{interface}.";
				&zenlog( "Zapi $zapierror" );
			}
		}
	}
	else
	{
		my $errormsg = "The $type farm profile has backends only in services.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	if ( !$error )
	{
		&zenlog(
			"ZAPI success, some parameters have been changed in the backend $id_server in farm $farmname."
		);

		my $message = "Backend modified";
		my $body = {
					 description => $description,
					 params      => $json_obj,
					 message     => $message,
		};

		if ( eval { require Zevenet::Cluster; } )
		{
			if ( &getFarmStatus( $farmname ) eq 'up' )
			{
				&runZClusterRemoteManager( 'farm', 'restart', $farmname );
			}
		}

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		&zenlog(
			"Error trying to modify the backend in the farm $farmname, it's not possible to modify the backend."
		);

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

		&httpResponse({ code => 400, body => $body });
	}
}

sub modify_service_backends #( $json_obj, $farmname, $service, $id_server )
{
	my ( $json_obj, $farmname, $service, $id_server ) = @_;

	my $description = "Modify service backend";

	# Check that the farm exists
	if ( &getFarmFile( $farmname ) == -1 )
	{
		my $errormsg = "The farmname $farmname does not exist.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 404, body => $body });
	}

	my $type = &getFarmType( $farmname );

	if ( $type eq "gslb" && eval { require Zevenet::API3::Farm::GSLB; } )
	{
		&modify_gslb_service_backends( $json_obj, $farmname, $service, $id_server );
	}
	elsif ( $type !~ /(?:https?)/ )
	{
		my $errormsg = "The $type farm profile does not support services.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	# HTTP
	require Zevenet::Farm::Action;
	require Zevenet::Farm::Config;
	require Zevenet::Farm::Backend;
	require Zevenet::Farm::HTTP::Service;

	# validate SERVICE
	my @services = &getHTTPFarmServices( $farmname );
	my $found_service = grep { $service eq $_ } @services;

	# check if the service exists
	if ( !$found_service )
	{
		my $errormsg = "Could not find the requested service.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	# validate BACKEND
	my $backendsvs = &getFarmVS( $farmname, $service, "backends" );
	my @be_list = split ( "\n", $backendsvs );
	my $be;

	foreach my $be_line ( @be_list )
	{
		my @current_be = split ( " ", $be_line );

		if ( $current_be[1] == $id_server ) # id
		{
			$current_be[7] = undef if $current_be[7] eq '-'; # timeout
			$current_be[9] = undef if $current_be[9] eq '-'; # priority

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

	# check if the backend was found
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

	# validate BACKEND new ip
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

			&zenlog( "Zapi $errormsg" );
			&httpResponse({ code => 400, body => $body });
		}

		$be->{ ip } = $json_obj->{ ip };
	}

	# validate BACKEND new port
	if ( exists ( $json_obj->{ port } ) )
	{
		require Zevenet::Net::Validate;

		unless ( &isValidPortNumber( $json_obj->{ port } ) eq 'true' )
		{
			my $errormsg = "Error, trying to modify the backends in a farm $farmname, invalid port.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg,
			};

			&zenlog( "Zapi $errormsg" );
			&httpResponse({ code => 400, body => $body });
		}

		$be->{ port } = $json_obj->{ port };
	}

	# validate BACKEND weigh
	if ( exists ( $json_obj->{ weight } ) )
	{
		unless ( $json_obj->{ weight } =~ /^[1-9]$/ )
		{
			my $errormsg = "Error, trying to modify the backends in a farm $farmname, invalid weight.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg,
			};

			&zenlog( "Zapi $errormsg" );
			&httpResponse({ code => 400, body => $body });
		}

		$be->{ priority } = $json_obj->{ weight };
	}

	# validate BACKEND timeout
	if ( exists ( $json_obj->{ timeout } ) )
	{
		unless ( $json_obj->{ timeout } eq ''
			   || ( $json_obj->{ timeout } =~ /^\d+$/ && $json_obj->{ timeout } != 0 ) )
		{
			my $errormsg = "Error, trying to modify the backends in a farm $farmname, invalid timeout.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg,
			};

			&zenlog( "Zapi $errormsg" );
			&httpResponse({ code => 400, body => $body });
		}

		$be->{ timeout } = $json_obj->{ timeout };
	}

	# apply BACKEND change
	my $status = &setFarmServer(
								 $id_server,       $be->{ ip },
								 $be->{ port },    "",
								 "",               $be->{ priority },
								 $be->{ timeout }, $farmname,
								 $service
	);

	# check if there was an error modifying the backend
	if ( $status == -1 )
	{
		my $errormsg = "Error, trying to modify the backends in a farm $farmname, it's not possible to modify the backend with IP $json_obj->{ip} in service $service.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&zenlog( "Zapi $errormsg" );
		&httpResponse({ code => 400, body => $body });
	}

	# no error found, return successful response
	&zenlog(
		"ZAPI success, some parameters have been changed in the backend $id_server in service $service in farm $farmname."
	);

	my $body = {
				 description => $description,
				 params      => $json_obj,
				 message     => "Backend modified",
	};

	if ( &getFarmStatus( $farmname ) eq "up" )
	{
		&setFarmRestart( $farmname );

		$body->{ status } = 'needed restart';
		$body->{ info } =
		  "There're changes that need to be applied, stop and start farm to apply them!";
	}

	&httpResponse({ code => 200, body => $body });
}

# DELETE

# DELETE /farms/<farmname>/backends/<backendid> Delete a backend of a Farm
sub delete_backend # ( $farmname, $id_server )
{
	my ( $farmname, $id_server ) = @_;

	my $description = "Delete backend";

	# validate FARM NAME
	if ( &getFarmFile( $farmname ) == -1 )
	{
		my $errormsg = "The farmname $farmname does not exists.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	# validate FARM TYPE
	my $type = &getFarmType( $farmname );
	unless ( $type eq 'l4xnat' || $type eq 'datalink' )
	{
		my $errormsg = "The $type farm profile has backends only in services.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	require Zevenet::Farm::Backend;

	my @backends = &getFarmServers( $farmname );
	my $backend_line = $backends[$id_server];

	if ( !$backend_line )
	{
		my $errormsg = "Could not find a backend with such id.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 404, body => $body });
	}

	my $status = &runFarmServerDelete( $id_server, $farmname );

	if ( $status != -1 )
	{
		&zenlog(
			   "ZAPI success, the backend $id_server in farm $farmname has been deleted." );

		if ( eval { require Zevenet::Cluster; } )
		{
			&runZClusterRemoteManager( 'farm', 'restart', $farmname );
		}

		my $message = "Backend removed";

		my $body = {
					 description => $description,
					 success     => "true",
					 message     => $message
		};

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		&zenlog(
			"ZAPI error, trying to delete the backend $id_server in farm $farmname, it's not possible to delete the backend."
		);

		# Error
		my $errormsg =
		  "It's not possible to delete the backend with ID $id_server of the $farmname farm.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

#  DELETE /farms/<farmname>/services/<servicename>/backends/<backendid> Delete a backend of a Service
sub delete_service_backend # ( $farmname, $service, $id_server )
{
	my ( $farmname, $service, $id_server ) = @_;

	my $description = "Delete service backend";

	# validate FARM NAME
	if ( &getFarmFile( $farmname ) == -1 )
	{
		my $errormsg = "The farmname $farmname does not exists.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	# validate FARM TYPE
	my $type = &getFarmType( $farmname );

	if ( $type eq 'gslb' && eval { require Zevenet::API3::Farm::GSLB; } )
	{
		&delete_gslb_service_backend( $farmname, $service, $id_server );
	}
	elsif ( $type !~ /(?:https?)/ )
	{
		my $errormsg = "The $type farm profile does not support services.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	# HTTP
	require Zevenet::Farm::Action;
	require Zevenet::Farm::Config;
	require Zevenet::Farm::Backend;
	require Zevenet::Farm::HTTP::Service;

	# validate SERVICE
	my @services = &getHTTPFarmServices($farmname);

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

	my @backends = split ( "\n", &getFarmVS( $farmname, $service, "backends" ) );
	my $be_found = grep { (split ( " ", $_ ))[1] == $id_server } @backends;

	# check if the backend id is available
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

	my $status = &runFarmServerDelete( $id_server, $farmname, $service );

	# check if there was an error deleting the backend
	if ( $status == -1 )
	{
		&zenlog(
			"ZAPI error, trying to delete the backend $id_server in service $service in farm $farmname, it's not possible to delete the backend."
		);

		my $errormsg =
		  "Could not find the backend with ID $id_server of the $farmname farm.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	# no error found, return successful response
	&zenlog(
		"ZAPI success, the backend $id_server in service $service in farm $farmname has been deleted."
	);

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

1;
