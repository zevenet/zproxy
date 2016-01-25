#!/usr/bin/perl -w

######### PUT HTTP
#
# curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin -d '{"conectimeout":"22","newfarmname":"FarmHTTP2","vip":"178.62.126.152","vport":"88"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/FarmHTTP
#
#
#####Documentation of PUT HTTP####
#**
#  @api {put} /farms/<farmname> Modify a http|https Farm
#  @apiGroup Farm Modify
#  @apiName PutFarmHTTP
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiDescription Modify the params in a HTTP|HTTPS Farm
#  @apiVersion 1.0.0
#
#
#
# @apiSuccess	{Number}		contimeout	This value indicates how long the farm is going to wait for a connection to the backend in seconds.
# @apiSuccess	{Number}		restimeout	This value indicates how long the farm is going to wait for a response from the backends in seconds.
# @apiSuccess	{Number}		resurrectime	This value in seconds is the period to get out a blacklisted real server and checks if is alive.
# @apiSuccess	{Number}		reqtimeout	This value indicates how long the farm is going to wait for a client request in seconds.
# @apiSuccess	{Number}		maxthreads		This value indicates the number of working threads.
# @apiSuccess	{String}		rewritelocation	If enabled, the farm is forced to modify the Location: and Content-location: headers in responses to clients. The options are: enabled, disabled or enabled-backends.
# @apiSuccess	{String}		httpverb		This field indicates the operations that will be permitted to the HTTP client requests. The options are: standardHTTP, extendedHTTP, standardWebDAV, MSextWebDAV or MSRPCext.
# @apiSuccess	{String}		error414		Personalized message error 414.
# @apiSuccess	{String}		error500		Personalized message error 500.
# @apiSuccess	{String}		error501		Personalized message error 501.
# @apiSuccess	{String}		error503		Personalized message error 503.
# @apiSuccess	{String}		listener		A listener defines how the farm is going to play with the requests from the clients. The options are: http or https.
# @apiSuccess	{String}		ciphers 		Only in https. This field is used to build a list of ciphers accepted by SSL connections in order to harden the SSL connection. The options are: all or customsecurity.
# @apiSuccess	{String}		cipherc 		Only in https. This is the allowed customized list of ciphers that will be accepted by the SSL connection, which it’s a string in the same format as in OpenSSL ciphers.
# @apiSuccess	{String}		certname		This field is used to add a new service through the same virtual IP and port, which specify how the requests from the clients are managed and delivered.
# @apiSuccess	{String}		newfarmname	The new Farm's name.
# @apiSuccess	{Number}		vport			PORT of the farm, where is listening the virtual service.
# @apiSuccess	{String}		vip			IP of the farm, where is listening the virtual service.
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Modify farm FarmHTTP2",
#   "params" : [
#      {
#         "ciphers" : "customsecurity"
#      },
#      {
#         "error501" : "Message error 501"
#      },
#      {
#         "cipherc" : "TLSv1+SSLv3+HIGH:-MEDIUM:-LOW*:-ADH*"
#      },
#      {
#         "error414" : "Message error 414"
#      },
#      {
#         "certname" : "zencert.pem"
#      },
#      {
#         "restimeout" : "47"
#      },
#      {
#         "vip" : "178.62.126.152"
#      },
#      {
#         "reqtimeout" : "32"
#      },
#      {
#         "conectimeout" : "22"
#      },
#      {
#         "resurrectime" : "12"
#      },
#      {
#         "maxthreads" : "259"
#      },
#      {
#         "rewritelocation" : "enabled"
#      },
#      {
#         "vport" : "88"
#      },
#      {
#         "newfarmname" : "FarmHTTP2"
#      },
#      {
#         "error500" : "Message error 500"
#      },
#      {
#         "error503" : "Message error 503"
#      },
#      {
#         "listener" : "https"
#      },
#      {
#         "httpverb" : "standardHTTP"
#      }
#   ]
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#       -u zapi:<password> -d '{"conectimeout":"22","newfarmname":"FarmHTTP2","vip":"178.62.126.152","vport":"88",
#       "restimeout":"47","resurrectime":"12","reqtimeout":"32","rewritelocation":"enabled","httpverb":"standardHTTP",
#       "error414":"Message error 414","error500":"Message error 500","error501":"Message error 501",
#       "error503":"Message error 503","listener":"https","ciphers":"customsecurity","cipherc":"TLSv1+SSLv3+HIGH:-MEDIUM:-LOW*:-ADH*",
#       "maxthreads":"259","certname":"zencert.pem"}' https://<zenlb_server>:444/zapi/v1/zapi.cgi/farms/FarmHTTP
#
# @apiSampleRequest off
#
#**

our $origin;
if ($origin ne 1){
    exit;
}

######## Params

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
	$changedname = "false";
	
######## Functions

	# Modify Backend Connection Timeout
	if(exists($json_obj->{contimeout})){
		if($json_obj->{contimeout} =~ /^$/){
                        $error = "true";
                } elsif ($json_obj->{contimeout} =~ /^\d+$/) {
			my $status = &setFarmConnTO($json_obj->{contimeout},$farmname);
			if ($status != -1){
				$restart_flag= "true";
			} else {
				$error = "true";
			}
		} else {
			$error = "true";
		}
	}

        # Modify Backend Respone Timeout
        if(exists($json_obj->{restimeout})){
                if($json_obj->{restimeout} =~ /^$/){
                        $error = "true";
                } elsif ($json_obj->{restimeout} =~ /^\d+$/) {
                        $status = &setFarmTimeout($json_obj->{restimeout},$farmname);
                        if ($status != -1){
                                $restart_flag= "true";
                        } else {
                                $error = "true";
                        }
                } else {
                        $error = "true";
                }
        }

        # Modify Frequency To Check Resurrected Backends
        if(exists($json_obj->{resurrectime})){
                if($json_obj->{resurrectime} =~ /^$/){
                        $error = "true";
                } elsif ($json_obj->{resurrectime} =~ /^\d+$/) {
                        $status = &setFarmBlacklistTime($json_obj->{resurrectime},$farmname);
                        if ($status != -1){
                                $restart_flag= "true";
                        } else {
                                $error = "true";
                        }
                } else {
                        $error = "true";
                }
        }
	
	# Modify Client Request Timeout
        if(exists($json_obj->{reqtimeout})){
                if($json_obj->{reqtimeout} =~ /^$/){
                        $error = "true";
                } elsif ($json_obj->{reqtimeout} =~ /^\d+$/) {
                        $status = &setFarmClientTimeout($json_obj->{reqtimeout},$farmname);
                        if ($status != -1){
                                $restart_flag= "true";
                        } else {
                                $error = "true";
                        }
                } else {
                        $error = "true";
                }
        }

	# Modify Number Of Working Threads
        if(exists($json_obj->{maxthreads})){
                if($json_obj->{maxthreads} =~ /^$/){
                        $error = "true";
                } elsif ($json_obj->{maxthreads} =~ /^\d+$/) {
                        $status = &setFarmMaxConn($json_obj->{maxthreads},$farmname);
                        if ($status != -1){
                                $restart_flag= "true";
                        } else {
                                $error = "true";
                        }
                } else {
                        $error = "true";
                }
        }

	# Modify Rewrite Location Headers
        if(exists($json_obj->{rewritelocation})){
                if($json_obj->{rewritelocation} =~ /^$/){
                        $error = "true";
                } elsif ($json_obj->{rewritelocation} =~ /^disabled|enabled|enabled-backends$/) {
			if ($json_obj->{rewritelocation} eq "disabled"){
				$rewritelocation = 0;
			} elsif ($json_obj->{rewritelocation} eq "enabled"){
				$rewritelocation = 1;
			} elsif ($json_obj->{rewritelocation} eq "enabled-backends"){
				$rewritelocation = 2;
			}
                        $status1 = &setFarmRewriteL($farmname,$rewritelocation);
                        if ($status1 != -1){
                                $restart_flag= "true";
				#&runFarmRestart($farmname);
                        } else {
                                $error = "true";
                        }
                } else {
                        $error = "true";
                }
        }

	# Modify HTTP Verbs Accepted
	if(exists($json_obj->{httpverb})){
                if($json_obj->{httpverb} =~ /^$/){
                        $error = "true";
                } elsif ($json_obj->{httpverb} =~ /^standardHTTP|extendedHTTP|standardWebDAV|MSextWebDAV|MSRPCext$/) {
                        if ($json_obj->{httpverb} eq "standardHTTP"){
                                $httpverb = 0;
                        } elsif ($json_obj->{httpverb} eq "extendedHTTP"){
                                $httpverb = 1;
                        } elsif ($json_obj->{httpverb} eq "standardWebDAV"){
                                $httpverb = 2;
                        } elsif ($json_obj->{httpverb} eq "MSextWebDAV"){
				$httpverb = 3;
			} elsif ($json_obj->{httpverb} eq "MSRPCext"){
				$httpverb = 4;
			}
                        $status = &setFarmHttpVerb($httpverb,$farmname);
                        if ($status != -1){
                                $restart_flag= "true";
                                #&runFarmRestart($farmname);
                        } else {
                                $error = "true";
                        }
                } else {
                        $error = "true";
                }
        }

	#Modify Error 414
	if (exists($json_obj->{error414})){
		if($json_obj->{error414} =~ /^$/){
                        $error = "true";
                } else {
			$status = &setFarmErr($farmname,$json_obj->{error414},"414");
			if ($status != -1){
				$restart_flag = "true";
			} else {
				$error = "true";
			}
		}
	}

	#Modify Error 500
        if (exists($json_obj->{error500})){
                if($json_obj->{error500} =~ /^$/){
                        $error = "true";
                } else {
                        $status = &setFarmErr($farmname,$json_obj->{error500},"500");
                        if ($status != -1){
                                $restart_flag = "true";
                        } else {
                                $error = "true";
                        }
                }
        }

	#Modify Error 501
        if (exists($json_obj->{error501})){
                if($json_obj->{error501} =~ /^$/){
                        $error = "true";
                } else {
                        $status = &setFarmErr($farmname,$json_obj->{error501},"501");
                        if ($status != -1){
                                $restart_flag = "true";
                        } else {
                                $error = "true";
                        }
                }
        }

	#Modify Error 503
        if (exists($json_obj->{error503})){
                if($json_obj->{error503} =~ /^$/){
                        $error = "true";
                } else {
                        $status = &setFarmErr($farmname,$json_obj->{error503},"503");
                        if ($status != -1){
                                $restart_flag = "true";
                        } else {
                                $error = "true";
                        }
                }
        }

	# Modify Farm Listener
	if(exists($json_obj->{listener})){
		if($json_obj->{listener} =~ /^$/){
                        $error = "true";
                } elsif ($json_obj->{listener} =~ /^http|https$/){
			$status = &setFarmListen($farmname,$json_obj->{listener});
                        if ($status != -1){
                                $restart_flag= "true";
                        } else {
                                $error = "true";
                        }

		} else {
			$error = "true";
		}
	}
	
	
	# Modify HTTPS Params
	my $farmtype = &getFarmType( $farmname );
	if ( $farmtype eq "https" )
	{

		# Modify Ciphers
		if ( exists ( $json_obj->{ ciphers } ) )
		{
			if ( $json_obj->{ ciphers } =~ /^$/ )
			{
				$error = "true";
				&logfile(
					"ZAPI error, trying to modify a http farm $farmname, invalid ciphers, can't be blank."
				);
			}
			elsif ( $json_obj->{ ciphers } =~ /^all|customsecurity|highsecurity$/ )
			{
				if ( $json_obj->{ ciphers } eq "all" )
				{
					$ciphers = "cipherglobal";
					$flag    = "true";
				}
				elsif ( $json_obj->{ ciphers } eq "customsecurity" )
				{
					$ciphers = "ciphercustom";
				}
				elsif ( $json_obj->{ ciphers } eq "highsecurity" )
				{
					$ciphers = "cipherpci";
				}
				$status = &setFarmCipherList( $farmname, $ciphers );
				if ( $status != -1 )
				{
					$restart_flag = "true";
				}
				else
				{
					$error = "true";
					&logfile(
						"ZAPI error, trying to modify a http farm $farmname, some errors happened trying to modify the ciphers."
					);
				}
			}
			else
			{
				$error = "true";
				&logfile(
						  "ZAPI error, trying to modify a http farm $farmname, invalid ciphers." );
			}
		}

		# Get ciphers value
		my $cipher = &getFarmCipherSet( $farmname );
		chomp ( $cipher );

		if ( $flag eq "false" )
		{
			if ( $cipher eq "ciphercustom" )
			{
				# Modify Customized Ciphers
				if ( exists ( $json_obj->{ cipherc } ) )
				{
					if ( $json_obj->{ cipherc } =~ /^$/ )
					{
						$error = "true";
						&logfile(
							"ZAPI error, trying to modify a http farm $farmname, invalid cipherc, can't be blank."
						);
					}
					else
					{
						$cipherc = $json_obj->{ cipherc };
						$cipherc =~ s/\ //g;
						if ( $cipherc eq "" )
						{
							$error = "true";
						}
						else
						{
							$status = &setFarmCipherList( $farmname, $cipher, $cipherc );
							if ( $status != -1 )
							{
								$restart_flag = "true";
							}
							else
							{
								$error = "true";
								&logfile(
									"ZAPI error, trying to modify a http farm $farmname, some errors happened trying to modify the cipherc."
								);
							}
						}
					}
				}
			}
		}

		# Add Certificate to SNI list
		if ( exists ( $json_obj->{ certname } ) )
		{
			$status = &setFarmCertificateSNI( $json_obj->{ certname }, $farmname );
			if ( $status != -1 )
			{
				$restart_flag = "true";
			}
			else
			{
				$error = "true";
				&logfile(
					"ZAPI error, trying to modify a http farm $farmname, some errors happened trying to modify the certname."
				);
			}
		}
	}
	else
	{

		if (    exists ( $json_obj->{ ciphers } )
			 || exists ( $json_obj->{ cipherc } )
			 || exists ( $json_obj->{ certname } ) )
		{
			# Error
			print $q->header(
							  -type    => 'text/plain',
							  -charset => 'utf-8',
							  -status  => '400 Bad Request'
			);
			$errormsg = "To modify ciphers, chiperc or certname, listener must be https.";
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


        # Modify only vport
        if(exists($json_obj->{vport}) && !exists($json_obj->{vip})){
                if($json_obj->{vport} =~ /^$/){
                        $error = "true";
                }elsif(!$json_obj->{vport} =~ /^\d+$/){
                        $error = "true";
                }else{
                        $status = &setFarmVirtualConf($vip,$json_obj->{vport},$farmname);
                        if($status == -1){
                                $error = "true";
                        } else {
                                $restart_flag = "true";
                        }
                }
        }

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
                                        	$status = &setFarmVirtualConf($json_obj->{vip},$json_obj->{vport},$farmname);
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
        if(exists($json_obj->{newfarmname})){
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
					$oldfstat = &runFarmStop($farmname,"true");
                                        if ($oldfstat != 0){
                                                $error = "true";
                                        } else {
                                        	#Change farm name
                                        	my $fnchange = &setNewFarmName($farmname,$json_obj->{newfarmname});
						$changedname = "true";
                                        	if ($fnchange == -1){
                                                	&error = "true";
                                        	} elsif ($fnchange == -2){
                                                	$error= "true";
							$newfstat = &runFarmStart($farmname,"true");
							if ($newfstat != 0){
								$error = "true";
							}
                                        	} else {
							$farmname = $json_obj->{newfarmname};
							$newfstat = &runFarmStart($farmname,"true");
							if ($newfstat != 0){
                                                                $error = "true";
                                                        }
                                        	}
                                	}	
                        	}
                	} else {
						$error = "true";
					}
				}
        	}
	}

        # Check errors and print JSON
        if ($error ne "true") {

		if($changedname ne "true"){
			if($restart_flag eq "true"){
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
                                	description => "Modify farm $farmname",
                                	params => $out_p,
					info => "There're changes that need to be applied, stop and start farm to apply them!"
                        	});
                        	print $output;

			}
		} else {
			
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

		}

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

