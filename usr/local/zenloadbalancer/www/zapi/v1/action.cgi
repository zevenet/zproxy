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


# POST action
#
# curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin -d '{"action":"stop"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/FarmTCP/actions
#
#
#
#####Documentation of ACTIONS####
#**
#  @api {post} /farms/<farmname>/actions Set an action
#  @apiGroup Farm Actions
#  @apiName PostActions
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiDescription Set a given action in a Farm
#  @apiVersion 1.0.0
#
#
#
# @apiSuccess   {String}        action			Set the action desired. The actions are: stop, start and restart.
#
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Set a new action in FarmTCP",
#   "params" : [
#      {
#         "action" : "stop"
#      }
#   ]
#}
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#       -u zapi:<password> -d '{"action":"stop"}' https://<zenlb_server>:444/zapi/v1/zapi.cgi/farms/FarmTCP/actions
#
# @apiSampleRequest off
#
#**
our $origin;
if ( $origin ne 1 ){
    exit;
}


sub actions() {
		
	# Params
	$farmname = @_[0];
	
	use CGI;
        use JSON;
	my $out_p = [];

        my $q = CGI->new;
        my $json = JSON->new;
        my $data = $q->param('POSTDATA');
        my $json_obj = $json->decode($data);

	my $j = JSON::XS->new->utf8->pretty(1);
        $j->canonical($enabled);

	my $error = "false";
	my $action = "false";

	# Check input errors	
	if($json_obj->{action} =~ /^stop|start|restart$/){
		$action = $json_obj->{action};
	} else {
		print $q->header(
                    -type=> 'text/plain',
                    -charset=> 'utf-8',
                    -status=> '400 Bad Request'
                );
                $errormsg = "Invalid action; the possible actions are stop, start and restart";
                my $output = $j->encode({
                     description => "New farm $farmname",
                     error => "true",
                     message => $errormsg
                });
		print $output;
		exit;
	} 

	# Functions
	if ($action eq "stop"){
		my $status = &runFarmStop($farmname,"true");
		if ($status != 0){
			$error = "true";
		}
	}

	if ($action eq "start"){
		my $status = &runFarmStart($farmname,"true");
		if ($status != 0){
			$error = "true";
		}
	}	

	if ($action eq "restart"){
		my $status = &runFarmStop($farmname,"true");
                if ($status != 0){
                        $error = "true";
                }
		my $status1 = &runFarmStart($farmname,"true");
		if ($status == 0){
			my $type = &getFarmType($farmname);
			if ($type eq "http" || $type eq "http" ){
				&setFarmHttpBackendStatus($farmname);
			}
		&setFarmNoRestart($farmname);
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

                push $out_p, { action  => $json_obj->{action} };

                my $output = $j->encode({
                     description => "Set a new action in $farmname",
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
                $errormsg = "Errors found trying to execute the action $json_obj->{action} in farm $farmname";
                my $output = $j->encode({
                     description => "Set a new action in $farmname",
                     error => "true",
                     message => $errormsg
                });
                print $output;
        	exit;

	}		

}

1

