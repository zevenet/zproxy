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
# TCP:
#
# curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin -d '{"algorithm":"roundrobin","persistence":"true","maxclients":"2049","tracking":"0","timeout":"5","connmax":"257","maxservers":"10","xforwardedfor":"true","blacklist":"30","vip":"178.62.126.152","vport":"12345"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/newfarmTCP
#
# curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin -d '{"algorithm":"prio","persistence":"false","maxclients":"2000","tracking":"10","timeout":"10","connmax":"513","maxservers":"100","xforwardedfor":"false","blacklist":"40","vip":"178.62.126.152","vport":"54321"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/newfarmTCP
#
#
#
#####Documentation of PUT TCP####
#**
#  @api {put} /farms/<farmname> Modify a tcp|udp Farm
#  @apiGroup Farm Modify
#  @apiName PutFarm
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiDescription Modify the params in a TCP|UDP Farm
#  @apiVersion 1.0.0
#
#
#
# @apiSuccess	{String}		algorithm	Type of load balancing algorithm used in the Farm. The options are: roundrobin, hash, weight or prio.
# @apiSuccess	{Number}		blacklist	This value in seconds is the period to get out a blacklisted real server and checks if is alive.
# @apiSuccess	{Number}		vport			PORT of the farm, where is listening the virtual service.
# @apiSuccess	{String}		persistence	With this option enabled all the clients with the same ip address will be connected to the same server. The options are true and false.
# @apiSuccess	{Number}		maxclients	The max number of clients that will be possible to memorize.
# @apiSuccess	{Number}		maxservers	It’s the max number of real servers that the farm will be able to have configured.
# @apiSuccess	{String}		newfarmname	The new Farm's name.
# @apiSuccess	{Number}		timeout		It’s the max seconds that the real server has to respond for a request.
# @apiSuccess	{String}		vip			IP of the farm, where is listening the virtual service.
# @apiSuccess	{Number}		tracking		is the max time of life for this clients to be memorized (the max client age).
# @apiSuccess	{Number}		connmax		It’s the max value of established connections and active clients that the virtual service will be able to manage.
# @apiSuccess	{String}		xforwardedfor	This option enables the HTTP header X-Forwarded-For to provide to the real server the ip client address.
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Modify farm newfarmTCP",
#   "params" : [
#      {
#         "algorithm" : "prio"
#      },
#      {
#         "blacklist" : "39"
#      },
#      {
#         "vport" : "5432"
#      },
#      {
#         "persistence" : "false"
#      },
#      {
#         "maxclients" : "2000"
#      },
#      {
#         "maxservers" : "99"
#      },
#      {
#         "newfarmname" : "newFarmTCP2"}
#      {
#         "timeout" : "8"
#      },
#      {
#         "vip" : "178.62.126.152"
#      },
#      {
#         "tracking" : "9"
#      },
#      {
#         "connmax" : "513"
#      },
#      {
#         "xforwardedfor" : "true"
#      }
#   ]
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#       -u zapi:<password> -d '{"algorithm":"prio","persistence":"false","maxclients":"2000","tracking":"10",
#       "newfarmname":"newFarmTCP2","connmax":"513",,"maxservers":"100","xforwardedfor":"false","vip":"178.62.126.152",
#       "vport":"54321","timeout":"10","blacklist":"40"}' https://<zenlb_server>:444/zapi/v1/zapi.cgi/farms/newFarmTCP
#
# @apiSampleRequest off
#
#**

our $origin;
if ($origin ne 1){
    exit;
}

sub modify_farm() {

	$farmname = @_[0];

	my $out_p = [];

	use CGI;
	use JSON;

	my $q = CGI->new;
	my $json = JSON->new;
	my $data = $q->param('PUTDATA');
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
			description => "Modify farm",
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
				description => "Modify farm",
				error => "true",
				message => $errormsg
		});
		print $output;
		exit;

	}
	
	my $type = &getFarmType($farmname);

    if ($type eq "http" || $type eq "https"){
        require "/usr/local/zenloadbalancer/www/zapi/v1/put_http.cgi";
    }

	if ($type eq "l4xnat"){
		require "/usr/local/zenloadbalancer/www/zapi/v1/put_l4.cgi";
	}

	if ($type eq "datalink"){
        require "/usr/local/zenloadbalancer/www/zapi/v1/put_datalink.cgi";
    }

	if ($type eq "gslb"){
        require "/usr/local/zenloadbalancer/www/zapi/v1/put_gslb.cgi";
    }
	
	if ($type eq "tcp" || $type eq "udp"){
	
		#global info for a farm
		$maxtimeout = "10000";
		$maxmaxclient = "3000000";
		$maxsimconn = "32760";
		$maxbackend = "10000";
	
		#use Data::Dumper;
		#print Dumper($json_obj);
		
		my $reload_flag = "false";
		my $restart_flag = "false";
		my $error = "false";
		
		#foreach $key (keys %$json_obj) {
		#	printf "%s => '%s'\n", $key, $json_obj->{$key};
		#}
		
		if (exists($json_obj->{algorithm})) {
			if ($json_obj->{algorithm} =~ /^$/) {
				$error = "true";
			}
			if ($json_obj->{algorithm} =~ /^roundrobin|hash|weight|prio$/) {
				my $status = &setFarmAlgorithm($json_obj->{algorithm},$farmname);
				if ($status == -1){
					$error = "true";
				}
			} else {
				$error = "true";
			}
		}
		
		if (exists($json_obj->{persistence})) {
			if ($json_obj->{persistence} =~ /^$/) {
				$error = "true";
			}
			if ($json_obj->{persistence} =~ /^true|false$/) {
				my $status = &setFarmPersistence($json_obj->{persistence},$farmname);
				if ($status == -1){
					$error = "true";
				}
			} else {
				$error = "true";
			}
		}
		
		# Modify Backend response timeout secs	
		if (exists($json_obj->{timeout})) {
			if ($json_obj->{timeout} =~ /^$/) {
				$error = "true";
			} elsif (!$json_obj->{timeout} =~ /^\d+$/) {
				$error = "true";
			} elsif (!$json_obj->{timeout} > $maxtimeout) {
				$error = "true";
			} else {
				my $status = &setFarmTimeout($json_obj->{timeout},$farmname);
				if ($status == -1){
					$error = "true";
				} else {
					$restart_flag = "true";
				}
			}
		}

		# Modify Add X-Forwarded-For header to http requests
		if (exists($json_obj->{xforwardedfor})) {
			if ($json_obj->{xforwardedfor} =~ /^$/) {
				$error = "true";
			}
			if ($json_obj->{xforwardedfor} =~ /^true|false$/) {
				my $status = &setFarmXForwFor($json_obj->{xforwardedfor},$farmname);
				if ($status == -1){
					$error = "true";
				}
			} else {
				$error = "true";
			}
		}
		
		# Modify Frequency to check resurrected backends secs
		if (exists($json_obj->{blacklist})) {
			if ($json_obj->{blacklist} =~ /^$/) {
				$error = "true";
			}
			if ($json_obj->{blacklist} =~ /^\d+$/) {
				my $status = &setFarmBlacklistTime($json_obj->{blacklist},$farmname);
				if ($status == -1){
					$error = "true";
				}
			} else {
				$error = "true";
			}
		}

		# Get current max_clients & tracking time
                @client = &getFarmMaxClientTime($farmname);
                if (@client == -1){
                        $maxclients = 256;
                        $tracking = 10;
                } else {
                        $maxclients = @client[0];
                        $tracking = @client[1];
                }

                # Modify both max_clients & tracking
                if (exists($json_obj->{maxclients}) && exists($json_obj->{tracking})) {
                        if ($json_obj->{maxclients} =~ /^$/) {
                                $error = "true";
                        } elsif (!$json_obj->{maxclients} =~ /^\d+$/) {
                                $error = "true";
                        } elsif ($json_obj->{maxclients} > $maxmaxclient){
                                $error = "true";
                        } else {
                                if (exists($json_obj->{tracking})) {
                                        if ($json_obj->{tracking} =~ /^$/) {
                                                $error = "true";
                                        } elsif (!$json_obj->{tracking} =~ /^\d+$/) {
                                                $error = "true";
                                        } else {

                                                # No error
                                                my $status = &setFarmMaxClientTime($json_obj->{maxclients},$json_obj->{tracking},$farmname);
                                                if ($status == -1){
                                                        $error = "true";
                                                } else {
                                                        $restart_flag = "true";
                                                }
                                        }
                                }
                        }
                }

		# Modify only max_clients param
                if (exists($json_obj->{maxclients}) && !exists($json_obj->{tracking})) {
                        if ($json_obj->{maxclients} =~ /^$/) {
                                $error = "true";
                        } elsif (!$json_obj->{maxclients} =~ /^\d+$/) {
                                $error = "true";
                        } elsif ($json_obj->{maxclients} > $maxmaxclient){
                                $error = "true";
                        } else {
                                # No error
                                my $status = &setFarmMaxClientTime($json_obj->{maxclients},$tracking,$farmname);
                                if ($status == -1){
                                        $error = "true";
                                } else {
                                        $restart_flag = "true";
                                }
                        }
                }

                # Modify only tracking param
                if (!exists($json_obj->{maxclients}) && exists($json_obj->{tracking})) {
                        if ($json_obj->{tracking} =~ /^$/) {
                                $error = "true";
                        } elsif (!$json_obj->{tracking} =~ /^\d+$/) {
                                $error = "true";
                        } else {
                                # No error
                                my $status = &setFarmMaxClientTime($maxclients,$json_obj->{tracking},$farmname);
                                if ($status == -1){
                                        $error = "true";
                                } else {
                                        $restart_flag = "true";
                                }
                        }
                }

		# Modify Max number of simultaneous connections that manage in Virtual IP
		if (exists($json_obj->{connmax})) {
                        if ($json_obj->{connmax} =~ /^$/) {
                                $error = "true";
                        } elsif (!$json_obj->{connmax} =~ /^\d+$/) {
                                $error = "true";
                        } elsif (!$json_obj->{connmax} > $maxsimconn) {
                                $error = "true";
                        } else {
                                my $status = &setFarmMaxConn($json_obj->{connmax},$farmname);
                                if ($status == -1){
                                        $error = "true";
                                } else {
                                        $restart_flag = "true";
                                }
                        }
                }

		# Modify Max number of real ip servers
                if (exists($json_obj->{maxservers})) {
                        if ($json_obj->{maxservers} =~ /^$/) {
                                $error = "true";
                        } elsif (!$json_obj->{maxservers} =~ /^\d+$/) {
                                $error = "true";
                        } elsif (!$json_obj->{maxservers} > $maxbackend) {
                                $error = "true";
                        } else {
                                my $status = &setFarmMaxServers($json_obj->{maxservers},$farmname);
                                if ($status == -1){
                                        $error = "true";
                                } else {
                                        $restart_flag = "true";
                                }
                        }
                }		
		
		# Get current vip & vport
		$vip = &getFarmVip("vip",$farmname);
		$vport = &getFarmVip("vipp",$farmname);
		
		# Modify both vip & vport
		if (exists($json_obj->{vip}) && exists($json_obj->{vport})) {
			if ($json_obj->{vip} =~ /^$/) {
				$error = "true";
			} elsif (!$json_obj->{vip} =~ /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/) {
				$error = "true";
			} else {
				if (exists($json_obj->{vport})) {
					if ($json_obj->{vport} =~ /^$/) {
						$error = "true";
					} elsif (!$json_obj->{vport} =~ /^\d+$/) {
						$error = "true";
					} else {
						
						# No error
						my $status = &setFarmVirtualConf($json_obj->{vip},$json_obj->{vport},$farmname);
						if ($status == -1){
							$error = "true";
						} else {
							$restart_flag = "true";
						}
					}
				}
			}
		}
		
		# Modify only vip
		if (exists($json_obj->{vip}) && !exists($json_obj->{vport})) {
			if ($json_obj->{vip} =~ /^$/) {
				$error = "true";
			} elsif (!$json_obj->{vip} =~ /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/) {
				$error = "true";
			} else {
				# No error
				my $status = &setFarmVirtualConf($json_obj->{vip},$vport,$farmname);
				if ($status == -1){
					$error = "true";
				} else {
					$restart_flag = "true";
				}
			}
		}
		
		# Modify only vport
		if (!exists($json_obj->{vip}) && exists($json_obj->{vport})) {
			if ($json_obj->{vport} =~ /^$/) {
				$error = "true";
			} elsif (!$json_obj->{vport} =~ /^\d+$/) {
				$error = "true";
			} else {
				# No error
				my $status = &setFarmVirtualConf($vip,$json_obj->{vport},$farmname);
				if ($status == -1){
					$error = "true";
				} else {
					$restart_flag = "true";
				}
			}
		}
		
		# Modify Farm's Name
        if(exists($json_obj->{newfarmname})){
                if($json_obj->{newfarmname} =~ /^$/){
                        $error = "true";
                } else {
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
		
		# Restart farm if needed
		if ($restart_flag eq "true") {
			&runFarmStop($farmname,"true");
			&runFarmStart($farmname,"true");
		}
	
		# Print params
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
		
	}
}

# PUT /farms/FarmTCP/farmguardian
#
# TCP/UDP/L4XNAT:
#
# curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin -d '{"fgtimecheck":"5","fgscript":"eyy","fgenabled":"true","fglog":"true"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/L4FARM/fg
#
# HTTP/HTTPS
#
# curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin -d '{"fgtimecheck":"5","fgscript":"eyy","fgenabled":"true","fglog":"false","service":"sev1"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/FarmHTTP/fg
#
#
#####Documentation of PUT FARMGUARDIAN####
#**
#  @api {put} /farms/<farmname>/fg Modify the parameters of the farm guardian in a Farm
#  @apiGroup Farm Guardian
#  @apiName PutFarmFG
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiDescription Modify the parameters of the farm guardian in a Farm with tcp, udp or l4xnat profile
#  @apiVersion 1.0.0
#
#
#
# @apiSuccess	{Number}		fgtimecheck	The farm guardian will check each 'timetocheck' seconds.
# @apiSuccess	{String}		fgscript	The command that farm guardian will check.
# @apiSuccess	{String}		fgenabled	Enabled the use of farm guardian. The options are: true and false.
# @apiSuccess	{String}		fglog		Enabled the use of logs in farm guardian. The options are: true and false.
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Modify farm L4FARM",
#   "params" : [
#      {
#         "fglog" : "true"
#      },
#      {
#         "fgenabled" : "true"
#      },
#      {
#         "fgscript" : "Command of Farm Guardian"
#      },
#      {
#         "fgtimecheck" : "5"
#      }
#   ]
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#       -u zapi:<password> -d '{"fgtimecheck":"5","fgscript":"Command of Farm Guardian",
#       "fgenabled":"true","fglog":"true"}' https://<zenlb_server>:444/zapi/v1/zapi.cgi/farms/L4FARM/fg
#
# @apiSampleRequest off
#
#**
#####Documentation of PUT FARMGUARDIAN SERVICE####
#**
#  @api {put} /farms/<farmname>/fg Modify the parameters of the farm guardian in a Service
#  @apiGroup Farm Guardian
#  @apiName PutFarmFGS
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiDescription Modify the parameters of the farm guardian in a Service http|https
#  @apiVersion 1.0.0
#
#
#
# @apiSuccess	{Number}		fgtimecheck	The farm guardian will check each 'timetocheck' seconds.
# @apiSuccess	{String}		fgscript		The command that farm guardian will check.
# @apiSuccess	{String}		fgenabled	Enabled the use of farm guardian.
# @apiSuccess	{String}		fglog		Enabled the use of logs in farm guardian.
# @apiSuccess	{String}		service		The Service's name which farm guardian will be modified.
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Modify farm FarmHTTP",
#   "params" : [
#      {
#         "fglog" : "true"
#      },
#      {
#         "fgenabled" : "true"
#      },
#      {
#         "fgscript" : "Command of Farm Guardian"
#      },
#      {
#         "fgtimecheck" : "5"
#      }
#      {
#         "service" : "service1"
#      }
#   ]
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#       -u zapi:<password> -d '{"fgtimecheck":"5","fgscript":"Command of Farm Guardian","fgenabled":"true",
#       "fglog":"true","service":"service1"}' https://<zenlb_server>:444/zapi/v1/zapi.cgi/farms/FarmHTTP/fg
#
# @apiSampleRequest off
#
#**



sub modify_farmguardian() {

	$farmname = @_[0];

	my $out_p = [];
	
	use CGI;
	use JSON;
	
	my $q = CGI->new;
	my $json = JSON->new;
	my $data = $q->param('PUTDATA');
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
				description => "Modify farm guardian",
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
				description => "Modify farm guardian",
				error => "true",
				message => $errormsg
		});
		print $output;
		exit;

	}
	
	
	my $type = &getFarmType($farmname);
	

	if(exists($json_obj->{service})){
		if($json_obj->{service} =~ /^$/){
			$error = "true";
		}	else {
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
				
			} else {
				$service = $json_obj->{service};
			}
			
		}
	}
	
	
	


	if ($type eq "tcp" || $type eq "udp" || $type eq "l4xnat"){
		@fgconfig = &getFarmGuardianConf($farmname,"");
	} elsif ($type eq "http" || $type eq "https"){
		@fgconfig = &getFarmGuardianConf($farmname,$service);
	}
	my $timetocheck = @fgconfig[1];
	$timetocheck = $timetocheck + 0;
	my $check_script = @fgconfig[2];
	$check_script =~ s/\n//g;
	$check_script =~ s/\"/\'/g;
	my $usefarmguardian = @fgconfig[3];
	$usefarmguardian =~ s/\n//g;
	my $farmguardianlog = @fgconfig[4];
	
	if(exists($json_obj->{fgtimecheck})){
		if($json_obj->{fgtimecheck} =~ /^$/){
			$error = "true";
		}
		$timetocheck = $json_obj->{fgtimecheck};
		$timetocheck = $timetocheck + 0;
	}

	if(exists($json_obj->{fgscript})){
		if($json_obj->{fgscript} =~/^$/){
			$error = "true";
		}
		$check_script = $json_obj->{fgscript};
	}

	if(exists($json_obj->{fgenabled})){
		if($json_obj->{fgenabled} =~ /^$/){
			$error = "true";
		}
		$usefarmguardian = $json_obj->{fgenabled};
	}

	if(exists($json_obj->{fglog})){
		if($json_obj{fglog}){
			$error = "true";
		}
		$farmguardianlog = $json_obj->{fglog};
	}

	if ($type eq "tcp" || $type eq "udp" || $type eq "l4xnat"){
		&runFarmGuardianStop($farmname,"");
		$status = &runFarmGuardianCreate($farmname,$timetocheck,$check_script,$usefarmguardian,$farmguardianlog,"");
		if ($status != -1){
			if ($usefarmguardian eq "true"){
				$status = &runFarmGuardianStart($farmname,"");
				if ($status == -1){
					$error = "true";
				}
			} else {
				$error = "true";
			}
		} else {
			$error = "true";
		}

	} elsif ($type eq "http" || $type eq "https"){
		&runFarmGuardianStop($farmname,$service);
		$status = &runFarmGuardianCreate($farmname,$timetocheck,$check_script,$usefarmguardian,$farmguardianlog,$service);
		
		if ($status != -1){
			if ($usefarmguardian eq "true"){
				$status = &runFarmGuardianStart($farmname,$service);
				if ($status == -1){
					$error = "true";
					print "ERROR, status=$status";
				}
			} else {
				$error = "true";
			}
		} else {
			$error = "true";
		}

	}

	# Print params
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
#  @apiVersion 1.0.0
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
#       "weight":"1"}' https://<zenlb_server>:444/zapi/v1/zapi.cgi/farms/FarmTCP/backends/1
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
#  @apiVersion 1.0.0
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
#       "weight":"1"}' https://<zenlb_server>:444/zapi/v1/zapi.cgi/farms/L4FARM/backends/1
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
#  @apiVersion 1.0.0
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
#       "weight":"1"}' https://<zenlb_server>:444/zapi/v1/zapi.cgi/farms/DATAFARM/backends/1
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
#  @apiVersion 1.0.0
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
#       "weight":"1"}' https://<zenlb_server>:444/zapi/v1/zapi.cgi/farms/FarmHTTP/backends/1
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
#  @apiVersion 1.0.0
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
#       https://<zenlb_server>:444/zapi/v1/zapi.cgi/farms/FarmGSLB/backends/1
#
# @apiSampleRequest off
#
#**



sub modify_backends(){

	my ($farmname, $id_server) = @_;
	my $out_p = [];
	
	use CGI;
	use JSON;
	
	my $q = CGI->new;
	my $json = JSON->new;
	my $data = $q->param('PUTDATA');
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
					description => "Modify backend",
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
				description => "Modify backend",
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
                $errormsg = "Invalid id server, please insert a valid value.";
                my $output = $j->encode({
                        description => "Modify backend",
                        error => "true",
                        message => $errormsg
                });
                print $output;
                exit;
        }

	$error = "false";
	my $type = &getFarmType($farmname);
	
	
	
	
	

	if ($type eq "l4xnat" || $type eq "datalink"){

		# Params
                my @run = &getFarmServers($farmname);
                $serv_values = @run[$id_server];
                my @l_serv = split (";",$serv_values);

                # Functions
                if (exists($json_obj->{ip})){
                        if ($json_obj->{ip} =~ /^$/){
                                $error = "true";
                        } elsif ($json_obj->{ip} =~ /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/){
                                @l_serv[1] = $json_obj->{ip};
                        } else {
                                $error = "true";
                        }
                }

                if(exists($json_obj->{port})){
                        if ($json_obj->{port} =~ /^$/){
                                $error = "true";
                        } elsif ($json_obj->{port} =~ /^\d+/){
                                @l_serv[2] = $json_obj->{port} + 0;
                        } else {
                                $error = "true";
                        }
                }

                if(exists($json_obj->{interface})){
                        if ($json_obj->{interface} =~ /^$/){
                                $error = "true";
                        } elsif ($json_obj->{interface} =~ /^eth\d+/){
                                @l_serv[2] = $json_obj->{interface};
                        } else {
                                $error = "true";
                        }
                }

		if ($type eq "l4xnat"){
                	if(exists($json_obj->{weight})){
                        	if ($json_obj->{weight} =~ /^$/){
                                	$error = "true";
                        	} elsif ($json_obj->{weight} =~ /^\d+$/){
                                	@l_serv[4] = $json_obj->{weight} + 0;
                        	} else {
                                	$error = "true";
                        	}
                	}

                	if(exists($json_obj->{priority})){
                        	if ($json_obj->{priority} =~ /^$/){
                                	$error = "true";
                        	} elsif ($json_obj->{priority} =~ /^\d+$/){
                                	@l_serv[5] = $json_obj->{priority} + 0;
                        	} else {
                                	$error = "true";
                        	}
                	}

			if ($error eq "false"){
                                $status = &setFarmServer($id_server,@l_serv[1],$l_serv[2],"",$l_serv[4],$l_serv[5],"",$farmname);
                                if ($status == -1){
                                        $error = "true";
                                }
                        }
		} elsif ($type eq "datalink"){
			if(exists($json_obj->{weight})){
                                if ($json_obj->{weight} =~ /^$/){
                                        $error = "true";
                                } elsif ($json_obj->{weight} =~ /^\d+$/){
                                        @l_serv[3] = $json_obj->{weight} + 0;
                                } else {
                                        $error = "true";
                                }
                        }

                        if(exists($json_obj->{priority})){
                                if ($json_obj->{priority} =~ /^$/){
                                        $error = "true";
                                } elsif ($json_obj->{priority} =~ /^\d+$/){
                                        @l_serv[4] = $json_obj->{priority} + 0;
                                } else {
                                        $error = "true";
                                }
                        }
			if ($error eq "false"){
                        	$status = &setFarmServer($id_server,@l_serv[1],$l_serv[2],"",$l_serv[3],$l_serv[4],"",$farmname);
                        	if ($status == -1){
                                	$error = "true";
                        	}
                	}
		}
	}


        if ($type eq "tcp" || $type eq "udp"){
		
		# Params
		my @run = &getFarmServers($farmname);
		$serv_values = @run[$id_server];

		my @l_serv = split ("\ ",$serv_values);

		# Functions	
		if (exists($json_obj->{ip})){
			if ($json_obj->{ip} =~ /^$/){
				$error = "true";
			} elsif ($json_obj->{ip} =~ /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/){
				@l_serv[2] = $json_obj->{ip};
			} else {
				$error = "true";
			}
		}

		if(exists($json_obj->{port})){
			if ($json_obj->{port} =~ /^$/){
                                $error = "true";
                        } elsif ($json_obj->{port} =~ /^\d+/){
                        	@l_serv[4] = $json_obj->{port} + 0;
			} else {
				$error = "true";
			}
		}

		if(exists($json_obj->{maxcon})){
                        if ($json_obj->{maxcon} =~ /^$/){
                                $error = "true";
                        } elsif ($json_obj->{maxcon} =~ /^\d+$/){
                        	@l_serv[8] = $json_obj->{maxcon} + 0;
			} else {
				$error = "true";
			}
                }

		if(exists($json_obj->{weight})){
                        if ($json_obj->{weight} =~ /^$/){
                                $error = "true";
                        } elsif ($json_obj->{weight} =~ /^\d+$/){
                        	@l_serv[12] = $json_obj->{weight} + 0;
			} else {
				$error = "true";
			}
                }

		if(exists($json_obj->{priority})){
                        if ($json_obj->{priority} =~ /^$/){
                                $error = "true";
                        } elsif ($json_obj->{priority} =~ /^\d+$/){
                        	@l_serv[14] = $json_obj->{priority} + 0;
			} else {
				$error = "true";
			}
                }

		if ($error eq "false"){
			$status = &setFarmServer($id_server,@l_serv[2],$l_serv[4],$l_serv[8],$l_serv[12],$l_serv[14],"",$farmname);
			if ($status == -1){
				$error = "true";
			}
		}
		
	}

	if ($type eq "http" || $type eq "https"){

		#Params
		if(exists($json_obj->{service})){
			if ($json_obj->{service} =~ /^$/){
				$error = "true";
			} else {
				$service = $json_obj->{service};
			}
		} else {
			$error = "true";
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
		
		my $backendsvs = &getFarmVS($farmname,$service,"backends");
		
		my @be = split("\n",$backendsvs);
		foreach $subline(@be){
                        @subbe = split("\ ",$subline);
			if (@subbe[1] == $id_server){
				last;
			}
		}

		# Functions
		if (exists($json_obj->{ip})){
                        if ($json_obj->{ip} =~ /^$/){
                                $error = "true";
                        } elsif ($json_obj->{ip} =~ /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/){
                                @subbe[3] = $json_obj->{ip};
                        } else {
                                $error = "true";
                        }
                }

                if(exists($json_obj->{port})){
                        if ($json_obj->{port} =~ /^$/){
                                $error = "true";
                        } elsif ($json_obj->{port} =~ /^\d+/){
                                @subbe[5] = $json_obj->{port} + 0;
                        } else {
                                $error = "true";
                        }
                }
		
		if(exists($json_obj->{weight})){
                        if ($json_obj->{weight} =~ /^$/){
                                $error = "true";
                        } elsif ($json_obj->{weight} =~ /^\d+$/){
                                @subbe[9] = $json_obj->{weight} + 0;
                        } else {
                                $error = "true";
                        }
                }

		if(exists($json_obj->{timeout})){
                        if ($json_obj->{timeout} =~ /^$/){
                                $error = "true";
                        } elsif ($json_obj->{timeout} =~ /^\d+$/){
                                @subbe[7] = $json_obj->{timeout} + 0;
                        } else {
                                $error = "true";
                        }
                }

		if ($error eq "false"){
                        $status = &setFarmServer($id_server,@subbe[3],$subbe[5],"","",$subbe[9],$subbe[7],$farmname,$service);
                        if ($status == -1){
                                $error = "true";
                        } else {
								&setFarmRestart($farmname);
						}
                }	
	}

	if ($type eq "gslb"){

		#Params
         if(exists($json_obj->{service})){
                 if ($json_obj->{service} =~ /^$/){
                         $error = "true";
                 } else {
                         $service = $json_obj->{service};
                 }
         } else {
                 $error = "true";
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

		my $backendsvs = &getFarmVS($farmname,$service,"backends");
		my @be = split("\n",$backendsvs);
		foreach $subline(@be){
			$subline =~ s/^\s+//;
			if ($subline =~ /^$/){
				next;
			}

			@subbe = split(" => ",$subline);
			if (@subbe[0] == $id_server){
				last;
			}
		}
		my $lb = &getFarmVS($farmname,$service,"algorithm");
		
		# Functions
		if (exists($json_obj->{ip})){
                        if ($json_obj->{ip} =~ /^$/){
                                $error = "true";
                        } elsif ($json_obj->{ip} =~ /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/){
                                @subbe[1] = $json_obj->{ip};
                        } else {
                                $error = "true";
                        }
                }

		if ($error eq "false"){
			$status = &setGSLBFarmNewBackend($farmname,$service,$lb,$id_server,@subbe[1]);
			if ($status == -1){
				$error = "true";		
			} else {
				&setFarmRestart($farmname);
			}
		}
	}

	# Print params
	if ($type eq "http" || $type eq "https" || $type eq "gslb"){
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
                                description => "Modify backend $id_server in farm $farmname",
                                params => $out_p,
				info => "There're changes that need to be applied, stop and start farm to apply them!"
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
	} else {

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
                                description => "Modify backend $id_server in farm $farmname",
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
#  @apiVersion 1.0.0
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
#       "zone":"zone1"}' https://<zenlb_server>:444/zapi/v1/zapi.cgi/farms/FarmGSLB/resources/3
#
# @apiSampleRequest off
#
#**


sub modify_resources(){

	my ($farmname, $id_resource) = @_;
    my $out_p = [];

    use CGI;
    use JSON;

    my $q = CGI->new;
    my $json = JSON->new;
    my $data = $q->param('PUTDATA');
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
                    description => "Modify resource",
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
				description => "Modify resource",
				error => "true",
				message => $errormsg
		});
		print $output;
		exit;

	}
	
	$error = "false";	

	#Params
        if(exists($json_obj->{zone})){
        	if ($json_obj->{zone} =~ /^$/){
                	$error = "true";
                } else {
                        $zone = $json_obj->{zone};
                }
        } else {
                # Error
                print $q->header(
                   -type=> 'text/plain',
                   -charset=> 'utf-8',
                   -status=> '400 Bad Request'
                );
                $errormsg = "The zone parameter is empty, please insert a zone.";
                my $output = $j->encode({
                        description => "Modify resource",
                        error => "true",
                        message => $errormsg
                });
                print $output;
                exit;
        }

        my $backendsvs = &getFarmVS($farmname,$zone,"resources");
        my @be = split("\n",$backendsvs);
        foreach $subline(@be){
                if ($subline =~ /^$/){
                        next;
                  }
		@subbe = split("\;",$subline);
                @subbe1 = split("\t",@subbe[0]);
                @subbe2 = split("\_",@subbe[1]);
                if (@subbe2[1] == $id_resource){
                        last;
                }
        }

	# Functions
	if(exists($json_obj->{rname})){
		if($json_obj->{rname} =~ /^$/){
			$error = "true";
		} else {
			@subbe1[0]  = $json_obj->{rname};
		}
	}		

	if(exists($json_obj->{ttl})){
		if($json_obj->{ttl} =~ /^$/){
			$error = "true";
		} elsif ($json_obj->{ttl} =~ /^\d+/){
			@subbe1[1] = $json_obj->{ttl};
		} else {
			$error = "true";
		}
	}	

	if(exists($json_obj->{type})){
		if($json_obj->{type} =~ /^$/){
			$error = "true";
		} elsif ($json_obj->{type} =~ /^NS|A|CNAME|DYNA$/){
			@subbe1[2] = $json_obj->{type};
		} else {
			$error = "true";
		}
	}

	if(exists($json_obj->{rdata})){
		if($json_obj->{rdata} =~ /^$/){
			$error = "true";
		} else {
			@subbe1[3] = $json_obj->{rdata};
		}			
	}

	if($error eq "false"){
		$status = &setFarmZoneResource($id_resource,@subbe1[0],@subbe1[1],@subbe1[2],@subbe1[3],$farmname,$zone);
		if ($status == -1){
			$error = "true";
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
                                description => "Modify resource $id_resource in farm $farmname",
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
#  @apiVersion 1.0.0
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
#       https://<zenlb_server>:444/zapi/v1/zapi.cgi/farms/FarmGSLB/zones/zone1
#
# @apiSampleRequest off
#
#**


sub modify_zones(){

    my ($farmname, $zone) = @_;
    my $out_p = [];

    use CGI;
    use JSON;

    my $q = CGI->new;
    my $json = JSON->new;
    my $data = $q->param('PUTDATA');
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
                    description => "Modify zone",
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
				description => "Modify zone",
				error => "true",
				message => $errormsg
		});
		print $output;
		exit;

	}
	
	# Check that the provided zone is configured in the farm
	my @zones = &getFarmZones( $farmname );
	
	my $found = 0;
	foreach $farmzone (@zones) {
		#print "zone: $farmzone";
		if ($zone eq $farmzone) {
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
		$errormsg = "Invalid zone name, please insert a valid value.";
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
	if ($json_obj->{defnamesv} =~ /^$/){
		$error = "true";
	}
	if ($error eq "false"){
		&setFarmVS($farmname,$zone,"ns",$json_obj->{defnamesv});
		if ($? eq 0){
                        &runFarmReload($farmname);
                } else {
			$error = "true";
                }
	}

	# Print params
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
                        description => "Modify zone $zone in farm $farmname",
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
                        description => "Modify zone $zone in farm $farmname",
                        error => "true",
                	message => $errormsg
                });
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
#  @apiVersion 1.0.0
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
#       https://<zenlb_server>:444/zapi/v1/zapi.cgi/farms/FarmGSLB/services/sev2
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
#  @apiVersion 1.0.0
#
#
#
# @apiSuccess   {String}        vhost			This field specifies the condition determined by the domain name through the same virtual IP and port defined by a HTTP farm.
# @apiSuccess	{String}	urlp			This field allows to determine a web service regarding the URL the client is requesting through a specific URL pattern which will be syntactically checked.
# @apiSuccess	{String}	redirect			This field behaves as a special backend, as the client request is answered by a redirect to a new URL automatically.
# @apiSuccess	{String}	persistence		This parameter defines how the HTTP service is going to manage the client session. The options are: nothing, IP, BASIC, URL, PARM, COOKIE and HEADER.
# @apiSuccess	{Number}	ttl			Only with persistence. This value indicates the max time of life for an inactive client session (max session age) in seconds.
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
#       "httpsb":"true"}' https://<zenlb_server>:444/zapi/v1/zapi.cgi/farms/FarmHTTP/services/sev2
#
# @apiSampleRequest off
#
#**


sub modify_services(){

    my ($farmname, $service) = @_;
    my $out_p = [];

    use CGI;
    use JSON;
	use URI::Escape;

    my $q = CGI->new;
    my $json = JSON->new;
    my $data = $q->param('PUTDATA');
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
                    description => "Modify service",
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
				description => "Modify service",
				error => "true",
				message => $errormsg
		});
		print $output;
		exit;

	}
	

    $error = "false";
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
	
	
	if ($type eq "http" || $type eq "https"){
		# Functions
		if(exists($json_obj->{vhost})){
			if($json_obj->{vhost} =~ /^$/){
				$error = "true";
			} else {
				&setFarmVS($farmname,$service,"vs",$json_obj->{vhost});
			}
		}

		if(exists($json_obj->{urlp})){
			if($json_obj->{urlp} =~ /^$/){
				$error = "true";
			} else {
				&setFarmVS($farmname,$service,"urlp",$json_obj->{urlp});
			}
		}

		if(exists($json_obj->{redirect})){
			my $redirect = uri_unescape($json_obj->{redirect});
			if($redirect =~ /^$/){
				$error = "true";
			} elsif ($redirect =~ /^http\:\/\//i || $redirect =~ /^https:\/\//i){
				&setFarmVS($farmname,$service,"redirect",$redirect);
			} else {
				$error = "true";
			}
		}

		if(exists($json_obj->{persistence})){
                        if($json_obj->{persistence} =~ /^$/){
                                $error = "true";
                        } elsif ($json_obj->{persistence} =~ /^nothing|IP|BASIC|URL|PARM|COOKIE|HEADER$/){
				$session = $json_obj->{persistence};
				$status = &setFarmVS($farmname,$service,"session","$session");
        			if ($status != 0){
       					$error = "true";	
				}
			}
		}

		if(exists($json_obj->{ttl})){
                	if($json_obj->{ttl} =~ /^$/){
                        	$error = "true";
                	} elsif ($json_obj->{ttl} =~ /^\d+/){
                        	$status = &setFarmVS($farmname,$service,"ttl","$json_obj->{ttl}");
				if($status != 0){
					$error = "true";
				}
                	} else {
                        	$error = "true";
                	}
        	}

		if(exists($json_obj->{sessionid})){
                        if($json_obj->{sessionid} =~ /^$/){
                                $error = "true";
                        } else {
                                &setFarmVS($farmname,$service,"sessionid",$json_obj->{sessionid});
                        }
                }

		if(exists($json_obj->{leastresp})){
			if($json_obj->{leastresp} =~ /^$/){
				$error = "true";
			} elsif ($json_obj->{leastresp} =~ /^true|false$/){
				if (($json_obj->{leastresp} eq "true")){
					&setFarmVS($farmname,$service,"dynscale",$json_obj->{leastresp});
				} elsif (($json_obj->{leastresp} eq "false")){
					&setFarmVS($farmname,$service,"dynscale","");
				}
			} else {
				$error = "true";
			}
		}

		if(exists($json_obj->{httpsb})){
                        if($json_obj->{httpsb} =~ /^$/){
				$error = "true";
                        } elsif ($json_obj->{httpsb} =~ /^true|false$/){
				if (($json_obj->{httpsb} eq "true")){
                                	&setFarmVS($farmname,$service,"httpsbackend",$json_obj->{httpsb});  
				} elsif (($json_obj->{httpsb} eq "false")){
					&setFarmVS($farmname,$service,"httpsbackend","");
				}                                      
			} else {
                                $error = "true";
                        }
                }
	}	

	if ($type eq "gslb"){
		# Functions
        	if ($json_obj->{deftcpport} =~ /^$/){
                	$error = "true";
        	}
        	if ($error eq "false"){
                	&setFarmVS($farmname,$service,"dpc",$json_obj->{deftcpport});
                	if ($? eq 0){
                        	&runFarmReload($farmname);
                	} else {
                        	$error = "true";
                	}
        	}
	}

	# Print params
	if ($error ne "true") {
			&setFarmRestart($farmname);
			
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
	                description => "Modify service $service in farm $farmname",
	                params => $out_p,
					info => "There're changes that need to be applied, stop and start farm to apply them!"
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
	                description => "Modify service $service in farm $farmname",
	                error => "true",
	                message => $errormsg
	        });
	        print $output;
	        exit;
	
	}

}



1
