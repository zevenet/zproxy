#!/usr/bin/perl -w

##############################################################################
#
#     This file is part of the Zen Load Balancer Enterprise Edition software
#     package.
#
#     Copyright (C) 2014 SOFINTEL IT ENGINEERING SL, Sevilla (Spain)
#
#     This file cannot be distributed, released in public domain and/or for
#     commercial purposes.
#
###############################################################################

# PUT /farms/FarmHTTP
#
#

sub modify_farm # ( $json_obj, $farmname )
{
	my $json_obj = shift;
	my $farmname = shift;

	if ( $farmname =~ /^$/ )
	{
		&zenlog(
			"ZAPI error, trying to modify a farm $farmname, invalid farmname, can't be blank."
		);

		# Error
		my $errormsg = "Invalid farm name, please insert a valid value.";
		my $body = {
					 description => "Modify backend",
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
					 description => "Modify farm",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	my $type = &getFarmType( $farmname );

	if ( $type eq "http" || $type eq "https" )
	{
		require "/usr/local/zenloadbalancer/www/zapi/v3/put_http.cgi";
		&modify_http_farm( $json_obj, $farmname );
	}

	if ( $type eq "l4xnat" )
	{
		require "/usr/local/zenloadbalancer/www/zapi/v3/put_l4.cgi";
		&modify_l4xnat_farm( $json_obj, $farmname );
	}

	if ( $type eq "datalink" )
	{
		require "/usr/local/zenloadbalancer/www/zapi/v3/put_datalink.cgi";
		&modify_datalink_farm( $json_obj, $farmname );
	}

	if ( $type eq "gslb" )
	{
		require "/usr/local/zenloadbalancer/www/zapi/v3/put_gslb.cgi";
		&modify_gslb_farm( $json_obj, $farmname );
	}
}

# Modify Backends
#
# curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -d '{"ip":"192.168.0.10","port":"88","priority":"2","weight":"1"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/L4XNAT/backends/1
#
#####Documentation of PUT BACKEND L4####
#**
#  @api {put} /farms/<farmname>/backends/<backendid> Modify a l4xnat Backend
#  @apiGroup Farm Modify
#  @apiName PutBckL4
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiParam {Number} backendid Backend ID, unique ID.
#  @apiDescription Modify the params of a backend in a L4XNAT Farm
#  @apiVersion 3.0.0
#
#
#
# @apiSuccess	{String}		ip			IP of the backend, where is listening the real service.
# @apiSuccess	{Number}		port			PORT of the backend, where is listening the real service.
# @apiSuccess   {Number}        priority		It’s the priority value for the current backend.
# @apiSuccess   {Number}        weight		It's the weight value for the current backend.
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Modify backend 1 in farm L4FARM",
#   "params" : [
#      {
#         "priority" : "2"
#      },
#      {
#         "ip" : "192.168.0.10"
#      },
#      {
#         "weight" : "1"
#      },
#      {
#         "port" : "88"
#      }
#   ]
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        -d '{"ip":"192.168.0.10","port":"88","priority":"2",
#       "weight":"1"}' https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/L4FARM/backends/1
#
# @apiSampleRequest off
#
#**
#####Documentation of PUT BACKEND DATALINK####
#**
#  @api {put} /farms/<farmname>/backends/<backendid> Modify a datalink Backend
#  @apiGroup Farm Modify
#  @apiName PutBckDATALINK
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiParam {Number} backendid Backend ID, unique ID.
#  @apiDescription Modify the params of a backend in a DATALINK Farm
#  @apiVersion 3.0.0
#
#
#
# @apiSuccess   {String}        ip                       IP of the backend, where is listening the real service.
# @apiSuccess   {String}        interface	It’s the local network interface where the backend is connected to.
# @apiSuccess   {Number}        priority         It’s the priority value for the current backend.
# @apiSuccess   {Number}        weight           It's the weight value for the current backend.
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Modify backend 1 in farm DATAFARM",
#   "params" : [
#      {
#         "priority" : "2"
#      },
#      {
#         "interface" : "eth0"
#      },
#      {
#         "ip" : "192.168.0.11"
#      },
#      {
#         "weight" : "1"
#      },
#   ]
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        -d '{"ip":"192.168.0.10","interface":"eth0","priority":"2",
#       "weight":"1"}' https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/DATAFARM/backends/1
#
# @apiSampleRequest off
#
#**
#####Documentation of PUT BACKEND HTTP####
#**
#  @api {put} /farms/<farmname>/backends/<backendid> Modify a http|https Backend
#  @apiGroup Farm Modify
#  @apiName PutBckHTTP
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiParam {Number} backendid Backend ID, unique ID.
#  @apiDescription Modify the params of a backend in a service of a HTTP|HTTPS Farm
#  @apiVersion 3.0.0
#
#
#
# @apiSuccess   {String}        ip                       IP of the backend, where is listening the real service.
# @apiSuccess   {String}        port	        PORT of the backend, where is listening the real service.
# @apiSuccess   {String}        service		The service where the backend belongs.
# @apiSuccess	{Number}	timeout		It’s the backend timeout to respond a certain request.
# @apiSuccess   {Number}        weight           It's the weight value for the current backend.
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Modify backend 1 in farm FarmHTTP",
#   "info" : "There're changes that need to be applied, stop and start farm to apply them!",
#   "params" : [
#      {
#         "timeout" : "12"
#      },
#      {
#         "ip" : "192.168.0.10"
#      },
#      {
#         "weight" : "1"
#      },
#      {
#         "service" : "sev2"
#      },
#      {
#         "port" : "88"
#      }
#   ]
#}
#
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        -d '{"ip":"192.168.0.10","port":"88","timeout":"12","service":"sev2",
#       "weight":"1"}' https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/FarmHTTP/backends/1
#
# @apiSampleRequest off
#
#**

#####Documentation of PUT BACKEND GSLB####
#**
#  @api {put} /farms/<farmname>/backends/<backendid> Modify a gslb Backend
#  @apiGroup Farm Modify
#  @apiName PutBckGSLB
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiParam {Number} backendid Backend ID, unique ID.
#  @apiDescription Modify the params of a backend in a service of a GSLB Farm
#  @apiVersion 3.0.0
#
#
#
# @apiSuccess   {String}        ip                       IP of the backend, where is listening the real service.
# @apiSuccess   {String}        service			The service where the backend belongs.
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Modify backend 1 in farm FarmGSLB",
#   "params" : [
#      {
#         "ip" : "192.168.0.10"
#      },
#      {
#         "service" : "sev2"
#      }
#   ]
#}
#
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        -d '{"ip":"192.168.0.10","service":"sev2"}'
#       https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/FarmGSLB/backends/1
#
# @apiSampleRequest off
#
#**

sub modify_backends #( $json_obj, $farmname, $id_server )
{
	my ( $json_obj, $farmname, $id_server ) = @_;

	my $description = "Modify backend";

	# Check that the farm exists
	if ( &getFarmFile( $farmname ) == -1 )
	{
		# Error
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
			# Error
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
			if ( &getValidFormat('IPv4', $json_obj->{ ip } ) )
			{
				$backend->{ vip } = $json_obj->{ ip };
			}
			else
			{
				$error = "true";
				&zenlog(
						 "Error trying to modify the backend in the farm $farmname, invalid IP." );
			}
		}

		if ( !$error && exists ( $json_obj->{ port } ) )
		{
			if ( &isValidPortNumber( $json_obj->{ port } ) eq 'true' || $json_obj->{ port } eq '' )
			{
				$backend->{ vport } = $json_obj->{ port };
			}
			else
			{
				$error = "true";
				&zenlog(
					  "Error trying to modify the backend in the farm $farmname, invalid port number."
				);
			}
		}

		if ( !$error && exists ( $json_obj->{ weight } ) )
		{
			if ( $json_obj->{ weight } =~ /^\d*[1-9]$/ ) # 1 or higher
			{
				$backend->{ weight } = $json_obj->{ weight };
			}
			else
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify the backends in a farm $farmname, invalid weight."
				);
			}
		}

		if ( !$error && exists ( $json_obj->{ priority } ) )
		{
			if ( $json_obj->{ priority } =~ /^\d$/ ) # (0-9)
			{
				$backend->{ priority } = $json_obj->{ priority };
			}
			else
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify the backends in the farm $farmname, invalid priority."
				);
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
			);

			if ( $status == -1 )
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify the backends in a farm $farmname, it's not possible to modify the backend with ip $json_obj->{ip}."
				);
			}
		}
	}
	elsif ( $type eq "datalink" )
	{
		my @run = &getFarmServers( $farmname );
		my $serv_values = @run[$id_server];
		my $be;

		if ( ! $serv_values )
		{
			# Error
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
			if ( &getValidFormat('IPv4', $json_obj->{ ip } ) )
			{
				$be->{ ip } = $json_obj->{ ip };
			}
			else
			{
				$error = "true";
				&zenlog(
					 "ZAPI error, trying to modify the backends in the farm $farmname, invalid IP." );
			}
		}

		if ( !$error && exists ( $json_obj->{ interface } ) )
		{
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
				&zenlog(
					"ZAPI error, trying to modify the backends in the farm $farmname, invalid interface."
				);
			}
		}

		if ( !$error && exists ( $json_obj->{ weight } ) )
		{
			if ( $json_obj->{ weight } !~ /^\d+$/ && $json_obj->{ weight } != 1 ) # 1 or higher
			{
				$be->{ weight } = $json_obj->{ weight };
			}
			else
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify the backends in the farm $farmname, invalid weight."
				);
			}
		}

		if ( !$error && exists ( $json_obj->{ priority } ) )
		{
			if ( $json_obj->{ priority } =~ /^[1-9]$/ ) # (1-9)
			{
				$be->{ priority } = $json_obj->{ priority };
			}
			else
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify the backends in the farm $farmname, invalid priority."
				);
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
				&zenlog(
					"ZAPI error, trying to modify the backends in the farm $farmname, it's not possible to modify the backend with IP $json_obj->{ip} and interface $json_obj->{interface}."
				);
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

		&httpResponse({ code => 404, body => $body });
	}

	# Print params
	if ( !$error )
	{
		&zenlog(
			"ZAPI success, some parameters have been changed in the backend $id_server in farm $farmname."
		);

		# Success
		my $body = {
					 description => $description,
					 params      => $json_obj
		};

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		&zenlog(
			"Error trying to modify the backend in the farm $farmname, it's not possible to modify the backend."
		);

		# Error
		my $errormsg = "Errors found trying to modify farm $farmname";
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
		# Error
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

	if ( $type eq "http" || $type eq "https" )
	{
		# validate SERVICE
		{
			my @services = &getFarmServices($farmname);
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

				&httpResponse({ code => 404, body => $body });
			}
		}

		# validate BACKEND
		my $be;
		{
			my $backendsvs = &getFarmVS( $farmname, $service, "backends" );
			my @be_list = split ( "\n", $backendsvs );

			foreach my $be_line ( @be_list )
			{
				my @current_be = split ( " ", $be_line );

				if ( $current_be[1] == $id_server )
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

				&httpResponse({ code => 404, body => $body });
			}
		}

		# Functions
		if ( exists ( $json_obj->{ ip } ) )
		{
			if ( &getValidFormat('IPv4', $json_obj->{ ip } ) )
			{
				$be->{ ip } = $json_obj->{ ip };
			}
			else
			{
				$error = "true";
				&zenlog(
					 "ZAPI error, trying to modify the backends in a farm $farmname, invalid IP." );
			}
		}

		if ( !$error && exists ( $json_obj->{ port } ) )
		{
			if ( &isValidPortNumber( $json_obj->{ port } eq 'true' ) )
			{
				$be->{ port } = $json_obj->{ port };
			}
			else
			{
				$error = "true";
				&zenlog(
					  "ZAPI error, trying to modify the backends in a farm $farmname, invalid port."
				);
			}
		}

		if ( !$error && exists ( $json_obj->{ weight } ) )
		{
			if ( $json_obj->{ weight } =~ /^[1-9]$/ )
			{
				$be->{ priority } = $json_obj->{ weight };
			}
			else
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify the backends in a farm $farmname, invalid weight."
				);
			}
		}

		if ( !$error && exists ( $json_obj->{ timeout } ) )
		{
			if ( $json_obj->{ timeout } eq '' || ( $json_obj->{ timeout } =~ /^\d+$/ && $json_obj->{ timeout } != 0 ) )
			{
				$be->{ timeout } = $json_obj->{ timeout };
			}
			else
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify the backends in a farm $farmname, invalid timeout."
				);
			}
		}

		if ( !$error )
		{
			my $status = &setFarmServer(
										 $id_server,       $be->{ ip },
										 $be->{ port },    "",
										 "",               $be->{ priority },
										 $be->{ timeout }, $farmname,
										 $service
			);

			if ( $status == -1 )
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify the backends in a farm $farmname, it's not possible to modify the backend with IP $json_obj->{ip} in service $service."
				);
			}
			else
			{
				&setFarmRestart( $farmname );
			}
		}
	}
	elsif ( $type eq "gslb" )
	{
		# validate SERVICE
		{
			my @services = &getGSLBFarmServices($farmname);
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

				&httpResponse({ code => 404, body => $body });
			}
		}

		# validate BACKEND
		my $be;
		{
			my $backendsvs = &getFarmVS( $farmname, $service, "backends" );
			my @be_list = split ( "\n", $backendsvs );

			foreach my $be_line ( @be_list )
			{
				$be_line =~ s/^\s+//;
				next if !$be_line;

				my @current_be = split ( " => ", $be_line );

				if ( $current_be[0] == $id_server )
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

				&httpResponse({ code => 404, body => $body });
			}
		}

		my $lb = &getFarmVS( $farmname, $service, "algorithm" );

		# Functions
		if ( exists ( $json_obj->{ ip } ) )
		{
			if ( &getValidFormat('IPv4', $json_obj->{ ip } ) )
			{
				$be->{ ip } = $json_obj->{ ip };
			}
			else
			{
				$error = "true";
				&zenlog(
					 "ZAPI error, trying to modify the backends in a farm $farmname, invalid IP." );
			}
		}

		if ( !$error )
		{
			my $status =
			  &setGSLBFarmNewBackend( $farmname, $service, $lb, $id_server, @subbe[1] );

			if ( $status == -1 )
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify the backends in a farm $farmname, it's not possible to modify the backend with IP $json_obj->{ip} in service $service."
				);
			}
			else
			{
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

		&httpResponse({ code => 404, body => $body });
	}

	# Print params
	if ( !$error )
	{
		&zenlog(
			"ZAPI success, some parameters have been changed in the backend $id_server in service $service in farm $farmname."
		);

		# Success
		# Get farm status. If farm is down the restart is not required.
		my $status = &getFarmStatus( $farmname);
		my $body;

		if ( $status eq "up" )
		{
			$body = {
				description => $description,
				params      => $json_obj,
				status      => 'needed restart',
				info =>
				  "There're changes that need to be applied, stop and start farm to apply them!"
			};
		}
		if ( $status eq "down" )
		{
			$body = {
					  description => "Modify backend $id_server in farm $farmname",
					  params      => $json_obj,
			};
		}

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		&zenlog(
			"ZAPI error, trying to modify the backends in a farm $farmname, it's not possible to modify the backend."
		);

		# Error
		my $errormsg = "Errors found trying to modify farm $farmname";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}



# curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -d '{"vhost":"www.marca.com","urlp":"^/myapp$","redirect":"https://google.es","persistence":"URL","ttl":"120","sessionid":"sidd","leastrep":"false","httpsb":"false"}' https://178.62.126.152:444/zapi/v1/zapi.cgi/farms/FarmHTTP/services/sev1

#
#
#
#####Documentation of PUT SERVICE GSLB####
#**
#  @api {put} /farms/<farmname>/services/<serviceid> Modify a gslb Service
#  @apiGroup Farm Modify
#  @apiName PutServGSLB
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiParam {String} serviceid Service name, unique ID.
#  @apiDescription Modify the params of a service in a GSLB Farm
#  @apiVersion 3.0.0
#
#
#
# @apiSuccess   {Number}        deftcpport		This is the health check TCP port that the service is going to check in order to determine that the backend service is alive.
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Modify service sev2 in farm FarmGSLB",
#   "params" : [
#      {
#         "deftcpport" : "80"
#      }
#   ]
#}
#
#
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        -d '{"deftcpport":"80"}'
#       https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/FarmGSLB/services/sev2
#
# @apiSampleRequest off
#
#**
#
#####Documentation of PUT SERVICE HTTP####
#**
#  @api {put} /farms/<farmname>/services/<serviceid> Modify a http|https Service
#  @apiGroup Farm Modify
#  @apiName PutServHTTP
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiParam {String} serviceid Service name, unique ID.
#  @apiDescription Modify the params of a service in a HTTP|HTTPS Farm
#  @apiVersion 3.0.0
#
#
#
# @apiSuccess   {String}    vhost			This field specifies the condition determined by the domain name through the same virtual IP and port defined by a HTTP farm.
# @apiSuccess	{String}	urlp			This field allows to determine a web service regarding the URL the client is requesting through a specific URL pattern which will be syntactically checked.
# @apiSuccess	{String}	redirect		This field behaves as a special backend, as the client request is answered by a redirect to a new URL automatically.
# @apiSuccess	{String}	redirecttype	There are two options: default or append. With default option, the url is taken as an absolute host and path to redirect to. With append option, the original request path will be appended to the host and path you specified.
# @apiSuccess	{String}	cookieinsert	This field enable the cookie options for backends. The options are true or false.
# @apiSuccess	{String}	cookiename		This field is the cookie name (session ID). Enable cookieinsert field is required.
# @apiSuccess	{String}	cookiedomain	This field is the cookie domain. Enable cookieinsert field is required.
# @apiSuccess	{String}	cookiepath		This field is the cookie path. Enable cookieinsert field is required.
# @apiSuccess	{Number}	cookiettl		This field is the max time of life for a cookie (in seconds). Enable cookieinsert field is required.
# @apiSuccess	{String}	persistence		This parameter defines how the HTTP service is going to manage the client session. The options are: nothing, IP, BASIC, URL, PARM, COOKIE and HEADER.
# @apiSuccess	{Number}	ttl				Only with persistence. This value indicates the max time of life for an inactive client session (max session age) in seconds.
# @apiSuccess	{String}	sessionid		This field is the URL, COOKIE or HEADER parameter name that will be analyzed by the farm service and will manage the client session.
# @apiSuccess	{String}	leastresp		This field enable the least responde balancing method. the options are true or false.
# @apiSuccess	{String}	httpsb			This checkbox indicates to the farm that the backends servers defined in the current service are using the HTTPS language and then the data will be encrypted before to be sent. The options are true or false.
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Modify service sev2 in farm FarmHTTP",
#   "info" : "There're changes that need to be applied, stop and start farm to apply them!",
#   "params" : [
#      {
#         "urlp" : "^/myapp1$"
#      },
#      {
#         "ttl" : "125"
#      },
#      {
#         "leastresp" : "true"
#      },
#      {
#         "persistence" : "URL"
#      },
#      {
#         "redirecttype" : "append"
#      },
#      {
#         "redirect" : "http://zenloadbalancer.com"
#      },
#      {
#         "cookieinsert" : "true"
#      },
#      {
#         "cookiename" : "SESSIONID"
#      },
#	   {
#         "cookiedomain" : "domainname.com"
#      },
#      {
#         "cookiepath" : "/"
#      },
#      {
#         "cookiettl" : "10"
#      },
#      {
#         "httpsb" : "true"
#      },
#      {
#         "redirect" : "http://zenloadbalancer.com"
#      },
#      {
#         "vhost" : "www.mywebserver.com"
#      },
#      {
#         "sessionid" : "sid"
#      }
#   ]
#}
#
#
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        -d '{"vhost":"www.mywebserver.com","urlp":"^/myapp1$","persistence":"URL",
#       "redirect":"http://zenloadbalancer.com","ttl":"125","sessionid":"sid","leastresp":"true",
#       "httpsb":"true"}' https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/FarmHTTP/services/sev2
#
# @apiSampleRequest off
#
#**

sub modify_services # ( $json_obj, $farmname, $service )
{
	my ( $json_obj, $farmname, $service ) = @_;

	my $output_params;

	# validate FARM NAME
	if ( &getFarmFile( $farmname ) == -1 ) {
		# Error
		my $errormsg = "The farmname $farmname does not exists.";

		my $body = {
					 description => "Modify service",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	# validate FARM TYPE
	my $type = &getFarmType( $farmname );
	unless ( $type eq 'gslb' || $type eq 'http' || $type eq 'https' )
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

	# validate SERVICE
	{
		my @services;

		if ($type eq "gslb")
		{
			@services = &getGSLBFarmServices($farmname);
		}
		else
		{
			@services = &getFarmServices($farmname);
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

			&httpResponse({ code => 404, body => $body });
		}
	}

	my $error = "false";

	if ( $type eq "http" || $type eq "https" )
	{
		# Functions
		if ( exists ( $json_obj->{ vhost } ) )
		{
			&setFarmVS( $farmname, $service, "vs", $json_obj->{ vhost } );
		}

		if ( exists ( $json_obj->{ urlp } ) )
		{
			&setFarmVS( $farmname, $service, "urlp", $json_obj->{ urlp } );
		}

		$redirecttype = &getFarmVS( $farmname, $service, "redirecttype" );

		if ( exists ( $json_obj->{ redirect } ) )
		{
			my $redirect = uri_unescape( $json_obj->{ redirect } );

			if ( $redirect =~ /^http\:\/\//i || $redirect =~ /^https:\/\//i || $redirect eq '' )
			{
				&setFarmVS( $farmname, $service, "redirect", $redirect );
			}
			else
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify the service $service in a farm $farmname, invalid redirect."
				);
			}
		}

		$redirect = &getFarmVS( $farmname, $service, "redirect" );

		if ( exists ( $json_obj->{ redirecttype } ) )
		{
			my $redirecttype = $json_obj->{ redirecttype };

			if ( $redirecttype eq "default" )
			{
				&setFarmVS( $farmname, $service, "redirect", $redirect );
			}
			elsif ( $redirecttype eq "append" )
			{
				&setFarmVS( $farmname, $service, "redirectappend", $redirect );
			}
			elsif ( exists $json_obj->{ redirect } && $json_obj->{ redirect } )
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify the service $service in a farm $farmname, invalid redirecttype."
				);
			}
		}

		if ( exists ( $json_obj->{ persistence } ) )
		{
			if (
					$json_obj->{ persistence } =~ /^nothing|IP|BASIC|URL|PARM|COOKIE|HEADER$/ )
			{
				$session = $json_obj->{ persistence };
				$status = &setFarmVS( $farmname, $service, "session", "$session" );
				if ( $status != 0 )
				{
					$error = "true";
					&zenlog(
						"ZAPI error, trying to modify the service $service in a farm $farmname, it's not possible to change the persistence parameter."
					);
				}
			}
		}

		if ( exists ( $json_obj->{ ttl } ) )
		{
			if ( $json_obj->{ ttl } =~ /^$/ )
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify the service $service in a farm $farmname, invalid ttl, can't be blank."
				);
			}
			elsif ( $json_obj->{ ttl } =~ /^\d+/ )
			{
				$status = &setFarmVS( $farmname, $service, "ttl", "$json_obj->{ttl}" );
				if ( $status != 0 )
				{
					$error = "true";
					&zenlog(
						"ZAPI error, trying to modify the service $service in a farm $farmname, it's not possible to change the ttl parameter."
					);
				}
			}
			else
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify the service $service in a farm $farmname, invalid ttl, must be numeric."
				);
			}
		}

		if ( exists ( $json_obj->{ sessionid } ) )
		{
			&setFarmVS( $farmname, $service, "sessionid", $json_obj->{ sessionid } );
		}

		if ( exists ( $json_obj->{ leastresp } ) )
		{
			if ( $json_obj->{ leastresp } =~ /^$/ )
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify the service $service in a farm $farmname, invalid leastresp, can't be blank."
				);
			}
			elsif ( $json_obj->{ leastresp } =~ /^true|false$/ )
			{
				if ( ( $json_obj->{ leastresp } eq "true" ) )
				{
					&setFarmVS( $farmname, $service, "dynscale", $json_obj->{ leastresp } );
				}
				elsif ( ( $json_obj->{ leastresp } eq "false" ) )
				{
					&setFarmVS( $farmname, $service, "dynscale", "" );
				}
			}
			else
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify the service $service in a farm $farmname, invalid leastresp."
				);
			}
		}

		if ( exists ( $json_obj->{ cookieinsert } ) )
		{
			if ( $json_obj->{ cookieinsert } =~ /^$/ )
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify the service $service in a farm $farmname, invalid cookieinsert, can't be blank."
				);
			}
			elsif ( $json_obj->{ cookieinsert } =~ /^true|false$/ )
			{
				if ( ( $json_obj->{ cookieinsert } eq "true" ) )
				{
					&setFarmVS( $farmname, $service, "cookieins", $json_obj->{ cookieinsert } );
				}
				elsif ( ( $json_obj->{ cookieinsert } eq "false" ) )
				{
					&setFarmVS( $farmname, $service, "cookieins", "" );
				}
			}
			else
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify the service $service in a farm $farmname, invalid cookieinsert."
				);
			}
		}

		#~ &zenlog("farmname:$farmname service:$service cookiedomain:$json_obj->{ cookiedomain } cookiename:$json_obj->{ cookiename } cookiepath:$json_obj->{ cookiepath } cookieinsert: $json_obj->{ cookieinsert } cookiettl:$json_obj->{ cookiettl }");

		if ( $json_obj->{ cookieinsert } eq "true" )
		{
			if ( exists ( $json_obj->{ cookiedomain } ) )
			{
				#~ &zenlog("farmname:$farmname service:$service cookiedomain:$json_obj->{ cookiedomain }");
				&setFarmVS( $farmname, $service, "cookieins-domain", $json_obj->{ cookiedomain } );
			}

			if ( exists ( $json_obj->{ cookiename } ) )
			{
				#~ &zenlog("farmname:$farmname service:$service cookiename:$json_obj->{ cookiename }");
				&setFarmVS( $farmname, $service, "cookieins-name", $json_obj->{ cookiename } );
			}

			if ( exists ( $json_obj->{ cookiepath } ) )
			{
				#~ &zenlog("farmname:$farmname service:$service cookiepath:$json_obj->{ cookiepath }");
				&setFarmVS( $farmname, $service, "cookieins-path", $json_obj->{ cookiepath } );
			}

			if ( exists ( $json_obj->{ cookiettl } ) )
			{
				if ( $json_obj->{ cookiettl } =~ /^$/ )
				{
					$error = "true";
					&zenlog(
						"ZAPI error, trying to modify the service $service in a farm $farmname, invalid cookiettl, can't be blank."
					);
				}
				else
				{
					&setFarmVS( $farmname, $service, "cookieins-ttlc", $json_obj->{ cookiettl } );
				}
			}
		}

		if ( exists ( $json_obj->{ httpsb } ) )
		{
			if ( $json_obj->{ httpsb } =~ /^$/ )
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify the service $service in a farm $farmname, invalid httpsb, can't be blank."
				);
			}
			elsif ( $json_obj->{ httpsb } =~ /^true|false$/ )
			{
				if ( ( $json_obj->{ httpsb } eq "true" ) )
				{
					&setFarmVS( $farmname, $service, "httpsbackend", $json_obj->{ httpsb } );
				}
				elsif ( ( $json_obj->{ httpsb } eq "false" ) )
				{
					&setFarmVS( $farmname, $service, "httpsbackend", "" );
				}
			}
			else
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify the service $service in a farm $farmname, invalid httpsb."
				);
			}
		}

		$output_params = &getHttpFarmService( $farmname, $service );
	}

	if ( $type eq "gslb" )
	{
		# Functions
		if ( $json_obj->{ deftcpport } =~ /^$/ )
		{
			$error = "true";
			&zenlog(
				"ZAPI error, trying to modify the service $service in a farm $farmname, invalid deftcpport, can't be blank."
			);
		}
		if ( $error eq "false" )
		{
			&setFarmVS( $farmname, $service, "dpc", $json_obj->{ deftcpport } );
			if ( $? eq 0 )
			{
				&runFarmReload( $farmname );
			}
			else
			{
				$error = "true";
				&zenlog(
					"ZAPI error, trying to modify the service $service in a farm $farmname, it's not possible to change the deftcpport parameter."
				);
			}
		}

		# FIXME: Read gslb configuration instead of returning input
		$output_params = $json_obj;
	}

	# Print params
	if ( $error ne "true" )
	{
		&setFarmRestart( $farmname );

		&zenlog(
			"ZAPI success, some parameters have been changed in service $service in farm $farmname."
		);

		# Success
		my $body = {
			description => "Modify service $service in farm $farmname",
			params      => $output_params,
			status      => 'needed restart',
			info =>
			  "There're changes that need to be applied, stop and start farm to apply them!"
		};

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		&zenlog(
			"ZAPI error, trying to modify the zones in a farm $farmname, it's not possible to modify the service $service."
		);

		# Error
		$errormsg = "Errors found trying to modify farm $farmname";

		my $body = {
					 description => "Modify service $service in farm $farmname",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

1;
