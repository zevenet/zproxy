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
#  @apiVersion 1.0.0
#
#
#
# @apiSuccess   {String}        interface                Interface where the farm will be created.
# @apiSuccess	{Number}	vport			PORT of the farm, where is listening the virtual service.
# @apiSuccess	{String}	profile			The protocol of the created Farm. The options are: TCP, UDP, HTTP, L4xNAT, DATALINK and GSLB.
# @apiSuccess   {String}        vip                      IP of the farm, where is listening the virtual service.
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
#       https://<zenlb_server>:444/zapi/v1/zapi.cgi/farms/newfarmTCP
#
# @apiSampleRequest off
#
#**


our $origin;
if ($origin ne 1){
    exit;
}

sub new_farm() {

	$farmname = @_[0];

	my $out_p = [];

	use CGI;
	use JSON;

	my $q = CGI->new;
	my $json = JSON->new;
	my $data = $q->param('POSTDATA');
	my $json_obj = $json->decode($data);

	$farmname =~ s/\ //g;
	$farmname =~ s/\_//g;
	&setFarmName($farmname);
	$error = "false";

	my $j = JSON::XS->new->utf8->pretty(1);
	$j->canonical($enabled);

	if ($json_obj->{vip} eq ""){
	
		# Error
		print $q->header(
		   -type=> 'text/plain',
		   -charset=> 'utf-8',
		   -status=> '400 Bad Request'
		);
		$errormsg = "Please especify a Virtual IP";
		my $output = $j->encode({
			description => "New farm $farmname",
			error => "true",
			message => $errormsg
		});
		print $output;
		exit;
	}

	if ($farmname =~ /^$/){
		
		# Error
		print $q->header(
		   -type=> 'text/plain',
		   -charset=> 'utf-8',
		   -status=> '400 Bad Request'
		);
		$errormsg = "The farm name can't be empty";
		my $output = $j->encode({
			description => "New farm $farmname",
			error => "true",
			message => $errormsg
		});
		print $output;
		exit;
	}

	if ($farmprotocol =~ /TCP|HTTP|UDP|HTTPS|GSLB|L4XNAT|DATALINK/ ) {
		if (&isnumber($json_obj->{vport}) eq "true"){
			$inuse = &checkport($json_obj->{vip},$json_obj->{vport});
			if ($inuse eq "true"){
			
				# Error
				print $q->header(
				   -type=> 'text/plain',
				   -charset=> 'utf-8',
				   -status=> '422 Unprocessable Entity'
				);
				$errormsg = "The Virtual Port ".$json_obj->{vport}." in Virtual IP ".$json_obj->{vip}." is in use, select another port or add another Virtual IP";
				my $output = $j->encode({
					description => "New farm $farmname",
					error => "true",
					message => $errormsg
				});
				print $output;
				exit;
			}
		} else {
			
			# Error
			print $q->header(
			   -type=> 'text/plain',
			   -charset=> 'utf-8',
			   -status=> '400 Bad Request'
			);
			$errormsg = "Invalid Virtual Port value, it must be numeric";
			my $output = $j->encode({
				description => "New farm $farmname",
				error => "true",
				message => $errormsg
			});
			print $output;
			exit;
		}
	}

	my $fdev = $json_obj->{interface};

	$status = &runFarmCreate($json_obj->{profile},$json_obj->{vip},$json_obj->{vport},$farmname,$fdev);
	if ($status == -1){
		
		# Error
		print $q->header(
		   -type=> 'text/plain',
		   -charset=> 'utf-8',
		   -status=> '400 Bad Request'
		);
		$errormsg = "The $farmname farm can't be created";
		my $output = $j->encode({
			description => "New farm $farmname",
			error => "true",
			message => $errormsg
		});
		print $output;
		exit;
	}
	if ($status == -2){
		
		# Error
		print $q->header(
		   -type=> 'text/plain',
		   -charset=> 'utf-8',
		   -status=> '422 Unprocessable Entity'
		);
		$errormsg = "The $farmname farm already exists, please set a different farm name";
		my $output = $j->encode({
			description => "New farm $farmname",
			error => "true",
			message => $errormsg
		});
		print $output;
		exit;
	}
	
	# Success
	print $q->header(
	   -type=> 'text/plain',
	   -charset=> 'utf-8',
	   -status=> '201 Created'
	);
	push $out_p, { name => $farmname, profile => $json_obj->{profile}, vip => $json_obj->{vip}, vport => $json_obj->{vport}+0, interface => $fdev };
	my $j = JSON::XS->new->utf8->pretty(1);
	$j->canonical($enabled);
	my $output = $j->encode({
		description => "New farm $farmname",
		params => $out_p
	});
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
#  @api {post} /farms/<farmname>/backends Create a new Backend in a tcp Farm
#  @apiGroup Farm Create
#  @apiName PostFarmBackendTCP
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiDescription Create a new Backend of a given TCP Farm
#  @apiVersion 1.0.0
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
#       "priority":"1", "weight":"1"}' https://<zenlb_server>:444/zapi/v1/zapi.cgi/farms/FarmTCP/backends
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
#  @apiVersion 1.0.0
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
#       "service":"service1"}' https://<zenlb_server>:444/zapi/v1/zapi.cgi/farms/FarmHTTP/backends
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
#  @apiVersion 1.0.0
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
#       https://<zenlb_server>:444/zapi/v1/zapi.cgi/farms/FarmGSLB/backends
#
# @apiSampleRequest off
#
#**


sub new_farm_backend() {
	
	$farmname = @_[0];

	my $out_p = [];

	use CGI;
	use JSON;

	my $q = CGI->new;
	my $json = JSON->new;
	my $data = $q->param('POSTDATA');
	my $json_obj = $json->decode($data);

	my $j = JSON::XS->new->utf8->pretty(1);
	$j->canonical($enabled);
	
	if ($farmname =~ /^$/){
		
		# Error
		print $q->header(
		   -type=> 'text/plain',
		   -charset=> 'utf-8',
		   -status=> '400 Bad Request'
		);
		$errormsg = "Invalid farm name, please insert a valid value.";
		my $output = $j->encode({
			description => "New backend",
			error => "true",
			message => $errormsg
		});
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
	
	my $type = &getFarmType($farmname);
	
	if ($type eq "tcp" || $type eq "udp"){
	
		# ID = ID of the last backend server + 1
		my $id = 0;
		my $server = "false";
		my @run = &getFarmServers($farmname);
		
		foreach $l_servers(@run){
			my @l_serv = split("\ ",$l_servers);
			if (@l_serv[2] ne "0.0.0.0"){
				if (@l_serv[0]+0 >= $id) {
					$id = @l_serv[0]+0;
					$server = "true";
				}
			}
		}
		if ($server eq "true") {
			$id++;
		}

	
		if (&ipisok($json_obj->{ip}) eq "false"){
			
			# Error
			$error = 1;
			print $q->header(
			   -type=> 'text/plain',
			   -charset=> 'utf-8',
			   -status=> '400 Bad Request'
			);
			$errormsg = "Invalid real server IP value, please insert a valid value.";
			my $output = $j->encode({
				description => "New backend $id",
				error => "true",
				message => $errormsg
			});
			print $output;
			exit;

		}
		if ($json_obj->{ip} =~ /^$/ || $json_obj->{port} =~ /^$/){
			
			# Error
			print $q->header(
			   -type=> 'text/plain',
			   -charset=> 'utf-8',
			   -status=> '400 Bad Request'
			);
			$errormsg = "Invalid IP address and port for a real server, it can't be blank.";
			my $output = $j->encode({
				description => "New backend $id",
				error => "true",
				message => $errormsg
			});
			print $output;
			exit;
			
		}
		
		$status = &setFarmServer($id,$json_obj->{ip},$json_obj->{port},$json_obj->{maxconnections},$json_obj->{weight},$json_obj->{priority},"",$farmname);
		if ($status != -1){
			
			# Success
			print $q->header(
			   -type=> 'text/plain',
			   -charset=> 'utf-8',
			   -status=> '201 Created'
			);
			push $out_p, { id => $id, ip => $json_obj->{ip}, port => $json_obj->{port}+0, maxconnections => $json_obj->{max_connections}+0, weight => $json_obj->{weight}+0, priority => $json_obj->{priority}+0 };				
			
			my $j = JSON::XS->new->utf8->pretty(1);
			$j->canonical($enabled);
			my $output = $j->encode({
				description => "New backend $id",
				params => $out_p
			});
			print $output;
			
		} else {

			# Error
			print $q->header(
			   -type=> 'text/plain',
			   -charset=> 'utf-8',
			   -status=> '400 Bad Request'
			);
			$errormsg = "It's not possible to create the real server with ip ".$json_obj->{ip}." and port ".$json_obj->{port}." for the $farmname farm";
			my $output = $j->encode({
				description => "New backend $id",
				error => "true",
				message => $errormsg
			});
			print $output;
			exit;
			
		}
	}
	if ($type eq "http" || $type eq "https"){
	
	
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
					description => "New backend",
					error => "true",
					message => $errormsg
			});
			print $output;
			exit;
			
		}
	

		my $backendsvs = &getFarmVS($farmname,$json_obj->{service},"backends");
		my @be = split("\n",$backendsvs);	
		foreach $subl(@be){
			my @subbe = split("\ ",$subl);
			$id = @subbe[1] + 1;
		}

		if ($id =~ /^$/){
			$id = 0;
		}		
	
		if (&ipisok($json_obj->{ip}) eq "false"){
			
			# Error
			$error = 1;
			print $q->header(
			   -type=> 'text/plain',
			   -charset=> 'utf-8',
			   -status=> '400 Bad Request'
			);
			$errormsg = "Invalid real server IP value, please insert a valid value.";
			my $output = $j->encode({
				description => "New backend $id",
				error => "true",
				message => $errormsg
			});
			print $output;
			exit;

		}
		
		if ($json_obj->{ip} =~ /^$/ || $json_obj->{port} =~ /^$/){
			
			# Error
			print $q->header(
			   -type=> 'text/plain',
			   -charset=> 'utf-8',
			   -status=> '400 Bad Request'
			);
			$errormsg = "Invalid IP address and port for a real server, it can't be blank.";
			my $output = $j->encode({
				description => "New backend $id",
				error => "true",
				message => $errormsg
			});
			print $output;
			exit;
			
		}
		
		if ($json_obj->{priority}  && ($json_obj->{priority} > 9 || $json_obj->{priority} < 1)){
			
			# Error
			print $q->header(
			   -type=> 'text/plain',
			   -charset=> 'utf-8',
			   -status=> '400 Bad Request'
			);
			$errormsg = "Invalid weight value for a real server, it must be 1-9.";
			my $output = $j->encode({
				description => "New backend $id",
				error => "true",
				message => $errormsg
			});
			print $output;
			exit;
		}
		
		# First param ($id) is an empty string to let function autogenerate the id for the new backend 
		$status = &setFarmServer("",$json_obj->{ip},$json_obj->{port},"","",$json_obj->{weight},$json_obj->{timeout},$farmname,$json_obj->{service});

		if ($status != -1){
			
			# Success
			&setFarmRestart($farmname);
			print $q->header(
			   -type=> 'text/plain',
			   -charset=> 'utf-8',
			   -status=> '201 Created'
			);
			push $out_p, { id => $id, ip => $json_obj->{ip}, port => $json_obj->{port}+0, weight => $json_obj->{weight}+0, timeout => $json_obj->{timeout}+0, service => $json_obj->{service} };				
			
			my $j = JSON::XS->new->utf8->pretty(1);
			$j->canonical($enabled);
			my $output = $j->encode({
				description => "New backend $id",
				params => $out_p
			});
			print $output;
			
		} else {

			# Error
			print $q->header(
			   -type=> 'text/plain',
			   -charset=> 'utf-8',
			   -status=> '400 Bad Request'
			);
			$errormsg = "It's not possible to create the real server with ip ".$json_obj->{ip}." and port ".$json_obj->{port}." for the $farmname farm";
			my $output = $j->encode({
				description => "New backend $id",
				error => "true",
				message => $errormsg
			});
			print $output;
			exit;
			
		}
	
	}
	if ($type eq "gslb") {
		
		$id = 1;
		my $lb = &getFarmVS($farmname,$json_obj->{service},"algorithm");
		my $backendsvs = &getFarmVS($farmname,$json_obj->{service},"backends");
		my @be = split("\n",$backendsvs);
		foreach $subline(@be){
			$subline =~ s/^\s+//;
			if ($subline =~ /^$/){
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
		
		
		if ($json_obj->{service} =~ /^$/){
			
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

		$status = &setGSLBFarmNewBackend($farmname,$json_obj->{service},$lb,$id,$json_obj->{ip});
		if ($status != -1){
			# Success
			&setFarmRestart($farmname);
			print $q->header(
			   -type=> 'text/plain',
			   -charset=> 'utf-8',
			   -status=> '201 Created'
			);
			push $out_p, { id => $id, ip => $json_obj->{ip}, service =>$json_obj->{service} };				
			
			my $j = JSON::XS->new->utf8->pretty(1);
			$j->canonical($enabled);
			my $output = $j->encode({
				description => "New backend $id",
				params => $out_p
			});
			print $output;
		} else {
			
			# Error
			print $q->header(
			   -type=> 'text/plain',
			   -charset=> 'utf-8',
			   -status=> '400 Bad Request'
			);
			$errormsg = "It's not possible to create the backend ".$json_obj->{ip}." for the service $service.";
			my $output = $j->encode({
				description => "New backend $id",
				error => "true",
				message => $errormsg
			});
			print $output;
			exit;
		}	
	}
	
	if ($type eq "l4xnat"){
		require "/usr/local/zenloadbalancer/www/zapi/v1/post_l4.cgi";
	}
	
	if ($type eq "datalink"){
		require "/usr/local/zenloadbalancer/www/zapi/v1/post_datalink.cgi";
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
#  @apiVersion 1.0.0
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
#       -u zapi:<password> -d '{"id":"newserv"}' https://<zenlb_server>:444/zapi/v1/zapi.cgi/farms/FarmHTTP/services
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
#  @apiVersion 1.0.0
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
#       https://<zenlb_server>:444/zapi/v1/zapi.cgi/farms/FarmGSLB/services
#
# @apiSampleRequest off
#
#**


sub new_farm_service() {
	
	$farmname = @_[0];

	my $out_p = [];

	use CGI;
	use JSON;

	my $q = CGI->new;
	my $json = JSON->new;
	my $data = $q->param('POSTDATA');
	my $json_obj = $json->decode($data);

	my $j = JSON::XS->new->utf8->pretty(1);
	$j->canonical($enabled);
	
	if ($farmname =~ /^$/){
		
		# Error
		print $q->header(
		   -type=> 'text/plain',
		   -charset=> 'utf-8',
		   -status=> '400 Bad Request'
		);
		$errormsg = "Invalid farm name, please insert a valid value.";
		my $output = $j->encode({
			description => "New service",
			error => "true",
			message => $errormsg
		});
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
	
	my $type = &getFarmType($farmname);
	
	if ($type eq "http" || $type eq "https"){
		
		if ($json_obj->{id} =~ /^$/){
			
			# Error
			print $q->header(
			   -type=> 'text/plain',
			   -charset=> 'utf-8',
			   -status=> '400 Bad Request'
			);
			$errormsg = "Invalid service, please insert a valid value.";
			my $output = $j->encode({
				description => "New service",
				error => "true",
				message => $errormsg
			});
			print $output;
			exit;
		}
		
		my $result = &setFarmHTTPNewService($farmname,$json_obj->{id});
		
		if ($result eq "0"){

			# Success
			&setFarmRestart($farmname);
			print $q->header(
			   -type=> 'text/plain',
			   -charset=> 'utf-8',
			   -status=> '201 Created'
			);
			push $out_p, { id => $json_obj->{id} };				
			
			my $j = JSON::XS->new->utf8->pretty(1);
			$j->canonical($enabled);
			my $output = $j->encode({
				description => "New service " . $json_obj->{id},
				params => $out_p
			});
			print $output;

		}
		if ($result eq "2"){
			
			# Error
			print $q->header(
			   -type=> 'text/plain',
			   -charset=> 'utf-8',
			   -status=> '400 Bad Request'
			);
			$errormsg = "New service can't be empty.";
			my $output = $j->encode({
				description => "New service " . $json_obj->{id},
				error => "true",
				message => $errormsg
			});
			print $output;
			exit;
			
		}
		if ($result eq "1"){
			
			# Error
			print $q->header(
			   -type=> 'text/plain',
			   -charset=> 'utf-8',
			   -status=> '400 Bad Request'
			);
			$errormsg = "Service named " . $json_obj->{id} . " already exists.";
			my $output = $j->encode({
				description => "New service " . $json_obj->{id},
				error => "true",
				message => $errormsg
			});
			print $output;
			exit;
			
		}
		if ($result eq "3"){

			# Error
			print $q->header(
			   -type=> 'text/plain',
			   -charset=> 'utf-8',
			   -status=> '400 Bad Request'
			);
			$errormsg = "Service name is not valid, only allowed numbers, letters and hyphens.";
			my $output = $j->encode({
				description => "New service " . $json_obj->{id},
				error => "true",
				message => $errormsg
			});
			print $output;
			exit;
		}
		
	}
	
	if ($type eq "gslb") {

		if ($json_obj->{id} =~ /^$/){
			
			# Error
			print $q->header(
			   -type=> 'text/plain',
			   -charset=> 'utf-8',
			   -status=> '400 Bad Request'
			);
			$errormsg = "Invalid service, please insert a valid value.";
			my $output = $j->encode({
				description => "New service " . $json_obj->{id},
				error => "true",
				message => $errormsg
			});
			print $output;
			exit;
		}
		
		if ($json_obj->{algorithm} =~ /^$/){

			# Error
			print $q->header(
			   -type=> 'text/plain',
			   -charset=> 'utf-8',
			   -status=> '400 Bad Request'
			);
			$errormsg = "Invalid algorithm, please insert a valid value.";
			my $output = $j->encode({
				description => "New service " . $json_obj->{id},
				error => "true",
				message => $errormsg
			});
			print $output;
			exit;
		}

		$status = &setGSLBFarmNewService($farmname,$json_obj->{id},$json_obj->{algorithm});
		if ($status != -1){

			# Success
			&runFarmReload($farmname);
			print $q->header(
			   -type=> 'text/plain',
			   -charset=> 'utf-8',
			   -status=> '201 Created'
			);
			push $out_p, { id => $json_obj->{id}, algorithm =>$json_obj->{algorithm} };				
			
			my $j = JSON::XS->new->utf8->pretty(1);
			$j->canonical($enabled);
			my $output = $j->encode({
				description => "New service " . $json_obj->{id},
				params => $out_p
			});
			print $output;
			
		} else {
			
			# Error
			print $q->header(
			   -type=> 'text/plain',
			   -charset=> 'utf-8',
			   -status=> '400 Bad Request'
			);
			$errormsg = "It's not possible to create the service " . $json_obj->{id};
			my $output = $j->encode({
				description => "New service " . $json_obj->{id},
				error => "true",
				message => $errormsg
			});
			print $output;
			exit;
			
		}
	}
}

#
# curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin -d '{"id":"zone123"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/FarmGSLB/zones
#
#
#####Documentation of POST ZONES GSLB####
#**
#  @api {post} /farms/<farmname>/zones Create a new zone in a gslb Farm
#  @apiGroup Farm Create
#  @apiName PostZoneGSLB
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiDescription Create a new zone in a given gslb Farm
#  @apiVersion 1.0.0
#
#
#
# @apiSuccess   {String}        id                     Zone's name.
#
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "New zone myzone.com",
#   "params" : [
#      {
#         "id" : "myzone.com"
#      }
#   ]
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#       -u zapi:<password> -d '{"id":"myzone.com"}' https://<zenlb_server>:444/zapi/v1/zapi.cgi/farms/FarmGSLB/zones
#
# @apiSampleRequest off
#
#**


sub new_farm_zone() {
	
	$farmname = @_[0];

	my $out_p = [];

	use CGI;
	use JSON;

	my $q = CGI->new;
	my $json = JSON->new;
	my $data = $q->param('POSTDATA');
	my $json_obj = $json->decode($data);

	my $j = JSON::XS->new->utf8->pretty(1);
	$j->canonical($enabled);
	
	if ($farmname =~ /^$/){
		
		# Error
		print $q->header(
		   -type=> 'text/plain',
		   -charset=> 'utf-8',
		   -status=> '400 Bad Request'
		);
		$errormsg = "Invalid farm name, please insert a valid value.";
		my $output = $j->encode({
			description => "New zone",
			error => "true",
			message => $errormsg
		});
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
				description => "New zone",
				error => "true",
				message => $errormsg
		});
		print $output;
		exit;

	}
	
	if ($json_obj->{id} =~ /^$/){
			
		# Error
		print $q->header(
		   -type=> 'text/plain',
		   -charset=> 'utf-8',
		   -status=> '400 Bad Request'
		);
		$errormsg = "Invalid zone name, please insert a valid value.";
		my $output = $j->encode({
			description => "New zone " . $json_obj->{id},
			error => "true",
			message => $errormsg
		});
		print $output;
		exit;
	}
	
	if ( $json_obj->{ id } !~ /.*\..*/ )
        {
                &logfile(
                        "Wrong zone name. The name has to be like zonename.com, zonename.net, etc. The zone $zone can't be created"
                );

                # Error
                print $q->header(
                                                  -type    => 'text/plain',
                                                  -charset => 'utf-8',
                                                  -status  => '400 Bad Request'
                );
                $errormsg =
                  "Invalid zone name, please insert a valid value like zonename.com, zonename.net, etc. The zone $zone can't be created.";
                my $output = $j->encode(
                                                                 {
                                                                   description => "New zone " . $json_obj->{ id },
                                                                   error       => "true",
                                                                   message     => $errormsg
                                                                 }
                );
                print $output;
                exit;
        }

	
	my $result = &setGSLBFarmNewZone($farmname,$json_obj->{id});
	if ($result eq "0"){
		
		# Success
		&runFarmReload($farmname);
		print $q->header(
		   -type=> 'text/plain',
		   -charset=> 'utf-8',
		   -status=> '201 Created'
		);
		push $out_p, { id => $json_obj->{id} };				
		
		my $j = JSON::XS->new->utf8->pretty(1);
		$j->canonical($enabled);
		my $output = $j->encode({
			description => "New zone " . $json_obj->{id},
			params => $out_p
		});
		print $output;	
		
	} else {
		
		# Error
		print $q->header(
		   -type=> 'text/plain',
		   -charset=> 'utf-8',
		   -status=> '400 Bad Request'
		);
		$errormsg = "It's not possible to create the zone " . $json_obj->{id};
		my $output = $j->encode({
			description => "New zone " . $json_obj->{id},
			error => "true",
			message => $errormsg
		});
		print $output;
		exit;
	}
	
}

#
# curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin -d '{"zone":"zone123","rname":"resource1","ttl":"10","type":"NS","rdata":"1.1.1.1"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/FarmGSLB/zoneresources
#
#
#####Documentation of POST RESOURCES GSLB####
#**
#  @api {post} /farms/<farmname>/zoneresources Create a new resource of a zone in a gslb Farm
#  @apiGroup Farm Create
#  @apiName PostZoneResourceGSLB
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiDescription Create a new resource of a zone in a given gslb Farm
#  @apiVersion 1.0.0
#
#
#
# @apiSuccess   {String}        rname                     Resource's name.
# @apiSuccess	{rdata}		rdata			It’s the real data needed by the record type.
# @apiSuccess	{Number}	ttl			The Time to Live value for the current record.
# @apiSuccess	{String}	type			DNS record type. The options are: NS, A, CNAME and DYNA.
# @apiSuccess	{String}	zone			It's the zone where the resource will be created.
#
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "New zone resource resource2",
#   "params" : [
#      {
#         "rname" : "resource2",
#         "rdata" : "192.168.0.9",
#         "ttl" : "10",
#         "type" : "NS",
#         "zone" : "zone1"
#      }
#   ]
#}
#
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#       -u zapi:<password> -d '{"rname":"resource2", "rdata":"192.168.0.9", "ttl":"10", "type":"NS",
#       "zone":"zone1"}' https://<zenlb_server>:444/zapi/v1/zapi.cgi/farms/FarmGSLB/zoneresources
#
# @apiSampleRequest off
#
#**


sub new_farm_zoneresource() {
	
	$farmname = @_[0];

	my $out_p = [];

	use CGI;
	use JSON;

	my $q = CGI->new;
	my $json = JSON->new;
	my $data = $q->param('POSTDATA');
	my $json_obj = $json->decode($data);

	my $j = JSON::XS->new->utf8->pretty(1);
	$j->canonical($enabled);
	
	if ($farmname =~ /^$/){
		
		# Error
		print $q->header(
		   -type=> 'text/plain',
		   -charset=> 'utf-8',
		   -status=> '400 Bad Request'
		);
		$errormsg = "Invalid farm name, please insert a valid value.";
		my $output = $j->encode({
			description => "New zone resource",
			error => "true",
			message => $errormsg
		});
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
				description => "New zone resource",
				error => "true",
				message => $errormsg
		});
		print $output;
		exit;

	}
	
	if ($json_obj->{rname} =~ /^$/){
			
		# Error
		print $q->header(
		   -type=> 'text/plain',
		   -charset=> 'utf-8',
		   -status=> '400 Bad Request'
		);
		$errormsg = "Invalid zone resource name, please insert a valid value.";
		my $output = $j->encode({
			description => "New zone resource " . $json_obj->{rname},
			error => "true",
			message => $errormsg
		});
		print $output;
		exit;
	}
	
	if ($json_obj->{rdata} =~ /^$/){
			
		# Error
		print $q->header(
		   -type=> 'text/plain',
		   -charset=> 'utf-8',
		   -status=> '400 Bad Request'
		);
		$errormsg = "Invalid zone resource server, please insert a valid value.";
		my $output = $j->encode({
			description => "New zone resource " . $json_obj->{rname},
			error => "true",
			message => $errormsg
		});
		print $output;
		exit;
	}

	$status = &setFarmZoneResource("",$json_obj->{rname},$json_obj->{ttl},$json_obj->{type},$json_obj->{rdata},$farmname,$json_obj->{zone});
	
	if ($status != -1){
		
		# Success
		&runFarmReload($farmname);
		print $q->header(
		   -type=> 'text/plain',
		   -charset=> 'utf-8',
		   -status=> '201 Created'
		);
		push $out_p, { rname => $json_obj->{rname}, zone => ,$json_obj->{zone}, ttl => $json_obj->{ttl}, type => $json_obj->{type}, rdata => $json_obj->{rdata} };				
		
		my $j = JSON::XS->new->utf8->pretty(1);
		$j->canonical($enabled);
		my $output = $j->encode({
			description => "New zone resource " . $json_obj->{rname},
			params => $out_p
		});
		print $output;
		
	} else {
		
		# Error
		print $q->header(
		   -type=> 'text/plain',
		   -charset=> 'utf-8',
		   -status=> '400 Bad Request'
		);
		$errormsg = "It's not possible to modify the resource name ".$json_obj->{rdata}." for the zone " . $json_obj->{rname};
		my $output = $j->encode({
			description => "New zone resource " . $json_obj->{rname},
			error => "true",
			message => $errormsg
		});
		print $output;
		exit;
	}
}

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
#  @apiVersion 1.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Delete farm FarmTCP",
#   "message" : "The Farm FarmTCP has been deleted.",
#   "success" : "true"
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X DELETE -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#       -u zapi:<password> https://<zenlb_server>:444/zapi/v1/zapi.cgi/farms/FarmTCP
#
# @apiSampleRequest off
#
#**


sub delete_farm() {
	
	$farmname = @_[0];

	use CGI;
	my $q = CGI->new;

	my $j = JSON::XS->new->utf8->pretty(1);
	$j->canonical($enabled);
	
	if ($farmname =~ /^$/){
		
		# Error
		print $q->header(
		   -type=> 'text/plain',
		   -charset=> 'utf-8',
		   -status=> '400 Bad Request'
		);
		$errormsg = "Invalid farm name, please insert a valid value.";
		my $output = $j->encode({
			description => "Delete farm $farmname",
			error => "true",
			message => $errormsg
		});
		print $output;
		exit;
	}

	my $newffile = &getFarmFile($farmname);
        if ($newffile == -1){
        	print $q->header(
                   -type=> 'text/plain',
                   -charset=> 'utf-8',
                   -status=> '400 Bad Request'
                );
		$errormsg = "The farm $farmname doesn't exist, try another name.";
		my $output = $j->encode({
                        description => "Delete farm $farmname",
                        error => "true",
                        message => $errormsg
                });
                print $output;
		exit;
        }
	
	my $stat = &runFarmStop($farmname,"true");
	if ($stat == 0){
		# Success
	}

	$stat = &runFarmDelete($farmname);
	
	#print "stat: $stat\n";
	
	if ($stat == 0){
		
		# Success
		print $q->header(
		   -type=> 'text/plain',
		   -charset=> 'utf-8',
		   -status=> '200 OK'
		);		
		
		my $j = JSON::XS->new->utf8->pretty(1);
		$j->canonical($enabled);
		
		$message = "The Farm $farmname has been deleted.";
		my $output = $j->encode({
			description => "Delete farm $farmname",
			success => "true",
			message => $message
		});
		print $output;
		
	} else {

		# Error
		print $q->header(
		   -type=> 'text/plain',
		   -charset=> 'utf-8',
		   -status=> '400 Bad Request'
		);
		$errormsg = "The Farm $farmname hasn't been deleted";
		my $output = $j->encode({
			description => "Delete farm $farmname",
			error => "true",
			message => $errormsg
		});
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
#  @apiVersion 1.0.0
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
#       -u zapi:<password> https://<zenlb_server>:444/zapi/v1/zapi.cgi/farms/FarmGSLB/services/service1
#
# @apiSampleRequest off
#
#**


sub delete_service() {
	
	my ($farmname, $service) = @_;

	use CGI;
	my $q = CGI->new;

	my $j = JSON::XS->new->utf8->pretty(1);
	$j->canonical($enabled);
	
	if ($farmname =~ /^$/){
		
		# Error
		print $q->header(
		   -type=> 'text/plain',
		   -charset=> 'utf-8',
		   -status=> '400 Bad Request'
		);
		$errormsg = "Invalid farm name, please insert a valid value.";
		my $output = $j->encode({
			description => "Delete service",
			error => "true",
			message => $errormsg
		});
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
				description => "Delete service",
				error => "true",
				message => $errormsg
		});
		print $output;
		exit;

	}
	
	if ($service =~ /^$/){
		
		# Error
		print $q->header(
		   -type=> 'text/plain',
		   -charset=> 'utf-8',
		   -status=> '400 Bad Request'
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
	
	my $type = &getFarmType($farmname);
	
	# Check that the provided service is configured in the farm
	my @services;
	if ($type eq "gslb"){
		@services = &getGSLBFarmServices($farmname);
	} else {
		@services = &getFarmServices($farmname);
	}
	
	my $found = 0;
	foreach $farmservice (@services) {
		print "service: $farmservice";
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
				description => "Delete service",
				error => "true",
				message => $errormsg
		});
		print $output;
		exit;
		
	}
	
	my $ret;
	if ($type eq "http" || $type eq "https"){
		$ret = &deleteFarmService($farmname,$service);
    }
	if ($type eq "gslb"){
		$ret = &setGSLBFarmDeleteService($farmname,$service);
	}	

	if ($ret eq -2){

		# Error
		print $q->header(
						  -type    => 'text/plain',
						  -charset => 'utf-8',
						  -status  => '400 Bad Request'
		);
		
		my $j = JSON::XS->new->utf8->pretty(1);
		$j->canonical($enabled);
		
		$message = "The service $service in farm $farmname hasn't been deleted. The service is used by a zone.";
		my $output = $j->encode({
			description => "Delete service $service in farm $farmname.",
			error => "true",
			message => $message
		});
		print $output;
		
	}
	elsif ($ret eq 0){

		# Success
		&setFarmRestart($farmname);
		print $q->header(
		   -type=> 'text/plain',
		   -charset=> 'utf-8',
		   -status=> '200 OK'
		);		
		
		my $j = JSON::XS->new->utf8->pretty(1);
		$j->canonical($enabled);
		
		$message = "The service $service in farm $farmname has been deleted.";
		my $output = $j->encode({
			description => "Delete service $service in farm $farmname.",
			success => "true",
			message => $message
		});
		print $output;
		
	} else {
	
		# Error
		print $q->header(
		   -type=> 'text/plain',
		   -charset=> 'utf-8',
		   -status=> '400 Bad Request'
		);
		$errormsg = "Service $service in farm $farmname hasn't been deleted.";
		my $output = $j->encode({
			description => "Delete service $service in farm $farmname",
			error => "true",
			message => $errormsg
		});
		print $output;
		exit;
	
	}
}

#
# curl --tlsv1 -k -X DELETE -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/FarmGSLB/zones/zone1
#
#
#####Documentation of DELETE ZONE####
#**
#  @api {delete} /farms/<farmname>/zones/<zonename> Delete a zone of a  gslb Farm
#  @apiGroup Farm Delete
#  @apiName DeleteZone
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiParam {String} zonename  Zone name, unique ID.
#  @apiDescription Delete a given zone of a gslb Farm
#  @apiVersion 1.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Delete zone zone1 in farm FarmGSLB",
#   "message" : "The zone zone1 in farm FarmGSLB has been deleted.",
#   "success" : "true"
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X DELETE -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#       -u zapi:<password> https://<zenlb_server>:444/zapi/v1/zapi.cgi/farms/FarmGSLB/zones/zone1
#
# @apiSampleRequest off
#
#**


sub delete_zone() {
	
	my ($farmname, $zone) = @_;

	use CGI;
	my $q = CGI->new;

	my $j = JSON::XS->new->utf8->pretty(1);
	$j->canonical($enabled);
	
	if ($farmname =~ /^$/){
		
		# Error
		print $q->header(
		   -type=> 'text/plain',
		   -charset=> 'utf-8',
		   -status=> '400 Bad Request'
		);
		$errormsg = "Invalid farm name, please insert a valid value.";
		my $output = $j->encode({
			description => "Delete zone",
			error => "true",
			message => $errormsg
		});
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
				description => "Delete zone",
				error => "true",
				message => $errormsg
		});
		print $output;
		exit;

	}
	
	if ($zone =~ /^$/){
		
		# Error
		print $q->header(
		   -type=> 'text/plain',
		   -charset=> 'utf-8',
		   -status=> '400 Bad Request'
		);
		$errormsg = "Invalid zone name, please insert a valid value.";
		my $output = $j->encode({
			description => "Delete zone",
			error => "true",
			message => $errormsg
		});
		print $output;
		exit;
	}
	
	&setGSLBFarmDeleteZone($farmname,$zone);
	
	if ($? eq 0){

		# Success
		&runFarmReload($farmname);
		print $q->header(
		   -type=> 'text/plain',
		   -charset=> 'utf-8',
		   -status=> '200 OK'
		);		
		
		my $j = JSON::XS->new->utf8->pretty(1);
		$j->canonical($enabled);
		
		$message = "The zone $zone in farm $farmname has been deleted.";
		my $output = $j->encode({
			description => "Delete zone $zone in farm $farmname.",
			success => "true",
			message => $message
		});
		print $output;
		
	} else {
	
		# Error
		print $q->header(
		   -type=> 'text/plain',
		   -charset=> 'utf-8',
		   -status=> '400 Bad Request'
		);
		$errormsg = "Zone $zone in farm $farmname hasn't been deleted.";
		my $output = $j->encode({
			description => "Delete zone $zone in farm $farmname",
			error => "true",
			message => $errormsg
		});
		print $output;
		exit;
	
	}
}

#
# curl --tlsv1 -k -X DELETE -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/FarmTCP/backends/0
#
#
#####Documentation of DELETE BACKEND####
#**
#  @api {delete} /farms/<farmname>/backends/<backendid> Delete a backend of a Farm
#  @apiGroup Farm Delete
#  @apiName DeleteBackend
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiParam {Number} backendid  Backend ID, unique ID.
#  @apiDescription Delete a given backend of a tcp, udp, datalink or l4xnat Farm
#  @apiVersion 1.0.0
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
#       -u zapi:<password> https://<zenlb_server>:444/zapi/v1/zapi.cgi/farms/L4FARM/backends/4
#
# @apiSampleRequest off
#
#**


sub delete_backend() {
	
	my ($farmname, $id_server) = @_;

	use CGI;
	my $q = CGI->new;

	my $j = JSON::XS->new->utf8->pretty(1);
	$j->canonical($enabled);
	
	if ($farmname =~ /^$/){
		
		# Error
		print $q->header(
		   -type=> 'text/plain',
		   -charset=> 'utf-8',
		   -status=> '400 Bad Request'
		);
		$errormsg = "Invalid farm name, please insert a valid value.";
		my $output = $j->encode({
			description => "Delete backend",
			error => "true",
			message => $errormsg
		});
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
				description => "Delete backend",
				error => "true",
				message => $errormsg
		});
		print $output;
		exit;

	}
	
	if ($id_server =~ /^$/){
		
		# Error
		print $q->header(
		   -type=> 'text/plain',
		   -charset=> 'utf-8',
		   -status=> '400 Bad Request'
		);
		$errormsg = "Invalid backend id, please insert a valid value.";
		my $output = $j->encode({
			description => "Delete backend",
			error => "true",
			message => $errormsg
		});
		print $output;
		exit;
	}
	
	$status = &runFarmServerDelete($id_server,$farmname);
	if ($status != -1){
		
		# Success
		print $q->header(
		   -type=> 'text/plain',
		   -charset=> 'utf-8',
		   -status=> '200 OK'
		);		
		
		my $j = JSON::XS->new->utf8->pretty(1);
		$j->canonical($enabled);
		
		$message = "The real server with ID $id_server of the $farmname farm has been deleted.";
		my $output = $j->encode({
			description => "Delete backend $id_server in farm $farmname.",
			success => "true",
			message => $message
		});
		print $output;
		
	} else {
		
		# Error
		print $q->header(
		   -type=> 'text/plain',
		   -charset=> 'utf-8',
		   -status=> '400 Bad Request'
		);
		$errormsg = "It's not possible to delete the real server with ID $id_server of the $farmname farm.";
		my $output = $j->encode({
			description => "Delete backend $id_server in farm $farmname.",
			error => "true",
			message => $errormsg
		});
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
#  @apiVersion 1.0.0
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
#       -u zapi:<password> https://<zenlb_server>:444/zapi/v1/zapi.cgi/farms/newfarmHTTP/services/service1/backends/4
#
# @apiSampleRequest off
#
#**


sub delete_service_backend() {
	
	my ($farmname, $service, $id_server) = @_;

	use CGI;
	my $q = CGI->new;

	my $j = JSON::XS->new->utf8->pretty(1);
	$j->canonical($enabled);
	
	if ($farmname =~ /^$/){
		
		# Error
		print $q->header(
		   -type=> 'text/plain',
		   -charset=> 'utf-8',
		   -status=> '400 Bad Request'
		);
		$errormsg = "Invalid farm name, please insert a valid value.";
		my $output = $j->encode({
			description => "Delete service backend",
			error => "true",
			message => $errormsg
		});
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
				description => "Delete service backend",
				error => "true",
				message => $errormsg
		});
		print $output;
		exit;

	}
	
	if ($service =~ /^$/){
		
		# Error
		print $q->header(
		   -type=> 'text/plain',
		   -charset=> 'utf-8',
		   -status=> '400 Bad Request'
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
				description => "Delete service backend",
				error => "true",
				message => $errormsg
		});
		print $output;
		exit;
		
	}
	
	
	
	if ($id_server =~ /^$/){
		
		# Error
		print $q->header(
		   -type=> 'text/plain',
		   -charset=> 'utf-8',
		   -status=> '400 Bad Request'
		);
		$errormsg = "Invalid backend id, please insert a valid value.";
		my $output = $j->encode({
			description => "Delete service backend",
			error => "true",
			message => $errormsg
		});
		print $output;
		exit;
	}
	
	my $type = &getFarmType($farmname);
	if ($type eq "http" || $type eq "https"){	
		$status = &runFarmServerDelete($id_server,$farmname,$service);
	}
	if ($type eq "gslb"){
		$status = &remFarmServiceBackend($id_server,$farmname,$service);
	}

	if ($status != -1){
		
		# Success
		&setFarmRestart($farmname);
		print $q->header(
		   -type=> 'text/plain',
		   -charset=> 'utf-8',
		   -status=> '200 OK'
		);		
		
		my $j = JSON::XS->new->utf8->pretty(1);
		$j->canonical($enabled);
		
		$message = "The real server with ID $id_server in the service $service of the farm $farmname has been deleted.";
		my $output = $j->encode({
			description => "Delete backend with ID $id_server in the service $service of the farm $farmname.",
			success => "true",
			message => $message
		});
		print $output;
		
	} else {
		
		# Error
		print $q->header(
		   -type=> 'text/plain',
		   -charset=> 'utf-8',
		   -status=> '400 Bad Request'
		);
		$errormsg = "It's not possible to delete the real server with ID $id_server of the $farmname farm.";
		my $output = $j->encode({
			description => "Delete backend $id_server in the service $service of the farm $farmname.",
			error => "true",
			message => $errormsg
		});
		print $output;
		exit;
		
	}
}





#
# curl --tlsv1 -k -X DELETE -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/FarmGSLB/zones/zoneKKKKK/resources/0
#
#
#####Documentation of DELETE RESOURCE in a ZONE####
#**
#  @api {delete} /farms/<farmname>/zones/<zonename>/resources/<resourceid> Delete a resource of a Zone
#  @apiGroup Farm Delete
#  @apiName DeleteResource
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiParam {String} zonename  Zone name, unique ID.
#  @apiParam {Number} resourceid  Resource ID, unique ID.
#  @apiDescription Delete a given resource in a zone of a gslb Farm
#  @apiVersion 1.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Delete resource with ID 2 in the zonee zone1 of the farm FarmGSLB.",
#   "message" : "The resource with ID 2 in the zone zone1 of the farm FarmGSLB has been deleted.",
#   "success" : "true"
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X DELETE -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#       -u zapi:<password> https://<zenlb_server>:444/zapi/v1/zapi.cgi/farms/FarmGSLB/zones/zone1/resources/2
#
# @apiSampleRequest off
#
#**

sub delete_zone_resource() {
	
	my ($farmname, $zone, $id_server) = @_;

	use CGI;
	my $q = CGI->new;

	my $j = JSON::XS->new->utf8->pretty(1);
	$j->canonical($enabled);
	
	if ($farmname =~ /^$/){
		
		# Error
		print $q->header(
		   -type=> 'text/plain',
		   -charset=> 'utf-8',
		   -status=> '400 Bad Request'
		);
		$errormsg = "Invalid farm name, please insert a valid value.";
		my $output = $j->encode({
			description => "Delete zone resource",
			error => "true",
			message => $errormsg
		});
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
				description => "Delete zone resource",
				error => "true",
				message => $errormsg
		});
		print $output;
		exit;

	}
	
	if ($zone =~ /^$/){
		
		# Error
		print $q->header(
		   -type=> 'text/plain',
		   -charset=> 'utf-8',
		   -status=> '400 Bad Request'
		);
		$errormsg = "Invalid zone name, please insert a valid value.";
		my $output = $j->encode({
			description => "Delete zone resource",
			error => "true",
			message => $errormsg
		});
		print $output;
		exit;
	}
	
	if ($id_server =~ /^$/){
		
		# Error
		print $q->header(
		   -type=> 'text/plain',
		   -charset=> 'utf-8',
		   -status=> '400 Bad Request'
		);
		$errormsg = "Invalid resource id, please insert a valid value.";
		my $output = $j->encode({
			description => "Delete zone resource",
			error => "true",
			message => $errormsg
		});
		print $output;
		exit;
	}
	
	$status = &remFarmZoneResource($id_server,$farmname,$zone);
	if ($status != -1){
		
		# Success
		&runFarmReload($farmname);
		print $q->header(
		   -type=> 'text/plain',
		   -charset=> 'utf-8',
		   -status=> '200 OK'
		);		
		
		my $j = JSON::XS->new->utf8->pretty(1);
		$j->canonical($enabled);
		
		$message = "The resource with id $id_server in the zone $zone of the farm $farmnamehas been deleted.";
		my $output = $j->encode({
			description => "Delete resource with id $id_server in the zone $zone of the farm $farmname.",
			success => "true",
			message => $message
		});
		print $output;
		
	} else {
		
		# Error
		print $q->header(
		   -type=> 'text/plain',
		   -charset=> 'utf-8',
		   -status=> '400 Bad Request'
		);
		$errormsg = "It's not possible to delete the resource with id $id_server in the zone $zone of the farm $farmname.";
		my $output = $j->encode({
			description => "Delete resource with id $id_server in the zone $zone of the farm $farmname.",
			error => "true",
			message => $errormsg
		});
		print $output;
		exit;
		
	}
}


#upload .pem certs
sub upload_certs(){

        my $out_p = [];
	my $upload_dir= $configdir;

        use CGI;
        use JSON;

        my $q = CGI->new;
        my $json = JSON->new;
        #my $data = $q->param('POSTDATA');
        #my $json_obj = $json->decode($data);

        my $j = JSON::XS->new->utf8->pretty(1);
        $j->canonical($enabled);

	$filen = $q->param('filename');
	print "filename $filen or ". $q->param('filename') ." \n";

	if ($q->param('filename') =~ /.*\.pem$/){


###
	my $action = $q->param("action");
	my $filename = $q->param("fileup");

	my $upload_filehandle = $q->upload("fileup");

	print "ACTION IS $action and FILENAME is $filename<br><br>\n\n";
	if ($action eq "Upload" && $filename !~ /^$/)
	        {
	        if ($filename =~ /\.pem$/)
	                {
	                if ($filename =~ /\\/){
       		        @filen = split(/\\/,$filename);
                	$filename = $filen[-1];
                	        }

                	open ( UPLOADFILE, ">$upload_dir/$filename" ) or die "$!";
                	binmode UPLOADFILE;
                	while ( <$upload_filehandle> )
                	        {
                	        print UPLOADFILE;
                	        }
                	close UPLOADFILE;
                	print "<br>";
                	&successmsg("File $filename uploaded!");
                	}
        	else
        	        {
        	        print "<br>";
        	        &errormsg("file withuot pem extension");
        	        }
        	}


###




	}



}

1


