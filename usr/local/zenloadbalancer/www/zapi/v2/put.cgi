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

# PUT /farms/FarmTCP
#
#

our $origin;
if ( $origin ne 1 )
{
	exit;
}

sub modify_farm()
{

	$farmname = @_[0];

	my $out_p = [];

	use CGI;
	use JSON;

	my $q        = CGI->new;
	my $json     = JSON->new;
	my $data     = $q->param( 'PUTDATA' );
	my $json_obj = $json->decode( $data );

	my $j = JSON::XS->new->utf8->pretty( 1 );
	$j->canonical( $enabled );
	if ( $farmname =~ /^$/ )
	{
		&logfile(
			"ZAPI error, trying to modify a farm $farmname, invalid farmname, can't be blank."
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request'
		);
		$errormsg = "Invalid farm name, please insert a valid value.";
		my $output = $j->encode(
								 {
								   description => "Modify backend",
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
		-status=> '404 Not Found'
		);
		$errormsg = "The farmname $farmname does not exists.";
		my $output = $j->encode({
				description => "Modify farm",
				error => "true",
				message => $errormsg
		});
		print $output;
		exit;

	}

	my $type = &getFarmType( $farmname );

	if ( $type eq "http" || $type eq "https" )
	{
		require "/usr/local/zenloadbalancer/www/zapi/v2/put_http.cgi";
	}

	if ( $type eq "l4xnat" )
	{
		require "/usr/local/zenloadbalancer/www/zapi/v2/put_l4.cgi";
	}

	if ( $type eq "datalink" )
	{
		require "/usr/local/zenloadbalancer/www/zapi/v2/put_datalink.cgi";
	}

	if ( $type eq "gslb" )
	{
		require "/usr/local/zenloadbalancer/www/zapi/v2/put_gslb.cgi";
	}

	if ( $type eq "tcp" || $type eq "udp" )
	{
		require "/usr/local/zenloadbalancer/www/zapi/v2/put_tcp.cgi";
	}
}

# Modify Backends
#
# curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin -d '{"ip":"192.168.0.10","port":"88","maxcon":"1000","priority":"2","weight":"1"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/TCP/backends/1
#
#####Documentation of PUT BACKEND TCP####
#**
#  @api {put} /farms/<farmname>/backends/<backendid> Modify a tcp|udp Backend
#  @apiGroup Farm Modify
#  @apiName PutBckTCP
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiParam {Number} backendid Backend ID, unique ID.
#  @apiDescription Modify the params of a backend in a TCP|UDP Farm
#  @apiVersion 2.0.0
#
#
#
# @apiSuccess	{String}		ip			IP of the backend, where is listening the real service.
# @apiSuccess	{Number}		port			PORT of the backend, where is listening the real service.
# @apiSuccess	{Number}		maxcon		It’s the max number of concurrent connections that the current real server will be able to receive.
# @apiSuccess   {Number}        	priority		It’s the priority value for the current real server.
# @apiSuccess   {Number}        	weight		It's the weight value for the current real server.
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Modify farm TCP",
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
#         "maxcon" : "1000"
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
#       -u zapi:<password> -d '{"ip":"192.168.0.10","port":"88","maxcon":"1000","priority":"2",
#       "weight":"1"}' https://<zenlb_server>:444/zapi/v2/zapi.cgi/farms/FarmTCP/backends/1
#
# @apiSampleRequest off
#
#**
#
#
# curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin -d '{"ip":"192.168.0.10","port":"88","priority":"2","weight":"1"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/L4FARM/backends/1
#
#####Documentation of PUT BACKEND L4####
#**
#  @api {put} /farms/<farmname>/backends/<backendid> Modify a l4xnat Backend
#  @apiGroup Farm Modify
#  @apiName PutBckL4
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiParam {Number} backendid Backend ID, unique ID.
#  @apiDescription Modify the params of a backend in a L4XNAT Farm
#  @apiVersion 2.0.0
#
#
#
# @apiSuccess	{String}		ip			IP of the backend, where is listening the real service.
# @apiSuccess	{Number}		port			PORT of the backend, where is listening the real service.
# @apiSuccess   {Number}        priority		It’s the priority value for the current real server.
# @apiSuccess   {Number}        weight		It's the weight value for the current real server.
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
#       -u zapi:<password> -d '{"ip":"192.168.0.10","port":"88","priority":"2",
#       "weight":"1"}' https://<zenlb_server>:444/zapi/v2/zapi.cgi/farms/L4FARM/backends/1
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
#  @apiVersion 2.0.0
#
#
#
# @apiSuccess   {String}        ip                       IP of the backend, where is listening the real service.
# @apiSuccess   {String}        interface	It’s the local network interface where the backend is connected to.
# @apiSuccess   {Number}        priority         It’s the priority value for the current real server.
# @apiSuccess   {Number}        weight           It's the weight value for the current real server.
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
#       -u zapi:<password> -d '{"ip":"192.168.0.10","interface":"eth0","priority":"2",
#       "weight":"1"}' https://<zenlb_server>:444/zapi/v2/zapi.cgi/farms/DATAFARM/backends/1
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
#  @apiVersion 2.0.0
#
#
#
# @apiSuccess   {String}        ip                       IP of the backend, where is listening the real service.
# @apiSuccess   {String}        port	        PORT of the backend, where is listening the real service.
# @apiSuccess   {String}        service		The service where the backend belongs.
# @apiSuccess	{Number}	timeout		It’s the backend timeout to respond a certain request.
# @apiSuccess   {Number}        weight           It's the weight value for the current real server.
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
#       -u zapi:<password> -d '{"ip":"192.168.0.10","port":"88","timeout":"12","service":"sev2",
#       "weight":"1"}' https://<zenlb_server>:444/zapi/v2/zapi.cgi/farms/FarmHTTP/backends/1
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
#  @apiVersion 2.0.0
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
#       -u zapi:<password> -d '{"ip":"192.168.0.10","service":"sev2"}'
#       https://<zenlb_server>:444/zapi/v2/zapi.cgi/farms/FarmGSLB/backends/1
#
# @apiSampleRequest off
#
#**

sub modify_backends()
{

	my ( $farmname, $id_server ) = @_;
	my $out_p = [];

	use CGI;
	use JSON;

	my $q        = CGI->new;
	my $json     = JSON->new;
	my $data     = $q->param( 'PUTDATA' );
	my $json_obj = $json->decode( $data );

	my $j = JSON::XS->new->utf8->pretty( 1 );
	$j->canonical( $enabled );

	if ( $farmname =~ /^$/ )
	{
		&logfile(
			"ZAPI error, trying to modify the backends in a farm $farmname, invalid farmname, can't be blank."
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request'
		);
		$errormsg = "Invalid farm name, please insert a valid value.";
		my $output = $j->encode(
								 {
								   description => "Modify backend",
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
		-status=> '404 Not Found'
		);
		$errormsg = "The farmname $farmname does not exists.";
		my $output = $j->encode({
				description => "Modify backend",
				error => "true",
				message => $errormsg
		});
		print $output;
		exit;

	}

	if ( $id_server =~ /^$/ )
	{
		&logfile(
			"ZAPI error, trying to modify the backends in a farm $farmname, invalid id_server, can't be blank."
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request'
		);
		$errormsg = "Invalid id server, please insert a valid value.";
		my $output = $j->encode(
								 {
								   description => "Modify backend",
								   error       => "true",
								   message     => $errormsg
								 }
		);
		print $output;
		exit;
	}

	$error = "false";
	my $type = &getFarmType( $farmname );

	if ( $type eq "l4xnat" || $type eq "datalink" )
	{

		# Params
		my @run = &getFarmServers( $farmname );
		$serv_values = @run[$id_server];
		my @l_serv = split ( ";", $serv_values );

		# Functions
		if ( exists ( $json_obj->{ ip } ) )
		{
			if ( $json_obj->{ ip } =~ /^$/ )
			{
				$error = "true";
				&logfile(
					"ZAPI error, trying to modify the backends in a farm $farmname, invalid IP, can't be blank."
				);
			}
			elsif ( $json_obj->{ ip } =~ /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/ )
			{
				@l_serv[1] = $json_obj->{ ip };
			}
			else
			{
				$error = "true";
				&logfile(
					 "ZAPI error, trying to modify the backends in a farm $farmname, invalid IP." );
			}
		}

		if ( exists ( $json_obj->{ port } ) )
		{
			if ( $json_obj->{ port } =~ /^$/ )
			{
				$error = "true";
				&logfile(
					"ZAPI error, trying to modify the backends in a farm $farmname, invalid port, can't be blank."
				);
			}
			elsif ( $json_obj->{ port } =~ /^\d+/ )
			{
				@l_serv[2] = $json_obj->{ port } + 0;
			}
			else
			{
				$error = "true";
				&logfile(
					  "ZAPI error, trying to modify the backends in a farm $farmname, invalid port."
				);
			}
		}

		if ( exists ( $json_obj->{ interface } ) )
		{
			if ( $json_obj->{ interface } =~ /^$/ )
			{
				$error = "true";
				&logfile(
					"ZAPI error, trying to modify the backends in a farm $farmname, invalid interface, can't be blank."
				);
			}
			elsif ( $json_obj->{ interface } =~ /^eth\d+/ )
			{
				@l_serv[2] = $json_obj->{ interface };
			}
			else
			{
				$error = "true";
				&logfile(
					"ZAPI error, trying to modify the backends in a farm $farmname, invalid interface."
				);
			}
		}

		if ( $type eq "l4xnat" )
		{
			if ( exists ( $json_obj->{ weight } ) )
			{
				if ( $json_obj->{ weight } =~ /^$/ )
				{
					$error = "true";
					&logfile(
						"ZAPI error, trying to modify the backends in a farm $farmname, invalid weight, can't be blank."
					);
				}
				elsif ( $json_obj->{ weight } =~ /^\d+$/ )
				{
					@l_serv[4] = $json_obj->{ weight } + 0;
				}
				else
				{
					$error = "true";
					&logfile(
						"ZAPI error, trying to modify the backends in a farm $farmname, invalid weight."
					);
				}
			}

			if ( exists ( $json_obj->{ priority } ) )
			{
				if ( $json_obj->{ priority } =~ /^$/ )
				{
					$error = "true";
					&logfile(
						"ZAPI error, trying to modify the backends in a farm $farmname, invalid priority, can't be blank."
					);
				}
				elsif ( $json_obj->{ priority } =~ /^\d+$/ )
				{
					@l_serv[5] = $json_obj->{ priority } + 0;
				}
				else
				{
					$error = "true";
					&logfile(
						"ZAPI error, trying to modify the backends in a farm $farmname, invalid priority."
					);
				}
			}

			if ( $error eq "false" )
			{
				$status =
				  &setFarmServer( $id_server, @l_serv[1], $l_serv[2], "", $l_serv[4],
								  $l_serv[5], "", $farmname );

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

				if ( $status == -1 )
				{
					$error = "true";
					&logfile(
						"ZAPI error, trying to modify the backends in a farm $farmname, it's not possible to modify the real server with ip $json_obj->{ip}."
					);
				}
			}
		}
		elsif ( $type eq "datalink" )
		{
			if ( exists ( $json_obj->{ weight } ) )
			{
				if ( $json_obj->{ weight } =~ /^$/ )
				{
					$error = "true";
					&logfile(
						"ZAPI error, trying to modify the backends in a farm $farmname, invalid weight, can't be blank."
					);
				}
				elsif ( $json_obj->{ weight } =~ /^\d+$/ )
				{
					@l_serv[3] = $json_obj->{ weight } + 0;
				}
				else
				{
					$error = "true";
					&logfile(
						"ZAPI error, trying to modify the backends in a farm $farmname, invalid weight."
					);
				}
			}

			if ( exists ( $json_obj->{ priority } ) )
			{
				if ( $json_obj->{ priority } =~ /^$/ )
				{
					$error = "true";
					&logfile(
						"ZAPI error, trying to modify the backends in a farm $farmname, invalid priority, can't be blank."
					);
				}
				elsif ( $json_obj->{ priority } =~ /^\d+$/ )
				{
					@l_serv[4] = $json_obj->{ priority } + 0;
				}
				else
				{
					$error = "true";
					&logfile(
						"ZAPI error, trying to modify the backends in a farm $farmname, invalid priority."
					);
				}
			}

			if ( $error eq "false" )
			{
				$status =
				  &setFarmServer( $id_server, @l_serv[1], $l_serv[2], "", $l_serv[3],
								  $l_serv[4], "", $farmname );
				if ( $status == -1 )
				{
					$error = "true";
					&logfile(
						"ZAPI error, trying to modify the backends in a farm $farmname, it's not possible to modify the real server with IP $json_obj->{ip} and interface $json_obj->{interface}."
					);
				}
			}
		}
	}

	if ( $type eq "tcp" || $type eq "udp" )
	{

		# Params
		my @run = &getFarmServers( $farmname );
		$serv_values = @run[$id_server];

		my @l_serv = split ( "\ ", $serv_values );

		# Functions
		if ( exists ( $json_obj->{ ip } ) )
		{
			if ( $json_obj->{ ip } =~ /^$/ )
			{
				$error = "true";
				&logfile(
					"ZAPI error, trying to modify the backends in a farm $farmname, invalid IP, can't be blank."
				);
			}
			elsif ( $json_obj->{ ip } =~ /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/ )
			{
				@l_serv[2] = $json_obj->{ ip };
			}
			else
			{
				$error = "true";
				&logfile(
					 "ZAPI error, trying to modify the backends in a farm $farmname, invalid IP." );
			}
		}

		if ( exists ( $json_obj->{ port } ) )
		{
			if ( $json_obj->{ port } =~ /^$/ )
			{
				$error = "true";
				&logfile(
					"ZAPI error, trying to modify the backends in a farm $farmname, invalid port, can't be blank."
				);
			}
			elsif ( $json_obj->{ port } =~ /^\d+/ )
			{
				@l_serv[4] = $json_obj->{ port } + 0;
			}
			else
			{
				$error = "true";
				&logfile(
					  "ZAPI error, trying to modify the backends in a farm $farmname, invalid port."
				);
			}
		}

		if ( exists ( $json_obj->{ maxcon } ) )
		{
			if ( $json_obj->{ maxcon } =~ /^$/ )
			{
				$error = "true";
				&logfile(
					"ZAPI error, trying to modify the backends in a farm $farmname, invalid maxcon, can't be blank."
				);
			}
			elsif ( $json_obj->{ maxcon } =~ /^\d+$/ )
			{
				@l_serv[8] = $json_obj->{ maxcon } + 0;
			}
			else
			{
				$error = "true";
				&logfile(
					"ZAPI error, trying to modify the backends in a farm $farmname, invalid maxcon."
				);
			}
		}

		if ( exists ( $json_obj->{ weight } ) )
		{
			if ( $json_obj->{ weight } =~ /^$/ )
			{
				$error = "true";
				&logfile(
					"ZAPI error, trying to modify the backends in a farm $farmname, invalid weight, can't be blank."
				);
			}
			elsif ( $json_obj->{ weight } =~ /^\d+$/ )
			{
				@l_serv[12] = $json_obj->{ weight } + 0;
			}
			else
			{
				$error = "true";
				&logfile(
					"ZAPI error, trying to modify the backends in a farm $farmname, invalid weight."
				);
			}
		}

		if ( exists ( $json_obj->{ priority } ) )
		{
			if ( $json_obj->{ priority } =~ /^$/ )
			{
				$error = "true";
				&logfile(
					"ZAPI error, trying to modify the backends in a farm $farmname, invalid priority, can't be blank."
				);
			}
			elsif ( $json_obj->{ priority } =~ /^\d+$/ )
			{
				@l_serv[14] = $json_obj->{ priority } + 0;
			}
			else
			{
				$error = "true";
				&logfile(
					"ZAPI error, trying to modify the backends in a farm $farmname, invalid priority."
				);
			}
		}

		if ( $error eq "false" )
		{
			$status = &setFarmServer( $id_server,  @l_serv[2],  $l_serv[4], $l_serv[8],
									  $l_serv[12], $l_serv[14], "",         $farmname );
			if ( $status == -1 )
			{
				$error = "true";
				&logfile(
					"ZAPI error, trying to modify the backends in a farm $farmname, it's not possible to modify the real server with IP $json_obj->{ip}."
				);
			}
		}

	}

	if ( $type eq "http" || $type eq "https" )
	{

		#Params
		if ( exists ( $json_obj->{ service } ) )
		{
			if ( $json_obj->{ service } =~ /^$/ )
			{
				$error = "true";
				&logfile(
					"ZAPI error, trying to modify the backends in a farm $farmname, invalid service, can't be blank."
				);
			}
			else
			{
				$service = $json_obj->{ service };
			}
		}
		else
		{
			$error = "true";
			&logfile(
				"ZAPI error, trying to modify the backends in a farm $farmname, it's necessary to insert the service parameter."
			);
		}
		
		
		# Check that the provided service is configured in the farm
		my @services = &getFarmServices($farmname);
		
		my $found = 0;
		foreach $farmservice (@services) {
			#print "service: $farmservice";
			if ($json_obj->{service} eq $farmservice) {
				$found = 1;
				break;
			}
		}
		if ($found eq 0){
			
			# Error
			print $q->header(
			-type=> 'text/plain',
			-charset=> 'utf-8',
			-status=> '400 Bad Request'
			);
			$errormsg = "Invalid service name, please insert a valid value.";
			my $output = $j->encode({
					description => "Modify backend",
					error => "true",
					message => $errormsg
			});
			print $output;
			exit;
			
		}
		

		my $backendsvs = &getFarmVS( $farmname, $service, "backends" );
		my @be = split ( "\n", $backendsvs );
		foreach $subline ( @be )
		{
			@subbe = split ( "\ ", $subline );
			if ( @subbe[1] == $id_server )
			{
				last;
			}
		}

		# Functions
		if ( exists ( $json_obj->{ ip } ) )
		{
			if ( $json_obj->{ ip } =~ /^$/ )
			{
				$error = "true";
				&logfile(
					"ZAPI error, trying to modify the backends in a farm $farmname, invalid IP, can't be blank."
				);
			}
			elsif ( $json_obj->{ ip } =~ /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/ )
			{
				@subbe[3] = $json_obj->{ ip };
			}
			else
			{
				$error = "true";
				&logfile(
					 "ZAPI error, trying to modify the backends in a farm $farmname, invalid IP." );
			}
		}

		if ( exists ( $json_obj->{ port } ) )
		{
			if ( $json_obj->{ port } =~ /^$/ )
			{
				$error = "true";
				&logfile(
					"ZAPI error, trying to modify the backends in a farm $farmname, invalid port, can't be blank."
				);
			}
			elsif ( $json_obj->{ port } =~ /^\d+/ )
			{
				@subbe[5] = $json_obj->{ port } + 0;
			}
			else
			{
				$error = "true";
				&logfile(
					  "ZAPI error, trying to modify the backends in a farm $farmname, invalid port."
				);
			}
		}

		if ( exists ( $json_obj->{ weight } ) )
		{
			if ( $json_obj->{ weight } =~ /^$/ )
			{
				$error = "true";
				&logfile(
					"ZAPI error, trying to modify the backends in a farm $farmname, invalid weight, can't be blank."
				);
			}
			elsif ( $json_obj->{ weight } =~ /^\d+$/ )
			{
				@subbe[9] = $json_obj->{ weight } + 0;
			}
			else
			{
				$error = "true";
				&logfile(
					"ZAPI error, trying to modify the backends in a farm $farmname, invalid weight."
				);
			}
		}

		if ( exists ( $json_obj->{ timeout } ) )
		{
			if ( $json_obj->{ timeout } =~ /^$/ )
			{
				$error = "true";
				&logfile(
					"ZAPI error, trying to modify the backends in a farm $farmname, invalid timeout, can't be blank."
				);
			}
			elsif ( $json_obj->{ timeout } =~ /^\d+$/ )
			{
				@subbe[7] = $json_obj->{ timeout } + 0;
			}
			else
			{
				$error = "true";
				&logfile(
					"ZAPI error, trying to modify the backends in a farm $farmname, invalid timeout."
				);
			}
		}

		if ( $error eq "false" )
		{
			$status = &setFarmServer(
									  $id_server, @subbe[3], $subbe[5], "",
									  "",         $subbe[9], $subbe[7], $farmname,
									  $service
			);
			if ( $status == -1 )
			{
				$error = "true";
				&logfile(
					"ZAPI error, trying to modify the backends in a farm $farmname, it's not possible to modify the real server with IP $json_obj->{ip} in service $service."
				);
			}
			else
			{
				&setFarmRestart( $farmname );
			}
		}
	}

	if ( $type eq "gslb" )
	{

		#Params
		if ( exists ( $json_obj->{ service } ) )
		{
			if ( $json_obj->{ service } =~ /^$/ )
			{
				$error = "true";
				&logfile(
					"ZAPI error, trying to modify the backends in a farm $farmname, invalid service, can't be blank."
				);
			}
			else
			{
				$service = $json_obj->{ service };
			}
		}
		else
		{
			$error = "true";
			&logfile(
				"ZAPI error, trying to modify the backends in a farm $farmname, it's necessary to insert the service parameter."
			);
		}
		
		# Check that the provided service is configured in the farm
		my @services = &getGSLBFarmServices($farmname);
		
		my $found = 0;
		foreach $farmservice (@services) {
			#print "service: $farmservice";
			if ($json_obj->{service} eq $farmservice) {
				$found = 1;
				break;
			}
		}
		if ($found eq 0){
			
			# Error
			print $q->header(
			-type=> 'text/plain',
			-charset=> 'utf-8',
			-status=> '400 Bad Request'
			);
			$errormsg = "Invalid service name, please insert a valid value.";
			my $output = $j->encode({
					description => "Modify backend",
					error => "true",
					message => $errormsg
			});
			print $output;
			exit;
			
		}

		my $backendsvs = &getFarmVS( $farmname, $service, "backends" );
		my @be = split ( "\n", $backendsvs );
		foreach $subline ( @be )
		{
			$subline =~ s/^\s+//;
			if ( $subline =~ /^$/ )
			{
				next;
			}

			@subbe = split ( " => ", $subline );
			if ( @subbe[0] == $id_server )
			{
				last;
			}
		}
		my $lb = &getFarmVS( $farmname, $service, "algorithm" );

		# Functions
		if ( exists ( $json_obj->{ ip } ) )
		{
			if ( $json_obj->{ ip } =~ /^$/ )
			{
				$error = "true";
				&logfile(
					"ZAPI error, trying to modify the backends in a farm $farmname, invalid IP, can't be blank."
				);
			}
			elsif ( $json_obj->{ ip } =~ /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/ )
			{
				@subbe[1] = $json_obj->{ ip };
			}
			else
			{
				$error = "true";
				&logfile(
					 "ZAPI error, trying to modify the backends in a farm $farmname, invalid IP." );
			}
		}

		if ( $error eq "false" )
		{
			$status =
			  &setGSLBFarmNewBackend( $farmname, $service, $lb, $id_server, @subbe[1] );
			if ( $status == -1 )
			{
				$error = "true";
				&logfile(
					"ZAPI error, trying to modify the backends in a farm $farmname, it's not possible to modify the real server with IP $json_obj->{ip} in service $service."
				);
			}
			else
			{
				&setFarmRestart( $farmname );
			}
		}
	}

	# Print params
	if ( $type eq "http" || $type eq "https" || $type eq "gslb" )
	{
		if ( $error ne "true" )
		{
			&logfile(
				"ZAPI success, some parameters have been changed in the backend $id_server in service $service in farm $farmname."
			);

			# Success
			print $q->header(
							  -type    => 'text/plain',
							  -charset => 'utf-8',
							  -status  => '200 OK'
			);

			foreach $key ( keys %$json_obj )
			{
				push $out_p, { $key => $json_obj->{ $key } };
			}

			my $j = JSON::XS->new->utf8->pretty( 1 );
			$j->canonical( $enabled );
			
			
			# Get farm status. If farm is down the restart is not required.
			my $status = &getFarmStatus( $farmname);
			my $output;
			if ($status eq "up") {
			
				$output = $j->encode(
					{
					   description => "Modify backend $id_server in farm $farmname",
					   params      => $out_p,
					   info =>
						 "There're changes that need to be applied, stop and start farm to apply them!"
					}
				);
			}
			if ($status eq "down") {
			
				$output = $j->encode(
					{
					   description => "Modify backend $id_server in farm $farmname",
					   params      => $out_p
					}
				);
			}
			print $output;

		}
		else
		{
			&logfile(
				"ZAPI error, trying to modify the backends in a farm $farmname, it's not possible to modify the backend."
			);

			# Error
			print $q->header(
							  -type    => 'text/plain',
							  -charset => 'utf-8',
							  -status  => '400 Bad Request'
			);
			$errormsg = "Errors found trying to modify farm $farmname";
			my $output = $j->encode(
									 {
									   description => "Modify farm $farmname",
									   error       => "true",
									   message     => $errormsg
									 }
			);
			print $output;
			exit;

		}
	}
	else
	{

		if ( $error ne "true" )
		{
			&logfile(
				"ZAPI success, some parameters have been changed in the backend $id_server in farm $farmname."
			);

			# Success
			print $q->header(
							  -type    => 'text/plain',
							  -charset => 'utf-8',
							  -status  => '200 OK'
			);

			foreach $key ( keys %$json_obj )
			{
				push $out_p, { $key => $json_obj->{ $key } };
			}

			my $j = JSON::XS->new->utf8->pretty( 1 );
			$j->canonical( $enabled );
			my $output = $j->encode(
								{
								  description => "Modify backend $id_server in farm $farmname",
								  params      => $out_p
								}
			);
			print $output;

		}
		else
		{
			&logfile(
				"ZAPI error, trying to modify the backends in a farm $farmname, it's not possible to modify the backend."
			);

			# Error
			print $q->header(
							  -type    => 'text/plain',
							  -charset => 'utf-8',
							  -status  => '400 Bad Request'
			);
			$errormsg = "Errors found trying to modify farm $farmname";
			my $output = $j->encode(
									 {
									   description => "Modify farm $farmname",
									   error       => "true",
									   message     => $errormsg
									 }
			);
			print $output;
			exit;

		}

	}

}

#
# curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin -d '{"rname":"ww2","ttl":"8","type":"DYNA","rdata":"sev2","zone":"zone1"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/FarmGSLB/resources/3
#
#####Documentation of PUT RESOURCES####
#**
#  @api {put} /farms/<farmname>/resources/<resourceid> Modify a gslb Resource
#  @apiGroup Farm Modify
#  @apiName PutResource
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiParam {Number} resourceid Resource ID, unique ID.
#  @apiDescription Modify the params of a resource of a zone in a GSLB Farm
#  @apiVersion 2.0.0
#
#
#
# @apiSuccess   {String}        zone                     It's the zone where the resource will be created.
# @apiSuccess   {Number}	ttl		The Time to Live value for the current record.
# @apiSuccess   {String}        type		DNS record type. The options are: NS, A, CNAME and DYNA.
# @apiSuccess   {String}        rdata		It’s the real data needed by the record type.
# @apiSuccess	{String}	rname		Resource's name.
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Modify resource 3 in farm FarmGSLB",
#   "params" : [
#      {
#         "zone" : "zone1"
#      },
#      {
#         "ttl" : "8"
#      },
#      {
#         "type" : "DYNA"
#      },
#      {
#         "rdata" : "sev2"
#      },
#      {
#         "rname" : "www"
#      }
#   ]
#}
#
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#       -u zapi:<password> -d '{"rname":"www","ttl":"8","type":"DYNA","rdata":"sev2",
#       "zone":"zone1"}' https://<zenlb_server>:444/zapi/v2/zapi.cgi/farms/FarmGSLB/resources/3
#
# @apiSampleRequest off
#
#**

sub modify_resources()
{

	my ( $farmname, $id_resource ) = @_;
	my $out_p = [];

	use CGI;
	use JSON;

	my $q        = CGI->new;
	my $json     = JSON->new;
	my $data     = $q->param( 'PUTDATA' );
	my $json_obj = $json->decode( $data );

	my $j = JSON::XS->new->utf8->pretty( 1 );
	$j->canonical( $enabled );

	if ( $farmname =~ /^$/ )
	{
		&logfile(
			"ZAPI error, trying to modify the resources in a farm $farmname, invalid farmname, can't be blank."
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request'
		);
		$errormsg = "Invalid farm name, please insert a valid value.";
		my $output = $j->encode(
								 {
								   description => "Modify resource",
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
		-status=> '404 Not Found'
		);
		$errormsg = "The farmname $farmname does not exists.";
		my $output = $j->encode({
				description => "Modify resource",
				error => "true",
				message => $errormsg
		});
		print $output;
		exit;

	}

	$error = "false";

	#Params
	if ( exists ( $json_obj->{ zone } ) )
	{
		if ( $json_obj->{ zone } =~ /^$/ )
		{
			$error = "true";
			&logfile(
				"ZAPI error, trying to modify the resources in a farm $farmname, invalid zone, can't be blank."
			);
		}
		else
		{
			$zone = $json_obj->{ zone };
		}
	}
	else
	{
		&logfile(
			"ZAPI error, trying to modify the resources in a farm $farmname, invalid zone, it's necessary to insert the zone parameter."
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request'
		);
		$errormsg = "The zone parameter is empty, please insert a zone.";
		my $output = $j->encode(
								 {
								   description => "Modify resource",
								   error       => "true",
								   message     => $errormsg
								 }
		);
		print $output;
		exit;
	}

	my $backendsvs = &getFarmVS( $farmname, $zone, "resources" );
	my @be = split ( "\n", $backendsvs );
	foreach $subline ( @be )
	{
		if ( $subline =~ /^$/ )
		{
			next;
		}
		@subbe  = split ( "\;", $subline );
		@subbe1 = split ( "\t", @subbe[0] );
		@subbe2 = split ( "\_", @subbe[1] );
		if ( @subbe2[1] == $id_resource )
		{
			last;
		}
	}

	# Functions
	if ( exists ( $json_obj->{ rname } ) )
	{
		if ( $json_obj->{ rname } =~ /^$/ )
		{
			$error = "true";
			&logfile(
				"ZAPI error, trying to modify the resources in a farm $farmname, invalid rname, can't be blank."
			);
		}
		else
		{
			@subbe1[0] = $json_obj->{ rname };
		}
	}

	if ( exists ( $json_obj->{ ttl } ) )
	{
		if ( $json_obj->{ ttl } =~ /^$/ )
		{
			$error = "true";
			&logfile(
				"ZAPI error, trying to modify the resources in a farm $farmname, invalid ttl, can't be blank."
			);
		}
		elsif ( $json_obj->{ ttl } =~ /^\d+/ )
		{
			@subbe1[1] = $json_obj->{ ttl };
		}
		else
		{
			$error = "true";
			&logfile(
				  "ZAPI error, trying to modify the resources in a farm $farmname, invalid ttl."
			);
		}
	}

	if ( exists ( $json_obj->{ type } ) )
	{
		if ( $json_obj->{ type } =~ /^$/ )
		{
			$error = "true";
			&logfile(
				"ZAPI error, trying to modify the resources in a farm $farmname, invalid type, can't be blank."
			);
		}
		elsif ( $json_obj->{ type } =~ /^NS|A|CNAME|DYNA$/ )
		{
			@subbe1[2] = $json_obj->{ type };
		}
		else
		{
			$error = "true";
			&logfile(
				 "ZAPI error, trying to modify the resources in a farm $farmname, invalid type."
			);
		}
	}

	if ( exists ( $json_obj->{ rdata } ) )
	{
		if ( $json_obj->{ rdata } =~ /^$/ )
		{
			$error = "true";
			&logfile(
				"ZAPI error, trying to modify the resources in a farm $farmname, invalid rdata, can't be blank."
			);
		}
		else
		{
			@subbe1[3] = $json_obj->{ rdata };
		}
	}

	if ( $error eq "false" )
	{
		$status = &setFarmZoneResource(
										$id_resource, @subbe1[0], @subbe1[1],
										@subbe1[2],   @subbe1[3], $farmname,
										$zone
		);
		if ( $status == -1 )
		{
			$error = "true";
			&logfile(
				"ZAPI error, trying to modify the resources in a farm $farmname, it's not possible to modify the resource $id_resource in zone $zone."
			);
		}
		elsif ($status == -2){
			# Error
                print $q->header(
                   -type=> 'text/plain',
                   -charset=> 'utf-8',
                   -status=> '404 Not Found'
                );
                $errormsg = "The resource with ID $id_resource does not exist.";
                my $output = $j->encode({
                        description => "Modify resource",
                        error => "true",
                        message => $errormsg
                });
                print $output;
                exit;
		}
	}

	# Print params
	if ( $error ne "true" )
	{
		&logfile(
			"ZAPI success, some parameters have been changed in the resource $id_resource in zone $zone in farm $farmname."
		);

		# Success
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '200 OK'
		);

		foreach $key ( keys %$json_obj )
		{
			push $out_p, { $key => $json_obj->{ $key } };
		}

		my $j = JSON::XS->new->utf8->pretty( 1 );
		$j->canonical( $enabled );
		my $output = $j->encode(
						 {
						   description => "Modify resource $id_resource in farm $farmname",
						   params      => $out_p
						 }
		);
		print $output;

	}
	else
	{
		&logfile(
			"ZAPI error, trying to modify the resources in a farm $farmname, it's not possible to modify the resource."
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request'
		);
		$errormsg = "Errors found trying to modify farm $farmname";
		my $output = $j->encode(
								 {
								   description => "Modify farm $farmname",
								   error       => "true",
								   message     => $errormsg
								 }
		);
		print $output;
		exit;

	}

}

#
# curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin -d '{"defnamesv":"ns1"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/FarmGSLB/zones/zone1
#
#####Documentation of PUT ZONE####
#**
#  @api {put} /farms/<farmname>/zones/<zoneid> Modify a gslb Zone
#  @apiGroup Farm Modify
#  @apiName PutZone
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiParam {String} zoneid Zone name, unique ID.
#  @apiDescription Modify the params of a Zone in a GSLB Farm
#  @apiVersion 2.0.0
#
#
#
# @apiSuccess   {String}        defnamesv		This will be the entry point root name server that will be available as the Start of Authority (SOA) DNS record.
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Modify zone zone1 in farm FarmGSLB",
#   "params" : [
#      {
#         "defnamesv" : "ns1"
#      }
#   ]
#}
#
#
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#       -u zapi:<password> -d '{"defnamesv":"ns1"}'
#       https://<zenlb_server>:444/zapi/v2/zapi.cgi/farms/FarmGSLB/zones/zone1
#
# @apiSampleRequest off
#
#**

sub modify_zones()
{

	my ( $farmname, $zone ) = @_;
	my $out_p = [];

	use CGI;
	use JSON;

	my $q        = CGI->new;
	my $json     = JSON->new;
	my $data     = $q->param( 'PUTDATA' );
	my $json_obj = $json->decode( $data );

	my $j = JSON::XS->new->utf8->pretty( 1 );
	$j->canonical( $enabled );

	if ( $farmname =~ /^$/ )
	{
		&logfile(
			"ZAPI error, trying to modify the zones in a farm $farmname, invalid farmname, can't be blank."
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request'
		);
		$errormsg = "Invalid farm name, please insert a valid value.";
		my $output = $j->encode(
								 {
								   description => "Modify zone",
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
		-status=> '404 Not Found'
		);
		$errormsg = "The farmname $farmname does not exists.";
		my $output = $j->encode({
				description => "Modify zone",
				error => "true",
				message => $errormsg
		});
		print $output;
		exit;

	}

	$error = "false";

	# Functions
	if ( $json_obj->{ defnamesv } =~ /^$/ )
	{
		$error = "true";
		&logfile(
			"ZAPI error, trying to modify the zones in a farm $farmname, invalid defnamesv, can't be blank."
		);
	}
	if ( $error eq "false" )
	{
		&setFarmVS( $farmname, $zone, "ns", $json_obj->{ defnamesv } );
		if ( $? eq 0 )
		{
			&runFarmReload( $farmname );
		}
		else
		{
			$error = "true";
			&logfile(
				"ZAPI error, trying to modify the zones in a farm $farmname, it's not possible to modify the zone $zone."
			);
		}
	}

	# Print params
	if ( $error ne "true" )
	{
		&logfile(
			"ZAPI success, some parameters have been changed  in zone $zone in farm $farmname."
		);

		# Success
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '200 OK'
		);

		foreach $key ( keys %$json_obj )
		{
			push $out_p, { $key => $json_obj->{ $key } };
		}

		my $j = JSON::XS->new->utf8->pretty( 1 );
		$j->canonical( $enabled );
		my $output = $j->encode(
								 {
								   description => "Modify zone $zone in farm $farmname",
								   params      => $out_p
								 }
		);
		print $output;

	}
	else
	{
		&logfile(
			"ZAPI error, trying to modify the zones in a farm $farmname, it's not possible to modify the zone $zone."
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request'
		);
		$errormsg = "Errors found trying to modify farm $farmname";
		my $output = $j->encode(
								 {
								   description => "Modify zone $zone in farm $farmname",
								   error       => "true",
								   message     => $errormsg
								 }
		);
		print $output;
		exit;

	}

}

# curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin -d '{"vhost":"www.marca.com","urlp":"^/myapp$","redirect":"https://google.es","persistence":"URL","ttl":"120","sessionid":"sidd","leastrep":"false","httpsb":"false"}' https://178.62.126.152:444/zapi/v1/zapi.cgi/farms/FarmHTTP/services/sev1

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
#  @apiVersion 2.0.0
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
#       -u zapi:<password> -d '{"deftcpport":"80"}'
#       https://<zenlb_server>:444/zapi/v2/zapi.cgi/farms/FarmGSLB/services/sev2
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
#  @apiVersion 2.0.0
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
#       -u zapi:<password> -d '{"vhost":"www.mywebserver.com","urlp":"^/myapp1$","persistence":"URL",
#       "redirect":"http://zenloadbalancer.com","ttl":"125","sessionid":"sid","leastresp":"true",
#       "httpsb":"true"}' https://<zenlb_server>:444/zapi/v2/zapi.cgi/farms/FarmHTTP/services/sev2
#
# @apiSampleRequest off
#
#**

sub modify_services()
{

	my ( $farmname, $service ) = @_;
	my $out_p = [];

	use CGI;
	use JSON;
	use URI::Escape;

	my $q        = CGI->new;
	my $json     = JSON->new;
	my $data     = $q->param( 'PUTDATA' );
	my $json_obj = $json->decode( $data );

	my $j = JSON::XS->new->utf8->pretty( 1 );
	$j->canonical( $enabled );

	if ( $farmname =~ /^$/ )
	{
		&logfile(
			"ZAPI error, trying to modify the services in a farm $farmname, invalid farmname, can't be blank."
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request'
		);
		$errormsg = "Invalid farm name, please insert a valid value.";
		my $output = $j->encode(
								 {
								   description => "Modify service",
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
		-status=> '404 Not Found'
		);
		$errormsg = "The farmname $farmname does not exists.";
		my $output = $j->encode({
				description => "Modify service",
				error => "true",
				message => $errormsg
		});
		print $output;
		exit;

	}

	if ( $service =~ /^$/ )
	{
		&logfile(
			"ZAPI error, trying to modify the services in a farm $farmname, invalid farmname, can't be blank."
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request'
		);
		$errormsg = "Invalid service name, please insert a valid value.";
		my $output = $j->encode(
								 {
								   description => "Modify service",
								   error       => "true",
								   message     => $errormsg
								 }
		);
		print $output;
		exit;
	}

	$error = "false";
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
		-status=> '400 Bad Request'
		);
		$errormsg = "Invalid service name, please insert a valid value.";
		my $output = $j->encode({
				description => "Modify service",
				error => "true",
				message => $errormsg
		});
		print $output;
		exit;
		
	}

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
			if ( $redirect =~ /^http\:\/\//i || $redirect =~ /^https:\/\//i || $redirect =~ /^$/ )
			{
				&setFarmVS( $farmname, $service, "redirect", $redirect );
			}
			else
			{
				$error = "true";
				&logfile(
					"ZAPI error, trying to modify the service $service in a farm $farmname, invalid redirect."
				);
			}
		}

		$redirect = &getFarmVS( $farmname, $service, "redirect" );

		if ( exists ( $json_obj->{ redirecttype } ) )
		{
			my $redirecttype = $json_obj->{ redirecttype };
			if ( $redirecttype =~ /^$/ )
			{
				$error = "true";
				&logfile(
					"ZAPI error, trying to modify the service $service in a farm $farmname, invalid redirecttype, can't be blank."
				);
			}
			elsif ( $redirecttype eq "default" )
			{
				&setFarmVS( $farmname, $service, "redirect", $redirect );
			}
			elsif ( $redirecttype eq "append" )
			{
				&setFarmVS( $farmname, $service, "redirectappend", $redirect );
			}
			else
			{
				$error = "true";
				&logfile(
					"ZAPI error, trying to modify the service $service in a farm $farmname, invalid redirecttype."
				);
			}
		}

		if ( exists ( $json_obj->{ persistence } ) )
		{
			if ( $json_obj->{ persistence } =~ /^$/ )
			{
				$error = "true";
				&logfile(
					"ZAPI error, trying to modify the service $service in a farm $farmname, invalid persistence, can't be blank."
				);
			}
			elsif (
					$json_obj->{ persistence } =~ /^nothing|IP|BASIC|URL|PARM|COOKIE|HEADER$/ )
			{
				$session = $json_obj->{ persistence };
				$status = &setFarmVS( $farmname, $service, "session", "$session" );
				if ( $status != 0 )
				{
					$error = "true";
					&logfile(
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
				&logfile(
					"ZAPI error, trying to modify the service $service in a farm $farmname, invalid ttl, can't be blank."
				);
			}
			elsif ( $json_obj->{ ttl } =~ /^\d+/ )
			{
				$status = &setFarmVS( $farmname, $service, "ttl", "$json_obj->{ttl}" );
				if ( $status != 0 )
				{
					$error = "true";
					&logfile(
						"ZAPI error, trying to modify the service $service in a farm $farmname, it's not possible to change the ttl parameter."
					);
				}
			}
			else
			{
				$error = "true";
				&logfile(
					"ZAPI error, trying to modify the service $service in a farm $farmname, invalid ttl, must be numeric."
				);
			}
		}

		if ( exists ( $json_obj->{ sessionid } ) )
		{
			if ( $json_obj->{ sessionid } =~ /^$/ )
			{
				$error = "true";
				&logfile(
					"ZAPI error, trying to modify the service $service in a farm $farmname, invalid sessionid, can't be blank."
				);
			}
			else
			{
				&setFarmVS( $farmname, $service, "sessionid", $json_obj->{ sessionid } );
			}
		}

		if ( exists ( $json_obj->{ leastresp } ) )
		{
			if ( $json_obj->{ leastresp } =~ /^$/ )
			{
				$error = "true";
				&logfile(
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
				&logfile(
					"ZAPI error, trying to modify the service $service in a farm $farmname, invalid leastresp."
				);
			}
		}

		if ( exists ( $json_obj->{ cookieinsert } ) )
		{
			if ( $json_obj->{ cookieinsert } =~ /^$/ )
			{
				$error = "true";
				&logfile(
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
				&logfile(
					"ZAPI error, trying to modify the service $service in a farm $farmname, invalid cookieinsert."
				);
			}
		}

		if ( exists ( $json_obj->{ cookiedomain } ) )
		{
			if ( $json_obj->{ cookiedomain } =~ /^$/ )
			{
				$error = "true";
				&logfile(
					"ZAPI error, trying to modify the service $service in a farm $farmname, invalid cookiedomain, can't be blank."
				);
			}
			else
			{
				&setFarmVS( $farmname, $service, "cookieins-domain",
							$json_obj->{ cookiedomain } );
			}
		}

		if ( exists ( $json_obj->{ cookiename } ) )
		{
			if ( $json_obj->{ cookiename } =~ /^$/ )
			{
				$error = "true";
				&logfile(
					"ZAPI error, trying to modify the service $service in a farm $farmname, invalid cookiename, can't be blank."
				);
			}
			else
			{
				&setFarmVS( $farmname, $service, "cookieins-name", $json_obj->{ cookiename } );
			}
		}

		if ( exists ( $json_obj->{ cookiepath } ) )
		{
			if ( $json_obj->{ cookiepath } =~ /^$/ )
			{
				$error = "true";
				&logfile(
					"ZAPI error, trying to modify the service $service in a farm $farmname, invalid cookiepath, can't be blank."
				);
			}
			else
			{
				&setFarmVS( $farmname, $service, "cookieins-path", $json_obj->{ cookiepath } );
			}
		}

		if ( exists ( $json_obj->{ cookiettl } ) )
		{
			if ( $json_obj->{ cookiettl } =~ /^$/ )
			{
				$error = "true";
				&logfile(
					"ZAPI error, trying to modify the service $service in a farm $farmname, invalid cookiettl, can't be blank."
				);
			}
			else
			{
				&setFarmVS( $farmname, $service, "cookieins-ttlc", $json_obj->{ cookiettl } );
			}
		}

		if ( exists ( $json_obj->{ httpsb } ) )
		{
			if ( $json_obj->{ httpsb } =~ /^$/ )
			{
				$error = "true";
				&logfile(
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
				&logfile(
					"ZAPI error, trying to modify the service $service in a farm $farmname, invalid httpsb."
				);
			}
		}
	}

	if ( $type eq "gslb" )
	{
		# Functions
		if ( $json_obj->{ deftcpport } =~ /^$/ )
		{
			$error = "true";
			&logfile(
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
				&logfile(
					"ZAPI error, trying to modify the service $service in a farm $farmname, it's not possible to change the deftcpport parameter."
				);
			}
		}
	}

	# Print params
	if ( $error ne "true" )
	{
		&setFarmRestart( $farmname );

		&logfile(
			"ZAPI success, some parameters have been changed  in service $service in farm $farmname."
		);

		# Success
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '200 OK'
		);

		foreach $key ( keys %$json_obj )
		{
			push $out_p, { $key => $json_obj->{ $key } };
		}

		my $j = JSON::XS->new->utf8->pretty( 1 );
		$j->canonical( $enabled );
		my $output = $j->encode(
			{
			   description => "Modify service $service in farm $farmname",
			   params      => $out_p,
			   info =>
				 "There're changes that need to be applied, stop and start farm to apply them!"
			}
		);
		print $output;

	}
	else
	{
		&logfile(
			"ZAPI error, trying to modify the zones in a farm $farmname, it's not possible to modify the service $service."
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request'
		);
		$errormsg = "Errors found trying to modify farm $farmname";
		my $output = $j->encode(
							  {
								description => "Modify service $service in farm $farmname",
								error       => "true",
								message     => $errormsg
							  }
		);
		print $output;
		exit;

	}

}

1
