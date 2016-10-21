#!/usr/bin/perl -w

# POST /farms/
#
# curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -d '{"profile":"HTTP","vip":"178.62.126.152","vport":"12345","interface":"eth0"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/newfarmHTTP
#
# HTTP status code reference: http://www.restapitutorial.com/httpstatuscodes.html
#
#
#
#####Documentation of POST####
#**
#  @api {post} /farms/<farmname> Create a new Farm
#  @apiGroup Farm Create
#  @apiName PostFarm
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiDescription Create a new Farm with a specific protocol
#  @apiVersion 3.0.0
#
#
#
# @apiSuccess	{Number}	vport			PORT of the farm, where is listening the virtual service. Only mandatory in HTTP and GSLB profile.
# @apiSuccess	{String}	profile			The protocol of the created Farm. The options are: HTTP, L4xNAT, DATALINK and GSLB. Mandatory.
# @apiSuccess   {String}        vip                      IP of the farm, where is listening the virtual service. Mandatory.
#
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "New farm newfarmHTTP",
#   "params" : [
#      {
#         "interface" : "eth0",
#         "name" : "newfarmHTTP",
#         "vport" : 80,
#         "profile" : "HTTP",
#         "vip" : "178.62.126.152"
#      }
#   ]
#}
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        -d '{"profile":"HTTP", "vip":"178.62.126.152", "vport":"80","interface":"eth0"}'
#       https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/newfarmHTTP
#
# @apiSampleRequest off
#
#**

sub new_farm # ( $json_obj )
{
	my $json_obj = shift;

	# 3 Mandatory Parameters ( 1 mandatory for HTTP or GSBL and optional for L4xNAT )
	#
	#	- farmname
	#	- profile
	#	- vip
	#	- vport: optional for L4xNAT and not used in Datalink profile.

	#~ &setFarmName( $json_obj->{ farmname } );
	my $error = "false";
	my $description = "Creating farm '$json_obj->{ farmname }'";

	# FARMNAME validation
	# Valid name and doesn't exist already
	if (   !&getValidFormat( 'farm_name', $json_obj->{ farmname } )
		 || &getFarmType( $json_obj->{ farmname } ) != 1 )
	{
		my $errormsg = "Error trying to create a new farm, the farm name is required to have alphabet letters, numbers or hypens (-) only.";
		&zenlog( $errormsg );

		# Error
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 400, body => $body });
	}

	# Farm PROFILE validation
	if ( $json_obj->{ profile } !~ /^(:?HTTP|GSLB|L4XNAT|DATALINK)$/ )
	{
		my $errormsg = "Error trying to create a new farm, the farm's profile is not supported.";
		&zenlog( $errormsg );

		# Error
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 400, body => $body });
	}

	# VIP validation
	# vip must be available
	if ( ! grep { $_ eq $json_obj->{ vip } } &listallips() )
	{
		my $errormsg = "Error trying to create a new farm, an available virtual IP must be set.";
		&zenlog( $errormsg );

		# Error
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 400, body => $body });
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
	if ( ! &getValidPort( $json_obj->{ vip }, $json_obj->{ vport }, $json_obj->{ profile } ) )
	{
		my $errormsg = "Error trying to create a new farm, the virtual port must be an acceptable value and must be available.";
		&zenlog( $errormsg );

		# Error
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 400, body => $body });
	}

	$json_obj->{ 'interface' } = &getInterfaceOfIp( $json_obj->{ 'vip' } );

	$status = &runFarmCreate( $json_obj->{ profile },
							  $json_obj->{ vip },
							  $json_obj->{ vport },
							  $json_obj->{ farmname },
							  $json_obj->{ interface } );

	if ( $status == -1 )
	{
		&zenlog(
				  "ZAPI error, trying to create a new farm $json_obj->{ farmname }, can't be created." );

		# Error
		my $errormsg = "The $json_obj->{ farmname } farm can't be created";

		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg,
		};

		&httpResponse({ code => 400, body => $body });
	}
	else
	{
		&zenlog( "ZAPI success, the farm $json_obj->{ farmname } has been created successfully." );

		# Success
		my $out_p;

		if ( $json_obj->{ profile } eq "DATALINK" )
		{
			$out_p = {
				name      => $json_obj->{ farmname },
				profile   => $json_obj->{ profile },
				vip       => $json_obj->{ vip },
				interface => $json_obj->{ interface },
			  };
		}
		else
		{
			$out_p = {
				name      => $json_obj->{ farmname },
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

		&httpResponse({ code => 201, body => $body });
	}
}

#
# HTTP:
#
# curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -d '{"ip":"1.1.1.1","port":"80","maxconnections":"1000","weight":"1","timeout":"10","priority":"1","service":"service1"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/newfarmHTTP/backends
#
# GSLB:
#
# curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -d '{"ip":"1.1.1.1","service":"servicio1"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/FarmGSLB/backends
#
#
#
#####Documentation of POST BACKENDS HTTP####
#**
#  @api {post} /farms/<farmname>/backends Create a new Backend in a http|https Farm
#  @apiGroup Farm Create
#  @apiName PostFarmBackendHTTP
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiDescription Create a new Backend of a given HTTP|HTTPS Farm
#  @apiVersion 3.0.0
#
#
#
# @apiSuccess   {String}        ip	                IP of the backend, where is listening the real service.
# @apiSuccess   {Number}        port                     PORT of the backend, where is listening the real service.
# @apiSuccess	{String}	service			Service's name which the backend will be created.
# @apiSuccess	{Number}	timeout			It’s the backend timeout to respond a certain request.
# @apiSuccess   {Number}        weight                   It's the weight value for the current real server.
#
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "New backend 4",
#   "params" : [
#      {
#         "id" : 4,
#         "ip" : "192.168.0.2",
#         "port" : 80,
#         "service" : "service1",
#         "timeout" : 10,
#         "weight" : 1
#      }
#   ]
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        -d '{"timeout":"10", "ip":"192.168.0.1", "port":"80", "weight":"1",
#       "service":"service1"}' https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/FarmHTTP/backends
#
# @apiSampleRequest off
#
#**
#
#
#####Documentation of POST BACKENDS GSLB####
#**
#  @api {post} /farms/<farmname>/backends Create a new Backend in a gslb Farm
#  @apiGroup Farm Create
#  @apiName PostFarmBackendGSLB
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiDescription Create a new Backend of a given GSLB Farm
#  @apiVersion 3.0.0
#
#
#
# @apiSuccess   {String}        ip	                IP of the backend, where is listening the real service.
# @apiSuccess	{String}	service			Service's name which the backend will be created.
#
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "New backend 2",
#   "params" : [
#      {
#         "id" : 2,
#         "ip" : "192.160.1.5",
#         "service" : "sev1"
#      }
#   ]
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        -d '{"ip":"192.168.1.5", "service":"sev1"}'
#       https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/FarmGSLB/backends
#
# @apiSampleRequest off
#
#**

#
#####Documentation of POST BACKENDS L4XNAT####
#**
#  @api {post} /farms/<farmname>/backends Create a new Backend in a l4xnat Farm
#  @apiGroup Farm Create
#  @apiName PostFarmBackendL4XNAT
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiDescription Create a new Backend of a given L4XNAT Farm
#  @apiVersion 3.0.0
#
#
#
# @apiSuccess   {String}        ip               IP of the backend, where is listening the real service.
# @apiSuccess   {Number}        port                    PORT of the backend, where is listening the real service.
# @apiSuccess   {Number}        priority                 It’s the priority value for the current real server.
# @apiSuccess   {Number}        weight                   It's the weight value for the current real server.
#
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "New backend 4",
#   "params" : [
#      {
#         "id" : 4,
#         "ip" : "192.168.1.8",
#         "port" : 79,
#         "priority" : 3,
#         "weight" : 2
#      }
#   ]
#}
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        -d '{"ip":"192.168.1.8", "port":"79", "priority":"3",
#       "weight":"2"}' https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/L4FARM/backends
#
# @apiSampleRequest off
#
#**

#
#####Documentation of POST BACKENDS DATALINK####
#**
#  @api {post} /farms/<farmname>/backends Create a new Backend in a datalink Farm
#  @apiGroup Farm Create
#  @apiName PostFarmBackendDATALINK
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiDescription Create a new Backend of a given DATALINK Farm
#  @apiVersion 3.0.0
#
#
#
# @apiSuccess   {String}        interface               It’s the local network interface where the backend is connected to.
# @apiSuccess   {String}        ip                      IP of the backend, where is listening the real service.
# @apiSuccess   {Number}        priority                        It’s the priority value for the current real server.
# @apiSuccess   {Number}        weight                   It's the weight value for the current real server.
#
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "New backend 3",
#   "params" : [
#      {
#         "id" : 3,
#         "interface" : "eth0",
#         "ip" : "192.168.1.6",
#         "priority" : 3,
#         "weight" : 2
#      }
#   ]
#}
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        -d '{"ip":"192.168.1.5", "interface":"eth0","weight":"2",
#       "priority":"3"}' https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/DATAFARM/backends
#
# @apiSampleRequest off
#**

sub new_farm_backend # ( $json_obj, $farmname )
{
	my $json_obj = shift;
	my $farmname = shift;

	# Initial parameters
	my $description = "New farm backend";
	my $default_priority = 1;
	my $default_weight   = 1;

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

		&httpResponse({ code => 404, body => $body });
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
				if ( @l_serv[1] ne "0.0.0.0" )
				{
					if ( @l_serv[0] > $id )
					{
						$id = @l_serv[0];
					}
				}
			}

			if ( $id >= 0 )
			{
				$id++;
			}
		}

		# validate IP
		if ( ! &getValidFormat('IPv4', $json_obj->{ ip }) )
		{
			&zenlog(
				"ZAPI error, trying to create a new backend l4xnat in farm $farmname, invalid real server IP value."
			);

			# Error
			$error = 1;
			my $errormsg = "Invalid real server IP value, please insert a valid value.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}

		# validate PORT
		unless ( &isValidPortNumber( $json_obj->{ port } ) eq 'true' || $json_obj->{ port } eq '' )
		{
			&zenlog(
				"ZAPI error, trying to create a new backend l4xnat in farm $farmname, invalid IP address and port for a real server, ir can't be blank."
			);

			# Error
			my $errormsg = "Invalid IP address and port for a real server, it can't be blank.";
			my $body = {
									   description => $description,
									   error       => "true",
									   message     => $errormsg
									 };

			&httpResponse({ code => 400, body => $body });
		}

		# validate PRIORITY
		$json_obj->{ priority } = $default_priority if ! exists $json_obj->{ priority };

		if ( $json_obj->{ priority } !~ /^\d$/ ) # (0-9)
		{
			# Error
			my $errormsg =
			  "Invalid real server priority value, please insert a value within the range 0-9.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}

		# validate WEIGHT
		$json_obj->{ weight } = $default_weight if ! exists $json_obj->{ weight };

		if ( $json_obj->{ weight } !~ /^\d*[1-9]$/ ) # 1 or higher
		{
			# Error
			my $errormsg =
			  "Invalid real server weight value, please insert a value greater than 0.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}

####### Create backend

		my $status = &setFarmServer(
									 $id,                   $json_obj->{ ip },
									 $json_obj->{ port },   "",
									 $json_obj->{ weight }, $json_obj->{ priority },
									 "",                    $farmname
		);

		if ( $status != -1 )
		{
			&zenlog(
				"ZAPI success, a new backend has been created in farm $farmname with IP $json_obj->{ip}."
			);

			# Success
			my $body = {
						 description => $description,
						 params      => {
									 id       => $id,
									 ip       => $json_obj->{ ip },
									 port     => $json_obj->{ port } + 0,
									 weight   => $json_obj->{ weight },
									 priority => $json_obj->{ priority },
						 },
			};

			&httpResponse({ code => 201, body => $body });
		}
		else
		{
			# Error
			my $errormsg =
			    "It's not possible to create the real server with ip "
			  . $json_obj->{ ip }
			  . " and port "
			  . $json_obj->{ port }
			  . " for the $farmname farm";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}
	}
	elsif ( $type eq "datalink" )
	{
		# get an ID
		my $id  = 0;
		my @run = &getFarmServers( $farmname );
		if ( @run > 0 )
		{
			foreach $l_servers ( @run )
			{
				my @l_serv = split ( ";", $l_servers );
				if ( @l_serv[1] ne "0.0.0.0" )
				{
					if ( @l_serv[0] > $id )
					{
						$id = @l_serv[0];
					}
				}
			}

			if ( $id >= 0 )
			{
				$id++;
			}
		}

		# validate IP
		if ( ! &getValidFormat('IPv4', $json_obj->{ ip }) )
		{
			&zenlog(
				"ZAPI error, trying to create a new backend datalink in farm $farmname, invalid real server IP value."
			);

			# Error
			my $errormsg = "Invalid real server IP value, please insert a valid value.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}

		# validate INTERFACE
		my $valid_interface;

		for my $iface ( &getActiveInterfaceList() )
		{
			next if $iface->{ vini }; # discard virtual interfaces
			next if !$iface->{ addr }; # discard interfaces without address

			if ( $iface->{ name } eq $json_obj->{ interface } )
			{
				$valid_interface = 'true';
			}
		}

		if ( ! $valid_interface )
		{
			&zenlog(
				"ZAPI error, trying to create a new backend in the farm $farmname, invalid interface."
			);

			my $errormsg = "Invalid interface value, please insert any non-virtual interface.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg,
			};

			&httpResponse({ code => 400, body => $body });
		}

		# validate WEIGHT
		$json_obj->{ weight } = $default_weight if ! exists $json_obj->{ weight };

		if ( $json_obj->{ weight } !~ /^\d+$/ && $json_obj->{ weight } != 1 ) # 1 or higher
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

			&httpResponse({ code => 400, body => $body });
		}

		# validate PRIORITY
		$json_obj->{ priority } = $default_priority if ! exists $json_obj->{ priority };

		if ( $json_obj->{ priority } !~ /^[1-9]$/ ) # (1-9)
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

			&httpResponse({ code => 400, body => $body });
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
			my $body = {
						 description => $description,
						 params      => {
									 id        => $id,
									 ip        => $json_obj->{ ip },
									 interface => $json_obj->{ interface },
									 weight    => $json_obj->{ weight } + 0,
									 priority  => $json_obj->{ priority } + 0
						 },
			};

			&httpResponse({ code => 201, body => $body });
		}
		else
		{
			&zenlog(
				"ZAPI error, trying to create a new backend datalink in farm $farmname, it's not possible to create the real server."
			);

			# Error
			my $errormsg =
			    "It's not possible to create the real server with ip "
			  . $json_obj->{ ip }
			  . " and port "
			  . $json_obj->{ port }
			  . " for the $farmname farm";

			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
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

		&httpResponse({ code => 400, body => $body });
	}
}

sub new_service_backend # ( $json_obj, $farmname, $service )
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

		&httpResponse({ code => 404, body => $body });
	}

	# validate FARM TYPE
	my $type = &getFarmType( $farmname );

	if ( $type eq "http" || $type eq "https" )
	{
		my $default_weight = 5;
		my $default_timeout = '';

		# validate SERVICE
		# Check that the provided service is configured in the farm
		my @services = &getFarmServices($farmname);

		my $found = 0;
		foreach my $farmservice (@services)
		{
			#print "service: $farmservice";
			if ($service eq $farmservice)
			{
				$found = 1;
				last;
			}
		}

		if ($found eq 0)
		{
			# Error
			my $errormsg = "Invalid service name, please insert a valid value.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}

		# get an ID
		my $backendsvs = &getFarmVS( $farmname, $service, "backends" );
		my @be = split ( "\n", $backendsvs );

		foreach my $subl ( @be )
		{
			my @subbe = split ( "\ ", $subl );
			$id = @subbe[1] + 1;
		}

		if ( $id =~ /^$/ )
		{
			$id = 0;
		}

		# validate IP
		if ( ! &getValidFormat('IPv4', $json_obj->{ ip }) )
		{
			&zenlog(
				"ZAPI error, trying to create a new backend http in service $json_obj->{service} in farm $farmname, invalid backend IP value."
			);

			# Error
			my $errormsg = "Invalid backend IP value, please insert a valid value.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}

		# validate PORT
		if ( ! &isValidPortNumber( $json_obj->{ port } ) )
		{
			&zenlog(
				"ZAPI error, trying to create a new backend http in service $json_obj->{service} in farm $farmname, invalid IP address and port for a backend, ir can't be blank."
			);

			# Error
			my $errormsg =
			  "Invalid port for a backend.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}

		# validate WEIGHT
		$json_obj->{ weight } = $default_weight if ! exists $json_obj->{ weight };

		if ( $json_obj->{ weight } !~ /^[1-9]$/ )
		{
			&zenlog(
				"ZAPI error, trying to create a new backend http in service $json_obj->{service} in farm $farmname, invalid weight value for a backend, it must be 1-9."
			);

			# Error
			my $errormsg = "Invalid weight value for a backend, it must be 1-9.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}

		# validate TIMEOUT
		$json_obj->{ timeout } = $default_timeout if ! exists $json_obj->{ timeout };

		unless ( $json_obj->{ timeout } eq '' || ( $json_obj->{ timeout } =~ /^\d+$/ && $json_obj->{ timeout } != 0 ) )
		{
			&zenlog(
				"ZAPI error, trying to modify the backends in a farm $farmname, invalid timeout."
			);

			# Error
			my $errormsg = "Invalid timeout value for a real server, it must be empty or greater than 0.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}

# First param ($id) is an empty string to let function autogenerate the id for the new backend
		$status = &setFarmServer(
								  "",
								  $json_obj->{ ip },
								  $json_obj->{ port },
								  "",
								  "",
								  $json_obj->{ weight },
								  $json_obj->{ timeout },
								  $farmname,
								  $service,
		);

		if ( $status != -1 )
		{
			&zenlog(
				"ZAPI success, a new backend has been created in farm $farmname in service $json_obj->{service} with IP $json_obj->{ip}."
			);

			# Success
			&setFarmRestart( $farmname );
			my $body = {
						 description => $description,
						 params      => {
									 id      => $id,
									 ip      => $json_obj->{ ip },
									 port    => $json_obj->{ port } + 0,
									 weight  => $json_obj->{ weight } + 0,
									 timeout => $json_obj->{ timeout } + 0,
									 service => $json_obj->{ service }
						 },
			};

			&httpResponse({ code => 201, body => $body });
		}
		else
		{
			# Error
			my $errormsg =
			    "It's not possible to create the real server with ip "
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
			my @services = &getFarmServices($farmname);
			my $found_service;

			foreach my $service ( @services )
			{
				if ( $json_obj->{ service } eq $service )
				{
					$found_service = 1;
					last;
				}
			}

			if ( !$found_service )
			{
				# Error
				my $errormsg = "Could not find the requested service.";
				my $body = {
							 description => $description,
							 error       => "true",
							 message     => $errormsg
				};

				&httpResponse({ code => 404, body => $body });
			}
		}

		# Get an ID
		my $id = 1;
		my $lb         = &getFarmVS( $farmname, $json_obj->{ service }, "algorithm" );
		my $backendsvs = &getFarmVS( $farmname, $json_obj->{ service }, "backends" );
		my @be = split ( "\n", $backendsvs );

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
		if ( ! &getValidFormat('IPv4', $json_obj->{ ip } ) )
		{
			$error = "true";
			&zenlog(
				 "ZAPI error, trying to create a new backend in the service $service of the farm $farmname, invalid IP." );

			# Error
			my $errormsg = "Could not find the requested service.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}

		#Adding the backend
		my $status = &setGSLBFarmNewBackend( $farmname, $json_obj->{ service },
										  $lb, $id, $json_obj->{ ip } );
		if ( $status != -1 )
		{
			&zenlog(
				"ZAPI success, a new backend has been created in farm $farmname in service $json_obj->{service} with IP $json_obj->{ip}."
			);

			# Success
			&setFarmRestart( $farmname );
			my $body = {
						 description => $description,
						 params      => {
									 id      => $id,
									 ip      => $json_obj->{ ip },
						 },
			};

			&httpResponse({ code => 201, body => $body });
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

		&httpResponse({ code => 400, body => $body });
	}
}

#
# HTTP:
#
# curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -d '{"id":"servicio123"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/newfarmHTTP/services
#
# GSLB:
#
# curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -d '{"id":"servicio123","algorithm":"roundrobin"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/FarmGSLB/services
#
#
#
#####Documentation of POST SERVICES HTTP####
#**
#  @api {post} /farms/<farmname>/services Create a new service in a http|https Farm
#  @apiGroup Farm Create
#  @apiName PostServiceHTTP
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiDescription Create a service in a given http|https Farm
#  @apiVersion 3.0.0
#
#
#
# @apiSuccess   {String}        id                     Service's name.
#
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "New service newserv",
#   "params" : [
#      {
#         "id" : "newserv"
#      }
#   ]
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        -d '{"id":"newserv"}' https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/FarmHTTP/services
#
# @apiSampleRequest off
#
#**
#
#
#####Documentation of POST SERVICES GSLB####
#**
#  @api {post} /farms/<farmname>/services Create a new service in a gslb Farm
#  @apiGroup Farm Create
#  @apiName PostServiceGSLB
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiDescription Create a new service in a given gslb Farm
#  @apiVersion 3.0.0
#
#
#
# @apiSuccess	{String}	algorithm		Type of load balancing algorithm used in the service. The options are: roundrobin and prio.
# @apiSuccess   {String}        id                     Service's name.
#
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "New service newserv",
#   "params" : [
#      {
#         "algorithm" : "roundrobin",
#         "id" : "newserv"
#      }
#   ]
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        -d '{"algorithm":"roundrobin", "id":"newserv"}'
#       https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/FarmGSLB/services
#
# @apiSampleRequest off
#
#**

sub new_farm_service # ( $json_obj, $farmname )
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

		&httpResponse({ code => 400, body => $body });
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

		&httpResponse({ code => 404, body => $body });
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

			&httpResponse({ code => 400, body => $body });
		}

		my $result = &setFarmHTTPNewService( $farmname, $json_obj->{ id } );

		if ( $result eq "0" )
		{
			&zenlog(
				"ZAPI success, a new service has been created in farm $farmname with id $json_obj->{id}."
			);

			# Success
			&setFarmRestart( $farmname );

			my $body = {
						 description => "New service " . $json_obj->{ id },
						 params      => { id => $json_obj->{ id } },
			};

			&httpResponse({ code => 201, body => $body });
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

			&httpResponse({ code => 400, body => $body });
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

			&httpResponse({ code => 400, body => $body });
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

			&httpResponse({ code => 400, body => $body });
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

			&httpResponse({ code => 400, body => $body });
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

			&httpResponse({ code => 400, body => $body });
		}

		$status = &setGSLBFarmNewService( $farmname,
										  $json_obj->{ id },
										  $json_obj->{ algorithm } );
		if ( $status != -1 )
		{
			&zenlog(
				"ZAPI success, a new service has been created in farm $farmname with id $json_obj->{id}."
			);

			# Success
			&runFarmReload( $farmname );

			my $body = {
						 description => "New service " . $json_obj->{ id },
						 params      => {
									 id        => $json_obj->{ id },
									 algorithm => $json_obj->{ algorithm }
						 },
			};

			&httpResponse({ code => 201, body => $body });
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

			&httpResponse({ code => 400, body => $body });
		}
	}
}

1;
