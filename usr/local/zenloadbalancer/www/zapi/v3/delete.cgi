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
# curl --tlsv1 -k -X DELETE -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/FarmBORRAME
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
#       -u zapi:<password> https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/FarmHTTP
#
# @apiSampleRequest off
#
#**

sub delete_farm()
{

	$farmname = @_[0];

	use CGI;
	my $q = CGI->new;

	my $j = JSON::XS->new->utf8->pretty( 1 );
	$j->canonical( $enabled );

	if ( $farmname =~ /^$/ )
	{
		&zenlog(
				  "ZAPI error, trying to delete the farm $farmname, invalid farm name." );

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request',
					  'Access-Control-Allow-Origin'  => '*'
		);
		$errormsg = "Invalid farm name, please insert a valid value.";
		my $output = $j->encode(
								 {
								   description => "Delete farm $farmname",
								   error       => "true",
								   message     => $errormsg
								 }
		);
		print $output;
		exit;
	}

	my $newffile = &getFarmFile( $farmname );
	if ( $newffile == -1 )
	{
		&zenlog(
			 "ZAPI error, trying to delete the farm $farmname, the farm name doesn't exist."
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request',
					  'Access-Control-Allow-Origin'  => '*'
		);
		$errormsg = "The farm $farmname doesn't exist, try another name.";
		my $output = $j->encode(
								 {
								   description => "Delete farm $farmname",
								   error       => "true",
								   message     => $errormsg
								 }
		);
		print $output;
		exit;
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
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '200 OK',
					  'Access-Control-Allow-Origin'  => '*'
		);

		my $j = JSON::XS->new->utf8->pretty( 1 );
		$j->canonical( $enabled );

		$message = "The Farm $farmname has been deleted.";
		my $output = $j->encode(
								 {
								   description => "Delete farm $farmname",
								   success     => "true",
								   message     => $message
								 }
		);
		print $output;

	}
	else
	{
		&zenlog(
			"ZAPI error, trying to delete the farm $farmname, the farm hasn't been deleted."
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request',
					  'Access-Control-Allow-Origin'  => '*'
		);
		$errormsg = "The Farm $farmname hasn't been deleted";
		my $output = $j->encode(
								 {
								   description => "Delete farm $farmname",
								   error       => "true",
								   message     => $errormsg
								 }
		);
		print $output;
		exit;

	}
}

#
# curl --tlsv1 -k -X DELETE -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/FarmHTTP/services/service1
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
#       -u zapi:<password> https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/FarmGSLB/services/service1
#
# @apiSampleRequest off
#
#**

sub delete_service()
{

	my ( $farmname, $service ) = @_;

	use CGI;
	my $q = CGI->new;

	my $j = JSON::XS->new->utf8->pretty( 1 );
	$j->canonical( $enabled );

	if ( $farmname =~ /^$/ )
	{
		&zenlog(
			"ZAPI error, trying to delete the service $service in farm $farmname, invalid farm name."
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request',
					  'Access-Control-Allow-Origin'  => '*'
		);
		$errormsg = "Invalid farm name, please insert a valid value.";
		my $output = $j->encode(
								 {
								   description => "Delete service",
								   error       => "true",
								   message     => $errormsg
								 }
		);
		print $output;
		exit;
	}
	
	# Check that the farm exists
	if ( &getFarmFile( $farmname ) == -1 ) {
		# Error
		print $q->header(
		-type=> 'text/plain',
		-charset=> 'utf-8',
		-status=> '404 Not Found',
					  'Access-Control-Allow-Origin'  => '*'
		);
		$errormsg = "The farmname $farmname does not exists.";
		my $output = $j->encode({
				description => "Delete service",
				error => "true",
				message => $errormsg
		});
		print $output;
		exit;

	}
	
	
	if ( $service =~ /^$/ )
	{
		&zenlog(
			"ZAPI error, trying to delete the service $service in farm $farmname, invalid service name."
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request',
					  'Access-Control-Allow-Origin'  => '*'
		);
		$errormsg = "Invalid service name, please insert a valid value.";
		my $output = $j->encode(
								 {
								   description => "Delete service",
								   error       => "true",
								   message     => $errormsg
								 }
		);
		print $output;
		exit;
	}

	my $type = &getFarmType( $farmname );
	
	# Check that the provided service is configured in the farm
	my @services;
	if ($type eq "gslb"){
		@services = &getGSLBFarmServices($farmname);
	} else {
		@services = &getFarmServices($farmname);
	}

	my $found = 0;
	foreach $farmservice (@services) {
		#print "service: $farmservice";
		if ($service eq $farmservice) {
			$found = 1;
			break;
		}
	}
	if ($found eq 0){
		
		# Error
		print $q->header(
		-type=> 'text/plain',
		-charset=> 'utf-8',
		-status=> '400 Bad Request',
					  'Access-Control-Allow-Origin'  => '*'
		);
		$errormsg = "Invalid service name, please insert a valid value.";
		my $output = $j->encode({
				description => "Delete service",
				error => "true",
				message => $errormsg
		});
		print $output;
		exit;
		
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
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request',
					  'Access-Control-Allow-Origin'  => '*'
		);

		my $j = JSON::XS->new->utf8->pretty( 1 );
		$j->canonical( $enabled );

		$message = "The service $service in farm $farmname hasn't been deleted. The service is used by a zone.";
		my $output = $j->encode(
							 {
							   description => "Delete service $service in farm $farmname.",
							   error     => "true",
							   message     => $message
							 }
		);
		print $output;

	}
	elsif ( $return eq 0 )
	{
		&zenlog(
				 "ZAPI success, the service $service in farm $farmname has been deleted." );

		# Success
		&setFarmRestart( $farmname );
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '200 OK',
					  'Access-Control-Allow-Origin'  => '*'
		);

		my $j = JSON::XS->new->utf8->pretty( 1 );
		$j->canonical( $enabled );

		$message = "The service $service in farm $farmname has been deleted.";
		my $output = $j->encode(
							 {
							   description => "Delete service $service in farm $farmname.",
							   success     => "true",
							   message     => $message
							 }
		);
		print $output;

	}
	else
	{
		&zenlog(
			"ZAPI error, trying to delete the service $service in farm $farmname, the service hasn't been deleted."
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request',
					  'Access-Control-Allow-Origin'  => '*'
		);
		$errormsg = "Service $service in farm $farmname hasn't been deleted.";
		my $output = $j->encode(
							  {
								description => "Delete service $service in farm $farmname",
								error       => "true",
								message     => $errormsg
							  }
		);
		print $output;
		exit;
	}
}

#
# curl --tlsv1 -k -X DELETE -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/FarmHTTP/backends/0
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
#   "message" : "The real server with ID 4 of the L4FARM farm has been deleted.",
#   "success" : "true"
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X DELETE -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#       -u zapi:<password> https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/L4FARM/backends/4
#
# @apiSampleRequest off
#
#**

sub delete_backend()
{

	my ( $farmname, $id_server ) = @_;

	use CGI;
	my $q = CGI->new;

	my $j = JSON::XS->new->utf8->pretty( 1 );
	$j->canonical( $enabled );

	if ( $farmname =~ /^$/ )
	{
		&zenlog(
			"ZAPI error, trying to delete the backend $id_server in farm $farmname, invalid farm name."
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request',
					  'Access-Control-Allow-Origin'  => '*'
		);
		$errormsg = "Invalid farm name, please insert a valid value.";
		my $output = $j->encode(
								 {
								   description => "Delete backend",
								   error       => "true",
								   message     => $errormsg
								 }
		);
		print $output;
		exit;
	}
	
	# Check that the farm exists
	if ( &getFarmFile( $farmname ) == -1 ) {
		# Error
		print $q->header(
		-type=> 'text/plain',
		-charset=> 'utf-8',
		-status=> '404 Not Found',
					  'Access-Control-Allow-Origin'  => '*'
		);
		$errormsg = "The farmname $farmname does not exists.";
		my $output = $j->encode({
				description => "Delete backend",
				error => "true",
				message => $errormsg
		});
		print $output;
		exit;

	}
	
	
	
	if ( $id_server =~ /^$/ )
	{
		&zenlog(
			"ZAPI error, trying to delete the backend $id_server in farm $farmname, invalid backend id."
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request',
					  'Access-Control-Allow-Origin'  => '*'
		);
		$errormsg = "Invalid backend id, please insert a valid value.";
		my $output = $j->encode(
								 {
								   description => "Delete backend",
								   error       => "true",
								   message     => $errormsg
								 }
		);
		print $output;
		exit;
	}

	$status = &runFarmServerDelete( $id_server, $farmname );
	if ( $status != -1 )
	{
		# Changes must be applied in iptables
		# my $type = &getFarmType($farmname);
		# if ($type eq "l4xnat"){
		# if ( &getFarmStatus( $farmname ) eq 'up' )
		# {
		# &runFarmStop( $farmname, "false" );
		# &runFarmStart( $farmname, "false" );
		# &sendL4ConfChange( $farmname );
		# }
		# }
		&zenlog(
			   "ZAPI success, the backend $id_server in farm $farmname has been deleted." );

		# Success
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '200 OK',
					  'Access-Control-Allow-Origin'  => '*'
		);

		my $j = JSON::XS->new->utf8->pretty( 1 );
		$j->canonical( $enabled );

		$message =
		  "The real server with ID $id_server of the $farmname farm has been deleted.";
		my $output = $j->encode(
						   {
							 description => "Delete backend $id_server in farm $farmname.",
							 success     => "true",
							 message     => $message
						   }
		);
		print $output;

	}
	else
	{
		&zenlog(
			"ZAPI error, trying to delete the backend $id_server in farm $farmname, it's not possible to delete the real server."
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request',
					  'Access-Control-Allow-Origin'  => '*'
		);
		$errormsg =
		  "It's not possible to delete the real server with ID $id_server of the $farmname farm.";
		my $output = $j->encode(
						   {
							 description => "Delete backend $id_server in farm $farmname.",
							 error       => "true",
							 message     => $errormsg
						   }
		);
		print $output;
		exit;

	}
}

#
# curl --tlsv1 -k -X DELETE -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/newfarmHTTP/services/service1/backends/0
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
#   "message" : "The real server with ID 5 in the service service1 of the farm newfarmHTTP has been deleted.",
#   "success" : "true"
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X DELETE -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#       -u zapi:<password> https://<zenlb_server>:444/zapi/v3/zapi.cgi/farms/newfarmHTTP/services/service1/backends/4
#
# @apiSampleRequest off
#
#**

sub delete_service_backend()
{

	my ( $farmname, $service, $id_server ) = @_;

	use CGI;
	my $q = CGI->new;

	my $j = JSON::XS->new->utf8->pretty( 1 );
	$j->canonical( $enabled );

	if ( $farmname =~ /^$/ )
	{
		&zenlog(
			"ZAPI error, trying to delete the backend $id_server in service $service in farm $farmname, invalid farm name."
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request',
					  'Access-Control-Allow-Origin'  => '*'
		);
		$errormsg = "Invalid farm name, please insert a valid value.";
		my $output = $j->encode(
								 {
								   description => "Delete service backend",
								   error       => "true",
								   message     => $errormsg
								 }
		);
		print $output;
		exit;
	}
	
	# Check that the farm exists
	if ( &getFarmFile( $farmname ) == -1 ) {
		# Error
		print $q->header(
		-type=> 'text/plain',
		-charset=> 'utf-8',
		-status=> '404 Not Found',
					  'Access-Control-Allow-Origin'  => '*'
		);
		$errormsg = "The farmname $farmname does not exists.";
		my $output = $j->encode({
				description => "Delete service backend",
				error => "true",
				message => $errormsg
		});
		print $output;
		exit;

	}

	if ( $service =~ /^$/ )
	{
		&zenlog(
			"ZAPI error, trying to delete the backend $id_server in service $service in farm $farmname, invalid service name."
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request',
					  'Access-Control-Allow-Origin'  => '*'
		);
		$errormsg = "Invalid service name, please insert a valid value.";
		my $output = $j->encode(
								 {
								   description => "Delete service backend",
								   error       => "true",
								   message     => $errormsg
								 }
		);
		print $output;
		exit;
	}
	
	# Check that the provided service is configured in the farm
	my @services;
	if ($type eq "gslb"){
		@services = &getGSLBFarmServices($farmname);
	} else {
		@services = &getFarmServices($farmname);
	}

	my $found = 0;
	foreach $farmservice (@services) {
		#print "service: $farmservice";
		if ($service eq $farmservice) {
			$found = 1;
			break;
		}
	}
	if ($found eq 0){
		
		# Error
		print $q->header(
		-type=> 'text/plain',
		-charset=> 'utf-8',
		-status=> '400 Bad Request',
					  'Access-Control-Allow-Origin'  => '*'
		);
		$errormsg = "Invalid service name, please insert a valid value.";
		my $output = $j->encode({
				description => "Delete service backend",
				error => "true",
				message => $errormsg
		});
		print $output;
		exit;
		
	}

	if ( $id_server =~ /^$/ )
	{
		&zenlog(
			"ZAPI error, trying to delete the backend $id_server in service $service in farm $farmname, invalid backend id."
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request',
					  'Access-Control-Allow-Origin'  => '*'
		);
		$errormsg = "Invalid backend id, please insert a valid value.";
		my $output = $j->encode(
								 {
								   description => "Delete service backend",
								   error       => "true",
								   message     => $errormsg
								 }
		);
		print $output;
		exit;
	}

	my $type = &getFarmType( $farmname );
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
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '200 OK',
					  'Access-Control-Allow-Origin'  => '*'
		);

		my $j = JSON::XS->new->utf8->pretty( 1 );
		$j->canonical( $enabled );

		$message =
		  "The real server with ID $id_server in the service $service of the farm $farmname has been deleted.";
		my $output = $j->encode(
			{
			   description =>
				 "Delete backend with ID $id_server in the service $service of the farm $farmname.",
			   success => "true",
			   message => $message
			}
		);
		print $output;

	}
	else
	{
		&zenlog(
			"ZAPI error, trying to delete the backend $id_server in service $service in farm $farmname, it's not possible to delete the real server."
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request',
					  'Access-Control-Allow-Origin'  => '*'
		);
		$errormsg =
		  "It's not possible to delete the real server with ID $id_server of the $farmname farm.";
		my $output = $j->encode(
			{
			   description =>
				 "Delete backend $id_server in the service $service of the farm $farmname.",
			   error   => "true",
			   message => $errormsg
			}
		);
		print $output;
		exit;

	}
}

1

