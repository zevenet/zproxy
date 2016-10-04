#!/usr/bin/perl -w

# POST /farms/
#
# curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin -d '{"profile":"HTTP","vip":"178.62.126.152","vport":"12345","interface":"eth0"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/newfarmHTTP
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
# @apiSuccess   {String}        interface                Interface where the farm will be created. Mandatory.
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
#       -u zapi:<password> -d '{"profile":"HTTP", "vip":"178.62.126.152", "vport":"80","interface":"eth0"}'
#       https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/newfarmHTTP
#
# @apiSampleRequest off
#
#**

sub new_farm # ( $json_obj, $farmname )
{
	my $json_obj = shift;
	my $farmname = shift;

	$farmname =~ s/\ //g;
	$farmname =~ s/\_//g;

	&setFarmName( $farmname );
	$error = "false";

	if ( $json_obj->{ vip } eq "" )
	{
		&zenlog(
			"ZAPI error, trying to create a new farm $farmname, invalid virtual IP value, it can't be blank."
		);

		# Error
		my $errormsg = "Please especify a Virtual IP";

		my $body = {
					 description => "New farm $farmname",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	if ( $farmname =~ /^$/ )
	{
		&zenlog(
				  "ZAPI error, trying to create a new farm $farmname, invalid farm name." );

		# Error
		my $errormsg = "The farm name can't be empty";

		my $body = {
					 description => "New farm $farmname",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	if ( $farmprotocol =~ /HTTP|HTTPS|GSLB|L4XNAT|DATALINK/ )
	{
		if ( &isnumber( $json_obj->{ vport } ) eq "true" )
		{
			my $inuse = &checkport( $json_obj->{ vip }, $json_obj->{ vport } );

			if ( $inuse eq "true" )
			{
				&zenlog(
					"ZAPI error, trying to create a new farm $farmname, the virtual port $json_obj->{vport} in virtual IP .$json_obj->{vip}. is in use."
				);

				# Error
				my $errormsg =
				    "The Virtual Port "
				  . $json_obj->{ vport }
				  . " in Virtual IP "
				  . $json_obj->{ vip }
				  . " is in use, select another port or add another Virtual IP";

				my $body = {
							 description => "New farm $farmname",
							 error       => "true",
							 message     => $errormsg
				};

				&httpResponse({ code => 422, body => $body });
			}
		}
		else
		{
			&zenlog(
				"ZAPI error, trying to create a new farm $farmname, invalid virtual port value, must be numeric."
			);

			# Error
			my $errormsg = "Invalid Virtual Port value, it must be numeric";

			my $body = {
						 description => "New farm $farmname",
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}
	}

	my $fdev = $json_obj->{ interface };

	$status = &runFarmCreate( $json_obj->{ profile },
							  $json_obj->{ vip },
							  $json_obj->{ vport },
							  $farmname, $fdev );
	if ( $status == -1 )
	{
		&zenlog(
				  "ZAPI error, trying to create a new farm $farmname, can't be created." );

		# Error
		my $errormsg = "The $farmname farm can't be created";

		my $body = {
					 description => "New farm $farmname",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
	if ( $status == -2 )
	{
		&zenlog(
			"ZAPI error, trying to create a new farm $farmname, the farm already exists, set a different farm name."
		);

		# Error
		my $errormsg =
		  "The $farmname farm already exists, please set a different farm name";

		my $body = {
					 description => "New farm $farmname",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 422, body => $body });
	}
	&zenlog( "ZAPI success, the farm $farmname has been created successfully." );

	if ( $json_obj->{ vport } eq "" )
	{
		$vport = "*";
	}
	else
	{
		$vport = $json_obj->{ vport };
	}

	# Success
	my @out_p;

	if ( $json_obj->{ profile } eq "DATALINK" )
	{
		push @out_p,
		  {
			name      => $farmname,
			profile   => $json_obj->{ profile },
			vip       => $json_obj->{ vip },
			interface => $fdev
		  };
	}
	else
	{
		push @out_p,
		  {
			name      => $farmname,
			profile   => $json_obj->{ profile },
			vip       => $json_obj->{ vip },
			vport     => $vport,
			interface => $fdev
		  };
	}

	my $body = {
				 description => "New farm $farmname",
				 params      => \@out_p
	};

	&httpResponse({ code => 201, body => $body });
}

#
# HTTP:
#
# curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin -d '{"ip":"1.1.1.1","port":"80","maxconnections":"1000","weight":"1","timeout":"10","priority":"1","service":"service1"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/newfarmHTTP/backends
#
# GSLB:
#
# curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin -d '{"ip":"1.1.1.1","service":"servicio1"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/FarmGSLB/backends
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
#       -u zapi:<password> -d '{"timeout":"10", "ip":"192.168.0.1", "port":"80", "weight":"1",
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
#       -u zapi:<password> -d '{"ip":"192.168.1.5", "service":"sev1"}'
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
#       -u zapi:<password> -d '{"ip":"192.168.1.8", "port":"79", "priority":"3",
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
#       -u zapi:<password> -d '{"ip":"192.168.1.5", "interface":"eth0","weight":"2",
#       "priority":"3"}' https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/DATAFARM/backends
#
# @apiSampleRequest off
#**

sub new_farm_backend # ( $json_obj, $farmname )
{
	my $json_obj = shift;
	my $farmname = shift;

	# Initial parameters
	my $priority = 1;
	my $weight   = 1;

	if ( $farmname =~ /^$/ )
	{
		&zenlog(
			"ZAPI error, trying to create a new backend in farm $farmname, invalid farm name."
		);

		# Error
		my $errormsg = "Invalid farm name, please insert a valid value.";
		my $body = {
					 description => "New backend",
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
					 description => "New backend",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	my $type = &getFarmType( $farmname );

	if ( $type eq "http" || $type eq "https" )
	{
		# Check that the provided service is configured in the farm
		my @services = &getFarmServices($farmname);

		my $found = 0;
		foreach my $farmservice (@services)
		{
			#print "service: $farmservice";
			if ($json_obj->{service} eq $farmservice)
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
						 description => "Modify farm guardian",
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}

		my $backendsvs = &getFarmVS( $farmname, $json_obj->{ service }, "backends" );
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

		if ( &ipisok( $json_obj->{ ip } ) eq "false" )
		{
			&zenlog(
				"ZAPI error, trying to create a new backend http in service $json_obj->{service} in farm $farmname, invalid real server IP value."
			);

			# Error
			$error = 1;
			my $errormsg = "Invalid real server IP value, please insert a valid value.";
			my $body = {
						 description => "New backend $id",
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}

		if ( $json_obj->{ ip } =~ /^$/ || $json_obj->{ port } =~ /^$/ )
		{
			&zenlog(
				"ZAPI error, trying to create a new backend http in service $json_obj->{service} in farm $farmname, invalid IP address and port for a real server, ir can't be blank."
			);

			# Error
			my $errormsg =
			  "Invalid IP address and port for a real server, it can't be blank.";
			my $body = {
						 description => "New backend $id",
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}

		if ( $json_obj->{ priority }
			 && ( $json_obj->{ priority } > 9 || $json_obj->{ priority } < 1 ) )
		{
			&zenlog(
				"ZAPI error, trying to create a new backend http in service $json_obj->{service} in farm $farmname, invalid weight value for a real server, it must be 1-9."
			);

			# Error
			my $errormsg = "Invalid weight value for a real server, it must be 1-9.";
			my $body = {
						 description => "New backend $id",
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
								  $json_obj->{ service }
		);

		if ( $status != -1 )
		{
			&zenlog(
				"ZAPI success, a new backend has been created in farm $farmname in service $json_obj->{service} with IP $json_obj->{ip}."
			);

			# Success
			&setFarmRestart( $farmname );
			my $body = {
						 description => "New backend $id",
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
						 description => "New backend $id",
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 400, body => $body } );
		}

	}

	if ( $type eq "gslb" )
	{
		$id = 1;
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

		# Check that the provided service is configured in the farm
		my @services = &getGSLBFarmServices($farmname);
		
		my $found = 0;
		foreach my $service (@services)
		{
			print "service: $service";
			if ($json_obj->{service} eq $service)
			{
				$found = 1;
				last;
			}
		}

		if ($found eq 0)
		{
			# Error
			my $errormsg = "Invalid service, please insert a valid value.";
			my $body = {
						 description => "New backend $id",
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}

		if ( $json_obj->{ service } =~ /^$/ )
		{
			&zenlog(
				"ZAPI error, trying to create a new backend gslb in service $json_obj->{service} farm $farmname, invalid service."
			);

			# Error
			my $errormsg = "Invalid service, please insert a valid value.";
			my $body = {
						 description => "New backend $id",
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}

		$status = &setGSLBFarmNewBackend( $farmname, $json_obj->{ service },
										  $lb, $id, $json_obj->{ ip } );
		if ( $status != -1 )
		{
			&zenlog(
				"ZAPI success, a new backend has been created in farm $farmname in service $json_obj->{service} with IP $json_obj->{ip}."
			);

			# Success
			&setFarmRestart( $farmname );
			my $body = {
						 description => "New backend $id",
						 params      => {
									 id      => $id,
									 ip      => $json_obj->{ ip },
									 service => $json_obj->{ service }
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
						 description => "New backend $id",
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse( { code => 400, body => $body } );
		}
	}

	if ( $type eq "l4xnat" )
	{
		######## Check errors

		if ( $farmname =~ /^$/ )
		{
			&zenlog(
				"ZAPI error, trying to create a new backend l4xnat in farm $farmname, invalid farm name."
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

		if ( &ipisok( $json_obj->{ ip } ) eq "false" )
		{
			&zenlog(
				"ZAPI error, trying to create a new backend l4xnat in farm $farmname, invalid real server IP value."
			);

			# Error
			$error = 1;
			my $errormsg = "Invalid real server IP value, please insert a valid value.";
			my $body = {
						 description => "New backend $id",
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}

		if ( $json_obj->{ ip } =~ /^$/ || $json_obj->{ port } =~ /^$/ )
		{
			&zenlog(
				"ZAPI error, trying to create a new backend l4xnat in farm $farmname, invalid IP address and port for a real server, ir can't be blank."
			);

			# Error
			my $errormsg = "Invalid IP address and port for a real server, it can't be blank.";
			my $body = {
									   description => "New backend $id",
									   error       => "true",
									   message     => $errormsg
									 };

			&httpResponse({ code => 400, body => $body });
		}

		if ( exists ( $json_obj->{ priority } ) )
		{
			$priority = $json_obj->{ priority };

			if ( $priority =~ /^$/ )
			{
				$priority = 1;
			}
			elsif ( $priority < 0 )
			{
				# Error
				my $errormsg =
				  "Invalid real server priority value, please insert a value greater than or equal to 0.";
				my $body = {
							 description => "New backend $id",
							 error       => "true",
							 message     => $errormsg
				};

				&httpResponse({ code => 400, body => $body });
			}
			elsif ( $priority > 9 )
			{
				# Error
				my $errormsg =
				  "Invalid real server priority value, please insert a value less than or equal to 9.";
				my $body = {
							 description => "New backend $id",
							 error       => "true",
							 message     => $errormsg
				};

				&httpResponse({ code => 400, body => $body });
			}
		}

		if ( exists ( $json_obj->{ weight } ) )
		{
			$weight = $json_obj->{ weight };

			if ( $weight =~ /^$/ )
			{
				$weight = 1;
			}
			elsif ( $weight < 1 )
			{
				# Error
				my $errormsg =
				  "Invalid real server weight value, please insert a value greater than 0.";
				my $body = {
							 description => "New backend $id",
							 error       => "true",
							 message     => $errormsg
				};

				&httpResponse({ code => 400, body => $body });
			}
		}

####### Create backend

		$status = &setFarmServer( $id,
								  $json_obj->{ ip },
								  $json_obj->{ port },
								  "", $weight, $priority, "", $farmname );
		if ( $status != -1 )
		{
			&zenlog(
				"ZAPI success, a new backend has been created in farm $farmname with IP $json_obj->{ip}."
			);

			# Success
			my $body = {
						 description => "New backend $id",
						 params      => {
									 id       => $id,
									 ip       => $json_obj->{ ip },
									 port     => $json_obj->{ port } + 0,
									 weight   => $weight,
									 priority => $priority
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
						 description => "New backend $id",
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}
	}

	if ( $type eq "datalink" )
	{
		######## Check errors

		if ( $farmname =~ /^$/ )
		{
			&zenlog(
				"ZAPI error, trying to create a new backend datalink in farm $farmname, invalid farm name."
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

		if ( &ipisok( $json_obj->{ ip } ) eq "false" )
		{
			&zenlog(
				"ZAPI error, trying to create a new backend datalink in farm $farmname, invalid real server IP value."
			);

			# Error
			$error = 1;
			my $errormsg = "Invalid real server IP value, please insert a valid value.";
			my $body = {
						 description => "New backend $id",
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}

		if ( $json_obj->{ ip } =~ /^$/ )
		{
			&zenlog(
				"ZAPI error, trying to create a new backend datalink in farm $farmname, invalid farm name, it can't be blank."
			);

			# Error
			my $errormsg = "Invalid IP address for a real server, it can't be blank.";
			my $body = {
						 description => "New backend $id",
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}

####### Create backend

		$status = &setFarmServer(
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
						 description => "New backend $id",
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
						 description => "New backend $id",
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}

	}
}

#
# HTTP:
#
# curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin -d '{"id":"servicio123"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/newfarmHTTP/services
#
# GSLB:
#
# curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin -d '{"id":"servicio123","algorithm":"roundrobin"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/FarmGSLB/services
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
#       -u zapi:<password> -d '{"id":"newserv"}' https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/FarmHTTP/services
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
#       -u zapi:<password> -d '{"algorithm":"roundrobin", "id":"newserv"}'
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
