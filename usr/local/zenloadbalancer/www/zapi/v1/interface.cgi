#!/usr/bin/perl -w

# POST Virtual Network Interface
#
# curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin -d '{"name":"new2","ip":"1.1.1.3","netmask":"255.255.192.0"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/addvini/eth0
#
#####Documentation of POST VINI####
#**
#  @api {post} /addvini/<interface> Create a new virtual network interface
#  @apiGroup Interfaces
#  @apiName PostVini
#  @apiParam {String} interface  Interface name, unique ID.
#  @apiDescription Create a new virtual network interface of a given interface
#  @apiVersion 1.0.0
#
#
#
# @apiSuccess   {String}        name                     The name of the virtual network interface.
# @apiSuccess	{String}	ip			IP of the virtual network interface.
#
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "New virtual network interface eth0:new2",
#   "params" : [
#      {
#         "HWaddr" : "04:01:41:01:86:01",
#         "gateway" : null,
#         "ip" : "192.168.0.150",
#         "name" : "eth0:new",
#         "netmask" : "255.255.192.0"
#      }
#   ]
#}
#
# @apiExample {curl} Example Usage:
#	curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#	-u zapi:<password> -d '{"name":"new","ip":"192.168.0.150"}'
#	https://<zenlb_server>:444/zapi/v1/zapi.cgi/addvini/eth0
#
# @apiSampleRequest off
#
#**

our $origin;
if ($origin ne 1){
    exit;
}

sub new_vini() {

        my $fdev = @_[0];
		my $if = $fdev;

        my $out_p = [];

        use CGI;
        use JSON;

        my $q = CGI->new;
        my $json = JSON->new;
        my $data = $q->param('POSTDATA');
        my $json_obj = $json->decode($data);

        $error = "false";

        my $j = JSON::XS->new->utf8->pretty(1);
        $j->canonical($enabled);

	# Check interface errors
	if ($fdev =~ /^$/){
                # Error
		$error = "true";
                print $q->header(
                   -type=> 'text/plain',
                   -charset=> 'utf-8',
                   -status=> '400 Bad Request'
                );
                $errormsg = "Interface name can't be empty";
                my $output = $j->encode({
                        description => "Interface $fdev",
                        error => "true",
                        message => $errormsg
                });
                print $output;
                exit;
        }

	if ($fdev =~ /\s+/ ){
		# Error
		$error = "true";
                print $q->header(
                   -type=> 'text/plain',
                   -charset=> 'utf-8',
                   -status=> '400 Bad Request'
                );
                $errormsg = "Interface name is not valid";
                my $output = $j->encode({
                        description => "Interface $fdev",
                        error => "true",
                        message => $errormsg
                });
                print $output;
                exit;
	}
	
	# Check network interface errors
	my $ifn = "$fdev\:$json_obj->{name}";

	my $exists = &ifexist($ifn);
	if ($exists eq "true"){
		# Error
		$error = "true";
                print $q->header(
                   -type=> 'text/plain',
                   -charset=> 'utf-8',
                   -status=> '400 Bad Request'
                );
                $errormsg = "Network interface $ifn already exists.";
                my $output = $j->encode({
                        description => "Network interface $ifn",
                        error => "true",
                        message => $errormsg
                });
                print $output;
                exit;	
	}
	
	# Check address errors
	if (&ipisok($json_obj->{ip}) eq "false"){
		# Error
		$error = "true";
                print $q->header(
                   -type=> 'text/plain',
                   -charset=> 'utf-8',
                   -status=> '400 Bad Request'
                );
                $errormsg = "IP Address $json_obj->{ip} structure is not ok.";
                my $output = $j->encode({
                        description => "IP Address $json_obj->{ip}",
                        error => "true",
                        message => $errormsg
                });
                print $output;
                exit;
	}
	
	# Check new IP address is not in use
	my @activeips = &listallips();
	for my $ip ( @activeips )
	{
		if ( $ip eq $json_obj->{ ip } )
		{
			# Error
			$error = "true";
			print $q->header(
							  -type    => 'text/plain',
							  -charset => 'utf-8',
							  -status  => '400 Bad Request'
			);
			$errormsg = "IP Address $json_obj->{ip} is already in use.";
			my $output = $j->encode(
									 {
									   description => "IP Address $json_obj->{ip}",
									   error       => "true",
									   message     => $errormsg
									 }
			);
			print $output;
			exit;		
		}
	}
	
	# Check netmask errors
	if ( $json_obj->{netmask} !~ /^$/ && &ipisok($json_obj->{netmask}) eq "false") {
		# Error
		$error = "true";
                print $q->header(
                   -type=> 'text/plain',
                   -charset=> 'utf-8',
                   -status=> '400 Bad Request'
                );
                $errormsg = "Netmask Address $json_obj->{netmask} structure is not ok.";
                my $output = $j->encode({
                        description => "Netmask Address $json_obj->{netmask}",
                        error => "true",
                        message => $errormsg
                });
                print $output;
                exit;
	}	

	# Check gateway errors
	if ( $json_obj->{gateway} !~ /^$/ && &ipisok($json_obj->{gateway}) eq "false") {
		# Error
		$error = "true";
                print $q->header(
                   -type=> 'text/plain',
                   -charset=> 'utf-8',
                   -status=> '400 Bad Request'
                );
                $errormsg = "Gateway Address $json_obj->{gateway} structure is not ok.";
                my $output = $j->encode({
                        description => "Gateway Address $json_obj->{gateway}",
                        error => "true",
                        message => $errormsg
                });
                print $output;
                exit;
	}

	# get params of fdev
        my $s = IO::Socket::INET->new(Proto => 'udp');
        my @interfaces = $s->if_list;
        my @interfacesdw;
        my $fla = "false";
	my $i = 0;
        for my $if (@interfaces) {
                if ( $if !~ /^lo|sit0/ && $fla eq "false" ){
                        my $flags = $s->if_flags($if);
                        $hwaddr = $s->if_hwaddr($if);
                        $status = "";
                        $ip = "";
                        $netmask = "";
                        $gw = "";
                        $link = "on";
                        if (($flags & IFF_UP) && ($fla eq "false")) {
                                $status="up";
                                $ip = $s->if_addr($if);
                                $netmask = $s->if_netmask($if);
                                $bc = $s->if_broadcast($if);
                                $gw = &getDefaultGW($if);
				$myname = @interfaces[0+$i];
				$i = $i + 1;
				if ($myname eq $fdev){
					$fla = "true";
					$netmaskvi = $netmask;	
				}
                        }
			# List configured interfaces with down state
                        opendir(DIR, "$configdir");
                        @files = grep(/^if\_$if.*\_conf$/,readdir(DIR));
                        closedir(DIR);
                        foreach $file (@files) {
                        my @filename = split('_',$file);
                        $iff = @filename[1];
                        if (! (grep $_ eq $iff, @interfaces) && ! (grep $_ eq $iff, @interfacesdw)) {
                                open FI, "$configdir/$file";
                                while ($line=<FI>) {
                                        my @s_line = split(':',$line);
                                        my $ifd = @s_line[0];
                                        my $ifnamef = @s_line[1];
                                        my $named = "$ifd\:$ifnamef";
                                        my $toipv = @s_line[2];
                                        my $netmask = @s_line[3];
                                        my $status = "down";
                                        my $gw =  @s_line[5];
                                        close FI;
					if ($named eq $fdev){
						$netmaskvi = $netmask;
					}
				}
                        # No show this interface again
                        push(@interfacesdw,$iff);
                        }
			}

		}
	}


	# No errors
	if ( $error eq "false" ){
			$exists = &ifexist($ifn);
                        if ($exists eq "false"){
                                &createIf($ifn);
                        }
                        &delRoutes("local",$ifn);
                        &logfile("running '$ifconfig_bin $ifn $json_obj->{ip} netmask $netmaskvi' ");
                        @eject = `$ifconfig_bin $ifn $json_obj->{ip} netmask $netmaskvi 2> /dev/null`;
                        &upIf($ifn);
                        $state = $?;
                        if ($state == 0){
                                $status = "up";
                                #print "Network interface $if is now UP\n";
                        } else {
				$error = "true";
			}
                        if ( $ifn =~ /\:/ ) {
                                &writeConfigIf($ifn,"$ifn\:$json_obj->{ip}\:$netmaskvi\:$status\:\:");
                        } else {
                                &writeRoutes($ifn);
                                &writeConfigIf($ifn,"$ifn\:\:$json_obj->{ip}\:$netmaskvi\:$status\:$gw\:");
                        }
                        &applyRoutes("local",$ifn,$gw);
                        #print "All is ok, saved $if interface config file\n";
	
	}

	if ($error eq "false"){
		# Success
        	print $q->header(
           	   -type=> 'text/plain',
           	   -charset=> 'utf-8',
           	   -status=> '201 Created'
        	);
		push $out_p, { name => $ifn, ip => $json_obj->{ip}, netmask => $netmaskvi, gateway => $gw, HWaddr => $hwaddr };
		my $j = JSON::XS->new->utf8->pretty(1);
		$j->canonical($enabled);
		my $output = $j->encode({
			description => "New virtual network interface $ifn",
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
		$errormsg = "The $ifn virtual network interface can't be created";
                my $output = $j->encode({
                        description => "New virtual network interface $ifn",
                        error => "true",
                        message => $errormsg
                });
                print $output;
                exit;
	}

}

# POST Vlan Network Interface
#
# curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin -d '{"name":"3","ip":"1.1.1.3","netmask":"255.255.192.0"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/addvlan/eth0
#
#####Documentation of POST VLAN####
#**
#  @api {post} /addvlan/<interface> Create a new vlan network interface
#  @apiGroup Interfaces
#  @apiName PostVlan
#  @apiParam {String} interface  Interface name, unique ID.
#  @apiDescription Create a new vlan network interface of a given interface
#  @apiVersion 1.0.0
#
#
#
# @apiSuccess   {String}        name                     The name of the vlan network interface.
# @apiSuccess   {String}        ip                       IP of the vlan network interface.
# @apiSuccess   {String}        netmask                  Netmask of the vlan network interface.
# @apiSuccess   {String}        gateway                  Gateway of the vlan network interface.
#
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "New vlan network interface eth0.3",
#   "params" : [
#      {
#         "HWaddr" : "04:01:41:01:86:01",
#         "gateway" : "192.168.1.0",
#         "ip" : "192.168.1.150",
#         "name" : "eth0.3",
#         "netmask" : "255.255.255.0"
#      }
#   ]
#}
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#       -u zapi:<password> -d '{"name":"new","ip":"192.168.1.150","netmask":"255.255.255.0",
#       "gateway":"192.168.1.0"}' https://<zenlb_server>:444/zapi/v1/zapi.cgi/addvlan/eth0
#
# @apiSampleRequest off
#
#**


sub new_vlan() {

        my $fdev = @_[0];

	my $out_p = [];

        use CGI;
        use JSON;

        my $q = CGI->new;
        my $json = JSON->new;
        my $data = $q->param('POSTDATA');
        my $json_obj = $json->decode($data);

        $error = "false";

        my $j = JSON::XS->new->utf8->pretty(1);
        $j->canonical($enabled);

        # Check interface errors
        if ($fdev =~ /^$/){
                # Error
                $error = "true";
                print $q->header(
                   -type=> 'text/plain',
                   -charset=> 'utf-8',
                   -status=> '400 Bad Request'
                );
                $errormsg = "Interface name can't be empty";
                my $output = $j->encode({
                        description => "Interface $fdev",
                        error => "true",
                        message => $errormsg
                });
                print $output;
                exit;
        }
	
	if ($fdev =~ /\s+/ ){
                # Error
                $error = "true";
                print $q->header(
                   -type=> 'text/plain',
                   -charset=> 'utf-8',
                   -status=> '400 Bad Request'
                );
                $errormsg = "Interface name is not valid";
                my $output = $j->encode({
                        description => "Interface $fdev",
                        error => "true",
                        message => $errormsg
                });
                print $output;
                exit;
        }
	
	# Check name errors
	if ($json_obj->{name} !~ /^\d+$/) {
		# Error
                $error = "true";
                print $q->header(
                   -type=> 'text/plain',
                   -charset=> 'utf-8',
                   -status=> '400 Bad Request'
                );
                $errormsg = "The name for Vlan must be a number.";
                my $output = $j->encode({
                        description => "Name $json_obj->{name} of Vlan",
                        error => "true",
                        message => $errormsg
                });
                print $output;
                exit;
	}

    # Check network interface errors
    my $ifn = "$fdev\.$json_obj->{name}";

    my $exists = &ifexist($ifn);
    if ($exists eq "true"){
            # Error
            $error = "true";
            print $q->header(
               -type=> 'text/plain',
               -charset=> 'utf-8',
               -status=> '400 Bad Request'
            );
            $errormsg = "Vlan network interface $ifn already exists.";
            my $output = $j->encode({
                    description => "Vlan network interface $ifn",
                    error => "true",
                    message => $errormsg
            });
            print $output;
            exit;
    }

    # Check address errors
    if (&ipisok($json_obj->{ip}) eq "false"){
            # Error
            $error = "true";
            print $q->header(
               -type=> 'text/plain',
               -charset=> 'utf-8',
               -status=> '400 Bad Request'
            );
            $errormsg = "IP Address $json_obj->{ip} structure is not ok.";
            my $output = $j->encode({
                    description => "IP Address $json_obj->{ip}",
                    error => "true",
                    message => $errormsg
            });
            print $output;
            exit;
    }
	
	# Check new IP address is not in use
	my @activeips = &listallips();
	for my $ip ( @activeips )
	{
		if ( $ip eq $json_obj->{ ip } )
		{
			# Error
			$error = "true";
			print $q->header(
							  -type    => 'text/plain',
							  -charset => 'utf-8',
							  -status  => '400 Bad Request'
			);
			$errormsg = "IP Address $json_obj->{ip} is already in use.";
			my $output = $j->encode(
									 {
									   description => "IP Address $json_obj->{ip}",
									   error       => "true",
									   message     => $errormsg
									 }
			);
			print $output;
			exit;		
		}
	}

	# Check netmask errors
        if ( $json_obj->{netmask} !~ /^$/ && &ipisok($json_obj->{netmask}) eq "false") {
                # Error
                $error = "true";
                print $q->header(
                   -type=> 'text/plain',
                   -charset=> 'utf-8',
                   -status=> '400 Bad Request'
                );
                $errormsg = "Netmask Address $json_obj->{netmask} structure is not ok.";
                my $output = $j->encode({
                        description => "Netmask Address $json_obj->{netmask}",
                        error => "true",
                        message => $errormsg
                });
                print $output;
                exit;
        }

        # Check gateway errors
        if ( $json_obj->{gateway} !~ /^$/ && &ipisok($json_obj->{gateway}) eq "false") {
                # Error
                $error = "true";
                print $q->header(
                   -type=> 'text/plain',
                   -charset=> 'utf-8',
                   -status=> '400 Bad Request'
                );
                $errormsg = "Gateway Address $json_obj->{gateway} structure is not ok.";
                my $output = $j->encode({
                        description => "Gateway Address $json_obj->{gateway}",
                        error => "true",
                        message => $errormsg
                });
                print $output;
                exit;
        }
	
	# get params of fdev
        my $s = IO::Socket::INET->new(Proto => 'udp');
        my @interfaces = $s->if_list;
        my @interfacesdw;
        my $fla = "false";
        my $i = 0;
        for my $if (@interfaces) {
                if ( $if !~ /^lo|sit0/ && $fla eq "false"){
                        my $flags = $s->if_flags($if);
                        $hwaddr = $s->if_hwaddr($if);
                        $status = "";
                        $ip = "";
                        $netmask = "";
                        $gw = "";
                        $link = "on";
                        if (($flags & IFF_UP) && ($fla eq "false")) {
                                $status="up";
                                $ip = $s->if_addr($if);
                                $netmask = $s->if_netmask($if);
                                $bc = $s->if_broadcast($if);
                                $gw = &getDefaultGW($if);
                                $myname = @interfaces[0+$i];
                                $i = $i + 1;
                                if ($myname eq $fdev){
                                        $fla = "true";
                                }
                        }
		}
	}
	
	# No errors
        if ( $error eq "false" ){
                        $exists = &ifexist($ifn);
                        if ($exists eq "false"){
                                &createIf($ifn);
                        }
                        &delRoutes("local",$ifn);
                        &logfile("running '$ifconfig_bin $ifn $json_obj->{ip} netmask $json_obj->{netmask}' ");
                        @eject = `$ifconfig_bin $ifn $json_obj->{ip} netmask $json_obj->{netmask} 2> /dev/null`;
                        &upIf($ifn);
                        $state = $?;
                        if ($state == 0){
                                $status = "up";
                                #print "Network interface $if is now UP\n";
                        } else {
                                $error = "true";
                        }
                        if ( $if =~ /\:/ ) {
                                &writeConfigIf($ifn,"$ifn\:$json_obj->{ip}\:$json_obj->{netmask}\:$status\:\:");
                        } else {
                                &writeRoutes($ifn);
                                &writeConfigIf($ifn,"$ifn\:\:$json_obj->{ip}\:$json_obj->{netmask}\:$status\:$json_obj->{gateway}\:");
                        }
                        &applyRoutes("local",$ifn,$json_obj->{gateway});
                        #print "All is ok, saved $if interface config file\n";

        }

        if ($error eq "false"){
                # Success
                print $q->header(
                   -type=> 'text/plain',
                   -charset=> 'utf-8',
                   -status=> '201 Created'
                );
                push $out_p, { name => $ifn, ip => $json_obj->{ip}, netmask => $json_obj->{netmask}, gateway => $json_obj->{gateway}, HWaddr => $hwaddr };
                my $j = JSON::XS->new->utf8->pretty(1);
                $j->canonical($enabled);
                my $output = $j->encode({
                        description => "New vlan network interface $ifn",
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
                $errormsg = "The $ifn vlan network interface can't be created";
                my $output = $j->encode({
                        description => "New vlan network interface $ifn",
                        error => "true",
                        message => $errormsg
                });
                print $output;
                exit;
        }
		
}

# DELETE Virtual Network Interface
#
# curl --tlsv1 -k -X DELETE -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin https://178.62.126.152:445/zapi/v1/zapi.cgi/deleteif/eth0:new 
#
#
#####Documentation of DELETE INTERFACE####
#**
#  @api {delete} /deleteif/<interface> Delete a interface
#  @apiGroup Interfaces
#  @apiName DeleteIf
#  @apiParam {String} interface  Interface name, unique ID.
#  @apiDescription Delete a interface, a virtual network interface or a vlan
#  @apiVersion 1.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Delete interface eth0:new",
#   "message" : "The interface eth0:new has been deleted.",
#   "success" : "true"
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X DELETE -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#       -u zapi:<password> https://<zenlb_server>:444/zapi/v1/zapi.cgi/deleteif/eth0:new
#
# @apiSampleRequest off
#
#**


sub delete_interface() {
	
	my $if = @_[0];

        use CGI;

        my $q = CGI->new;

        $error = "false";

        my $j = JSON::XS->new->utf8->pretty(1);
        $j->canonical($enabled);

	# Check input errors and delete vini
	if ( $if !~ /^$/) {
                &delRoutes("local",$if);
                &downIf($if);
                &delIf($if);
                
		# Success
		print $q->header(
                   -type=> 'text/plain',
                   -charset=> 'utf-8',
                   -status=> '200 OK'
                );

                my $j = JSON::XS->new->utf8->pretty(1);
                $j->canonical($enabled);

                $message = "The interface $if has been deleted.";
                my $output = $j->encode({
                        description => "Delete interface $if",
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
                $errormsg = "The $if interface can't be deleted";
                my $output = $j->encode({
                        description => "Delete interface $if",
                        error => "true",
                        message => $errormsg
                });
                print $output;
                exit;
        }
	
	
}

# GET Interface
#
# curl --tlsv1 -k -X GET -H 'Content- Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin https://178.62.126.152:445/zapi/v1/zapi.cgi/interfaces
#
#####Documentation of GET INTERFACES####
#**
#  @api {get} /interfaces Get params of the interfaces
#  @apiGroup Interfaces
#  @apiName GetInterfaces
#  @apiDescription Gat all the params of the interfaces
#  @apiVersion 1.0.0
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "List interfaces",
#   "interfaces" : [
#      {
#         "HWaddr" : "04:01:41:01:86:01",
#         "gateway" : "",
#         "ip" : "178.62.126.152",
#         "name" : "eth0",
#         "netmask" : "255.255.192.0",
#         "status" : "up"
#      },
#      {
#         "HDWaddr" : "04:01:41:01:86:01",
#         "gateway" : "192.168.0.1",
#         "ip" : "192.168.0.155",
#         "name" : "eth0.5:22",
#         "netmask" : "255.255.255.0",
#         "status" : "down"
#      },
#      {
#         "HDWaddr" : "04:01:41:01:86:01",
#         "gateway" : "",
#         "ip" : "172.62.125.10",
#         "name" : "eth0:n1",
#         "netmask" : "255.255.192.0",
#         "status" : "down"
#      },
#      {
#         "HWaddr" : "04:01:41:01:86:01",
#         "gateway" : "192.160.0.1",
#         "ip" : "192.168.0.150",
#         "name" : "eth0.5",
#         "netmask" : "255.255.255.0",
#         "status" : "up"
#      }
#   ]
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X GET -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#       -u zapi:<password> https://<zenlb_server>:444/zapi/v1/zapi.cgi/interfaces
#
# @apiSampleRequest off
#
#**


sub get_interface() {

	my $out = [];

	use CGI;
	my $q = CGI->new;

	my $s = IO::Socket::INET->new(Proto => 'udp');
	my @interfaces = $s->if_list;
	my @interfacesdw;
	my $i = 0;
	for my $if (@interfaces) {
	        if ( $if !~ /^lo|sit0/ ){
	                my $flags = $s->if_flags($if);
	                $hwaddr = $s->if_hwaddr($if);
	                $status = "";
	                $ip = "";
	                $netmask = "";
	                $gw = "";
	                $link = "on";
	                if ($flags & IFF_UP) {
	                        $status="up";
	                        $ip = $s->if_addr($if);
	                        $netmask = $s->if_netmask($if);
	                        $bc = $s->if_broadcast($if);
	                        $gw = &getDefaultGW($if);
				if ($gw =~ /^$/){
                                                $gw = "";
                                }
		
				push $out, {name => @interfaces[0+$i], ip => $ip, netmask => $netmask, gateway => $gw, status => $status, HWaddr => $hwaddr};
				$i = $i +1; 
	                } else {
	                        $status="down";
	                        if (-e "$configdir/if_$if\_conf") {
	                                tie @array, 'Tie::File', "$configdir/if_$if\_conf", recsep => ':';
	                                $ip = $array[2];
	                                $netmask = $array[3];
	                                $gw = $array[5];
					push $out, {name => @interfaces[0+$i], ip => $ip, netmask => $netmask, gateway => $gw, status => $status, HWaddr => $hwaddr};
					$i = $i +1;
	                                untie @array;
	                        }
	                }
	                if (!($flags & IFF_RUNNING) && ($flags & IFF_UP)) {
	                        $link = "off";
	                }
	                if ( !$netmask ) { $netmask = "-"; }
	                if ( !$ip ) { $ip = "-"; }
	                if ( !$hwaddr ) { $hwaddr = "-"; }
	                if ( !$gw ) { $gw = "-"; }

			# List configured interfaces with down state
                	opendir(DIR, "$configdir");
                	@files = grep(/^if\_$if.*\_conf$/,readdir(DIR));
                	closedir(DIR);
                	foreach $file (@files) {
                        my @filename = split('_',$file);
                        $iff = @filename[1];
                        if (! (grep $_ eq $iff, @interfaces) && ! (grep $_ eq $iff, @interfacesdw)) {
                                open FI, "$configdir/$file";
                                while ($line=<FI>) {
                                        my @s_line = split(':',$line);
					my $ifd = @s_line[0];
                                        my $ifnamef = @s_line[1];
					my $named = "$ifd\:$ifnamef";
                                        my $toipv = @s_line[2];
                                        my $netmask = @s_line[3];
                                        my $status = "down";
                                        my $gw =  @s_line[5];
                                        close FI;

					push $out, {name => $named, ip => $toipv, netmask => $netmask, gateway => $gw, status => $status, HDWaddr => $hwaddr};
				}
			# No show this interface again
                        push(@interfacesdw,$iff);
			}
			}
	}
	}
	
	print $q->header(
	    -type=> 'text/plain',
	    -charset=> 'utf-8',
	    -status=> '200 OK'
	);

		
	my $j = JSON::XS->new->utf8->pretty(1);
	$j->canonical($enabled);
	my $output = $j->encode({
    	   description => "List interfaces",
    	   interfaces => $out,
 	});
	print $output;


}

# POST Interface actions
#
# curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin -d '{"action":"down"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/ifaction/eth0
#
#####Documentation of POST INTERFACE ACTION####
#**
#  @api {post} /ifaction/<interface> Set an action in a interface
#  @apiGroup Interfaces
#  @apiName Postifaction
#  @apiParam {String} interface  Interface name, unique ID.
#  @apiDescription Set an action in a interface, virtual network interface or vlan
#  @apiVersion 1.0.0
#
#
#
# @apiSuccess   {String}        action                   The action that will be set in the interface. Could it be up or down.
#
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Action in interface eth0:new",
#   "params" : [
#      {
#         "action" : "down"
#      }
#   ]
#}
#
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#       -u zapi:<password> -d '{"action":"down"}'
#       https://<zenlb_server>:444/zapi/v1/zapi.cgi/ifaction/eth0:new
#
# @apiSampleRequest off
#
#**


sub ifaction() {

    my $fdev = @_[0];
	my $out_p = [];

    use CGI;
    use JSON;

    my $q = CGI->new;
    my $json = JSON->new;
    my $data = $q->param('POSTDATA');
    my $json_obj = $json->decode($data);

    my $j = JSON::XS->new->utf8->pretty(1);
    $j->canonical($enabled);

	$error = "false";

	# Check interface errors
        if ($fdev =~ /^$/)
		{
            # Error
            $error = "true";
            print $q->header(
               -type=> 'text/plain',
               -charset=> 'utf-8',
               -status=> '400 Bad Request'
            );
            $errormsg = "Interface name can't be empty";
            my $output = $j->encode(
				{
						description => "Interface $fdev",
						error => "true",
						message => $errormsg
				}
			);
            print $output;
            exit;
        }

        if ($fdev =~ /\s+/ )
		{
            # Error
            $error = "true";
            print $q->header(
               -type=> 'text/plain',
               -charset=> 'utf-8',
               -status=> '400 Bad Request'
            );
            $errormsg = "Interface name is not valid";
            my $output = $j->encode(
				{
						description => "Interface $fdev",
						error => "true",
						message => $errormsg
				}
			);
            print $output;
            exit;
        }
	
	# Check input errors
	if ($json_obj->{action} !~ /^up|down/)
	{
		# Error
                $error = "true";
                print $q->header(
                   -type=> 'text/plain',
                   -charset=> 'utf-8',
                   -status=> '400 Bad Request'
                );
                $errormsg = "Action value must be up or down";
                my $output = $j->encode(
					{
							description => "Action value $json_obj->{action}",
							error => "true",
							message => $errormsg
					}
				);
                print $output;
                exit;
	}
	
	# Open conf file to get the interface parameters
	my $if = $fdev;
	tie @array, 'Tie::File', "$configdir/if_$if\_conf", recsep => ':';
	
	# Check if the ip is already in use
	my @activeips = &listallips();
	for my $ip ( @activeips )
	{
		if ( $ip eq @array[2] && $json_obj->{ action } ne "down" )
		{
			# Error
			$error = "true";
			print $q->header(
							  -type    => 'text/plain',
							  -charset => 'utf-8',
							  -status  => '400 Bad Request'
			);
			$errormsg = "Interface $if cannot be UP, IP Address @array[2] is already in use";
			my $output = $j->encode(
									 {
									   description => "Interface $fdev",
									   error       => "true",
									   message     => $errormsg
									 }
			);
			print $output;
			exit;
		}
	}
	
	# Everything is ok
	$exists = &ifexist($if);
    if ($exists eq "false")
	{
    	&createIf($if);
    }
    
    if ($json_obj->{action} eq "up")
	{
		&logfile("running '$ifconfig_bin $if @array[2] netmask @array[3]' ");
		@eject=`$ifconfig_bin $if @array[2] netmask @array[3] 2> /dev/null`;
		&upIf($if);
		$state = $?;
		if ($state == 0)
		{
			@array[4] = "up";
		} 
		else 
		{
			$error = "true";
		}
		&applyRoutes("local",$if,@array[5]);
	} 
	elsif ($json_obj->{action} eq "down")
	{
		&delRoutes("local",$if);
		&downIf($if);
		if ( $? == 0) 
		{
			@array[4] = "down";
		} 
		else 
		{
			$error = "true";
		}
	}
	untie @array;

	if ($error eq "false"){
                # Success
                print $q->header(
                   -type=> 'text/plain',
                   -charset=> 'utf-8',
                   -status=> '201 Created'
                );
                push $out_p, { action => $json_obj->{action}};
                my $j = JSON::XS->new->utf8->pretty(1);
                $j->canonical($enabled);
                my $output = $j->encode({
                        description => "Action in interface $fdev",
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
                $errormsg = "The action $json_obj->{action} is not set in interface $fdev";
                my $output = $j->encode({
                        description => "Action in interface $fdev",
                        error => "true",
                        message => $errormsg
                });
                print $output;
                exit;
        }


}

# PUT Interface
#
# curl --tlsv1 -k -X POST -H 'Content-Type: application/json' -H "ZAPI_KEY: MyIzgr8gcGEd04nIfThgZe0YjLjtxG1vAL0BAfST6csR9Hg5pAWcFOFV1LtaTBJYs" -u zapi:admin -d '{"gateway":"1.1.1.0","ip":"1.1.1.3","netmask":"255.255.192.0"}' https://178.62.126.152:445/zapi/v1/zapi.cgi/modifyif/eth0:n1
#
#####Documentation of PUT INTERFACE####
#**
#  @api {put} /modifyif/<interface> Modify a interface
#  @apiGroup Interfaces
#  @apiName PutIf
#  @apiParam {String} interface  Interface name, unique ID.
#  @apiDescription Modify a interface, vlan or a virtual network interface
#  @apiVersion 1.0.0
#
#
#
# @apiSuccess   {String}        ip                       IP of the interface.
# @apiSuccess   {String}        netmask                  Netmask of the interface.
# @apiSuccess   {String}        gateway                  Gateway of the interface. This value could not be modified in virtual network interface.
#
#
#
# @apiSuccessExample Success-Response:
#{
#   "description" : "Modify interface eth0:new",
#   "params" : [
#      {
#         "gateway" : "192.168.1.0"
#      },
#      {
#         "ip" : "192.168.1.160"
#      },
#      {
#         "netmask" : "255.255.255.0"
#      }
#   ]
#}
#
# @apiExample {curl} Example Usage:
#       curl --tlsv1 -k -X PUT -H 'Content-Type: application/json' -H "ZAPI_KEY: <ZAPI_KEY_STRING>"
#       -u zapi:<password> -d '{"ip":"192.168.1.160","netmask":"255.255.255.0",
#       "gateway":"192.168.1.0"}' https://<zenlb_server>:444/zapi/v1/zapi.cgi/modifyif/eth0:new
#
# @apiSampleRequest off
#
#**



sub modify_interface() {

        my $fdev = @_[0];

        my $out_p = [];

        use CGI;
        use JSON;

        my $q = CGI->new;
        my $json = JSON->new;
        my $data = $q->param('PUTDATA');
        my $json_obj = $json->decode($data);

        $error = "false";

        my $j = JSON::XS->new->utf8->pretty(1);
        $j->canonical($enabled);

        # Check interface errors
        if ($fdev =~ /^$/){
                # Error
                $error = "true";
                print $q->header(
                   -type=> 'text/plain',
                   -charset=> 'utf-8',
                   -status=> '400 Bad Request'
                );
                $errormsg = "Interface name can't be empty";
                my $output = $j->encode({
                        description => "Modify interface $fdev",
                        error => "true",
                        message => $errormsg
                });
                print $output;
                exit;
        }

        if ($fdev =~ /\s+/ ){
                # Error
                $error = "true";
                print $q->header(
                   -type=> 'text/plain',
                   -charset=> 'utf-8',
                   -status=> '400 Bad Request'
                );
                $errormsg = "Interface name is not valid";
                my $output = $j->encode({
                        description => "Modify interface $fdev",
                        error => "true",
                        message => $errormsg
                });
                print $output;
                exit;
	}

	# Check address errors
        if (&ipisok($json_obj->{ip}) eq "false"){
                # Error
                $error = "true";
                print $q->header(
                   -type=> 'text/plain',
                   -charset=> 'utf-8',
                   -status=> '400 Bad Request'
                );
                $errormsg = "IP Address $json_obj->{ip} structure is not ok.";
                my $output = $j->encode({
                        description => "IP Address $json_obj->{ip}",
                        error => "true",
                        message => $errormsg
                });
                print $output;
                exit;
        }

        # Check netmask errors
        if ( $json_obj->{netmask} !~ /^$/ && &ipisok($json_obj->{netmask}) eq "false") {
                # Error
                $error = "true";
                print $q->header(
                   -type=> 'text/plain',
                   -charset=> 'utf-8',
                   -status=> '400 Bad Request'
                );
                $errormsg = "Netmask Address $json_obj->{netmask} structure is not ok.";
                my $output = $j->encode({
                        description => "Netmask Address $json_obj->{netmask}",
                        error => "true",
                        message => $errormsg
                });
                print $output;
                exit;
        }

        # Check gateway errors
        if ( $json_obj->{gateway} !~ /^$/ && &ipisok($json_obj->{gateway}) eq "false") {
                # Error
                $error = "true";
                print $q->header(
                   -type=> 'text/plain',
                   -charset=> 'utf-8',
                   -status=> '400 Bad Request'
                );
                $errormsg = "Gateway Address $json_obj->{gateway} structure is not ok.";
                my $output = $j->encode({
                        description => "Gateway Address $json_obj->{gateway}",
                        error => "true",
                        message => $errormsg
                });
                print $output;
                exit;
        }

	# Get the current values
	my $if = $fdev;

	my $s = IO::Socket::INET->new(Proto => 'udp');
	my $flags = $s->if_flags($if);
	
	$hwaddr = $s->if_hwaddr($if);
	$file = "$configdir/if_$if\_conf";
	tie @array, 'Tie::File', "$file", recsep => ':';
	my $size = @array;
	$ipaddr = $array[2];
	$netmask = $array[3];
	$state = $array[4];
	$gwaddr = $array[5];
	$name = @array[1];
	untie @array;

	# Set the new params
	if(exists($json_obj->{ip})){
		$ipaddr = $json_obj->{ip};
	}
	if(exists($json_obj->{netmask})){
                $netmask = $json_obj->{netmask};
        }
	if(exists($json_obj->{gateway}) && $name =~ /^$/){
                $gwaddr = $json_obj->{gateway};
        }

	# Modify interface
	if ($error eq "false"){
			$exists = &ifexist($if);
                        if ($exists eq "false"){
                                &createIf($if);
                        }
                        &delRoutes("local",$if);
                        &logfile("running '$ifconfig_bin $if $ipaddr netmask $netmask' ");
                        @eject = `$ifconfig_bin $if $ipaddr netmask $netmask 2> /dev/null`;
                        &upIf($if);
                        $state = $?;
                        if ($state == 0){
                                $status = "up";
                        }
                        if ( $if =~ /\:/ ) {
                                &writeConfigIf($if,"$if\:$ipaddr\:$netmask\:$status\:\:");
                        } else {
                                &writeRoutes($if);
                                &writeConfigIf($if,"$if\:\:$ipaddr\:$netmask\:$status\:$gwaddr\:");
                        }
                        &applyRoutes("local",$if,$gwaddr);

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
                        description => "Modify interface $if",
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
                $errormsg = "Errors found trying to modify interface $if";
                my $output = $j->encode({
                        description => "Modify interface $if",
                        error => "true",
                        message => $errormsg
                });
                print $output;
                exit;

        }

	
}

1
