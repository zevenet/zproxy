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

#
# curl --tlsv1 -k -X DELETE -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/FarmBORRAME
#
#
#####Documentation of DELETE FARM####
#**
#  @api {delete} /farms/<farmname> Delete a Farm
#  @apiGroup Farm Delete
#  @apiName DeleteFarm
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiDescription Delete a given Farm
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Delete farm FarmHTTP",
#   "message" : "The Farm FarmHTTP has been deleted.",
#   "success" : "true"
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X DELETE -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/FarmHTTP
#
# @apiSampleRequest off
#
#**

sub delete_farm # ( $farmname )
{
	my $farmname = shift;

	if ( $farmname =~ /^$/ )
	{
		&zenlog(
				  "ZAPI error, trying to delete the farm $farmname, invalid farm name." );

		# Error
		my $errormsg = "Invalid farm name, please insert a valid value.";
		my $body = {
					 description => "Delete farm $farmname",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	my $newffile = &getFarmFile( $farmname );
	if ( $newffile == -1 )
	{
		&zenlog(
			 "ZAPI error, trying to delete the farm $farmname, the farm name doesn't exist."
		);

		# Error
		my $errormsg = "The farm $farmname doesn't exist, try another name.";
		my $body = {
					 description => "Delete farm $farmname",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	my $stat = &runFarmStop( $farmname, "true" );
	if ( $stat == 0 )
	{
		# Success
	}

	$stat = &runFarmDelete( $farmname );

	if ( $stat == 0 )
	{
		&zenlog( "ZAPI success, the farm $farmname has been deleted." );

		# Success
		my $message = "The Farm $farmname has been deleted.";
		my $body = {
					 description => "Delete farm $farmname",
					 success     => "true",
					 message     => $message
		};

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		&zenlog(
			"ZAPI error, trying to delete the farm $farmname, the farm hasn't been deleted."
		);

		# Error
		my $errormsg = "The Farm $farmname hasn't been deleted";
		my $body = {
					 description => "Delete farm $farmname",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

#
# curl --tlsv1 -k -X DELETE -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/FarmHTTP/services/service1
#
#
#####Documentation of DELETE SERVICE####
#**
#  @api {delete} /farms/<farmname>/services/<servicename> Delete a service of a Farm
#  @apiGroup Farm Delete
#  @apiName DeleteService
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiParam {String} servicename  Service name, unique ID.
#  @apiDescription Delete a given zone of a http, https or gslb Farm
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Delete service service1 in farm FarmGSLB",
#   "message" : "The service service1 in farm FarmGSLB has been deleted.",
#   "success" : "true"
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X DELETE -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/FarmGSLB/services/service1
#
# @apiSampleRequest off
#
#**

sub delete_service # ( $farmname, $service )
{
	my ( $farmname, $service ) = @_;

	if ( $farmname =~ /^$/ )
	{
		&zenlog(
			"ZAPI error, trying to delete the service $service in farm $farmname, invalid farm name."
		);

		# Error
		my $errormsg = "Invalid farm name, please insert a valid value.";
		my $body = {
					 description => "Delete service",
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
					 description => "Delete service",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}

	if ( $service =~ /^$/ )
	{
		&zenlog(
			"ZAPI error, trying to delete the service $service in farm $farmname, invalid service name."
		);

		# Error
		my $errormsg = "Invalid service name, please insert a valid value.";
		my $output = {
					   description => "Delete service",
					   error       => "true",
					   message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	my $type = &getFarmType( $farmname );
	
	# Check that the provided service is configured in the farm
	my @services;
	if ($type eq "gslb")
	{
		@services = &getGSLBFarmServices($farmname);
	}
	else
	{
		@services = &getFarmServices($farmname);
	}

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
				description => "Delete service",
				error => "true",
				message => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
	
	
	if ( $type eq "http" || $type eq "https" )
	{
		$return = &deleteFarmService( $farmname, $service );
	}
	if ( $type eq "gslb" )
	{
		$return = &setGSLBFarmDeleteService( $farmname, $service );
	}

	if ( $return eq -2 )
	{
		&zenlog(
				 "ZAPI error, the service $service in farm $farmname hasn't been deleted. The service is used by a zone." );

		# Error
		my $message = "The service $service in farm $farmname hasn't been deleted. The service is used by a zone.";
		my $body = {
					 description => "Delete service $service in farm $farmname.",
					 error       => "true",
					 message     => $message
		};

		&httpResponse({ code => 400, body => $body });
	}
	elsif ( $return eq 0 )
	{
		&zenlog(
				 "ZAPI success, the service $service in farm $farmname has been deleted." );

		# Success
		&setFarmRestart( $farmname );
		my $message = "The service $service in farm $farmname has been deleted.";
		my $body = {
					 description => "Delete service $service in farm $farmname.",
					 success     => "true",
					 message     => $message
		};

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		&zenlog(
			"ZAPI error, trying to delete the service $service in farm $farmname, the service hasn't been deleted."
		);

		# Error
		my $errormsg = "Service $service in farm $farmname hasn't been deleted.";
		my $body = {
					 description => "Delete service $service in farm $farmname",
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}
}

#
# curl --tlsv1 -k -X DELETE -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/FarmHTTP/backends/0
#
#
#####Documentation of DELETE BACKEND####
#**
#  @api {delete} /farms/<farmname>/backends/<backendid> Delete a backend of a Farm
#  @apiGroup Farm Delete
#  @apiName DeleteBackend
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiParam {Number} backendid  Backend ID, unique ID.
#  @apiDescription Delete a given backend of a datalink or l4xnat Farm
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Delete backend 4 in farm L4FARM.",
#   "message" : "The backend with ID 4 of the L4FARM farm has been deleted.",
#   "success" : "true"
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X DELETE -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/L4FARM/backends/4
#
# @apiSampleRequest off
#
#**

sub delete_backend # ( $farmname, $id_server )
{
	my ( $farmname, $id_server ) = @_;

	my $description = "Delete backend";

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
	unless ( $type eq 'l4xnat' || $type eq 'datalink' )
	{
		# Error
		my $errormsg = "The $type farm profile has backends only in services.";
		my $body = {
					 description => $description,
					 error       => "true",
					 message     => $errormsg
		};

		&httpResponse({ code => 400, body => $body });
	}

	my @backends = &getFarmServers( $farmname );
	my $backend_line = $backends[$id_server];

	if ( !$backend_line )
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

	my $status = &runFarmServerDelete( $id_server, $farmname );

	if ( $status != -1 )
	{
		&zenlog(
			   "ZAPI success, the backend $id_server in farm $farmname has been deleted." );

		# Success
		#~ my $message = "The backend with ID $id_server of the $farmname farm has been deleted.";
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

#
# curl --tlsv1 -k -X DELETE -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/newfarmHTTP/services/service1/backends/0
#
#
#####Documentation of DELETE BACKEND in a SERVICE####
#**
#  @api {delete} /farms/<farmname>/services/<servicename>/backends/<backendid> Delete a backend of a Service
#  @apiGroup Farm Delete
#  @apiName DeleteBackendServ
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiParam {String} servicename Service name, unique ID.
#  @apiParam {Number} backendid  Backend ID, unique ID.
#  @apiDescription Delete a given backend in a service of a http, https or gslb Farm
#  @apiVersion 3.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Delete backend with ID 5 in the service service1 of the farm newfarmHTTP.",
#   "message" : "The backend with ID 5 in the service service1 of the farm newfarmHTTP has been deleted.",
#   "success" : "true"
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X DELETE -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#        https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/newfarmHTTP/services/service1/backends/4
#
# @apiSampleRequest off
#
#**

sub delete_service_backend # ( $farmname, $service, $id_server )
{
	my ( $farmname, $service, $id_server ) = @_;

	my $description = "Delete service backend";

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
	unless ( $type eq 'http' || $type eq 'https' || $type eq 'gslb' )
	{
		# Error
		my $errormsg = "The $type farm profile has backends only in services.";
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

		# validate ALGORITHM
		unless ( &getFarmVS( $farmname, $service, "algorithm" ) eq 'roundrobin' )
		{
			&zenlog(
				 "ZAPI error, this service algorithm does not support removing backends." );

			# Error
			my $errormsg = "Could not find the requested service.";
			my $body = {
						 description => $description,
						 error       => "true",
						 message     => $errormsg
			};

			&httpResponse({ code => 400, body => $body });
		}
	}

	my $status;

	if ( $type eq "http" || $type eq "https" )
	{
		$status = &runFarmServerDelete( $id_server, $farmname, $service );
	}
	if ( $type eq "gslb" )
	{
		$status = &remFarmServiceBackend( $id_server, $farmname, $service );
	}

	if ( $status != -1 )
	{
		&zenlog(
			"ZAPI success, the backend $id_server in service $service in farm $farmname has been deleted."
		);

		# Success
		&setFarmRestart( $farmname );
		#~ my $message = "The backend with ID $id_server in the service $service of the farm $farmname has been deleted.";
		my $message = "Backend removed";
		my $body = {
			   description => $description,
			   success => "true",
			   message => $message
			};

		&httpResponse({ code => 200, body => $body });
	}
	else
	{
		&zenlog(
			"ZAPI error, trying to delete the backend $id_server in service $service in farm $farmname, it's not possible to delete the backend."
		);

		# Error
		my $errormsg =
		  "Could not find the backend with ID $id_server of the $farmname farm.";
		my $body = {
			   description => $description,
			   error   => "true",
			   message => $errormsg
		};

		&httpResponse({ code => 404, body => $body });
	}
}

1;
