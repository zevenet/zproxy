#!/usr/bin/perl -w

#
# curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin -d '{"ip":"1.2.1.2","interface":"eth0","weight":"2","priority":"3"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/farms/DATAFARM/backends
#
#
#
#####Documentation of POST BACKENDS DATALINK####
#**
#  @api {post} /farms/<farmname>/backends Create a new Backend in a datalink Farm
#  @apiGroup Farm Create
#  @apiName PostFarmBackendDATALINK
#  @apiParam {String} farmname  Farm name, unique ID.
#  @apiDescription Create a new Backend of a given DATALINK Farm
#  @apiVersion 1.0.0
#
#
#
# @apiSuccess	{String}	interface		It’s the local network interface where the backend is connected to.
# @apiSuccess   {String}        ip			IP of the backend, where is listening the real service.
# @apiSuccess   {Number}	priority			It’s the priority value for the current real server.
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
#       "priority":"3"}' https://<zenlb_server>:444/zapi/v1/zapi.cgi/farms/DATAFARM/backends
#
# @apiSampleRequest off
#**

our $origin;
if ($origin ne 1){
    exit;
}

######## Params

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

######## Check errors

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

        my $id = 0;
        my @run = &getFarmServers($farmname);
	if (@run > 0){
        	foreach $l_servers(@run){
                	my @l_serv = split(";",$l_servers);
                	if (@l_serv[1] ne "0.0.0.0"){
                        	if (@l_serv[0] > $id) {
                                	$id = @l_serv[0];
                        	}
                  	}
        	}
	
		if ($id >= 0) {
                	$id++;
        	}
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

        if ($json_obj->{ip} =~ /^$/){

                        # Error
                        print $q->header(
                           -type=> 'text/plain',
                           -charset=> 'utf-8',
                           -status=> '400 Bad Request'
                        );
                        $errormsg = "Invalid IP address for a real server, it can't be blank.";
                        my $output = $j->encode({
                                description => "New backend $id",
                                error => "true",
                                message => $errormsg
                        });
                        print $output;
                        exit;

                }

####### Create backend

        $status = &setFarmServer($id,$json_obj->{ip},$json_obj->{interface},"",$json_obj->{weight},$json_obj->{priority},"",$farmname);
                if ($status != -1){

                        # Success
                        print $q->header(
                           -type=> 'text/plain',
                           -charset=> 'utf-8',
                           -status=> '201 Created'
                        );
                        push $out_p, { id => $id, ip => $json_obj->{ip}, interface => $json_obj->{interface}, weight => $json_obj->{weight}+0, priority => $json_obj->{priority}+0 };

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


