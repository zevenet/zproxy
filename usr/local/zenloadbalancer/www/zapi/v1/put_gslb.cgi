#!/usr/bin/perl -w

######### PUT GSLB
#
# curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin -d '{"newfarmname":"newFarmGSLB","vip":"178.62.126.152","port":"53"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/FarmGSLB
#
#
#####Documentation of PUT GSLB####
#**
#  @api {put} /farms/<farmname> Modify a gslb Farm
#  @apiGroup Farm Modify
#  @apiName PutFarmGSLB
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiDescription Modify the params in a GSLB Farm
#  @apiVersion 1.0.0
#
#
#
# @apiSuccess	{String}		newfarmname	The new Farm's name.
# @apiSuccess	{Number}		port			PORT of the farm, where is listening the virtual service.
# @apiSuccess	{String}		vip			IP of the farm, where is listening the virtual service.
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Modify farm newFarmGSLB",
#   "params" : [
#      {
#         "vip" : "178.62.126.152"
#      },
#      {
#         "port" : "53"
#      },
#      {
#         "newfarmname" : "newFarmGSLB"
#      }
#   ]
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#       -u zapi:<password> -d '{"vip":"178.62.126.152","port":"53",
#       "newfarmname":"newFarmGSLB"}' https://<zenlb_server>:444/zapi/v1/zapi.cgi/farms/newFarmGSLB
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

######## Functions

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
     #if(exists($json_obj->{newfarmname})){
     #        if($json_obj->{newfarmname} =~ /^$/){
     #                $error = "true";
     #        } else {
     #                #Check if farmname has correct characters (letters, numbers and hyphens)
     #                if($json_obj->{newfarmname} =~ /^[a-zA-Z0-9\-]*$/){
     #                        #Check if the new farm's name alredy exists
     #                        my $newffile = &getFarmFile($json_obj->{newfarmname});
     #                        if ($newffile != -1){
     #                                $error = "true";
     #                        } else {
     #                                #Change farm name
     #                                my $fnchange = &setNewFarmName($farmname,$json_obj->{newfarmname});
     #                                if ($fnchange == -1){
     #                                        &error = "true";
     #                                } else {
     #                                        $restart_flag = "true";
	 #										  $farmname = $json_obj->{newfarmname};
     #                                }
     #                        }
     #                } else {
     #                        $error = "true";
     #                }
     #        }
     #}

      # Restart Farm
      #if($restart_flag eq "true"){
      #        &runFarmStop($farmname,"true");
      #        &runFarmStart($farmname,"true");
      #}

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
    #if ($error ne "true") {
    #
    #        if($changedname ne "true"){
    #                if($restart_flag eq "true"){
    #                        &setFarmRestart($farmname);
    #
    #                        # Success
    #                        print $q->header(
    #                           -type=> 'text/plain',
    #                           -charset=> 'utf-8',
    #                           -status=> '200 OK'
    #                        );
    #
    #                        foreach $key (keys %$json_obj) {
    #                                push $out_p, { $key =>$json_obj->{$key}}
    #                        }
    #
    #                        my $j = JSON::XS->new->utf8->pretty(1);
    #                        $j->canonical($enabled);
    #                        my $output = $j->encode({
    #                                description => "Modify farm $farmname",
    #                                params => $out_p,
    #                                info => "There're changes that need to be applied, stop and start farm to apply them!"
    #                        });
    #                        print $output;
    #
    #                }
    #        } else {
    #
    #                # Success
    #                        print $q->header(
    #                           -type=> 'text/plain',
    #                           -charset=> 'utf-8',
    #                           -status=> '200 OK'
    #                        );
    #
    #                        foreach $key (keys %$json_obj) {
    #                                push $out_p, { $key =>$json_obj->{$key}}
    #                        }
    #
    #                        my $j = JSON::XS->new->utf8->pretty(1);
    #                        $j->canonical($enabled);
    #                        my $output = $j->encode({
    #                                description => "Modify farm $farmname",
    #                                params => $out_p
    #                        });
    #                        print $output;
    #
    #        }
    #
    #} else {
    #
    #        # Error
    #        print $q->header(
    #           -type=> 'text/plain',
    #           -charset=> 'utf-8',
    #           -status=> '400 Bad Request'
    #        );
    #        $errormsg = "Errors found trying to modify farm $farmname";
    #        my $output = $j->encode({
    #                description => "Modify farm $farmname",
    #                error => "true",
    #                message => $errormsg
    #        });
    #        print $output;
    #        exit;
    #}



        # Check errors and print JSON
        if ($error ne "true") {
				if($changedname ne "true"){
						&setFarmRestart($farmname);
				
                        # Success
                        print $q->header(
                           -type=> 'text/plain',
                           -charset=> 'utf-8',
                           -status=> '200 OK'
                        );

                        foreach $key (keys %$json_obj) {
                                push $out_p, { $key =>$json_obj->{$key}};
								#print "out: $out_p[1]\n";
								#$line = $out_p;
								#$out_p = "$line, $key => $json_obj->{$key}";
                        }

                        my $j = JSON::XS->new->utf8->pretty(1);
                        $j->canonical($enabled);
                        my $output = $j->encode({
                                description => "Modify farm $farmname",
                                params => $out_p,
								info => "There're changes that need to be applied, stop and start farm to apply them!"
                        });
                        print $output;
						
				} else {
				
						# Success
                        print $q->header(
                           -type=> 'text/plain',
                           -charset=> 'utf-8',
                           -status=> '200 OK'
                        );

                        foreach $key (keys %$json_obj) {
                                push $out_p, { $key =>$json_obj->{$key}};
								#print "out: $out_p[1]\n";
								#$line = $out_p;
								#$out_p = "$line, $key => $json_obj->{$key}";
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

