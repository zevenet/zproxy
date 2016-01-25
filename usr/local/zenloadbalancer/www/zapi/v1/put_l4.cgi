#!/usr/bin/perl -w

######### PUT L4XNAT
#
# curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin -d '{"algorithm":"weight","persistence":"none","newfarmname":"newfarmEUL4","protocol":"tcp","nattype":"nat","ttl":"125","vip":"178.62.126.152","port":"81"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/L4FARM
#
#
#####Documentation of PUT L4XNAT####
#**
#  @api {put} /farms/<farmname> Modify a l4xnat Farm
#  @apiGroup Farm Modify
#  @apiName PutFarmL4XNAT
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiDescription Modify the params in a L4XNAT Farm
#  @apiVersion 1.0.0
#
#
#
# @apiSuccess	{String}		algorithm	Type of load balancing algorithm used in the Farm. The options are: leastconn, weight or prio.
# @apiSuccess	{String}		persistence	With this option enabled all the clients with the same ip address will be connected to the same server. The options are: none or ip.
# @apiSuccess	{String}		newfarmname	The new Farm's name.
# @apiSuccess	{String}		protocol	This field specifies the protocol to be balanced at layer 4. The options are: all, tcp, udp, sip, ftp or tftp.
# @apiSuccess	{String}		nattype		This field indicates the NAT type which means how the load balancer layer 4 core is going to operate. The options are: nat or dnat.
# @apiSuccess	{Number}		ttl			This field value indicates the number of seconds that the persistence between the client source and the backend is being assigned.
# @apiSuccess	{Number}		port			PORT of the farm, where is listening the virtual service.
# @apiSuccess	{String}		vip			IP of the farm, where is listening the virtual service.
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Modify farm newfarmEUL4",
#   "params" : [
#      {
#         "algorithm" : "weight"
#      },
#      {
#         "protocol" : "tcp"
#      },
#      {
#         "ttl" : "125"
#      },
#      {
#         "port" : "81"
#      },
#      {
#         "persistence" : "none"
#      },
#      {
#         "newfarmname" : "newfarmL4"
#      },
#      {
#         "vip" : "178.62.126.152"
#      },
#      {
#         "nattype" : "nat"
#      }
#   ]
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#       -u zapi:<password> -d '{"algorithm":"weight","persistence":"none","newfarmname":"newfarmL4",
#       "protocol":"tcp","nattype":"nat","ttl":"125","vip":"178.62.126.152","port":"81"}'
#        https://<zenlb_server>:444/zapi/v1/zapi.cgi/farms/L4FARM
#
# @apiSampleRequest off
#
#**

our $origin;
if ($origin ne 1){
    exit;
}

####### Params

	my $out_p = [];

        use CGI;
        use JSON;

        my $q = CGI->new;
        my $json = JSON->new;
        my $data = $q->param('PUTDATA');
        my $json_obj = $json->decode($data);

        my $j = JSON::XS->new->utf8->pretty(1);
        $j->canonical($enabled);

	# Flags
	my $reload_flag = "false";
        my $restart_flag = "false";
        my $error = "false";	

        # Get current vip & vport
        $vip = &getFarmVip("vip",$farmname);
        $vport = &getFarmVip("vipp",$farmname);

####### Functions

	# Modify Load Balance Algorithm
	if(exists($json_obj->{algorithm})){
		if ($json_obj->{algorithm} =~ /^$/){
			$error = "true";
		}
		if ($json_obj->{algorithm} =~ /^leastconn|weight|prio$/) {
			$status = &setFarmAlgorithm($json_obj->{algorithm},$farmname);
                        if ($status == -1){
                        	$error = "true";
                        } else {
				$restart_flag = "true";
			}
                } else {
			$error = "true";
                }
	}

	# Modify Persistence Mode
	if(exists($json_obj->{persistence})){
		if($json_obj->{persistence} =~ /^$/){
			$error = "true";
		}
		if ($json_obj->{persistence} =~ /^none|ip$/){
			$statusp = &setFarmSessionType($json_obj->{persistence},$farmname,"");
                	if ($statusp != 0){
				$error = "true";
			} else {
                                $restart_flag = "true";
                        }
		} else {
			$error = "true";
		}
	}	

	# Modify Protocol Type
	if(exists($json_obj->{protocol})){
		if ($json_obj->{protocol} =~ /^$/){
			$error = "true";
		}
		if ($json_obj->{protocol} =~ /^all|tcp|udp|sip|ftp|tftp$/){
        		$status = &setFarmProto($json_obj->{protocol},$farmname);
        		if ($status != 0){
                		$error = "true";
			} else {
				$restart_flag = "true";
			}
		} else {
			$error = "true";
		}
	}

	# Modify NAT Type
	if(exists($json_obj->{nattype})){
		if($json_obj->{nattype} =~ /^$/){
			$error = "true";
		}
		if($json_obj->{nattype} =~ /^nat|dnat$/){
		
			if (&getFarmNatType($farmname) ne $json_obj->{nattype}) {
				$status = &setFarmNatType($json_obj->{nattype},$farmname);			
					if ($status != 0){
					$error = "true";
				} else {
					$restart_flag = "true";
				}
			}
		} else {
                        $error = "true";
                }
	}

	# Modify IP Adress Persistence Time To Limit
	if(exists($json_obj->{ttl})){
		if($json_obj->{ttl} =~ /^$/){
			$error = "true";
		}
		elsif($json_obj->{ttl} =~ /^\d+$/){
			#$status = &setFarmMaxClientTime(0,$json_obj->{ttl},$farmname);
			if ($status != 0){
				$error = "true";
			} else {
                                $restart_flag = "true";
                        }
		} else {
                        $error = "true";
                }
	}

	# Modify only vip
	if(exists($json_obj->{vip}) && !exists($json_obj->{port})){
		if($json_obj->{vip} =~ /^$/){
			$error = "true";
		}elsif(!$json_obj->{vip} =~ /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/){
			$error = "true";
		}else{
			$status = &setFarmVirtualConf($json_obj->{vip},$vport,$farmname);
			if($status == -1){
				$error = "true";
			} else {
				$restart_flag = "true";
			}
		}
	}

	# Modify only vport
	if(exists($json_obj->{port}) && !exists($json_obj->{vip})){
		if($json_obj->{port} =~ /^$/){
                        $error = "true";
                }elsif(!$json_obj->{port} =~ /^\d+$/){
                        $error = "true";
                }else{
                        $status = &setFarmVirtualConf($vip,$json_obj->{port},$farmname);
                        if($status == -1){
                                $error = "true";
                        } else {
                                $restart_flag = "true";
                        }
                }
        }
		


	# Modify both vip & vport
	if (exists($json_obj->{vip}) && exists($json_obj->{port})) {
		if ($json_obj->{vip} =~ /^$/) {
			$error = "true";
		} elsif (!$json_obj->{vip} =~ /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/) {
			$error = "true";
		} else {
			if (exists($json_obj->{port})) {
				if ($json_obj->{port} =~ /^$/) {
					$error = "true";
				} elsif (!$json_obj->{port} =~ /^\d+$/) {
					$error = "true";
				} else {
					$status = &setFarmVirtualConf($json_obj->{vip},$json_obj->{port},$farmname);
					if ($status == -1){
						$error = "true";
					} else {
						$restart_flag = "true";
					}
				}
			}
		}
	}

        # Modify Farm's Name
        if (exists($json_obj->{newfarmname})){
                if($json_obj->{newfarmname} =~ /^$/){
                        $error = "true";
                } else {
						if ($json_obj->{newfarmname} ne $farmname) {
							#Check if farmname has correct characters (letters, numbers and hyphens)
							if($json_obj->{newfarmname} =~ /^[a-zA-Z0-9\-]*$/){
									#Check if the new farm's name alredy exists
									my $newffile = &getFarmFile($json_obj->{newfarmname});
									if ($newffile != -1){
											$error = "true";
									} else {
											#Change farm name
											my $fnchange = &setNewFarmName($farmname,$json_obj->{newfarmname});
											if ($fnchange == -1){
													&error = "true";
											} else {
													$restart_flag = "true";
							$farmname = $json_obj->{newfarmname};	
											}
									}
							} else {
									$error = "true";
							}
						}
                }
        }

	# Restart Farm
	if($restart_flag eq "true"){
		&runFarmStop($farmname,"true");
		&runFarmStart($farmname,"true");
	}

	# Check errors and print JSON
	if ($error ne "true") {
		
			# Success
			print $q->header(
			   -type=> 'text/plain',
			   -charset=> 'utf-8',
			   -status=> '200 OK'
			);
			
			foreach $key (keys %$json_obj) {
				push $out_p, { $key =>$json_obj->{$key}}
			}
			
			
			my $j = JSON::XS->new->utf8->pretty(1);
			$j->canonical($enabled);
			my $output = $j->encode({
				description => "Modify farm $farmname",
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
			$errormsg = "Errors found trying to modify farm $farmname";
			my $output = $j->encode({
				description => "Modify farm $farmname",
				error => "true",
				message => $errormsg
			});
			print $output;
			exit;
	}


1			
