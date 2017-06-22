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

use Zevenet::Net;

sub new_farm    # ( $json_obj )
{
	my $json_obj = shift;

   # 3 Mandatory Parameters ( 1 mandatory for HTTP or GSBL and optional for L4xNAT )
   #
   #	- farmname
   #	- profile
   #	- vip
   #	- vport: optional for L4xNAT and not used in Datalink profile.

	#~ &setFarmName( $json_obj->{ farmname } );
	my $error       = "false";
	my $description = "Creating farm '$json_obj->{ farmname }'";

	# validate FARM NAME
	unless (    $json_obj->{ farmname }
			 && &getValidFormat( 'farm_name', $json_obj->{ farmname } ) )
	{
		my $errormsg =
		  "Error trying to create a new farm, the farm name is required to have alphabet letters, numbers or hypens (-) only.";
		&zenlog( $errormsg );

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
		&zenlog( $errormsg );

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
		&zenlog( $errormsg );

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
		&zenlog( $errormsg );

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
	if (
		 !&getValidPort(
						 $json_obj->{ vip },
						 $json_obj->{ vport },
						 $json_obj->{ profile }
		 )
	  )
	{
		my $errormsg =
		  "Error trying to create a new farm, the virtual port must be an acceptable value and must be available.";
		&zenlog( $errormsg );

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

	if ( $status == -1 )
	{
		&zenlog(
			"ZAPI error, trying to create a new farm $json_obj->{ farmname }, can't be created."
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
			 "ZAPI success, the farm $json_obj->{ farmname } has been created successfully."
		);

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

		&runZClusterRemoteManager( 'farm', 'start', $json_obj->{ farmname } );

		&httpResponse( { code => 201, body => $body } );
	}
}

sub new_farm_backend    # ( $json_obj, $farmname )
{
	my $json_obj = shift;
	my $farmname = shift;

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
				"ZAPI error, trying to create a new backend l4xnat in farm $farmname, invalid IP address and port for a backend, ir can't be blank."
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

		if ( $json_obj->{ max_conns } !~ /^[0-9]+$/ ) # (0 or higher)
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

			# Success
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

			&runZClusterRemoteManager( 'farm', 'restart', $farmname );

			&httpResponse( { code => 201, body => $body } );
		}
		else
		{
			&zenlog(
				"ZAPI error, trying to create a new backend datalink in farm $farmname, it's not possible to create the backend."
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
	my $json_obj = shift;
	my $farmname = shift;
	my $service  = shift;

	# Initial parameters
	my $description = "New service backend";

	# Check that the farm exists
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

	if ( $type eq "http" || $type eq "https" )
	{
		# validate SERVICE
		# Check that the provided service is configured in the farm
		my @services = &getFarmServices( $farmname );

		my $found = 0;
		foreach my $farmservice ( @services )
		{
			#print "service: $farmservice";
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
		my $backendsvs = &getFarmVS( $farmname, $service, "backends" );
		my @be = split ( "\n", $backendsvs );

		my $id;
		foreach my $subl ( @be )
		{
			my @subbe = split ( "\ ", $subl );
			$id = $subbe[1] + 1;
		}

		if ( $id =~ /^$/ )
		{
			$id = 0;
		}

		# validate IP
		unless ( defined $json_obj->{ ip }
				 && &getValidFormat( 'IPv4_addr', $json_obj->{ ip } ) )
		{
			&zenlog(
				"ZAPI error, trying to create a new backend http in service $service in farm $farmname, invalid backend IP value."
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
		unless ( &isValidPortNumber( $json_obj->{ port } ) eq 'true' )
		{
			&zenlog(
				"ZAPI error, trying to create a new backend http in service $service in farm $farmname, invalid IP address and port for a backend, ir can't be blank."
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
				"ZAPI error, trying to create a new backend http in service $service in farm $farmname, invalid weight value for a backend, it must be 1-9."
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
				"ZAPI error, trying to modify the backends in a farm $farmname, invalid timeout."
			);

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
		my $status = &setFarmServer(
									 "",                     $json_obj->{ ip },
									 $json_obj->{ port },    "",
									 "",                     $json_obj->{ weight },
									 $json_obj->{ timeout }, $farmname,
									 $service,
		);

		if ( $status != -1 )
		{
			&zenlog(
				"ZAPI success, a new backend has been created in farm $farmname in service $service with IP $json_obj->{ip}."
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

			if ( &getFarmStatus( $farmname ) eq 'up' )
			{
				&setFarmRestart( $farmname );
				$body->{ status } = 'needed restart';
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
		my $id         = 1;
		my $lb         = &getFarmVS( $farmname, $service, "algorithm" );
		my $backendsvs = &getFarmVS( $farmname, $service, "backends" );
		my @be         = split ( "\n", $backendsvs );

		# validate ALGORITHM
		unless ( $lb eq 'roundrobin' )
		{
			&zenlog(
				   "ZAPI error, this service algorithm does not support adding new backends." );

			# Error
			my $errormsg = "This service algorithm does not support adding new backends.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 400, body => $body } );
		}

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
		my $status =
		  &setGSLBFarmNewBackend( $farmname, $service, $lb, $id, $json_obj->{ ip } );

		if ( $status != -1 )
		{
			&zenlog(
				"ZAPI success, a new backend has been created in farm $farmname in service $service with IP $json_obj->{ip}."
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

			if ( &getFarmStatus( $farmname ) eq 'up' )
			{
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

sub new_farm_service    # ( $json_obj, $farmname )
{
	my $json_obj = shift;
	my $farmname = shift;

	if ( $farmname =~ /^$/ )
	{
		&zenlog(
			"ZAPI error, trying to create a new service in farm $farmname, invalid farm name."
		);

		# Error
		my $errormsg = "Invalid farm name, please insert a valid value.";

		my $body = {
					 description => "New service",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 400, body => $body } );
	}

	# Check that the farm exists
	if ( &getFarmFile( $farmname ) == -1 )
	{
		# Error
		my $errormsg = "The farmname $farmname does not exists.";

		my $body = {
					 description => "New service",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse( { code => 404, body => $body } );
	}

	my $type = &getFarmType( $farmname );

	if ( $type eq "http" || $type eq "https" )
	{
		if ( $json_obj->{ id } =~ /^$/ )
		{
			&zenlog(
				"ZAPI error, trying to create a new service in farm $farmname, invalid service name."
			);

			# Error
			my $errormsg = "Invalid service, please insert a valid value.";

			my $body = {
						 description => "New service",
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 400, body => $body } );
		}

		my $result = &setFarmHTTPNewService( $farmname, $json_obj->{ id } );

		if ( $result eq "0" )
		{
			&zenlog(
				"ZAPI success, a new service has been created in farm $farmname with id $json_obj->{id}."
			);

			# Success
			my $body = {
						 description => "New service " . $json_obj->{ id },
						 params      => { id => $json_obj->{ id } },
			};

			if ( &getFarmStatus( $farmname ) eq 'up' )
			{
				&setFarmRestart( $farmname );
				$body->{ status } = 'needed restart';
			}

			&httpResponse( { code => 201, body => $body } );
		}
		if ( $result eq "2" )
		{
			&zenlog(
				"ZAPI error, trying to create a new service in farm $farmname, new service $json_obj->{id} can't be empty."
			);

			# Error
			my $errormsg = "New service can't be empty.";
			my $body = {
						 description => "New service " . $json_obj->{ id },
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 400, body => $body } );
		}
		if ( $result eq "1" )
		{
			&zenlog(
				"ZAPI error, trying to create a new service in farm $farmname, the service $json_obj->{id} already exists."
			);

			# Error
			my $errormsg = "Service named " . $json_obj->{ id } . " already exists.";
			my $body = {
						 description => "New service " . $json_obj->{ id },
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 400, body => $body } );
		}
		if ( $result eq "3" )
		{
			&zenlog(
				"ZAPI error, trying to create a new service in farm $farmname, the service name $json_obj->{id} is not valid, only allowed numbers,letters and hyphens."
			);

			# Error
			my $errormsg =
			  "Service name is not valid, only allowed numbers, letters and hyphens.";
			my $body = {
						 description => "New service " . $json_obj->{ id },
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 400, body => $body } );
		}
	}

	if ( $type eq "gslb" )
	{
		if ( $json_obj->{ id } =~ /^$/ )
		{
			&zenlog(
				"ZAPI error, trying to create a new service in farm $farmname, invalid service name."
			);

			# Error
			my $errormsg = "Invalid service, please insert a valid value.";
			my $body = {
						 description => "New service " . $json_obj->{ id },
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 400, body => $body } );
		}

		if ( $json_obj->{ algorithm } =~ /^$/ )
		{
			&zenlog(
				"ZAPI error, trying to create a new service in farm $farmname, invalid algorithm."
			);

			# Error
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
		if ( $status != -1 )
		{
			&zenlog(
				"ZAPI success, a new service has been created in farm $farmname with id $json_obj->{id}."
			);

			# Success
			my $body = {
						 description => "New service " . $json_obj->{ id },
						 params      => {
									 id        => $json_obj->{ id },
									 algorithm => $json_obj->{ algorithm }
						 },
			};

			if ( &getFarmStatus( $farmname ) eq 'up' )
			{
				&setFarmRestart( $farmname );
				$body->{ status } = 'needed restart';
			}

			&httpResponse( { code => 201, body => $body } );
		}
		else
		{
			&zenlog(
				"ZAPI error, trying to create a new service in farm $farmname, it's not possible to create the service $json_obj->{id}."
			);

			# Error
			my $errormsg = "It's not possible to create the service " . $json_obj->{ id };
			my $body = {
						 description => "New service " . $json_obj->{ id },
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 400, body => $body } );
		}
	}
}

1;
