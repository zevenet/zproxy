#!/usr/bin/perl -w

# POST /farms/
#
# curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin -d '{"profile":"TCP","vip":"178.62.126.152","vport":"12345","interface":"eth0"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/newfarmTCP
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
#  @apiVersion 2.0.0
#
#
#
# @apiSuccess   {String}        interface                Interface where the farm will be created. Mandatory.
# @apiSuccess	{Number}	vport			PORT of the farm, where is listening the virtual service. Only mandatory in TCP, UDP, HTTP and GSLB profile.
# @apiSuccess	{String}	profile			The protocol of the created Farm. The options are: TCP, UDP, HTTP, L4xNAT, DATALINK and GSLB. Mandatory.
# @apiSuccess   {String}        vip                      IP of the farm, where is listening the virtual service. Mandatory.
#
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "New farm newfarmTCP",
#   "params" : [
#      {
#         "interface" : "eth0",
#         "name" : "newfarmTCP",
#         "vport" : 80,
#         "profile" : "TCP",
#         "vip" : "178.62.126.152"
#      }
#   ]
#}
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#       -u zapi:<password> -d '{"profile":"TCP", "vip":"178.62.126.152", "vport":"80","interface":"eth0"}'
#       https://<zenlb_server>:444/zapi/v2/zapi.cgi/farms/newfarmTCP
#
# @apiSampleRequest off
#
#**

our $origin;
if ( $origin ne 1 )
{
	exit;
}

sub new_farm()
{

	$farmname = @_[0];

	my $out_p = [];

	use CGI;
	use JSON;

	my $q        = CGI->new;
	my $json     = JSON->new;
	my $data     = $q->param( 'POSTDATA' );
	my $json_obj = $json->decode( $data );

	$farmname =~ s/\ //g;
	$farmname =~ s/\_//g;
	&setFarmName( $farmname );
	$error = "false";

	my $j = JSON::XS->new->utf8->pretty( 1 );
	$j->canonical( $enabled );

	if ( $json_obj->{ vip } eq "" )
	{
		&logfile(
			"ZAPI error, trying to create a new farm $farmname, invalid virtual IP value, it can't be blank."
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request'
		);
		$errormsg = "Please especify a Virtual IP";
		my $output = $j->encode(
								 {
								   description => "New farm $farmname",
								   error       => "true",
								   message     => $errormsg
								 }
		);
		print $output;
		exit;
	}

	if ( $farmname =~ /^$/ )
	{
		&logfile(
				  "ZAPI error, trying to create a new farm $farmname, invalid farm name." );

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request'
		);
		$errormsg = "The farm name can't be empty";
		my $output = $j->encode(
								 {
								   description => "New farm $farmname",
								   error       => "true",
								   message     => $errormsg
								 }
		);
		print $output;
		exit;
	}

	if ( $farmprotocol =~ /TCP|HTTP|UDP|HTTPS|GSLB|L4XNAT|DATALINK/ )
	{
		if ( &isnumber( $json_obj->{ vport } ) eq "true" )
		{
			$inuse = &checkport( $json_obj->{ vip }, $json_obj->{ vport } );
			if ( $inuse eq "true" )
			{
				&logfile(
					"ZAPI error, trying to create a new farm $farmname, the virtual port $json_obj->{vport} in virtual IP .$json_obj->{vip}. is in use."
				);

				# Error
				print $q->header(
								  -type    => 'text/plain',
								  -charset => 'utf-8',
								  -status  => '422 Unprocessable Entity'
				);
				$errormsg =
				    "The Virtual Port "
				  . $json_obj->{ vport }
				  . " in Virtual IP "
				  . $json_obj->{ vip }
				  . " is in use, select another port or add another Virtual IP";
				my $output = $j->encode(
										 {
										   description => "New farm $farmname",
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
			&logfile(
				"ZAPI error, trying to create a new farm $farmname, invalid virtual port value, must be numeric."
			);

			# Error
			print $q->header(
							  -type    => 'text/plain',
							  -charset => 'utf-8',
							  -status  => '400 Bad Request'
			);
			$errormsg = "Invalid Virtual Port value, it must be numeric";
			my $output = $j->encode(
									 {
									   description => "New farm $farmname",
									   error       => "true",
									   message     => $errormsg
									 }
			);
			print $output;
			exit;
		}
	}

	my $fdev = $json_obj->{ interface };

	$status = &runFarmCreate( $json_obj->{ profile },
							  $json_obj->{ vip },
							  $json_obj->{ vport },
							  $farmname, $fdev );
	if ( $status == -1 )
	{
		&logfile(
				  "ZAPI error, trying to create a new farm $farmname, can't be created." );

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request'
		);
		$errormsg = "The $farmname farm can't be created";
		my $output = $j->encode(
								 {
								   description => "New farm $farmname",
								   error       => "true",
								   message     => $errormsg
								 }
		);
		print $output;
		exit;
	}
	if ( $status == -2 )
	{
		&logfile(
			"ZAPI error, trying to create a new farm $farmname, the farm already exists, set a different farm name."
		);

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '422 Unprocessable Entity'
		);
		$errormsg =
		  "The $farmname farm already exists, please set a different farm name";
		my $output = $j->encode(
								 {
								   description => "New farm $farmname",
								   error       => "true",
								   message     => $errormsg
								 }
		);
		print $output;
		exit;
	}
	&logfile( "ZAPI success, the farm $farmname has been created successfully." );

	if ( $json_obj->{ vport } eq "" )
	{
		$vport = "*";
	}
	else
	{
		$vport = $json_obj->{ vport };
	}

	# Success
	print $q->header(
					  -type    => 'text/plain',
					  -charset => 'utf-8',
					  -status  => '201 Created'
	);
	if ( $json_obj->{ profile } eq "DATALINK" )
	{
		push $out_p,
		  {
			name      => $farmname,
			profile   => $json_obj->{ profile },
			vip       => $json_obj->{ vip },
			interface => $fdev
		  };
	}
	else
	{
		push $out_p,
		  {
			name      => $farmname,
			profile   => $json_obj->{ profile },
			vip       => $json_obj->{ vip },
			vport     => $vport,
			interface => $fdev
		  };
	}
	my $j = JSON::XS->new->utf8->pretty( 1 );
	$j->canonical( $enabled );
	my $output = $j->encode(
							 {
							   description => "New farm $farmname",
							   params      => $out_p
							 }
	);
	print $output;

}

#
# TCP:
#
# curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin -d '{"ip":"1.1.1.1","port":"80","maxconnections":"1000","weight":"1","priority":"1"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/newfarmTCP12345679/backends
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
#####Documentation of POST BACKENDS TCP####
#**
#  @api {post} /farms/<farmname>/backends Create a new Backend in a tcp|udp Farm
#  @apiGroup Farm Create
#  @apiName PostFarmBackendTCP
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiDescription Create a new Backend of a given TCP Farm
#  @apiVersion 2.0.0
#
#
#
# @apiSuccess   {String}        ip	                IP of the backend, where is listening the real service.
# @apiSuccess   {Number}        maxconnections		It’s the max number of concurrent connections that the current real server will be able to receive.
# @apiSuccess   {Number}        port                     PORT of the backend, where is listening the real service.
# @apiSuccess   {Number}        priority			It’s the priority value for the current real server.
# @apiSuccess   {Number}        weight			It's the weight value for the current real server.
#
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "New backend 0",
#   "params" : [
#      {
#         "id" : 0,
#         "ip" : "192.168.0.1",
#         "maxconnections" : 1000,
#         "port" : 80,
#         "priority" : 1,
#         "weight" : 1
#      }
#   ]
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#       -u zapi:<password> -d '{"maxconnections":"1000", "ip":"192.168.0.1", "port":"80",
#       "priority":"1", "weight":"1"}' https://<zenlb_server>:444/zapi/v2/zapi.cgi/farms/FarmTCP/backends
#
# @apiSampleRequest off
#
#**
#
#
#####Documentation of POST BACKENDS HTTP####
#**
#  @api {post} /farms/<farmname>/backends Create a new Backend in a http|https Farm
#  @apiGroup Farm Create
#  @apiName PostFarmBackendHTTP
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiDescription Create a new Backend of a given HTTP|HTTPS Farm
#  @apiVersion 2.0.0
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
#       "service":"service1"}' https://<zenlb_server>:444/zapi/v2/zapi.cgi/farms/FarmHTTP/backends
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
#  @apiVersion 2.0.0
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
#       https://<zenlb_server>:444/zapi/v2/zapi.cgi/farms/FarmGSLB/backends
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
#  @apiVersion 2.0.0
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
#       "weight":"2"}' https://<zenlb_server>:444/zapi/v2/zapi.cgi/farms/L4FARM/backends
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
#  @apiVersion 2.0.0
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
#       "priority":"3"}' https://<zenlb_server>:444/zapi/v2/zapi.cgi/farms/DATAFARM/backends
#
# @apiSampleRequest off
#**

sub new_farm_backend()
{

	$farmname = @_[0];

	my $out_p = [];

	use CGI;
	use JSON;

	my $q        = CGI->new;
	my $json     = JSON->new;
	my $data     = $q->param( 'POSTDATA' );
	my $json_obj = $json->decode( $data );

	my $j = JSON::XS->new->utf8->pretty( 1 );
	$j->canonical( $enabled );

	# Initial parameters
	my $priority = 1;
	my $weight   = 1;

	if ( $farmname =~ /^$/ )
	{
		&logfile(
			"ZAPI error, trying to create a new backend in farm $farmname, invalid farm name."
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
								   description => "New backend",
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
				description => "New backend",
				error => "true",
				message => $errormsg
		});
		print $output;
		exit;

	}

	my $type = &getFarmType( $farmname );

	if ( $type eq "tcp" || $type eq "udp" )
	{

		# ID = ID of the last backend server + 1
		my $id     = 0;
		my $server = "false";
		my @run    = &getFarmServers( $farmname );

		foreach $l_servers ( @run )
		{
			my @l_serv = split ( "\ ", $l_servers );
			if ( @l_serv[2] ne "0.0.0.0" )
			{
				if ( @l_serv[0] + 0 >= $id )
				{
					$id     = @l_serv[0] + 0;
					$server = "true";
				}
			}
		}
		if ( $server eq "true" )
		{
			$id++;
		}

		if ( &ipisok( $json_obj->{ ip } ) eq "false" )
		{
			&logfile(
				"ZAPI error, trying to create a new backend in farm $farmname, invalid real server IP value."
			);

			# Error
			$error = 1;
			print $q->header(
							  -type    => 'text/plain',
							  -charset => 'utf-8',
							  -status  => '400 Bad Request'
			);
			$errormsg = "Invalid real server IP value, please insert a valid value.";
			my $output = $j->encode(
									 {
									   description => "New backend $id",
									   error       => "true",
									   message     => $errormsg
									 }
			);
			print $output;
			exit;

		}
		if ( $json_obj->{ ip } =~ /^$/ || $json_obj->{ port } =~ /^$/ )
		{
			&logfile(
				"ZAPI error, trying to create a new backend in farm $farmname, invalid IP address and port for a real server, it can't be blank."
			);

			# Error
			print $q->header(
							  -type    => 'text/plain',
							  -charset => 'utf-8',
							  -status  => '400 Bad Request'
			);
			$errormsg = "Invalid IP address and port for a real server, it can't be blank.";
			my $output = $j->encode(
									 {
									   description => "New backend $id",
									   error       => "true",
									   message     => $errormsg
									 }
			);
			print $output;
			exit;

		}

		$status = &setFarmServer(
								  $id,
								  $json_obj->{ ip },
								  $json_obj->{ port },
								  $json_obj->{ maxconnections },
								  $json_obj->{ weight },
								  $json_obj->{ priority },
								  "",
								  $farmname
		);

		if ( $status != -1 )
		{
			&logfile(
				"ZAPI success, a new backend has been created in farm $farmname with IP $json_obj->{ip}."
			);

			# Success
			print $q->header(
							  -type    => 'text/plain',
							  -charset => 'utf-8',
							  -status  => '201 Created'
			);
			push $out_p,
			  {
				id             => $id,
				ip             => $json_obj->{ ip },
				port           => $json_obj->{ port } + 0,
				maxconnections => $json_obj->{ maxconnections } + 0,
				weight         => $json_obj->{ weight } + 0,
				priority       => $json_obj->{ priority } + 0
			  };

			my $j = JSON::XS->new->utf8->pretty( 1 );
			$j->canonical( $enabled );
			my $output = $j->encode(
									 {
									   description => "New backend $id",
									   params      => $out_p
									 }
			);
			print $output;

		}
		else
		{

			# Error
			print $q->header(
							  -type    => 'text/plain',
							  -charset => 'utf-8',
							  -status  => '400 Bad Request'
			);
			$errormsg =
			    "It's not possible to create the real server with ip "
			  . $json_obj->{ ip }
			  . " and port "
			  . $json_obj->{ port }
			  . " for the $farmname farm";
			my $output = $j->encode(
									 {
									   description => "New backend $id",
									   error       => "true",
									   message     => $errormsg
									 }
			);
			print $output;
			exit;

		}
	}
	if ( $type eq "http" || $type eq "https" )
	{
	
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
					description => "Modify farm guardian",
					error => "true",
					message => $errormsg
			});
			print $output;
			exit;
			
		}

		my $backendsvs = &getFarmVS( $farmname, $json_obj->{ service }, "backends" );
		my @be = split ( "\n", $backendsvs );
		foreach $subl ( @be )
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
			&logfile(
				"ZAPI error, trying to create a new backend http in service $json_obj->{service} in farm $farmname, invalid real server IP value."
			);

			# Error
			$error = 1;
			print $q->header(
							  -type    => 'text/plain',
							  -charset => 'utf-8',
							  -status  => '400 Bad Request'
			);
			$errormsg = "Invalid real server IP value, please insert a valid value.";
			my $output = $j->encode(
									 {
									   description => "New backend $id",
									   error       => "true",
									   message     => $errormsg
									 }
			);
			print $output;
			exit;

		}

		if ( $json_obj->{ ip } =~ /^$/ || $json_obj->{ port } =~ /^$/ )
		{
			&logfile(
				"ZAPI error, trying to create a new backend http in service $json_obj->{service} in farm $farmname, invalid IP address and port for a real server, ir can't be blank."
			);

			# Error
			print $q->header(
							  -type    => 'text/plain',
							  -charset => 'utf-8',
							  -status  => '400 Bad Request'
			);
			$errormsg = "Invalid IP address and port for a real server, it can't be blank.";
			my $output = $j->encode(
									 {
									   description => "New backend $id",
									   error       => "true",
									   message     => $errormsg
									 }
			);
			print $output;
			exit;

		}

		if ( $json_obj->{ priority }
			 && ( $json_obj->{ priority } > 9 || $json_obj->{ priority } < 1 ) )
		{
			&logfile(
				"ZAPI error, trying to create a new backend http in service $json_obj->{service} in farm $farmname, invalid weight value for a real server, it must be 1-9."
			);

			# Error
			print $q->header(
							  -type    => 'text/plain',
							  -charset => 'utf-8',
							  -status  => '400 Bad Request'
			);
			$errormsg = "Invalid weight value for a real server, it must be 1-9.";
			my $output = $j->encode(
									 {
									   description => "New backend $id",
									   error       => "true",
									   message     => $errormsg
									 }
			);
			print $output;
			exit;
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
			&logfile(
				"ZAPI success, a new backend has been created in farm $farmname in service $json_obj->{service} with IP $json_obj->{ip}."
			);

			# Success
			&setFarmRestart( $farmname );
			print $q->header(
							  -type    => 'text/plain',
							  -charset => 'utf-8',
							  -status  => '201 Created'
			);
			push $out_p,
			  {
				id      => $id,
				ip      => $json_obj->{ ip },
				port    => $json_obj->{ port } + 0,
				weight  => $json_obj->{ weight } + 0,
				timeout => $json_obj->{ timeout } + 0,
				service => $json_obj->{ service }
			  };

			my $j = JSON::XS->new->utf8->pretty( 1 );
			$j->canonical( $enabled );
			my $output = $j->encode(
									 {
									   description => "New backend $id",
									   params      => $out_p
									 }
			);
			print $output;

		}
		else
		{

			# Error
			print $q->header(
							  -type    => 'text/plain',
							  -charset => 'utf-8',
							  -status  => '400 Bad Request'
			);
			$errormsg =
			    "It's not possible to create the real server with ip "
			  . $json_obj->{ ip }
			  . " and port "
			  . $json_obj->{ port }
			  . " for the $farmname farm";
			my $output = $j->encode(
									 {
									   description => "New backend $id",
									   error       => "true",
									   message     => $errormsg
									 }
			);
			print $output;
			exit;

		}

	}
	if ( $type eq "gslb" )
	{

		$id = 1;
		my $lb         = &getFarmVS( $farmname, $json_obj->{ service }, "algorithm" );
		my $backendsvs = &getFarmVS( $farmname, $json_obj->{ service }, "backends" );
		my @be = split ( "\n", $backendsvs );
		foreach $subline ( @be )
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
		foreach $service (@services) {
			print "service: $service";
			if ($json_obj->{service} eq $service) {
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
			$errormsg = "Invalid service, please insert a valid value.";
			my $output = $j->encode({
				description => "New backend $id",
				error => "true",
				message => $errormsg
			});
			print $output;
			exit;
		}
		

		if ( $json_obj->{ service } =~ /^$/ )
		{
			&logfile(
				"ZAPI error, trying to create a new backend gslb in service $json_obj->{service} farm $farmname, invalid service."
			);

			# Error
			print $q->header(
							  -type    => 'text/plain',
							  -charset => 'utf-8',
							  -status  => '400 Bad Request'
			);
			$errormsg = "Invalid service, please insert a valid value.";
			my $output = $j->encode(
									 {
									   description => "New backend $id",
									   error       => "true",
									   message     => $errormsg
									 }
			);
			print $output;
			exit;
		}

		$status = &setGSLBFarmNewBackend( $farmname, $json_obj->{ service },
										  $lb, $id, $json_obj->{ ip } );
		if ( $status != -1 )
		{
			&logfile(
				"ZAPI success, a new backend has been created in farm $farmname in service $json_obj->{service} with IP $json_obj->{ip}."
			);

			# Success
			&setFarmRestart( $farmname );
			print $q->header(
							  -type    => 'text/plain',
							  -charset => 'utf-8',
							  -status  => '201 Created'
			);
			push $out_p,
			  { id => $id, ip => $json_obj->{ ip }, service => $json_obj->{ service } };

			my $j = JSON::XS->new->utf8->pretty( 1 );
			$j->canonical( $enabled );
			my $output = $j->encode(
									 {
									   description => "New backend $id",
									   params      => $out_p
									 }
			);
			print $output;
		}
		else
		{

			# Error
			print $q->header(
							  -type    => 'text/plain',
							  -charset => 'utf-8',
							  -status  => '400 Bad Request'
			);
			$errormsg =
			    "It's not possible to create the backend "
			  . $json_obj->{ ip }
			  . " for the service $service.";
			my $output = $j->encode(
									 {
									   description => "New backend $id",
									   error       => "true",
									   message     => $errormsg
									 }
			);
			print $output;
			exit;
		}
	}

	if ( $type eq "l4xnat" )
	{
		######## Check errors

		if ( $farmname =~ /^$/ )
		{
			&logfile(
				"ZAPI error, trying to create a new backend l4xnat in farm $farmname, invalid farm name."
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
									   description => "New service",
									   error       => "true",
									   message     => $errormsg
									 }
			);
			print $output;
			exit;
		}

		# Get ID of the new backend
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
			&logfile(
				"ZAPI error, trying to create a new backend l4xnat in farm $farmname, invalid real server IP value."
			);

			# Error
			$error = 1;
			print $q->header(
							  -type    => 'text/plain',
							  -charset => 'utf-8',
							  -status  => '400 Bad Request'
			);
			$errormsg = "Invalid real server IP value, please insert a valid value.";
			my $output = $j->encode(
									 {
									   description => "New backend $id",
									   error       => "true",
									   message     => $errormsg
									 }
			);
			print $output;
			exit;

		}

		if ( $json_obj->{ ip } =~ /^$/ || $json_obj->{ port } =~ /^$/ )
		{
			&logfile(
				"ZAPI error, trying to create a new backend l4xnat in farm $farmname, invalid IP address and port for a real server, ir can't be blank."
			);

			# Error
			print $q->header(
							  -type    => 'text/plain',
							  -charset => 'utf-8',
							  -status  => '400 Bad Request'
			);
			$errormsg = "Invalid IP address and port for a real server, it can't be blank.";
			my $output = $j->encode(
									 {
									   description => "New backend $id",
									   error       => "true",
									   message     => $errormsg
									 }
			);
			print $output;
			exit;

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
				print $q->header(
								  -type    => 'text/plain',
								  -charset => 'utf-8',
								  -status  => '400 Bad Request'
				);
				$errormsg =
				  "Invalid real server priority value, please insert a value greater than or equal to 0.";
				my $output = $j->encode(
										 {
										   description => "New backend $id",
										   error       => "true",
										   message     => $errormsg
										 }
				);
				print $output;
				exit;
			}
			elsif ( $priority > 9 )
			{
				# Error
				print $q->header(
								  -type    => 'text/plain',
								  -charset => 'utf-8',
								  -status  => '400 Bad Request'
				);
				$errormsg =
				  "Invalid real server priority value, please insert a value less than or equal to 9.";
				my $output = $j->encode(
										 {
										   description => "New backend $id",
										   error       => "true",
										   message     => $errormsg
										 }
				);
				print $output;
				exit;
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
				print $q->header(
								  -type    => 'text/plain',
								  -charset => 'utf-8',
								  -status  => '400 Bad Request'
				);
				$errormsg =
				  "Invalid real server weight value, please insert a value greater than 0.";
				my $output = $j->encode(
										 {
										   description => "New backend $id",
										   error       => "true",
										   message     => $errormsg
										 }
				);
				print $output;
				exit;
			}

		}

####### Create backend

		$status = &setFarmServer( $id,
								  $json_obj->{ ip },
								  $json_obj->{ port },
								  "", $weight, $priority, "", $farmname );
		if ( $status != -1 )
		{
			&logfile(
				"ZAPI success, a new backend has been created in farm $farmname with IP $json_obj->{ip}."
			);

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

			# Success
			print $q->header(
							  -type    => 'text/plain',
							  -charset => 'utf-8',
							  -status  => '201 Created'
			);
			push $out_p,
			  {
				id       => $id,
				ip       => $json_obj->{ ip },
				port     => $json_obj->{ port } + 0,
				weight   => $weight,
				priority => $priority
			  };

			my $j = JSON::XS->new->utf8->pretty( 1 );
			$j->canonical( $enabled );
			my $output = $j->encode(
									 {
									   description => "New backend $id",
									   params      => $out_p
									 }
			);
			print $output;

		}
		else
		{

			# Error
			print $q->header(
							  -type    => 'text/plain',
							  -charset => 'utf-8',
							  -status  => '400 Bad Request'
			);
			$errormsg =
			    "It's not possible to create the real server with ip "
			  . $json_obj->{ ip }
			  . " and port "
			  . $json_obj->{ port }
			  . " for the $farmname farm";
			my $output = $j->encode(
									 {
									   description => "New backend $id",
									   error       => "true",
									   message     => $errormsg
									 }
			);
			print $output;
			exit;

		}

	}

	if ( $type eq "datalink" )
	{

		######## Params

		$farmname = @_[0];

		my $out_p = [];

		use CGI;
		use JSON;

		my $q        = CGI->new;
		my $json     = JSON->new;
		my $data     = $q->param( 'POSTDATA' );
		my $json_obj = $json->decode( $data );

		my $j = JSON::XS->new->utf8->pretty( 1 );
		$j->canonical( $enabled );

######## Check errors

		if ( $farmname =~ /^$/ )
		{
			&logfile(
				"ZAPI error, trying to create a new backend datalink in farm $farmname, invalid farm name."
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
									   description => "New service",
									   error       => "true",
									   message     => $errormsg
									 }
			);
			print $output;
			exit;
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
			&logfile(
				"ZAPI error, trying to create a new backend datalink in farm $farmname, invalid real server IP value."
			);

			# Error
			$error = 1;
			print $q->header(
							  -type    => 'text/plain',
							  -charset => 'utf-8',
							  -status  => '400 Bad Request'
			);
			$errormsg = "Invalid real server IP value, please insert a valid value.";
			my $output = $j->encode(
									 {
									   description => "New backend $id",
									   error       => "true",
									   message     => $errormsg
									 }
			);
			print $output;
			exit;

		}

		if ( $json_obj->{ ip } =~ /^$/ )
		{
			&logfile(
				"ZAPI error, trying to create a new backend datalink in farm $farmname, invalid farm name, it can't be blank."
			);

			# Error
			print $q->header(
							  -type    => 'text/plain',
							  -charset => 'utf-8',
							  -status  => '400 Bad Request'
			);
			$errormsg = "Invalid IP address for a real server, it can't be blank.";
			my $output = $j->encode(
									 {
									   description => "New backend $id",
									   error       => "true",
									   message     => $errormsg
									 }
			);
			print $output;
			exit;

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
			&logfile(
				"ZAPI success, a new backend has been created in farm $farmname with IP $json_obj->{ip}."
			);

			# Success
			print $q->header(
							  -type    => 'text/plain',
							  -charset => 'utf-8',
							  -status  => '201 Created'
			);
			push $out_p,
			  {
				id        => $id,
				ip        => $json_obj->{ ip },
				interface => $json_obj->{ interface },
				weight    => $json_obj->{ weight } + 0,
				priority  => $json_obj->{ priority } + 0
			  };

			my $j = JSON::XS->new->utf8->pretty( 1 );
			$j->canonical( $enabled );
			my $output = $j->encode(
									 {
									   description => "New backend $id",
									   params      => $out_p
									 }
			);
			print $output;

		}
		else
		{
			&logfile(
				"ZAPI error, trying to create a new backend datalink in farm $farmname, it's not possible to create the real server."
			);

			# Error
			print $q->header(
							  -type    => 'text/plain',
							  -charset => 'utf-8',
							  -status  => '400 Bad Request'
			);
			$errormsg =
			    "It's not possible to create the real server with ip "
			  . $json_obj->{ ip }
			  . " and port "
			  . $json_obj->{ port }
			  . " for the $farmname farm";
			my $output = $j->encode(
									 {
									   description => "New backend $id",
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
#  @apiVersion 2.0.0
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
#       -u zapi:<password> -d '{"id":"newserv"}' https://<zenlb_server>:444/zapi/v2/zapi.cgi/farms/FarmHTTP/services
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
#  @apiVersion 2.0.0
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
#       https://<zenlb_server>:444/zapi/v2/zapi.cgi/farms/FarmGSLB/services
#
# @apiSampleRequest off
#
#**

sub new_farm_service()
{

	$farmname = @_[0];

	my $out_p = [];

	use CGI;
	use JSON;

	my $q        = CGI->new;
	my $json     = JSON->new;
	my $data     = $q->param( 'POSTDATA' );
	my $json_obj = $json->decode( $data );

	my $j = JSON::XS->new->utf8->pretty( 1 );
	$j->canonical( $enabled );

	if ( $farmname =~ /^$/ )
	{
		&logfile(
			"ZAPI error, trying to create a new service in farm $farmname, invalid farm name."
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
								   description => "New service",
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
				description => "New service",
				error => "true",
				message => $errormsg
		});
		print $output;
		exit;

	}

	my $type = &getFarmType( $farmname );

	if ( $type eq "http" || $type eq "https" )
	{

		if ( $json_obj->{ id } =~ /^$/ )
		{
			&logfile(
				"ZAPI error, trying to create a new service in farm $farmname, invalid service name."
			);

			# Error
			print $q->header(
							  -type    => 'text/plain',
							  -charset => 'utf-8',
							  -status  => '400 Bad Request'
			);
			$errormsg = "Invalid service, please insert a valid value.";
			my $output = $j->encode(
									 {
									   description => "New service",
									   error       => "true",
									   message     => $errormsg
									 }
			);
			print $output;
			exit;
		}

		my $result = &setFarmHTTPNewService( $farmname, $json_obj->{ id } );

		if ( $result eq "0" )
		{
			&logfile(
				"ZAPI success, a new service has been created in farm $farmname with id $json_obj->{id}."
			);

			# Success
			&setFarmRestart( $farmname );
			print $q->header(
							  -type    => 'text/plain',
							  -charset => 'utf-8',
							  -status  => '201 Created'
			);
			push $out_p, { id => $json_obj->{ id } };

			my $j = JSON::XS->new->utf8->pretty( 1 );
			$j->canonical( $enabled );
			my $output = $j->encode(
									 {
									   description => "New service " . $json_obj->{ id },
									   params      => $out_p
									 }
			);
			print $output;

		}
		if ( $result eq "2" )
		{
			&logfile(
				"ZAPI error, trying to create a new service in farm $farmname, new service $json_obj->{id} can't be empty."
			);

			# Error
			print $q->header(
							  -type    => 'text/plain',
							  -charset => 'utf-8',
							  -status  => '400 Bad Request'
			);
			$errormsg = "New service can't be empty.";
			my $output = $j->encode(
									 {
									   description => "New service " . $json_obj->{ id },
									   error       => "true",
									   message     => $errormsg
									 }
			);
			print $output;
			exit;

		}
		if ( $result eq "1" )
		{
			&logfile(
				"ZAPI error, trying to create a new service in farm $farmname, the service $json_obj->{id} already exists."
			);

			# Error
			print $q->header(
							  -type    => 'text/plain',
							  -charset => 'utf-8',
							  -status  => '400 Bad Request'
			);
			$errormsg = "Service named " . $json_obj->{ id } . " already exists.";
			my $output = $j->encode(
									 {
									   description => "New service " . $json_obj->{ id },
									   error       => "true",
									   message     => $errormsg
									 }
			);
			print $output;
			exit;

		}
		if ( $result eq "3" )
		{
			&logfile(
				"ZAPI error, trying to create a new service in farm $farmname, the service name $json_obj->{id} is not valid, only allowed numbers,letters and hyphens."
			);

			# Error
			print $q->header(
							  -type    => 'text/plain',
							  -charset => 'utf-8',
							  -status  => '400 Bad Request'
			);
			$errormsg =
			  "Service name is not valid, only allowed numbers, letters and hyphens.";
			my $output = $j->encode(
									 {
									   description => "New service " . $json_obj->{ id },
									   error       => "true",
									   message     => $errormsg
									 }
			);
			print $output;
			exit;
		}

	}

	if ( $type eq "gslb" )
	{

		if ( $json_obj->{ id } =~ /^$/ )
		{
			&logfile(
				"ZAPI error, trying to create a new service in farm $farmname, invalid service name."
			);

			# Error
			print $q->header(
							  -type    => 'text/plain',
							  -charset => 'utf-8',
							  -status  => '400 Bad Request'
			);
			$errormsg = "Invalid service, please insert a valid value.";
			my $output = $j->encode(
									 {
									   description => "New service " . $json_obj->{ id },
									   error       => "true",
									   message     => $errormsg
									 }
			);
			print $output;
			exit;
		}

		if ( $json_obj->{ algorithm } =~ /^$/ )
		{
			&logfile(
				"ZAPI error, trying to create a new service in farm $farmname, invalid algorithm."
			);

			# Error
			print $q->header(
							  -type    => 'text/plain',
							  -charset => 'utf-8',
							  -status  => '400 Bad Request'
			);
			$errormsg = "Invalid algorithm, please insert a valid value.";
			my $output = $j->encode(
									 {
									   description => "New service " . $json_obj->{ id },
									   error       => "true",
									   message     => $errormsg
									 }
			);
			print $output;
			exit;
		}

		$status = &setGSLBFarmNewService( $farmname,
										  $json_obj->{ id },
										  $json_obj->{ algorithm } );
		if ( $status != -1 )
		{
			&logfile(
				"ZAPI success, a new service has been created in farm $farmname with id $json_obj->{id}."
			);

			# Success
			&runFarmReload( $farmname );
			print $q->header(
							  -type    => 'text/plain',
							  -charset => 'utf-8',
							  -status  => '201 Created'
			);
			push $out_p, { id => $json_obj->{ id }, algorithm => $json_obj->{ algorithm } };

			my $j = JSON::XS->new->utf8->pretty( 1 );
			$j->canonical( $enabled );
			my $output = $j->encode(
									 {
									   description => "New service " . $json_obj->{ id },
									   params      => $out_p
									 }
			);
			print $output;

		}
		else
		{
			&logfile(
				"ZAPI error, trying to create a new service in farm $farmname, it's not possible to create the service $json_obj->{id}."
			);

			# Error
			print $q->header(
							  -type    => 'text/plain',
							  -charset => 'utf-8',
							  -status  => '400 Bad Request'
			);
			$errormsg = "It's not possible to create the service " . $json_obj->{ id };
			my $output = $j->encode(
									 {
									   description => "New service " . $json_obj->{ id },
									   error       => "true",
									   message     => $errormsg
									 }
			);
			print $output;
			exit;

		}
	}
}

1

